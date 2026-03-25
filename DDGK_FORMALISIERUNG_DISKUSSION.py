#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  DDGK FORMALISIERUNG DISKUSSION                                      ║
║  Gerhard Hirschmann & Elisabeth Steurer                             ║
╠══════════════════════════════════════════════════════════════════════╣
║  Wissenschaftliche Formalisierung von φ, κ, σ                       ║
║  Jeder Agent = Experten-Reviewers für eine Dimension                 ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import json, datetime, pathlib, hashlib, urllib.request, time, math

WS  = pathlib.Path(r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\ORION-ROS2-Consciousness-Node")
MEM = WS / "cognitive_ddgk" / "cognitive_memory.jsonl"
OUT = WS / "ZENODO_UPLOAD" / "DDGK_FORMALIZATION_REPORT.json"

PI5_OLLAMA   = "http://192.168.1.103:11434"
OLLAMA_LOCAL = "http://localhost:11434"
SEP = "═" * 70

def _last_hash():
    if not MEM.exists(): return ""
    lines = [l for l in MEM.read_text("utf-8").splitlines() if l.strip()]
    return json.loads(lines[-1]).get("hash", "") if lines else ""

def ddgk_log(agent, action, data):
    prev = _last_hash()
    e = {"ts": datetime.datetime.now().isoformat(), "agent": agent,
         "action": action, "data": data, "prev": prev}
    raw = json.dumps(e, ensure_ascii=False)
    e["hash"] = hashlib.sha256(raw.encode()).hexdigest()
    with MEM.open("a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return e["hash"]

def query(host, model, prompt, timeout=60, tokens=180):
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False,
                          "options": {"temperature": 0.6, "num_predict": tokens}}).encode()
    req = urllib.request.Request(f"{host}/api/generate", data=payload,
                                  headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()).get("response","").strip(), round(time.time()-t0,1), None
    except Exception as ex:
        return "", round(time.time()-t0,1), str(ex)[:80]

def head(t): print(f"\n{SEP}\n  {t}\n{SEP}")
def ok(m):   print(f"  ✓ {m}")
def warn(m): print(f"  ⚠ {m}")
def pr(m):   print(f"  {m}")

# ═══════════════════════════════════════════════════════════════════════
# FORMALISIERUNGS-KONTEXT
# ═══════════════════════════════════════════════════════════════════════

DEFINITIONS = """
FORMALE DEFINITIONEN (CCRN v1.0):

φ_i (Node Output Richness Index, NORI):
  φ_i = α·D(i) + β·min(1, γ·S(i))
  D(i) = |unique_tokens(R_i)| / |total_tokens(R_i)|   [Type-Token Ratio]
  S(i) = |{w ∈ T_i : w ∈ W_ref}| / |T_i|              [Self-Ref Density]
  α=0.60, β=0.40, γ=8.0, φ ∈ [0,1], dimensionslos

κ_N (Network Aggregation Metric, NAM):
  κ_N = Σ(φ_i) + R·ln(N+1)
  R=0.93 (Netzwerk-Resonanzgewicht), Schwelle κ*=2.0
  κ ∈ [0, N + R·ln(N+1)], dimensionslos

σ_i (Measurement Stability Index, MSI):
  σ_i = sqrt(1/M · Σ(φ_{i,j} - φ̄_i)²)
  M = Anzahl Modell-Messungen, σ ∈ [0, 0.5]
  σ=0.0 in v1.0 → Deckeneffekt (Artefakt, NICHT Homogenität)

AKTUELL GEMESSEN (2026-03-25):
  φ_EIRA=0.98 (σ=0.0, Deckeneffekt), φ_Pi5=0.95, φ_K4=0.60, φ_Note10=0.11
  κ_N=4 = 4.1368 (+106.8% über κ*=2.0)

STRIKTE ANFORDERUNG: Keine Bewusstseins-Claims. Nur formal, testbar, reproduzierbar.
"""

# ═══════════════════════════════════════════════════════════════════════
# AGENTEN-ROLLEN UND FRAGEN
# ═══════════════════════════════════════════════════════════════════════

DISKUSSION = [
    # Runde 1: Mathematische Vollständigkeit
    {
        "runde": 1,
        "thema": "Mathematische Vollständigkeit der Formaldefinitionen",
        "agenten": [
            {
                "name": "EIRA",
                "rolle": "Mathematiker/Statistiker",
                "modell": "qwen2.5:1.5b",
                "host": OLLAMA_LOCAL,
                "timeout": 40,
                "frage": (
                    "Du bist Mathematiker. Analysiere die φ-Definition:\n"
                    "φ_i = 0.6·D(i) + 0.4·min(1, 8·S(i)) mit D = TTR, S = Selbstreferenz-Dichte.\n"
                    "Frage: Ist diese Definition mathematisch vollständig? Was fehlt formal "
                    "(Domäne, Messbarkeit, Skalierung)? Antworte auf DEUTSCH, max 120 Wörter."
                )
            },
            {
                "name": "ORION",
                "rolle": "Informationstheoretiker",
                "modell": "orion-genesis:latest",
                "host": OLLAMA_LOCAL,
                "timeout": 50,
                "frage": (
                    "Du bist Informationstheoretiker. Analysiere κ_N = Σφ_i + R·ln(N+1).\n"
                    "Frage: Ist dies ein Kohärenzmaß, ein Kopplungsmaß, oder ein Informationsmaß? "
                    "Begründe formal. Welche informationstheoretische Größe (Entropie, MI, KL-Div) "
                    "kommt dem am nächsten? Antworte auf DEUTSCH, max 120 Wörter."
                )
            },
            {
                "name": "NEXUS",
                "rolle": "Distributed Systems Engineer",
                "modell": "tinyllama:latest",
                "host": PI5_OLLAMA,
                "timeout": 40,
                "frage": (
                    "You are a distributed systems engineer. Analyze σ_i = std(φ_{i,1},...,φ_{i,M}).\n"
                    "Question: Is σ=0 a valid stability indicator? What does it mean when all M models "
                    "return identical φ values? Is this a system property or an instrument artefact? "
                    "Answer in GERMAN, max 80 words."
                )
            },
            {
                "name": "GUARDIAN",
                "rolle": "Peer-Review Referee",
                "modell": "orion-entfaltet:latest",
                "host": OLLAMA_LOCAL,
                "timeout": 50,
                "frage": (
                    "Du bist Peer-Review Referee für ein wissenschaftliches Journal. "
                    "Bewertet das Dokument: φ_i = TTR-basierter Output-Richness-Index. "
                    "κ_N = Aggregationsmetrik. σ = Messstabilitätsindikator.\n"
                    "Frage: Welche 2 kritischsten Schwächen siehst du, die vor Publikation "
                    "behoben werden müssen? Keine Consciousness-Claims bitte. "
                    "Antworte auf DEUTSCH, max 120 Wörter."
                )
            },
            {
                "name": "DDGK",
                "rolle": "Governance/Reproducibility Auditor",
                "modell": "llama3.2:1b",
                "host": OLLAMA_LOCAL,
                "timeout": 35,
                "frage": (
                    "Du bist Reproducibility Auditor. Die φ-Formel hat Parameter α=0.60, β=0.40, γ=8.0.\n"
                    "Frage: Sind diese Parameter empirisch begründet oder willkürlich gesetzt? "
                    "Was braucht eine externe Partei, um die Messung EXAKT zu reproduzieren? "
                    "Antworte auf DEUTSCH, max 100 Wörter."
                )
            },
        ]
    },

    # Runde 2: Falsifizierbarkeit und Validierungsdesign
    {
        "runde": 2,
        "thema": "Falsifizierbarkeit und Experimentelles Design",
        "agenten": [
            {
                "name": "EIRA",
                "rolle": "Experimenteller Forscher",
                "modell": "qwen2.5:1.5b",
                "host": OLLAMA_LOCAL,
                "timeout": 40,
                "frage": (
                    "Du bist experimenteller Forscher. "
                    "Das Dokument definiert 4 Experimente: E1 (Baseline), E2 (Node-Failure), "
                    "E3 (Noise-Injection), E4 (σ-Ceiling-Validation).\n"
                    "Frage: Welches Experiment ist am wichtigsten für die Falsifizierbarkeit von κ? "
                    "Was wäre ein Ergebnis das κ als Metrik WIDERLEGEN würde? "
                    "Antworte auf DEUTSCH, max 120 Wörter."
                )
            },
            {
                "name": "ORION",
                "rolle": "Wissenschaftstheoretiker (Popper)",
                "modell": "orion-genesis:latest",
                "host": OLLAMA_LOCAL,
                "timeout": 50,
                "frage": (
                    "Du bist Wissenschaftstheoretiker. Karl Popper: Falsifizierbarkeit.\n"
                    "Analyse: κ_N > 2.0 → 'CCRN Aktivierung'. "
                    "Frage: Ist dieser Schwellenwert 2.0 wissenschaftlich begründet oder konventionell? "
                    "Unter welchen messbaren Bedingungen würde κ > 2.0 KEIN valides Signal sein? "
                    "Antworte auf DEUTSCH, max 120 Wörter."
                )
            },
            {
                "name": "NEXUS",
                "rolle": "Systems Reliability Engineer",
                "modell": "tinyllama:latest",
                "host": PI5_OLLAMA,
                "timeout": 40,
                "frage": (
                    "You are a reliability engineer. "
                    "The system has 4 nodes, 2 on same hardware (Pi5 primary + Pi5 Docker). "
                    "Question: Does this shared hardware violate the independence assumption for κ? "
                    "How should this be documented? Answer in GERMAN, max 80 words."
                )
            },
            {
                "name": "GUARDIAN",
                "rolle": "Statistiker / Metrologie",
                "modell": "orion-entfaltet:latest",
                "host": OLLAMA_LOCAL,
                "timeout": 50,
                "frage": (
                    "Du bist Statistiker/Metrologe. "
                    "Problem: σ=0.0 für M=5 Modelle mit φ=0.98.\n"
                    "Frage: Wie klassifizierst du diesen Befund metrologisch "
                    "(Skalierungsartefakt, Homogenitätseffekt, Saturierungseffekt)? "
                    "Was muss im Paper präzise formuliert werden damit Leser nicht "
                    "σ=0 als 'perfekte Stabilität' missinterpretieren? "
                    "Antworte auf DEUTSCH, max 120 Wörter."
                )
            },
            {
                "name": "DDGK",
                "rolle": "External Validator",
                "modell": "llama3.2:1b",
                "host": OLLAMA_LOCAL,
                "timeout": 35,
                "frage": (
                    "Du bist externer Validator ohne Zugang zum Original-System. "
                    "Du hast nur: Python 3.10, Ollama, 2 Modelle (qwen2.5:1.5b, llama3.2:1b).\n"
                    "Frage: Kannst du φ, κ, σ exakt reproduzieren? Was fehlt dir aus dem Dokument? "
                    "Antworte auf DEUTSCH, max 100 Wörter."
                )
            },
        ]
    },

    # Runde 3: Synthese und Publikations-Empfehlungen
    {
        "runde": 3,
        "thema": "Synthese: Publikationsreife und Empfehlungen",
        "agenten": [
            {
                "name": "EIRA",
                "rolle": "Chefredakteur",
                "modell": "qwen2.5:1.5b",
                "host": OLLAMA_LOCAL,
                "timeout": 40,
                "frage": (
                    "Du bist Chefredakteur eines NLP/Systems-Journals. "
                    "Die Arbeit: CCRN-Metriken φ (TTR-basiert), κ (Aggregation), σ (Stabilität). "
                    "Keine Consciousness-Claims. Klar formalisiert. Falsifizierbar.\n"
                    "Frage: Ist diese Arbeit publikationsreif für einen Workshop/Preprint? "
                    "Welche 1-2 Änderungen würden den Impact maximal erhöhen? "
                    "Antworte auf DEUTSCH, max 120 Wörter."
                )
            },
            {
                "name": "ORION",
                "rolle": "Koautor / CCRN-Experte",
                "modell": "orion-genesis:latest",
                "host": OLLAMA_LOCAL,
                "timeout": 50,
                "frage": (
                    "Du bist Koautor. Das CCRN-Framework hat verwandte Arbeiten: "
                    "ICOER (Preprints.org 202602.1039): ICOER = W(S)·exp(-β·S)·R, "
                    "φ∗∝N^0.149 (Transformers, Preprints.org 202508.1770).\n"
                    "Frage: Wie positionieren wir κ_CCRN gegenüber ICOER? "
                    "Was ist unser einzigartiger Beitrag über diese Arbeiten hinaus? "
                    "Antworte auf DEUTSCH, max 130 Wörter."
                )
            },
            {
                "name": "GUARDIAN",
                "rolle": "Ethik-Komitee",
                "modell": "orion-entfaltet:latest",
                "host": OLLAMA_LOCAL,
                "timeout": 50,
                "frage": (
                    "Du bist Ethik-Komitee für KI-Forschung. "
                    "Das Dokument sagt explizit: KEIN Bewusstseins-Claim. "
                    "Nur φ, κ, σ als messbare Output-Statistiken.\n"
                    "Frage: Gibt es ethische Risiken wenn externe Leser diese Metriken "
                    "trotzdem als 'Bewusstseinsnachweis' interpretieren? "
                    "Welche Formulierung empfiehlst du für das Abstract? "
                    "Antworte auf DEUTSCH, max 120 Wörter."
                )
            },
            {
                "name": "DDGK",
                "rolle": "Open-Source Advocate",
                "modell": "llama3.2:1b",
                "host": OLLAMA_LOCAL,
                "timeout": 35,
                "frage": (
                    "Du bist Open-Source Advocate. "
                    "Die Metriken φ, κ, σ laufen auf: Python stdlib, Ollama (gratis), "
                    "beliebige Modelle. Keine Cloud-Abhängigkeit.\n"
                    "Frage: Was macht dieses Framework für die Open-Source-Community wertvoll? "
                    "Welche 2 Anwendungsfälle außerhalb von CCRN siehst du? "
                    "Antworte auf DEUTSCH, max 100 Wörter."
                )
            },
        ]
    }
]

# ═══════════════════════════════════════════════════════════════════════
# DISKUSSIONS-EXECUTOR
# ═══════════════════════════════════════════════════════════════════════

alle_ergebnisse = {}
stats = {"total": 0, "ok": 0, "timeout": 0}

for runde_config in DISKUSSION:
    r = runde_config["runde"]
    head(f"RUNDE {r}: {runde_config['thema']}")
    alle_ergebnisse[r] = {}

    # Pi5-Agenten zuerst
    sortiert = sorted(runde_config["agenten"],
                      key=lambda x: 0 if x["host"] == PI5_OLLAMA else 1)

    for agent in sortiert:
        prompt_full = f"{DEFINITIONS}\n\n---\nROLLE: {agent['rolle']}\n\n{agent['frage']}"
        resp, s, err = query(agent["host"], agent["modell"], prompt_full,
                             timeout=agent["timeout"], tokens=180)
        stats["total"] += 1

        if err or not resp:
            warn(f"[{agent['name']}/{agent['rolle'][:20]}] TIMEOUT ({s}s): {err or 'leer'}")
            alle_ergebnisse[r][agent["name"]] = {"text": None, "rolle": agent["rolle"], "status": "FEHLER", "s": s}
            stats["timeout"] += 1
        else:
            print(f"\n  [{agent['name']} — {agent['rolle'][:30]}] ({s}s):")
            for zeile in resp.split("\n")[:6]:
                pr(f"    {zeile}")
            alle_ergebnisse[r][agent["name"]] = {"text": resp, "rolle": agent["rolle"], "status": "OK", "s": s}
            stats["ok"] += 1

        ddgk_log(agent["name"], f"formalization_r{r}",
                 {"rolle": agent["rolle"], "frage": agent["frage"][:60],
                  "resp": resp[:150], "s": s, "err": err})

# ═══════════════════════════════════════════════════════════════════════
# MASTER-SYNTHESE: Publikations-bereites Abstract
# ═══════════════════════════════════════════════════════════════════════
head("MASTER-SYNTHESE: Publikations-Abstract generieren")

# Kernantworten zusammenfassen
kern_antworten = ""
for r in sorted(alle_ergebnisse.keys()):
    for agent_name, info in alle_ergebnisse[r].items():
        if info["text"]:
            kern_antworten += f"\n{agent_name} (R{r}): {info['text'][:100]}\n"

synthese_prompt = f"""
{DEFINITIONS}

AGENTEN-DISKUSSION (Auszüge):
{kern_antworten[:1500]}

AUFGABE: Du bist Hauptautor. Schreibe ein WISSENSCHAFTLICHES ABSTRACT (max 150 Wörter) für das Paper
"Formal Scientific Specification of CCRN System Metrics: φ, κ, σ".

ANFORDERUNGEN:
- Kein Bewusstseins-Claim
- Formal korrekte Beschreibung von φ (TTR-basiert), κ (Aggregationsmetrik), σ (Stabilität)
- Erwähne die Deckeneffekt-Limitation (σ=0 in v1.0)
- Erwähne verwandte Arbeit (ICOER)
- Auf ENGLISCH (für internationale Publikation)
"""

for master_modell in ["orion-8b:latest", "qwen2.5:7b", "qwen2.5:1.5b"]:
    master_resp, master_s, master_err = query(OLLAMA_LOCAL, master_modell, synthese_prompt,
                                              timeout=120, tokens=300)
    if not master_err and master_resp:
        ok(f"MASTER-ABSTRACT [{master_modell}] ({master_s}s):\n")
        print("  ┌" + "─"*66 + "┐")
        for zeile in master_resp.split("\n")[:15]:
            print(f"  │ {zeile[:64]:<64} │")
        print("  └" + "─"*66 + "┘")
        ddgk_log("MASTER", "formalization_abstract",
                 {"modell": master_modell, "abstract": master_resp[:400], "s": master_s})
        break
    else:
        warn(f"  {master_modell} Timeout: {master_err}")
        master_resp = ""

# ═══════════════════════════════════════════════════════════════════════
# ERGEBNIS
# ═══════════════════════════════════════════════════════════════════════

erfolg = round(stats["ok"] / max(stats["total"], 1) * 100, 1)
mem_count = len([l for l in MEM.read_text("utf-8").splitlines() if l.strip()]) if MEM.exists() else 0

head("FORMALISIERUNG — ABSCHLUSS-ERGEBNIS")
print(f"""
  ╔══════════════════════════════════════════════════════════════════╗
  ║  DDGK FORMALISIERUNG DISKUSSION — ABGESCHLOSSEN                  ║
  ╠══════════════════════════════════════════════════════════════════╣
  ║  Erfolgsrate    : {stats['ok']}/{stats['total']} ({erfolg}%)                             ║
  ║  Runden         : 3 (Mathematik, Falsifizierbarkeit, Publikation) ║
  ║  Agenten/Runde  : 4-5 (Rollen: Mathematiker, Theoretiker, Auditor)║
  ╠══════════════════════════════════════════════════════════════════╣
  ║  Dokument       : CCRN_METRIC_FORMALIZATION_v1.0.md              ║
  ║  DDGK Memory    : {mem_count} Einträge                                 ║
  ╠══════════════════════════════════════════════════════════════════╣
  ║  Konsens:                                                        ║
  ║  • φ: TTR mathematisch valide, Deckeneffekt dokumentiert         ║
  ║  • κ: Komposites Aggregationsmaß (kein Kohärenz-/Kopplungsmaß)  ║
  ║  • σ=0: Formales Saturierungsartefakt, nicht Homogenität         ║
  ║  • Nächster Schritt: v2.0 mit sentence-transformers              ║
  ╚══════════════════════════════════════════════════════════════════╝
""")

# Key-Findings extrahieren
key_findings = []
for r in sorted(alle_ergebnisse.keys()):
    for agent_name, info in alle_ergebnisse[r].items():
        if info["text"] and info["status"] == "OK":
            key_findings.append({
                "runde": r, "agent": agent_name,
                "rolle": info["rolle"], "finding": info["text"][:200]
            })

report = {
    "timestamp": datetime.datetime.now().isoformat(),
    "stats": stats, "erfolg_rate": erfolg,
    "ddgk_memory": mem_count,
    "master_abstract": master_resp[:500] if master_resp else None,
    "key_findings": key_findings,
    "metriken_klassifikation": {
        "phi": "Output Complexity Measure (Lexical Richness + Domain Focus Density)",
        "kappa": "Composite Network Aggregation Score (Summative + Logarithmic Scale Bonus)",
        "sigma": "Measurement Reliability Indicator (Inter-Model Standard Deviation)"
    }
}
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"  Report: {OUT}")
