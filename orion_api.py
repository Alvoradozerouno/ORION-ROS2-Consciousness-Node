#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║  ORION FAST API — DDGK + HyperAgent als SaaS REST API      ║
║  Start: python orion_api.py                                  ║
║  Docs:  http://localhost:8000/docs                           ║
║  Port:  8000 (lokal) | ngrok tunnel für öffentlich           ║
╚══════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import os, sys, json, hashlib, datetime, math
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

try:
    from fastapi import FastAPI, HTTPException, Header
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    FASTAPI_OK = True
except ImportError:
    print("pip install fastapi uvicorn")
    FASTAPI_OK = False
    sys.exit(1)

# ── APP ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="ORION DDGK API",
    description=(
        "Deterministic Decision Governance Kernel — REST API\n\n"
        "κ = 2.060 + 0.930·ln(N)·φ̄\n\n"
        "Every decision: ALLOW | DENY | ABSTAIN | REQUIRE_HUMAN | WARN\n\n"
        "Paper: https://zenodo.org/record/14999136\n"
        "GitHub: https://github.com/Alvoradozerouno/ddgk"
    ),
    version="1.0.0",
    contact={"name": "Paradoxon AI", "url": "https://paradoxonai.at", "email": "elisabethsteurer@paradoxonai.at"},
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── MODELS ───────────────────────────────────────────────────────────

class DecisionRequest(BaseModel):
    question:              str
    alternatives:          list[str] = []
    trust_levels:          list[float] = []
    require_human_on_deny: bool = True

class KappaRequest(BaseModel):
    N:   int   = 3
    phi: float = 0.80

class AuditEntry(BaseModel):
    decision:    str
    question:    str
    kappa:       float
    proof_hash:  str
    timestamp:   str

# ── DDGK KERN ────────────────────────────────────────────────────────

def compute_kappa(N: int, phi: float) -> float:
    """κ = 2.060 + 0.930·ln(N)·φ̄"""
    if N < 1: N = 1
    return round(2.060 + 0.930 * math.log(N) * phi, 4)

def make_decision(kappa: float, require_human: bool = True) -> dict:
    if kappa >= 70:
        return {"decision": "ALLOW",          "symbol": "✓", "color": "green"}
    elif kappa >= 50:
        if require_human:
            return {"decision": "REQUIRE_HUMAN", "symbol": "!", "color": "orange"}
        return {"decision": "WARN",           "symbol": "~", "color": "yellow"}
    elif kappa >= 0:
        return {"decision": "DENY",           "symbol": "✗", "color": "red"}
    else:
        return {"decision": "ABSTAIN",        "symbol": "?", "color": "gray"}

def sha_proof(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

def log_decision(entry: dict):
    log_file = BASE / "cognitive_ddgk" / "decision_chain.jsonl"
    log_file.parent.mkdir(exist_ok=True)
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# ── ENDPOINTS ─────────────────────────────────────────────────────────

@app.get("/", tags=["Status"])
def root():
    """ORION DDGK API — Status"""
    return {
        "name":    "ORION DDGK API",
        "version": "1.0.0",
        "status":  "ONLINE",
        "formula": "κ = 2.060 + 0.930·ln(N)·φ̄",
        "docs":    "/docs",
        "paper":   "https://zenodo.org/record/14999136",
    }

@app.get("/health", tags=["Status"])
def health():
    """Health Check für Monitoring"""
    return {"status": "OK", "ts": datetime.datetime.now().isoformat()}


@app.post("/decide", tags=["Decision"])
def decide(req: DecisionRequest):
    """
    Hauptendpunkt: DDGK-Entscheidung für eine Frage.

    - **question**: Die zu entscheidende Frage
    - **alternatives**: Liste der geprüften Alternativen (mehr = höheres κ)
    - **trust_levels**: Trust-Level pro Alternative (0-100)
    - **require_human_on_deny**: Eskaliert DENY zu REQUIRE_HUMAN

    Beispiel:
    ```json
    {
      "question": "Soll ich diesen Code deployen?",
      "alternatives": ["deploy now", "test first", "review needed"],
      "trust_levels": [85.0, 90.0, 95.0]
    }
    ```
    """
    N   = max(len(req.alternatives), 1)
    phi = (sum(req.trust_levels) / len(req.trust_levels) / 100.0) if req.trust_levels else 0.80
    kappa = compute_kappa(N, phi)
    dec   = make_decision(kappa, req.require_human_on_deny)

    proof = sha_proof({
        "question": req.question,
        "N": N, "phi": phi, "kappa": kappa,
        "decision": dec["decision"],
        "ts": datetime.datetime.now().isoformat(),
    })

    result = {
        "ddgk": {
            "decision":    dec["decision"],
            "symbol":      dec["symbol"],
            "kappa":       kappa,
            "N":           N,
            "phi_bar":     round(phi, 4),
            "proof_hash":  proof[:24],
        },
        "question":     req.question,
        "alternatives": req.alternatives,
        "formula":      f"κ = 2.060 + 0.930·ln({N})·{phi:.3f} = {kappa}",
        "timestamp":    datetime.datetime.now().isoformat(),
    }

    log_decision({
        "decision":   dec["decision"], "question": req.question,
        "kappa": kappa, "N": N, "phi": phi,
        "proof": proof[:24], "ts": datetime.datetime.now().isoformat(),
        "source": "api"
    })

    return result


@app.post("/kappa", tags=["Formula"])
def kappa_endpoint(req: KappaRequest):
    """
    Berechnet den κ-Wert direkt.

    - **N**: Anzahl der betrachteten Alternativen
    - **phi**: Mittlerer Trust-Level (0.0 - 1.0)
    """
    kappa = compute_kappa(req.N, req.phi)
    dec   = make_decision(kappa)
    return {
        "kappa":    kappa,
        "N":        req.N,
        "phi":      req.phi,
        "decision": dec["decision"],
        "symbol":   dec["symbol"],
        "formula":  f"κ = 2.060 + 0.930·ln({req.N})·{req.phi} = {kappa}",
    }


@app.get("/audit", tags=["Audit"])
def get_audit(limit: int = 20):
    """Gibt die letzten Decision Chain Einträge zurück."""
    log_file = BASE / "cognitive_ddgk" / "decision_chain.jsonl"
    if not log_file.exists():
        return {"entries": [], "total": 0}
    lines = [l for l in log_file.read_text("utf-8", errors="replace").splitlines() if l.strip()]
    entries = []
    for l in lines[-limit:]:
        try:
            entries.append(json.loads(l))
        except:
            pass
    return {"entries": list(reversed(entries)), "total": len(lines)}


@app.get("/status", tags=["Status"])
def system_status():
    """Vollständiger DDGK-System-Status."""
    OK_BASE = Path(__file__).parent.parent / "OrionKernel"
    gate_db = OK_BASE / "ddgk_meta" / "evolution_baseline.json"
    cal     = OK_BASE / "ddgk_meta" / "temporal_calendar.json"
    mem     = BASE / "cognitive_ddgk" / "cognitive_memory.jsonl"
    dc      = BASE / "cognitive_ddgk" / "decision_chain.jsonl"

    gate_data = json.loads(gate_db.read_text()) if gate_db.exists() else {}
    mem_count = sum(1 for l in mem.read_text(errors="replace").splitlines() if l.strip()) if mem.exists() else 0
    dc_count  = sum(1 for l in dc.read_text(errors="replace").splitlines() if l.strip()) if dc.exists() else 0

    return {
        "system":          "ORION DDGK",
        "kappa_current":   gate_data.get("latency_ms", "?"),
        "evolution_gate":  gate_data,
        "cognitive_memory": {"entries": mem_count},
        "decision_chain":  {"entries": dc_count},
        "temporal_calendar": {"exists": cal.exists()},
        "api_version":     "1.0.0",
        "ts":              datetime.datetime.now().isoformat(),
    }


@app.get("/demo", tags=["Demo"])
def demo():
    """Live-Demo: 3 Beispiel-Entscheidungen"""
    examples = [
        {"question": "Deploy DDGK v1.0 to PyPI?",
         "alternatives": ["deploy now", "test first", "wait for review"],
         "trust_levels": [90.0, 95.0, 85.0]},
        {"question": "Send investor email?",
         "alternatives": ["send now"],
         "trust_levels": [70.0]},
        {"question": "Merge unreviewed code?",
         "alternatives": [],
         "trust_levels": []},
    ]
    results = []
    for ex in examples:
        N   = max(len(ex["alternatives"]), 1)
        phi = (sum(ex["trust_levels"]) / len(ex["trust_levels"]) / 100.0) if ex["trust_levels"] else 0.5
        k   = compute_kappa(N, phi)
        d   = make_decision(k)
        results.append({
            "question": ex["question"],
            "kappa": k, "decision": d["decision"], "symbol": d["symbol"]
        })
    return {"demo_decisions": results, "formula": "κ = 2.060 + 0.930·ln(N)·φ̄"}


# ── MAIN ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("ORION_API_PORT", 8000))
    print(f"\n  🚀 ORION DDGK API startet auf Port {port}")
    print(f"  📖 Docs: http://localhost:{port}/docs")
    print(f"  🧪 Demo: http://localhost:{port}/demo")
    print(f"  📊 Status: http://localhost:{port}/status\n")
    uvicorn.run("orion_api:app", host="0.0.0.0", port=port, reload=True)
