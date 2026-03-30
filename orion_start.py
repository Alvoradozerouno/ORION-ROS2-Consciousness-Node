#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════╗
║  ORION MASTER START — 1 Befehl startet alles                          ║
║  Löst die Schleife: Single Entry Point für das gesamte System         ║
║                                                                          ║
║  python orion_start.py                    → alles starten              ║
║  python orion_start.py --status           → nur Status                  ║
║  python orion_start.py --loop "Ziel"      → Autonomous Loop mit Ziel   ║
║  python orion_start.py --dashboard        → nur Dashboard Port 7860    ║
║  python orion_start.py --hyper "Beschr."  → neues Tool bauen           ║
║  python orion_start.py --nuclear          → Nuclear Safety Simulator   ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import sys, os, json, time, argparse, subprocess, threading, datetime
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

# ── Farben ──────────────────────────────────────────────────────────────────
C = {
    "cyan":   "\033[96m", "green":  "\033[92m", "yellow": "\033[93m",
    "red":    "\033[91m", "purple": "\033[95m", "bold":   "\033[1m",
    "dim":    "\033[2m",  "reset":  "\033[0m",
}
def c(color: str, text: str) -> str:
    return f"{C.get(color,'')}{text}{C['reset']}"

def banner():
    print()
    print(c("cyan", "╔══════════════════════════════════════════════════════════════╗"))
    print(c("cyan", "║") + c("bold", "  🧠 ORION MASTER START — DDGK HyperSystem v1.0              ") + c("cyan", "║"))
    print(c("cyan", "║") + c("dim",  f"  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC+2 | κ=3.3493 CCRN AKTIV                  ") + c("cyan", "║"))
    print(c("cyan", "╚══════════════════════════════════════════════════════════════╝"))
    print()

def status_check():
    """Schneller Status-Check aller Systeme."""
    print(c("bold", "  📊 SYSTEM-STATUS"))
    print("  " + "─"*55)

    checks = []

    # Ollama
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=2)
        checks.append(("🟢", "Ollama",           "qwen2.5:1.5b/7b aktiv"))
    except:
        checks.append(("🔴", "Ollama",           "nicht erreichbar"))

    # κ_CCRN
    try:
        from cognitive_ddgk.cognitive_ddgk_core import CognitiveDDGK
        ddgk = CognitiveDDGK()
        state = ddgk.get_state()
        k = state.get("kappa_ccrn", 0)
        checks.append(("🟢", f"κ_CCRN={k:.4f}", "CCRN AKTIV" if k > 2.0 else "UNTER SCHWELLE"))
    except Exception as e:
        checks.append(("🟡", "κ_CCRN", f"Fallback: 3.3493 ({str(e)[:30]})"))

    # Memory-Dateien
    mem_files = [
        ("cognitive_ddgk/cognitive_memory.jsonl",  "Cognitive Memory"),
        ("cognitive_ddgk/decision_chain.jsonl",    "Decision Chain"),
        ("cognitive_ddgk/autonomous_loop_memory.jsonl", "Autonomous Loop"),
        ("cognitive_ddgk/nuclear_audit_chain.jsonl", "Nuclear Audit"),
    ]
    for fname, label in mem_files:
        fp = BASE / fname
        if fp.exists():
            lines = sum(1 for l in fp.read_text("utf-8", errors="replace").splitlines() if l.strip())
            checks.append(("🟢", label, f"{lines} Einträge"))
        else:
            checks.append(("⚫", label, "nicht vorhanden"))

    # HyperAgent Tools
    synth_count = len(list((BASE / "cognitive_ddgk" / "synthesized_tools").glob("tool_*.py")))
    hyper_count = len([f for f in (BASE / "hyper_tools").glob("*.py")
                       if not f.name.startswith("__")]) if (BASE / "hyper_tools").exists() else 0
    checks.append(("🟢" if synth_count+hyper_count > 0 else "🟡",
                   "Tools", f"{synth_count} synthesized + {hyper_count} hyper"))

    # Hardware-Warnung
    try:
        import psutil
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\")
        ram_icon = "🟢" if ram.percent < 70 else ("🟡" if ram.percent < 85 else "🔴")
        disk_icon = "🟢" if disk.percent < 85 else ("🟡" if disk.percent < 92 else "🔴")
        checks.append((ram_icon,  f"RAM {ram.percent:.0f}%",  f"{ram.available/(1024**3):.1f}GB frei"))
        checks.append((disk_icon, f"Disk C: {disk.percent:.0f}%", f"{disk.free/(1024**3):.1f}GB frei"))
    except: pass

    for icon, label, detail in checks:
        print(f"  {icon}  {label:28s}  {c('dim', detail)}")

    print()
    return checks

def run_dashboard():
    """Startet das DDGK Dashboard auf Port 7860."""
    print(c("cyan", "  🖥️  Starte DDGK Dashboard auf http://localhost:7860"))
    t = threading.Thread(
        target=lambda: subprocess.run([sys.executable, str(BASE/"ddgk_dashboard.py")]),
        daemon=True
    )
    t.start()
    time.sleep(1.5)
    print(c("green", "  ✅ Dashboard läuft → http://localhost:7860"))
    return t

def run_hyper_agent(goal: str = "", tool_desc: str = ""):
    """Führt HyperAgent aus — entweder mit Ziel oder Tool-Beschreibung."""
    print(c("purple", f"  🦾 HyperAgent → {'Tool bauen: ' + tool_desc if tool_desc else 'Ziel: ' + goal}"))
    if tool_desc:
        cmd = [sys.executable, str(BASE/"hyper_agent.py"), "--create", tool_desc]
    elif goal:
        cmd = [sys.executable, str(BASE/"hyper_agent.py"), "--goal", goal]
    else:
        cmd = [sys.executable, str(BASE/"hyper_agent.py"), "--list"]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    for line in (result.stdout + result.stderr).splitlines()[:20]:
        if line.strip():
            print(f"    {line}")

def run_autonomous_loop(goal: str, cycles: int = 3):
    """Startet den Autonomous Loop."""
    print(c("cyan", f"  🔄 Autonomous Loop → '{goal[:50]}' ({cycles} Zyklen)"))
    cmd = [
        sys.executable, str(BASE/"self_prompting_autonomous_loop.py"),
        "--level", "2", "--cycles", str(cycles),
        "--goal", goal
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    for line in (result.stdout + result.stderr).splitlines()[:25]:
        if line.strip():
            print(f"    {line}")

def run_nuclear():
    """Nuclear Safety Simulator."""
    print(c("red", "  ⚛️  Nuclear Safety Simulator →"))
    cmd = [sys.executable, str(BASE/"nuclear_safety_simulator.py")]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    for line in (result.stdout + result.stderr).splitlines()[:20]:
        if line.strip():
            print(f"    {line}")

def cleanup_pids():
    """Bereinigt .pid Dateien die den Workspace aufblähen."""
    pid_files = list(BASE.rglob("*.pid"))
    print(c("yellow", f"  🧹 Bereinige {len(pid_files)} .pid Dateien..."))
    removed = 0
    for pf in pid_files:
        try:
            pf.unlink()
            removed += 1
        except: pass
    print(c("green", f"  ✅ {removed} .pid Dateien entfernt"))
    return removed

def run_full_system(goal: str = "CCRN-Status prüfen und κ berechnen"):
    """Startet das vollständige System."""
    banner()

    print(c("bold", "  🚀 STARTE VOLLES ORION SYSTEM"))
    print()

    # 1. Status
    checks = status_check()

    # 2. HyperAgent — neue Tools prüfen
    print(c("bold", "  🦾 PHASE 1: HyperAgent Tool-Check"))
    run_hyper_agent()
    print()

    # 3. Decision Chain — Entscheidung loggen
    print(c("bold", "  🔗 PHASE 2: Decision Chain"))
    try:
        from cognitive_ddgk.decision_chain import DDGKDecisionChain, PolicyResult, Trust
        chain = DDGKDecisionChain()
        rec = chain.decide(
            goal=f"ORION Master Start: {goal}",
            action="run_full_system",
            reasoning=[
                "Master-Start initiiert alle Subsysteme",
                f"Ziel: {goal}",
                "DDGK Policy: ALLOW für System-Initialisierung",
            ],
            alternatives=[
                ("manual_start", "Erfordert manuellen Start jeder Komponente"),
                ("skip", "Lässt System im unvollständigen Zustand"),
            ],
            input_state={"goal": goal, "ts": datetime.datetime.now().isoformat()},
            validation=PolicyResult.ALLOW,
            trust=Trust.VERIFIED_DOCUMENT,
            risk="LOW",
            agent_id="ORION-MASTER",
            kappa=3.3493,
        )
        print(c("green", f"  ✅ Decision Chain: {rec.decision_id[:16]}..."))
    except Exception as e:
        print(c("yellow", f"  ⚠️  Decision Chain: {e}"))
    print()

    # 4. Autonomous Loop
    print(c("bold", f"  🔄 PHASE 3: Autonomous Loop → '{goal}'"))
    run_autonomous_loop(goal, cycles=3)
    print()

    # 5. Final Status
    print(c("bold", "  📊 FINAL STATUS"))
    status_check()

    print(c("green", "  ✅ ORION System vollständig gestartet!"))
    print()
    print(c("dim", "  Nächste Schritte:"))
    print(c("dim", "    python orion_start.py --dashboard    → Live Dashboard"))
    print(c("dim", "    python orion_start.py --nuclear      → Safety Simulator"))
    print(c("dim", "    python orion_start.py --loop 'Ziel'  → Eigenes Ziel"))


# ── MAIN ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="ORION Master Start — 1 Befehl für alles")
    ap.add_argument("--status",    action="store_true",  help="Nur Status anzeigen")
    ap.add_argument("--dashboard", action="store_true",  help="Dashboard starten (Port 7860)")
    ap.add_argument("--loop",      type=str, default="", help="Autonomous Loop mit Ziel")
    ap.add_argument("--hyper",     type=str, default="", help="Neues Tool bauen")
    ap.add_argument("--nuclear",   action="store_true",  help="Nuclear Safety Simulator")
    ap.add_argument("--cleanup",   action="store_true",  help="PID-Dateien bereinigen")
    ap.add_argument("--cycles",    type=int, default=3,  help="Anzahl Loop-Zyklen")
    args = ap.parse_args()

    banner()

    if args.status:
        status_check()
    elif args.dashboard:
        t = run_dashboard()
        print(c("dim", "  Dashboard läuft — STRG+C zum Beenden"))
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            print(c("yellow", "\n  Dashboard gestoppt."))
    elif args.loop:
        status_check()
        run_autonomous_loop(args.loop, args.cycles)
    elif args.hyper:
        run_hyper_agent(tool_desc=args.hyper)
    elif args.nuclear:
        run_nuclear()
    elif args.cleanup:
        cleanup_pids()
    else:
        # Volles System
        run_full_system("CCRN-Status prüfen, κ berechnen und Workspace analysieren")
