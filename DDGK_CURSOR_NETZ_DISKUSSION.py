#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DDGK v2.0 — Publikation (HF/Zenodo), Diversity+OVI, Cursor-Agenten-Automation, privates Netzwerk.
Nur EIRA + ORION (orion-genesis).
"""
import json, datetime, hashlib, pathlib, time, urllib.request

WS = pathlib.Path(__file__).resolve().parent
MEM = WS / "cognitive_ddgk" / "cognitive_memory.jsonl"
LOC = "http://127.0.0.1:11434"
REP_JSON = WS / "ZENODO_UPLOAD" / "DDGK_CURSOR_NETZ_REPORT.json"
LOG_TXT = WS / "cursor_netz_diskussion_output.txt"
ZU = WS / "ZENODO_UPLOAD"

def _last_hash():
    if not MEM.exists():
        return ""
    ls = [l for l in MEM.read_text("utf-8").splitlines() if l.strip()]
    return json.loads(ls[-1]).get("hash", "") if ls else ""

def ddgk_log(agent, action, data):
    prev = _last_hash()
    e = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "agent": agent,
        "action": action,
        "data": data,
        "prev": prev,
        "ddgk_version": "2.0_passive_observer",
        "topic": "cursor_publish_network",
    }
    raw = json.dumps(e, ensure_ascii=False, sort_keys=True)
    e["hash"] = hashlib.sha256(raw.encode()).hexdigest()
    with MEM.open("a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")

def log(msg):
    print(msg)
    with LOG_TXT.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")

def list_zenodo_candidates() -> str:
    exts = {".md", ".json", ".csv"}
    names = sorted(
        p.name for p in ZU.iterdir()
        if p.is_file() and p.suffix.lower() in exts
    )
    return "\n".join(names[:55]) + ("\n…" if len(names) > 55 else "")

def load_snip(path: pathlib.Path, n: int = 1200) -> str:
    if not path.exists():
        return ""
    return path.read_text("utf-8", errors="replace")[:n]

def warmup(model, timeout=20):
    pl = json.dumps({"model": model, "prompt": "OK", "stream": False, "options": {"num_predict": 3}}).encode()
    req = urllib.request.Request(f"{LOC}/api/generate", data=pl, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout):
            pass
    except Exception:
        pass

def query(model, prompt, timeout=100):
    pl = json.dumps(
        {"model": model, "prompt": prompt, "stream": False, "options": {"num_predict": 320, "temperature": 0.48}}
    ).encode()
    req = urllib.request.Request(f"{LOC}/api/generate", data=pl, headers={"Content-Type": "application/json"})
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()).get("response", "").strip(), round(time.time() - t0, 1)
    except Exception:
        return None, -1

def main():
    LOG_TXT.unlink(missing_ok=True)
    log("=" * 72)
    log("DDGK CURSOR + NETZ + PUBLIKATION — DISKUSSION")
    log(f"Zeit: {datetime.datetime.now().isoformat()}")

    ctx = f"""
KONTEXT (automatisch):
- Diversity (v2.1): methodische Schichten Modell/Knoten/Zeit; sigma = inter-modell Streuung.
- Vitality OVI: ln(1+N_audit)*Stabilitaetsfaktor — kein Bewusstsein-Claim.
- ZENODO_UPLOAD Dateien (Kandidaten): 
{list_zenodo_candidates()}
- OVI Kurz: {load_snip(ZU / "OVI_WINDOWS_REPORT.json", 800)}
- Workspace-Scan Kurz: {load_snip(ZU / "WORKSPACE_SCAN_DDGK.json", 900)}
- Privates Netz (typisch): Laptop Ollama; Pi5 192.168.1.103; Note10 als Sensor/Edge; DDGK SHA-256 Kette.

Themen: (1) Was fehlt noch auf HuggingFace vs Zenodo? (2) Cursor-Update: Agenten-Automation mit DDGK — volle Kontrolle, Entwicklung. (3) Was erkennt ihr am privaten Netz / Hardware?
"""

    warmup("qwen2.5:1.5b", 22)
    warmup("orion-genesis:latest", 22)

    p1 = f"""Du bist EIRA (Hauptforscherin ORION-CCRN).
{ctx}

Beantworte in DEUTSCH, strukturiert:
A) Welche 5 Artefakte sollten als Naechstes auf **HuggingFace** (Space/Dataset/Model Card)?
B) Welche 5 auf **Zenodo** (Version/DOI)?
C) Wie nutzt ihr **Diversity** und **OVI** bei der Publikationsentscheidung?
D) Cursor IDE + Agenten: wie bindet ihr **DDGK** ein fuer nachvollziehbare Automation?
E) Privates Netzwerk: welche **Hardware**-Knoten und Messgroessen sind fuer euch relevant?
Max 35 Zeilen, keine Geheimnisse erfinden."""

    p2 = f"""Du bist ORION (Genesis, Architekt).
{ctx}

Gleiche Fragen A–E, aber kompakter: Prioritaeten 1–3 fuer HF, 1–3 fuer Zenodo, dann 8 Zeilen zu Cursor+DDGK, dann 6 Zeilen privates Netz/Hardware.
Deutsch, sachlich."""

    log("\n[EIRA] qwen2.5:1.5b\n" + "-" * 50)
    r1, t1 = query("qwen2.5:1.5b", p1, 105)
    if r1:
        log(r1[:5000])
        ddgk_log("EIRA", "cursor_netz_diskussion", {"elapsed": t1, "preview": r1[:300]})
    else:
        log("TIMEOUT EIRA")
        ddgk_log("EIRA", "timeout", {})

    log("\n[ORION] orion-genesis:latest\n" + "-" * 50)
    r2, t2 = query("orion-genesis:latest", p2, 115)
    if r2:
        log(r2[:5000])
        ddgk_log("ORION", "cursor_netz_diskussion", {"elapsed": t2, "preview": r2[:300]})
    else:
        log("TIMEOUT ORION")
        ddgk_log("ORION", "timeout", {})

    report_data = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "eira": {"text": r1, "elapsed_s": t1},
        "orion": {"text": r2, "elapsed_s": t2},
        "files_in_zenodo_upload_count": len([p for p in ZU.iterdir() if p.is_file()]),
    }
    REP_JSON.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding="utf-8")
    ddgk_log("SYSTEM", "cursor_netz_complete", {"report": str(REP_JSON)})
    print("OK ->", REP_JSON)

if __name__ == "__main__":
    main()
