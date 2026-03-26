#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OVI nach CCRN_METRIC_FORMALIZATION_v2.1 §9 — aus cognitive_memory.jsonl."""
import json, math, pathlib, re, statistics
from collections import defaultdict
from datetime import datetime, timezone

WS = pathlib.Path(__file__).resolve().parent
MEM = WS / "cognitive_ddgk" / "cognitive_memory.jsonl"
OUT_JSON = WS / "ZENODO_UPLOAD" / "OVI_WINDOWS_REPORT.json"
OUT_CSV = WS / "ZENODO_UPLOAD" / "ovi_by_day.csv"
EPS = 0.05

def extract_phis(obj, out):
    """Nur explizite phi-Werte (0..1.2), nicht kappa."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("phi", "phi_val", "phi_i") and isinstance(v, (int, float)):
                x = float(v)
                if 0.0 <= x <= 1.2:
                    out.append(x)
            else:
                extract_phis(v, out)
    elif isinstance(obj, list):
        for x in obj:
            extract_phis(x, out)

def day_key(ts: str) -> str | None:
    if not ts or len(ts) < 10:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")
    except Exception:
        return None

def main():
    if not MEM.exists():
        print("Keine cognitive_memory.jsonl")
        return
    lines = [l for l in MEM.read_text("utf-8").splitlines() if l.strip()]
    by_day: dict[str, list] = defaultdict(lambda: {"n": 0, "phis": []})
    for line in lines:
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = e.get("ts") or ""
        dk = day_key(ts)
        if not dk:
            continue
        by_day[dk]["n"] += 1
        extract_phis(e.get("data") or {}, by_day[dk]["phis"])

    rows = []
    for dk in sorted(by_day.keys()):
        n = by_day[dk]["n"]
        phis = by_day[dk]["phis"]
        if len(phis) >= 2:
            sigma_phi = statistics.stdev(phis)
        elif len(phis) == 1:
            sigma_phi = 0.0
        else:
            sigma_phi = 0.0
        factor = max(0.0, 1.0 - sigma_phi / (sigma_phi + EPS)) if sigma_phi >= 0 else 1.0
        ovi = math.log(1 + n) * factor
        rows.append({
            "day_utc": dk,
            "N_audit": n,
            "sigma_phi_sample": round(sigma_phi, 6),
            "phi_samples_count": len(phis),
            "OVI": round(ovi, 6),
        })

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps({"source": str(MEM), "windows": rows}, indent=2), encoding="utf-8")
    with OUT_CSV.open("w", encoding="utf-8") as f:
        f.write("day_utc,N_audit,sigma_phi_sample,phi_samples_count,OVI\n")
        for r in rows:
            f.write(f"{r['day_utc']},{r['N_audit']},{r['sigma_phi_sample']},{r['phi_samples_count']},{r['OVI']}\n")
    print(f"OK: {len(rows)} Tage -> {OUT_JSON.name}, {OUT_CSV.name}")

if __name__ == "__main__":
    main()
