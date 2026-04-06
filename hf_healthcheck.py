#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hugging Face Zugang pruefen — .env (workspace_env) + master.env.ini + optional Cache.
whoami: bevorzugt HUGGINGFACE_TOKEN, sonst HF_TOKEN (env vor INI).
Gibt NIE den vollen Token aus (nur Laenge + Status).
"""
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

CACHE = pathlib.Path.home() / ".cache" / "huggingface" / "token"


def _load_context():
    """dotenv + Pfade; liefert Quellen-Infos ohne Secret-Werte."""
    try:
        from workspace_env import (
            load_hf_tokens_from_master_ini,
            load_workspace_dotenv,
            resolve_master_ini_path,
        )

        load_workspace_dotenv(override=False)
        ini_path = resolve_master_ini_path()
        ini_hf, ini_hg = load_hf_tokens_from_master_ini()
    except ImportError:
        ini_path = None
        ini_hf, ini_hg = None, None

    env_hf = (os.environ.get("HF_TOKEN") or "").strip() or None
    env_hg = (os.environ.get("HUGGINGFACE_TOKEN") or "").strip() or None

    primary = env_hg or ini_hg or env_hf or ini_hf
    primary_src = None
    if env_hg:
        primary_src = "env HUGGINGFACE_TOKEN"
    elif ini_hg:
        primary_src = "INI HUGGINGFACE_TOKEN"
    elif env_hf:
        primary_src = "env HF_TOKEN"
    elif ini_hf:
        primary_src = "INI HF_TOKEN"

    return {
        "ini_path": ini_path,
        "ini_hf": ini_hf,
        "ini_hg": ini_hg,
        "env_hf": env_hf,
        "env_hg": env_hg,
        "primary": primary,
        "primary_src": primary_src,
    }


def whoami(token: str) -> tuple[int, dict | None]:
    req = urllib.request.Request(
        "https://huggingface.co/api/whoami",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8", errors="replace"))
        except Exception:
            body = {"raw": str(e.code)}
        return e.code, body
    except Exception as ex:
        return -1, {"error": str(ex)}


def main() -> int:
    print("=== HF Healthcheck (keine Secrets in der Ausgabe) ===\n")
    ctx = _load_context()

    print(f"master.env.ini: {ctx['ini_path'] or '(nicht gefunden)'}")
    print(
        f"Env HF_TOKEN / HUGGINGFACE_TOKEN: "
        f"{'gesetzt' if ctx['env_hf'] else 'leer'} / {'gesetzt' if ctx['env_hg'] else 'leer'}"
    )
    if ctx["ini_path"]:
        print(
            f"INI HF_TOKEN / HUGGINGFACE_TOKEN: "
            f"{'gesetzt' if ctx['ini_hf'] else 'leer'} / {'gesetzt' if ctx['ini_hg'] else 'leer'}"
        )
        same = (
            ctx["ini_hf"] and ctx["ini_hg"] and (ctx["ini_hf"] == ctx["ini_hg"])
        )
        print(f"INI: HF_TOKEN == HUGGINGFACE_TOKEN: {same}")
    print(f"whoami-Quelle: {ctx['primary_src'] or '(kein Token)'}\n")

    if not ctx["primary"]:
        print("FEHL: Weder HUGGINGFACE_TOKEN noch HF_TOKEN in .env / master.env.ini / Umgebung.")
        print("  → .env aus .env.example; oder MASTER_ENV_INI setzen; oder export HF_TOKEN=...")
        return 2

    code, data = whoami(ctx["primary"])
    if code == 200 and isinstance(data, dict):
        name = data.get("name") or data.get("id") or "?"
        print(f"whoami: OK (HTTP {code}) — angemeldet als: {name}")
        print("\nNaechster Schritt: Bei Bedarf huggingface-cli login für ~/.cache (zusaetzlich).")
        return 0

    print(f"whoami: FEHLER (HTTP {code})")
    if isinstance(data, dict):
        print(f"Detail: {data.get('error', data)}")
    print(
        "\n*** Token wird von Hugging Face abgelehnt (401) oder Netzwerkfehler. ***\n"
        "Moegliche Ursachen: Token widerrufen, abgelaufen, Tippfehler.\n\n"
        "So beheben:\n"
        "  1) https://huggingface.co/settings/tokens — neuen Token\n"
        "  2) In .env HUGGINGFACE_TOKEN=... und/oder HF_TOKEN=... (nicht committen)\n"
        "  3) Oder master.env.ini im Repo oder unter EIRA/ (siehe workspace_env)\n"
        "  4) python hf_healthcheck.py erneut\n"
    )

    if CACHE.exists():
        tc = CACHE.read_text(encoding="utf-8", errors="replace").strip()
        c2, d2 = whoami(tc)
        print(f"\nLokaler Cache ~/.cache/huggingface/token: HTTP {c2} (Laenge Token {len(tc)})")
        if c2 == 200:
            print("Hinweis: Cache-Token funktioniert — .env/INI auf denselben Wert setzen.")
        else:
            print("Hinweis: Cache-Token ungueltig; neuen Token verwenden.")

    return 1


if __name__ == "__main__":
    sys.exit(main())
