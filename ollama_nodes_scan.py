#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama-Erreichbarkeit: Laptop, Pi5, optional Note10 (HTTP /api/tags).

Hinweis: „Installiert“ = erreichbarer Ollama-HTTP-Dienst (kein SSH/Package-Check).
Note10: In Termux typisch OLLAMA_HOST=0.0.0.0 und im selben WLAN die LAN-IP des
Handys eintragen (OLLAMA_NOTE10=http://<ip>:11434).
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request
from typing import Any


def _normalize_base(url: str) -> str:
    u = (url or "").strip()
    if not u:
        return ""
    if u.startswith("http://") or u.startswith("https://"):
        return u.rstrip("/")
    return f"http://{u}".rstrip("/")


def probe_ollama(base: str, timeout: float) -> dict[str, Any]:
    """GET /api/version (optional) und /api/tags."""
    out: dict[str, Any] = {
        "url": base,
        "skipped": False,
        "einsatzbereit": False,
        "version": None,
        "model_count": 0,
        "models": [],
        "fehler": None,
    }
    if not base:
        out["fehler"] = "keine URL konfiguriert"
        return out

    ver_url = f"{base}/api/version"
    try:
        with urllib.request.urlopen(ver_url, timeout=timeout) as r:
            body = json.loads(r.read().decode("utf-8", errors="replace"))
            out["version"] = body.get("version")
    except Exception:
        pass

    tags_url = f"{base}/api/tags"
    try:
        with urllib.request.urlopen(tags_url, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8", errors="replace"))
        models = [m.get("name", "?") for m in data.get("models", []) if isinstance(m, dict)]
        out["models"] = models
        out["model_count"] = len(models)
        out["einsatzbereit"] = True
    except urllib.error.HTTPError as ex:
        out["fehler"] = f"HTTP {ex.code}"
    except Exception as ex:
        out["fehler"] = str(ex)[:160]

    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Ollama Laptop / Pi5 / Note10 scannen")
    ap.add_argument(
        "--laptop",
        default=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"),
        help="Laptop Ollama (Default: env OLLAMA_HOST oder 127.0.0.1:11434)",
    )
    ap.add_argument(
        "--pi5",
        default=os.environ.get("OLLAMA_PI5", "http://192.168.1.103:11434"),
        help="Pi5 Ollama (Default: env OLLAMA_PI5)",
    )
    ap.add_argument(
        "--note10",
        default=os.environ.get("OLLAMA_NOTE10", ""),
        help="Note10 Ollama-URL, z. B. http://192.168.1.x:11434 (Default: env OLLAMA_NOTE10)",
    )
    ap.add_argument("--timeout", type=float, default=6.0, help="Sekunden pro Request")
    ap.add_argument(
        "--json-out",
        type=pathlib.Path,
        default=None,
        help="Optional: Report als JSON schreiben",
    )
    args = ap.parse_args()

    knoten = [
        ("Laptop", _normalize_base(args.laptop)),
        ("Pi5", _normalize_base(args.pi5)),
        ("Note10", _normalize_base(args.note10)),
    ]

    print("\n=== Ollama-Knoten-Scan ===\n", flush=True)
    ergebnis: dict[str, Any] = {"knoten": {}}

    for name, base in knoten:
        if name == "Note10" and not base:
            row = {
                "url": "",
                "skipped": True,
                "einsatzbereit": False,
                "version": None,
                "model_count": 0,
                "models": [],
                "fehler": "OLLAMA_NOTE10 nicht gesetzt — übersprungen",
            }
            ergebnis["knoten"][name] = row
            print(f"  [{name}] SKIP — OLLAMA_NOTE10 nicht gesetzt (--note10)\n", flush=True)
            continue

        row = probe_ollama(base, args.timeout)
        ergebnis["knoten"][name] = row
        if row["einsatzbereit"]:
            v = row.get("version") or "?"
            print(
                f"  [{name}] OK — einsatzbereit — v{v} — {row['model_count']} Modell(e)",
                flush=True,
            )
            preview = row["models"][:8]
            if preview:
                print(f"         Modelle: {preview}{' …' if len(row['models']) > 8 else ''}", flush=True)
        else:
            print(f"  [{name}] FAIL — nicht erreichbar: {row.get('fehler')}", flush=True)
        print(f"         URL: {base or '(leer)'}\n", flush=True)

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(ergebnis, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"JSON: {args.json_out}\n", flush=True)

    ok_ct = sum(1 for v in ergebnis["knoten"].values() if v.get("einsatzbereit"))
    pruef = sum(1 for v in ergebnis["knoten"].values() if not v.get("skipped"))
    skip_ct = sum(1 for v in ergebnis["knoten"].values() if v.get("skipped"))
    print(
        f"Zusammenfassung: {ok_ct}/{pruef} gepruefte Knoten OK"
        + (f" ({skip_ct} uebersprungen)" if skip_ct else "")
        + ".\n",
        flush=True,
    )
    return 0 if ok_ct == pruef else 1


if __name__ == "__main__":
    sys.exit(main())
