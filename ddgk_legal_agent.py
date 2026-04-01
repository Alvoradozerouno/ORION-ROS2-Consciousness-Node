#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  DDGK JURIST AGENT — Vorabversion für Human Review                ║
║                                                                    ║
║  ⚠️  KEINE RECHTSBERATUNG. Alle Outputs REQUIRES_HUMAN_LAWYER=True ║
║                                                                    ║
║  Fähigkeiten:                                                      ║
║   1. EU AI Act Artikel-Mapping (Art. 6, 9, 13, 14, 17, 61)       ║
║   2. DSGVO Art. 22 Prüfung (automatisierte Entscheidungen)        ║
║   3. MiFID II Art. 17 (Algo-Trading Audit)                        ║
║   4. Vertragsklausel-Template (NICHT final)                       ║
║   5. Haftungsrisiko-Score 0-100                                   ║
║   6. Patent-Vorprüfung (Freedom-to-Operate Hinweise)              ║
║                                                                    ║
║  Alle Outputs: Decision Chain SHA-256 + REQUIRES_HUMAN_LAWYER     ║
╚══════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import json, hashlib, datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional

BASE   = Path(__file__).parent
DC_LOG = BASE / "cognitive_ddgk" / "decision_chain.jsonl"
DC_LOG.parent.mkdir(exist_ok=True)

try:
    from rich.console import Console
    RICH = True; con = Console()
except ImportError:
    RICH = False
    class _C:
        def print(self,*a,**kw): print(*a)
    con = _C()


# ─── EU AI ACT KNOWLEDGE BASE (Stand 2026) ───────────────────────────────────

EU_AI_ACT_ARTICLES = {
    "Art.6":  {
        "title": "Hochrisiko-KI Klassifizierung",
        "summary": "KI-Systeme in kritischen Bereichen = Hochrisiko",
        "domains": ["banking","insurance","healthcare","infrastructure","hr","education","law"],
        "obligation": "Registrierung, Konformitätsbewertung, CE-Kennzeichnung",
        "ddgk_covers": False,
        "ddgk_note": "Externe Registrierung bei nationaler Behörde nötig",
    },
    "Art.9":  {
        "title": "Risikomanagement-System",
        "summary": "Laufendes Risikomanagement-System PFLICHT",
        "domains": ["all"],
        "obligation": "Risk Assessment vor Deployment, kontinuierlich",
        "ddgk_covers": True,
        "ddgk_note": "✅ DDGK Guardian v2 (Risk Score 0-100, kontinuierlich)",
    },
    "Art.13": {
        "title": "Transparenz und Information",
        "summary": "Entscheidungen müssen nachvollziehbar sein",
        "domains": ["all"],
        "obligation": "Audit-Trail, Erklärungen für Nutzer",
        "ddgk_covers": True,
        "ddgk_note": "✅ Decision Chain (SHA-256, alternatives_considered)",
    },
    "Art.14": {
        "title": "Menschliche Aufsicht",
        "summary": "Mensch muss KI überwachen und eingreifen können",
        "domains": ["all"],
        "obligation": "Human-in-the-Loop für kritische Entscheidungen",
        "ddgk_covers": True,
        "ddgk_note": "✅ HITL Bridge (hitl_mcp_bridge.py, approval_token)",
    },
    "Art.17": {
        "title": "Qualitätsmanagementsystem",
        "summary": "Dokumentiertes QM-System PFLICHT",
        "domains": ["all"],
        "obligation": "Prozesse, Verantwortlichkeiten, Tests dokumentieren",
        "ddgk_covers": True,
        "ddgk_note": "✅ Memory Pipeline (2-Phasen, cognitive_memory.md)",
    },
    "Art.61": {
        "title": "Post-Market Monitoring",
        "summary": "Laufende Überwachung nach Deployment",
        "domains": ["all"],
        "obligation": "Incident Reporting, kontinuierliches Monitoring",
        "ddgk_covers": False,
        "ddgk_note": "⚠️ Temporal Daemon (Ansatz) — vollständige Lösung ausstehend",
    },
}

MIFID_II = {
    "Art.17": {
        "title": "Algo-Trading Pflichten",
        "summary": "Algorithmische Handelssysteme brauchen Audit-Trail",
        "ddgk_covers": True,
        "ddgk_note": "✅ Decision Chain — jede Algo-Entscheidung verifizierbar",
    },
    "Art.25": {
        "title": "Eignungsprüfung",
        "summary": "Suitability Assessment für KI-gestützte Beratung",
        "ddgk_covers": False,
        "ddgk_note": "⚠️ Guardian Risk Score = Ansatz, vollständige Lösung ausstehend",
    },
}

GDPR = {
    "Art.22": {
        "title": "Automatisierte Einzelentscheidungen",
        "summary": "Recht auf Erklärung bei automatisierten Entscheidungen",
        "ddgk_covers": True,
        "ddgk_note": "✅ alternatives_considered — einziger bekannter Mechanismus",
    },
    "Art.35": {
        "title": "Datenschutz-Folgenabschätzung",
        "summary": "DPIA für Hochrisiko-Verarbeitung",
        "ddgk_covers": False,
        "ddgk_note": "❌ Externe DPIA durch Datenschutzbeauftragten nötig",
    },
}

DOMAIN_MAPPING = {
    "banking":        ["Art.6","Art.9","Art.13","Art.14","Art.17"],
    "insurance":      ["Art.6","Art.9","Art.13","Art.14"],
    "healthcare":     ["Art.6","Art.9","Art.13","Art.14","Art.17"],
    "trading":        ["Art.9","Art.13","MiFID II Art.17","GDPR Art.22"],
    "hr":             ["Art.6","Art.9","Art.13","GDPR Art.22"],
    "infrastructure": ["Art.6","Art.9","Art.13","Art.14","Art.17"],
    "education":      ["Art.6","Art.9","Art.13"],
    "general":        ["Art.9","Art.13","Art.14"],
}

# Haftungsrisiko-Muster
LIABILITY_PATTERNS = [
    ("hochrisiko",     40, "Hochrisiko-KI → erhöhte Haftung"),
    ("personenbezogen",30, "Personenbezogene Daten → DSGVO-Haftung"),
    ("automatisch",    25, "Automatisierte Entscheidungen → Art. 22 DSGVO"),
    ("kredit",         35, "Kreditentscheidungen → EU AI Act Hochrisiko"),
    ("medizin",        50, "Medizinische KI → höchste Haftungsstufe"),
    ("trading",        30, "Algo-Trading → MiFID II Haftung"),
    ("ohne audit",     45, "Kein Audit-Trail → Compliance-Risiko"),
    ("ohne erklärung", 35, "Keine Erklärbarkeit → DSGVO Risiko"),
]

# Vertragsklausel-Templates
CONTRACT_TEMPLATES = {
    "ai_service_provider": """
KLAUSEL: KI-GOVERNANCE UND COMPLIANCE [VORABVERSION — HUMAN REVIEW REQUIRED]
§X.X — KI-System Compliance

(1) Der Anbieter stellt sicher, dass alle KI-Systeme im Sinne der EU KI-Verordnung
    (EU) 2024/1689 den geltenden Anforderungen entsprechen.

(2) Für Hochrisiko-KI-Systeme gemäß Art. 6 EU AI Act stellt der Anbieter bereit:
    a) Risikomanagement-System (Art. 9)
    b) Nachvollziehbarkeitsdokumentation (Art. 13)
    c) Menschliche Aufsicht (Art. 14)

(3) Der Auftraggeber erhält auf Anfrage Zugang zum Audit-Trail (Decision Chain).

HINWEIS: Diese Klausel ersetzt keine Rechtsberatung. [REQUIRES_HUMAN_LAWYER=True]
""",
    "ai_user": """
KLAUSEL: NUTZUNG VON KI-SYSTEMEN [VORABVERSION — HUMAN REVIEW REQUIRED]
§X.X — KI-Transparenz und Aufsicht

(1) Der Nutzer wird darüber informiert, dass Entscheidungen teilweise durch
    KI-Systeme unterstützt werden (Transparenzpflicht Art. 13 EU AI Act).

(2) Bei erheblichen automatisierten Entscheidungen hat der Nutzer das Recht
    auf menschliche Überprüfung (Art. 14 EU AI Act, Art. 22 DSGVO).

HINWEIS: Diese Klausel ersetzt keine Rechtsberatung. [REQUIRES_HUMAN_LAWYER=True]
""",
}

# Patent-Vorprüfung Knowledge Base
PATENT_PRIOR_ART = {
    "decision_chain_sha256": {
        "invention": "Kryptografisch gesicherte Audit-Kette für KI-Entscheidungen",
        "prior_art_found": False,
        "ddgk_priority": "2025-12-15 (erste Implementierung)",
        "recommendation": "PATENT ANMELDEN — Österr. Patentamt, dann EPA",
        "cost_estimate": "€5.000-15.000 + Anwaltskosten",
    },
    "alternatives_considered": {
        "invention": "alternatives_considered Feld in KI-Entscheidungsdokumentation",
        "prior_art_found": False,
        "ddgk_priority": "2025-12-15",
        "recommendation": "PATENT ANMELDEN — hohes Differenzierungspotential",
        "cost_estimate": "€5.000-15.000 + Anwaltskosten",
    },
    "kappa_coherence": {
        "invention": "κ = 2.060 + 0.930·ln(N)·φ̄ für Multi-Agenten Kohärenz",
        "prior_art_found": True,
        "prior_art_note": "DOI 10.5281/zenodo.14999136 — wir selbst haben published",
        "recommendation": "KEIN PATENT mehr möglich, aber Prior Art gesetzt (andere auch nicht)",
        "cost_estimate": "N/A",
    },
}


# ─── LEGAL AGENT CLASS ───────────────────────────────────────────────────────

@dataclass
class LegalAssessment:
    """Ergebnis der JURIST-Analyse. REQUIRES_HUMAN_LAWYER=True."""
    REQUIRES_HUMAN_LAWYER: bool = True
    domain:           str = ""
    articles_found:   List[str] = field(default_factory=list)
    ddgk_coverage:    Dict[str, str] = field(default_factory=dict)
    coverage_pct:     int = 0
    liability_score:  int = 0
    liability_reasons:List[str] = field(default_factory=list)
    action_items:     List[str] = field(default_factory=list)
    contract_template:str = ""
    chain_hash:       str = ""
    disclaimer:       str = "KEINE RECHTSBERATUNG. Durch Rechtsanwalt prüfen lassen."


class DDGKLegalAgent:
    """
    JURIST Agent — Vorabversion für Human Review.
    ⚠️ KEINE RECHTSBERATUNG. Alle Outputs REQUIRES_HUMAN_LAWYER=True.
    """

    def analyse_eu_ai_act(self, system_description: str, domain: str = "") -> LegalAssessment:
        """EU AI Act Artikel-Mapping."""
        # Domain erkennen
        if not domain:
            domain = self._detect_domain(system_description)

        articles = DOMAIN_MAPPING.get(domain, DOMAIN_MAPPING["general"])
        coverage = {}
        covered  = 0

        for art in articles:
            if art.startswith("Art."):
                info = EU_AI_ACT_ARTICLES.get(art, {})
                note = info.get("ddgk_note","❓ Prüfung nötig")
                coverage[art] = note
                if info.get("ddgk_covers"): covered += 1
            elif art.startswith("MiFID"):
                key = art.replace("MiFID II ","")
                info = MIFID_II.get(key, {})
                note = info.get("ddgk_note","❓")
                coverage[art] = note
                if info.get("ddgk_covers"): covered += 1
            elif art.startswith("GDPR"):
                key = art.replace("GDPR ","")
                info = GDPR.get(key, {})
                note = info.get("ddgk_note","❓")
                coverage[art] = note
                if info.get("ddgk_covers"): covered += 1

        pct = int(100 * covered / len(articles)) if articles else 0

        # Liability Score
        liability_score, reasons = self._assess_liability(system_description)

        action_items = [
            f"Nationale EU AI Act Behörde: www.bmdw.gv.at (AT) / BNetzA (DE)",
            "Datenschutzbeauftragten bestellen (falls > 250 MA oder Hochrisiko-Verarbeitung)",
            "Konformitätsbewertung durch akkreditierte Stelle (für Hochrisiko-KI Art. 6)",
        ]
        if domain in ["banking","insurance","trading"]:
            action_items.append("FMA Österreich informieren (Finanzmarktaufsicht)")

        result = LegalAssessment(
            domain=domain,
            articles_found=articles,
            ddgk_coverage=coverage,
            coverage_pct=pct,
            liability_score=liability_score,
            liability_reasons=reasons,
            action_items=action_items,
            contract_template=CONTRACT_TEMPLATES.get("ai_service_provider",""),
        )
        result.chain_hash = self._write_chain("EU_AI_ACT_ASSESSMENT", system_description[:100], pct)
        return result

    def check_gdpr_art22(self, decision_description: str) -> Dict:
        """DSGVO Art. 22 Prüfung für automatisierte Entscheidungen."""
        automated = any(w in decision_description.lower() for w in
                        ["automatisch","automat","ohne mensch","kein mensch","algorithmus"])
        significant = any(w in decision_description.lower() for w in
                          ["kredit","ablehnung","kündigung","bewerbung","versicherung","score"])

        result = {
            "REQUIRES_HUMAN_LAWYER": True,
            "art22_triggered": automated and significant,
            "automated": automated,
            "significant_effect": significant,
            "ddgk_solution": "✅ alternatives_considered + HITL" if (automated and significant) else "ℹ️ Vorsorglich dokumentieren",
            "user_rights": ["Recht auf Erklärung","Recht auf menschliche Prüfung","Recht auf Widerspruch"] if (automated and significant) else [],
            "action": "DSGVO Art. 22 Abs. 3 PFLICHT: Erklärbarkeit implementieren" if (automated and significant) else "Vorsorglich dokumentieren",
            "disclaimer": "KEINE RECHTSBERATUNG. Datenschutzbeauftragten konsultieren.",
        }
        self._write_chain("GDPR_ART22_CHECK", decision_description[:100], int(result["art22_triggered"]) * 100)
        return result

    def freedom_to_operate(self, invention_key: str = "") -> Dict:
        """Patent-Vorprüfung für bekannte DDGK-Innovationen."""
        results = {}
        for key, info in PATENT_PRIOR_ART.items():
            if not invention_key or invention_key in key:
                results[key] = {**info, "REQUIRES_PATENT_LAWYER": True}

        return {
            "REQUIRES_PATENT_LAWYER": True,
            "disclaimer": "KEINE Rechts-/Patentberatung. Patentanwalt konsultieren.",
            "inventions": results,
            "recommendation": "Provisional Patent Application DIESE WOCHE einreichen",
            "contact": "Österr. Patentamt: www.patentamt.at | EPA: www.epo.org",
        }

    def draft_contract_clause(self, clause_type: str = "ai_service_provider") -> Dict:
        """Vertragsklausel-Template. NICHT final, HUMAN REVIEW REQUIRED."""
        template = CONTRACT_TEMPLATES.get(clause_type, CONTRACT_TEMPLATES["ai_service_provider"])
        return {
            "REQUIRES_HUMAN_LAWYER": True,
            "REQUIRES_LEGAL_REVIEW": True,
            "clause_type":  clause_type,
            "template":     template,
            "disclaimer":   "VORABVERSION. Kein Rechtsrat. Anwalt beauftragen.",
            "next_step":    "An Rechtsanwalt für EU AI Act Recht weiterleiten",
        }

    def _detect_domain(self, text: str) -> str:
        text = text.lower()
        mapping = [
            (["bank","kredit","darlehen","finanz"],      "banking"),
            (["versicherung","police","schaden"],         "insurance"),
            (["arzt","patient","diagnose","medizin"],     "healthcare"),
            (["trading","algo","handel","börse"],         "trading"),
            (["personal","bewerbung","recruiting","hr"],  "hr"),
            (["strom","energie","netz","infrastruktur"],  "infrastructure"),
            (["schule","student","bildung"],              "education"),
        ]
        for keywords, domain in mapping:
            if any(k in text for k in keywords):
                return domain
        return "general"

    def _assess_liability(self, text: str):
        score, reasons = 0, []
        for pattern, weight, reason in LIABILITY_PATTERNS:
            if pattern in text.lower():
                score += weight
                reasons.append(f"⚠️ {reason} (+{weight})")
        return min(score, 100), reasons

    def _write_chain(self, type_: str, content: str, score: int) -> str:
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        prev = ""
        if DC_LOG.exists():
            lines = DC_LOG.read_text("utf-8").strip().splitlines()
            if lines:
                try: prev = json.loads(lines[-1]).get("hash","")
                except: pass

        entry = {
            "ts": ts, "type": f"JURIST_{type_}",
            "content_preview": content[:80],
            "score": score,
            "REQUIRES_HUMAN_LAWYER": True,
            "prev_hash": prev,
        }
        chain_str = json.dumps(entry, sort_keys=True, ensure_ascii=False)
        entry["hash"] = hashlib.sha256(chain_str.encode()).hexdigest()

        with DC_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry["hash"]

    def display(self, a: LegalAssessment):
        con.print("\n  ⚖️ JURIST AGENT — Vorabversion" if not RICH else
                  "\n  [bright_red]⚖️ JURIST AGENT — Vorabversion[/bright_red]")
        con.print(f"  ⚠️  REQUIRES_HUMAN_LAWYER=True | KEINE RECHTSBERATUNG")
        con.print(f"  Domain: {a.domain} | Coverage: {a.coverage_pct}% | Haftung: {a.liability_score}/100")
        con.print()
        con.print("  EU AI Act Artikel:")
        for art, note in a.ddgk_coverage.items():
            con.print(f"    {art:20s}  {note}")
        if a.liability_reasons:
            con.print("\n  Haftungsrisiken:")
            for r in a.liability_reasons:
                con.print(f"    {r}")
        con.print("\n  Nächste Schritte:")
        for item in a.action_items:
            con.print(f"    □ {item}")
        con.print(f"\n  Chain: {a.chain_hash[:16]}...")
        con.print(f"  {a.disclaimer}")


# ─── MAIN (Demo) ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    jurist = DDGKLegalAgent()

    print("\n" + "="*60)
    print("  DDGK JURIST AGENT — Demo")
    print("  ⚠️  KEINE RECHTSBERATUNG!")
    print("="*60)

    # Test 1: TIWAG (Infrastruktur)
    print("\n  [TEST 1] TIWAG — KI-System für Strom-Netzbetrieb")
    a1 = jurist.analyse_eu_ai_act(
        "KI-System für automatische Entscheidungen im Stromnetz",
        domain="infrastructure"
    )
    jurist.display(a1)

    # Test 2: Algo-Trading
    print("\n  [TEST 2] Hedge Fund — Algorithmisches Trading System")
    a2 = jurist.analyse_eu_ai_act("Trading-Algorithmus für automatischen Aktienhandel")
    jurist.display(a2)

    # Test 3: DSGVO Art. 22
    print("\n  [TEST 3] DSGVO Art. 22 — Automatische Kreditentscheidung")
    r3 = jurist.check_gdpr_art22("Automatische Kreditablehnung ohne menschliche Prüfung")
    print(f"  Art.22 ausgelöst: {r3['art22_triggered']}")
    print(f"  DDGK-Lösung: {r3['ddgk_solution']}")
    print(f"  ⚠️  {r3['disclaimer']}")

    # Test 4: Patent
    print("\n  [TEST 4] Patent-Vorprüfung")
    p = jurist.freedom_to_operate()
    for key, info in p["inventions"].items():
        status = "✅ PATENT MÖGLICH" if not info["prior_art_found"] else "⚠️ PRIOR ART"
        print(f"  {status}: {info['invention'][:50]}")
        print(f"           → {info['recommendation']}")
