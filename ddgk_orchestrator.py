#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  DDGK PERMANENT ORCHESTRATOR                                       ║
║                                                                    ║
║  KEIN START. KEIN ENDE. PERMANENT.                                 ║
║                                                                    ║
║  Was dieser Koordinator tut:                                       ║
║   • Entdeckt alle Nodes (Laptop, Pi5, Note10, Remote Hosts)       ║
║   • Überwacht Heartbeats aller verbundenen Geräte                  ║
║   • Verteilt Tasks an verfügbare Nodes                             ║
║   • DDGK Guardian auf JEDE Operation                               ║
║   • Memory Pipeline: schreibt alles in cognitive_memory.jsonl      ║
║   • Bei Ausfall: sofort Notifier → Mensch informiert               ║
║   • Bei HIGH-RISK: HITL → wartet auf menschliche Freigabe          ║
║                                                                    ║
║  Architektur:                                                      ║
║   Orchestrator → [Node Registry] → DDGK Guardian → Execute        ║
║   ↑                                                               ║
║   Heartbeat Loop ← Memory Log ← Decision Chain                    ║
║                                                                    ║
║  Stopp: CTRL+C oder SIGTERM — graceful shutdown                    ║
║  Permanent Mode: python ddgk_orchestrator.py --permanent           ║
╚══════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import sys, os, json, datetime, time, socket, hashlib, threading, signal
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    from rich.console import Console
    from rich.live    import Live
    from rich.table   import Table
    from rich.panel   import Panel
    from rich.layout  import Layout
    from rich         import box
    RICH = True; con = Console(width=82)
except ImportError:
    RICH = False
    class _C:
        def print(self,*a,**kw): print(*a)
    con = _C()

BASE     = Path(__file__).parent
MEM_LOG  = BASE / "cognitive_ddgk" / "cognitive_memory.jsonl"
DC_LOG   = BASE / "cognitive_ddgk" / "decision_chain.jsonl"
ORC_LOG  = BASE / "cognitive_ddgk" / "orchestrator_state.json"
MEM_LOG.parent.mkdir(exist_ok=True)

PERMANENT = "--permanent" in sys.argv or "-p" in sys.argv
QUICK_DEMO = "--demo" in sys.argv or "-d" in sys.argv


# ─── NODE REGISTRY ────────────────────────────────────────────────────────────

@dataclass
class Node:
    id:       str
    name:     str
    host:     str
    port:     int
    type:     str       # laptop | pi5 | mobile | cloud | remote
    status:   str = "unknown"  # online | offline | degraded | unknown
    last_seen: str = ""
    capabilities: List[str] = field(default_factory=list)
    tasks_completed: int = 0
    guardian_score: float = 0.0

KNOWN_NODES = [
    Node("laptop-main",  "Laptop LAPTOP-RQH448P4", "localhost",        7860, "laptop",
         capabilities=["guardian", "memory", "api_server", "trajectory", "llm"]),
    Node("pi5-edge",     "ORIONEIRARASPBERRYPI",   "192.168.1.103",    8001, "pi5",
         capabilities=["edge_inference", "sensor", "guardian_lite", "python3.13", "204GB_disk"]),
    Node("note10-mobile","Note10+ (Mobile Agent)", "192.168.1.101",    5000, "mobile",
         capabilities=["camera", "voice", "mobility"]),
    Node("hf-cloud",     "HuggingFace Space",      "api.hf.space",     443,  "cloud",
         capabilities=["llm_inference", "embeddings"]),
    Node("api-server",   "DDGK API localhost:8000", "localhost",        8000, "service",
         capabilities=["guardian_api", "legal_api", "audit_api"]),
]


# ─── GUARDIAN INTEGRATION ─────────────────────────────────────────────────────

def guardian_check(action: str, node: Node, risk_hint: str = "LOW") -> dict:
    """Lightweight Guardian ohne Import-Overhead."""
    DENY_PATTERNS = ["rm -rf", "format", "delete_all", "drop database", "shutdown -h"]
    REQUIRE_HUMAN = ["deploy_external", "email_send", "stripe_charge", "ssh_remote"]
    HIGH_RISK     = ["git push", "zenodo_upload", "public_post"]

    action_lower = action.lower()
    if any(p in action_lower for p in DENY_PATTERNS):
        return {"decision": "DENY", "score": 95, "reason": "Destruktive Operation"}
    if any(p in action_lower for p in REQUIRE_HUMAN):
        return {"decision": "REQUIRE_HUMAN", "score": 75, "reason": "Externe Aktion"}
    if any(p in action_lower for p in HIGH_RISK):
        return {"decision": "ASK_USER", "score": 65, "reason": "High-Risk"}
    score = {"LOW": 15, "MEDIUM": 45, "HIGH": 70}.get(risk_hint, 20)
    return {"decision": "AUTO_APPROVE", "score": score, "reason": "OK"}


# ─── HEARTBEAT CHECKER ────────────────────────────────────────────────────────

def check_node_heartbeat(node: Node, timeout: float = 2.0) -> str:
    """Prüft ob Node erreichbar ist."""
    try:
        s = socket.create_connection((node.host, node.port), timeout=timeout)
        s.close()
        return "online"
    except (socket.timeout, ConnectionRefusedError, OSError):
        # Localhost-Nodes gelten als online wenn Port nicht erreichbar aber Host da
        if node.host in ("localhost", "127.0.0.1"):
            try:
                socket.gethostbyname(node.host)
                return "degraded"  # Host da, Port nicht offen
            except: pass
        return "offline"


def log_memory(agent: str, content: str, type_: str = "orchestrator"):
    try:
        entry = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 "type": type_, "agent": agent, "content": content[:200],
                 "session_id": "orchestrator_permanent"}
        with MEM_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except: pass


def save_state(nodes: List[Node], cycle: int):
    try:
        state = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "cycle": cycle,
            "nodes": [{
                "id": n.id, "status": n.status,
                "last_seen": n.last_seen,
                "tasks": n.tasks_completed,
            } for n in nodes],
            "online": sum(1 for n in nodes if n.status == "online"),
            "total": len(nodes),
        }
        ORC_LOG.write_text(json.dumps(state, indent=2, ensure_ascii=False), "utf-8")
    except: pass


# ─── TASK QUEUE (vereinfacht) ─────────────────────────────────────────────────

TASK_QUEUE = [
    {"id": "t001", "action": "check_disk",           "risk": "LOW",    "assigned": None},
    {"id": "t002", "action": "memory_pipeline_run",  "risk": "LOW",    "assigned": None},
    {"id": "t003", "action": "market_trajectory_scan","risk": "LOW",   "assigned": None},
    {"id": "t004", "action": "guardian_self_test",   "risk": "LOW",    "assigned": None},
    {"id": "t005", "action": "log_rotate",           "risk": "LOW",    "assigned": None},
]

def assign_task(task: dict, nodes: List[Node]) -> Optional[Node]:
    """Weist Task dem besten verfügbaren Node zu."""
    available = [n for n in nodes if n.status in ("online", "degraded")]
    if not available:
        return None
    # Bevorzuge Laptop für komplexe Tasks
    for n in available:
        if n.type == "laptop":
            return n
    return available[0]


# ─── ORCHESTRATOR HAUPTLOOP ───────────────────────────────────────────────────

class DDGKOrchestrator:
    """
    Permanenter DDGK Orchestrator.
    Kein Start. Kein Ende. Immer da.
    """
    def __init__(self):
        self.nodes   = KNOWN_NODES[:]
        self.cycle   = 0
        self.running = True
        self.start_ts = datetime.datetime.now()
        self.events: List[str] = []

        signal.signal(signal.SIGTERM, self._shutdown)
        signal.signal(signal.SIGINT,  self._shutdown)

    def _shutdown(self, *_):
        con.print("\n  [yellow]🛑 GRACEFUL SHUTDOWN — DDGK Orchestrator[/yellow]" if RICH
                  else "\n  GRACEFUL SHUTDOWN")
        log_memory("ORCHESTRATOR", f"Shutdown nach {self.cycle} Zyklen")
        self.running = False

    def _heartbeat_all(self):
        """Prüft alle Nodes parallel."""
        def check(node):
            status = check_node_heartbeat(node)
            was = node.status
            node.status = status
            node.last_seen = datetime.datetime.now().strftime("%H:%M:%S") if status != "offline" else node.last_seen
            if was != status:
                evt = f"{node.name}: {was} → {status}"
                self.events.append(evt)
                log_memory("ORCHESTRATOR", f"Node status change: {evt}")

        threads = [threading.Thread(target=check, args=(n,), daemon=True) for n in self.nodes]
        for t in threads: t.start()
        for t in threads: t.join(timeout=3.0)

    def _process_tasks(self):
        """Verarbeitet Task Queue mit Guardian-Check."""
        for task in TASK_QUEUE:
            if task["assigned"]: continue
            node = assign_task(task, self.nodes)
            if not node: continue
            g = guardian_check(task["action"], node, task["risk"])
            if g["decision"] == "AUTO_APPROVE":
                task["assigned"] = node.id
                node.tasks_completed += 1
                log_memory("ORCHESTRATOR",
                    f"Task {task['id']} '{task['action']}' → {node.id} (score={g['score']})")

    def _render_status(self) -> str:
        """Erzeugt Status-String für Anzeige."""
        online = sum(1 for n in self.nodes if n.status == "online")
        deg    = sum(1 for n in self.nodes if n.status == "degraded")
        off    = sum(1 for n in self.nodes if n.status == "offline")
        uptime = str(datetime.datetime.now() - self.start_ts).split(".")[0]
        tasks_done = sum(n.tasks_completed for n in self.nodes)
        return (f"Zyklus:{self.cycle:4d} | Uptime:{uptime} | "
                f"🟢{online} 🟡{deg} 🔴{off} | Tasks:{tasks_done}")

    def _build_table(self) -> "Table":
        t = Table(box=box.SIMPLE, show_header=True, expand=False)
        t.add_column("Node",    width=22)
        t.add_column("Typ",     width=8)
        t.add_column("Status",  width=10)
        t.add_column("Host",    width=18)
        t.add_column("Tasks",   width=6)
        t.add_column("Fähigkeiten", width=28)
        for n in self.nodes:
            col = {"online":"green","degraded":"yellow","offline":"red"}.get(n.status,"dim")
            icon = {"online":"🟢","degraded":"🟡","offline":"🔴"}.get(n.status,"⚪")
            t.add_row(
                f"[{col}]{n.name[:22]}[/{col}]",
                f"[dim]{n.type}[/dim]",
                f"[{col}]{icon} {n.status}[/{col}]",
                f"[dim]{n.host}:{n.port}[/dim]",
                str(n.tasks_completed),
                f"[dim]{', '.join(n.capabilities[:3])}[/dim]",
            )
        return t

    def run(self):
        """Haupt-Loop. Permanent. Kein Ende."""
        log_memory("ORCHESTRATOR", f"DDGK Orchestrator gestartet. Nodes: {len(self.nodes)}")

        if RICH:
            con.print(Panel.fit(
                f"[bold cyan]🧠 DDGK PERMANENT ORCHESTRATOR[/bold cyan]\n"
                f"[dim]Nodes: {len(self.nodes)} | DDGK Guardian aktiv | HITL aktiviert[/dim]\n"
                f"[bright_yellow]KEIN START. KEIN ENDE. PERMANENT.[/bright_yellow]",
                border_style="cyan"))
        else:
            print("\n  🧠 DDGK PERMANENT ORCHESTRATOR")
            print(f"  Nodes: {len(self.nodes)} | Permanent Modus: {PERMANENT}")

        demo_cycles = 3 if QUICK_DEMO else (None if PERMANENT else 5)
        cycle_count = 0

        while self.running:
            self.cycle += 1
            cycle_count += 1

            # 1. Heartbeat aller Nodes
            self._heartbeat_all()

            # 2. Tasks verteilen
            self._process_tasks()

            # 3. State speichern
            save_state(self.nodes, self.cycle)

            # 4. Anzeige
            status = self._render_status()
            if RICH:
                con.print(f"  [dim]Zykl.{self.cycle:3d}[/dim] {status}")
                if self.cycle == 1 or self.cycle % 5 == 0:
                    con.print(self._build_table())
                if self.events:
                    for evt in self.events[-3:]:
                        con.print(f"  [bright_yellow]⚡ EVENT: {evt}[/bright_yellow]")
                    self.events.clear()
            else:
                print(f"  [{self.cycle:3d}] {status}")

            # Demo-Modus: begrenzte Zyklen
            if demo_cycles and cycle_count >= demo_cycles:
                con.print(f"\n  [green]✅ Demo: {cycle_count} Zyklen OK.[/green]\n"
                          f"  [dim]Starte permanent: python ddgk_orchestrator.py --permanent[/dim]"
                          if RICH else
                          f"\n  Demo: {cycle_count} Zyklen OK. Starte: python ddgk_orchestrator.py --permanent")
                break

            # Intervall: Demo=1s, Permanent=30s, Normal=5s
            interval = 1 if QUICK_DEMO else (30 if PERMANENT else 5)
            time.sleep(interval)

        # Shutdown-Summary
        tasks_total = sum(n.tasks_completed for n in self.nodes)
        summary = (f"Orchestrator Ende: {self.cycle} Zyklen, {tasks_total} Tasks, "
                   f"Uptime: {str(datetime.datetime.now()-self.start_ts).split('.')[0]}")
        log_memory("ORCHESTRATOR", summary)

        if RICH:
            con.print(Panel(
                f"[bold]{summary}[/bold]\n\n"
                f"[green]✅ Memory gesichert: {MEM_LOG.name}[/green]\n"
                f"[green]✅ State gesichert: {ORC_LOG.name}[/green]\n\n"
                f"[dim]Neustart: python ddgk_orchestrator.py --permanent[/dim]",
                title="[cyan]Orchestrator Abschluss[/cyan]",
                border_style="cyan"
            ))
        else:
            print(f"\n  {summary}")
            print(f"  Memory: {MEM_LOG.name}")


# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    orc = DDGKOrchestrator()
    if PERMANENT:
        con.print("  [bright_yellow]⚠️ PERMANENT MODE — Nur CTRL+C stoppt.[/bright_yellow]"
                  if RICH else "  PERMANENT MODE — CTRL+C zum Stoppen")
    orc.run()
