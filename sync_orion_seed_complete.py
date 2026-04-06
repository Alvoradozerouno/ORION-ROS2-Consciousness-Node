#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🟢 Automatischer Sync: ORION_SEED_COMPLETE → workspace/external/ORION_SEED_COMPLETE

Excludes: .git, __pycache__, .pytest_cache, node_modules, *.log
Quelle:   ORION_SEED_SOURCE aus OS, <repo>/.env, dann master.env.ini (Allowlist), sonst E:\\ORION_SEED_COMPLETE

Nutzung:
  python sync_orion_seed_complete.py
  python sync_orion_seed_complete.py --dry-run
  python MULTI_AGENT_ASSET_ANALYSIS.py   # sync läuft standardmäßig vor dem Scan
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_WS = Path(__file__).resolve().parent

# .env vor Auswertung von ORION_SEED_SOURCE
try:
    from workspace_env import load_workspace_dotenv

    load_workspace_dotenv(override=False)
except ImportError:
    pass

_DEFAULT_SRC = Path(os.environ.get("ORION_SEED_SOURCE", r"E:\ORION_SEED_COMPLETE"))
_DEFAULT_DST = _WS / "external" / "ORION_SEED_COMPLETE"
_META = _DEFAULT_DST / ".ddgk_seed_integration.json"

_EXCLUDE_DIRS = frozenset({".git", "__pycache__", ".pytest_cache", "node_modules"})


def _should_copy(src: Path, dst: Path) -> bool:
    if not dst.exists():
        return True
    return src.stat().st_mtime > dst.stat().st_mtime


def sync_orion_seed(
    src: Path | None = None,
    dst: Path | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> dict:
    src = Path(src) if src else _DEFAULT_SRC
    dst = Path(dst) if dst else _DEFAULT_DST

    result = {
        "ok": False,
        "source": str(src),
        "dest": str(dst),
        "copied": 0,
        "skipped": 0,
        "errors": 0,
        "dry_run": dry_run,
    }

    if not src.is_dir():
        result["error"] = f"Quelle fehlt oder kein Ordner: {src}"
        return result

    if not dry_run:
        dst.mkdir(parents=True, exist_ok=True)

    for dirpath, dirnames, filenames in os.walk(src, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in _EXCLUDE_DIRS]
        rel = Path(dirpath).relative_to(src)
        target_dir = dst / rel
        for fn in filenames:
            if fn.endswith(".log"):
                result["skipped"] += 1
                continue
            sfile = Path(dirpath) / fn
            tfile = target_dir / fn
            if not force and tfile.exists() and not _should_copy(sfile, tfile):
                result["skipped"] += 1
                continue
            try:
                if dry_run:
                    result["copied"] += 1
                else:
                    target_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(sfile, tfile)
                    result["copied"] += 1
            except OSError:
                result["errors"] += 1

    result["ok"] = result["errors"] == 0

    if not dry_run and result["ok"]:
        meta = {
            "source_path": str(src),
            "workspace_relative": "external/ORION_SEED_COMPLETE",
            "last_sync_utc": datetime.now(timezone.utc).isoformat(),
            "robocopy_excludes": list(_EXCLUDE_DIRS) + ["*.log"],
            "last_stats": {k: result[k] for k in ("copied", "skipped", "errors")},
            "ddgk_notes": {
                "governance": "Skripte mit Netz/Email/Control nur mit HITL + Policy.",
                "secrets": "Keine Klartext-Credentials committen.",
            },
        }
        try:
            _META.parent.mkdir(parents=True, exist_ok=True)
            if _META.exists():
                old = json.loads(_META.read_text(encoding="utf-8"))
                old.update(meta)
                meta = old
            _META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="ORION_SEED_COMPLETE → external/ (auto sync)")
    ap.add_argument("--dry-run", action="store_true", help="Nur zählen, nichts schreiben")
    ap.add_argument("--force", action="store_true", help="Alle Dateien neu kopieren")
    ap.add_argument("--source", type=Path, default=None, help="Override Quellordner")
    ap.add_argument("--dest", type=Path, default=None, help="Override Zielordner")
    args = ap.parse_args()

    r = sync_orion_seed(src=args.source, dst=args.dest, dry_run=args.dry_run, force=args.force)
    status = "🟢" if r.get("ok") else "🔴"
    sym = "📜" if r.get("dry_run") else "🏗️"
    print(f"{status} {sym} ORION_SEED_SYNC  Quelle={r['source']}")
    print(f"   Ziel={r['dest']}")
    print(f"   kopiert/aktualisiert={r['copied']}  übersprungen={r['skipped']}  Fehler={r['errors']}")
    if r.get("error"):
        print(f"   ⚠️ {r['error']}")
    return 0 if r.get("ok") or r.get("error") else 1


if __name__ == "__main__":
    raise SystemExit(main())
