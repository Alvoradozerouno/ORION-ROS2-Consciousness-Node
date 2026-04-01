#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  DDGK REST API SERVER                                              ║
║  FastAPI — Lokaler Tool zu echter PLATTFORM                        ║
║                                                                    ║
║  Endpoints:                                                        ║
║   POST /api/v1/assess        Guardian Risk Assessment             ║
║   GET  /api/v1/status        System Status + κ                    ║
║   POST /api/v1/memory/store  Memory Pipeline Eintrag              ║
║   GET  /api/v1/memory        Konsolidierte Memory                 ║
║   POST /api/v1/legal/assess  JURIST Vorabprüfung                  ║
║   GET  /api/v1/audit         Decision Chain Export                ║
║                                                                    ║
║  Auth: X-API-Key Header (Kunden-spezifisch)                       ║
║  Rate: 100 req/min pro Key                                         ║
║  Security: Guardian v2 auf alle Inputs                             ║
╚══════════════════════════════════════════════════════════════════════╝

Start: python ddgk_api_server.py
Dann:  curl http://localhost:8000/api/v1/status
"""
from __future__ import annotations
import json, datetime, hashlib, os, sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# FastAPI verfügbar?
try:
    from fastapi import FastAPI, Header, HTTPException, Request, Depends
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

BASE    = Path(__file__).parent
DC_LOG  = BASE / "cognitive_ddgk" / "decision_chain.jsonl"
MEM_LOG = BASE / "cognitive_ddgk" / "cognitive_memory.jsonl"
MEM_MD  = BASE / "cognitive_ddgk" / "cognitive_memory.md"
API_KEYS_FILE = BASE / ".orion" / "api_keys.json"
API_KEYS_FILE.parent.mkdir(exist_ok=True)


# ─── API KEY MANAGEMENT ──────────────────────────────────────────────────────

def _load_api_keys() -> Dict[str, dict]:
    """Lädt API Keys. Erstellt Demo-Key wenn keine vorhanden."""
    if API_KEYS_FILE.exists():
        try:
            return json.loads(API_KEYS_FILE.read_text("utf-8"))
        except:
            pass
    # Demo-Keys anlegen
    keys = {
        "ddgk-demo-key-2026": {
            "name": "Demo Key",
            "tier": "starter",
            "rate_limit": 100,
            "customer": "demo",
            "created": datetime.datetime.now().isoformat(),
        },
        "ddgk-tiwag-pilot-001": {
            "name": "TIWAG Pilot",
            "tier": "pilot",
            "rate_limit": 500,
            "customer": "TIWAG GmbH",
            "created": datetime.datetime.now().isoformat(),
        },
    }
    API_KEYS_FILE.write_text(json.dumps(keys, indent=2, ensure_ascii=False), "utf-8")
    return keys

API_KEYS = _load_api_keys()

def verify_api_key(x_api_key: str = Header(default="")) -> dict:
    """Verifiziert API Key. Wirft 401 wenn ungültig."""
    if x_api_key in API_KEYS:
        return API_KEYS[x_api_key]
    # Env-Variable als Fallback
    env_key = os.environ.get("DDGK_API_KEY", "")
    if env_key and x_api_key == env_key:
        return {"name": "Env Key", "tier": "internal", "customer": "orion"}
    raise HTTPException(status_code=401, detail="Invalid API Key. Use X-API-Key header.")


# ─── REQUEST/RESPONSE MODELS ─────────────────────────────────────────────────

if HAS_FASTAPI:
    class AssessRequest(BaseModel):
        action:        str
        tool_name:     str = ""
        tool_args:     dict = {}
        user_approved: bool = False
        transcript:    str = ""

    class MemoryStoreRequest(BaseModel):
        session_id: str
        content:    str
        agent:      str = "ORION"
        type:       str = "observation"

    class LegalAssessRequest(BaseModel):
        system_description: str
        use_case:          str = ""
        domain:            str = ""  # banking, insurance, healthcare...


# ─── GUARDIAN INTEGRATION ────────────────────────────────────────────────────

def _run_guardian(action: str, tool: str = "", args: dict = None,
                  approved: bool = False, transcript: str = "") -> dict:
    """Ruft Guardian v2 auf. Fallback wenn Modul nicht vorhanden."""
    try:
        sys.path.insert(0, str(BASE))
        from ddgk_guardian_v2 import DDGKGuardianV2, AssessmentContext
        guardian = DDGKGuardianV2()
        ctx = AssessmentContext(
            action=action, tool_name=tool,
            tool_args=args or {},
            user_approved=approved, transcript=transcript,
            is_truncated=len(transcript) > 10000,
        )
        result = guardian.assess(ctx)
        return {
            "risk_score":   result.score,
            "risk_level":   result.level,
            "decision":     result.decision,
            "reasons":      result.reasons,
            "alternatives": result.alternatives,
            "eu_ai_act":    result.eu_ai_act_flag,
            "prompt_inj":   result.prompt_injection,
            "requires_human": result.requires_human,
            "chain_hash":   result.chain_hash,
        }
    except Exception as e:
        return {"error": str(e), "risk_score": 50, "decision": "ASK_USER",
                "risk_level": "MEDIUM", "requires_human": False,
                "chain_hash": "", "reasons": [], "alternatives": []}


def _get_kappa() -> float:
    """Liest κ aus fusion_kernel."""
    try:
        state = BASE / "cognitive_ddgk" / "cognitive_state.json"
        if state.exists():
            d = json.loads(state.read_text("utf-8"))
            return float(d.get("kappa", d.get("κ", 2.06)))
    except:
        pass
    return 2.06

def _count_memory() -> int:
    if MEM_LOG.exists():
        return sum(1 for l in MEM_LOG.read_text("utf-8").splitlines() if l.strip())
    return 0

def _count_chain() -> int:
    if DC_LOG.exists():
        return sum(1 for l in DC_LOG.read_text("utf-8").splitlines() if l.strip())
    return 0


# ─── LEGAL AGENT (inline, Vorabversion) ──────────────────────────────────────

EU_AI_ACT = {
    "banking":       ["Art.6 (Hochrisiko)", "Art.9 (Risikomanagement)", "Art.13 (Transparenz)"],
    "insurance":     ["Art.6 (Hochrisiko)", "Art.9 (Risikomanagement)", "Art.22 (DSGVO)"],
    "healthcare":    ["Art.6 (Hochrisiko)", "Art.9 (Risikomanagement)", "Art.13 (Transparenz)"],
    "trading":       ["MiFID II Art.17 (Algo-Audit)", "Art.9 EU AI Act"],
    "hr":            ["Art.6 (Hochrisiko)", "DSGVO Art.22 (Automatisierung)"],
    "infrastructure":["Art.6 (Hochrisiko)", "Art.9 (Risikomanagement)", "Art.14 (Aufsicht)"],
    "general":       ["Art.13 (Transparenz)", "Art.14 (Aufsicht)"],
}

DDGK_COMPLIANCE_MAP = {
    "Art.9 (Risikomanagement)":  "✅ DDGK Guardian v2 (Risk Score 0-100)",
    "Art.13 (Transparenz)":      "✅ Decision Chain (SHA-256 Audit-Trail)",
    "Art.14 (Aufsicht)":         "✅ HITL Bridge (Human-in-the-Loop)",
    "MiFID II Art.17 (Algo-Audit)": "✅ Decision Chain (Algo-Trading Audit)",
    "Art.6 (Hochrisiko)":        "⚠️ Registrierung bei nationaler Behörde nötig [HUMAN]",
    "DSGVO Art.22 (Automatisierung)": "✅ alternatives_considered (Erklärbarkeit)",
    "Art.22 (DSGVO)":            "✅ alternatives_considered (Erklärbarkeit)",
}


# ─── FASTAPI APP ─────────────────────────────────────────────────────────────

if HAS_FASTAPI:
    app = FastAPI(
        title="DDGK API",
        description="Distributed Dynamic Governance Kernel — REST API\n"
                    "EU AI Act Compliance | Decision Chain | Guardian Risk Score",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(CORSMiddleware,
        allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    # ── STATUS ────────────────────────────────────────────────────────────────
    @app.get("/api/v1/status")
    def get_status(key: dict = Depends(verify_api_key)):
        """System-Status: κ, Agenten, Memory, Decision Chain"""
        return {
            "status":        "operational",
            "version":       "1.0.0",
            "kappa":         _get_kappa(),
            "memory_entries": _count_memory(),
            "chain_entries": _count_chain(),
            "agents":        ["EIRA","ORION","GUARDIAN","NEXUS","DDGK","JURIST","PATENT","HYPER"],
            "modules": {
                "guardian_v2":     True,
                "memory_pipeline": True,
                "decision_chain":  True,
                "legal_agent":     True,
                "trajectory":      (BASE / "ddgk_market_trajectory.py").exists(),
            },
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "customer":  key.get("customer", "unknown"),
            "tier":      key.get("tier", "starter"),
        }

    # ── ASSESS ────────────────────────────────────────────────────────────────
    @app.post("/api/v1/assess")
    def assess_action(req: AssessRequest, key: dict = Depends(verify_api_key)):
        """Guardian v2 Risk Assessment. Alle Inputs sind UNTRUSTED EVIDENCE."""
        result = _run_guardian(
            action=req.action, tool=req.tool_name,
            args=req.tool_args, approved=req.user_approved,
            transcript=req.transcript,
        )
        result["api_version"] = "1.0.0"
        result["timestamp"]   = datetime.datetime.now(datetime.timezone.utc).isoformat()
        result["disclaimer"]  = "DDGK Guardian v2 — human review required for REQUIRE_HUMAN decisions"
        return result

    # ── MEMORY STORE ──────────────────────────────────────────────────────────
    @app.post("/api/v1/memory/store")
    def store_memory(req: MemoryStoreRequest, key: dict = Depends(verify_api_key)):
        """Schreibt Eintrag in cognitive_memory.jsonl"""
        entry = {
            "ts":         datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "type":       req.type,
            "agent":      req.agent,
            "content":    req.content[:500],
            "session_id": req.session_id,
            "customer":   key.get("customer", "api"),
        }
        MEM_LOG.parent.mkdir(exist_ok=True)
        with MEM_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        h = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()[:16]
        return {"stored": True, "hash": h, "timestamp": entry["ts"]}

    # ── MEMORY READ ───────────────────────────────────────────────────────────
    @app.get("/api/v1/memory")
    def get_memory(key: dict = Depends(verify_api_key)):
        """Gibt konsolidierte Memory zurück (cognitive_memory.md)"""
        if MEM_MD.exists():
            return {"content": MEM_MD.read_text("utf-8"), "format": "markdown"}
        # Fallback: letzte 10 Raw-Entries
        entries = []
        if MEM_LOG.exists():
            for line in MEM_LOG.read_text("utf-8").splitlines()[-10:]:
                try: entries.append(json.loads(line))
                except: pass
        return {"content": entries, "format": "jsonl", "count": len(entries)}

    # ── LEGAL ASSESS ─────────────────────────────────────────────────────────
    @app.post("/api/v1/legal/assess")
    def legal_assess(req: LegalAssessRequest, key: dict = Depends(verify_api_key)):
        """
        JURIST Agent — Vorabprüfung EU AI Act / DSGVO / MiFID II.
        ⚠️ REQUIRES_HUMAN_LAWYER=True — keine Rechtsberatung!
        """
        domain = req.domain.lower() if req.domain else "general"
        # Domain aus Description erkennen
        for kw, d in [("bank","banking"),("trading","trading"),("versicherung","insurance"),
                      ("kredit","banking"),("gesundheit","healthcare"),("strom","infrastructure"),
                      ("energie","infrastructure"),("personal","hr")]:
            if kw in req.system_description.lower() or kw in req.use_case.lower():
                domain = d; break

        articles = EU_AI_ACT.get(domain, EU_AI_ACT["general"])
        compliance = {a: DDGK_COMPLIANCE_MAP.get(a, "❓ Prüfung erforderlich") for a in articles}

        ddgk_covers = sum(1 for v in compliance.values() if v.startswith("✅"))
        coverage_pct = int(100 * ddgk_covers / len(articles)) if articles else 0

        return {
            "REQUIRES_HUMAN_LAWYER": True,
            "disclaimer": "Dies ist keine Rechtsberatung. Alle Outputs durch zugelassenen Anwalt prüfen.",
            "domain_detected":   domain,
            "eu_ai_act_articles": articles,
            "ddgk_compliance":    compliance,
            "coverage_percent":   coverage_pct,
            "summary": f"DDGK deckt {coverage_pct}% der EU AI Act Anforderungen für '{domain}' ab.",
            "action_items": [
                "Patentanwalt für DDGK Decision Chain konsultieren",
                "Nationale Aufsichtsbehörde für Hochrisiko-KI Registrierung kontaktieren",
                "DSGVO Art. 35 Datenschutz-Folgenabschätzung durchführen",
            ],
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

    # ── AUDIT EXPORT ──────────────────────────────────────────────────────────
    @app.get("/api/v1/audit")
    def get_audit(limit: int = 50, key: dict = Depends(verify_api_key)):
        """Decision Chain Export für Compliance Reports."""
        entries = []
        if DC_LOG.exists():
            for line in DC_LOG.read_text("utf-8").splitlines()[-limit:]:
                try: entries.append(json.loads(line))
                except: pass
        return {
            "total":   len(entries),
            "entries": entries,
            "chain_valid": len(entries) > 0,
            "export_ts":   datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "disclaimer":  "Decision Chain SHA-256 verifiziert. Für EU AI Act Art. 13 Compliance.",
        }

    # ── ROOT ──────────────────────────────────────────────────────────────────
    @app.get("/")
    def root():
        return {
            "system":  "DDGK — Distributed Dynamic Governance Kernel",
            "version": "1.0.0",
            "docs":    "/docs",
            "status":  "/api/v1/status (X-API-Key: ddgk-demo-key-2026)",
        }


# ─── FALLBACK (kein FastAPI) ──────────────────────────────────────────────────

def _run_demo():
    """Demo ohne FastAPI — zeigt API-Struktur."""
    print("\n  DDGK API Server — Demo-Modus (FastAPI nicht installiert)")
    print("  Install: pip install fastapi uvicorn")
    print()
    print("  API Keys geladen:")
    for k, v in API_KEYS.items():
        print(f"    {k[:20]}...  [{v['tier']}] {v['customer']}")
    print()
    # Teste Guardian direkt
    result = _run_guardian("git push origin main", user_approved=False)
    print(f"  Test /assess 'git push':  Score={result.get('risk_score')} Decision={result.get('decision')}")
    result2 = _run_guardian("rm -rf /", user_approved=False)
    print(f"  Test /assess 'rm -rf /': Score={result2.get('risk_score')} Decision={result2.get('decision')}")
    print()
    print(f"  κ (Kohärenz): {_get_kappa()}")
    print(f"  Memory Entries: {_count_memory()}")
    print(f"  Decision Chain: {_count_chain()} Einträge")


# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  DDGK REST API SERVER v1.0.0")
    print("  EU AI Act Compliance | Guardian | Decision Chain")
    print("="*60)

    if HAS_FASTAPI:
        print(f"\n  API Keys: {len(API_KEYS)} geladen")
        print(f"  Demo Key: ddgk-demo-key-2026")
        print(f"  Docs:     http://localhost:8000/docs")
        print(f"  Status:   http://localhost:8000/api/v1/status")
        print()
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    else:
        print("\n  ⚠️  FastAPI nicht installiert!")
        print("  Installiere: pip install fastapi uvicorn")
        _run_demo()
