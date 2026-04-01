# 🏢 TIWAG Pilot — DDGK AI Governance

**Paradoxon AI | Elisabeth Steurer | paradoxonai.at**  
**Ansprechpartner TIWAG:** CTO / Digitalisierung  
**Pilot-Dauer:** 3 Monate  
**Preis:** €5.000 (Pilot) → €2.990/Monat (Produktion)

---

## 🎯 Use Case: KI-Entscheidungs-Audit für Netzbetrieb

### Problem das TIWAG hat:
```
EU AI Act Art. 9 gilt ab August 2026 für kritische Infrastruktur.
TIWAG betreibt kritische Infrastruktur (Strom, Wasserkraft).
Jede KI-Entscheidung im Netzbetrieb muss:
  1. Dokumentiert sein (Audit-Trail)
  2. Nachvollziehbar sein (Decision Chain)
  3. Bei hochrisiko: menschlich freigegeben sein (HITL)
  
Ohne DDGK: manuelles Logging → fehleranfällig → EU AI Act Non-Compliance
Mit DDGK:  automatisch → lückenlos → EU AI Act ready
```

### Was DDGK für TIWAG liefert:
```
1. REST API Integration
   TIWAG KI-System → POST /api/v1/assess → DDGK Guardian → Decision
   
2. SHA-256 Audit Trail
   Jede KI-Entscheidung → unveränderlicher Hash-verkettet Log
   → Nachweisbar vor Regulatoren (E-Control, EU AI Act)

3. Human-in-the-Loop
   Risk Score > 60 → automatische Email an Schichtleiter
   → "Freigabe erforderlich: Lastvermittlung Netz XY"

4. Weekly Report
   PDF-Export der Decision Chain → Compliance-Nachweis
```

---

## 📋 Pilot-Setup (3 Schritte, 1 Tag)

### Schritt 1: API verbinden
```bash
# Auf TIWAG-Server oder per ngrok:
pip install requests

import requests
r = requests.post("https://api.paradoxonai.at/api/v1/assess", json={
    "action": "lastverteilung_anpassen",
    "tool":   "netz_ki_v2",
    "context": "Netzlast 85% → KI empfiehlt Reduktion Zone 3",
    "user_approved": False
}, headers={"X-API-Key": "TIWAG-PILOT-KEY"})

print(r.json())
# {"risk_score": 45, "decision": "AUTO_APPROVE", "chain_hash": "a3f7c912"}
```

### Schritt 2: HITL konfigurieren
```python
# ddgk_tiwag_config.py
TIWAG_CONFIG = {
    "company": "TIWAG AG",
    "notify_email": "schichtleiter@tiwag.at",
    "risk_threshold_human": 60,   # > 60 → Email an Schichtleiter
    "risk_threshold_deny":  85,   # > 85 → Automatisch abgelehnt
    "audit_retention_days": 730,  # 2 Jahre → DSGVO-konform
}
```

### Schritt 3: Dashboard einrichten
```
http://api.paradoxonai.at/dashboard
→ Zeigt: alle TIWAG KI-Entscheidungen, Risk Scores, HITL-Events
→ Export: PDF für E-Control / Compliance-Berichte
```

---

## 💰 Preismodell

| Phase | Dauer | Preis | Inhalt |
|-------|-------|-------|--------|
| **Pilot** | 3 Monate | **€5.000** | Setup + 100.000 API Calls + Support |
| **Business** | laufend | **€2.990/Monat** | Unlimited Calls + 2h/Monat Support |
| **Enterprise** | laufend | **€9.990/Monat** | Dedicated Instance + SLA 99.9% |

---

## 📧 Nächster Schritt

Öffne: `DDGK_TIWAG_PITCH_EMAIL.md`  
Ersetze `[NAME]`, `[EMAIL]`  
Sende heute!

---

*Paradoxon AI | Einzelunternehmen Elisabeth Steurer | Almdorf 9/10, 6380 St. Johann in Tirol*  
*DOI: 10.5281/zenodo.14999136 | paradoxonai.at*
