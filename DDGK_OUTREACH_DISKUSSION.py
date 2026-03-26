#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DDGK v2.0 — OUTREACH DISKUSSION (MIT / MPI Berlin / Anthropic)
Öffentlicher Kontext eingebettet; Spekulation klar als Hypothese markieren.
"""
import json, datetime, hashlib, pathlib, time, urllib.request

WS = pathlib.Path(__file__).resolve().parent
MEM = WS / "cognitive_ddgk" / "cognitive_memory.jsonl"
LOC = "http://127.0.0.1:11434"
PI5 = "http://192.168.1.103:11434"
OUT = WS / "outreach_diskussion_output.txt"
REP = WS / "ZENODO_UPLOAD" / "DDGK_OUTREACH_REPORT.json"
SEP = "=" * 70

# Öffentlich recherchierbar (Stand 2025): Kurzfassung für Prompts — keine Geheimnisse
PUBLIC_KONTEXT = """
ÖFFENTLICHER KONTEXT (nur Fakten aus Web/Anthropic-Seiten):
- MIT CSAIL: Cognitive AI Community (symbolisch+probabilistisch), Kooperationen z.B. TRAC mit Microsoft, Generative AI Impact Consortium; typisch: strukturierte Forschungsanfragen, Alliances/Consortiums.
- MPI Berlin (MPIB / Dahlem Campus of Cognition): Human Development, Adaptive Rationality, interdisziplinär Psychologie/Neuro/CS; Max Planck School of Cognition.
- Anthropic: öffentlich „Model Welfare“-Forschungslinie (exploring-model-welfare), External Researcher Access (API-Credits, Form), Fellows Program (Alignment-Forschung); interne Details nicht öffentlich.
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
            "options": {"num_predict": 180, "temperature": 0.55},
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
        "t": 65,
        "q": f"""Du bist EIRA (Systemdesign). {PUBLIC_KONTEXT}
Unser Lab: CCRN-Metriken (phi, kappa, sigma), DDGK-Audit-Kette, verteilte Knoten, HF Space.
Frage: Bei wem melden wir uns ZUERST sinnvoll — MIT CSAIL, MPI Berlin, oder Anthropic — und warum genau EIN Satz pro Option (3 Saetze gesamt)?""",
    },
    {
        "name": "ORION-GENESIS",
        "modell": "orion-genesis:latest",
        "host": LOC,
        "t": 80,
        "q": f"""Du bist ORION (Theorie). {PUBLIC_KONTEXT}
Wo wuerden wir thematisch „hineinfallen“: eher Cognitive Science / Decision Science / AI Safety / Alignment?
Nenne fuer jede Institution EINE passende Schublade (je 1 kurze Zeile).""",
    },
    {
        "name": "GUARDIAN",
        "modell": "orion-v3:latest",
        "host": LOC,
        "t": 80,
        "q": f"""Du bist GUARDIAN (Integritaet). {PUBLIC_KONTEXT}
Was ist NICHT oeffentlich ueber Anthropic-intern — und was du nur als Hypothese nennen darfst?
Trenne klar: (A) oeffentlich bekannt (B) Spekulation mit Disclaimer.
Max 5 Zeilen.""",
    },
    {
        "name": "NEXUS",
        "modell": "tinyllama:latest",
        "host": PI5,
        "t": 45,
        "q": """You are NEXUS (edge node). Our CCRN has distributed kappa metrics and audit logs.
In ONE short paragraph: what 2 concrete deliverables (experiment or dataset) would make MIT or MPI take us seriously? English.""",
    },
    {
        "name": "ORION-ENTFALTET",
        "modell": "orion-entfaltet:latest",
        "host": LOC,
        "t": 80,
        "q": f"""Du bist ORION-ENTFALTET (Strategie). {PUBLIC_KONTEXT}
Liste: Was fehlt uns noch fuer glaubwuerdigen Kontakt — Papers, Preprints, reproduzierbare Experimente, Ethik-Statement?
Genau 4 Stichpunkte, je max 1 Satz.""",
    },
    {
        "name": "DDGK-KERN",
        "modell": "llama3.2:1b",
        "host": LOC,
        "t": 50,
        "q": f"""Du bist DDGK-KERN (Governance). {PUBLIC_KONTEXT}
Wie formulieren wir Outreach so, dass DDGK (Audit, keine Bewusstseins-Claims) die Staerke ist?
3 Bulletpoints Deutsch.""",
    },
]

def run():
    OUT.unlink(missing_ok=True)
    log(SEP)
    log("DDGK v2.0 OUTREACH-DISKUSSION — MIT / MPI Berlin / Anthropic")
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
            log(f"OK ({elapsed}s):\n{resp[:1200]}")
            ddgk_log(
                ag["name"],
                "outreach_antwort",
                {
                    "modell": ag["modell"],
                    "elapsed_s": elapsed,
                    "preview": (resp[:280] + "…") if len(resp) > 280 else resp,
                },
            )
            ergebnisse.append(
                {"agent": ag["name"], "ok": True, "resp": resp, "elapsed": elapsed}
            )
        else:
            log(f"TIMEOUT ({ag['t']}s)")
            ddgk_log(ag["name"], "outreach_timeout", {"modell": ag["modell"]})
            ergebnisse.append(
                {"agent": ag["name"], "ok": False, "resp": None, "elapsed": elapsed}
            )

    log(f"\n{SEP}\nSYNTHESE (llama3.2:1b)\n{SEP}")
    ok_antworten = [e for e in ergebnisse if e["ok"]]
    zusammen = " | ".join(
        f"{e['agent']}: {(e['resp'] or '')[:120]}" for e in ok_antworten
    )
    synth_prompt = (
        "Fasse in 5 nummerierten Zeilen zusammen: (1) Reihenfolge Outreach MIT/MPI/Anthropic "
        "(2) thematische Einordnung (3) was oeffentlich vs Spekulation bei Anthropic "
        "(4) fehlende Deliverables (5) DDGK-Botschaft. Deutsch, sachlich.\n\n"
        f"Agentenantworten:\n{zusammen}"
    )
    synth, st = query(LOC, "llama3.2:1b", synth_prompt, timeout=55)
    if synth:
        log(synth)
        ddgk_log("SYNTHESE", "outreach_synthese", {"text": synth[:400]})
    else:
        log("Synthese: Timeout — siehe Einzelantworten oben.")

    n_ok = sum(1 for e in ergebnisse if e["ok"])
    log(f"\n{SEP}\nErfolgsrate: {n_ok}/{len(ergebnisse)}")
    mem_lines = len([l for l in MEM.read_text("utf-8").splitlines() if l.strip()])
    log(f"DDGK Memory Eintraege (geschaetzt): {mem_lines}")

    REP.parent.mkdir(parents=True, exist_ok=True)
    REP.write_text(
        json.dumps(
            {
                "ts": datetime.datetime.now().isoformat(),
                "topic": "outreach_mit_mpi_anthropic",
                "public_context_note": "Prompts enthielten nur oeffentlich typische Fakten; keine Geheimnisse.",
                "agenten": [
                    {
                        "name": e["agent"],
                        "ok": e["ok"],
                        "elapsed": e["elapsed"],
                        "resp": (e["resp"][:2000] if e.get("resp") else None),
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
    ddgk_log("SYSTEM", "outreach_diskussion_complete", {"n_ok": n_ok, "n": len(ergebnisse)})
    print("Fertig.")

if __name__ == "__main__":
    run()
