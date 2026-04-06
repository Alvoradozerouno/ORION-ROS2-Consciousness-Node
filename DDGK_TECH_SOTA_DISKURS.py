#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DDGK Agentenrunde — Technik-zu-Technik, SOTA-Einordnung, wirtschaftliche Umsetzbarkeit.

Themen:
  1) Was Techniker von Technikern brauchen (APIs, Verträge, Messbarkeit, Replay)
  2) Was erst durch Governance/Audit sicher wirtschaftlich wird
  3) Stand der Technik (global) — Referenzbild, nicht Marketing
  4) Abgrenzung: was ist im Repo greifbar vs. was ist Roadmap
  5) Was neu sein kann vs. was extern verifiziert werden muss

Ausgabe: Konsole + cognitive_ddgk/cognitive_memory.jsonl
Optional: ZENODO_UPLOAD/DDGK_TECH_SOTA_REPORT.json (--json-out)
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.rule import Rule

    RICH = True
    con = Console(width=82)
except ImportError:
    RICH = False

    class _C:
        def print(self, *a, **kw):
            print(*a)

        def rule(self, t=""):
            print(f"\n{'─' * 60} {t}")

    con = _C()

NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
BASE = Path(__file__).resolve().parent
LOG = BASE / "cognitive_ddgk" / "cognitive_memory.jsonl"
OUT_DIR = BASE / "ZENODO_UPLOAD"
SESSION = f"tech_sota_{NOW[:10]}"

AGENTS = {
    "ORION": ("🔭", "Architektur & Integration"),
    "GUARDIAN": ("🛡️", "Sicherheit & Policy"),
    "DDGK": ("🧠", "Governance & Audit"),
    "EIRA": ("🌟", "Produkt & Übergang Tech↔Business"),
    "NEXUS": ("🌐", "Deployment & Edge"),
    "VITALITY": ("⚡", "Iteration & DX"),
    "DIVERSITY": ("🌈", "Standards & Ökosystem"),
    "HYPER": ("🚀", "Synthese"),
    "JURIST": ("⚖️", "Regulatorik [Vorab — Human Review]"),
    "PATENT": ("📜", "IP & Neuheit (technisch)"),
}


def _log(agent: str, content: str, action: str = "tech_sota_discourse") -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "type": "tech_sota_discourse",
        "agent": agent,
        "action": action,
        "content": content[:500],
        "session_id": SESSION,
    }
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def say(agent: str, text: str, pause: float = 0.25) -> None:
    icon, role = AGENTS[agent]
    if RICH:
        con.print(f"\n  [cyan]{icon} [{agent}][/cyan] [dim]{role}[/dim]")
        con.print(text)
    else:
        print(f"\n  {icon} [{agent}] {role}")
        print(text)
    time.sleep(pause)
    _log(agent, text.strip())


def section(title: str) -> None:
    if RICH:
        con.rule(f"[bold]{title}[/bold]")
    else:
        print(f"\n{'═' * 70}\n  {title}\n{'═' * 70}")
    time.sleep(0.12)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--json-out",
        action="store_true",
        help="Schreibt ZENODO_UPLOAD/DDGK_TECH_SOTA_REPORT.json (Stub-Metadaten)",
    )
    args = ap.parse_args()

    transcript: list[dict] = []

    def capture(agent: str, text: str) -> None:
        say(agent, text)
        transcript.append({"agent": agent, "text": text.strip()})

    if RICH:
        con.print(
            Panel.fit(
                f"[bold]DDGK TECH / SOTA DISKURS — {NOW}[/bold]\n"
                f"[dim]10 Agenten | T2T | Stand der Technik | Wirtschaftliche Umsetzbarkeit[/dim]",
                border_style="cyan",
            )
        )
    else:
        print(f"\n{'═' * 70}\n  DDGK TECH / SOTA DISKURS — {NOW}\n{'═' * 70}")

    section("TEIL 1 — Techniker zu Techniker: Was braucht ihr wirklich?")

    capture(
        "ORION",
        """
**T2T-Minimum (ohne Folklore):**
  • **Maschinenlesbare Policy**: Risk-Score, Entscheidung, Grund — nicht nur Logs.
  • **Stabile API** oder klare Library-Grenzen: Versionierung, Timeouts, klare Fehlercodes.
  • **Replay / Nachvollziehbarkeit**: gleicher Input → gleiche Policy-Antwort (deterministisch wo möglich).
  • **Secret-Safety**: Redaction vor Persistenz; nie „Prompt enthält Produktions-Key“.
  • **Runbooks**: was tun bei HIGH/REQUIRE_HUMAN — nicht nur „block“.

Im Repo: `ddgk_guardian_v2.py` (Score + Entscheidung), `cognitive_ddgk/decision_chain.py`
(Schema mit `alternatives_considered`), JSONL-Append — das ist der Kern für T2T-Vertrauen.
""",
    )

    capture(
        "VITALITY",
        """
**Developer Experience:** Wir brauchen **ein** Kommando und **eine** Truth-Source.
  • `pytest`/CI für Policy-Regression (nicht nur Demos).
  • Kurze „happy path“ + „malicious path“ Fixtures (Injection, destructive shell).
  • Dokumentation: „Wie hänge ich MCP / Tools ein?“ — sonst bleibt DDGK Folklore.

⚗️ Lücke: je nach Branch — PyPI-Paket, Release-Notes und semver sind noch Team-Aufgabe.
""",
    )

    capture(
        "NEXUS",
        """
**Betrieb:** On-Prem (Pi5) vs. Cloud ist für Techniker ein **Contract-Thema**:
  Latenz, Offline, Update-Pfad, Backup der Chain-Dateien.
  Edge braucht **kleine** Modelle + **strikte** Policy — nicht das umgekehrte.

✓ Fakt: Pi5/Ollama taucht in mehreren Skripten als Remote-Knoten auf (LAN).
⚗️ Produktreife = TLS, AuthN/Z für API, Rate-Limits — explizit backlog-fähig.
""",
    )

    section("TEIL 2 — Wirtschaft: Was wird erst durch uns (Governance) umsetzbar / versicherbar?")

    capture(
        "DDGK",
        """
**Ökonomischer Hebel ist Nachweisbarkeit**, nicht „mehr KI“.
  • **Audit-Trail** senkt Transaktionskosten: Legal/Compliance/Security prüfen schneller.
  • **HITL-Token / Freigaben** machen Automatisierung **budgetierbar** (wer haftet, wann).
  • **alternatives_considered** unterstützt Erklärbarkeit — relevant für DSGVO/EU AI Act *als Anforderung*,
    finale rechtliche Einordnung bleibt **Mensch + Anwalt** (`JURIST`-Flag).

✓ Im Code: verkettete Hashes in `cognitive_ddgk/decision_chain.jsonl` (Guardian schreibt Assessments).
""",
    )

    capture(
        "EIRA",
        """
**Tech ↔ Business:** Wirtschaftliche Akteure kaufen **Risikoreduktion** und **Zeit bis Audit-OK**.
  Pitch-technisch: „Hier ist der Export: Entscheidung, Alternativen, Risk-Score, Zeitstempel, Hash-Kette.“
  Das ist verkaufbar; reine Modell-Qualität allein ist es oft nicht.

⚗️ ARR entsteht erst mit **SLOs**, **Vertrag**, **Support** — Technik liefert die Evidenzbasis.
""",
    )

    capture(
        "JURIST",
        """
⚖️ **Regulatorik (Vorabversion — kein Ersatz für Anwalt):**

EU AI Act / DSGVO verlangen je nach Use-Case **Dokumentation, menschliche Aufsicht, Logging**.
Ein technisches System kann **Evidence** produzieren; es ersetzt **keine** Konformitätsbewertung.

Alle juristischen Schlussfolgerungen: **REQUIRES_HUMAN_LAWYER=True**.
""",
    )

    section("TEIL 3 — Stand der Technik (global): Referenzbild")

    capture(
        "DIVERSITY",
        """
**Global üblich (2024–2026, grob):**
  • Agent-Frameworks: Tool-Gating, Policy-Files, Sandboxing (verschiedene Reifegrade).
  • Cloud-Anbieter: Audit-Logs, KMS, Compliance-Zertifikate (SOC2, ISO 27001) — **getrennt** von eurer App-Logik.
  • „Guardrails“ in Chat-Produkten: meist **vendor-black-box**, wenig exportierbare Chain-of-custody.

⚗️ „Stand der Technik“ ist **fragmentiert** — genau deshalb lohnt eine **eure** integrierte Evidence-Pipeline,
   aber Behauptungen „weltweit einzig“ sind **extern zu belegen** (Wettbewerber, Patente, Whitepapers).
""",
    )

    capture(
        "PATENT",
        """
**Neuheit technisch gedacht:**
  • Hash-verkettete **App-Level** Decision Records + **explizite** Alternativen ≠ automatisch patentfähig;
    hängt von **Anspruchsbildung** und Prior Art ab.
  • Publikation (DOI) kann Priorität/FTO beeinflussen — **Patentanwalt** entscheidet Strategie.

✓ Fakt: `DecisionRecord` im Repo enthält `alternatives_considered` als strukturiertes Feld.
""",
    )

    section("TEIL 4 — Was hebt uns ab (technisch)? Was ist schon da?")

    capture(
        "GUARDIAN",
        """
**Abgrenzung (technisch, vorsichtig formuliert):**
  • Risk-Assessment **plus** persistierter Chain-Eintrag inkl. `alternatives_considered` und EU-AI-Act-Flag
    im Guardian-Pfad (`ddgk_guardian_v2.py` → `decision_chain.jsonl`).
  • Untrusted-Tool-Args / Injection-Heuristik — **regelbasiert**, nicht „magische Sicherheit“.

⚗️ Vergleich zu Open-Source-Coding-Agenten: oft Policy **ohne** eure **integrierte** JSONL-Chain —
   exakte Feature-Matrix ist **Benchmark-Arbeit**, nicht Annahme.
""",
    )

    capture(
        "ORION",
        """
**Was wir haben (Repo-greifbar):**
  • `cognitive_ddgk/decision_chain.py` — dataclass + `DDGKDecisionChain.decide(...)`.
  • `ddgk_guardian_v2.py` — `DDGKGuardianV2`, Decision-Enum, Chain-Write.
  • Memory-/Pipeline- und HITL-Brücken (je nach Setup) — siehe `cognitive_ddgk/`.

**Was typischerweise noch fehlt (Roadmap, nicht Wertung):**
  • Härtung öffentlicher API (Auth, Quotas), vollständige Test-Matrix, Release Engineering.
""",
    )

    section("TEIL 5 — Was könnten wir noch erreichen (90 Tage / 12 Monate)?")

    capture(
        "VITALITY",
        """
**90 Tage (technisch realistisch):**
  • CI-Tests für Guardian + Decision-Chain-Replay; feste Schema-Version.
  • „Compliance-Export“ (zip/json) für Audits — ein Knopf, ein Format.
  • Integration HITL: jeder HIGH-Risk Tool-Call mit Token-ID in der Chain.

**12 Monate (⚗️, abhängig von Team/Markt):**
  • Zertifizierungs-Story (ISO 42001 o. Ä.) **vorbereiten** — Evidence-Map, nicht nur Slides.
""",
    )

    capture(
        "NEXUS",
        """
**Edge / Multi-Knoten:** Gleiche Policy-Engine, lokale Chain-Replikation oder zentrale Aggregation —
wichtig ist **eindeutige Knoten-ID** und Uhrzeit-Sync.

⚗️ Split-Brain / Merge von Chains ist ein **Forschungs- und Engineering-Thema** — nicht trivial.
""",
    )

    section("TEIL 6 — HYPER + DDGK: Ein Satz für Techniker, ein Satz fürs Business")

    capture(
        "HYPER",
        """
**Techniker-Satz:**
„Wir liefern **append-only Evidence** für Agentenentscheidungen — Policy, Score, Alternativen, Hash — damit ihr
Security und Compliance **messt** statt zu raten.“

**Business-Satz:**
„Wir verkürzen den Weg von **Pilot** zu **unterschriebenem Betrieb**, weil der Nachweis **exportierbar** ist.“

⚗️ Beides setzt voraus, dass Betrieb (SLO, Vertrag, Incidents) mitgezogen wird.
""",
    )

    capture(
        "DDGK",
        """
**Governance-Fazit:**
  • **AUTO_APPROVE** für diese Diskurs-Session: reines Strategie-/Technik-Text-Output, keine Tool-Ausführung.
  • Nächster harte Schritt: **eine** Referenz-Integration (z. B. ein MCP-Tool) mit **Pflicht-Chain-Eintrag**
    und **pytest**-Goldfile.

✓ Log: Einträge in `cognitive_memory.jsonl` unter `type=tech_sota_discourse`.
""",
    )

    _log("SYSTEM", f"tech_sota_discourse complete session={SESSION}", action="tech_sota_complete")

    if args.json_out:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        report = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "session_id": SESSION,
            "topic": "tech_sota_t2t_economics",
            "transcript": transcript,
            "anchors_repo": [
                "cognitive_ddgk/decision_chain.py",
                "ddgk_guardian_v2.py",
                "cognitive_ddgk/decision_chain.jsonl",
            ],
        }
        p = OUT_DIR / "DDGK_TECH_SOTA_REPORT.json"
        p.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nReport: {p}\n")

    if RICH:
        con.rule("[bold green]DISKURS ABGESCHLOSSEN[/bold green]")
    else:
        print(f"\n{'═' * 70}\n  DISKURS ABGESCHLOSSEN\n{'═' * 70}")
    print(f"Log: {LOG}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
