# QIPP — VICTOR'S Personal Build Guide
## macOS · Scrapfly ✓ · MongoDB Atlas ✓ · GitHub Copilot
**Victor's role: Data Pipelines Lead + Opportunity Engine + AI Layer**

---

> **Ground truth on the PoC:** The HTML file `MedSave_Platform_v4_SouthYorkshire.html` is the pixel-perfect design contract. Every page in the React app must match it exactly. You are responsible for making the data real. Your services feed the numbers you see on every screen.

---

## 1. Your Tooling — macOS Setup

### 1.1 What You Already Have
- ✅ Scrapfly account (API key ready)
- ✅ MongoDB Atlas cluster (connection string ready)
- ✅ GitHub Student Pack (includes all tools below)
- macOS → use Homebrew for everything

### 1.2 macOS Environment Setup

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11 (exact version — async SQLAlchemy compatibility)
brew install python@3.11
python3.11 --version  # confirm

# Install Node 18 LTS
brew install node@18
node --version  # confirm 18.x

# Install Redis
brew install redis
brew services start redis   # starts on login automatically
redis-cli ping              # should return PONG

# Install Git (probably already have it)
brew install git

# Install the GitHub CLI (useful for PRs)
brew install gh
gh auth login
```

### 1.3 IDE Options for Victor

**Option A: Google Antigravity (Recommended — matches what your partner uses)**

Antigravity is Google's agentic IDE launched November 2025. Free, VS Code-based, autonomous AI agents, built-in browser testing. Available for macOS.

```bash
# Download from antigravity.google/download → macOS installer
# Run the .dmg, drag to Applications
# First launch: sign in with Google account
# Set Terminal Policy: "Auto" (lets agents run standard commands)
# Rate limits refresh every 5 hours — very generous for individual dev
```

Key features for your work:
- **Agent Manager:** Send "Implement the OpportunityDiscoveryEngine from the spec" — agent writes all code across multiple files
- **Built-in browser:** Test your FastAPI endpoints and see the React UI
- **Artifacts:** Every task generates a plan + diff you can review before accepting

**Option B: PyCharm Pro (via Student Pack)**

Excellent FastAPI, MongoDB, and Python tooling. Get it free via JetBrains Student:
```
jetbrains.com/community/education → Apply for Student license
→ Download PyCharm (2025.1+ — now unified product, free for students)
→ Activate with JetBrains Account
```
PyCharm detects FastAPI routes automatically, has MongoDB plugin, and excellent Alembic support.

**Option C: VS Code + GitHub Copilot**
Standard setup — install from code.visualstudio.com, then install GitHub Copilot extension.

---

### 1.4 GitHub Student Pack — Benefits to Activate

Go to `education.github.com/pack`:

| Benefit | Use For | Notes |
|---------|---------|-------|
| **GitHub Copilot Student** | Free AI completions | Already available |
| **MongoDB Atlas $50 credit** | You already have this set up — apply the credit to your org | Apply at mongodb.com/students |
| **JetBrains (PyCharm Pro)** | Python IDE with MongoDB plugin | Apply at jetbrains.com/student |
| **DigitalOcean $200** | Deploy backend/frontend | Claim now — use for final pitch deploy |
| **Namecheap .me domain** | Custom domain for demo | qipp.health or similar |
| **Heroku $13/mo × 24** | Alternative deploy | Backup option |
| **Datadog (2 years free)** | Monitor FastAPI server | Claim for production |
| **Sentry** | Error tracking | sentry.io/for/education |
| **1Password (1 year)** | Store all API keys safely | Claim immediately |

---

## 2. Your Scrapfly Setup (You Own This)

You already have the Scrapfly account. Here is exactly how to use it in the project.

**Configuration** (`backend/.env`):
```env
SCRAPFLY_API_KEY=scp-live-YOUR_EXISTING_KEY
SCRAPFLY_DATA_DIR=./data/scrapfly_cache
```

**The caching service** (`backend/app/services/scrapfly_cache.py`):

```python
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

CACHE_DIR = Path("./data/scrapfly_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL_HOURS = 24

def _cache_path(url: str) -> Path:
    key = hashlib.md5(url.encode()).hexdigest()
    return CACHE_DIR / f"{key}.json"

def get_cached(url: str) -> Optional[str]:
    path = _cache_path(url)
    if not path.exists():
        return None
    cached = json.loads(path.read_text())
    cached_at = datetime.fromisoformat(cached["cached_at"])
    if datetime.utcnow() - cached_at < timedelta(hours=CACHE_TTL_HOURS):
        return cached["data"]
    return None   # stale — will be refreshed

def get_stale_cached(url: str) -> Optional[str]:
    """Fallback — return stale cache if fresh fetch fails"""
    path = _cache_path(url)
    if path.exists():
        return json.loads(path.read_text())["data"]
    return None

def save_cache(url: str, data: str) -> None:
    path = _cache_path(url)
    path.write_text(json.dumps({
        "cached_at": datetime.utcnow().isoformat(),
        "url": url,
        "data": data
    }))
```

---

## 3. Your Core Service — OpenPrescribingService (You Own This)

**File:** `backend/app/services/openprescribing_service.py`

This is the most important service in the system. It calls all OpenPrescribing endpoints via Scrapfly.

```python
import json
import re
import httpx
from typing import Optional
from scrapfly import ScrapflyClient, ScrapeConfig
from app.services.scrapfly_cache import get_cached, get_stale_cached, save_cache
from app.config import settings

BASE_URL = "https://openprescribing.net/api/1.0"

class OpenPrescribingService:
    def __init__(self, scrapfly_key: str):
        self.scrapfly_key = scrapfly_key

    async def _fetch(self, url: str) -> str:
        """Fetch via Scrapfly with 24h local cache. Falls back to stale on failure."""
        
        # 1. Check fresh cache
        cached = get_cached(url)
        if cached:
            return cached
        
        # 2. Fetch via Scrapfly
        try:
            client = ScrapflyClient(key=self.scrapfly_key)
            result = client.scrape(ScrapeConfig(
                url=url,
                asp=True,       # Cloudflare bypass
                country="GB",   # UK proxy for NHS sites
            ))
            content = result.scrape_result["content"]
            
            # OpenPrescribing sometimes wraps JSON in HTML
            if not (content.strip().startswith("[") or content.strip().startswith("{")):
                match = re.search(r"(\[.*?\]|\{.*?\})", content, re.DOTALL)
                if match:
                    content = match.group(1)
            
            save_cache(url, content)
            return content
            
        except Exception as e:
            # 3. Fall back to stale cache
            stale = get_stale_cached(url)
            if stale:
                print(f"[OpenPrescribing] Scrapfly failed, using stale cache: {e}")
                return stale
            raise e

    # ── ENDPOINT 1: BNF Code Search ──────────────────────────────────
    async def search_bnf_codes(self, query: str, exact: bool = False) -> list[dict]:
        """
        Find BNF codes by prefix or name.
        query="0601022" → all DPP4 inhibitors
        query="0212000" → all statins  
        """
        url = f"{BASE_URL}/bnf_code/?q={query}&format=json&exact={'true' if exact else 'false'}"
        data = await self._fetch(url)
        return json.loads(data)

    # ── ENDPOINT 2: Spending by Organisation ─────────────────────────
    async def get_spending_by_org(
        self,
        bnf_code: str,
        org_type: str,          # practice | pcn | sicbl | icb
        org_code: Optional[str] = None
    ) -> list[dict]:
        """
        Primary savings data source.
        
        Examples:
        get_spending_by_org("0212000", "practice", "02P")
        → statin spending, all SY practices
        
        get_spending_by_org("0601022", "sicbl", "02P")
        → DPP4 spending for South Yorkshire Sub-ICB
        """
        params = f"code={bnf_code}&org_type={org_type}&format=json"
        if org_code:
            params += f"&org={org_code}"
        url = f"{BASE_URL}/spending_by_org/?{params}"
        data = await self._fetch(url)
        return json.loads(data)

    # ── ENDPOINT 3: Measures by Organisation ─────────────────────────
    async def get_measures_for_org(
        self,
        org_id: str,
        org_level: str   # practice | pcn | sub_icb | icb
    ) -> dict:
        """
        Pre-computed NHS quality measures — this is what TRIGGERS opportunities.
        Each measure shows where prescribing deviates from best practice.
        
        For South Yorkshire: get_measures_for_org("02P", "sub_icb")
        """
        endpoint_map = {
            "practice": "measure_by_practice",
            "pcn":      "measure_by_pcn",
            "sub_icb":  "measure_by_sicbl",
            "icb":      "measure_by_icb",
        }
        endpoint = endpoint_map[org_level]
        url = f"{BASE_URL}/{endpoint}/?org={org_id}&format=json"
        data = await self._fetch(url)
        return json.loads(data)

    # ── ENDPOINT 4: Drug Tariff CSV ───────────────────────────────────
    async def get_tariff_prices(self, force: bool = False) -> list[dict]:
        """
        Download full NHS Drug Tariff from OpenPrescribing.
        Returns ~12,000 records with prices for every drug.
        force=True bypasses cache.
        """
        import csv
        import io
        
        url = f"{BASE_URL}/tariff/?format=csv"
        
        if force:
            from app.services.scrapfly_cache import _cache_path
            cache_file = _cache_path(url)
            if cache_file.exists():
                cache_file.unlink()  # delete cache to force fresh fetch
        
        # For tariff CSV, check for manual fallback file
        fallback_path = "backend/tariff.csv"
        
        try:
            raw = await self._fetch(url)
        except Exception as e:
            import os
            if os.path.exists(fallback_path):
                with open(fallback_path) as f:
                    raw = f.read()
            else:
                raise e
        
        results = []
        reader = csv.DictReader(io.StringIO(raw))
        for row in reader:
            try:
                price_pence = int(row.get("price_pence") or 0)
                pack_size = float(row.get("pack_size") or 1)
                results.append({
                    "vmpp_id":         row.get("vmpp_id", ""),
                    "vmpp":            row.get("vmpp", ""),
                    "product":         row.get("product", ""),
                    "bnf_code":        row.get("bnf_code", ""),
                    "tariff_category": row.get("tariff_category", ""),
                    "price_pence":     price_pence,
                    "pack_size":       pack_size,
                    "price_per_unit_pence": round(price_pence / pack_size, 4) if pack_size > 0 else 0,
                    "date":            row.get("date", ""),
                    "concession":      row.get("concession", "").lower() == "true",
                })
            except (ValueError, TypeError):
                continue  # skip malformed rows
        
        return results

    # ── ENDPOINT 5: Price Concessions ─────────────────────────────────
    async def get_price_concessions(self) -> list[dict]:
        """
        Current Drug Tariff price concessions.
        Feeds the 'Price Concession Cost Dashboard' in the PoC.
        When generics have supply issues, NHSBSA grants temporary price increases.
        """
        url = f"{BASE_URL}/concessions/?format=json"
        data = await self._fetch(url)
        return json.loads(data)

    # ── ENDPOINT 6: Price per Unit by Practice ────────────────────────
    async def get_price_per_unit(
        self,
        bnf_code: str,
        org_code: str
    ) -> list[dict]:
        """
        Price per unit across practices — reveals ghost generics.
        Outlier practices prescribing branded drugs show up as high-cost outliers.
        Feeds the 'Price per Unit' page in the PoC.
        """
        url = f"{BASE_URL}/price_per_unit/?code={bnf_code}&org={org_code}&format=json"
        data = await self._fetch(url)
        return json.loads(data)

    # ── AGGREGATE HELPER ──────────────────────────────────────────────
    async def get_qipp_prescribing_data(self) -> dict:
        """
        Fetch prescribing data for ALL 10 QIPP workstreams at once.
        Used by the opportunity discovery engine.
        """
        import asyncio
        
        WORKSTREAM_PREFIXES = {
            "DPP4":           "0601022",
            "SGLT2":          "0601023",
            "STATINS":        "0212000",
            "DOACs":          "0208020",
            "PPI":            "0103050",
            "ANTIDEPRESSANTS":"0403030",
            "GABAPENTINOIDS": "0408010",
            "ASTHMA_INHALERS":"0301011",
            "COPD_INHALERS":  "0301040",
            "GLP1":           "0601023",
        }
        
        results = {}
        for workstream, prefix in WORKSTREAM_PREFIXES.items():
            try:
                bnf_codes = await self.search_bnf_codes(prefix)
                spending  = await self.get_spending_by_org(prefix, "practice", "02P")
                results[workstream] = {
                    "chemicals": [c["id"] for c in bnf_codes if c.get("type") == "chemical"],
                    "spending_data": spending,
                }
                await asyncio.sleep(0.2)  # avoid hammering Scrapfly
            except Exception as e:
                print(f"[OpenPrescribing] Error fetching {workstream}: {e}")
                results[workstream] = {"chemicals": [], "spending_data": []}
        
        return results
```

---

## 4. Your Core Service — OpportunityDiscoveryEngine (You Own This)

**File:** `backend/app/services/opportunity_discovery.py`

This generates the actual £ saving opportunities from live data.

```python
import asyncio
from datetime import datetime
from app.services.openprescribing_service import OpenPrescribingService
from app.mongo_models.opportunity import OpportunityDocument
from app.mongo_models.tariff_price import TariffPriceDocument

# ── WORKSTREAM MAPPINGS ───────────────────────────────────────────────
# These map OpenPrescribing measure IDs → drug switch details
# measure_id comes from /measure_by_sicbl/ API response
WORKSTREAM_MAPPINGS = [
    {
        "measure_id":       "statin_intensity",
        "workstream":       "STATINS",
        "expensive_bnf":    "0212000B0AA",   # Branded statins
        "target_bnf":       "0212000B0",     # Generic Atorvastatin
        "expensive_drug":   "Branded Statin (Lipitor/Crestor)",
        "target_drug":      "Atorvastatin (Generic)",
        "opportunity_type": "ghost_generic",
        "ease_score":       5,
        "bnf_section":      "0212000",
        "bnf_chapter":      "Ch.2 Cardiovascular",
        "nice_reference":   "NICE CG181",
        "hard_exclusions":  ["documented statin intolerance", "specialist brand recommendation"],
        "soft_exclusions":  ["patient preference documented"],
        "clinical_guidance": "Switch to generic atorvastatin 20mg. Counsel patient that the active ingredient is identical. Check for documented intolerance before switching.",
        "patient_letter_summary": "Your statin medication is being changed to the generic version — it contains exactly the same medicine.",
        "is_on_nhse_16":    True,
    },
    {
        "measure_id":       "doac",
        "workstream":       "DOACs",
        "expensive_bnf":    "0208020Z0",   # Rivaroxaban
        "target_bnf":       "0208020X0",   # Edoxaban
        "expensive_drug":   "Rivaroxaban (Xarelto)",
        "target_drug":      "Edoxaban (Lixiana)",
        "opportunity_type": "therapeutic_switch",
        "ease_score":       3,
        "bnf_section":      "0208020",
        "bnf_chapter":      "Ch.2 Cardiovascular",
        "nice_reference":   "NICE TA355",
        "hard_exclusions":  ["valvular AF", "eGFR < 30", "documented contraindication"],
        "soft_exclusions":  ["patient preference for current drug"],
        "clinical_guidance": "Review patients on Rivaroxaban for AF. Exclude valvular AF and eGFR < 30. Switch to Edoxaban 60mg OD (30mg if eGFR 15-50, <60kg, or interacting drugs). Inform GP and patient.",
        "patient_letter_summary": "Your blood-thinning medicine is changing to edoxaban, which is clinically equivalent and more cost-effective.",
        "is_on_nhse_16":    True,
    },
    {
        "measure_id":       "sglt2",
        "workstream":       "SGLT2",
        "expensive_bnf":    "0601023AW",   # Canagliflozin
        "target_bnf":       "0601023AV",   # Dapagliflozin
        "expensive_drug":   "Canagliflozin (Invokana)",
        "target_drug":      "Dapagliflozin (Forxiga)",
        "opportunity_type": "therapeutic_switch",
        "ease_score":       3,
        "bnf_section":      "0601023",
        "bnf_chapter":      "Ch.6 Endocrine",
        "nice_reference":   "NICE TA683",
        "hard_exclusions":  ["eGFR < 45", "heart failure NYHA class IV"],
        "soft_exclusions":  ["recurrent UTIs documented"],
        "clinical_guidance": "Switch Canagliflozin to Dapagliflozin 10mg OD in T2DM patients. Exclude eGFR < 45. Check for documented recurrent UTIs as soft exclusion.",
        "patient_letter_summary": "Your diabetes tablet is being changed to dapagliflozin — it works in the same way and is equally effective.",
        "is_on_nhse_16":    False,
    },
    {
        "measure_id":       "dpp4",
        "workstream":       "DPP4",
        "expensive_bnf":    "0601023AH",   # Sitagliptin
        "target_bnf":       "0601022B0",   # Alogliptin
        "expensive_drug":   "Sitagliptin/Linagliptin",
        "target_drug":      "Alogliptin (Vipidia)",
        "opportunity_type": "therapeutic_switch",
        "ease_score":       3,
        "bnf_section":      "0601022",
        "bnf_chapter":      "Ch.6 Endocrine",
        "nice_reference":   "NICE TA336",
        "hard_exclusions":  ["hepatic impairment", "heart failure"],
        "soft_exclusions":  ["established on current drug > 5 years with stable HbA1c"],
        "clinical_guidance": "Switch Sitagliptin/Linagliptin to Alogliptin 25mg OD (12.5mg if eGFR 30-60). Review at 3 months. Check HbA1c at 6 months post-switch.",
        "patient_letter_summary": "Your diabetes tablet is being changed to alogliptin, which works in the same way.",
        "is_on_nhse_16":    False,
    },
    {
        "measure_id":       "ppi",
        "workstream":       "PPI",
        "expensive_bnf":    "0103050P0",   # Esomeprazole/Pantoprazole
        "target_bnf":       "0103050L0",   # Lansoprazole
        "expensive_drug":   "Esomeprazole/Pantoprazole",
        "target_drug":      "Lansoprazole 30mg (Generic)",
        "opportunity_type": "therapeutic_switch",
        "ease_score":       4,
        "bnf_section":      "0103050",
        "bnf_chapter":      "Ch.1 Gastro-Intestinal",
        "nice_reference":   "NICE CG184",
        "hard_exclusions":  ["specialist recommendation for specific PPI", "drug interaction requiring specific PPI"],
        "soft_exclusions":  ["Barrett's oesophagus"],
        "clinical_guidance": "Switch to Lansoprazole 30mg or Omeprazole 20mg generic. Review indication — consider step-down or deprescribing for low-risk patients.",
        "patient_letter_summary": "Your acid tablet is being switched to an equally effective, lower-cost alternative.",
        "is_on_nhse_16":    False,
    },
    {
        "measure_id":       "antidepressant",
        "workstream":       "ANTIDEPRESSANTS",
        "expensive_bnf":    "0403030E0",   # Escitalopram
        "target_bnf":       "0403030D0",   # Sertraline
        "expensive_drug":   "Escitalopram",
        "target_drug":      "Sertraline (Generic)",
        "opportunity_type": "therapeutic_switch",
        "ease_score":       3,
        "bnf_section":      "0403030",
        "bnf_chapter":      "Ch.4 CNS",
        "nice_reference":   "NICE CG90",
        "hard_exclusions":  ["QTc prolongation risk", "documented escitalopram-specific response"],
        "soft_exclusions":  ["patient stability on current medication > 2 years"],
        "clinical_guidance": "Switch Escitalopram to Sertraline 50mg in newly initiated patients. For established patients, clinical review required. Taper current SSRI before starting new one.",
        "patient_letter_summary": "Your antidepressant is being reviewed — please speak with your doctor before making any changes.",
        "is_on_nhse_16":    False,
    },
    {
        "measure_id":       "pregabalin",
        "workstream":       "GABAPENTINOIDS",
        "expensive_bnf":    "0408010AE",   # Pregabalin branded (Lyrica)
        "target_bnf":       "0408010AE",   # Pregabalin generic
        "expensive_drug":   "Pregabalin (Lyrica/branded)",
        "target_drug":      "Pregabalin (Generic)",
        "opportunity_type": "ghost_generic",
        "ease_score":       5,
        "bnf_section":      "0408010",
        "bnf_chapter":      "Ch.4 CNS",
        "nice_reference":   "NICE NG193",
        "hard_exclusions":  ["documented intolerance to generic excipients"],
        "soft_exclusions":  [],
        "clinical_guidance": "Switch branded Pregabalin (Lyrica) to generic Pregabalin. Active ingredient is identical. No dose adjustment needed. Inform patient.",
        "patient_letter_summary": "Your pain/nerve medicine is being changed to the generic version — it contains exactly the same medicine.",
        "is_on_nhse_16":    False,
    },
]

SAVINGS_THRESHOLDS = {
    "practice": 500,
    "pcn":      2000,
    "sub_icb":  10000,
    "icb":      25000,
}

class OpportunityDiscoveryEngine:
    def __init__(self, op_service: OpenPrescribingService):
        self.op_service = op_service

    async def discover_for_sub_icb(
        self,
        sub_icb_ods: str,   # "02P" for South Yorkshire
        tenant_id: str
    ) -> list[OpportunityDocument]:
        
        print(f"[Discovery] Starting for {sub_icb_ods}...")
        
        # 1. Fetch all quality measures for the Sub-ICB
        measures_response = await self.op_service.get_measures_for_org(
            org_id=sub_icb_ods,
            org_level="sub_icb"
        )
        measures = {}
        for m in measures_response.get("measures", []):
            measures[m["measure"]] = m
        
        print(f"[Discovery] Got {len(measures)} measures from OpenPrescribing")
        
        # 2. Load current Drug Tariff prices into memory index
        tariff_index = await self._build_tariff_index()
        print(f"[Discovery] Tariff index built: {len(tariff_index)} BNF entries")
        
        # 3. Process each workstream
        opportunities = []
        for mapping in WORKSTREAM_MAPPINGS:
            measure = measures.get(mapping["measure_id"])
            if not measure:
                print(f"[Discovery] No measure found for {mapping['measure_id']}, skipping")
                continue
            if measure.get("denominator", 0) == 0:
                continue
            
            opp = self._build_opportunity(
                measure=measure,
                mapping=mapping,
                tariff_index=tariff_index,
                sub_icb_ods=sub_icb_ods,
                tenant_id=tenant_id,
            )
            
            if opp and opp.annual_saving >= SAVINGS_THRESHOLDS["sub_icb"]:
                opportunities.append(opp)
                print(f"[Discovery] {mapping['workstream']}: £{opp.annual_saving:,.0f}/yr")
        
        # 4. Clear stale identified opportunities, insert fresh ones
        await OpportunityDocument.find({
            "tenant_id": tenant_id,
            "sub_icb_ods": sub_icb_ods,
            "status": "identified"
        }).delete()
        
        if opportunities:
            await OpportunityDocument.insert_many(opportunities)
            print(f"[Discovery] Inserted {len(opportunities)} opportunities")
        
        return opportunities

    def _build_opportunity(
        self,
        measure: dict,
        mapping: dict,
        tariff_index: dict,
        sub_icb_ods: str,
        tenant_id: str,
    ) -> OpportunityDocument | None:
        
        actual_cost = measure.get("actual_cost", 0) or 0
        if actual_cost <= 0:
            return None
        
        numerator   = measure.get("numerator", 0) or 0
        denominator = measure.get("denominator", 1) or 1
        
        # Base estimate: 25% saving on current spend
        base_saving = actual_cost * 0.25
        patients    = max(int(numerator / 12), 1)  # monthly → annual items
        
        # Refine with Drug Tariff prices if available
        exp_prefix    = mapping["expensive_bnf"][:9]   # chemical level
        target_prefix = mapping["target_bnf"][:9]
        
        exp_price    = tariff_index.get(exp_prefix)     # pence per unit
        target_price = tariff_index.get(target_prefix)
        
        if exp_price and target_price and exp_price > target_price:
            unit_saving  = (exp_price - target_price) / 100   # pence → pounds
            annual_saving = unit_saving * patients * 28        # 28-day supply cycle
        else:
            annual_saving = base_saving
        
        if annual_saving <= 0:
            return None
        
        ease_labels = {5: "Simple", 4: "Easy", 3: "Moderate", 2: "Complex", 1: "High Effort"}
        
        return OpportunityDocument(
            tenant_id=tenant_id,
            icb_ods="QF7",
            sub_icb_ods=sub_icb_ods,
            pcn_ods=None,
            practice_ods=None,
            org_level="sub_icb",
            workstream=mapping["workstream"],
            status="identified",
            expensive_drug_name=mapping["expensive_drug"],
            target_drug_name=mapping["target_drug"],
            current_expensive_bnf=mapping["expensive_bnf"],
            target_cheap_bnf=mapping["target_bnf"],
            bnf_section_code=mapping["bnf_section"],
            bnf_chapter=mapping["bnf_chapter"],
            opportunity_type=mapping["opportunity_type"],
            annual_saving=round(annual_saving, 2),
            expensive_unit_cost=round((exp_price or 0) / 100, 4),
            cheap_unit_cost=round((target_price or 0) / 100, 4),
            estimated_patients=patients,
            ease_score=mapping["ease_score"],
            ease_label=ease_labels[mapping["ease_score"]],
            hard_exclusions=mapping.get("hard_exclusions", []),
            soft_exclusions=mapping.get("soft_exclusions", []),
            clinical_guidance=mapping.get("clinical_guidance", ""),
            nice_reference=mapping.get("nice_reference", ""),
            patient_letter_summary=mapping.get("patient_letter_summary", ""),
            is_on_nhse_16=mapping.get("is_on_nhse_16", False),
            gates_passed=self._count_gates(mapping),
            supply_risk="low",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    def _count_gates(self, mapping: dict) -> int:
        """Estimate how many clinical safety checks this switch passes"""
        gates = 0
        if mapping.get("nice_reference"):  gates += 1  # NICE guideline
        if mapping.get("is_on_nhse_16"):   gates += 1  # NHS England QIPP 16
        if mapping["opportunity_type"] == "ghost_generic": gates += 2  # simpler
        if mapping["ease_score"] >= 4:     gates += 1  # easy switch
        return min(gates, 5)

    async def _build_tariff_index(self) -> dict[str, float]:
        """
        Returns {bnf_code_9char: cheapest_price_pence}
        Uses MongoDB tariff_prices collection (populated by sync_tariff_prices task)
        """
        docs = await TariffPriceDocument.find_all().to_list()
        index = {}
        for doc in docs:
            key = doc.bnf_code[:9] if len(doc.bnf_code) >= 9 else doc.bnf_code
            if key not in index or doc.price_pence < index[key]:
                index[key] = doc.price_pence
        return index
```

---

## 5. Your MongoDB Models (You Own — You Set Up Atlas)

**File:** `backend/app/mongo_models/` (all 12 files)

You are responsible for all MongoDB Beanie document models since you set up Atlas.

```python
# backend/app/mongo_models/tariff_price.py
from beanie import Document
from pydantic import Field

class TariffPriceDocument(Document):
    vmpp_id:            str = ""
    vmpp:               str = ""        # "Atorvastatin 20mg tablets x28"
    product:            str = ""        # "Atorvastatin"
    bnf_code:           str = ""        # Used for prefix matching
    tariff_category:    str = ""        # A / C / M / E
    price_pence:        int = 0
    pack_size:          float = 28.0
    price_per_unit_pence: float = 0.0  # Derived: price_pence / pack_size
    date:               str = ""        # "2025-12"
    concession:         bool = False

    class Settings:
        name = "tariff_prices"
        indexes = ["bnf_code", "product", "date", "tariff_category", "concession"]
```

Your MongoDB Atlas connection string goes in `.env`:
```env
MONGODB_URI=mongodb+srv://YOUR_USER:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/qipp_patients
```

The `connect_mongodb()` call in `backend/app/mongodb.py` handles everything else — your partner writes that file.

---

## 6. Your Celery Tasks (You Own)

**File:** `backend/app/tasks/data_sync.py`

```python
# backend/app/tasks/data_sync.py
import asyncio
from app.tasks.celery_app import celery_app
from app.config import settings

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def sync_tariff_prices(self):
    """
    Daily: Download Drug Tariff from OpenPrescribing → MongoDB
    Scheduled: 03:00 daily
    """
    async def _run():
        from app.services.openprescribing_service import OpenPrescribingService
        from app.mongo_models.tariff_price import TariffPriceDocument
        
        op = OpenPrescribingService(scrapfly_key=settings.SCRAPFLY_API_KEY)
        records = await op.get_tariff_prices(force=True)
        
        # Clear old prices
        await TariffPriceDocument.delete_all()
        
        # Insert new prices in batches
        docs = [TariffPriceDocument(**r) for r in records]
        batch_size = 500
        for i in range(0, len(docs), batch_size):
            await TariffPriceDocument.insert_many(docs[i:i+batch_size])
        
        print(f"[Tariff Sync] Inserted {len(docs)} records")
        return len(docs)
    
    try:
        return asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3)
def discover_opportunities(self, sub_icb_ods: str = "02P", tenant_id: str = None):
    """
    Daily: Run opportunity discovery for South Yorkshire
    Scheduled: 02:30 daily
    """
    async def _run():
        from app.services.openprescribing_service import OpenPrescribingService
        from app.services.opportunity_discovery import OpportunityDiscoveryEngine
        from app.config import settings
        
        op = OpenPrescribingService(scrapfly_key=settings.SCRAPFLY_API_KEY)
        engine = OpportunityDiscoveryEngine(op)
        
        _tenant_id = tenant_id or "south-yorkshire-tenant-id"
        
        results = await engine.discover_for_sub_icb(
            sub_icb_ods=sub_icb_ods,
            tenant_id=_tenant_id,
        )
        return {"opportunities_created": len(results)}
    
    try:
        return asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc)
```

**Opportunity tasks:**
```python
# backend/app/tasks/opportunity_tasks.py

@celery_app.task(bind=True)
def trigger_discovery_for_practice(self, practice_ods: str, tenant_id: str):
    """On-demand discovery for a single practice"""
    async def _run():
        from app.services.openprescribing_service import OpenPrescribingService
        from app.services.opportunity_discovery import OpportunityDiscoveryEngine
        
        op = OpenPrescribingService(scrapfly_key=settings.SCRAPFLY_API_KEY)
        engine = OpportunityDiscoveryEngine(op)
        results = await engine.discover_for_sub_icb(
            sub_icb_ods="02P", tenant_id=tenant_id
        )
        return len(results)
    return asyncio.run(_run())
```

---

## 7. Your AI Layer — Gemini Integration (You Own)

**Files:** `backend/app/ai/gemini_client.py`, `backend/app/ai/guardrails.py`, `backend/app/routers/ai_search.py`

```python
# backend/app/ai/gemini_client.py
from google import genai
import json, re
from app.config import settings

_client = None

def get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client

async def generate_json(prompt: str) -> dict | list:
    client = get_client()
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL_NAME,  # "gemini-2.0-flash"
        contents=prompt
    )
    text = re.sub(r"```json\s*|```\s*", "", response.text).strip()
    return json.loads(text)

async def generate_text(prompt: str) -> str:
    client = get_client()
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL_NAME,
        contents=prompt
    )
    return response.text
```

**AI Patient Search endpoint** (this is the "AI patient search" page in the PoC):
```python
# backend/app/routers/ai_search.py
from fastapi import APIRouter, Depends
from app.ai.gemini_client import generate_json
from app.ai.guardrails import validate_ai_output

router = APIRouter(prefix="/ai", tags=["ai"])

AI_SEARCH_PROMPT = """
You are a clinical pharmacist AI assistant for South Yorkshire ICB (NHS, UK).
Context: ~650,000 registered patients, 105 GP practices.
ICB ODS: QF7, Sub-ICB: 02P.

The pharmacist query is: {query}

Return ONLY valid JSON (no markdown fences) in exactly this schema:
{{
  "bnf_codes": ["0212000B0AA"],
  "target_drug": "Generic Atorvastatin",
  "expensive_drug": "Branded Atorvastatin",
  "inclusion_criteria": [
    {{"criterion": "Patient on branded atorvastatin", "snomed_code": "372912004"}}
  ],
  "exclusion_criteria": [
    {{"criterion": "Documented statin intolerance", "severity": "mandatory"}},
    {{"criterion": "Specialist recommendation for brand", "severity": "mandatory"}},
    {{"criterion": "Patient preference documented", "severity": "soft"}}
  ],
  "estimated_icb_patients": 450,
  "emis_query": "Medicines Manager search\\nINCLUDE: ...",
  "systmone_query": "Protocol search\\nActive medication: ...",
  "search_summary": "One line summary of what was found",
  "annual_saving": 45000,
  "clinical_caveat": "Must be reviewed by qualified pharmacist before actioning"
}}
"""

@router.post("/patient-search")
async def ai_patient_search(
    query: str,
    current_user = Depends(get_current_active_user)
):
    prompt = AI_SEARCH_PROMPT.format(query=query)
    result = await generate_json(prompt)
    
    # Safety check
    import json as json_lib
    result_str = json_lib.dumps(result)
    guardrail = validate_ai_output(result_str)
    if not guardrail.safe:
        return {"error": "AI output failed safety check", "flagged": guardrail.flagged_phrases}
    
    # Log to audit trail (PostgreSQL)
    # ... (add AiDecisionAudit record here)
    
    return result
```

---

## 8. Your MongoDB Connection File (Coordinate with Your Partner)

Your partner writes `backend/app/mongodb.py` but uses YOUR Atlas connection string:

```python
# backend/app/mongodb.py
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

# Import all 12 document models (you write all of these)
from app.mongo_models.patient import PatientDocument
from app.mongo_models.opportunity import OpportunityDocument
from app.mongo_models.medication import MedicationDocument
from app.mongo_models.tariff_price import TariffPriceDocument
from app.mongo_models.icb_report import ICBReportDocument
from app.mongo_models.prescribing_data import PrescribingDataDocument
from app.mongo_models.drug_class import DrugClassDocument
from app.mongo_models.switchback import SwitchbackEventDocument
from app.mongo_models.supply_risk import SupplyRiskDocument
from app.mongo_models.ai_ruleset import AIRuleSetDocument
from app.mongo_models.formulary import FormularyDocument
from app.mongo_models.price_snapshot import PriceSnapshotDocument

motor_client: AsyncIOMotorClient | None = None

async def connect_mongodb(uri: str) -> None:
    global motor_client
    motor_client = AsyncIOMotorClient(uri)
    db = motor_client["qipp_patients"]
    await init_beanie(database=db, document_models=[
        PatientDocument, OpportunityDocument, MedicationDocument,
        TariffPriceDocument, ICBReportDocument, PrescribingDataDocument,
        DrugClassDocument, SwitchbackEventDocument, SupplyRiskDocument,
        AIRuleSetDocument, FormularyDocument, PriceSnapshotDocument,
    ])
    print("[MongoDB] Connected and Beanie initialized")

async def disconnect_mongodb() -> None:
    if motor_client:
        motor_client.close()
```

---

## 9. Your Sprint Tasks — Week by Week

### Sprint 1 (Week 1–2): You Own These

- [ ] Share MongoDB Atlas connection string with your partner (Day 1)
- [ ] Share Scrapfly API key with your partner (Day 1)
- [ ] Clone the repo (your partner creates it)
- [ ] Write ALL 12 Beanie MongoDB document models
- [ ] Write `backend/app/services/scrapfly_cache.py`
- [ ] Write `backend/app/services/openprescribing_service.py` (all 6 endpoints)
- [ ] Write `backend/app/config.py` (Pydantic Settings)
- [ ] Test: Can you call OpenPrescribing for SY (02P) and get spending data back?

### Sprint 2 (Week 3–4): You Own These

- [ ] Write `backend/app/services/opportunity_discovery.py` (full engine, all 7 mappings)
- [ ] Write `backend/app/tasks/data_sync.py` (sync_tariff_prices, discover_opportunities)
- [ ] Write `backend/app/tasks/opportunity_tasks.py`
- [ ] Write `backend/app/routers/opportunities.py` (list, filter, approve, sync trigger)
- [ ] **Test:** Run discovery for 02P → does it generate 7 opportunities with real £ values?
- [ ] Test: Drug Tariff sync loads ~12,000 records to MongoDB

### Sprint 3 (Week 5–6): You Own These

- [ ] Write `backend/app/ai/gemini_client.py`
- [ ] Write `backend/app/ai/guardrails.py`
- [ ] Write `backend/app/routers/ai_search.py` (patient search + free-text opportunity search)
- [ ] Write action sheet generation endpoint (Gemini prompt)
- [ ] Write patient letter generation endpoint (Gemini prompt)
- [ ] **Test:** AI patient search for "statins" returns a usable EMIS query

### Sprint 4–6: Frontend Support + Polish

- [ ] Help wire up AI search page on frontend
- [ ] Review opportunity register data and fix any edge cases
- [ ] Supply risk monitoring (check concessions endpoint daily)
- [ ] ePACT2 CSV upload endpoint for realized savings
- [ ] Price per unit analysis endpoint (feeds ghost generic detection page)
- [ ] Help with deployment on DigitalOcean

---

## 10. Coordination Protocol with Your Partner

**Day 1 — Share immediately:**
```
MongoDB Atlas URI → send to your partner for their .env
Scrapfly API key → send to your partner for their .env
```

**Git workflow:**
```bash
# Main branches:
main       → production only
develop    → integration (both merge here)
victor/feature-name → your feature branches

# Daily:
git checkout develop
git pull origin develop
git checkout -b victor/opportunity-engine
# ... build
git add .
git commit -m "feat: implement full opportunity discovery engine with 7 workstreams"
git push origin victor/opportunity-engine
# Open PR to develop
```

**What your partner delivers to you:**
1. Working FastAPI server on localhost:8000
2. Admin JWT token so you can test your endpoints
3. Supabase PostgreSQL connection string
4. Working `get_current_active_user` dependency (so your routers have auth)

**What you deliver to your partner:**
1. MongoDB Atlas URI (immediately — Day 1)
2. Scrapfly API key (immediately — Day 1)
3. Populated `opportunities` collection (so their dashboard has real data)
4. Populated `tariff_prices` collection (so their tariff pages work)
5. All 12 MongoDB Beanie models (so their `mongodb.py` can init Beanie)

---

## 11. macOS-Specific Notes

```bash
# macOS Celery works normally (unlike Windows — no --pool=solo needed)
celery -A app.tasks.celery_app worker --loglevel=info

# Python virtual environment activation on macOS
source qipp_venv/bin/activate

# Redis on macOS
brew services start redis
redis-cli ping  # should return PONG

# If you get SSL certificate errors with httpx:
pip install certifi
# Usually not needed on macOS, but add if you see SSL errors

# MongoDB compass (GUI for your Atlas cluster)
# Download from mongodb.com/products/tools/compass — great for debugging
# Connect with your Atlas URI → see your collections visually

# Check your Scrapfly credit usage
# https://app.scrapfly.io/dashboard → monitor monthly credits
# Each fresh fetch = 1 credit. With 24h cache, 1000/month is plenty.
```

---

## 12. Testing Your Services Standalone

Before the full backend is running, you can test your services independently:

```python
# test_op_service.py (run from backend/ directory)
import asyncio
from app.services.openprescribing_service import OpenPrescribingService
from app.config import settings

async def test():
    op = OpenPrescribingService(scrapfly_key=settings.SCRAPFLY_API_KEY)
    
    # Test 1: Get SY statin spending
    spending = await op.get_spending_by_org("0212000", "practice", "02P")
    print(f"Statin spending records: {len(spending)}")
    if spending:
        print(f"Sample: {spending[0]}")
    
    # Test 2: Get SY measures (triggers opportunity generation)
    measures = await op.get_measures_for_org("02P", "sub_icb")
    measure_ids = [m["measure"] for m in measures.get("measures", [])]
    print(f"Measures available: {measure_ids}")
    
    # Test 3: Drug Tariff (small sample)
    tariff = await op.get_tariff_prices()
    print(f"Tariff records: {len(tariff)}")
    print(f"Sample: {tariff[0] if tariff else 'none'}")

asyncio.run(test())
```

```bash
# Run from backend/ directory
source qipp_venv/bin/activate
python test_op_service.py
```

---

*Victor's guide ends here. See your partner's file for their responsibilities.*
*Build guide version: 1.0 | March 2026 | QIPP South Yorkshire*
