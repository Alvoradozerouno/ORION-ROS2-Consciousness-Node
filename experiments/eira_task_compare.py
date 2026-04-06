#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EIRA Testaufgabe — gleicher Prompt, zwei lokale Ollama-Modelle, Metriken-Vergleich.

Optional: IBM_QUANTUM_TOKEN-Status (ohne Token auszugeben): nur ob gesetzt + einfacher API-Ping.

Umgebung:
  - IBM_QUANTUM_TOKEN: os.environ oder EIRA/master.env.ini (siehe env_resolve.py)
  - Weitere .env-Dateien: Workspace-Root hat oft keine; EIRA/.env ist separat (nicht im ORION-Repo).

Ausgabe: ZENODO_UPLOAD/EIRA_TASK_COMPARE_REPORT.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

WS = Path(__file__).resolve().parent.parent
if str(WS) not in sys.path:
    sys.path.insert(0, str(WS))
ZENODO = WS / "ZENODO_UPLOAD"

from experiments.env_resolve import get_token  # noqa: E402

OLLAMA = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")

DEFAULT_TASK = """\
TESTAUFGABE EIRA (kurz, präzise, Deutsch):
Erkläre in genau 4 nummerierten Sätzen:
(1) Was misst κ im CCRN-Netz?
(2) Was misst ein CHSH-Wert S in einem LLM-Experiment?
(3) Warum sind das verschiedene Konzepte?
(4) Ein möglicher Fehler, wenn man sie verwechselt.
"""


def ollama_run(model: str, prompt: str, timeout: float = 120.0) -> dict:
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.35, "num_predict": 400},
        }
    ).encode()
    req = urllib.request.Request(
        f"{OLLAMA.rstrip('/')}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
        wall = time.perf_counter() - t0
        data = json.loads(raw.decode("utf-8", errors="replace"))
        text = (data.get("response") or "").strip()
        ev = int(data.get("eval_count") or 0)
        tps = ev / wall if wall > 0 else 0.0
        return {
            "ok": True,
            "text": text,
            "wall_s": round(wall, 3),
            "eval_count": ev,
            "tokens_per_s": round(tps, 3),
            "error": None,
        }
    except Exception as e:
        return {
            "ok": False,
            "text": "",
            "wall_s": round(time.perf_counter() - t0, 3),
            "eval_count": 0,
            "tokens_per_s": 0.0,
            "error": str(e)[:200],
        }


def ibm_token_probe(token: str) -> dict:
    """Minimaler Check: IBM Quantum API (kann je nach Account variieren)."""
    if not token:
        return {"present": False, "http": None, "note": "kein Token"}
    # Öffentlicher Health/Info-Endpunkt (ohne sensibles Echo)
    url = "https://api.quantum.ibm.com/api/v1/version"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            code = r.status
            _ = r.read(500)
        return {"present": True, "http": code, "endpoint": url}
    except urllib.error.HTTPError as e:
        return {
            "present": True,
            "http": e.code,
            "note": "HTTPError — Token evtl. ungültig oder Scope",
        }
    except Exception as e:
        return {"present": True, "http": None, "note": str(e)[:120]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eira-model", default="qwen2.5:1.5b", help="Modell für EIRA-Rolle")
    ap.add_argument("--compare-model", default="llama3.2:1b", help="Vergleichs-LLM")
    ap.add_argument("--task", default="", help="Eigene Aufgabe (sonst Default)")
    ap.add_argument("--skip-ibm", action="store_true")
    args = ap.parse_args()

    task = args.task.strip() or DEFAULT_TASK
    ibm = get_token("IBM_QUANTUM_TOKEN") if not args.skip_ibm else None
    ibm_status = ibm_token_probe(ibm or "")

    print("=== EIRA Task Compare ===", file=sys.stderr)
    print(f"EIRA-Modell:    {args.eira_model}", file=sys.stderr)
    print(f"Vergleich:      {args.compare_model}", file=sys.stderr)
    print(f"IBM Token:      {'gesetzt (Laenge ' + str(len(ibm)) + ')' if ibm else 'nicht gefunden'}", file=sys.stderr)

    r_eira = ollama_run(args.eira_model, task)
    r_cmp = ollama_run(args.compare_model, task)

    report = {
        "ts_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "ollama_host": OLLAMA,
        "task_preview": task[:200] + ("…" if len(task) > 200 else ""),
        "eira": {"model": args.eira_model, **r_eira},
        "compare": {"model": args.compare_model, **r_cmp},
        "ibm_quantum": {
            "token_from_env_or_master_ini": bool(ibm),
            "probe": ibm_status,
        },
        "env_hinweis": {
            "master_env_ini": "EIRA/master.env.ini enthält u.a. IBM_QUANTUM_TOKEN",
            "eira_dotenv": "EIRA/.env — separat; hier kein IBM-Eintrag nötig, wenn INI genutzt wird",
            "workspace": "ORION-Repo: optional .env mit IBM_QUANTUM_TOKEN=… (nicht committen)",
        },
    }
    ZENODO.mkdir(parents=True, exist_ok=True)
    out = ZENODO / "EIRA_TASK_COMPARE_REPORT.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nReport: {out}", file=sys.stderr)
    return 0 if (r_eira["ok"] and r_cmp["ok"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
