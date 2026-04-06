#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ORION_GO — ein Eintrag: Umgebung, Executor-Struktur, Edge-Assembly, Credential-Zeile.

  python ORION_GO.py
  python ORION_GO.py --no-edge      # nur Struktur + Credentials
  python ORION_GO.py --multi-agent  # danach MULTI_AGENT_ASSET_ANALYSIS (Seed-Sync)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description="ORION/DDGK Bootstrap + Edge-Assembly")
    ap.add_argument("--no-edge", action="store_true", help="Kein DDGK_EDGE_CLUSTER_ASSEMBLY")
    ap.add_argument("--multi-agent", action="store_true", help="Anschließend MULTI_AGENT_ASSET_ANALYSIS.py")
    ap.add_argument(
        "--edge-dry-run",
        action="store_true",
        help="Edge-Assembly ohne Ollama/Note10-HTTP-Probes",
    )
    args = ap.parse_args()

    try:
        from workspace_env import load_workspace_dotenv

        load_workspace_dotenv(override=False)
    except ImportError:
        pass

    print("[ORION_GO] DDGK_FULL_EXECUTOR_FINAL: Struktur + Agent-Pool ...", flush=True)
    import DDGK_FULL_EXECUTOR_FINAL as ex

    ex.DDGKExecutor()
    print("[ORION_GO] Executor-Struktur OK.", flush=True)

    try:
        from workspace_credentials import print_credentials_overview

        print_credentials_overview(compact=True)
    except Exception as e:
        print(f"[ORION_GO] Credentials-Übersicht: {e}", flush=True)

    if not args.no_edge:
        cmd = [sys.executable, str(ROOT / "DDGK_EDGE_CLUSTER_ASSEMBLY.py")]
        if args.edge_dry_run:
            cmd.append("--dry-run")
        print("[ORION_GO] Edge-Cluster-Assembly ...", flush=True)
        r = subprocess.run(cmd, cwd=str(ROOT))
        if r.returncode != 0:
            return r.returncode

    if args.multi_agent:
        print("[ORION_GO] MULTI_AGENT_ASSET_ANALYSIS ...", flush=True)
        r2 = subprocess.run(
            [sys.executable, str(ROOT / "MULTI_AGENT_ASSET_ANALYSIS.py"), "--skip-seed-sync"],
            cwd=str(ROOT),
        )
        return r2.returncode

    print("[ORION_GO] Fertig.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
