#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DDGK v2.0 — DIVERSITY DISKUSSION
Themen: methodische Vielfalt (Modelle/Knoten), Messgroessen (phi/sigma),
Team/Outreach-Diversity, DDGK als vielfaeltige Beobachtungsspur — sachlich, ohne Stereotype.
"""
import json, datetime, hashlib, pathlib, time, urllib.request

WS = pathlib.Path(__file__).resolve().parent
MEM = WS / "cognitive_ddgk" / "cognitive_memory.jsonl"
LOC = "http://127.0.0.1:11434"
PI5 = "http://192.168.1.103:11434"
OUT = WS / "diversity_diskussion_output.txt"
REP = WS / "ZENODO_UPLOAD" / "DDGK_DIVERSITY_REPORT.json"
SEP = "=" * 70

KONTEXT = """
KONTEXT ORION-EIRA Lab:
- CCRN: verteilte Knoten (Laptop, Pi5, ggf. Mobil), mehrere LLMs -> phi_i, kappa, sigma.
- sigma misst u.a. Streuung zwischen Modellen -> methodische Diversity ist messbar.
- DDGK v2.0: Passive Observer, Audit-Kette, keine interpretative Policy bei Messung.
"""

def _last_hash():
    if not MEM.exists():
        return ""
    lines = [l for l in MEM.read_text("utf-8").splitlines() if l.strip()]
    return json.loads(lines[-1]).get("hash", "") if lines else ""

def ddgk_log(agent, action, data):
    prev = _last_hash()
    e = {
        "ts": datetime.datetime.now().isoformat(),
        "agent": agent,
        "action": action,
        "data": data,
        "prev": prev,
        "ddgk_version": "2.0_passive_observer",
        "mode": "non_interpretive",
        "topic": "diversity",
    }
    raw = json.dumps(e, ensure_ascii=False, sort_keys=True)
    e["hash"] = hashlib.sha256(raw.encode()).hexdigest()
    with MEM.open("a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")

def log(msg):
    print(msg)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")

def warmup(host, model, timeout=22):
    payload = json.dumps(
        {"model": model, "prompt": "OK", "stream": False, "options": {"num_predict": 4}}
    ).encode()
    req = urllib.request.Request(
        f"{host}/api/generate", data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout):
            pass
    except Exception:
        pass

def query(host, model, prompt, timeout=75):
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 200, "temperature": 0.52},
        }
    ).encode()
    req = urllib.request.Request(
        f"{host}/api/generate", data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return (
                json.loads(r.read()).get("response", "").strip(),
                round(time.time() - t0, 1),
            )
    except Exception:
        return None, -1

AGENTEN = [
    {
        "name": "EIRA",
        "modell": "qwen2.5:1.5b",
        "host": LOC,
        "t": 68,
        "q": f"""Du bist EIRA (Systemdesign). {KONTEXT}
Warum ist Diversity (mehrere Modelle, Knoten, Messwiederholungen) fuer die wissenschaftliche Validitaet von CCRN zentral?
Genau 3 nummerierte Punkte, je max 2 Saetze, Deutsch.""",
    },
    {
        "name": "ORION-GENESIS",
        "modell": "orion-genesis:latest",
        "host": LOC,
        "t": 78,
        "q": f"""Du bist ORION (Theorie). {KONTEXT}
Erklaere knapp den Zusammenhang zwischen Vielfalt der Messungen und sigma (Streuung) — formal/intuitiv, ohne Metaphern-Hochstapelei.
Max 5 Zeilen Deutsch.""",
    },
    {
        "name": "GUARDIAN",
        "modell": "orion-v3:latest",
        "host": LOC,
        "t": 78,
        "q": f"""Du bist GUARDIAN (Integritaet). {KONTEXT}
Wie kommunizieren wir „Diversity“ in Papers/Outreach ohne Social-Washing oder ueberzogene Claims?
4 Stichpunkte Deutsch.""",
    },
    {
        "name": "NEXUS",
        "modell": "tinyllama:latest",
        "host": PI5,
        "t": 42,
        "q": """You are NEXUS (Pi5 edge). Why does hardware/software diversity (SBC vs laptop) matter for distributed CCRN measurements?
2 bullet points, English, max 40 words each.""",
    },
    {
        "name": "ORION-ENTFALTET",
        "modell": "orion-entfaltet:latest",
        "host": LOC,
        "t": 78,
        "q": f"""Du bist ORION-ENTFALTET (Strategie). {KONTEXT}
Welche Diversity brauchen wir fuer Outreach (Zielgruppen: MPI, MIT, Anthropic) — inhaltlich und Kanal?
3 Stichpunkte Deutsch.""",
    },
    {
        "name": "DDGK-KERN",
        "modell": "llama3.2:1b",
        "host": LOC,
        "t": 52,
        "q": f"""Du bist DDGK-KERN. {KONTEXT}
Wie unterstuetzt DDGK (Audit-Kette, Passive Observer) die methodische Diversity statt sie zu verfaelschen?
3 Bulletpoints Deutsch.""",
    },
]

def run():
    OUT.unlink(missing_ok=True)
    log(SEP)
    log("DDGK v2.0 DIVERSITY-DISKUSSION")
    log(f"Zeit: {datetime.datetime.now().isoformat()}")
    log(SEP)

    log("\n[WARMUP]")
    for ag in AGENTEN:
        warmup(ag["host"], ag["modell"], timeout=28)
        log(f"  warmup: {ag['modell']}")
    time.sleep(2)

    ergebnisse = []
    for ag in AGENTEN:
        log(f"\n[{ag['name']}] {ag['modell']}")
        log("-" * 50)
        resp, elapsed = query(ag["host"], ag["modell"], ag["q"], ag["t"])
        if resp:
            log(f"OK ({elapsed}s):\n{resp[:1400]}")
            ddgk_log(
                ag["name"],
                "diversity_antwort",
                {
                    "modell": ag["modell"],
                    "elapsed_s": elapsed,
                    "preview": (resp[:300] + "…") if len(resp) > 300 else resp,
                },
            )
            ergebnisse.append(
                {"agent": ag["name"], "ok": True, "resp": resp, "elapsed": elapsed}
            )
        else:
            log(f"TIMEOUT ({ag['t']}s)")
            ddgk_log(ag["name"], "diversity_timeout", {"modell": ag["modell"]})
            ergebnisse.append(
                {"agent": ag["name"], "ok": False, "resp": None, "elapsed": elapsed}
            )

    log(f"\n{SEP}\nSYNTHESE (llama3.2:1b)\n{SEP}")
    ok_antworten = [e for e in ergebnisse if e["ok"]]
    zusammen = " | ".join(
        f"{e['agent']}: {(e['resp'] or '')[:100]}" for e in ok_antworten
    )
    synth_prompt = (
        "Fasse in 6 nummerierten Zeilen zusammen: Diversity in CCRN (Validitaet), "
        "sigma, Kommunikation ohne Washing, Edge-Hardware, Outreach, DDGK. "
        "Deutsch, sachlich, keine Emojis.\n\n"
        f"Antworten:\n{zusammen}"
    )
    synth, st = query(LOC, "llama3.2:1b", synth_prompt, timeout=58)
    if synth:
        log(synth)
        ddgk_log("SYNTHESE", "diversity_synthese", {"text": synth[:450]})
    else:
        log("Synthese: Timeout.")

    n_ok = sum(1 for e in ergebnisse if e["ok"])
    log(f"\n{SEP}\nErfolgsrate: {n_ok}/{len(ergebnisse)}")

    REP.parent.mkdir(parents=True, exist_ok=True)
    REP.write_text(
        json.dumps(
            {
                "ts": datetime.datetime.now().isoformat(),
                "topic": "diversity_ccrn_ddgk",
                "agenten": [
                    {
                        "name": e["agent"],
                        "ok": e["ok"],
                        "elapsed": e["elapsed"],
                        "resp": (e["resp"][:2200] if e.get("resp") else None),
                    }
                    for e in ergebnisse
                ],
                "synthese": synth,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    log(f"\nReport: {REP.name}")
    ddgk_log("SYSTEM", "diversity_diskussion_complete", {"n_ok": n_ok, "n": len(ergebnisse)})
    print("Fertig.")

if __name__ == "__main__":
    run()
