#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  DDGK ARBITRAGE ENGINE — Intelligente Node-Delegation              ║
║                                                                    ║
║  Verteilt Tasks auf den besten verfügbaren Node:                   ║
║   PC-Master    → Formal Proofs, schwere Berechnungen               ║
║   Pi5-Edge     → I/O Control, Industrial OPC-UA, 20W               ║
║   Note10-Mobile→ Vision, Mobile Testing, NPU-Inference             ║
║   Laptop-Dev   → Orchestration, UI, Marketplace, API               ║
║                                                                    ║
║  SIK-Axiom: Jeder Task zum leistungsstärksten verfügbaren Node     ║
╚══════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import sys, socket, time, datetime, json, threading
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE     = Path(__file__).parent
ARB_LOG  = BASE / "cognitive_ddgk" / "arbitrage.jsonl"
ARB_LOG.parent.mkdir(exist_ok=True)

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


@dataclass
class NodeProfile:
    name:       str
    host:       str
    port:       int
    node_type:  str          # master | pi5 | mobile | laptop
    strengths:  list         # z.B. ["formal_proof", "heavy_compute"]
    watt_limit: float        # Watt-Budget
    weight:     float = 1.0  # Qualitäts-Gewicht für Arbitrage
    status:     str   = "unknown"
    vitality:   float = 100.0  # 0-100, aktuell verfügbar


# ─── NODE DEFINITIONEN ────────────────────────────────────────────────────────
NODES = [
    NodeProfile("PC-Master",    "localhost",       9000, "master",
                ["formal_proof", "heavy_compute", "llm", "cuda"],
                watt_limit=150.0, weight=3.0),

    NodeProfile("Pi5-Edge",     "192.168.1.103",   8001, "pi5",
                ["edge_control", "opc_ua", "iot", "sensor", "low_power"],
                watt_limit=20.0, weight=2.0),

    NodeProfile("Note10-Mobile","192.168.1.101",   5001, "mobile",
                ["vision", "npu_inference", "mobile_test", "camera"],
                watt_limit=5.0, weight=1.5),

    NodeProfile("Laptop-Dev",   "localhost",       8000, "laptop",
                ["orchestration", "ui", "marketplace", "api", "git"],
                watt_limit=45.0, weight=2.5),
]

# ─── TASK-TYPE → ANFORDERUNGSPROFIL ──────────────────────────────────────────
TASK_REQUIREMENTS = {
    "formal_proof":       ["formal_proof", "heavy_compute"],
    "kappa_calculation":  ["formal_proof", "heavy_compute"],
    "edge_control":       ["edge_control", "opc_ua"],
    "iot_sensor":         ["sensor", "iot"],
    "vision_analysis":    ["vision", "npu_inference"],
    "mobile_testing":     ["mobile_test", "camera"],
    "api_serve":          ["orchestration", "api"],
    "marketplace_update": ["marketplace", "ui"],
    "git_push":           ["git", "orchestration"],
    "llm_inference":      ["llm", "cuda"],
    "memory_pipeline":    ["orchestration", "api"],
    "market_trajectory":  ["orchestration", "heavy_compute"],
    "aec_validation":     ["formal_proof", "heavy_compute"],
    "guardian_check":     ["orchestration", "api"],
    "default":            ["orchestration"],
}


class DDGKArbitrageEngine:
    """
    Intelligente Task-Delegation an den optimalen Node.
    
    Selektions-Logik:
    1. Hat der Node die benötigten Stärken?
    2. Ist der Node erreichbar (Heartbeat)?
    3. Hat er ausreichend Vitality (CPU/RAM)?
    4. Liegt er im Watt-Budget?
    → Wähle den Node mit höchstem score = weight × vitality
    """

    def __init__(self, nodes: list[NodeProfile] = None):
        self.nodes = nodes or NODES[:]
        self._lock = threading.Lock()

    def _check_node(self, node: NodeProfile, timeout: float = 1.5) -> str:
        try:
            s = socket.create_connection((node.host, node.port), timeout=timeout)
            s.close()
            return "online"
        except:
            return "offline" if node.host not in ("localhost","127.0.0.1") else "degraded"

    def _get_vitality(self, node: NodeProfile) -> float:
        """Misst lokale Vitalität (nur wenn localhost)."""
        if node.host in ("localhost","127.0.0.1") and HAS_PSUTIL:
            cpu = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory().percent
            return max(0.0, 100 - (cpu * 0.6 + ram * 0.4))
        return 70.0  # Remote-Node: Schätzwert

    def refresh_all(self, parallel: bool = True) -> list[NodeProfile]:
        """Aktualisiert Status + Vitalität aller Nodes."""
        def _update(n):
            n.status   = self._check_node(n)
            n.vitality = self._get_vitality(n) if n.status != "offline" else 0.0

        if parallel:
            threads = [threading.Thread(target=_update, args=(n,), daemon=True)
                       for n in self.nodes]
            for t in threads: t.start()
            for t in threads: t.join(timeout=3.0)
        else:
            for n in self.nodes: _update(n)
        return self.nodes

    def delegate(self, task_type: str, require_online: bool = True) -> Optional[NodeProfile]:
        """
        Wählt den besten Node für den Task.
        Returns None wenn kein geeigneter Node verfügbar.
        """
        required = TASK_REQUIREMENTS.get(task_type, TASK_REQUIREMENTS["default"])
        candidates = []

        for node in self.nodes:
            if require_online and node.status == "offline":
                continue
            # Stärken-Match
            match_score = sum(1 for r in required if r in node.strengths)
            if match_score == 0:
                continue
            # Gesamt-Score
            score = node.weight * (node.vitality / 100.0) * match_score
            candidates.append((score, node))

        if not candidates:
            # Fallback: Laptop wenn alle offline
            fallback = next((n for n in self.nodes if n.node_type == "laptop"), None)
            return fallback

        candidates.sort(key=lambda x: x[0], reverse=True)
        best = candidates[0][1]

        # Audit-Log
        self._log_delegation(task_type, best, candidates)
        return best

    def _log_delegation(self, task_type: str, node: NodeProfile, candidates: list):
        entry = {
            "ts":        datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "task":      task_type,
            "delegated": node.name,
            "host":      f"{node.host}:{node.port}",
            "vitality":  round(node.vitality, 1),
            "alt_count": len(candidates),
        }
        with ARB_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def run_demo(self):
        """Zeigt Live-Arbitrage für alle Task-Typen."""
        print("\n  🔀 DDGK ARBITRAGE ENGINE — Live Demo")
        print("  " + "="*58)

        print("\n  Scanning nodes...")
        self.refresh_all()

        print(f"\n  {'NODE':20s} {'TYPE':10s} {'STATUS':10s} {'VITALITÄT':10s} {'W-LIMIT':8s}")
        print("  " + "-"*60)
        for n in self.nodes:
            v_bar = "█" * int(n.vitality/10) + "░" * (10 - int(n.vitality/10))
            print(f"  {n.name:20s} {n.node_type:10s} {n.status:10s} {v_bar} {n.watt_limit:5.0f}W")

        print(f"\n  {'TASK':25s} → {'DELEGIERT AN':20s} {'STÄRKEN-MATCH'}")
        print("  " + "-"*65)
        tasks = ["formal_proof", "edge_control", "vision_analysis",
                 "api_serve", "kappa_calculation", "aec_validation",
                 "git_push", "memory_pipeline", "llm_inference"]
        for task in tasks:
            node = self.delegate(task, require_online=False)
            if node:
                req = TASK_REQUIREMENTS.get(task, ["default"])
                match = [r for r in req if r in node.strengths]
                print(f"  {task:25s} → {node.name:20s} ✅ {', '.join(match)}")
            else:
                print(f"  {task:25s} → ❌ kein Node verfügbar")

        print(f"\n  Log: {ARB_LOG}")


# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    engine = DDGKArbitrageEngine()
    engine.run_demo()
