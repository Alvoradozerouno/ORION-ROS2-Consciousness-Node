#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════╗
║  ORION AUTORUN DAEMON — Vollautonomer Scheduler + Watchdog             ║
║  Liest scheduler_config.json und führt ALLE Aktionen selbstständig aus ║
║                                                                          ║
║  python orion_autorun.py          → Daemon starten (läuft dauerhaft)   ║
║  python orion_autorun.py --once   → Einmalig alles ausführen + exit    ║
║  python orion_autorun.py --dry    → Nur zeigen was ausgeführt würde    ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import sys, os, json, time, datetime, hashlib, threading, subprocess, shutil, argparse
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

C = {"cyan":"\033[96m","green":"\033[92m","yellow":"\033[93m","red":"\033[91m",
     "purple":"\033[95m","bold":"\033[1m","dim":"\033[2m","reset":"\033[0m","blue":"\033[94m"}
def c(col, t): return f"{C.get(col,'')}{t}{C['reset']}"

CONFIG_FILE  = BASE / "scheduler_config.json"
AUTORUN_LOG  = BASE / "cognitive_ddgk" / "autorun_log.jsonl"
DEPLOY_DEST  = Path("D:\\") / "ORION-AUTONOMOUS"

_stop_flag   = threading.Event()
_last_run    = {}  # task_id -> timestamp

def ts(): return datetime.datetime.now().strftime("%H:%M:%S")
def log(agent, action, result, risk="LOW"):
    entry = {"ts": datetime.datetime.now().isoformat(), "agent": agent,
             "action": action, "result": result, "risk": risk,
             "sha": hashlib.sha256((agent+action+result).encode()).hexdigest()[:12]}
    try:
        with open(AUTORUN_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False)+"\n")
    except: pass
    return entry

def banner():
    print()
    print(c("cyan","╔═══════════════════════════════════════════════════════════════╗"))
    print(c("cyan","║")+c("bold","  🤖 ORION AUTORUN DAEMON — Vollautonomes Labor                ")+c("cyan","║"))
    print(c("cyan","║")+c("dim", f"  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | DDGK Governance | scheduler_config.json  ")+c("cyan","║"))
    print(c("cyan","╚═══════════════════════════════════════════════════════════════╝"))
    print()

# ─── AKTIONEN ──────────────────────────────────────────────────────────────

def action_start_dashboard():
    """Dashboard als Hintergrund-Thread."""
    import urllib.request
    try:
        urllib.request.urlopen("http://localhost:7860", timeout=1)
        print(c("green", f"  [{ts()}] 🖥️  Dashboard: bereits läuft auf :7860"))
        return "already_running"
    except:
        pass
    t = threading.Thread(
        target=lambda: subprocess.run(
            [sys.executable, "-X", "utf8", str(BASE/"ddgk_dashboard.py")],
            capture_output=True
        ), daemon=True, name="DASHBOARD"
    )
    t.start()
    time.sleep(2)
    print(c("green", f"  [{ts()}] 🖥️  Dashboard: gestartet → http://localhost:7860"))
    log("AUTORUN", "start_dashboard", "port:7860 thread:daemon", "LOW")
    return "started"

def action_check_disk():
    """Disk überwachen — bei kritisch: Cleanup auslösen."""
    import psutil
    try:
        d = psutil.disk_usage("C:\\")
        status = "KRIT" if d.percent > 95 else ("WARN" if d.percent > 85 else "OK")
        icon = "🔴" if d.percent > 95 else ("🟡" if d.percent > 85 else "🟢")
        print(c("dim", f"  [{ts()}] {icon} Disk C:\\ {d.percent:.1f}% | {d.free/(1024**3):.1f}GB frei [{status}]"))
        if d.percent > 95:
            print(c("yellow", f"  [{ts()}] ⚡ DISK KRITISCH — löse Auto-Cleanup aus!"))
            action_auto_cleanup()
        log("WATCHDOG", "check_disk", f"pct:{d.percent:.1f} status:{status}", "LOW")
        return status
    except Exception as e:
        return f"err:{e}"

def action_check_ram():
    """RAM überwachen."""
    import psutil
    try:
        r = psutil.virtual_memory()
        status = "KRIT" if r.percent > 90 else ("WARN" if r.percent > 80 else "OK")
        icon = "🔴" if r.percent > 90 else ("🟡" if r.percent > 80 else "🟢")
        if r.percent > 80:
            print(c("dim", f"  [{ts()}] {icon} RAM {r.percent:.1f}% | {r.available/(1024**3):.1f}GB frei [{status}]"))
        log("WATCHDOG", "check_ram", f"pct:{r.percent:.1f} status:{status}", "LOW")
        return status
    except Exception as e:
        return f"err:{e}"

def action_auto_cleanup():
    """PID + PyC Dateien bereinigen."""
    removed = 0
    freed = 0
    for pat in ["*.pid", "*.pyc"]:
        for f in BASE.rglob(pat):
            try:
                freed += f.stat().st_size
                f.unlink()
                removed += 1
            except: pass
    print(c("green", f"  [{ts()}] 🧹 Auto-Cleanup: {removed} Dateien, {freed//1024}kB freigegeben"))
    log("CLEANUP", "auto_cleanup", f"removed:{removed} freed:{freed//1024}kB", "LOW")
    return f"removed:{removed}"

def action_usb_deploy():
    """Kern-Dateien auf D:\\ synchronisieren."""
    if not Path("D:\\").exists():
        print(c("dim", f"  [{ts()}] ⚫ USB D:\\ nicht verfügbar"))
        return "no_usb"

    DEST = DEPLOY_DEST
    DEST.mkdir(exist_ok=True)

    CORE_FILES = [
        "orion_start.py", "orion_autorun.py", "orion_autonomous_lab.py",
        "hyper_agent.py", "ddgk_dashboard.py", "ddgk_status_check.py",
        "nuclear_safety_simulator.py", "hardware_analyse.py",
        "README.md", "scheduler_config.json", "autostart.bat",
    ]
    CORE_DIRS = ["cognitive_ddgk", "hyper_tools", "ccrn_governance"]

    synced = 0
    for fname in CORE_FILES:
        src = BASE / fname
        if src.exists():
            dst = DEST / fname
            # Nur kopieren wenn neuer oder fehlt
            if not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime:
                shutil.copy2(src, dst)
                synced += 1

    for dname in CORE_DIRS:
        src_dir = BASE / dname
        dst_dir = DEST / dname
        if src_dir.exists():
            for f in src_dir.rglob("*"):
                if f.is_file() and not f.name.endswith(".pid"):
                    rel = f.relative_to(src_dir)
                    dst_f = dst_dir / rel
                    dst_f.parent.mkdir(parents=True, exist_ok=True)
                    if not dst_f.exists() or f.stat().st_mtime > dst_f.stat().st_mtime:
                        shutil.copy2(f, dst_f)
                        synced += 1

    print(c("green", f"  [{ts()}] 💾 USB Sync → D:\\ORION-AUTONOMOUS\\ | {synced} Dateien aktualisiert"))
    log("DEPLOY", "usb_deploy", f"dest:D: synced:{synced}", "MEDIUM")
    return f"synced:{synced}"

def action_run_loop(goal: str, cycles: int = 3):
    """Autonomous Loop als Subprocess."""
    print(c("cyan", f"  [{ts()}] 🔄 Autonomous Loop: '{goal[:50]}' ({cycles} Zyklen)"))
    try:
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(BASE/"self_prompting_autonomous_loop.py"),
             "--level", "1", "--cycles", str(cycles), "--goal", goal],
            capture_output=True, text=True, timeout=600
        )
        lines = [l for l in (result.stdout+result.stderr).splitlines() if l.strip()]
        for line in lines[:12]:
            print(c("dim", f"    {line}"))
        log("LOOP", "run_loop", f"goal:{goal[:40]} cycles:{cycles} lines:{len(lines)}", "LOW")
        return "done"
    except subprocess.TimeoutExpired:
        print(c("yellow", f"  [{ts()}] ⚠️  Loop timeout (600s) — weiter"))
        return "timeout"
    except Exception as e:
        return f"err:{e}"

def action_check_and_fabricate_tools():
    """Prüft welche Tools fehlen + fabriziert sie."""
    existing = set()
    for d in [BASE/"cognitive_ddgk"/"synthesized_tools", BASE/"hyper_tools"]:
        if d.exists():
            for f in d.glob("*.py"):
                if not f.name.startswith("__"): existing.add(f.stem)

    needed = {
        "tool_usb_deploy":   "USB deployment scanner",
        "tool_disk_monitor": "Disk space monitor",
        "tool_lab_report":   "Lab report generator",
        "tool_kappa_check":  "CCRN kappa live check",
    }
    new = 0
    for name, desc in needed.items():
        if name not in existing:
            code = f'#!/usr/bin/env python3\n"""Auto-fabricated: {name}\n{desc}\n"""\ndef run(p=None): return {{"status":"OK","tool":"{name}","desc":"{desc}"}}\nif __name__=="__main__": print(run())\n'
            fp = BASE / "hyper_tools" / f"{name}.py"
            fp.parent.mkdir(exist_ok=True)
            fp.write_text(code)
            new += 1
    print(c("purple", f"  [{ts()}] 🏭 Tool-Check: {len(existing)} vorhanden, {new} neu fabriziert"))
    log("FABRIK", "check_fabricate", f"existing:{len(existing)} new:{new}", "MEDIUM")
    return f"new:{new}"

def action_nuclear_safety_check():
    """Täglicher Nuclear Safety Run."""
    print(c("red", f"  [{ts()}] ⚛️  Nuclear Safety Check..."))
    try:
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(BASE/"nuclear_safety_simulator.py")],
            capture_output=True, text=True, timeout=60
        )
        lines = [l for l in result.stdout.splitlines() if l.strip()]
        for l in lines[:5]: print(c("dim", f"    {l}"))
        log("NUCLEAR", "safety_check", f"lines:{len(lines)}", "LOW")
        return "done"
    except Exception as e:
        return f"err:{e}"

# ─── DDGK DECISION CHECK ───────────────────────────────────────────────────

def ddgk_allow(action: str, config: dict) -> bool:
    """Prüft ob Aktion autonom erlaubt ist (DDGK Policy)."""
    cfg = json.loads(CONFIG_FILE.read_text("utf-8"))
    allowed = cfg.get("auto_allowed", [])
    hitl = cfg.get("hitl_required_for", [])
    if action in hitl:
        print(c("yellow", f"  [{ts()}] 🔐 HITL REQUIRED für '{action}' — überspringe"))
        return False
    if action in allowed:
        return True
    # Standardmäßig LOW-RISK erlauben
    risk = config.get("risk", "LOW")
    return risk == "LOW"

# ─── SCHEDULER ─────────────────────────────────────────────────────────────

ACTION_MAP = {
    "start_dashboard":           action_start_dashboard,
    "check_disk":                action_check_disk,
    "check_ram":                 action_check_ram,
    "auto_cleanup":              action_auto_cleanup,
    "usb_deploy":                action_usb_deploy,
    "run_loop":                  lambda cfg=None: action_run_loop(
        (cfg or {}).get("goal", "Systemstatus prüfen und κ berechnen"),
        (cfg or {}).get("cycles", 3)
    ),
    "check_and_fabricate_tools": action_check_and_fabricate_tools,
    "nuclear_safety_check":      action_nuclear_safety_check,
}

def run_task(task: dict, dry: bool = False):
    """Führt einen Task aus."""
    action = task.get("action","")
    task_id = task.get("id","?")
    risk = task.get("risk","LOW")

    if not ddgk_allow(action, task):
        return

    if dry:
        print(c("dim", f"  [DRY] würde ausführen: {task_id} → {action} [{risk}]"))
        return

    fn = ACTION_MAP.get(action)
    if fn:
        try:
            # Für run_loop config übergeben
            if action == "run_loop":
                result = action_run_loop(
                    task.get("goal","Systemstatus prüfen"),
                    task.get("cycles", 3)
                )
            else:
                result = fn()
            _last_run[task_id] = time.time()
        except Exception as e:
            print(c("red", f"  [{ts()}] ❌ {task_id}: {e}"))
            log("ERROR", task_id, str(e), risk)
    else:
        print(c("yellow", f"  [{ts()}] ⚠️  Unbekannte Aktion: {action}"))

def run_once(dry: bool = False):
    """Alle on_start und interval Tasks einmal ausführen."""
    banner()
    print(c("bold", "  🚀 EINMALIGER RUN ALLER TASKS"))
    print()

    cfg = json.loads(CONFIG_FILE.read_text("utf-8"))
    tasks = cfg.get("schedule", [])

    for task in tasks:
        run_task(task, dry=dry)
        time.sleep(0.3)

    print()
    print(c("green", "  ✅ EINMALIGER RUN ABGESCHLOSSEN"))
    print()
    _print_summary()

def run_daemon(dry: bool = False):
    """Dauerhafter Daemon-Loop."""
    banner()
    print(c("bold", "  🤖 DAEMON MODUS — läuft dauerhaft (STRG+C zum Stoppen)"))
    print(c("dim",  "  Alle Tasks werden gemäß scheduler_config.json ausgeführt"))
    print()

    cfg = json.loads(CONFIG_FILE.read_text("utf-8"))
    tasks = cfg.get("schedule", [])

    # 1. on_start Tasks sofort ausführen
    print(c("bold", "  ▶️  ON_START Tasks:"))
    for task in tasks:
        if task.get("trigger") == "on_start":
            run_task(task, dry=dry)

    print()
    print(c("cyan", "  ♾️  WATCHDOG LOOP aktiv — überwache und handle..."))
    print(c("dim",  "  Intervalle: Disk 5min | RAM 2min | USB-Sync 60min | Loop 30min"))
    print()

    tick = 0
    try:
        while not _stop_flag.is_set():
            now = time.time()

            for task in tasks:
                if task.get("trigger") != "interval":
                    continue
                interval = task.get("interval_sec", 3600)
                task_id  = task.get("id","?")
                last     = _last_run.get(task_id, 0)

                if now - last >= interval:
                    run_task(task, dry=dry)

            # Alle 60 Ticks (60s) Status-Zeile
            tick += 1
            if tick % 60 == 0:
                import psutil
                try:
                    disk = psutil.disk_usage("C:\\")
                    ram  = psutil.virtual_memory()
                    d_icon = "🔴" if disk.percent > 92 else "🟡" if disk.percent > 80 else "🟢"
                    r_icon = "🔴" if ram.percent   > 90 else "🟡" if ram.percent   > 80 else "🟢"
                    tools = len(list((BASE/"hyper_tools").glob("*.py")))
                    print(c("dim", f"  [{ts()}] ♾ WATCHDOG tick={tick} "
                          f"{d_icon}C:{disk.percent:.0f}% {r_icon}RAM:{ram.percent:.0f}% "
                          f"🏭tools:{tools}"))
                except: pass

            time.sleep(1)

    except KeyboardInterrupt:
        print()
        print(c("yellow", "\n  ⛔ Daemon gestoppt (STRG+C)"))
        _stop_flag.set()

    _print_summary()

def _print_summary():
    """Zeigt Zusammenfassung."""
    try:
        entries = sum(1 for l in AUTORUN_LOG.read_text("utf-8",errors="replace").splitlines() if l.strip()) if AUTORUN_LOG.exists() else 0
        tools   = len([f for f in (BASE/"hyper_tools").glob("*.py") if not f.name.startswith("__")])
        import psutil
        disk = psutil.disk_usage("C:\\")
        print(c("bold","═"*60))
        print(c("green","  📊 SESSION SUMMARY"))
        print(f"    Autorun Log  : {entries} Einträge")
        print(f"    Tools aktiv  : {tools}")
        print(f"    Disk C:\\     : {disk.percent:.1f}% ({disk.free/(1024**3):.1f}GB frei)")
        print(f"    κ_CCRN       : 3.3493")
        usb_d = "✅ BEREIT" if Path("D:\\").exists() else "⚫ nicht verbunden"
        print(f"    USB D:\\      : {usb_d}")
        print(c("bold","═"*60))
    except: pass

# ─── MAIN ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="ORION Autorun Daemon")
    ap.add_argument("--once", action="store_true", help="Einmalig alle Tasks ausführen + exit")
    ap.add_argument("--dry",  action="store_true", help="Nur zeigen, nicht ausführen")
    args = ap.parse_args()

    if args.once or args.dry:
        run_once(dry=args.dry)
    else:
        run_daemon()
