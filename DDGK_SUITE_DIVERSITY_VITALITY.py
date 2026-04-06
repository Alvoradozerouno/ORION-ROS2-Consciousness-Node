#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DDGK Multi-Agent Suite — Reihenfolge:
  1) DDGK_DIVERSITY_DISKUSSION.py   (methodische Vielfalt, sigma, Outreach)
  2) DDGK_VITALITAET_DISKUSSION.py (OVI, v2.1, Diversity-Link, DDGK Passive Observer)

Reports: ZENODO_UPLOAD/DDGK_DIVERSITY_REPORT.json, DDGK_VITALITAET_REPORT.json
Suite:   ZENODO_UPLOAD/DDGK_SUITE_DIVERSITY_VITALITY_REPORT.json
Memory:  cognitive_memory.jsonl (SYSTEM ddgk_suite_diversity_vitality_complete)

Ausfuehrung: python DDGK_SUITE_DIVERSITY_VITALITY.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

WS = Path(__file__).resolve().parent
MEM = WS / "cognitive_ddgk" / "cognitive_memory.jsonl"
ZENODO = WS / "ZENODO_UPLOAD"
STEPS = [
    ("DDGK_DIVERSITY_DISKUSSION.py", "diversity_diskussion"),
    ("DDGK_VITALITAET_DISKUSSION.py", "vitalitaet_diskussion"),
]


def _utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def memory_append(action: str, data: dict) -> None:
    if not MEM.exists():
        return
    lines = [l for l in MEM.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
    prev = json.loads(lines[-1]).get("hash", "") if lines else ""
    entry = {"ts": _utc(), "agent": "SYSTEM", "action": action, "data": data, "prev": prev}
    raw = json.dumps(entry, ensure_ascii=False)
    entry["hash"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    with MEM.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    results = []
    for script, key in STEPS:
        path = WS / script
        if not path.exists():
            print(f"FEHL: {script} nicht gefunden", file=sys.stderr)
            return 2
        print(f"\n{'='*60}\n  SUITE: starte {script}\n{'='*60}\n", flush=True)
        r = subprocess.run([sys.executable, str(path)], cwd=str(WS))
        results.append({"script": script, "exit": r.returncode})
        if r.returncode != 0:
            print(f"WARN: {script} Exit {r.returncode}", file=sys.stderr)

    ZENODO.mkdir(parents=True, exist_ok=True)
    suite_path = ZENODO / "DDGK_SUITE_DIVERSITY_VITALITY_REPORT.json"
    rep = {
        "ts_utc": _utc(),
        "suite": "DDGK_DIVERSITY_VITALITY_v1",
        "steps": results,
        "reports_expected": [
            "DDGK_DIVERSITY_REPORT.json",
            "DDGK_VITALITAET_REPORT.json",
        ],
        "features": [
            "diversity: methodische Vielfalt, sigma, DDGK v2 passive observer",
            "vitalitaet: OVI, CCRN_METRIC_FORMALIZATION_v2.1, Master orion-sik",
        ],
    }
    suite_path.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    memory_append(
        "ddgk_suite_diversity_vitality_complete",
        {"steps": results, "suite_report": str(suite_path.relative_to(WS))},
    )
    print(f"\nSuite-Report: {suite_path}", flush=True)
    return 0 if all(s["exit"] == 0 for s in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
