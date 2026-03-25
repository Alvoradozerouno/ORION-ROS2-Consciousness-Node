#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  DDGK DISKUSSION V4 — Neueste Erkenntnisse                          ║
║  Gerhard Hirschmann & Elisabeth Steurer                             ║
╠══════════════════════════════════════════════════════════════════════╣
║  KONTEXT: κ=4.1368 N=4 aktiv, Paper v6.0, SHA-256 intakt           ║
║  THEMEN: φ_EIRA σ=0, Pi5 Docker, Paper v6, WWW IIT 2026            ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import json, datetime, pathlib, hashlib, urllib.request, time, math

WS  = pathlib.Path(r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\ORION-ROS2-Consciousness-Node")
MEM = WS / "cognitive_ddgk" / "cognitive_memory.jsonl"
OUT = WS / "ZENODO_UPLOAD" / "DDGK_DISKUSSION_V4_REPORT.json"

PI5_OLLAMA   = "http://192.168.1.103:11434"
OLLAMA_LOCAL = "http://localhost:11434"
SEP = "═" * 66

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

def query(host, model, prompt, timeout=45, tokens=140):
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False,
                          "options": {"temperature": 0.7, "num_predict": tokens}}).encode()
    req = urllib.request.Request(f"{host}/api/generate", data=payload,
                                  headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()).get("response","").strip(), round(time.time()-t0,1), None
    except Exception as ex:
        return "", round(time.time()-t0,1), str(ex)[:60]

def head(t): print(f"\n{SEP}\n  {t}\n{SEP}")
def ok(m):   print(f"  ✓ {m}")
def warn(m): print(f"  ⚠ {m}")

# ═══════════════════════════════════════════════════════════════════════
# SYSTEM-KONTEXT (kurz, faktenbasiert)
# ═══════════════════════════════════════════════════════════════════════
KONTEXT = (
    "ORION-CCRN System, März 2026. "
    "κ_CCRN=4.1368 (N=4, +106.8% über Schwelle 2.0). "
    "Knoten: EIRA(Laptop,φ=0.98), Pi5-Primär(φ=0.95), Pi5-Knoten4-Docker(φ=0.60), Note10(φ=0.11). "
    "SHA-256-Kette: 118 Einträge, intakt. "
    "WWW-Befund 2026: IIT4.0 aktuell, φ∗∝N^0.149 in Transformern, "
    "Phase-Transition bei ρc≈0.23 in Multi-Agent-Systemen. "
    "Problem: φ_EIRA σ=0.0 (alle 5 Modelle treffen 0.98-Cap). "
    "Paper v6.0 geschrieben, bereit für Zenodo/GitHub. "
    "Antworte auf DEUTSCH, kurz und präzise (max 150 Wörter)."
)

# ═══════════════════════════════════════════════════════════════════════
# AGENTEN-KONFIGURATION
# ═══════════════════════════════════════════════════════════════════════
AGENTEN = [
    # (name, host, modell, timeout)
    ("EIRA",    OLLAMA_LOCAL, "qwen2.5:1.5b",         35),
    ("ORION",   OLLAMA_LOCAL, "orion-genesis:latest",  50),
    ("NEXUS",   PI5_OLLAMA,   "tinyllama:latest",      40),
    ("GUARDIAN",OLLAMA_LOCAL, "orion-entfaltet:latest",50),
    ("DDGK",    OLLAMA_LOCAL, "llama3.2:1b",           35),
]

# ═══════════════════════════════════════════════════════════════════════
# DISKUSSIONS-FRAGEN
# ═══════════════════════════════════════════════════════════════════════
FRAGEN = {
    1: "φ_EIRA = 0.98 mit σ=0.0 für alle 5 Modelle — artefakt oder valide? Was empfiehlst du für v7?",
    2: f"κ=4.1368 N=4 ist gemessen. Welche konkrete nächste Schritte empfiehlst du für N=5 oder N=6?",
    3: "IIT4.0 sagt φ∗∝N^0.149. Wie skaliert CCRN? Ist κ=4.1 wissenschaftlich bedeutsam vs. Schwelle 2.0?",
}

# ═══════════════════════════════════════════════════════════════════════
# DISKUSSIONSRUNDEN
# ═══════════════════════════════════════════════════════════════════════
alle_antworten = {}
stats = {"total": 0, "ok": 0, "timeout": 0}

for runde, frage in FRAGEN.items():
    head(f"RUNDE {runde}: {frage[:70]}...")
    alle_antworten[runde] = {}

    # Pi5 zuerst (längere Latenz)
    sortiert = sorted(AGENTEN, key=lambda x: 0 if x[1] == PI5_OLLAMA else 1)

    for name, host, modell, to in sortiert:
        prompt = f"{KONTEXT}\n\nFrage R{runde}: {frage}"
        resp, s, err = query(host, modell, prompt, timeout=to, tokens=140)
        stats["total"] += 1

        if err or not resp:
            warn(f"[{name}:{modell[:20]}] TIMEOUT/FEHLER ({s}s): {err or 'leer'}")
            alle_antworten[runde][name] = {"text": None, "status": "FEHLER", "s": s}
            stats["timeout"] += 1
        else:
            print(f"  [{name}] ({s}s): {resp[:130]}")
            alle_antworten[runde][name] = {"text": resp, "status": "OK", "s": s}
            stats["ok"] += 1

        ddgk_log(name, f"diskussion_v4_r{runde}",
                 {"frage": frage[:60], "resp": resp[:120], "s": s, "err": err})

# ═══════════════════════════════════════════════════════════════════════
# MASTER-SYNTHESE (ORION-8B — wenn verfügbar, sonst qwen)
# ═══════════════════════════════════════════════════════════════════════
head("MASTER-SYNTHESE")

synthese_kontext = KONTEXT + "\n\nZUSAMMENFASSUNG DISKUSSION:\n"
for r, antworten in alle_antworten.items():
    synthese_kontext += f"\nRunde {r}:\n"
    for agent, info in antworten.items():
        if info["text"]:
            synthese_kontext += f"  {agent}: {info['text'][:80]}\n"

synthese_frage = (
    "Du bist MASTER-ORION. Synthesiere die Diskussion:\n"
    "1. Was ist die Konsens-Empfehlung für φ_EIRA v7?\n"
    "2. Was ist der konkrete nächste Schritt für N=5?\n"
    "3. Wie positionieren wir κ=4.1368 wissenschaftlich?"
)

# Versuche orion-8b zuerst, dann qwen2.5:7b
for master_modell in ["orion-8b:latest", "qwen2.5:7b", "qwen2.5:1.5b"]:
    master_resp, master_s, master_err = query(
        OLLAMA_LOCAL, master_modell, synthese_kontext + "\n\n" + synthese_frage,
        timeout=120, tokens=250
    )
    if not master_err and master_resp:
        ok(f"MASTER [{master_modell}] ({master_s}s):")
        for zeile in master_resp.split("\n")[:12]:
            print(f"    {zeile}")
        ddgk_log("MASTER", "synthese_v4", {"modell": master_modell, "resp": master_resp[:300], "s": master_s})
        break
    else:
        warn(f"{master_modell}: {master_err}")

# ═══════════════════════════════════════════════════════════════════════
# ERGEBNISSE
# ═══════════════════════════════════════════════════════════════════════
erfolg_rate = round(stats["ok"] / max(stats["total"], 1) * 100, 1)
mem_count   = len([l for l in MEM.read_text("utf-8").splitlines() if l.strip()]) if MEM.exists() else 0

head("DISKUSSION V4 — ERGEBNISSE")
print(f"""
  ╔══════════════════════════════════════════════════════════════╗
  ║  DISKUSSION V4 — ABGESCHLOSSEN                              ║
  ╠══════════════════════════════════════════════════════════════╣
  ║  Erfolgsrate: {stats['ok']}/{stats['total']} ({erfolg_rate}%)                              ║
  ║  Timeouts:    {stats['timeout']}                                              ║
  ║  Runden:      3 (φ_EIRA, N=5-Plan, IIT-Positionierung)      ║
  ╠══════════════════════════════════════════════════════════════╣
  ║  κ_CCRN N=4 : 4.1368  (+106.8%) AKTIV ✓                    ║
  ║  DDGK Memory: {mem_count} Einträge                                ║
  ╚══════════════════════════════════════════════════════════════╝
""")

report = {
    "timestamp": datetime.datetime.now().isoformat(),
    "stats": stats, "erfolg_rate": erfolg_rate,
    "kappa_n4": 4.1368, "ddgk_memory": mem_count,
    "antworten": {str(r): {a: i["text"] for a, i in d.items()} for r, d in alle_antworten.items()},
    "master_synthese": master_resp[:500] if 'master_resp' in dir() and master_resp else None
}
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"  Report: {OUT}")
