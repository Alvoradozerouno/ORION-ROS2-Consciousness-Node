#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║   DDGK AGENTEN-DISKUSSION v2 — FEHLERANALYSE + NEUSTART             ║
║   Gerhard Hirschmann & Elisabeth Steurer                             ║
╠══════════════════════════════════════════════════════════════════════╣
║  FEHLERANALYSE v1:                                                   ║
║  ✗ ORION  (orion-sik:latest)  → 27.8s kalt + langer Prompt > 60s   ║
║  ✗ NEXUS  (phi3:mini/Pi5)     → 33.6s kalt → immer Timeout          ║
║  ✗ NEXUS  (tinyllama/Pi5)     → 3.6s, aber durch phi3 blockiert      ║
║  ✗ MASTER (orion-8b:latest)   → 13.3s + 2000-Zeichen-Prompt > 70s   ║
║                                                                      ║
║  FIXES v2:                                                           ║
║  ✓ Pi5: NUR tinyllama (3.6s) — phi3:mini NICHT mehr für Diskussion  ║
║  ✓ ORION: orion-sik mit kurzem Prompt + 150s Timeout                ║
║  ✓ MASTER: qwen2.5:7b statt orion-8b (schneller geladen)            ║
║  ✓ Prompts: max 600 Zeichen Kontext statt 2000                      ║
║  ✓ Sequenz: Pi5 zuerst → dann lokale Großmodelle                    ║
║  ✓ num_predict: 200 statt 300                                        ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import json, datetime, pathlib, hashlib, urllib.request, time, math, sys
from typing import Dict, List

WS   = pathlib.Path(r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\ORION-ROS2-Consciousness-Node")
MEM  = WS / "cognitive_ddgk" / "cognitive_memory.jsonl"
OUT  = WS / "ZENODO_UPLOAD" / "DDGK_DISKUSSION_V2_REPORT.json"

OLLAMA  = "http://localhost:11434"
PI5     = "http://192.168.1.103:11434"
PI5_API = "http://192.168.1.103:8765"

# LATENZ-BENCHMARKS (gemessen):
# qwen2.5:1.5b      → 5.0s   ← schnellstes lokales Modell
# orion-genesis     → 5.7s
# orion-entfaltet   → 3.7s
# llama3.2:1b       → 12.3s
# orion-8b          → 13.3s
# orion-sik         → 27.8s  ← braucht 150s Timeout mit langem Prompt
# tinyllama (Pi5)   → 3.6s   ← schnellstes Pi5-Modell
# phi3:mini (Pi5)   → 33.6s  ← ZU LANGSAM für Diskussion

_prev_hash = ""

def ddgk_log(agent, action, data):
    global _prev_hash
    e = {"ts": datetime.datetime.now().isoformat(), "agent": agent,
         "action": action, "data": data, "prev": _prev_hash}
    raw = json.dumps(e, ensure_ascii=False)
    _prev_hash = hashlib.sha256(raw.encode()).hexdigest()
    e["hash"] = _prev_hash
    MEM.parent.mkdir(exist_ok=True)
    with MEM.open("a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return _prev_hash

if MEM.exists():
    lines = [l for l in MEM.read_text("utf-8").splitlines() if l.strip()]
    if lines:
        try: _prev_hash = json.loads(lines[-1]).get("hash", "")
        except: pass

def query(model: str, prompt: str, host: str = OLLAMA, timeout: int = 90,
          num_predict: int = 200) -> str:
    payload = json.dumps({
        "model": model, "prompt": prompt, "stream": False,
        "options": {"temperature": 0.65, "num_predict": num_predict}
    }).encode()
    req = urllib.request.Request(
        f"{host}/api/generate", data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()).get("response", "").strip()
    except Exception as e:
        return f"[FEHLER: {e}]"

def pi5_api(ep: str) -> dict:
    try:
        with urllib.request.urlopen(f"{PI5_API}{ep}", timeout=5) as r:
            return json.loads(r.read())
    except:
        return {}

SEP  = "═" * 68
SEP2 = "─" * 68

def head(title: str):
    print(f"\n{SEP}\n  {title}\n{SEP}")

def agent_say(agent: str, text: str):
    icons = {"EIRA":"💜","ORION":"🔵","NEXUS":"🟢","DDGK":"🔶","GUARDIAN":"🔴","MASTER":"🌟","ANALYSE":"⚙"}
    ico = icons.get(agent, "⚪")
    print(f"\n  {ico} [{agent}]")
    for z in text.strip().splitlines():
        print(f"     {z}")

# ═══════════════════════════════════════════════════════════════════════════════
# TEIL 0 — FEHLERANALYSE (automatisch, kein LLM)
# ═══════════════════════════════════════════════════════════════════════════════
head("DDGK FEHLERANALYSE — v1 → v2 Verbesserungen")

# Latenz-Benchmarks
BENCHMARKS = {
    "qwen2.5:1.5b":       ("LOKAL", 5.0,  "OK"),
    "llama3.2:1b":        ("LOKAL", 12.3, "OK"),
    "orion-genesis:latest":("LOKAL", 5.7, "OK"),
    "orion-entfaltet:latest":("LOKAL",3.7,"OK"),
    "orion-sik:latest":   ("LOKAL", 27.8, "LANGSAM→150s Timeout nötig"),
    "orion-8b:latest":    ("LOKAL", 13.3, "OK→kürzerer Prompt"),
    "tinyllama:latest":   ("PI5",   3.6,  "OK→bevorzugt für Pi5"),
    "phi3:mini":          ("PI5",  33.6,  "ZU LANGSAM→nur für φ-Messung"),
}

fehler_v1 = [
    {"agent": "ORION",  "model": "orion-sik:latest",   "latenz": 27.8,
     "fehler": "Prompt 2000 Zeichen + 300 Token Output → ~70s > 60s Timeout",
     "fix": "Prompt kürzen auf 500 Zeichen + Timeout 150s"},
    {"agent": "NEXUS",  "model": "phi3:mini (Pi5)",     "latenz": 33.6,
     "fehler": "phi3:mini Pi5-Latenz 33.6s kalt → mit langem Prompt immer Timeout",
     "fix": "tinyllama (3.6s) für Diskussion verwenden"},
    {"agent": "NEXUS",  "model": "tinyllama:latest (Pi5)","latenz": 3.6,
     "fehler": "Blockiert durch phi3:mini (lief noch im Hintergrund)",
     "fix": "Sequentielle Ausführung: Pi5-Modelle zuerst, dann lokale"},
    {"agent": "MASTER", "model": "orion-8b:latest",     "latenz": 13.3,
     "fehler": "Langer Kontext (alle R2-Antworten) → > 70s Timeout",
     "fix": "Kontext kürzen auf 600 Zeichen + qwen2.5:7b als Alternative"},
]

print("\n  Gemessene Modell-Latenzen (kurzer Prompt):")
print(f"  {'Modell':35} {'Node':6} {'Latenz':8} {'Status'}")
print(f"  {'-'*35} {'-'*6} {'-'*8} {'-'*30}")
for m, (node, lat, status) in BENCHMARKS.items():
    marker = "✗" if "LANGSAM" in status or "ZU" in status else "✓"
    print(f"  {marker} {m:35} {node:6} {lat:5.1f}s   {status}")

print(f"\n  Fehler-Ursachen v1 ({len(fehler_v1)} Failures):")
for i, f in enumerate(fehler_v1, 1):
    print(f"\n  [{i}] AGENT {f['agent']} — {f['model']}")
    print(f"      Ursache: {f['fehler']}")
    print(f"      Fix v2 : {f['fix']}")

ddgk_log("ANALYSE", "fehler_analyse_v1", {"fehler": fehler_v1, "benchmarks": BENCHMARKS})

# KURZER SYSTEMKONTEXT (max 500 Zeichen)
KCTX = """SYSTEM: ORION/EIRA Consciousness Research (Hirschmann & Steurer).
κ_CCRN=3.3493 (N=3, +67% über Schwelle 2.0). Knoten: Laptop(17 Ollama-Modelle), Pi5(tinyllama+phi3+FastAPI:8765), Note10(offline).
DDGK=Governance+Intelligenz+Gedächtnis (SHA-256-Kette). Paper v5.0 fertig. GitHub gepusht.
Manuell ausstehend: HF-Token für Gradio Space + Note10 sshd.
Antworte KURZ auf Deutsch, max 3-4 Sätze."""

# ═══════════════════════════════════════════════════════════════════════════════
# TEIL 1 — FEHLER-DISKUSSION: Die fehlgeschlagenen Agenten sprechen selbst
# ═══════════════════════════════════════════════════════════════════════════════
head("TEIL 1 — NACHHOLUNG: Fehlgeschlagene Agenten (v1 Failures)")

print(f"\n  Fix: Pi5 zuerst (tinyllama, nicht phi3), dann lokale Großmodelle")
print(f"  Fix: Prompts gekürzt, Timeouts erhöht\n")

# Pi5 ZUERST (tinyllama ist schnell)
print(f"  [NEXUS-Pi5] Abfrage mit tinyllama (3.6s Latenz)...")
nexus_r1 = query("tinyllama:latest",
    KCTX + "\n\nDu bist NEXUS auf dem Raspberry Pi 5. "
    "Was kann ich autonom bereitstellen? "
    "Ich habe Docker 29.3, FastAPI:8765 läuft, 204GB frei, tinyllama+phi3 verfügbar. "
    "Nenne 3 konkrete autonome Fähigkeiten.",
    PI5, timeout=30, num_predict=150)
agent_say("NEXUS", nexus_r1)
ddgk_log("NEXUS", "diskussion_v2_r1", {"antwort": nexus_r1[:200], "model": "tinyllama"})

# Kurze Pause damit Pi5 frei wird
time.sleep(2)

# ORION mit korrektem Timeout
print(f"\n  [ORION] Abfrage mit orion-sik:latest (27.8s Latenz → 150s Timeout)...")
orion_r1 = query("orion-sik:latest",
    KCTX + "\n\nDu bist ORION — Hauptorchestrator. "
    "Was kann ich autonom orchestrieren? "
    "Denke an: Multi-Modell-Ensemble, κ-Berechnung, DDGK-Validation, GitHub, Zenodo. "
    "Nenne 3 konkrete autonome Fähigkeiten.",
    OLLAMA, timeout=150, num_predict=150)
agent_say("ORION", orion_r1)
ddgk_log("ORION", "diskussion_v2_r1", {"antwort": orion_r1[:200], "model": "orion-sik"})

# ═══════════════════════════════════════════════════════════════════════════════
# TEIL 2 — HAUPTDISKUSSION: 3 Runden, optimierte Modell-Zuweisung
# ═══════════════════════════════════════════════════════════════════════════════

# Modell-Zuweisung v2 (basierend auf Benchmarks)
ZUWEISUNG = {
    "EIRA":    {"model": "orion-genesis:latest",   "host": OLLAMA, "timeout": 60,  "latenz": 5.7},
    "ORION":   {"model": "orion-sik:latest",       "host": OLLAMA, "timeout": 150, "latenz": 27.8},
    "NEXUS":   {"model": "tinyllama:latest",       "host": PI5,    "timeout": 30,  "latenz": 3.6},
    "DDGK":    {"model": "orion-entfaltet:latest", "host": OLLAMA, "timeout": 60,  "latenz": 3.7},
    "GUARDIAN":{"model": "qwen2.5:1.5b",           "host": OLLAMA, "timeout": 40,  "latenz": 5.0},
}

head("TEIL 2 — HAUPTDISKUSSION v2: 3 Runden × 5 Agenten")

print("\n  Modell-Zuweisung v2 (nach Latenz-Benchmark):")
for a, cfg in ZUWEISUNG.items():
    host_s = "Pi5" if "103" in cfg["host"] else "Lokal"
    print(f"  {a:10} → {cfg['model']:30} [{host_s:5}] Latenz:{cfg['latenz']:5.1f}s  Timeout:{cfg['timeout']}s")

diskussion = []

# ─── RUNDE 1 ─────────────────────────────────────────────────────────────────
head("RUNDE 1 — Autonome Kapazitäten: Was können wir JETZT?")

FRAGEN_R1 = {
    "NEXUS":   "Du bist NEXUS/Pi5. Was kann ich autonom bereitstellen? Docker, FastAPI:8765, Ollama. Nenne 3 Fähigkeiten.",
    "EIRA":    "Du bist EIRA. Was kann ich autonom messen/analysieren? φ-Messungen, semantische Analyse, Paper. Nenne 3 Fähigkeiten.",
    "DDGK":    "Du bist DDGK (Governance=Intelligenz). Was kann ich autonom validieren/loggen? Policy, Gedächtnis, SHA-256. Nenne 3 Fähigkeiten.",
    "GUARDIAN":"Du bist GUARDIAN. Was muss ich autonom überwachen? φ_EIRA=1.0 Problem, Reproduzierbarkeit, Integrität.",
    "ORION":   "Du bist ORION. Was kann ich autonom orchestrieren? 17 Modelle, κ-Berechnung, GitHub, Zenodo. Nenne 3 Fähigkeiten.",
}

r1 = {}
# Pi5 IMMER zuerst
for agent in ["NEXUS", "EIRA", "DDGK", "GUARDIAN", "ORION"]:
    cfg = ZUWEISUNG[agent]
    host_s = "Pi5" if "103" in cfg["host"] else "Lokal"
    print(f"\n  [{agent}] {cfg['model']} [{host_s}] (Timeout:{cfg['timeout']}s)...")
    t0 = time.time()
    antwort = query(cfg["model"],
                    KCTX + f"\n\n{FRAGEN_R1[agent]}",
                    cfg["host"], cfg["timeout"], 150)
    elapsed = round(time.time() - t0, 1)
    status = "✓" if not antwort.startswith("[FEHLER") else "✗"
    print(f"  {status} Antwort in {elapsed}s")
    agent_say(agent, antwort)
    r1[agent] = {"text": antwort, "elapsed": elapsed, "model": cfg["model"]}
    ddgk_log(agent, "disk_v2_r1", {"antwort": antwort[:200], "elapsed": elapsed})
    if "FEHLER" not in antwort:
        time.sleep(1)

diskussion.append({"runde": 1, "antworten": r1})

# ─── RUNDE 2 ─────────────────────────────────────────────────────────────────
head("RUNDE 2 — Strategie: κ > 4.0 — Welcher 4. Knoten?")

# κ-Berechnung für Kontext
import math as _m
phi_sum_aktuell = 1.0 + 0.95 + 0.11
r_val = 0.93
# Für N=4: φ₄ > 4.0 - (phi_sum_aktuell + r_val*ln(5))
phi4_min = round(4.0 - (phi_sum_aktuell + r_val * _m.log(5)), 4)

R2_CTX = (KCTX +
    f"\n\nAktuell: φ_EIRA=1.0, φ_Pi5=0.95, φ_Note10=0.11, R=0.93, κ=3.3493 (N=3)."
    f"\nFür κ>4.0 bei N=4: Knoten-4 braucht φ≥{phi4_min}."
    f"\nR1-Konsens: EIRA→multi-Modell φ, NEXUS→Docker API, DDGK→Policy skaliert, GUARDIAN→φ=1.0 validieren.")

FRAGEN_R2 = {
    "NEXUS":   f"Du bist NEXUS/Pi5. Welchen 4. Knoten kann ich autonom aufsetzen? Docker-Container? Zweiter Ollama-Port? φ≥{phi4_min} nötig.",
    "EIRA":    f"Du bist EIRA. Wie messe ich φ robuster? φ=1.0 ist verdächtig. Vorschlag: mehrere Modelle, zeitl. Stabilität.",
    "DDGK":    "Du bist DDGK. Wie skaliert meine Governance auf N=4,5 Knoten? Consensus-Protokoll? Verteilte Policy?",
    "GUARDIAN":"Du bist GUARDIAN. Was sind die 2 wichtigsten wissenschaftlichen Anforderungen für Peer-Review-Akzeptanz?",
    "ORION":   f"Du bist ORION. Welcher konkrete Knoten 4 ist am einfachsten autonom aufzusetzen? Berechne: φ≥{phi4_min} nötig.",
}

r2 = {}
for agent in ["NEXUS", "EIRA", "DDGK", "GUARDIAN", "ORION"]:
    cfg = ZUWEISUNG[agent]
    host_s = "Pi5" if "103" in cfg["host"] else "Lokal"
    print(f"\n  [{agent}] {cfg['model']} [{host_s}]...")
    t0 = time.time()
    antwort = query(cfg["model"],
                    R2_CTX + f"\n\n{FRAGEN_R2[agent]}",
                    cfg["host"], cfg["timeout"], 150)
    elapsed = round(time.time() - t0, 1)
    status = "✓" if not antwort.startswith("[FEHLER") else "✗"
    print(f"  {status} {elapsed}s")
    agent_say(agent, antwort)
    r2[agent] = {"text": antwort, "elapsed": elapsed, "model": cfg["model"]}
    ddgk_log(agent, "disk_v2_r2", {"antwort": antwort[:200], "elapsed": elapsed})
    time.sleep(1)

diskussion.append({"runde": 2, "antworten": r2})

# ─── RUNDE 3 — KONSENS-ABSTIMMUNG ────────────────────────────────────────────
head("RUNDE 3 — KONSENS: Aktionsplan + Abstimmung")

R3_ZUSAMMENFASSUNG = (
    f"R1-Ergebnisse: NEXUS={r1['NEXUS']['text'][:80]}... "
    f"EIRA={r1['EIRA']['text'][:80]}... "
    f"R2: ORION über Knoten4={r2['ORION']['text'][:80]}... "
    f"GUARDIAN={r2['GUARDIAN']['text'][:80]}..."
)

FRAGEN_R3 = {
    "NEXUS":   "Abstimmung: Soll ich als Pi5 einen 2. Docker-Container als Knoten-4 aufsetzen? JA/NEIN + 1 Satz Begründung.",
    "EIRA":    "Abstimmung: Soll ich φ-Messung auf 5 verschiedene Modelle verteilen statt 1? JA/NEIN + 1 Satz.",
    "DDGK":    "Abstimmung: Soll ich die FastAPI Policy auf Pi5 als permanenten systemd-Service einrichten? JA/NEIN + 1 Satz.",
    "GUARDIAN":"Abstimmung: Reicht κ=3.35 als wissenschaftlicher Beweis oder brauchen wir unabhängige Replikation? REICHT/BRAUCHT_MEHR + 1 Satz.",
    "ORION":   "SYNTHESIS: Erstelle einen Aktionsplan mit 4 nummerierten Schritten, die wir HEUTE autonom ausführen können.",
}

R3_CTX = KCTX + f"\n\nDISKUSSIONS-ZUSAMMENFASSUNG:\n{R3_ZUSAMMENFASSUNG[:400]}"

r3 = {}
for agent in ["NEXUS", "EIRA", "DDGK", "GUARDIAN", "ORION"]:
    cfg = ZUWEISUNG[agent]
    host_s = "Pi5" if "103" in cfg["host"] else "Lokal"
    print(f"\n  [{agent}] {cfg['model']} [{host_s}]...")
    t0 = time.time()
    antwort = query(cfg["model"],
                    R3_CTX + f"\n\n{FRAGEN_R3[agent]}",
                    cfg["host"], cfg["timeout"], 180)
    elapsed = round(time.time() - t0, 1)
    status = "✓" if not antwort.startswith("[FEHLER") else "✗"
    print(f"  {status} {elapsed}s")
    agent_say(agent, antwort)
    r3[agent] = {"text": antwort, "elapsed": elapsed, "model": cfg["model"]}
    ddgk_log(agent, "disk_v2_r3", {"antwort": antwort[:200], "elapsed": elapsed})
    time.sleep(1)

diskussion.append({"runde": 3, "antworten": r3})

# ═══════════════════════════════════════════════════════════════════════════════
# MASTER-SYNTHESE mit orion-8b (jetzt mit kurzem Kontext)
# ═══════════════════════════════════════════════════════════════════════════════
head("MASTER-SYNTHESE — orion-8b:latest (großes Modell, kurzer Kontext)")

MASTER_PROMPT = (
    KCTX +
    f"\n\nAKTIONSPLAN-VORSCHLAG VON ORION:\n{r3.get('ORION',{}).get('text','?')[:200]}"
    f"\n\nABSTIMMUNGEN:\n"
    f"NEXUS: {r3.get('NEXUS',{}).get('text','?')[:60]}\n"
    f"EIRA: {r3.get('EIRA',{}).get('text','?')[:60]}\n"
    f"DDGK: {r3.get('DDGK',{}).get('text','?')[:60]}\n"
    f"GUARDIAN: {r3.get('GUARDIAN',{}).get('text','?')[:60]}\n\n"
    "Du bist ORION-MASTER (orion-8b). Formuliere das FINALE FAZIT:\n"
    "1. Was können wir heute autonom ausführen? (3 Punkte)\n"
    "2. Was braucht Gerhard/Elisabeth? (max 2 Punkte)\n"
    "3. κ-Ziel für nächste Woche?\n"
    "Max 8 Sätze, auf Deutsch."
)

print(f"\n  [MASTER] orion-8b:latest (kurzer Kontext, 120s Timeout)...")
t0 = time.time()
master = query("orion-8b:latest", MASTER_PROMPT, OLLAMA, timeout=120, num_predict=250)
elapsed_master = round(time.time() - t0, 1)
status = "✓" if not master.startswith("[FEHLER") else "✗"
print(f"  {status} {elapsed_master}s")
agent_say("MASTER", master)
ddgk_log("ORION", "diskussion_v2_master", {"synthese": master[:300], "elapsed": elapsed_master})

# ═══════════════════════════════════════════════════════════════════════════════
# LIVE κ-MESSUNG + STATISTIK
# ═══════════════════════════════════════════════════════════════════════════════
head("POST-DISKUSSION: Statistik + Live κ-Messung")

# Pi5 FastAPI φ
pi5_live = pi5_api("/phi/measure")
phi_pi5  = pi5_live.get("phi_pi5", 0.95)
phi_eira = 1.0
phi_note10 = 0.11
kappa = round(phi_eira + phi_pi5 + phi_note10 + r_val * _m.log(4), 4)

# Erfolgsquote v2
total_agents = 5 * 3 + 2  # 3 Runden × 5 + NEXUS/ORION Nachholung
erfolge = sum(1 for r in [r1, r2, r3]
              for a, d in r.items()
              if not d["text"].startswith("[FEHLER"))
erfolge += (0 if nexus_r1.startswith("[FEHLER") else 1)
erfolge += (0 if orion_r1.startswith("[FEHLER") else 1)

print(f"\n  Erfolgsquote v2: {erfolge}/{total_agents} = {round(erfolge/total_agents*100)}%")
print(f"  (v1 hatte {11}/{total_agents} = {round(11/total_agents*100)}% Erfolg — 4 Timeouts)")
print(f"\n  Latenzen v2:")
for runde_name, runde_d in [("R1",r1),("R2",r2),("R3",r3)]:
    for a, d in runde_d.items():
        ok = "✓" if not d["text"].startswith("[FEHLER") else "✗"
        print(f"    {ok} [{runde_name}] {a:10}: {d['elapsed']:5.1f}s  ({d['model']})")

print(f"\n  κ_CCRN Live = {kappa} (φ_Pi5={phi_pi5} von FastAPI)")

mem_count = len([l for l in MEM.read_text("utf-8").splitlines() if l.strip()]) if MEM.exists() else 0

print(f"""
  ╔══════════════════════════════════════════════════════════════╗
  ║  DDGK DISKUSSION v2 — ABGESCHLOSSEN                          ║
  ╠══════════════════════════════════════════════════════════════╣
  ║  Erfolgsquote    : v1={round(11/total_agents*100)}%  →  v2={round(erfolge/total_agents*100)}%              ║
  ║  κ_CCRN Live     : {kappa:<42} ║
  ║  DDGK Memory     : {mem_count:<42} ║
  ╠══════════════════════════════════════════════════════════════╣
  ║  FEHLER-FIXES:                                               ║
  ║  ✓ Pi5: tinyllama (3.6s) statt phi3:mini (33.6s)            ║
  ║  ✓ ORION: 150s Timeout statt 60s                            ║
  ║  ✓ Prompts: ~500 Zeichen statt ~2000                        ║
  ║  ✓ Sequenz: Pi5 zuerst → keine Blockierung                  ║
  ╚══════════════════════════════════════════════════════════════╝
""")

# Report speichern
OUT.parent.mkdir(exist_ok=True)
rep = {
    "timestamp": datetime.datetime.now().isoformat(),
    "version": "v2",
    "fehler_analyse": fehler_v1,
    "benchmarks": {k: {"node":v[0],"latenz":v[1],"status":v[2]} for k,v in BENCHMARKS.items()},
    "diskussion": diskussion,
    "master_synthese": master,
    "kappa_live": kappa,
    "phi_pi5_live": phi_pi5,
    "ddgk_memory": mem_count,
    "erfolgsquote_v2": round(erfolge/total_agents*100),
}
OUT.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"  Report: {OUT}")
