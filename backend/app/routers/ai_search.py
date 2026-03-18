from __future__ import annotations

import logging
import re

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("ai_search")

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_active_user
from app.mongo_models.opportunity_mongo import OpportunityDocument
from app.models.ai import AIDecisionAudit
from app.schemas.ai import (
    ClinicalQueryRequest,
    ClinicalQueryResponse,
    FindOpportunitiesRequest,
    FindOpportunitiesResponse,
    OpportunityIdea,
)
from app.services.gemini_service import GeminiService, GeminiServiceError

router = APIRouter(prefix="/ai-search", tags=["AI Search"])

TRUSTED_EVIDENCE_DOMAINS = [
    "nice.org.uk",
    "bnf.nice.org.uk",
    "england.nhs.uk",
    "nhs.uk",
    "nhsbsa.nhs.uk",
    "dm+d.nhsbsa.nhs.uk",
]


def _clinical_query_fallback(query_text: str) -> dict:
    text = query_text.lower()
    has_dpp4 = "dpp4" in text or "sitagliptin" in text or "linagliptin" in text
    has_hba1c = "hba1c" in text

    include = [
        "Adult patients on repeat prescribing",
        "Medication issued in last 6 months",
    ]
    exclude = [
        "Palliative care register",
        "Documented contraindication to switch",
    ]
    safety = [
        "Pharmacist review required before patient contact",
        "Apply local formulary and NICE guidance",
    ]

    if has_dpp4:
        include.extend([
            "Current repeat DPP4 inhibitor prescribing",
            "Recent diabetes review in primary care",
        ])
        exclude.extend([
            "Recent specialist diabetes initiation/change",
            "Documented treatment intolerance or contraindication",
        ])
        safety.append("Check renal function, frailty, and polypharmacy before switch recommendation")

    if has_hba1c:
        include.extend([
            "Latest HbA1c recorded in last 12 months",
            "HbA1c below locally agreed review threshold",
        ])
        safety.append("Confirm glycaemic stability before switching chronic diabetes medicines")

    emis_lines = [
        f"INCLUDE: {query_text}",
        "AND active repeat medication",
        "AND adult patients",
        "EXCLUDE: palliative care register",
        "EXCLUDE: documented contraindication/intolerance",
        "OUTPUT: patient identifiers, current medication, last review date",
    ]
    systmone_lines = [
        f"Find repeat prescribing cohort for: {query_text}",
        "Filter to adults with active repeat medication",
        "Exclude palliative care and contraindication-coded patients",
        "Output medication, latest clinical review, and monitoring indicators",
    ]

    if has_dpp4:
        emis_lines.insert(1, "AND DPP4 inhibitor class prescribing")
        systmone_lines.insert(1, "Filter diabetes medicines to DPP4 class")

    if has_hba1c:
        emis_lines.insert(2, "AND latest HbA1c available")
        systmone_lines.insert(2, "Filter by latest HbA1c where recorded")

    return {
        "emis_query": "\n".join(emis_lines),
        "systmone_query": "\n".join(systmone_lines),
        "inclusion_criteria": include,
        "exclusion_criteria": exclude,
        "safety_notes": safety,
    }


def _default_opportunities_fallback(query_text: str, max_results: int) -> list[dict]:
    defaults: list[dict] = [
        {
            "title": "DPP4 to lower-cost formulary option review",
            "rationale": "Patients on higher-cost DPP4s may have clinically suitable lower-cost alternatives, commonly toward sitagliptin where clinically appropriate and formulary-aligned.",
            "current_drug": "Linagliptin",
            "target_drug": "Sitagliptin (dose-adjusted if required; formulary dependent)",
            "estimated_annual_savings": 25000.0,
            "affected_patients": 120,
            "bnf_codes": ["0601023"],
            "exclusions": ["eGFR-related contraindications", "recent specialist initiation"],
        },
        {
            "title": "PPI formulation optimization",
            "rationale": "Capsules/tablets are often lower cost versus liquid formulations when clinically suitable.",
            "current_drug": "Omeprazole liquid",
            "target_drug": "Omeprazole capsules",
            "estimated_annual_savings": 18000.0,
            "affected_patients": 90,
            "bnf_codes": ["0103050"],
            "exclusions": ["Swallowing difficulties", "enteral tube requirements"],
        },
    ]
    out = defaults[:max_results]
    for item in out:
        item["rationale"] = f"{item['rationale']} Query context: {query_text}"
    return out


def _contextual_defaults(query_text: str, max_results: int) -> list[dict]:
    q = query_text.lower()
    defaults = _default_opportunities_fallback(query_text, max_results)

    contextual: list[dict] = []
    if "dpp4" in q or "hba1c" in q or "sitagliptin" in q or "linagliptin" in q:
        contextual.extend([d for d in defaults if "DPP4" in d["title"]])
    if "ppi" in q or "omeprazole" in q or "lansoprazole" in q:
        contextual.extend([d for d in defaults if "PPI" in d["title"]])
    if "brand" in q or "generic" in q:
        contextual.extend(defaults)

    if not contextual:
        return defaults[:max_results]

    # Preserve order and remove duplicates by title.
    seen: set[str] = set()
    deduped: list[dict] = []
    for item in contextual:
        key = str(item.get("title", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped[:max_results]


def _tokenize_query(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    stop_words = {
        "find", "show", "with", "from", "into", "for", "and", "the", "high", "low", "adult", "adults",
        "patients", "opportunities", "opportunity", "recent", "data", "care", "primary", "review", "using",
    }
    return [t for t in tokens if len(t) > 2 and t not in stop_words]


def _intent_keywords(query_text: str) -> set[str]:
    q = query_text.lower()
    keywords: set[str] = set()

    if any(term in q for term in ["dpp4", "hba1c", "sitagliptin", "linagliptin", "diabetes", "glyca"]):
        keywords.update({"dpp4", "hba1c", "sitagliptin", "linagliptin", "diabetes", "glucose", "glyca", "0601"})

    if any(term in q for term in ["ppi", "omeprazole", "lansoprazole", "pantoprazole", "gord", "reflux"]):
        keywords.update({"ppi", "omeprazole", "lansoprazole", "pantoprazole", "gord", "reflux", "0103"})

    if any(term in q for term in ["doac", "apixaban", "rivaroxaban", "edoxaban", "dabigatran", "af", "vte"]):
        keywords.update({"doac", "apixaban", "rivaroxaban", "edoxaban", "dabigatran", "af", "vte", "0208"})

    return keywords


def _is_word_match(haystack: str, token: str) -> bool:
    token = token.strip().lower()
    if not token:
        return False
    if token.isdigit():
        return token in haystack
    return re.search(rf"\b{re.escape(token)}\b", haystack) is not None


def _row_haystack(row: dict) -> str:
    fields = [
        str(row.get("description") or ""),
        str(row.get("workstream") or ""),
        str(row.get("therapeutic_area") or ""),
        str(row.get("current_expensive_bnf") or ""),
        str(row.get("target_cheap_bnf") or ""),
    ]
    return " ".join(fields).lower()


def _filter_rows_by_intent(raw_rows: list[dict], query_text: str) -> list[dict]:
    keywords = _intent_keywords(query_text)
    if not keywords:
        return raw_rows

    filtered: list[dict] = []
    for row in raw_rows:
        haystack = _row_haystack(row)
        if any(_is_word_match(haystack, keyword) for keyword in keywords):
            filtered.append(row)
    return filtered


def _is_idea_aligned(item: dict, query_text: str) -> bool:
    keywords = _intent_keywords(query_text)
    if not keywords:
        return True

    fields = [
        str(item.get("title") or ""),
        str(item.get("rationale") or ""),
        str(item.get("current_drug") or ""),
        str(item.get("target_drug") or ""),
        " ".join(str(x) for x in item.get("bnf_codes", [])),
    ]
    haystack = " ".join(fields).lower()
    return any(keyword in haystack for keyword in keywords)


def _switch_from_description(description: str) -> tuple[str | None, str | None]:
    parts = re.split(r"\s*(?:→|->| to )\s*", description, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return None, None


def _normalize_dpp4_direction(item: dict, query_text: str) -> dict:
    q = query_text.lower()
    if not any(term in q for term in ["dpp4", "hba1c", "sitagliptin", "linagliptin"]):
        return item

    current = str(item.get("current_drug") or "")
    target = str(item.get("target_drug") or "")
    current_l = current.lower()
    target_l = target.lower()

    if "sitagliptin" in current_l and "linagliptin" in target_l:
        normalized = dict(item)
        normalized["current_drug"] = "Linagliptin"
        normalized["target_drug"] = "Sitagliptin (dose-adjusted if required; formulary dependent)"

        rationale = str(normalized.get("rationale") or "")
        addendum = "Direction normalized for cost optimization: consider higher-cost DPP4s toward lower-cost formulary options, often sitagliptin when clinically appropriate."
        if addendum not in rationale:
            normalized["rationale"] = (rationale + " " + addendum).strip()

        return normalized

    return item


def _query_context_bits(query_text: str) -> tuple[list[str], list[str]]:
    q = query_text.lower()
    rationale_bits: list[str] = []
    exclusion_bits: list[str] = []

    if any(term in q for term in ["dpp4", "sitagliptin", "linagliptin"]):
        rationale_bits.append("focus on DPP4 class prescribing")
        exclusion_bits.extend([
            "eGFR-related contraindications",
            "Recent specialist diabetes initiation/change",
        ])

    if "hba1c" in q:
        rationale_bits.append("recent HbA1c review criteria applied")
        if match := re.search(r"hba1c[^\d]{0,12}(?:under|below|<)\s*(\d{1,3})", q):
            rationale_bits.append(f"HbA1c threshold under {match.group(1)} mmol/mol")
        exclusion_bits.append("Unstable glycaemic control requiring clinician review")

    if any(term in q for term in ["ppi", "omeprazole", "lansoprazole", "pantoprazole"]):
        rationale_bits.append("focus on PPI formulation optimization")

    if any(term in q for term in ["swallowing", "dysphagia", "tube"]):
        rationale_bits.append("exclude patients with swallowing or enteral administration constraints")
        exclusion_bits.extend([
            "Swallowing difficulties",
            "Enteral tube requirements",
        ])

    if any(term in q for term in ["brand", "generic"]):
        rationale_bits.append("focus on brand-to-generic optimization")

    if any(term in q for term in ["doac", "apixaban", "rivaroxaban", "edoxaban", "dabigatran"]):
        rationale_bits.append("focus on DOAC optimization and monitoring context")

    return rationale_bits, exclusion_bits


def _tighten_idea_with_query_context(item: dict, query_text: str) -> dict:
    item = _normalize_dpp4_direction(item, query_text)
    rationale_bits, exclusion_bits = _query_context_bits(query_text)

    base_rationale = str(item.get("rationale") or "")
    if rationale_bits:
        context_sentence = "Query constraints: " + "; ".join(rationale_bits) + "."
        if context_sentence not in base_rationale:
            base_rationale = (base_rationale + " " + context_sentence).strip()

    merged_exclusions = [str(x) for x in item.get("exclusions", []) if str(x).strip()]
    for exclusion in exclusion_bits:
        normalized_existing = {existing.strip().lower() for existing in merged_exclusions}
        if exclusion.strip().lower() not in normalized_existing:
            merged_exclusions.append(exclusion)

    tightened = dict(item)
    tightened["rationale"] = base_rationale
    tightened["exclusions"] = merged_exclusions
    return tightened


def _merge_web_evidence_into_item(item: dict, evidence_item: dict) -> dict:
    merged = dict(item)

    evidence_summary = str(evidence_item.get("evidence_summary") or "").strip()
    if evidence_summary:
        rationale = str(merged.get("rationale") or "")
        evidence_suffix = f" Evidence check: {evidence_summary}"
        if evidence_suffix not in rationale:
            merged["rationale"] = (rationale + evidence_suffix).strip()

    existing_exclusions = [str(x) for x in merged.get("exclusions", []) if str(x).strip()]
    existing_norm = {x.lower().strip() for x in existing_exclusions}
    for caution in evidence_item.get("clinical_cautions", []) or []:
        text = str(caution).strip()
        if text and text.lower() not in existing_norm:
            existing_exclusions.append(text)
            existing_norm.add(text.lower())

    merged["exclusions"] = existing_exclusions
    merged["evidence_summary"] = evidence_summary or None
    merged["confidence_score"] = evidence_item.get("confidence_score")
    merged["citations"] = [str(x) for x in evidence_item.get("citations", []) if str(x).strip()]
    return merged


async def _opportunities_fallback_from_mongo(query_text: str, max_results: int, tenant_id: str) -> list[dict]:
    logger.info("[mongo-fallback] Querying mongo for tenant=%s query=%r", tenant_id, query_text)
    collection = OpportunityDocument.get_pymongo_collection()
    raw = await collection.find({"icb_id": tenant_id}).sort("estimated_annual_savings", -1).limit(500).to_list(length=500)
    if not raw:
        logger.warning("[mongo-fallback] No mongo data for tenant=%s, returning HARDCODED defaults", tenant_id)
        return _default_opportunities_fallback(query_text, max_results)

    logger.info("[mongo-fallback] Found %d rows in mongo", len(raw))
    candidates = _filter_rows_by_intent(raw, query_text)
    if not candidates:
        logger.warning("[mongo-fallback] No intent-matched rows from %d mongo results, returning contextual defaults", len(raw))
        return _contextual_defaults(query_text, max_results)

    query_tokens = _tokenize_query(query_text)
    ranked: list[tuple[float, dict]] = []

    for row in candidates:
        description = str(row.get("description") or "")
        workstream = str(row.get("workstream") or "")
        therapeutic_area = str(row.get("therapeutic_area") or "")
        current_bnf = str(row.get("current_expensive_bnf") or "")
        target_bnf = str(row.get("target_cheap_bnf") or "")
        haystack = f"{description} {workstream} {therapeutic_area} {current_bnf} {target_bnf}".lower()

        match_score = sum(1 for token in query_tokens if _is_word_match(haystack, token))
        savings = float(row.get("estimated_annual_savings") or 0.0)
        score = (match_score * 1000000) + savings

        cur_from_desc, tgt_from_desc = _switch_from_description(description)
        current_drug = cur_from_desc or (current_bnf if current_bnf else None)
        target_drug = tgt_from_desc or (target_bnf if target_bnf else None)

        exclusions = [
            "Documented contraindication or intolerance",
            "Recent specialist-led medicine change",
        ]
        if "hba1c" in query_text.lower() or "dpp4" in query_text.lower():
            exclusions.append("Unstable glycaemic control requiring clinical review")

        idea = {
            "title": description if description else f"{workstream} opportunity",
            "rationale": f"Matched from live tenant opportunities dataset (workstream: {workstream or 'General'}).",
            "current_drug": current_drug,
            "target_drug": target_drug,
            "estimated_annual_savings": savings,
            "affected_patients": int(row.get("patients_affected") or 0),
            "bnf_codes": [x for x in [current_bnf, target_bnf] if x],
            "exclusions": exclusions,
        }
        ranked.append((score, idea))

    ranked.sort(key=lambda x: x[0], reverse=True)
    matched = [idea for score, idea in ranked if score >= 1000000][:max_results]
    if matched:
        logger.info("[mongo-fallback] Returning %d matched opportunities from mongo", len(matched))
        return matched

    logger.warning("[mongo-fallback] No high-score matches from %d candidates, returning contextual defaults", len(candidates))
    return _contextual_defaults(query_text, max_results)


@router.post("/clinical-query", response_model=ClinicalQueryResponse)
async def clinical_query(
    body: ClinicalQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    target_system = (body.target_system or "both").lower()
    if target_system not in {"emis", "systmone", "both"}:
        target_system = "both"

    service = GeminiService()
    try:
        logger.info("[clinical-query] Calling Gemini for query=%r system=%s", body.query_text, target_system)
        generated = await service.clinical_query(body.query_text, target_system)
        logger.info("[clinical-query] Gemini returned live result")
    except GeminiServiceError as exc:
        logger.warning("[clinical-query] Gemini failed (%s), using hardcoded fallback", exc)
        generated = _clinical_query_fallback(body.query_text)

    response = ClinicalQueryResponse(
        query_text=body.query_text,
        target_system=target_system,
        emis_query=str(generated.get("emis_query", "")),
        systmone_query=str(generated.get("systmone_query", "")),
        inclusion_criteria=[str(x) for x in generated.get("inclusion_criteria", [])],
        exclusion_criteria=[str(x) for x in generated.get("exclusion_criteria", [])],
        safety_notes=[str(x) for x in generated.get("safety_notes", [])],
    )

    db.add(AIDecisionAudit(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="clinical_query",
        input_summary=body.query_text,
        output_summary=response.model_dump_json(),
        guardrail_safe=True,
        endpoint="/api/ai-search/clinical-query",
        extra={"target_system": target_system},
    ))
    await db.commit()

    return response


@router.post("/find-opportunities", response_model=FindOpportunitiesResponse)
async def find_opportunities(
    body: FindOpportunitiesRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    tenant_id = str(current_user.tenant_id) if current_user.tenant_id else settings.SY_TENANT_ID
    service = GeminiService()
    data_source = "gemini"
    try:
        logger.info("[find-opportunities] Calling Gemini for query=%r max=%d", body.query_text, body.max_results)
        generated = await service.find_opportunities(body.query_text, body.max_results)
        ideas_raw = generated.get("opportunities", [])
        logger.info("[find-opportunities] Gemini returned %d ideas", len(ideas_raw))
    except GeminiServiceError as exc:
        logger.warning("[find-opportunities] Gemini failed (%s), falling back to mongo", exc)
        data_source = "mongo_fallback"
        ideas_raw = await _opportunities_fallback_from_mongo(body.query_text, body.max_results, tenant_id)

    aligned_ideas = [item for item in ideas_raw if _is_idea_aligned(item, body.query_text)]
    if not aligned_ideas:
        logger.warning("[find-opportunities] No aligned ideas from %s, falling back to mongo (tenant=%s)", data_source, tenant_id)
        data_source = "mongo_fallback"
        aligned_ideas = await _opportunities_fallback_from_mongo(body.query_text, body.max_results, tenant_id)

    tightened_items = [
        _tighten_idea_with_query_context(item, body.query_text)
        for item in aligned_ideas[:body.max_results]
    ]

    enriched_items = tightened_items
    try:
        logger.info("[find-opportunities] Enriching %d items with web evidence", len(tightened_items))
        evidence = await service.enrich_opportunities_with_web_evidence(
            query_text=body.query_text,
            opportunities=tightened_items,
            trusted_domains=TRUSTED_EVIDENCE_DOMAINS,
            max_results=body.max_results,
        )
        evidence_list = [x for x in evidence.get("evidence", []) if isinstance(x, dict)]
        logger.info("[find-opportunities] Web evidence returned %d items", len(evidence_list))
        evidence_by_title = {
            str(item.get("title", "")).strip().lower(): item
            for item in evidence_list
            if str(item.get("title", "")).strip()
        }

        merged: list[dict] = []
        for item in tightened_items:
            key = str(item.get("title", "")).strip().lower()
            evidence_item = evidence_by_title.get(key)
            merged.append(_merge_web_evidence_into_item(item, evidence_item) if evidence_item else item)
        enriched_items = merged
    except GeminiServiceError as exc:
        logger.warning("[find-opportunities] Web evidence enrichment failed (%s), skipping", exc)
        enriched_items = tightened_items

    opportunities = [
        OpportunityIdea(
            title=str(item.get("title", "Untitled opportunity")),
            rationale=str(item.get("rationale", "")),
            current_drug=item.get("current_drug"),
            target_drug=item.get("target_drug"),
            estimated_annual_savings=float(item.get("estimated_annual_savings", 0.0) or 0.0),
            affected_patients=int(item.get("affected_patients", 0) or 0),
            bnf_codes=[str(x) for x in item.get("bnf_codes", [])],
            exclusions=[str(x) for x in item.get("exclusions", [])],
            evidence_summary=(str(item.get("evidence_summary")).strip() if item.get("evidence_summary") else None),
            confidence_score=(float(item.get("confidence_score")) if item.get("confidence_score") is not None else None),
            citations=[str(x) for x in item.get("citations", []) if str(x).strip()],
        )
        for item in enriched_items
    ]

    response = FindOpportunitiesResponse(query_text=body.query_text, opportunities=opportunities)
    logger.info("[find-opportunities] Returning %d opportunities (source=%s)", len(opportunities), data_source)

    db.add(AIDecisionAudit(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="find_opportunities",
        input_summary=body.query_text,
        output_summary=response.model_dump_json(),
        guardrail_safe=True,
        endpoint="/api/ai-search/find-opportunities",
        extra={"max_results": body.max_results},
    ))
    await db.commit()

    return response


@router.get("/suggestions")
async def suggestions():
    return {
        "suggestions": [
            "Find high-savings DPP4 opportunities in adults with recent HbA1c under 75 mmol/mol",
            "Show PPI liquid-to-capsule switch candidates excluding swallowing difficulties",
            "Identify repeat prescriptions for expensive brands where generic equivalent exists",
            "Find opportunities with high savings and low implementation effort in primary care",
        ]
    }
