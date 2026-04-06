#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ Workspace-Cleanup — Agenten für Hygiene, Git-Inventar, .gitignore-Pflege.

Nur sichere Operationen: Cache-Verzeichnisse löschen, .gitignore ergänzen (Block-Marker).
Keine Löschung von Quellcode, .env oder cognitive_ddgk/*.jsonl.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

GITIGNORE_MARKER_BEGIN = "# <<< MULTIAGENT_WORKSPACE_CLEANUP_BEGIN"
GITIGNORE_MARKER_END = "# <<< MULTIAGENT_WORKSPACE_CLEANUP_END"

DEFAULT_GITIGNORE_LINES = [
    "# Generierte Asset-Analyse (Multi-Agent)",
    "cognitive_ddgk/asset_analysis_report.json",
    "# ORION-Seed-Snapshot — wiederherstellbar: python sync_orion_seed_complete.py",
    "external/ORION_SEED_COMPLETE/",
]


@dataclass
class HygieneAgent:
    agent_id: str = "AGENT-5-HYGIENE"

    def purge_python_caches(self, root: Path, dry_run: bool) -> dict[str, Any]:
        removed_dirs: list[str] = []
        removed_files: list[str] = []
        for dirpath, dirnames, filenames in os.walk(root, topdown=True):
            rel_parts = Path(dirpath).relative_to(root).parts
            if ".git" in rel_parts:
                dirnames[:] = []
                continue
            dirnames[:] = [
                d
                for d in dirnames
                if d not in ("node_modules", "dist", "build", ".svn")
            ]
            if Path(dirpath).name == "__pycache__":
                if not dry_run:
                    shutil.rmtree(dirpath, ignore_errors=True)
                removed_dirs.append(str(Path(dirpath)))
                dirnames[:] = []
                continue
            base = Path(dirpath).name
            if base in (".pytest_cache", ".mypy_cache", ".ruff_cache"):
                if not dry_run:
                    shutil.rmtree(dirpath, ignore_errors=True)
                removed_dirs.append(str(Path(dirpath)))
                dirnames[:] = []
                continue
            for fn in filenames:
                if fn.endswith((".pyc", ".pyo")):
                    fp = Path(dirpath) / fn
                    if not dry_run:
                        try:
                            fp.unlink()
                        except OSError:
                            pass
                    removed_files.append(str(fp))
        return {
            "agent": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "dry_run": dry_run,
            "removed_cache_dirs": removed_dirs,
            "removed_bytecode_files": removed_files[:500],
            "removed_bytecode_truncated": len(removed_files) > 500,
            "removed_bytecode_total": len(removed_files),
        }


@dataclass
class GitInventoryAgent:
    agent_id: str = "AGENT-6-GIT-INVENTORY"

    def status(self, root: Path) -> dict[str, Any]:
        try:
            r = subprocess.run(
                ["git", "status", "--porcelain=v1", "-u"],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=120,
            )
            lines = [ln for ln in (r.stdout or "").splitlines() if ln.strip()]
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as e:
            return {
                "agent": self.agent_id,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "lines": [],
            }
        untracked: list[str] = []
        other: list[str] = []
        for ln in lines:
            if ln.startswith("?? "):
                path = ln[3:].strip().strip('"')
                if " -> " in path:
                    path = path.split(" -> ", 1)[-1].strip()
                untracked.append(path)
            else:
                other.append(ln)
        return {
            "agent": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "returncode": r.returncode,
            "untracked": untracked,
            "untracked_count": len(untracked),
            "other_lines_sample": other[:100],
        }


@dataclass
class UntrackedClassifierAgent:
    agent_id: str = "AGENT-7-UNTRACKED-CLASSIFIER"

    def classify(self, paths: list[str]) -> dict[str, Any]:
        buckets: dict[str, list[str]] = {
            "python_tools": [],
            "markdown_docs": [],
            "zenodo_json": [],
            "cognitive_generated": [],
            "external_tree": [],
            "config_dotfiles": [],
            "other": [],
        }
        for p in paths:
            pl = p.replace("\\", "/").lower()
            if pl.startswith("external/"):
                buckets["external_tree"].append(p)
            elif pl.startswith("zenodo_upload/") and pl.endswith(".json"):
                buckets["zenodo_json"].append(p)
            elif pl.startswith("cognitive_ddgk/"):
                buckets["cognitive_generated"].append(p)
            elif pl.endswith(".py"):
                buckets["python_tools"].append(p)
            elif pl.endswith(".md"):
                buckets["markdown_docs"].append(p)
            elif pl.startswith(".") or pl.endswith((".yaml", ".yml", ".ini.example", "env.example")):
                buckets["config_dotfiles"].append(p)
            else:
                buckets["other"].append(p)
        return {
            "agent": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "buckets": buckets,
            "hint": "external/ORION_SEED_COMPLETE ist per .gitignore ausgeschlossen — Sync-Skript nutzen.",
        }


@dataclass
class GitignoreMaintenanceAgent:
    agent_id: str = "AGENT-8-GITIGNORE"

    def ensure_block(self, root: Path, dry_run: bool) -> dict[str, Any]:
        gi = root / ".gitignore"
        if not gi.is_file():
            return {"agent": self.agent_id, "skipped": True, "reason": "no .gitignore"}
        text = gi.read_text(encoding="utf-8", errors="replace")
        if GITIGNORE_MARKER_BEGIN in text and GITIGNORE_MARKER_END in text:
            return {"agent": self.agent_id, "updated": False, "reason": "block_present"}
        block = "\n".join(
            [
                "",
                GITIGNORE_MARKER_BEGIN,
                *DEFAULT_GITIGNORE_LINES,
                GITIGNORE_MARKER_END,
                "",
            ]
        )
        if dry_run:
            return {"agent": self.agent_id, "updated": False, "dry_run": True, "would_append_lines": len(DEFAULT_GITIGNORE_LINES)}
        gi.write_text(text.rstrip() + block, encoding="utf-8")
        return {"agent": self.agent_id, "updated": True, "appended_lines": len(DEFAULT_GITIGNORE_LINES)}


def run_cleanup_pipeline(
    root: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parent
    h = HygieneAgent()
    g = GitInventoryAgent()
    c = UntrackedClassifierAgent()
    gi = GitignoreMaintenanceAgent()

    r_h = h.purge_python_caches(root, dry_run=dry_run)
    r_g = g.status(root)
    untracked = r_g.get("untracked") or []
    r_c = c.classify(untracked)
    r_gi = gi.ensure_block(root, dry_run=dry_run)

    return {
        "timestamp": datetime.now().isoformat(),
        "workspace_root": str(root),
        "dry_run": dry_run,
        "agents": [r_h, r_g, r_c, r_gi],
        "summary": {
            "cache_dirs_removed": len(r_h.get("removed_cache_dirs", [])),
            "bytecode_hits": r_h.get("removed_bytecode_total", 0),
            "untracked_files": r_g.get("untracked_count", 0),
            "gitignore_updated": r_gi.get("updated", False),
        },
    }
