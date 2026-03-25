#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DDGK v2.0 — NEUSTART RUNDE 2 (kurze Prompts, Warmstart)
Fokus: Naechste Schritte nach HF Space Upload + Token Fix
"""
import json, datetime, hashlib, pathlib, time, urllib.request

WS  = pathlib.Path(r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\ORION-ROS2-Consciousness-Node")
MEM = WS / "cognitive_ddgk" / "cognitive_memory.jsonl"
LOC = "http://localhost:11434"
PI5 = "http://192.168.1.103:11434"
OUT = WS / "neustart_runde2_output.txt"
SEP = "=" * 70

def _last_hash():
    if not MEM.exists(): return ""
    lines = [l for l in MEM.read_text("utf-8").splitlines() if l.strip()]
    return json.loads(lines[-1]).get("hash", "") if lines else ""

def ddgk_log(agent, action, data):
    prev = _last_hash()
    e = {"ts": datetime.datetime.now().isoformat(), "agent": agent,
         "action": action, "data": data, "prev": prev, "ddgk_version": "2.0_passive_observer"}
    raw = json.dumps(e, ensure_ascii=False, sort_keys=True)
    e["hash"] = hashlib.sha256(raw.encode()).hexdigest()
    with MEM.open("a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")

def log(msg):
    print(msg)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")

def warmup(host, model, timeout=20):
    """Modell aufwaermen"""
    payload = json.dumps({"model": model, "prompt": "Hi", "stream": False,
                          "options": {"num_predict": 5}}).encode()
    req = urllib.request.Request(f"{host}/api/generate", data=payload,
                                  headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout): pass
    except: pass

def query(host, model, prompt, timeout=60):
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False,
                          "options": {"num_predict": 150, "temperature": 0.6}}).encode()
    req = urllib.request.Request(f"{host}/api/generate", data=payload,
                                  headers={"Content-Type": "application/json"})
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()).get("response","").strip(), round(time.time()-t0,1)
    except Exception as ex:
        return None, -1

AGENTEN = [
    {"name": "EIRA",          "modell": "qwen2.5:1.5b",       "host": LOC, "t": 60,
     "q": "CCRN System: kappa=3.35, HF Space live, 17 Modelle. Nenne 3 Schritte fuer heute (je 1 Satz)."},
    {"name": "ORION-GENESIS", "modell": "orion-genesis:latest","host": LOC, "t": 70,
     "q": "CCRN HF Space ist live. Welche 2 Metriken sollen als Grafik ergaenzt werden? Kurz."},
    {"name": "GUARDIAN",      "modell": "orion-v3:latest",     "host": LOC, "t": 70,
     "q": "CCRN vor arXiv: Nenne 2 kritische Luecken die noch validiert werden muessen."},
    {"name": "NEXUS",         "modell": "tinyllama:latest",    "host": PI5, "t": 40,
     "q": "Pi5 CCRN node: kappa=3.35 active. What 2 experiments can Pi5 run independently?"},
    {"name": "ORION-ENTFALTET","modell":"orion-entfaltet:latest","host": LOC,"t": 70,
     "q": "CCRN Lab vs Anthropic: Was ist UNSER einzigartiger Vorteil? 2 Saetze max."},
]

def run():
    log(SEP)
    log("DDGK v2.0 NEUSTART RUNDE 2 — KURZE PROMPTS")
    log(f"Zeit: {datetime.datetime.now().isoformat()}")
    log(SEP)

    # Alle Modelle aufwaermen
    log("\n[WARMUP] Modelle starten...")
    for ag in AGENTEN:
        warmup(ag["host"], ag["modell"], timeout=25)
        log(f"  Warmup: {ag['modell']}")
    log("Warmup fertig. Warte 3s...")
    time.sleep(3)

    ergebnisse = []
    for ag in AGENTEN:
        log(f"\n[{ag['name']}] {ag['modell']}")
        log("-" * 40)
        resp, elapsed = query(ag["host"], ag["modell"], ag["q"], ag["t"])
        if resp:
            log(f"OK ({elapsed}s): {resp[:300]}")
            ddgk_log(ag["name"], "runde2_antwort",
                     {"q": ag["q"][:60], "resp": resp[:200], "elapsed": elapsed})
            ergebnisse.append({"agent": ag["name"], "ok": True, "resp": resp, "elapsed": elapsed})
        else:
            log(f"TIMEOUT ({ag['t']}s)")
            ddgk_log(ag["name"], "runde2_timeout", {"model": ag["modell"]})
            ergebnisse.append({"agent": ag["name"], "ok": False, "resp": None, "elapsed": elapsed})

    # Synthese mit llama3.2:1b (schnell)
    log(f"\n{SEP}")
    log("SYNTHESE — llama3.2:1b (schnell)")
    log(SEP)
    erfolge = [e for e in ergebnisse if e["ok"]]
    auszug = " | ".join([f"{e['agent']}: {(e['resp'] or '')[:80]}" for e in erfolge])
    synth_q = f"Summarize in 3 action points: {auszug}"
    synth_resp, synth_t = query(LOC, "llama3.2:1b", synth_q, timeout=50)
    if synth_resp:
        log(f"SYNTHESE ({synth_t}s): {synth_resp}")
        ddgk_log("SYNTHESE-llama3.2", "runde2_synthese",
                 {"erfolge": len(erfolge), "synthese": synth_resp[:200]})
    else:
        log("Synthese Timeout — manuelle Zusammenfassung:")
        log("(1) SOFORT: HF Space testen, E_BELL Experiment starten")
        log("(2) HEUTE: arXiv Abstract einreichen")
        log("(3) WOCHE: Anthropic Welfare Kontakt aufnehmen")

    # Bericht
    n_ok = len(erfolge)
    n_total = len(ergebnisse)
    log(f"\n{SEP}")
    log(f"Ergebnis: {n_ok}/{n_total} OK ({round(n_ok/n_total*100)}%)")
    for e in ergebnisse:
        st = "OK" if e["ok"] else "TIMEOUT"
        log(f"  {st} [{e['agent']}] {e['elapsed']}s")

    # Memory zaehlen
    mem_count = len([l for l in MEM.read_text("utf-8").splitlines() if l.strip()])
    log(f"\nDDGK Memory: {mem_count} Eintraege")
    log("DDGK v2.0 — Runde 2 abgeschlossen.")

    ddgk_log("SYSTEM", "runde2_complete",
             {"ok": n_ok, "total": n_total, "mem": mem_count})

if __name__ == "__main__":
    OUT.unlink(missing_ok=True)
    run()
