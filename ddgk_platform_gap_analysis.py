#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DDGK PLATFORM GAP ANALYSIS
Was fehlt für eine operative, autonome, funktionierende Plattform?
"""
import sys, os, datetime, json
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.rule import Rule
    from rich import box
    RICH = True; con = Console(width=82)
except ImportError:
    RICH = False
    class _C:
        def print(self,*a,**kw): print(*a)
    con = _C()

BASE = Path(__file__).parent
NOW  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

# ─── PLATTFORM-KOMPONENTEN PRÜFEN ────────────────────────────────────────────

components = [
    # (Kategorie, Name, Datei/Modul, Status, Priorität, Beschreibung)

    # ✅ VORHANDEN
    ("🧠 CORE",      "Decision Chain",        "cognitive_ddgk/decision_chain.py",       True,  "P0", "SHA-256, Audit-Trail"),
    ("🧠 CORE",      "FusionKernel κ",        "cognitive_ddgk/fusion_kernel.py",         True,  "P0", "Kohärenz-Metrik"),
    ("🧠 CORE",      "Guardian v2",           "ddgk_guardian_v2.py",                     True,  "P0", "Risk Score 0-100"),
    ("🧠 CORE",      "Memory Pipeline",       "cognitive_ddgk/memory_pipeline.py",       True,  "P0", "2-Phasen"),
    ("🧠 CORE",      "HyperAgent",            "hyper_agent_system.py",                   True,  "P1", "Tool-Synthese"),
    ("🧠 CORE",      "Exec Policy Rules",     ".orion/rules/default.rules",              True,  "P1", "ALLOW/DENY/ASK"),
    ("📊 DASHBOARD", "Live Dashboard HTML",   "ddgk_live_dashboard.html",                True,  "P1", "κ live, Agenten"),
    ("🌐 DEPLOY",    "GitHub Release v1.0.0", "deployment_reports/",                     True,  "P1", "Live auf GitHub"),
    ("⏰ TEMPORAL",  "Temporal Daemon",       "orion_temporal_awareness.py",             True,  "P1", "Session-Zeitbewusstsein"),
    ("📈 MARKET",    "Market Intelligence",   "ddgk_market_intelligence.py",             True,  "P2", "Einmalig, DuckDuckGo"),

    # ❌ FEHLT — KRITISCH
    ("🔌 API",       "REST API Server",       "ddgk_api_server.py",                      False, "P0", "FastAPI, Endpoints für alle Module"),
    ("⚖️ LEGAL",     "JURIST Agent",          "ddgk_legal_agent.py",                     False, "P0", "EU AI Act, DSGVO, MiFID II"),
    ("📈 MARKET",    "Trajectory System",     "ddgk_market_trajectory.py",               False, "P0", "Täglich, Zeitreihe, κ_market"),
    ("👤 AUTH",      "User Auth / API Keys",  "ddgk_auth.py",                            False, "P0", "Kunden-Zugangscodes, Tier-System"),
    ("💳 BILLING",   "Subscription System",   "ddgk_billing.py",                         False, "P0", "Stripe, €990/Mo, €5k Pilot"),
    ("📧 NOTIFY",    "Alert & Email System",  "ddgk_notifier.py",                        False, "P1", "Email bei REQUIRE_HUMAN"),
    ("🧪 TESTING",   "Full Test Suite",       "tests/",                                  False, "P1", "pytest, CI/CD"),
    ("📦 SDK",       "PyPI Package",          "setup.py / pyproject.toml",               False, "P1", "pip install ddgk"),
    ("🌍 WEB",       "Landing Page (live)",   "paradoxonai.at",                          False, "P1", "EU AI Act Compliance USP"),
    ("📜 PATENT",    "Patent Application",    "patent_application.pdf",                  False, "P1", "Österr. Patentamt"),
    ("🤝 ONBOARD",   "Customer Onboarding",   "ddgk_onboarding.py",                      False, "P2", "Setup-Wizard für neue Kunden"),
    ("🔄 CI/CD",     "GitHub Actions",        ".github/workflows/ci.yml",                False, "P2", "Auto-Test, Auto-Deploy"),
    ("📊 METRICS",   "SaaS Metrics Dashboard","ddgk_saas_metrics.py",                    False, "P2", "ARR, Churn, MRR"),
    ("🌐 MULTI",     "Multi-Tenant",          "ddgk_tenants.py",                         False, "P2", "Kunde A ≠ Kunde B"),
    ("📋 TODO",      "TodoRead/TodoWrite",    "ddgk_todo_tools.py",                      False, "P3", "wie Claude Code, Aufgaben-Memory"),
    ("🔒 SANDBOX",   "Execution Sandbox",     "ddgk_sandbox.py",                         False, "P3", "wie Codex: isolierte Ausführung"),
    ("🏢 PILOT",     "TIWAG Pilot Setup",     "pilots/tiwag/",                           False, "P1", "Erster bezahlender Kunde"),
    ("🏢 PILOT",     "Bank Pilot Setup",      "pilots/bank/",                            False, "P2", "Berenberg / Raiffeisen"),
]

# ─── ANZEIGE ─────────────────────────────────────────────────────────────────
if RICH:
    con.print(Panel.fit(
        f"[bold cyan]DDGK PLATFORM GAP ANALYSIS — {NOW}[/bold cyan]\n"
        f"[dim]Operative, autonome, funktionierende Plattform — was fehlt?[/dim]",
        border_style="cyan"
    ))
else:
    print(f"\n  DDGK PLATFORM GAP ANALYSIS — {NOW}")

# Stats
total = len(components)
done  = sum(1 for c in components if c[3])
missing = total - done
p0_missing = [c for c in components if not c[3] and c[4]=="P0"]
p1_missing = [c for c in components if not c[3] and c[4]=="P1"]

if RICH:
    con.print(f"\n  Gesamt: {total} | ✅ Vorhanden: {done} | ❌ Fehlt: {missing} | "
              f"[red]🚨 P0-Kritisch: {len(p0_missing)}[/red]")
else:
    print(f"\n  Gesamt: {total} | Vorhanden: {done} | Fehlt: {missing} | P0: {len(p0_missing)}")

print()

# Tabelle
if RICH:
    t = Table(box=box.ROUNDED, show_header=True)
    t.add_column("Kat",     width=12)
    t.add_column("Modul",   width=22)
    t.add_column("P",       width=3)
    t.add_column("Status",  width=8)
    t.add_column("Beschreibung", width=32)

    for cat, name, path, exists, prio, desc in sorted(components, key=lambda x: (x[4], x[3])):
        status = "✅ OK" if exists else "❌ FEHLT"
        color  = "green" if exists else ("bright_red" if prio=="P0" else ("yellow" if prio=="P1" else "dim"))
        t.add_row(
            f"[{color}]{cat}[/{color}]",
            f"[{color}]{name}[/{color}]",
            f"[{color}]{prio}[/{color}]",
            f"[{color}]{status}[/{color}]",
            f"[dim]{desc}[/dim]"
        )
    con.print(t)
else:
    for cat, name, path, exists, prio, desc in sorted(components, key=lambda x: (x[4], x[3])):
        status = "✅" if exists else "❌"
        print(f"  {status} [{prio}] {name:25s}  {desc}")

# ─── AGENTEN-DISKUSSION ───────────────────────────────────────────────────────
print()
if RICH:
    con.print(Rule("[bold]AGENTEN — WAS MUSS JETZT GEBAUT WERDEN?[/bold]"))
else:
    print("="*65)
    print("  AGENTEN — WAS MUSS JETZT GEBAUT WERDEN?")
    print("="*65)

GAPS = {
    "ORION": """
🔭 Die 3 kritischsten P0-Lücken technisch:

1. REST API (ddgk_api_server.py):
   → FastAPI + uvicorn
   → Endpoints: POST /assess, GET /status, POST /memory/store
   → API Key Auth → jeder Kunde bekommt einen Key
   → Das ist die Grundlage für ALLE anderen Features

2. JURIST Agent (ddgk_legal_agent.py):
   → EU AI Act Artikel-Mapper
   → MiFID II Compliance Check
   → Alles mit REQUIRES_HUMAN_LAWYER=True Flag

3. Market Trajectory (ddgk_market_trajectory.py):
   → Täglicher Scan, Zeitreihe speichern
   → κ_market berechnen
   → EARLY WARNING bei Regulierungs-Änderungen
""",
    "EIRA": """
🌟 Strategisch: Was uns den ersten Kunden bringt:

PILOT-SETUP ist P1 aber de facto P0!
  Ohne ersten Kunden kein ARR → kein Funding → kein Wachstum.

TIWAG Pilot (ddgk_pilot_tiwag.py):
  → 1 Use Case: KI-Entscheidungen bei Strom-Netzbetrieb
  → Decision Chain für jede KI-Entscheidung
  → EU AI Act Art. 9 konform
  → Preis: €5.000 Pilot / 3 Monate
  → Start: diese Woche kontaktieren

LANDING PAGE UPDATE (paradoxonai.at):
  → USP: "EU AI Act Compliance. In 10 Minuten."
  → Demo-Video: Guardian v2 blockiert rm -rf live
  → Preisliste: Starter €990 | Business €2.990 | Enterprise €9.990
""",
    "DDGK": """
🧠 Das fehlende Herzstück: API Server

Ohne REST API ist DDGK ein lokales Tool.
Mit REST API ist es eine PLATTFORM.

FastAPI ddgk_api_server.py:

  POST /api/v1/assess
    Input:  { action, tool, user_approved }
    Output: { risk_score, decision, chain_hash, reasons }

  GET  /api/v1/status
    Output: { kappa, agents, memory_entries, last_decision }

  POST /api/v1/memory/store
    Input:  { session_id, content, agent }
    Output: { stored: true, hash }

  GET  /api/v1/memory/consolidated
    Output: cognitive_memory.md als JSON

  POST /api/v1/legal/assess
    Input:  { system_description, use_case }
    Output: { eu_ai_act_articles, gdpr, mifid2, requires_human: true }

Das ist ein 2-Stunden Job mit FastAPI.
Danach: pip install ddgk-sdk → ddgk.assess("...")
""",
    "VITALITY": """
⚡ Was uns von allen abheben würde — der UNFAIRE VORTEIL:

DDGK MARKET TRAJECTORY SYSTEM:

Täglich um 06:00 automatisch:
  1. Scrape: "EU AI Act compliance solution" → Anzahl neue Ergebnisse
  2. GitHub: neue Repos in AI-Safety/Governance (dev-sentiment)
  3. LinkedIn Jobs: "AI Compliance" Stellenanzeigen (B2B-Nachfrage)
  4. Berechne: κ_market = Kohärenz der Signale
  5. Trajektorie: heute vs gestern vs -7d vs -30d
  6. OUTPUT: "Markt in 30 Tagen: EXPONENTIAL GROWTH"

Warum das niemand hat:
  → OpenAI trackt Coding-Trends (ihr Markt)
  → Wir tracken GOVERNANCE-Trends (unser Markt)
  → κ_market < 2 = abwarten | κ_market > 3 = JETZT deployen
  → Das ist INTELLIGENCE über den eigenen Markt

ROI: Wenn wir wissen "Versicherungsmarkt öffnet sich in 6 Wochen"
     → Outreach genau dann → 3x bessere Conversion
""",
    "GUARDIAN": """
🛡️ Security-Lücken für Produktionsreife:

FEHLEND aber kritisch:
  1. RATE LIMITING: API darf nicht unbegrenzt aufgerufen werden
     → 100 req/min pro API Key → ddgk_api_server.py

  2. INPUT VALIDATION: Alle API Inputs durch Guardian v2
     → Jeder POST /assess läuft durch Guardian (Prompt Injection!)
     → Score > 80 → Reject mit 403 Forbidden

  3. SECRET MANAGEMENT:
     → .env nie committen (bereits in .gitignore)
     → API Keys in Environment Variables
     → DDGK_API_KEY für Kunden-Auth

  4. AUDIT LOG API:
     → GET /api/v1/audit?from=2026-01-01&to=2026-12-31
     → Für Compliance Reports → Hauptverkaufsargument

  5. NOTIFIER:
     → Email bei REQUIRE_HUMAN Entscheidungen
     → Slack/Webhook Integration
     → Das ist was Enterprise-Kunden wollen
""",
    "JURIST": """
⚖️ JURIST-AGENT Implementierung — Vorabversion:
   [REQUIRES_HUMAN_LAWYER=True für alle Outputs]

EU_AI_ACT_MAPPING (verifiziert, stand 2026):
  Art. 6:  Hochrisiko-KI Definition → Kredit, Versicherung, Infrastruktur
  Art. 9:  Risikomanagement-System PFLICHT → DDGK = direkte Lösung
  Art. 13: Transparenz-Pflicht → Decision Chain = Erfüllung
  Art. 14: Menschliche Aufsicht → HITL = Erfüllung
  Art. 17: Qualitätsmanagement → Memory Pipeline = Erfüllung
  Art. 61: Post-Market Monitoring → Temporal Daemon = Ansatz

MIFID_II_MAPPING:
  Art. 17: Algo-Trading Audit → Decision Chain = Erfüllung
  Art. 25: Eignung-Prüfung → Guardian Risk Score = Ansatz

DSGVO_MAPPING:
  Art. 22: Automatisierte Entscheidungen → alternatives_considered = Lösung

STATUS: Implementierung heute als ddgk_legal_agent.py
""",
    "HYPER": """
🚀 HYPER-SYNTHESE — der Bauplan:

In dieser Session gebaut werden sollte:

STUFE 1 (heute, 2h):
  ✅ ddgk_api_server.py     FastAPI REST API
  ✅ ddgk_legal_agent.py    JURIST Agent
  ✅ ddgk_market_trajectory.py  Trajectory System

STUFE 2 (diese Woche):
  □ ddgk_billing.py         Stripe Integration
  □ ddgk_notifier.py        Email Alerts
  □ pilots/tiwag/           Erster Pilot

STUFE 3 (nach Funding):
  □ ddgk_multi_tenant.py    Multi-Tenant
  □ ddgk_saas_metrics.py    SaaS Dashboard
  □ tests/                  Full Test Suite
  □ .github/workflows/      CI/CD

GLOBALER DIFFERENZIATOR:
  API + Legal + Trajectory + Decision Chain + EU AI Act
  = einzige KI-Governance-Plattform die SELBST compliant ist
    UND anderen bei Compliance hilft.

  Das ist wie ein Sicherheitssystem das sich selbst bewacht.
""",
}

for agent, text in GAPS.items():
    icons = {"ORION":"🔭","EIRA":"🌟","DDGK":"🧠","VITALITY":"⚡",
             "GUARDIAN":"🛡️","JURIST":"⚖️","HYPER":"🚀"}
    colors = {"ORION":"blue","EIRA":"cyan","DDGK":"yellow","VITALITY":"bright_cyan",
              "GUARDIAN":"red","JURIST":"bright_red","HYPER":"bright_blue"}
    icon = icons.get(agent,"•")
    color = colors.get(agent,"white")
    if RICH:
        con.print(f"\n  [{color}]{icon} [{agent}][/{color}]")
        con.print(text)
    else:
        print(f"\n  {icon} [{agent}]")
        print(text)

# ─── BAUPLAN ─────────────────────────────────────────────────────────────────
if RICH:
    con.print(Rule("[bold green]BAUPLAN — JETZT IMPLEMENTIEREN[/bold green]"))
    con.print(Panel(
        "[bold]STUFE 1 — HEUTE (diese Session):[/bold]\n"
        "  [red]P0[/red] ddgk_api_server.py          FastAPI REST API + Guardian Auth\n"
        "  [red]P0[/red] ddgk_legal_agent.py         JURIST Vorabversion\n"
        "  [red]P0[/red] ddgk_market_trajectory.py   Trajektorie + κ_market\n\n"
        "[bold]STUFE 2 — DIESE WOCHE:[/bold]\n"
        "  [yellow]P1[/yellow] ddgk_billing.py             Stripe €990/Mo\n"
        "  [yellow]P1[/yellow] ddgk_notifier.py            Email bei REQUIRE_HUMAN\n"
        "  [yellow]P1[/yellow] pilots/tiwag/               Erster Pilot\n"
        "  [yellow]P1[/yellow] paradoxonai.at update       EU AI Act USP\n\n"
        "[bold]Soll ich JETZT starten?[/bold] [dim](ddgk_api_server.py zuerst)[/dim]",
        title="[bold cyan]NÄCHSTE SCHRITTE[/bold cyan]",
        border_style="green"
    ))
else:
    print("\n  BAUPLAN:")
    print("  P0: ddgk_api_server.py, ddgk_legal_agent.py, ddgk_market_trajectory.py")
    print("  P1: ddgk_billing.py, ddgk_notifier.py, pilots/tiwag/")

print(f"\n  Plattform-Reife: {done}/{total} ({100*done//total}%)")
print(f"  P0-Lücken: {len(p0_missing)} | P1-Lücken: {len(p1_missing)}\n")
