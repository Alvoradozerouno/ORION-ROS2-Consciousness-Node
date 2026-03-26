#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WWW-Recherche via SerpAPI (Key nur aus Umgebung oder master.env.ini — nie ins Repo).
Schreibt ZENODO_UPLOAD/WWW_RESEARCH_LIVE.json (ohne API-Key).
"""
import json, pathlib, re, urllib.parse, urllib.request

WS = pathlib.Path(__file__).resolve().parent
INI = pathlib.Path(r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\EIRA\master.env.ini")
OUT = WS / "ZENODO_UPLOAD" / "WWW_RESEARCH_LIVE.json"

QUERIES = [
    "LLM output variability entropy calibration measurement 2024",
    "Samsung Exynos 9820 NPU mobile on-device inference",
    "next experiment distributed LLM network evaluation reproducibility",
]

def load_serp_key() -> str | None:
    import os
    k = os.environ.get("SERPAPI_KEY", "").strip()
    if k:
        return k
    if not INI.exists():
        return None
    txt = INI.read_text("utf-8", errors="replace")
    m = re.search(r"SERPAPI_KEY\s*=\s*(\S+)", txt)
    return m.group(1).strip() if m else None

def fetch_serp(q: str, api_key: str) -> dict:
    params = urllib.parse.urlencode(
        {"engine": "google", "q": q, "api_key": api_key, "num": "5"}
    )
    url = f"https://serpapi.com/search.json?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "ORION-DDGK/1.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))

def main():
    key = load_serp_key()
    results = {"queries": [], "error": None, "source": "serpapi" if key else "none"}
    if not key:
        results["error"] = "SERPAPI_KEY fehlt (env oder master.env.ini)"
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(results["error"])
        return
    for q in QUERIES:
        try:
            data = fetch_serp(q, key)
            organic = data.get("organic_results") or []
            results["queries"].append({
                "q": q,
                "top": [
                    {"title": o.get("title"), "link": o.get("link"), "snippet": (o.get("snippet") or "")[:400]}
                    for o in organic[:5]
                ],
            })
        except Exception as ex:
            results["queries"].append({"q": q, "error": str(ex)[:200]})
    OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"OK -> {OUT.name} ({len(results['queries'])} Queries)")

if __name__ == "__main__":
    main()
