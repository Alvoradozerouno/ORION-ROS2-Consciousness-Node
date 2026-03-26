#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DDGK v2.0 — Fortschritt: naechstes Experiment + LLM-Rauschen
Agenten: EIRA, ORION (Genesis), NEXUS, DDGK-EXPLORER (mit WWW+Workspace-Kontext)
"""
import json, datetime, hashlib, pathlib, time, urllib.request

WS = pathlib.Path(__file__).resolve().parent
MEM = WS / "cognitive_ddgk" / "cognitive_memory.jsonl"
LOC = "http://127.0.0.1:11434"
PI5 = "http://192.168.1.103:11434"
OUT = WS / "fortschritt_runden_output.txt"
REP = WS / "ZENODO_UPLOAD" / "DDGK_FORTSCHRITT_REPORT.json"
SNAP = WS / "ZENODO_UPLOAD" / "WWW_RESEARCH_SNAPSHOT.json"
LIVE = WS / "ZENODO_UPLOAD" / "WWW_RESEARCH_LIVE.json"
SCAN = WS / "ZENODO_UPLOAD" / "WORKSPACE_SCAN_DDGK.json"
OVI_REP = WS / "ZENODO_UPLOAD" / "OVI_WINDOWS_REPORT.json"
SEP = "=" * 72

def _last_hash():
    if not MEM.exists():
        return ""
    ls = [l for l in MEM.read_text("utf-8").splitlines() if l.strip()]
    return json.loads(ls[-1]).get("hash", "") if ls else ""

def ddgk_log(agent, action, data):
    prev = _last_hash()
    e = {
        "ts": datetime.datetime.now().isoformat(),
        "agent": agent,
        "action": action,
        "data": data,
        "prev": prev,
        "ddgk_version": "2.0_passive_observer",
        "topic": "fortschritt_llm_rauschen",
    }
    raw = json.dumps(e, ensure_ascii=False, sort_keys=True)
    e["hash"] = hashlib.sha256(raw.encode()).hexdigest()
    with MEM.open("a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")

def log(msg):
    print(msg)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")

def load_context() -> str:
    parts = []
    if SNAP.exists():
        parts.append("WWW_SNAPSHOT:\n" + SNAP.read_text("utf-8")[:3500])
    if LIVE.exists():
        parts.append("WWW_LIVE:\n" + LIVE.read_text("utf-8")[:4500])
    if SCAN.exists():
        parts.append("WORKSPACE_SCAN:\n" + SCAN.read_text("utf-8")[:2500])
    if OVI_REP.exists():
        parts.append("OVI:\n" + OVI_REP.read_text("utf-8")[:2000])
    return "\n\n".join(parts) if parts else "(kein Kontext)"

def warmup(host, model, timeout=22):
    pl = json.dumps({"model": model, "prompt": "OK", "stream": False, "options": {"num_predict": 3}}).encode()
    req = urllib.request.Request(f"{host}/api/generate", data=pl, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout):
            pass
    except Exception:
        pass

def query(host, model, prompt, timeout=85):
    pl = json.dumps(
        {"model": model, "prompt": prompt, "stream": False, "options": {"num_predict": 240, "temperature": 0.5}}
    ).encode()
    req = urllib.request.Request(f"{host}/api/generate", data=pl, headers={"Content-Type": "application/json"})
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()).get("response", "").strip(), round(time.time() - t0, 1)
    except Exception:
        return None, -1

def run_round(name, agenten):
    log(f"\n{SEP}\n{name}\n{SEP}")
    ctx = load_context()
    for ag in agenten:
        log(f"\n[{ag['name']}] {ag['modell']}")
        log("-" * 52)
        prompt = ag["template"].replace("{{CTX}}", ctx[:12000])
        resp, elapsed = query(ag["host"], ag["modell"], prompt, ag["t"])
        if resp:
            log(f"OK ({elapsed}s):\n{resp[:1800]}")
            ddgk_log(ag["name"], f"fortschritt_{name[:12]}", {"preview": resp[:220], "elapsed": elapsed})
        else:
            log(f"TIMEOUT ({ag['t']}s)")
            ddgk_log(ag["name"], "timeout", {"round": name})

def main():
    OUT.unlink(missing_ok=True)
    log(SEP)
    log("DDGK FORTSCHRITT — RUNDE 1 + 2")
    log(f"Zeit: {datetime.datetime.now().isoformat()}")
    log(SEP)

    for ag in [
        {"name": "warm", "modell": "qwen2.5:1.5b", "host": LOC},
        {"name": "warm", "modell": "orion-genesis:latest", "host": LOC},
        {"name": "warm", "modell": "orion-v3:latest", "host": LOC},
        {"name": "warm", "modell": "tinyllama:latest", "host": PI5},
    ]:
        warmup(ag["host"], ag["modell"], 25)
    time.sleep(1)

    # RUNDE 1 — naechstes Experiment
    run_round("R1_naechstes_Experiment", [
        {
            "name": "EIRA",
            "modell": "qwen2.5:1.5b",
            "host": LOC,
            "t": 72,
            "template": """Du bist EIRA (Systemdesign ORION-CCRN).
KONTEXT (Auszug Workspace/WWW/OVI):
{{CTX}}

Frage: Welches EINE Experiment bringt den groessten wissenschaftlichen Fortschritt fuer die naechsten 4 Wochen?
Antworte strukturiert: (A) Name (B) Messgroessen phi/kappa/sigma/OVI (C) Warum jetzt (D) Risiko — Deutsch, max 12 Zeilen.""",
        },
        {
            "name": "ORION",
            "modell": "orion-genesis:latest",
            "host": LOC,
            "t": 88,
            "template": """Du bist ORION (Theorie).
KONTEXT:
{{CTX}}

Priorisiere: E_BELL verteilt, E_KRIT N>4, oder OVI-Zeitreihe vs kappa — was ist fuer externe Replikation am ueberzeugendsten?
4 Stichpunkte Deutsch.""",
        },
        {
            "name": "NEXUS",
            "modell": "tinyllama:latest",
            "host": PI5,
            "t": 48,
            "template": """You are NEXUS (Pi5 edge node). Context:
{{CTX}}

What single on-edge measurement should we add next (latency, token throughput, audit rate)? English, 6 lines max.""",
        },
        {
            "name": "DDGK-EXPLORER",
            "modell": "orion-v3:latest",
            "host": LOC,
            "t": 88,
            "template": """Du bist DDGK-EXPLORER: verbinde WWW-Snippets mit unserem Audit-Ansatz.
KONTEXT (WWW + Scan + OVI):
{{CTX}}

Aufgabe: Nenne 3 konkrete Literatur-/Methoden-Anknuipfungen (Entropy/Calibration/On-Device) und wie DDGK sie nicht verfaelscht.
Deutsch, sachlich.""",
        },
    ])

    # RUNDE 2 — LLM Rauschen
    run_round("R2_LLM_Rauschen", [
        {
            "name": "EIRA",
            "modell": "qwen2.5:1.5b",
            "host": LOC,
            "t": 72,
            "template": """Du bist EIRA.
KONTEXT:
{{CTX}}

Thema: „LLM-Rauschen“ — Stochastic Decoding, Temperatur, inter-modell sigma.
Wie trennen wir messbar „Rauschen“ von echter kognitiver Integration (CCRN) ohne Bewusstseins-Claims?
5 Bulletpoints Deutsch.""",
        },
        {
            "name": "ORION",
            "modell": "orion-genesis:latest",
            "host": LOC,
            "t": 88,
            "template": """Du bist ORION.
KONTEXT:
{{CTX}}

Skizziere ein Mini-Protokoll: gleiche Prompts, M=5 Seeds oder Temperaturen, phi_i je Lauf, sigma ueber Laeufe — wie werten wir aus?
Max 10 Zeilen Deutsch.""",
        },
        {
            "name": "NEXUS",
            "modell": "tinyllama:latest",
            "host": PI5,
            "t": 48,
            "template": """NEXUS: Does fixed hardware (Pi5) reduce or hide LLM noise in kappa measurements? English, short paragraph.""",
        },
    ])

    report = {
        "ts": datetime.datetime.now().isoformat(),
        "context_files": [str(SNAP), str(LIVE), str(SCAN), str(OVI_REP)],
        "output_log": str(OUT),
    }
    REP.parent.mkdir(parents=True, exist_ok=True)
    REP.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    ddgk_log("SYSTEM", "fortschritt_runden_done", {"report": str(REP)})
    log(f"\n{SEP}\nReport-Meta: {REP.name}\nFertig.")
    print("OK")

if __name__ == "__main__":
    main()
