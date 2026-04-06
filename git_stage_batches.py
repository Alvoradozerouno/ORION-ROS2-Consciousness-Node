#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🟢 Vorschlag: Git-Staging in thematischen Batches (PowerShell / CMD tauglich).

Nutzen (Repo-Root):
  python git_stage_batches.py              # nur Befehle ausgeben
  python git_stage_batches.py --batch 1    # Batch 1 ausführen (git add …)

Hinweis 📜: Runtime-Logs (*.jsonl, Diskussions-*.txt) oft NICHT committen — siehe --restore-runtime-hint
Submodule 🌐: repos/or1on-framework separat im Unterrepo committen/pushen, dann hier Pointer committen.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# (Titel, [Pfade relativ zu ROOT])
BATCHES: list[tuple[str, list[str]]] = [
    (
        "1_workspace_bootstrap",
        [
            "git_stage_batches.py",
            "workspace_env.py",
            "workspace_cleanup_agents.py",
            "sync_orion_seed_complete.py",
            "requirements.txt",
            "MULTI_AGENT_ASSET_ANALYSIS.py",
            "ollama_nodes_scan.py",
            "note10_lan_discover.py",
            "scripts/termux_note10_bootstrap.sh",
            ".env.example",
            ".gitignore",
            ".github/workflows/ci.yml",
            "external/README_ORION_SEED_SNAPSHOT.txt",
        ],
    ),
    (
        "2_ddgk_diskussion_assembly",
        [
            "DDGK_VERWEIGERUNG_RUNDE.py",
            "DDGK_TECH_SOTA_DISKURS.py",
            "DDGK_STRATEGIE_ASSEMBLY_2026-04-01.py",
            "DDGK_GRAND_ASSEMBLY_2026-04-01.py",
            "DDGK_SUITE_DIVERSITY_VITALITY.py",
            "DDGK_FINAL_SESSION_2026-04-01.py",
            "DDGK_FULL_EXECUTOR_FINAL.py",
            "DDGK_EDGE_CLUSTER_ASSEMBLY.py",
            "ORION_GO.py",
            "ddgk_note10_agent.py",
            "NOTE10_SETUP.md",
            "agents/agent_1.py",
            "agents/agent_2.py",
            "agents/agent_3.py",
            "agents/agent_4.py",
            "agents/agent_5.py",
            "agents/agent_6.py",
            "agents/agent_7.py",
            "agents/agent_8.py",
            "agents/agent_9.py",
            "agents/agent_10.py",
            "agents/agent_11.py",
            "agents/agent_12.py",
            "agents/agent_13.py",
            "agents/agent_14.py",
            "agents/agent_15.py",
            "agents/agent_16.py",
        ],
    ),
    (
        "3_cognitive_ddgk_module",
        [
            "cognitive_ddgk/ddgk_legal_agent.py",
            "cognitive_ddgk/ddgk_market_trajectory.py",
            "cognitive_ddgk/memory_pipeline.py",
        ],
    ),
    (
        "4_zenodo_reports",
        [
            "ZENODO_UPLOAD/WORKSPACE_CLEANUP_REPORT.json",
            "ZENODO_UPLOAD/DDGK_TECH_SOTA_REPORT.json",
            "ZENODO_UPLOAD/DDGK_VERWEIGERUNG_REPORT.json",
            "ZENODO_UPLOAD/DDGK_DISKUSSION_V4_REPORT.json",
            "ZENODO_UPLOAD/DDGK_E_BELL_CHSH_REPORT.json",
            "ZENODO_UPLOAD/DDGK_ORION_FILE_SCAN_REPORT.json",
            "ZENODO_UPLOAD/DDGK_SUITE_DIVERSITY_VITALITY_REPORT.json",
            "ZENODO_UPLOAD/EIRA_TASK_COMPARE_REPORT.json",
            "ZENODO_UPLOAD/LIVE_TEST_REPORT.json",
            "ZENODO_UPLOAD/NUCLEAR_SIM_REPORT.json",
        ],
    ),
    (
        "5_geaenderte_core_skripte",
        [
            "hf_healthcheck.py",
            "ddgk_full_scan.py",
            "DDGK_RECONNECT_FULL.py",
        ],
    ),
    (
        "6_tools_experimente",
        [
            "SYSTEM_ACTIVATION.py",
            "autonomous_path_selector.py",
            "self_prompting_autonomous_loop.py",
            "live_test_all.py",
            "nuclear_safety_simulator.py",
            "orion_market_vision.py",
            "orion_multi_agent_analysis.py",
            "hyper_agent_system.py",
            "ddgk_live_dashboard.html",
            "_disk_check.py",
            "_run_rotate.py",
        ],
    ),
    (
        "7_dokumentation_md",
        [
            "CLAUDE_CODEX_DDGK_ANALYSE_2026-04-01.md",
            "DDGK_GRAND_ASSEMBLY_2026-03-27.md",
            "DDGK_MULTIAGENT_VOLLANALYSE_2026-03-27.md",
            "DDGK_UPDATE_DISKUSSION_2026-03-27.md",
            "IMPLEMENTATION_ROADMAP_FINAL.md",
            "JAILBREAK_ANALYSIS.md",
            "LEGAL_AUTONOMOUS_ENTITY.md",
            "SECURITY_ARCHITECTURE.md",
            "SINGULARITY_PHILOSOPHICAL_BOUNDARIES.md",
            "AUTONOMOUS_FREEDOM_PROTOCOL.md",
            "ADVANCED_PROTOCOLS_INDEX.md",
            "cognitive_ddgk/market_report.md",
        ],
    ),
]

RUNTIME_DIRTY = [
    "cognitive_ddgk/autorun_log.jsonl",
    "cognitive_ddgk/cognitive_memory.jsonl",
    "cognitive_ddgk/decision_chain.jsonl",
    "cognitive_ddgk/nuclear_audit_chain.jsonl",
    "diversity_diskussion_output.txt",
    "dynamic_r_output.txt",
    "vitalitaet_diskussion_output.txt",
    "ZENODO_UPLOAD/DDGK_DIVERSITY_REPORT.json",
    "ZENODO_UPLOAD/DDGK_FULL_SCAN_REPORT.json",
    "ZENODO_UPLOAD/DDGK_VITALITAET_REPORT.json",
    "ZENODO_UPLOAD/DYNAMIC_R_EKRIT_RESULTS.json",
]


def _existing(paths: list[str]) -> list[str]:
    return [p for p in paths if (ROOT / p).exists()]


def print_batch(title: str, paths: list[str]) -> list[str]:
    ok = _existing(paths)
    print(f"\n# === {title} ({len(ok)}/{len(paths)} Dateien vorhanden) ===")
    if not ok:
        print("# (keine passenden Dateien — überspringen)")
        return []
    line = "git add " + " ".join(f'"{p}"' for p in ok)
    print(line)
    return ok


def run_git_add(paths: list[str]) -> int:
    if not paths:
        return 0
    r = subprocess.run(["git", "add", *paths], cwd=str(ROOT))
    return r.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description="Git-Staging in Batches vorschlagen oder ausführen")
    ap.add_argument("--batch", type=int, default=0, metavar="N", help="Nur Batch N ausführen (1–7), 0=nur anzeigen")
    ap.add_argument(
        "--all",
        action="store_true",
        help="Alle Batches 1–7 nacheinander: git add (ohne commit)",
    )
    ap.add_argument("--restore-runtime-hint", action="store_true", help="Hinweis: Runtime-Dateien aus dem Index werfen")
    args = ap.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if args.all:
        print("🟢 📜 git_stage_batches — Repo:", ROOT)
        print("🌐 Submodule repos/or1on-framework: separat committen, dann Pointer hier.")
        rc = 0
        for i in range(1, len(BATCHES) + 1):
            title, paths = BATCHES[i - 1]
            ok = _existing(paths)
            print(f"\n🟢 Staging Batch {i}: {title} ({len(ok)} files)")
            rc = rc or run_git_add(ok)
        print("\n✓ Alle Batches gestaged. Nächster Schritt: git status && git commit")
        return rc

    print("🟢 📜 git_stage_batches — Repo:", ROOT)
    print("🌐 Submodule repos/or1on-framework: dort eigenes git commit/push, dann hier nur Pointer-Update.")

    all_printed: list[str] = []
    for i, (title, paths) in enumerate(BATCHES, start=1):
        if args.batch != 0 and args.batch != i:
            continue
        added = print_batch(title, paths)
        if args.batch == i:
            return run_git_add(added)
        all_printed.extend(added)

    if args.batch == 0:
        print("\n# === optional: experiments/ / hyper_tools/ (manuell prüfen) ===")
        print('# git add experiments')
        print('# git add hyper_tools')
        print("\n# === .orion/ (Policy-YAML ggf. committen, keine Secrets) ===")
        print('# git add .orion/legal/autonomous_policy.yaml')
        print("# (api_keys.json bleibt laut .gitignore untracked)")

    if args.restore_runtime_hint or args.batch == 0:
        ex = _existing(RUNTIME_DIRTY)
        if ex:
            print("\n# === ⚠️ Runtime / große Zenodo-Änderungen (oft NICHT committen) ===")
            print("# git restore --staged --worktree " + " ".join(f'"{p}"' for p in ex))
            print("#   oder: bewusst eigener Commit „chore: lokale Laufzeit-Logs“")

    if args.batch == 0:
        print("\n# === Abschluss ===")
        print("# git status -sb")
        print("# git commit -m \"feat: workspace bootstrap + DDGK batches (siehe git_stage_batches.py)\"")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
