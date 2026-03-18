from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import settings

logger = logging.getLogger("gemini_service")


class GeminiServiceError(Exception):
    pass


@dataclass
class GeminiService:
    model_name: str = settings.GEMINI_MODEL_NAME
    api_key: str = settings.GEMINI_API_KEY

    async def _generate_content(self, prompt: str, use_google_search: bool = False) -> dict[str, Any]:
        if not self.api_key:
            raise GeminiServiceError("GEMINI_API_KEY is not configured")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
        params = {"key": self.api_key}
        gen_config: dict[str, Any] = {
            "temperature": 0.2,
            "maxOutputTokens": 16384,
        }
        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": gen_config,
        }
        if use_google_search:
            payload["tools"] = [{"google_search": {}}]
        else:
            # Force JSON output when not using google_search tool
            gen_config["responseMimeType"] = "application/json"

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, params=params, json=payload)

        if resp.status_code != 200:
            raise GeminiServiceError(f"Gemini request failed: {resp.status_code} {resp.text[:300]}")

        return resp.json()

    @staticmethod
    def _extract_text(data: dict[str, Any]) -> str:
        try:
            content = data["candidates"][0]["content"]
            if isinstance(content, dict):
                parts = content.get("parts", [])
            elif isinstance(content, list) and content:
                parts = content[0].get("parts", [])
            else:
                parts = []
            # Gemini 2.5 flash puts thinking in early parts and the answer in later parts.
            # Concatenate all text parts so we don't miss the JSON output.
            texts = [str(p.get("text", "")) for p in parts if p.get("text")]
            if texts:
                combined = "\n".join(texts)
                logger.debug("[gemini] Raw response text (%d parts, %d chars)", len(texts), len(combined))
                return combined
        except Exception as exc:
            raise GeminiServiceError(f"Gemini response parse failed: {exc}") from exc

        raise GeminiServiceError("Gemini response parse failed: no text content")

    async def _generate_text(self, prompt: str) -> str:
        data = await self._generate_content(prompt, use_google_search=False)
        return self._extract_text(data)

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        text = text.strip()

        # Try to extract from markdown fenced code blocks first
        fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
        if fence_match:
            text = fence_match.group(1).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Find the outermost JSON object by matching braces
        start = text.find("{")
        if start == -1:
            logger.error("[gemini] No JSON found in response: %s", text[:500])
            raise GeminiServiceError("No JSON object found in model response")

        depth = 0
        end = -1
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break

        if end == -1:
            logger.error("[gemini] Unbalanced JSON braces in response: %s", text[:500])
            raise GeminiServiceError("No JSON object found in model response")

        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError as exc:
            logger.error("[gemini] JSON parse failed: %s — response: %s", exc, text[:500])
            raise GeminiServiceError(f"JSON parse failed: {exc}") from exc

    async def clinical_query(self, query_text: str, target_system: str) -> dict[str, Any]:
        prompt = (
            "You are an NHS medicines optimisation assistant.\n"
            "Return ONLY a single JSON object with these keys:\n"
            "- emis_query (string): EMIS Web clinical search query\n"
            "- systmone_query (string): SystmOne clinical search query\n"
            "- inclusion_criteria (array of strings)\n"
            "- exclusion_criteria (array of strings)\n"
            "- safety_notes (array of strings)\n\n"
            "IMPORTANT: In emis_query and systmone_query, put each clause on its own line using \\n. "
            "Format as:\n"
            "Line 1: Population\n"
            "Line 2: INCLUDE clause 1\n"
            "Line 3: INCLUDE clause 2 (etc.)\n"
            "Line 4: EXCLUDE clause 1\n"
            "Line 5: EXCLUDE clause 2 (etc.)\n"
            "Line 6: OUTPUT fields\n\n"
            "Do NOT include any explanation, markdown, or text outside the JSON.\n\n"
            f"Target system: {target_system}\nUser request: {query_text}"
        )
        raw = await self._generate_text(prompt)
        return self._extract_json(raw)

    async def find_opportunities(self, query_text: str, max_results: int) -> dict[str, Any]:
        prompt = (
            "You are an NHS prescribing analytics assistant.\n"
            "Return ONLY a single JSON object with key 'opportunities' containing an array.\n"
            "Each opportunity object must have these keys:\n"
            "- title (string)\n"
            "- rationale (string)\n"
            "- current_drug (string)\n"
            "- target_drug (string)\n"
            "- estimated_annual_savings (number)\n"
            "- affected_patients (integer)\n"
            "- bnf_codes (array of strings)\n"
            "- exclusions (array of strings)\n\n"
            "Keep rationale concise (1-2 sentences). Do NOT include any explanation, markdown, or text outside the JSON.\n\n"
            f"Return at most {max_results} opportunities.\nUser request: {query_text}"
        )
        raw = await self._generate_text(prompt)
        return self._extract_json(raw)

    @staticmethod
    def _extract_grounding_urls(data: dict[str, Any]) -> list[str]:
        urls: list[str] = []
        try:
            chunks = data["candidates"][0].get("groundingMetadata", {}).get("groundingChunks", [])
        except Exception:
            chunks = []

        for chunk in chunks:
            web = chunk.get("web") if isinstance(chunk, dict) else None
            if not isinstance(web, dict):
                continue
            uri = str(web.get("uri") or "").strip()
            if uri:
                urls.append(uri)
        return urls

    @staticmethod
    def _is_trusted_url(url: str, trusted_domains: list[str]) -> bool:
        try:
            host = (urlparse(url).hostname or "").lower()
        except Exception:
            return False

        if not host:
            return False

        for domain in trusted_domains:
            d = domain.lower().strip()
            if host == d or host.endswith("." + d):
                return True
        return False

    async def enrich_opportunities_with_web_evidence(
        self,
        query_text: str,
        opportunities: list[dict[str, Any]],
        trusted_domains: list[str],
        max_results: int,
    ) -> dict[str, Any]:
        if not self.api_key or not opportunities:
            return {"evidence": []}

        trimmed = opportunities[:max_results]
        prompt = (
            "You are an NHS medicines optimisation evidence assistant. "
            "Use Google Search grounding to verify cost-direction and clinical safety. "
            "Only provide citations from trusted sources where possible. "
            "Return JSON only with key 'evidence' (array). "
            "Each evidence item must include: title, evidence_summary, confidence_score, citations, clinical_cautions. "
            f"Trusted domains: {', '.join(trusted_domains)}. "
            f"User query: {query_text}. "
            f"Opportunities JSON: {json.dumps(trimmed, ensure_ascii=True)}"
        )

        data = await self._generate_content(prompt, use_google_search=True)
        raw = self._extract_text(data)
        parsed = self._extract_json(raw)

        grounded_urls = [
            url for url in self._extract_grounding_urls(data)
            if self._is_trusted_url(url, trusted_domains)
        ]

        evidence_items = parsed.get("evidence", []) if isinstance(parsed, dict) else []
        out: list[dict[str, Any]] = []
        for item in evidence_items:
            if not isinstance(item, dict):
                continue

            citations = [
                str(url).strip() for url in item.get("citations", [])
                if str(url).strip() and self._is_trusted_url(str(url).strip(), trusted_domains)
            ]
            if not citations and grounded_urls:
                citations = grounded_urls[:3]

            cautions = [str(x) for x in item.get("clinical_cautions", []) if str(x).strip()]
            confidence_raw = item.get("confidence_score", 0.0)
            try:
                confidence = max(0.0, min(1.0, float(confidence_raw)))
            except (TypeError, ValueError):
                confidence = 0.0

            out.append(
                {
                    "title": str(item.get("title", "")).strip(),
                    "evidence_summary": str(item.get("evidence_summary", "")).strip(),
                    "confidence_score": confidence,
                    "citations": citations,
                    "clinical_cautions": cautions,
                }
            )

        return {"evidence": out}

    async def generate_document(self, document_type: str, payload: dict[str, Any]) -> str:
        prompt = (
            "You are writing NHS-ready clinical communication text. "
            f"Document type: {document_type}. "
            "Return plain text only, no markdown. "
            f"Input data JSON: {json.dumps(payload, ensure_ascii=True)}"
        )
        return await self._generate_text(prompt)
