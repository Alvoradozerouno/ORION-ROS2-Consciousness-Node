#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zentrale Liste bekannter Credential-/API-Env-Keys (keine Werte, kein Logging von Secrets).

Nach load_workspace_dotenv() prüfen, welche Variablen in os.environ gesetzt sind.
"""
from __future__ import annotations

import os

# Reihenfolge: grob nach Dienst gruppiert
CREDENTIAL_ENV_KEYS: tuple[str, ...] = (
    "HUGGINGFACE_TOKEN",
    "HF_TOKEN",
    "HUGGING_FACE_HUB_TOKEN",
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "GITHUB_PAT",
    "ZENODO_API_TOKEN",
    "ZENODO_TOKEN",
    "SERPAPI_KEY",
    "NEWS_API_KEY",
    "SMTP_HOST",
    "SMTP_USER",
    "SMTP_PASS",
    "EMAIL_ADDRESS",
    "EMAIL_PASSWORD",
    "DISCORD_WEBHOOK_URL",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "SLACK_WEBHOOK_URL",
    "IBM_QUANTUM_TOKEN",
    "NASA_API_KEY",
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "SUPABASE_ANON_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "DDGK_API_KEY",
)


def _is_set(key: str) -> bool:
    v = os.environ.get(key)
    return bool(v and str(v).strip())


def credential_env_status() -> dict[str, bool]:
    """True = nicht-leer in os.environ (nach vorherigem load_workspace_dotenv empfohlen)."""
    return {k: _is_set(k) for k in CREDENTIAL_ENV_KEYS}


def print_credentials_overview(compact: bool = False) -> None:
    from workspace_env import load_hf_tokens_from_master_ini, load_workspace_dotenv, resolve_master_ini_path

    load_workspace_dotenv(override=False)
    st = credential_env_status()
    n_set = sum(1 for v in st.values() if v)
    ini_p = resolve_master_ini_path()
    ini_hf, ini_hg = load_hf_tokens_from_master_ini()

    if compact:
        extra = ""
        if ini_p:
            extra = f" | master.env.ini: {ini_p.name} (HF_TOKEN={'ja' if ini_hf else 'nein'}, HUGGINGFACE_TOKEN={'ja' if ini_hg else 'nein'})"
        print(
            f"[ENV/CRED] {n_set}/{len(st)} Keys gesetzt (keine Werte).{extra}"
        )
        print("            Vollstaendige Liste: python scripts/env_credential_status.py")
        print()
        return

    print("[ENV/CRED] Uebersicht (nur gesetzt/leer, keine Werte)")
    print(f"   master.env.ini: {ini_p if ini_p else '(nicht gefunden)'}")
    if ini_p:
        print(
            f"   INI HF_TOKEN / HUGGINGFACE_TOKEN vorhanden: "
            f"{bool(ini_hf)} / {bool(ini_hg)}"
        )
    for k in CREDENTIAL_ENV_KEYS:
        sym = "x" if st[k] else "."
        print(f"   [{sym}] {k}")
    print()
