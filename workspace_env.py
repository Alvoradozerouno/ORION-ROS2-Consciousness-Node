#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🟢 Workspace-Konfiguration: .env (python-dotenv) + optionales master.env.ini (Allowlist).

Reihenfolge:
  1) `<repo>/.env` via python-dotenv (override=False → OS + bestehende Envs haben Vorrang)
  2) `master.env.ini` — nur Allowlist-Keys, nur wenn Variable noch fehlt oder leer ist

master.env.ini wird zeilenweise wie KEY=value gelesen (kein [section]-Pflicht).
Keine Werte werden geloggt. Keine Token-Keys auf der Allowlist.

Optional: MASTER_ENV_INI mit absolutem Pfad zur INI-Datei
"""
from __future__ import annotations

import os
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent

# Nur Pfade/Hosts — keine Secrets/Tokens aus INI nach os.environ spiegeln
_MASTER_INI_ALLOWLIST = frozenset(
    {
        "ORION_SEED_SOURCE",
        "OLLAMA_HOST",
        "OLLAMA_PI5",
        "OLLAMA_NOTE10",
    }
)


def repo_root() -> Path:
    return _ROOT


def _env_unset_or_empty(key: str) -> bool:
    v = os.environ.get(key)
    return v is None or not str(v).strip()


def _master_ini_paths() -> list[Path]:
    custom = os.environ.get("MASTER_ENV_INI", "").strip()
    paths: list[Path] = []
    if custom:
        paths.append(Path(custom))
    paths.append(_ROOT / "master.env.ini")
    paths.append(_ROOT.parent / "EIRA" / "master.env.ini")
    return paths


def merge_master_ini_allowlist() -> int:
    """
    Liest erste existierende master.env.ini; setzt nur Allowlist-Keys, nur wo env leer.
    Returns: Anzahl neu gesetzter Variablen (ohne Werte auszugeben).
    """
    path: Path | None = None
    for p in _master_ini_paths():
        if p.is_file():
            path = p
            break
    if path is None:
        return 0

    n = 0
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key not in _MASTER_INI_ALLOWLIST:
            continue
        if not val:
            continue
        if not _env_unset_or_empty(key):
            continue
        os.environ[key] = val
        n += 1
    return n


def load_workspace_dotenv(override: bool = False) -> bool:
    """
    1) Lädt `<repo>/.env` mit python-dotenv (falls installiert).
    2) Ergänzt aus master.env.ini nur Allowlist-Keys für noch leere Variablen.

    Returns True wenn python-dotenv installiert ist; False wenn Paket fehlt
    (INI-Merge läuft trotzdem).
    """
    dotenv_ok = False
    try:
        from dotenv import load_dotenv

        dotenv_ok = True
        env_path = _ROOT / ".env"
        if env_path.is_file():
            load_dotenv(env_path, override=override)
    except ImportError:
        pass

    merge_master_ini_allowlist()
    return dotenv_ok


def dotenv_available() -> bool:
    try:
        import dotenv  # noqa: F401

        return True
    except ImportError:
        return False


def master_ini_allowlist_keys() -> frozenset[str]:
    """Nur für Tests/Docs — welche Keys aus INI übernommen werden dürfen."""
    return frozenset(_MASTER_INI_ALLOWLIST)


def resolve_master_ini_path() -> Path | None:
    """Erste existierende `master.env.ini` aus MASTER_ENV_INI / Repo / EIRA-Nachbar."""
    for p in _master_ini_paths():
        if p.is_file():
            return p
    return None


def load_hf_tokens_from_master_ini() -> tuple[str | None, str | None]:
    """
    Liest HF_TOKEN und HUGGINGFACE_TOKEN aus der ersten gefundenen master.env.ini.
    Keine Logs der Werte. Fehlt die Datei → (None, None).
    """
    path = resolve_master_ini_path()
    if path is None:
        return None, None
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, None
    hf = re.search(r"^HF_TOKEN\s*=\s*(\S+)", text, re.M)
    hg = re.search(r"^HUGGINGFACE_TOKEN\s*=\s*(\S+)", text, re.M)
    return (
        hf.group(1).strip() if hf else None,
        hg.group(1).strip() if hg else None,
    )
