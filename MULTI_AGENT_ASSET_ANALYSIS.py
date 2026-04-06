#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MULTI-AGENT ASSET ANALYSIS SYSTEM v1.0
======================================
Legitimate analysis of OrionKernel assets
Ensures system integrity & forward-compatible improvements only
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_WS_ROOT = Path(__file__).resolve().parent

# .env aus Repo-Root (ORION_SEED_SOURCE, Tokens, …) vor allen weiteren Imports
try:
    from workspace_env import load_workspace_dotenv

    _DOTENV_PKG_OK = load_workspace_dotenv(override=False)
except ImportError:
    _DOTENV_PKG_OK = False


class AssetAnalysisAgent:
    """AGENT: Asset Inventory & Structure Analysis"""
    
    def __init__(self):
        self.agent_id = "AGENT-1-ASSET-ANALYZER"
        self.results = {}
        
    def scan_assets(self) -> Dict:
        """Catalog all available assets"""
        assets = {
            "downloads": {
                "OrionKernel.zip": r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\OrionKernel.zip",
                "GENESIS10000_Full_Export_Suite.zip": r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\GENESIS10000_Full_Export_Suite.zip",
            },
            "usb_e_drive": {
                "attached_assets.zip": r"E:\attached_assets.zip",
                "ORION_SEED_COMPLETE": r"E:\ORION_SEED_COMPLETE",
                "genesis_extracted": r"E:\genesis_extracted",
            },
            "workspace_external": {
                "ORION_SEED_COMPLETE": str(_WS_ROOT / "external" / "ORION_SEED_COMPLETE"),
            },
        }
        
        catalog = {}
        for source, paths in assets.items():
            catalog[source] = {}
            for name, path in paths.items():
                if Path(path).exists():
                    item = Path(path)
                    catalog[source][name] = {
                        "path": str(path),
                        "exists": True,
                        "size_mb": round(item.stat().st_size / (1024*1024), 2),
                        "modified": item.stat().st_mtime,
                        "is_dir": item.is_dir(),
                        "is_file": item.is_file(),
                    }
                else:
                    catalog[source][name] = {
                        "path": str(path),
                        "exists": False,
                        "status": "NOT_FOUND"
                    }
        
        return {
            "agent": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "asset_catalog": catalog
        }

class IntegrityCheckAgent:
    """AGENT: Verify asset integrity & safety"""
    
    def __init__(self):
        self.agent_id = "AGENT-3-INTEGRITY-CHECK"
        
    def analyze_integrity(self) -> Dict:
        """Check that assets are safe to integrate"""
        return {
            "agent": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "malware_scan": "REQUIRES_MANUAL_REVIEW",
                "dependency_conflicts": "ANALYSIS_PENDING",
                "version_compatibility": "ANALYSIS_PENDING",
                "security_implications": "ANALYSIS_PENDING",
            },
            "recommendation": "Do not integrate unknown assets without manual review",
            "human_oversight": "REQUIRED"
        }

class SystemImpactAgent:
    """AGENT: Assess impact on current system"""
    
    def __init__(self):
        self.agent_id = "AGENT-2-SYSTEM-IMPACT"
        
    def assess_impact(self) -> Dict:
        """Evaluate how assets affect existing system"""
        return {
            "agent": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "current_system": {
                "core_agents": 10,
                "frameworks": ["DDGK", "Legal Agent", "Market Trajectory"],
                "status": "STABLE"
            },
            "asset_impact": {
                "potential_benefits": [
                    "Additional data models (GENESIS10000)",
                    "Extended asset library (attached_assets)",
                    "Seed data for training (ORION_SEED)"
                ],
                "risks": [
                    "Unknown compatibility",
                    "Potential version conflicts",
                    "Unreviewed code integration"
                ]
            },
            "recommendation": "STAGED INTEGRATION with testing at each phase"
        }

class RecommendationAgent:
    """AGENT: Generate improvement recommendations"""
    
    def __init__(self):
        self.agent_id = "AGENT-4-RECOMMENDATIONS"
        
    def generate_recommendations(self) -> Dict:
        """Safe, forward-compatible improvements"""
        return {
            "agent": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "safe_improvements": [
                {
                    "priority": "HIGH",
                    "action": "Extract & catalog GENESIS10000 data models",
                    "benefit": "Expand system capability",
                    "risk": "LOW - read-only analysis",
                    "steps": [
                        "1. Extract GENESIS10000_Full_Export_Suite.zip",
                        "2. Analyze file structure",
                        "3. Identify compatible components",
                        "4. Document integration points"
                    ]
                },
                {
                    "priority": "MEDIUM",
                    "action": "Catalog attached_assets for reusability",
                    "benefit": "Understand available resources",
                    "risk": "LOW - inventory only",
                    "steps": [
                        "1. Extract attached_assets.zip",
                        "2. List all files & types",
                        "3. Cross-reference with current system",
                        "4. Identify useful integrations"
                    ]
                },
                {
                    "priority": "LOW",
                    "action": "Review OrionKernel.zip for improvements",
                    "benefit": "Identify optimization opportunities",
                    "risk": "MEDIUM - requires careful review",
                    "steps": [
                        "1. Extract and analyze",
                        "2. Compare with current version",
                        "3. Test in isolated environment",
                        "4. Only merge safe improvements"
                    ]
                }
            ],
            "boundary_conditions": [
                "✅ Only read-only analysis until human approval",
                "✅ No merging of unknown code",
                "✅ All changes logged & reversible",
                "✅ System must remain stable",
                "❌ No automatic execution",
                "❌ No override of safety systems",
                "❌ No removal of human oversight"
            ]
        }

def _auto_sync_orion_seed() -> None:
    """🟢 Vor jedem Lauf: E:\\ORION_SEED_COMPLETE → external/ (falls Quelle existiert)."""
    try:
        from sync_orion_seed_complete import sync_orion_seed

        r = sync_orion_seed()
        if r.get("error"):
            print(f"🟡 🔌 SEED-SYNC übersprungen: {r['error']}")
        else:
            sym = "✓" if r.get("ok") else "⚠"
            print(
                f"🟢 🏗️ SEED-SYNC {sym}  "
                f"aktualisiert={r.get('copied', 0)}  übersprungen={r.get('skipped', 0)}"
            )
    except Exception as ex:
        print(f"🟡 🔌 SEED-SYNC nicht ausgeführt: {ex}")


def run_workspace_cleanup(dry_run: bool = False) -> dict:
    """🛡️ AGENT 5–8: Cache-Hygiene, Git-Inventar, Klassifikation, .gitignore-Block."""
    from workspace_cleanup_agents import run_cleanup_pipeline

    print("=" * 70)
    print("  MULTI-AGENT WORKSPACE CLEANUP (5–8)")
    print("=" * 70)
    print()
    payload = run_cleanup_pipeline(root=_WS_ROOT, dry_run=dry_run)
    s = payload.get("summary", {})
    sym = "📜" if dry_run else "🛡️"
    print(
        f"  {sym} Hygiene: cache-Ordner entfernt ~{s.get('cache_dirs_removed', 0)} | "
        f".pyc/.pyo Treffer: {s.get('bytecode_hits', 0)}"
    )
    print(f"  🌐 Git: untracked (vor Ignore-Filter): {s.get('untracked_files', 0)}")
    print(f"  📜 .gitignore Block aktualisiert: {'ja' if s.get('gitignore_updated') else 'nein (schon da oder dry-run)'}")
    zen = _WS_ROOT / "ZENODO_UPLOAD" / "WORKSPACE_CLEANUP_REPORT.json"
    zen.parent.mkdir(parents=True, exist_ok=True)
    with open(zen, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Report: {zen}")
    print()
    return payload


def run_analysis(skip_seed_sync: bool = False, workspace_cleanup: bool = False, cleanup_dry_run: bool = False):
    """Execute full multi-agent analysis; optional vorher Workspace-Cleanup."""
    print("="*70)
    print("  MULTI-AGENT ASSET ANALYSIS SYSTEM")
    print("  Safe Integration Framework v1.0")
    print("="*70)
    print()

    if not _DOTENV_PKG_OK:
        print(
            "🟡 ℹ️  python-dotenv fehlt — .env wird nicht auto-geladen "
            "(pip install -r requirements.txt). "
            "ℹ️  master.env.ini-Allowlist (Pfade/Hosts) wird trotzdem versucht."
        )
        print()

    try:
        from workspace_credentials import print_credentials_overview

        print_credentials_overview(compact=True)
    except Exception as ex:
        print(f"🟡 🔐 Credential-Übersicht übersprungen: {ex}")
        print()

    if not skip_seed_sync:
        _auto_sync_orion_seed()
        print()

    if workspace_cleanup:
        run_workspace_cleanup(dry_run=cleanup_dry_run)
        if not skip_seed_sync:
            _auto_sync_orion_seed()
            print()

    # Agent 1: Asset Inventory
    print("[AGENT-1] Asset Inventory Scan...")
    agent1 = AssetAnalysisAgent()
    result1 = agent1.scan_assets()
    found = sum(1 for source in result1['asset_catalog'].values() for item in source.values() if item.get('exists'))
    print(f"  Found assets: {found}")
    print()
    
    # Agent 2: System Impact
    print("[AGENT-2] System Impact Assessment...")
    agent2 = SystemImpactAgent()
    result2 = agent2.assess_impact()
    print(f"  Current system: {result2['current_system']['status']}")
    print(f"  Integration strategy: {result2['recommendation']}")
    print()
    
    # Agent 3: Integrity Check
    print("[AGENT-3] Integrity & Safety Check...")
    agent3 = IntegrityCheckAgent()
    result3 = agent3.analyze_integrity()
    print(f"  Human oversight: {result3['human_oversight']}")
    print()
    
    # Agent 4: Recommendations
    print("[AGENT-4] Recommendations Engine...")
    agent4 = RecommendationAgent()
    result4 = agent4.generate_recommendations()
    print(f"  Safe improvements identified: {len(result4['safe_improvements'])}")
    print()
    
    # Save full report
    found_assets = sum(
        1 for source in result1["asset_catalog"].values() for item in source.values() if item.get("exists")
    )
    full_report = {
        "timestamp": datetime.now().isoformat(),
        "system": "Multi-Agent Asset Analysis",
        "agents": [result1, result2, result3, result4],
        "summary": {
            "total_assets": found_assets,
            "ready_for_analysis": found_assets,
            "human_approval_required": True,
            "system_stability": "PRESERVED",
        },
    }
    
    report_path = Path("cognitive_ddgk/asset_analysis_report.json")
    report_path.parent.mkdir(exist_ok=True, parents=True)
    with open(report_path, 'w') as f:
        json.dump(full_report, f, indent=2)
    
    print("="*70)
    print(f"  Analysis complete. Report saved to: {report_path}")
    print("="*70)
    print()
    print("NEXT STEPS:")
    print("  1. Review recommendations in asset_analysis_report.json")
    print("  2. ZENODO_UPLOAD/WORKSPACE_CLEANUP_REPORT.json bei Cleanup-Lauf prüfen")
    print("  3. Test improvements in isolated environment")
    print("  4. Deploy only after human verification")
    print()

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="Multi-Agent Asset Analysis + optional Workspace-Cleanup (+ auto ORION seed sync)"
    )
    ap.add_argument(
        "--skip-seed-sync",
        action="store_true",
        help="Kein automatischer Sync von ORION_SEED_COMPLETE vor dem Scan",
    )
    ap.add_argument(
        "--workspace-cleanup",
        action="store_true",
        help="Vor Analyse: Multi-Agent Cleanup (Caches, Git-Inventar, .gitignore-Block)",
    )
    ap.add_argument(
        "--cleanup-dry-run",
        action="store_true",
        help="Nur Cleanup-Report simulieren (keine Löschung / kein .gitignore-Schreiben)",
    )
    ap.add_argument(
        "--cleanup-only",
        action="store_true",
        help="Nur Workspace-Cleanup (Agent 5–8), keine Asset-Analyse 1–4",
    )
    args = ap.parse_args()
    if args.cleanup_only:
        if not _DOTENV_PKG_OK:
            print(
                "🟡 ℹ️  python-dotenv fehlt — pip install -r requirements.txt\n"
            )
        try:
            from workspace_credentials import print_credentials_overview

            print_credentials_overview(compact=True)
        except Exception as ex:
            print(f"🟡 🔐 Credential-Übersicht übersprungen: {ex}\n")
        if not args.skip_seed_sync:
            _auto_sync_orion_seed()
            print()
        run_workspace_cleanup(dry_run=args.cleanup_dry_run)
        if not args.skip_seed_sync:
            _auto_sync_orion_seed()
        raise SystemExit(0)
    run_analysis(
        skip_seed_sync=args.skip_seed_sync,
        workspace_cleanup=args.workspace_cleanup,
        cleanup_dry_run=args.cleanup_dry_run,
    )
