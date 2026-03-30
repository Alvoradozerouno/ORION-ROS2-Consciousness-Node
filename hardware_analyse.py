#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════╗
║  HARDWARE + WORKSPACE VOLLANALYSE — DDGK Multi-Agent System    ║
║  ORION-ROS2-Consciousness-Node | 2026-03-30                    ║
╚══════════════════════════════════════════════════════════════════╝
"""
import sys, os, json, datetime, hashlib, platform
from pathlib import Path

BASE = Path(__file__).parent

print()
print("╔══════════════════════════════════════════════════════════════════╗")
print("║  🔴🟡🟢 DDGK VOLLANALYSE — Hardware + Workspace + System       ║")
print(f"║  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC+2                                        ║")
print("╚══════════════════════════════════════════════════════════════════╝")

# ── HARDWARE ──────────────────────────────────────────────────────────────
print()
print("═" * 65)
print("  💻 HARDWARE — LAPTOP-RQH448P4")
print("═" * 65)

try:
    import psutil

    # CPU
    cpu_phys    = psutil.cpu_count(logical=False)
    cpu_logic   = psutil.cpu_count(logical=True)
    cpu_freq    = psutil.cpu_freq()
    cpu_pct     = psutil.cpu_percent(interval=0.5)
    cpu_per     = psutil.cpu_percent(interval=0.3, percpu=True)

    print(f"\n  🔷 CPU")
    print(f"    Prozessor   : {platform.processor()[:55]}")
    print(f"    Kerne       : {cpu_phys} physisch / {cpu_logic} logisch (Hyper-Threading)")
    if cpu_freq:
        pct_bar = "█" * int(cpu_pct/10) + "░" * (10 - int(cpu_pct/10))
        print(f"    Frequenz    : {cpu_freq.current:.0f} MHz  (Max: {cpu_freq.max:.0f} MHz)")
        print(f"    Auslastung  : {cpu_pct:5.1f}%  [{pct_bar}]")
    print(f"    Pro Kern    : {' | '.join(f'C{i}:{p:.0f}%' for i, p in enumerate(cpu_per[:8]))}")

    # RAM
    ram  = psutil.virtual_memory()
    swap = psutil.swap_memory()
    ram_bar  = "█" * int(ram.percent/10)  + "░" * (10 - int(ram.percent/10))
    swap_bar = "█" * int(swap.percent/10) + "░" * (10 - int(swap.percent/10))
    ram_status = "🟢 OK" if ram.percent < 70 else ("🟡 WARN" if ram.percent < 85 else "🔴 KRIT")

    print(f"\n  🔷 ARBEITSSPEICHER (RAM)")
    print(f"    Gesamt      : {ram.total/(1024**3):.2f} GB")
    print(f"    Verfügbar   : {ram.available/(1024**3):.2f} GB")
    print(f"    Belegt      : {ram.used/(1024**3):.2f} GB  ({ram.percent:.1f}%)  [{ram_bar}]  {ram_status}")
    print(f"    Swap        : {swap.used/(1024**3):.2f} / {swap.total/(1024**3):.2f} GB  [{swap_bar}]")

    # Disk
    print(f"\n  🔷 FESTPLATTEN")
    for part in psutil.disk_partitions():
        try:
            u = psutil.disk_usage(part.mountpoint)
            bar = "█" * int(u.percent/10) + "░" * (10 - int(u.percent/10))
            status = "🟢" if u.percent < 80 else ("🟡" if u.percent < 90 else "🔴")
            print(f"    {part.device:20s} {part.fstype:6s}  {u.total/(1024**3):6.1f}GB  belegt:{u.used/(1024**3):6.1f}GB  frei:{u.free/(1024**3):5.1f}GB  {u.percent:5.1f}% [{bar}] {status}")
        except: pass

    # Netzwerk
    print(f"\n  🔷 NETZWERK")
    net_io = psutil.net_io_counters()
    print(f"    Gesendet    : {net_io.bytes_sent/(1024**2):.1f} MB  | Empfangen: {net_io.bytes_recv/(1024**2):.1f} MB")
    for iface, addrs in psutil.net_if_addrs().items():
        stats = psutil.net_if_stats().get(iface)
        for addr in addrs:
            if addr.family.name == 'AF_INET' and not addr.address.startswith('169'):
                up = "🟢 UP" if stats and stats.isup else "🔴 DOWN"
                print(f"    {iface:30s}  {addr.address:16s}  {up}")

    # Prozesse
    proc_count = len(psutil.pids())
    print(f"\n  🔷 PROZESSE")
    print(f"    Aktiv       : {proc_count} Prozesse")

    # Top CPU-Prozesse
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            if p.info['cpu_percent'] and p.info['cpu_percent'] > 0.5:
                procs.append(p.info)
        except: pass
    procs.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
    for p in procs[:5]:
        print(f"    PID {p['pid']:6d}  {p['name']:25s}  CPU:{p['cpu_percent']:5.1f}%  MEM:{p.get('memory_percent',0):.1f}%")

except ImportError:
    print("  ⚠️  psutil nicht verfügbar — vereinfachte Analyse")
    print(f"    OS         : {platform.system()} {platform.release()}")
    print(f"    Processor  : {platform.processor()}")
    print(f"    Machine    : {platform.machine()}")
    print(f"    Python     : {platform.python_version()}")

# ── BETRIEBSSYSTEM ─────────────────────────────────────────────────────────
print()
print("═" * 65)
print("  🖥️  BETRIEBSSYSTEM + PYTHON")
print("═" * 65)
print(f"    OS              : {platform.system()} {platform.release()}")
print(f"    OS Version      : {platform.version()[:60]}")
print(f"    Architecture    : {platform.architecture()[0]}")
print(f"    Hostname        : {platform.node()}")
print(f"    Python          : {sys.version.split()[0]}")
print(f"    Python-Pfad     : {sys.executable}")
print(f"    Locale          : {os.environ.get('LANG', os.environ.get('LC_ALL', 'nicht gesetzt'))}")

# ── WORKSPACE ANALYSE ──────────────────────────────────────────────────────
print()
print("═" * 65)
print("  📁 WORKSPACE — ORION-ROS2-Consciousness-Node")
print("═" * 65)

ext_stats: dict = {}
total_files = 0
total_bytes = 0
dirs_count  = 0

for root, dirs, files in os.walk(BASE):
    dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', '.venv']]
    dirs_count += len(dirs)
    for f in files:
        total_files += 1
        ext = Path(f).suffix.lower() or '(kein)'
        ext_stats[ext] = ext_stats.get(ext, 0) + 1
        try:
            total_bytes += os.path.getsize(os.path.join(root, f))
        except: pass

print(f"\n    Dateien gesamt  : {total_files}")
print(f"    Ordner          : {dirs_count}")
print(f"    Größe gesamt    : {total_bytes/(1024**2):.2f} MB")
print()
print("    📊 Dateitypen (Top 12):")
for ext, cnt in sorted(ext_stats.items(), key=lambda x: -x[1])[:12]:
    bar = "▓" * min(cnt, 30)
    print(f"      {ext:12s} {cnt:5d}  {bar}")

# ── DDGK SYSTEM-STATUS ─────────────────────────────────────────────────────
print()
print("═" * 65)
print("  🧠 DDGK SYSTEM-INVENTAR")
print("═" * 65)

ddgk_files = {
    "Cognitive Memory":     BASE / "cognitive_ddgk" / "cognitive_memory.jsonl",
    "Decision Chain":       BASE / "cognitive_ddgk" / "decision_chain.jsonl",
    "Decision Trace":       BASE / "cognitive_ddgk" / "decision_trace.jsonl",
    "Autonomous Loop":      BASE / "cognitive_ddgk" / "autonomous_loop_memory.jsonl",
    "Nuclear Audit":        BASE / "cognitive_ddgk" / "nuclear_audit_chain.jsonl",
    "HyperAgent Memory":    BASE / "cognitive_ddgk" / "hyper_agent_memory.jsonl",
    "CCRN Audit":           BASE / "ccrn_governance" / "audit_chain.jsonl",
}

total_entries = 0
for name, fp in ddgk_files.items():
    if fp.exists():
        lines = sum(1 for l in fp.read_text("utf-8", errors="replace").splitlines() if l.strip())
        total_entries += lines
        size = fp.stat().st_size
        status = "🟢" if lines > 0 else "🟡"
        print(f"    {status} {name:25s} : {lines:5d} Einträge  ({size//1024}kB)")
    else:
        print(f"    ⚫ {name:25s} : nicht vorhanden")

print(f"\n    📊 GESAMT AUDIT-EINTRÄGE: {total_entries}")

# DDGK Python-Module
print()
print("    🔷 DDGK Python-Module:")
ddgk_modules = [
    ("cognitive_ddgk/cognitive_ddgk_core.py", "CognitiveDDGK Core"),
    ("cognitive_ddgk/fusion_kernel.py",        "FusionKernel"),
    ("cognitive_ddgk/decision_chain.py",       "DecisionChain"),
    ("cognitive_ddgk/decision_trace.py",       "DecisionTrace (XAI)"),
    ("cognitive_ddgk/hitl_mcp_bridge.py",      "HITL Bridge"),
    ("nuclear_safety_simulator.py",            "Nuclear Safety Sim"),
    ("hyper_agent.py",                         "HyperAgent (v2)"),
    ("hyper_agent_system.py",                  "HyperAgent (v1)"),
    ("self_prompting_autonomous_loop.py",      "Autonomous Loop"),
    ("ddgk_dashboard.py",                      "Live Dashboard"),
    ("ddgk_live_dashboard.html",               "HTML Dashboard"),
]
for fname, label in ddgk_modules:
    fp = BASE / fname
    status = "✅" if fp.exists() else "❌"
    size   = f"{fp.stat().st_size//1024}kB" if fp.exists() else "—"
    print(f"      {status} {label:35s}  {fname}  ({size})")

# Synthesized Tools
synth = list((BASE / "cognitive_ddgk" / "synthesized_tools").glob("tool_*.py"))
hyper = list((BASE / "hyper_tools").glob("*.py")) if (BASE / "hyper_tools").exists() else []
print(f"\n    🔷 Synthetisierte Tools:")
print(f"      cognitive_ddgk/synthesized_tools/  : {len(synth)} Tools")
for t in synth:
    print(f"        ✅ {t.name}")
print(f"      hyper_tools/                       : {len(hyper)} Tools")
for t in hyper:
    if not t.name.startswith('__'):
        print(f"        ✅ {t.name}")

# ── DDGK SCHLEIFENANALYSE ──────────────────────────────────────────────────
print()
print("═" * 65)
print("  🔍 SCHLEIFENANALYSE — Warum hängen wir fest?")
print("═" * 65)

issues = []

# 1. Doppelte Implementierungen
if (BASE / "hyper_agent.py").exists() and (BASE / "hyper_agent_system.py").exists():
    issues.append(("⚠️", "DUPLIKAT", "hyper_agent.py + hyper_agent_system.py — keine gemeinsame Integration"))

# 2. Decision Chain vs Decision Trace
if (BASE / "cognitive_ddgk" / "decision_chain.py").exists() and \
   (BASE / "cognitive_ddgk" / "decision_trace.py").exists():
    issues.append(("⚠️", "DUPLIKAT", "decision_chain.py + decision_trace.py — parallele Audit-Systeme"))

# 3. Fehlende Master-Orchestrierung
if not (BASE / "orion_start.py").exists() and not (BASE / "master_orchestrator.py").exists():
    issues.append(("❌", "FEHLT", "Kein Master-Orchestrator — kein Single Entry Point für alles"))

# 4. Dashboard läuft nicht automatisch
if (BASE / "ddgk_dashboard.py").exists():
    issues.append(("ℹ️", "MANUELL", "Dashboard muss manuell gestartet werden (python ddgk_dashboard.py)"))

# 5. HyperAgent nicht in Autonomous Loop integriert
issues.append(("⚠️", "INTEGRATION", "HyperAgent nicht in Autonomous Loop integriert"))

# 6. Keine automatischen Tests
test_files = list(BASE.glob("test_*.py")) + list(BASE.glob("*_test.py"))
if not test_files:
    issues.append(("⚠️", "TESTS", "Keine automatischen Unit-Tests — kein CI/CD"))

print()
for icon, typ, desc in issues:
    print(f"  {icon}  [{typ:12s}] {desc}")

print()
print("  📋 ZUSAMMENFASSUNG SCHLEIFEN-URSACHEN:")
print("  1. Kein Single Entry Point → jede Session fängt anders an")
print("  2. Parallele Implementierungen → Verwirrung über welche zu nutzen")
print("  3. Context Window ~80% → Antworten werden kürzer, unvollständiger")
print("  4. Endloser 'dann weiter?' Zyklus → kein klares Abschlusskriterium")
print("  5. Fehlende Integration → Teile laufen, aber nicht gemeinsam")

# ── LÖSUNG ────────────────────────────────────────────────────────────────
print()
print("═" * 65)
print("  ✅ LÖSUNG: ORION MASTER START")
print("═" * 65)
print("  Erstelle: orion_start.py — 1 Befehl startet ALLES:")
print()
print("  python orion_start.py")
print("    → DDGK Dashboard (Port 7860)")
print("    → HyperAgent (neue Tools bauen wenn nötig)")
print("    → Decision Chain (jede Entscheidung geloggt)")
print("    → Autonomous Loop (Ziel-basiert, BALANCED)")
print("    → FusionKernel (κ live)")
print()

# Final Hash
summary = {
    "ts": datetime.datetime.now().isoformat(),
    "total_files": total_files,
    "total_bytes": total_bytes,
    "audit_entries": total_entries,
    "issues": len(issues),
    "python": sys.version.split()[0],
}
h = hashlib.sha256(json.dumps(summary, sort_keys=True).encode()).hexdigest()[:16]
print(f"  🔗 Analyse-Hash: {h}")
print(f"  📊 {total_files} Dateien | {total_bytes/(1024**2):.1f}MB | {total_entries} Audit-Einträge")
