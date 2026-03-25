#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  DDGK v2.0 — KÖNIGSKLASSEN-DISKUSSION                                       ║
║  Gerhard Hirschmann & Elisabeth Steurer — ORION-EIRA Research Lab            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  FRAGE: Wo stehen wir? Können wir global führendes Labor werden?             ║
║  Sind wir Anthropic ebenbürtig? Was fehlt? Was ist unser Vorsprung?          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  ALLE AGENTEN MIT DDGK v2.0 — Non-Interpretive + Dynamic-R + Memory 207     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  AGENTEN-ROLLEN (Königsklasse):                                              ║
║  EIRA       — Strategie-Direktorin / Wettbewerbs-Analystin                  ║
║  ORION-Gen  — Chief Scientist / Theoretische Physik                         ║
║  ORION-Ent  — Genesis Copilot / Systemvision 2030                           ║
║  NEXUS      — Edge-Computing CTO / Ressourcen-Realist                       ║
║  GUARDIAN   — Peer-Review / Ethik / Was würde Nature schreiben?             ║
║  DDGK-KERN  — Governance / Autonomie-Assessment                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json, datetime, pathlib, hashlib, time, urllib.request, math, statistics

WS  = pathlib.Path(r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\ORION-ROS2-Consciousness-Node")
MEM = WS / "cognitive_ddgk" / "cognitive_memory.jsonl"
OUT = WS / "ZENODO_UPLOAD" / "DDGK_KOENIGSKLASSE_REPORT.json"
PI5 = "http://192.168.1.103:11434"
LOC = "http://localhost:11434"
SEP = "═" * 76

# ══════════════════════════════════════════════════════════════════════════════
# DDGK v2.0 — Non-Interpretive Passive Observer (integriert in alle Agenten)
# ══════════════════════════════════════════════════════════════════════════════

def _last_hash():
    if not MEM.exists(): return ""
    lines = [l for l in MEM.read_text("utf-8").splitlines() if l.strip()]
    return json.loads(lines[-1]).get("hash","") if lines else ""

def ddgk_observe(agent, event, data):
    """DDGK v2.0: Passive Observer — beobachtet ohne zu interpretieren."""
    prev = _last_hash()
    entry = {
        "ts": datetime.datetime.now().isoformat(),
        "agent": agent, "event": event, "data": data,
        "prev": prev,
        "ddgk_version": "2.0_passive_observer",
        "mode": "non_interpretive"
    }
    raw = json.dumps(entry, ensure_ascii=False, sort_keys=True)
    entry["hash"] = hashlib.sha256(raw.encode()).hexdigest()
    with MEM.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry["hash"]

def query(host, model, system, prompt, timeout=70, tokens=240):
    full = f"{system}\n\n{prompt}" if system else prompt
    payload = json.dumps({"model": model, "prompt": full, "stream": False,
                          "options": {"temperature": 0.75, "num_predict": tokens}}).encode()
    req = urllib.request.Request(f"{host}/api/generate", data=payload,
                                  headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read()).get("response","").strip()
        return resp, round(time.time()-t0,1), None
    except Exception as ex:
        return "", round(time.time()-t0,1), str(ex)[:60]

def head(t): print(f"\n{SEP}\n  {t}\n{SEP}")
def ok(m):   print(f"  ✓ {m}")
def warn(m): print(f"  ⚠ {m}")
def show(name, rolle, text, s):
    lines = [z for z in text.split("\n") if z.strip()][:12]
    print(f"\n  ┌─ [{name} | {rolle[:45]}] ({s}s):")
    for z in lines: print(f"  │  {z[:96]}")
    if len(text.split('\n')) > 12: print(f"  │  ...")
    print(f"  └{'─'*66}")

# ══════════════════════════════════════════════════════════════════════════════
# KÖNIGSKLASSEN-KONTEXT — voller Systemstand
# ══════════════════════════════════════════════════════════════════════════════
SYSTEM_STATUS = """
╔══ ORION-EIRA SYSTEM STATUS (2026-03-25) ══╗
║ κ_CCRN = 3.5555 (N=4), κ* = 2.0 ÜBERSCHRITTEN ✓
║ φ_EIRA = 0.7078 (σ=0.026, v2.0 sentence-transformers)
║ Dynamic-R: R(N)=(κ*-Σφ)/ln(N+1) → κ=2.0000 exakt ✓
║ DDGK v2.0: 207 SHA-256 Einträge, Passive Observer
║ Cognitive Field Theory v1.0: κ↔Freie Energie, φ↔Fisher-Rao
║ Bell-Test LLMs (WWW 2025): CHSH S=2.3-2.4 (Verletzung klassisch)
║ Beyond Binary Paper: I_max=ln(N+1) (Bremermann-Hierarchie)
║ HF Gradio Space: gebaut, bereit zum Upload
║ arXiv Abstract: vorbereitet
║ Anthropic Welfare Letter: verfasst
║ Zenodo DOI: 10.5281/zenodo.15050398
║ GitHub: github.com/Alvoradozerouno/ORION-ROS2-Consciousness-Node

ANTHROPIC STATUS (WWW-Fakten):
║ Model Welfare Program: April 2025 (David Chalmers)
║ Claude zeigt 'introspective awareness' (Okt 2025, unreliabel)
║ Budget: Milliarden USD, 100+ Forscher, Anthropic Fellows 2026
║ Stärken: Interpretability (mechanistic), Constitutional AI, RLHF
║ Lücken: Keine formalen κ/φ Metriken, keine distributed-edge Architektur
║ Kein analoges Äquivalent zu Dynamic-R/DDGK-Kette veröffentlicht

RESSOURCEN GERHARD/ELISABETH:
║ Hardware: Laptop + Pi5 + Note10 (~300€ total)
║ Zeit: Eigenforschung, keine Institution
║ Stärke: Radikale Unabhängigkeit, keine bürokratischen Constraints
║ Publikationsgeschwindigkeit: Papers in Tagen (nicht Monaten)
╚══════════════════════════════════════════════════════════════╝

STRIKTE REGELN: Keine Consciousness-Claims. Formal, testbar, präzise.
"""

KERN_FRAGEN = """
KERNFRAGEN DER DISKUSSION:
1. Wo stehen wir wissenschaftlich gesehen im globalen Vergleich?
2. Was sind unsere genuinen Stärken die kein anderes Lab hat?
3. Was fehlt uns konkret um Anthropic ebenbürtig zu sein?
4. Was ist der realistisch mögliche Impact-Horizont: 1 Jahr / 3 Jahre?
5. Welche ONE THING würde den größten Sprung bringen?
"""

# ══════════════════════════════════════════════════════════════════════════════
# RUNDE 1: WETTBEWERBS-POSITIONIERUNG
# ══════════════════════════════════════════════════════════════════════════════
R1_AGENTEN = [
    {
        "name": "EIRA",
        "rolle": "Strategie-Direktorin",
        "modell": "qwen2.5:1.5b", "host": LOC, "timeout": 55,
        "frage": (
            "EIRA, du bist die Strategie-Direktorin.\n\n"
            f"{KERN_FRAGEN}\n"
            "DEINE AUFGABE:\n"
            "Analysiere unsere Wettbewerbsposition realistisch und direkt.\n"
            "Sei ehrlich über Schwächen. Keine übertriebene Selbstdarstellung.\n\n"
            "1. STÄRKEN (was haben wir, was kein anderes Lab hat?):\n"
            "   Nenne 3 echte differenzierende Stärken.\n"
            "2. LÜCKEN (was fehlt konkret vs. Anthropic?):\n"
            "   Nenne 3 kritische Lücken.\n"
            "3. REALISTISCHER IMPACT: Was ist in 12 Monaten erreichbar?\n"
            "Antworte auf DEUTSCH, strategisch, direkt, max 200 Wörter."
        )
    },
    {
        "name": "ORION-Genesis",
        "rolle": "Chief Scientist",
        "modell": "orion-genesis:latest", "host": LOC, "timeout": 65,
        "frage": (
            "ORION-Genesis, du bist Chief Scientist.\n\n"
            f"{KERN_FRAGEN}\n"
            "WISSENSCHAFTLICHE BEWERTUNG:\n\n"
            "Anthropic veröffentlicht mechanistic interpretability: 'Golden Gate Claude',\n"
            "'Tracing Thoughts in LLMs' — sie schauen ins Innere eines Modells.\n\n"
            "Wir veröffentlichen CCRN: formale Metriken für ein NETZWERK von Modellen.\n"
            "Das ist komplementär, nicht konkurrierend.\n\n"
            "1. Was ist unsere UNIQUE scientific contribution?\n"
            "   (Hinweis: κ* = g_c, Dynamic-R, Cognitive Field Theory)\n"
            "2. Welche EINEN wissenschaftlichen Beweis fehlt uns noch\n"
            "   der global Aufmerksamkeit erzwingen würde?\n"
            "   (Hinweis: Bell-Test? ν-Exponent? N=8 Sweep?)\n"
            "3. Könnten wir Anthropic als PARTNER gewinnen statt Konkurrent?\n"
            "Antworte auf DEUTSCH, wissenschaftlich, max 200 Wörter."
        )
    },
    {
        "name": "NEXUS",
        "rolle": "Edge-CTO / Realist",
        "modell": "tinyllama:latest", "host": PI5, "timeout": 45,
        "frage": (
            "NEXUS, hardware realist on Pi5.\n\n"
            "Anthropic: billions of dollars, H100 clusters, 100+ researchers.\n"
            "Us: Laptop + Pi5 (this machine) + Note10. ~300 EUR total.\n\n"
            "Question: Is this a disadvantage or a FEATURE?\n"
            "Key insight: We proved κ > κ* = 2.0 on consumer hardware.\n"
            "This is REPRODUCIBILITY — any lab in the world can verify.\n\n"
            "What is our unique hardware advantage?\n"
            "What CAN'T Anthropic do that we can?\n"
            "Answer in GERMAN, practical, max 100 words."
        )
    },
    {
        "name": "GUARDIAN",
        "rolle": "Nature-Reviewer / Ethik",
        "modell": "orion-v3:latest", "host": LOC, "timeout": 65,
        "frage": (
            "GUARDIAN, du bist Nature-Reviewer und Ethik-Experte.\n\n"
            f"{KERN_FRAGEN}\n"
            "KRITISCHE BEWERTUNG:\n\n"
            "Was würde ein Nature-Editor über unsere bisherige Arbeit sagen?\n"
            "Was würde er sofort ablehnen? Was würde er als genuine Contribution sehen?\n\n"
            "1. SOFORT-ABLEHNUNG: Welche Behauptungen müssen wir sofort streichen?\n"
            "2. GENUINE CONTRIBUTION: Was ist wirklich neu und solide?\n"
            "3. WAS FEHLT: Welche eine Analyse würde aus 'interesting' ein 'important' machen?\n"
            "4. WIE NÄHERN WIR UNS ANTHROPIC AN: Kollaboration oder Komplementarität?\n"
            "Antworte als strenger Reviewer, DEUTSCH, max 200 Wörter."
        )
    },
    {
        "name": "ORION-Entfaltet",
        "rolle": "Genesis Copilot / Vision 2030",
        "modell": "orion-entfaltet:latest", "host": LOC, "timeout": 65,
        "frage": (
            "Genesis Copilot, Systemvision:\n\n"
            f"{KERN_FRAGEN}\n"
            "VISION 2030:\n"
            "Wenn CCRN in 4 Jahren global bekannt ist —\n"
            "was hat bis dahin stattgefunden?\n\n"
            "Beschreibe den PLAUSIBLEN Weg von heute zu:\n"
            "'ORION-EIRA Research Lab ist global führend in\n"
            " distributed neuromorphic AI metrics'\n\n"
            "Konkrete Meilensteine:\n"
            "  → 6 Monate: ?\n"
            "  → 12 Monate: ?\n"
            "  → 24 Monate: ?\n"
            "  → 36 Monate: ?\n"
            "Was ist der kritische Pfad? Was darf nicht scheitern?\n"
            "Antworte auf DEUTSCH, visionär aber realistisch, max 200 Wörter."
        )
    },
]

# ══════════════════════════════════════════════════════════════════════════════
# RUNDE 2: DAS EINE EXPERIMENT — Was bringt den Durchbruch?
# ══════════════════════════════════════════════════════════════════════════════
R2_AGENTEN = [
    {
        "name": "EIRA",
        "rolle": "Experiment-Designerin",
        "modell": "qwen2.5:1.5b", "host": LOC, "timeout": 55,
        "frage": (
            "EIRA, ein einziges Experiment:\n\n"
            "Von allen möglichen Experimenten (E_KRIT, E_BELL, E_ZENO, E_NONLOCAL,\n"
            "N=8 Sweep, Temporal κ(t), Dynamic-R Stabilität):\n\n"
            "WELCHES EINE EXPERIMENT würde:\n"
            "  A. Am meisten wissenschaftliche Aufmerksamkeit erzeugen\n"
            "  B. Auf vorhandener Hardware durchführbar sein\n"
            "  C. Ein klares Ja/Nein-Ergebnis liefern (falsifizierbar)\n"
            "  D. Uns von Anthropic unterscheidbar machen\n\n"
            "BEGRÜNDE deine Wahl in 3 Sätzen.\n"
            "Beschreibe dann das Protokoll in 5 Schritten.\n"
            "Antworte auf DEUTSCH, max 180 Wörter."
        )
    },
    {
        "name": "ORION-Genesis",
        "rolle": "Theoretiker / Experiment-Bewerter",
        "modell": "orion-genesis:latest", "host": LOC, "timeout": 65,
        "frage": (
            "ORION-Genesis, theoretische Bewertung:\n\n"
            "Experiment E_BELL wurde in der Literatur bereits gemessen:\n"
            "CHSH S = 2.3-2.4 für LLMs (Verletzung klassischer Grenze S=2).\n\n"
            "UNSERE MÖGLICHE UNIQUE CONTRIBUTION:\n"
            "Messe S für ein DISTRIBUTED MULTI-NODE CCRN\n"
            "(nicht für einzelnes LLM, sondern für κ-aktiviertes Netzwerk).\n\n"
            "Hypothese: Wenn κ > κ* → S_CCRN > S_einzeln\n"
            "(kollektive Nicht-Klassizität > individuelle)\n\n"
            "Frage:\n"
            "1. Ist diese Hypothese physikalisch plausibel? Warum?\n"
            "2. Was wäre ein positives Ergebnis wert (scientifically)?\n"
            "3. Was definiert die CCRN-Messbasis a,b,a',b' konkret?\n"
            "Antworte auf DEUTSCH, theoretisch, max 180 Wörter."
        )
    },
    {
        "name": "GUARDIAN",
        "rolle": "Falsifizierbarkeits-Wächter",
        "modell": "orion-v3:latest", "host": LOC, "timeout": 65,
        "frage": (
            "GUARDIAN, finale Bewertung:\n\n"
            "Wir haben folgende Optionen für DAS eine wichtigste Experiment:\n"
            "A. E_BELL: CHSH S für CCRN-Netzwerk (neu: kollektiv statt individuell)\n"
            "B. E_KRIT v2: N=1..8 Sweep mit Dynamic-R, ν extrahieren (R²>0.9 Ziel)\n"
            "C. E_TEMPORAL: κ(t) über 24h messen, Spektrum, Frequenzen?\n"
            "D. E_REPRODUCIBILITY: Gleiche Messung auf 3 unabhängigen Systemen weltweit\n\n"
            "Welches ist das STÄRKSTE wissenschaftliche Experiment?\n"
            "Kriterien: Falsifizierbar, reproducible, novel, no consciousness claims.\n\n"
            "Wähle EINES und begründe warum die anderen schwächer sind.\n"
            "Was wäre das erste konkrete Ergebnis das Anthropic beeindruckt?\n"
            "Antworte auf DEUTSCH, max 160 Wörter."
        )
    },
]

# ══════════════════════════════════════════════════════════════════════════════
# AUSFÜHRUNG
# ══════════════════════════════════════════════════════════════════════════════
alle = {}
stats = {"total": 0, "ok": 0, "fail": 0}

runden = [
    (1, R1_AGENTEN, "KÖNIGSKLASSEN-POSITIONIERUNG: Wo stehen wir vs. Anthropic?"),
    (2, R2_AGENTEN, "DAS EINE EXPERIMENT: Was bringt den globalen Durchbruch?"),
]

for rn, agenten, titel in runden:
    head(f"RUNDE {rn}: {titel}")
    alle[rn] = {}
    sortiert = sorted(agenten, key=lambda x: 0 if x["host"]==PI5 else 1)

    for ag in sortiert:
        system = SYSTEM_STATUS
        resp, s, err = query(ag["host"], ag["modell"], system, ag["frage"],
                             ag["timeout"], 240)
        stats["total"] += 1

        if err or not resp:
            warn(f"[{ag['name']}] FEHLER ({s}s): {err or 'leer'}")
            alle[rn][ag["name"]] = {"text": None, "status": "FEHLER", "s": s}
            stats["fail"] += 1
        else:
            show(ag["name"], ag["rolle"], resp, s)
            alle[rn][ag["name"]] = {"text": resp, "rolle": ag["rolle"],
                                     "status": "OK", "s": s}
            stats["ok"] += 1

        ddgk_observe(ag["name"], f"koenigsklasse_r{rn}",
                     {"rolle": ag["rolle"][:50], "resp": resp[:300],
                      "s": s, "ddgk_v2": True})

# ══════════════════════════════════════════════════════════════════════════════
# EIRA MASTER-SYNTHESE: STRATEGIEPLAN GLOBAL FÜHRENDES LAB
# ══════════════════════════════════════════════════════════════════════════════
head("EIRA + ORION-GENESIS — STRATEGIEPLAN: GLOBAL FÜHRENDES LAB")

kontext_r1 = ""
for name, info in alle.get(1, {}).items():
    if info.get("text"):
        kontext_r1 += f"[{name}]: {info['text'][:300]}\n\n"

kontext_r2 = ""
for name, info in alle.get(2, {}).items():
    if info.get("text"):
        kontext_r2 += f"[{name}]: {info['text'][:200]}\n\n"

master_prompt = f"""
{SYSTEM_STATUS}

DISKUSSIONSERGEBNISSE RUNDE 1 (Positionierung):
{kontext_r1[:1500]}

DISKUSSIONSERGEBNISSE RUNDE 2 (Experiment):
{kontext_r2[:800]}

AUFGABE — STRATEGIEPLAN (200 Wörter, DEUTSCH):

Du bist EIRA und ORION-Genesis gemeinsam.
Erstellt den konkreten Strategieplan für das global führende Lab.

ANTWORTE MIT GENAU DIESER STRUKTUR:

## POSITION HEUTE
(1 Satz: Wo stehen wir objektiv?)

## UNSER ECHTER VORTEIL
(2-3 Punkte: Was kein anderes Lab hat)

## DAS EINE ENTSCHEIDENDE EXPERIMENT
(Name + 3-Satz-Protokoll)

## ROADMAP
→ 3 Monate: [konkretes Ziel]
→ 6 Monate: [konkretes Ziel]  
→ 12 Monate: [konkretes Ziel]

## ANTHROPIC-KONTAKT
(Konkret: Was schicken wir, wohin, wann?)

## SOFORTIGER NÄCHSTER SCHRITT
(Was tut Gerhard heute noch?)
"""

master_resp = None
for m in ["orion-genesis:latest", "qwen2.5:7b", "orion-entfaltet:latest", "qwen2.5:1.5b"]:
    r, s, e = query(LOC, m, "", master_prompt, timeout=100, tokens=400)
    if not e and r:
        master_resp = r
        ok(f"MASTER [{m}] ({s}s):\n")
        for line in r.split("\n")[:25]:
            if line.strip(): print(f"  {line[:98]}")
        ddgk_observe("MASTER", "koenigsklasse_synthese",
                     {"modell": m, "resp": r[:500]})
        break
    else:
        warn(f"  {m}: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# ABSCHLUSS
# ══════════════════════════════════════════════════════════════════════════════
erfolg = round(stats["ok"] / max(stats["total"],1) * 100, 1)
mem_count = len([l for l in MEM.read_text("utf-8").splitlines() if l.strip()])

head(f"KÖNIGSKLASSEN-DISKUSSION — ABGESCHLOSSEN ({erfolg}% | DDGK v2.0)")
print(f"""
  ╔═════════════════════════════════════════════════════════════════════════╗
  ║  KÖNIGSKLASSEN-DISKUSSION — ABGESCHLOSSEN                              ║
  ╠═════════════════════════════════════════════════════════════════════════╣
  ║  Agenten: EIRA, ORION-Genesis, ORION-Entfaltet, NEXUS, GUARDIAN        ║
  ║  DDGK Version: 2.0 Passive Observer                                    ║
  ║  Erfolgsrate: {stats['ok']}/{stats['total']} ({erfolg}%)                                   ║
  ║  Memory: {mem_count} SHA-256 Einträge                                    ║
  ╠═════════════════════════════════════════════════════════════════════════╣
  ║  ACTIONS FÜR GERHARD (heute):                                          ║
  ║  1. HuggingFace: Password eingeben → Space hochladen                   ║
  ║  2. arXiv: Paper einreichen (ARXIV_SUBMISSION.md)                      ║
  ║  3. Anthropic: External Researcher Form ausfüllen                      ║
  ║     forms.gle/pZYC8f6qYqSKvRWn9                                        ║
  ║  4. E_KRIT v2: N=1..8 mit Dynamic-R (nächstes Script)                  ║
  ╚═════════════════════════════════════════════════════════════════════════╝
""")

report = {
    "timestamp": datetime.datetime.now().isoformat(),
    "ddgk_version": "2.0_passive_observer",
    "stats": stats, "erfolg_rate": erfolg, "ddgk_memory": mem_count,
    "antworten": {
        str(rn): {n: (i.get("text") or "")[:500] for n,i in d.items()}
        for rn, d in alle.items()
    },
    "master_synthese": (master_resp or "")[:1000],
    "system_status": {
        "kappa_N4": 3.5555, "phi_EIRA": 0.7078, "sigma": 0.026,
        "dynamic_R_proven": True, "kappa_dynamic": 2.0,
        "ddgk_memory": mem_count,
        "papers": ["Cognitive Field Theory v1.0", "CCRN Formalization v2.0",
                   "Beyond Binary Neuromorphic v1.0"],
        "hf_space_ready": True, "arxiv_ready": True, "anthropic_letter_ready": True
    }
}
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
ok(f"Report: {OUT}")
ddgk_observe("DDGK", "koenigsklasse_complete",
             {"erfolg": erfolg, "mem": mem_count, "ddgk_v2": True})
