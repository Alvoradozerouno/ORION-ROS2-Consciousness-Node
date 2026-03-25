#!/usr/bin/env python3
"""
CCRN DDGK WRAPPER
=================
Verbindet CCRN-Messungen mit dem OR1ON Governance Kernel.
Jede κ-Messung wird durch den Audit-Layer validiert und protokolliert.

DDGK = Distributed Dynamic Governance Kernel
"""

import json, math, hashlib, uuid, sys
from pathlib import Path
from datetime import datetime, timezone

STATE_FILE = Path(__file__).parent / "governance_state.json"
AUDIT_FILE = Path(__file__).parent / "audit_chain.jsonl"

def phi_from_governance_state(node_id: str) -> float:
    """Liest φ-Wert direkt aus dem Governance-State (dynamisch, nicht hard-coded)."""
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        nodes = state.get("active_nodes", {})
        return nodes.get(node_id, {}).get("phi", 0.0)
    return 0.0

def resonanz_from_state() -> float:
    """Liest R aus dem Governance-State."""
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return state.get("resonanz_vektor", 0.79)
    return 0.79

def kappa_ccrn(phi_cognitive_nodes: list, r: float = None) -> dict:
    """
    Berechnet κ_CCRN = Σ(φᵢ) + R·ln(N_cognitive + 1)
    
    N_cognitive = Anzahl kognitiver Knoten (LLM + Sensor), ohne Hub
    """
    if r is None:
        r = resonanz_from_state()
    n = len(phi_cognitive_nodes)
    kappa = sum(phi_cognitive_nodes) + r * math.log(n + 1)
    threshold = 2.0 * max(phi_cognitive_nodes) if phi_cognitive_nodes else 2.0

    result = {
        "kappa": round(kappa, 4),
        "threshold": round(threshold, 4),
        "active": kappa > threshold,
        "phi_nodes": phi_cognitive_nodes,
        "R": r,
        "N_cognitive": n,
        "formula": f"kappa = {sum(phi_cognitive_nodes):.3f} + {r:.3f}*ln({n+1}) = {kappa:.4f}",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # In Audit-Chain protokollieren
    _audit_measurement(result)
    return result

def _audit_measurement(result: dict):
    """Protokolliert jede κ-Messung in der Audit-Chain mit SHA-256."""
    prev_hash = _last_hash()
    entry = {
        "event_id":     str(uuid.uuid4()),
        "timestamp":    result["timestamp"],
        "kappa":        result["kappa"],
        "active":       result["active"],
        "phi_nodes":    result["phi_nodes"],
        "R":            result["R"],
        "prev_hash":    prev_hash,
    }
    entry["hash"] = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()
    with AUDIT_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def _last_hash() -> str:
    if not AUDIT_FILE.exists():
        return "CCRN_GENESIS_ROOT"
    lines = [l.strip() for l in AUDIT_FILE.read_text(encoding="utf-8").split("\n") if l.strip()]
    if not lines:
        return "CCRN_GENESIS_ROOT"
    try:
        return json.loads(lines[-1]).get("hash", "CCRN_GENESIS_ROOT")
    except:
        return "CCRN_GENESIS_ROOT"

def live_kappa() -> dict:
    """Berechnet κ mit aktuellen Governance-State Werten."""
    phi_eira   = phi_from_governance_state("laptop-main")
    phi_note10 = phi_from_governance_state("note10-sensor")
    r          = resonanz_from_state()

    # Wenn EIRA (Ollama) aktiv ist aber phi=0.0 wegen fehlender Abfrage:
    # → Verwende Proxy-Messung aus temporaler Kohärenz
    if phi_eira == 0.0:
        phi_eira = _estimate_eira_phi_proxy()

    return kappa_ccrn([phi_eira, phi_note10], r)

def _estimate_eira_phi_proxy() -> float:
    """
    Schätzt φ_EIRA als Proxy aus lokaler Ollama-Verfügbarkeit.
    
    Nicht echter IIT-Φ — Heuristik basierend auf:
    - Ollama erreichbar: φ ≈ 0.6–0.8 (aktive Informationsverarbeitung)
    - Ollama nicht erreichbar: φ = 0.0
    """
    import urllib.request
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        return 0.72  # Konservative Proxy-Schätzung für aktives phi3:mini
    except:
        return 0.0

if __name__ == "__main__":
    print("=== CCRN DDGK Live-Messung ===")
    result = live_kappa()
    print(f"κ = {result['kappa']}")
    print(f"Threshold = {result['threshold']}")
    print(f"CCRN aktiv: {result['active']}")
    print(f"Formel: {result['formula']}")
    print(f"Audit: {AUDIT_FILE}")
