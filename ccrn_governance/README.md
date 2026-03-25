# CCRN Governance Layer (DDGK)

**DDGK** = Distributed Dynamic Governance Kernel

Dieses Verzeichnis enthält den Governance-Layer für alle CCRN-Messungen.

## Dateien

- `ddgk_layer.py` — OR1ON Governance Kernel (aus EIRA Workspace)
- `ccrn_ddgk_wrapper.py` — CCRN-spezifischer Wrapper für κ-Messungen
- `governance_state.json` — Aktueller Systemzustand mit echten φ-Werten
- `audit_chain.jsonl` — SHA-256 verkettete Audit-Protokolle aller Messungen

## Nutzung

```python
from ccrn_governance.ccrn_ddgk_wrapper import live_kappa, kappa_ccrn

# Live-Messung mit Governance-State
result = live_kappa()
print(f"κ = {result['kappa']} | Aktiv: {result['active']}")

# Manuelle Berechnung mit bekannten φ-Werten
result = kappa_ccrn([0.78, 0.11], r=0.93)
```

## Echte φ-Werte (aus Governance-State 2026-03-23)

| Knoten | φ (real) | φ (Paper v2.0) |
|--------|----------|----------------|
| laptop-main (EIRA) | 0.0 (Ollama inaktiv) → ~0.78 (aktiv) | 1.0 (hard-coded) |
| pi5-node (Nexus) | 1.0 | — |
| note10-sensor | 0.11 | 1.0 (hard-coded!) |
| resonanz_vektor | 0.93 | 0.79 |
