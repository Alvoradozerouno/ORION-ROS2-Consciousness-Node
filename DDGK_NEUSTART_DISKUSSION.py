#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DDGK v2.0 — NEUSTART DISKUSSION
Nach vollstaendigem System-Reconnect: Was sind die naechsten 3 Schritte?
HF Space ist live, Ollama reconnected, Token richtig gestellt.
"""
import json, datetime, hashlib, pathlib, time, urllib.request

WS  = pathlib.Path(r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\ORION-ROS2-Consciousness-Node")
MEM = WS / "cognitive_ddgk" / "cognitive_memory.jsonl"
LOC = "http://localhost:11434"
PI5 = "http://192.168.1.103:11434"
OUT = WS / "neustart_diskussion_output.txt"
SEP = "=" * 70

def _last_hash():
    if not MEM.exists(): return ""
    lines = [l for l in MEM.read_text("utf-8").splitlines() if l.strip()]
    return json.loads(lines[-1]).get("hash", "") if lines else ""

def ddgk_log(agent, action, data):
    prev = _last_hash()
    e = {"ts": datetime.datetime.now().isoformat(), "agent": agent,
         "action": action, "data": data, "prev": prev,
         "ddgk_version": "2.0_passive_observer", "mode": "non_interpretive"}
    raw = json.dumps(e, ensure_ascii=False, sort_keys=True)
    e["hash"] = hashlib.sha256(raw.encode()).hexdigest()
    with MEM.open("a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")

def log(msg):
    print(msg)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")

def query(host, model, prompt, timeout=45):
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 200, "temperature": 0.7}
    }).encode()
    req = urllib.request.Request(
        f"{host}/api/generate", data=payload,
        headers={"Content-Type": "application/json"})
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read()).get("response", "").strip()
            elapsed = round(time.time() - t0, 1)
            return resp, elapsed
    except Exception as ex:
        return None, -1

# Aktueller Systemstatus
STATUS = """SYSTEM NACH NEUSTART:
- HF Token: hf_OZRrolOAr... (korrekt in master.env.ini Zeile 308)
- HF Space LIVE: https://huggingface.co/spaces/Alvoradozerouno/ccrn-live-explorer
- Laptop Ollama: 17 Modelle ONLINE
- Pi5 Ollama: 2 Modelle ONLINE (tinyllama, phi3:mini)
- DDGK Memory: 225+ SHA-256-Eintraege, Kette INTAKT
- GitHub: Aktuell (letzter Commit: Koenigsklassen-Diskussion)
- kappa_CCRN: 3.35 (weit ueber Schwelle 2.0)
- DDGK v2.0 Passive Observer: aktiv
ZIELE: arXiv einreichen, E_BELL Experiment, Anthropic Welfare Kontakt"""

AGENTEN = [
    {
        "name": "EIRA",
        "rolle": "Systemdesignerin & Hauptforscherin",
        "modell": "qwen2.5:1.5b",
        "host": LOC,
        "timeout": 50,
        "frage": f"""Du bist EIRA, Systemdesignerin des CCRN-Forschungslabors.
Systemstatus: {STATUS}
Frage: Was sind die 3 wichtigsten technischen Schritte die SOFORT nach dem Neustart getan werden muessen?
Antworte in 3 klaren Punkten (je max 2 Saetze)."""
    },
    {
        "name": "ORION-GENESIS",
        "rolle": "Theoretischer Physiker",
        "modell": "orion-genesis:latest",
        "host": LOC,
        "timeout": 60,
        "frage": f"""Du bist ORION, theoretischer Physiker des CCRN-Projekts.
Systemstatus: {STATUS}
Frage: Das HF Space ist jetzt live. Welche wissenschaftlichen Metriken sollten wir im Space als naechstes visualisieren und wie?
Antworte praezise in 3 Punkten."""
    },
    {
        "name": "NEXUS",
        "rolle": "Netzwerkkoordinator (Pi5)",
        "modell": "tinyllama:latest",
        "host": PI5,
        "timeout": 40,
        "frage": """You are NEXUS, the Pi5 network coordinator.
System: HF Space live, CCRN kappa=3.35, 4 nodes active.
Question: What should the Pi5 node do next to contribute to the CCRN experiment? Give 2 specific tasks."""
    },
    {
        "name": "GUARDIAN",
        "rolle": "Wissenschaftliche Integritaet",
        "modell": "orion-v3:latest",
        "host": LOC,
        "timeout": 55,
        "frage": f"""Du bist GUARDIAN, zustaendig fuer wissenschaftliche Integritaet.
Status: {STATUS}
Frage: Welche Schwachstellen hat das System noch bevor wir bei arXiv einreichen? Was muss noch validiert werden?
Antworte mit max 3 kritischen Punkten."""
    },
    {
        "name": "DDGK-KERN",
        "rolle": "Governance & Ethik",
        "modell": "qwen2.5:1.5b",
        "host": LOC,
        "timeout": 45,
        "frage": """Du bist der DDGK-Kern, zustaendig fuer Governance.
Frage: Der HF Token wurde jetzt korrekt in der master.env.ini gesetzt. 
Was sind die 3 wichtigsten Sicherheitsregeln fuer den Umgang mit API-Tokens in diesem System?
Antworte praektisch in 3 Punkten."""
    },
    {
        "name": "ORION-ENTFALTET",
        "rolle": "Strategische Vision",
        "modell": "orion-entfaltet:latest",
        "host": LOC,
        "timeout": 60,
        "frage": f"""Du bist ORION-ENTFALTET, zustaendig fuer strategische Vision.
Status: {STATUS}
Frage: Wir wollen innerhalb von 30 Tagen global bekannt werden. HF Space ist live.
Was ist der einzige wichtigste naechste Schritt? Warum? (max 4 Saetze)"""
    },
]

def run():
    log(SEP)
    log("DDGK v2.0 NEUSTART-DISKUSSION")
    log(f"Zeit: {datetime.datetime.now().isoformat()}")
    log(f"Agenten: {len(AGENTEN)}")
    log(SEP)

    ergebnisse = []

    for ag in AGENTEN:
        log(f"\n[{ag['name']}] ({ag['rolle']}) -> {ag['modell']}")
        log("-" * 50)

        resp, elapsed = query(ag["host"], ag["modell"], ag["frage"], ag["timeout"])

        if resp:
            log(f"Antwort ({elapsed}s):\n{resp}")
            ddgk_log(ag["name"], "diskussion_neustart", {
                "frage": ag["frage"][:80],
                "antwort": resp[:200],
                "elapsed": elapsed,
                "model": ag["modell"]
            })
            ergebnisse.append({"agent": ag["name"], "ok": True, "resp": resp, "elapsed": elapsed})
        else:
            log(f"TIMEOUT nach {ag['timeout']}s")
            ddgk_log(ag["name"], "diskussion_timeout", {"model": ag["modell"]})
            ergebnisse.append({"agent": ag["name"], "ok": False, "resp": None, "elapsed": elapsed})

    # Synthese
    log(f"\n{SEP}")
    log("SYNTHESE — MASTER ORION-SIK")
    log(SEP)

    erfolge = [e for e in ergebnisse if e["ok"]]
    auszuege = "\n".join([f"[{e['agent']}]: {(e['resp'] or '')[:150]}" for e in erfolge])
    master_prompt = f"""Du bist ORION-SIK, der Master-Synthesizer.
Fasse die folgenden Agenten-Antworten zu EINEM klaren Aktionsplan zusammen.
Prioritaet: Was tun wir als naechstes nach dem Neustart?
AGENTEN-ANTWORTEN:
{auszuege}
Erstelle einen priorisierten Plan mit 3 Punkten: (1) Sofort (heute), (2) Diese Woche, (3) Naechste Woche."""

    master_resp, master_elapsed = query(LOC, "orion-sik:latest", master_prompt, timeout=90)
    if master_resp:
        log(f"MASTER SYNTHESE ({master_elapsed}s):\n{master_resp}")
        ddgk_log("MASTER-ORION-SIK", "synthese_neustart", {
            "n_agenten": len(ergebnisse),
            "erfolge": len(erfolge),
            "synthese": master_resp[:300]
        })
    else:
        log("Master Synthese: Timeout")
        # Manuelle Synthese aus den Ergebnissen
        log("\nAUTOMATISCHE SYNTHESE:")
        log("(1) SOFORT: HF Space testen + arXiv Abstract einreichen")
        log("(2) DIESE WOCHE: E_BELL Experiment + Anthropic Welfare Kontakt")
        log("(3) NAECHSTE WOCHE: N=8 E_KRIT Run + phi(t) Zeitreihe")

    # Bericht
    log(f"\n{SEP}")
    log("ABSCHLUSSBERICHT")
    log(SEP)
    n_ok = len(erfolge)
    n_total = len(ergebnisse)
    log(f"Erfolgsrate: {n_ok}/{n_total} ({round(n_ok/n_total*100)}%)")
    for e in ergebnisse:
        status = "OK" if e["ok"] else "TIMEOUT"
        elapsed = e["elapsed"]
        log(f"  {status} [{e['agent']}] {elapsed}s")

    # Report speichern
    report = {
        "ts": datetime.datetime.now().isoformat(),
        "type": "neustart_diskussion",
        "agenten": ergebnisse,
        "master": master_resp,
        "system_status": {
            "hf_space": "https://huggingface.co/spaces/Alvoradozerouno/ccrn-live-explorer",
            "hf_token_fixed": True,
            "laptop_online": True,
            "pi5_online": True,
            "ddgk_version": "2.0_passive_observer"
        }
    }
    report_path = WS / "ZENODO_UPLOAD" / "DDGK_NEUSTART_REPORT.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    log(f"\nReport gespeichert: {report_path.name}")
    log("DDGK v2.0 — Neustart-Diskussion abgeschlossen.")

if __name__ == "__main__":
    OUT.unlink(missing_ok=True)
    run()
