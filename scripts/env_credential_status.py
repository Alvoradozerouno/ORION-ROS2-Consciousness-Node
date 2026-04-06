#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Env-Credential-Status ohne Secret-Ausgabe (Repo-Root = Parent von scripts/)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from workspace_credentials import print_credentials_overview

    ap = argparse.ArgumentParser(description="Zeigt welche API/Credential-Env-Keys gesetzt sind.")
    ap.add_argument("--compact", action="store_true", help="Eine Zeile + Hinweis")
    args = ap.parse_args()
    print_credentials_overview(compact=args.compact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
