# -*- coding: utf-8 -*-
"""Zentrale Auflösung von Umgebungsvariablen: os.environ, dann EIRA master.env.ini."""
from __future__ import annotations

import re
from pathlib import Path

# Kanonische INI (wie hf_healthcheck.py)
MASTER_ENV = Path(
    r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\EIRA\master.env.ini"
)


def _from_ini(key: str) -> str | None:
    if not MASTER_ENV.exists():
        return None
    txt = MASTER_ENV.read_text(encoding="utf-8", errors="replace")
    m = re.search(rf"^{re.escape(key)}\s*=\s*(\S+)", txt, re.M)
    return m.group(1).strip() if m else None


def get_token(key: str) -> str | None:
    import os

    v = os.environ.get(key)
    if v and v.strip():
        return v.strip()
    v2 = _from_ini(key)
    return v2 if v2 else None
