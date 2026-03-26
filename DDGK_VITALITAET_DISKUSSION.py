#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DDGK v2.0 — VITALITÄT + DIVERSITY + NEUE ERKENNTNISSE
Bezug: OVI (Operational Vitality Index), Abschnitte 8–9 in CCRN_METRIC_FORMALIZATION_v2.1.md
"""
import json, datetime, hashlib, pathlib, time, urllib.request

WS = pathlib.Path(__file__).resolve().parent
MEM = WS / "cognitive_ddgk" / "cognitive_memory.jsonl"
LOC = "http://127.0.0.1:11434"
PI5 = "http://192.168.1.103:11434"
OUT = WS / "vitalitaet_diskussion_output.txt"
REP = WS / "ZENODO_UPLOAD" / "DDGK_VITALITAET_REPORT.json"
SEP = "=" * 70

KONTEXT = """
KONTEXT (v2.1 Spezifikation):
- OVI(T) = ln(1+N_audit) * max(0, 1 - sigma_phi/(sigma_phi+epsilon)) — zeitliche Audit-Aktivitaet, KEIN Bewusstsein.
- Diversity: Modell-, Knoten-, Zeit-Schichten; sigma = inter-modell Streuung.
- DDGK: Passive Observer, SHA-256 Kette in cognitive_memory.jsonl.
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
        "topic": "vitalitaet_diversity",
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

def query(host, model, prompt, timeout=78):
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 220, "temperature": 0.55},
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
        "t": 70,
        "q": f"""Du bist EIRA. {KONTEXT}
Wie haengen OVI (Vitalitaet der Audit-Kette) und wissenschaftliche Glaubwuerdigkeit zusammen — ohne Bewusstseins-Claims?
3 nummerierte Punkte Deutsch, je max 2 Saetze.""",
    },
    {
        "name": "ORION-GENESIS",
        "modell": "orion-genesis:latest",
        "host": LOC,
        "t": 82,
        "q": f"""Du bist ORION. {KONTEXT}
Welche NEUE Hypothese koennte man testen, wenn man OVI gegen kappa oder sigma korreliert (Zeitreihe)?
2 Hypothesen, je 1 Satz, Deutsch.""",
    },
    {
        "name": "GUARDIAN",
        "modell": "orion-v3:latest",
        "host": LOC,
        "t": 82,
        "q": f"""Du bist GUARDIAN. {KONTEXT}
Welche Fehlinterpretation von „Vitalitaet“ muss in Papers verboten sein?
4 kurze Regeln Deutsch.""",
    },
    {
        "name": "NEXUS",
        "modell": "tinyllama:latest",
        "host": PI5,
        "t": 45,
        "q": """NEXUS (Pi5): Does higher edge uptime increase OVI meaningfully if audits are honest?
One paragraph English, max 80 words.""",
    },
    {
        "name": "ORION-ENTFALTET",
        "modell": "orion-entfaltet:latest",
        "host": LOC,
        "t": 82,
        "q": f"""Du bist ORION-ENTFALTET. {KONTEXT}
Nenne EIN spannendes Forschungsloch, das wir mit OVI+DDGK+verteilten Knoten als Erste schliessen koennten.
Max 4 Saetze Deutsch.""",
    },
    {
        "name": "DDGK-KERN",
        "modell": "llama3.2:1b",
        "host": LOC,
        "t": 55,
        "q": f"""Du bist DDGK-KERN. {KONTEXT}
Warum ist Passive Observer wichtig, wenn OVI hoch ist (viele Events)?
3 Bullets Deutsch.""",
    },
]

def run():
    OUT.unlink(missing_ok=True)
    log(SEP)
    log("DDGK v2.0 VITALITÄT + DIVERSITY — DISKUSSIONSRUNDE")
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
            log(f"OK ({elapsed}s):\n{resp[:1500]}")
            ddgk_log(
                ag["name"],
                "vitalitaet_antwort",
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
            ddgk_log(ag["name"], "vitalitaet_timeout", {"modell": ag["modell"]})
            ergebnisse.append(
                {"agent": ag["name"], "ok": False, "resp": None, "elapsed": elapsed}
            )

    log(f"\n{SEP}\nMASTER-SYNTHESE (orion-sik:latest)\n{SEP}")
    ok_antworten = [e for e in ergebnisse if e["ok"]]
    zusammen = "\n".join(
        f"- {e['agent']}: {(e['resp'] or '')[:200]}" for e in ok_antworten
    )
    master_q = f"""Du bist ORION-SIK Master. Fasse zusammen fuer ein Lab-Logbuch:
{kontext_short()}
Agentenantworten:
{zusammen}

Aufgabe: Schreibe EXAKT 6 Zeilen: (1) OVI Bedeutung (2) eine testbare Hypothese (3) Diversity-Link (4) DDGK Rolle (5) ein Risiko (6) naechster Experiment-Schritt.
Deutsch, keine Emojis, keine Bewusstseins-Woerter."""

    master_resp, mt = query(LOC, "orion-sik:latest", master_q, timeout=120)
    if master_resp:
        log(master_resp[:2500])
        ddgk_log("MASTER-ORION-SIK", "vitalitaet_synthese", {"text": master_resp[:500]})
    else:
        log("Master: Timeout — Fallback-Synthese manuell im Report.")
        master_resp = None

    n_ok = sum(1 for e in ergebnisse if e["ok"])
    log(f"\n{SEP}\nErfolgsrate Agenten: {n_ok}/{len(ergebnisse)}")

    REP.parent.mkdir(parents=True, exist_ok=True)
    REP.write_text(
        json.dumps(
            {
                "ts": datetime.datetime.now().isoformat(),
                "topic": "vitalitaet_ovi_diversity_ddgk",
                "spec_ref": "ZENODO_UPLOAD/CCRN_METRIC_FORMALIZATION_v2.1.md",
                "agenten": [
                    {
                        "name": e["agent"],
                        "ok": e["ok"],
                        "elapsed": e["elapsed"],
                        "resp": (e["resp"][:2500] if e.get("resp") else None),
                    }
                    for e in ergebnisse
                ],
                "master_synthese": master_resp,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    log(f"\nReport: {REP.name}")
    ddgk_log(
        "SYSTEM",
        "vitalitaet_diskussion_complete",
        {"n_ok": n_ok, "n": len(ergebnisse), "spec": "v2.1"},
    )
    print("Fertig.")

def kontext_short():
    return "OVI=Audit-Aktivitaet*Stabilitaetsfaktor; kein Bewusstsein; DDGK=Passive Observer."

if __name__ == "__main__":
    run()
