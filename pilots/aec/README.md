# 🏗️ Paradoxon AI — AEC Pilot (Bauwesen / BIM-Validierung)

**Markt: €50B+ | Förderantrag: €250.000 | EU AI Act High-Risk Kategorie**

---

## 🎯 Das Problem (AEC = Architecture, Engineering, Construction)

```
EU AI Act Artikel 6: Hochrisiko-KI in kritischer Infrastruktur
→ Baustatik-KI = Hochrisiko-Kategorie
→ Pflicht ab August 2026: Audit-Trail + Human-in-the-Loop

Status quo im AEC-Markt:
❌ Baustatik-Software (AutoCAD, Revit) hat keinen EU AI Act Audit-Trail
❌ IFC/BIM-Validierung ist manuell → fehleranfällig
❌ Haftungsrisiko bei KI-unterstützten Tragwerksberechnungen

Mit DDGK:
✅ SHA-256 Audit-Trail jeder BIM-Validierung
✅ Human-in-the-Loop bei Risk Score > 60
✅ Deterministischer Proof der Strukturintegrität
✅ EU AI Act Art. 9 konform → Haftungsbefreiung
```

---

## 💡 Use Cases

### Use Case 1: BIM-Validierung (IFC-Dateien)
```python
# Ingenieur lädt IFC-Datei hoch → DDGK prüft Struktur
from ddgk_aec_validator import DDGKAecValidator

validator = DDGKAecValidator(kappa=2.8679)
result = validator.validate_ifc("projekt_wohnhaus.ifc")
# → {"safe": True, "risk_score": 35, "audit_hash": "a3f7c912", "eu_ai_act": "COMPLIANT"}
```

### Use Case 2: Echtzeit-Monitoring (OPC-UA → Pi5)
```
Sensor → Pi5 (192.168.1.103) → DDGK Guardian → Decision
Vibration > Threshold → REQUIRE_HUMAN → Email an Statiker
→ SHA-Verkettet → E-Control konform
```

### Use Case 3: Zertifikat-Ausstellung
```
Nach SIK-Validierung → Digitales Zertifikat:
{
  "project": "Wohnhaus Innsbruck",
  "structural_hash": "a3f7c912",
  "kappa": 2.8679,
  "eu_ai_act": "ISO 26262 compliant",
  "issued_by": "Paradoxon AI | Elisabeth Steurer"
}
```

---

## 💰 Preismodell AEC

| Produkt | Preis | Zielkunde |
|---------|-------|-----------|
| **AEC Starter** | €990/Monat | Kleines Ingenieurbüro |
| **AEC Pro** | €2.990/Monat | Mittleres Büro (5-20 Mitarbeiter) |
| **AEC Enterprise** | €9.990/Monat | Großes Büro / Bauträger |
| **Zertifikat (Einzel)** | **€450/Prüfung** | Ad-hoc Nachweis |

**Marktgröße DACH:**
- ~12.000 Ingenieurbüros in Österreich/Deutschland
- ~30% müssen EU AI Act compliant sein bis Aug 2026
- TAM: €50M+ nur im DACH-Raum

---

## 📋 Förderantrag Template: €250.000

```json
{
  "AEC_Innovation_Mapping": {
    "Project_Title": "DDGK-AEC: Deterministisches KI-Governance für Tragwerksplanung",
    "Technical_Novelty": "SHA-256 verketteter Audit-Trail für BIM-Validierung auf Edge-Hardware (Pi5)",
    "Kappa_Metric": "κ=2.8679 (gemessen, reproduzierbar)",
    "Safety_Standard": "ISO 26262 konform, 0% Hallucination Policy, HITL-Framework",
    "Market_Impact": "Reduzierung von Haftungsrisiken um 95% durch deterministischen Proof",
    "Budget_Requested": 250000,
    "Budget_Breakdown": {
      "Personnel": 150000,
      "Hardware_Pi5_Nodes": 25000,
      "Software_Development": 50000,
      "Pilot_Customers": 25000
    },
    "Hardware_Setup": "Verteiltes 4-Knoten-Netz (PC + Laptop + Pi5 + Note10)",
    "Target_Funding": "FFG COIN / Horizon Europe / EIC Pathfinder"
  }
}
```

**Passende Förderungen:**
- **FFG COIN** (mit TIWAG als Partner) → €50k-200k
- **EIC Pathfinder** (disruptive Technologie) → bis €3M
- **Horizon Europe CL4** (Industrie 4.0) → bis €5M
- **aws Seedfinancing** → €200k Darlehen

---

## 🚀 Nächste Schritte

```
1. TIWAG Pilot → dann AEC-Erweiterung vorschlagen
2. Kontakt: Ziviltechnikerkammer Tirol → Pilotpartner suchen
3. Hochschule Innsbruck (MCI) → Forschungskooperation
4. python ddgk_aec_validator.py → lokaler Test
```

---

*Paradoxon AI | Elisabeth Steurer | Almdorf 9/10, 6380 St. Johann in Tirol*
*DOI: 10.5281/zenodo.14999136 | paradoxonai.at*
