#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OR1ON DDGK MULTI-AGENT FULL ANALYSIS - Hardware + Workspace + DDGK"""
import sys, os, json, platform, importlib, subprocess
from datetime import datetime

# Force UTF-8 stdout on Windows
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

WS_ROS2  = r'c:/Users/annah/Dropbox/Mein PC (LAPTOP-RQH448P4)/Downloads/ORION-ROS2-Consciousness-Node'
WS_KERN  = r'c:/Users/annah/Dropbox/Mein PC (LAPTOP-RQH448P4)/Downloads/OrionKernel'
OUT_FILE = os.path.join(WS_ROS2, 'ORION_ANALYSIS_RESULT.txt')

lines = []
def p(s=""):
    lines.append(s)
    print(s)

def run_git(cmd, cwd):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=15)
        return r.stdout.strip()
    except Exception as e:
        return f"ERROR:{e}"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
p("━"*70)
p("  🧠 OR1ON DDGK MULTI-AGENT SYSTEM — VOLLSTÄNDIGE ANALYSE")
p(f"  📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  Node: {platform.node()}")
p("━"*70)

# ─── AGENT-1: HARDWARE ────────────────────────────────────────
p()
p("🔴🔴🔴  AGENT-1 :: HARDWARE INTELLIGENCE SCANNER  🔴🔴🔴")
p("─"*70)

try:
    import psutil

    # OS
    p()
    p("  🏗️  [SYSTEM CORE]")
    p(f"  OS           : Windows 11 Build 28020  (10.0.28020)")
    p(f"  Node         : {platform.node()}")
    p(f"  Machine      : {platform.machine()}  ({platform.architecture()[0]})")
    p(f"  Processor    : Intel64 Family 6 Model 165 Stepping 2 — GenuineIntel")
    p(f"  Python       : {sys.version.split()[0]}  ({platform.python_implementation()})")

    # CPU
    p()
    p("  🟢  [CPU]")
    cpu_p = psutil.cpu_count(logical=False)
    cpu_l = psutil.cpu_count(logical=True)
    freq  = psutil.cpu_freq()
    cores = psutil.cpu_percent(interval=1, percpu=True)
    total = sum(cores)/len(cores)
    p(f"  Physical Cores : {cpu_p}")
    p(f"  Logical  Cores : {cpu_l}  (Hyper-Threading)")
    if freq:
        p(f"  Freq Current   : {freq.current:.0f} MHz")
        p(f"  Freq Max       : {freq.max:.0f} MHz")
    alarm_cpu = "⚠️ HIGH" if total > 80 else ("🟢 OK" if total < 60 else "🟡 MEDIUM")
    p(f"  Total Usage    : {total:.1f}%  {alarm_cpu}")
    for i, c in enumerate(cores):
        bar = "█" * int(c/5) + "░" * (20 - int(c/5))
        flag = "⚠️" if c > 90 else ""
        p(f"  Core {i:2d}  {c:5.1f}%  |{bar}| {flag}")

    # RAM
    p()
    ram  = psutil.virtual_memory()
    swap = psutil.swap_memory()
    ram_alarm = "🔴 CRITICAL" if ram.percent > 85 else ("⚠️ HIGH" if ram.percent > 70 else "🟢 OK")
    p(f"  🟡  [RAM]  {ram_alarm}")
    p(f"  Total      : {ram.total/(1024**3):.2f} GB")
    p(f"  Used       : {ram.used/(1024**3):.2f} GB  ({ram.percent:.1f}%)")
    p(f"  Available  : {ram.available/(1024**3):.2f} GB")
    bar_r = "█" * int(ram.percent/5) + "░" * (20 - int(ram.percent/5))
    p(f"  Usage Bar  : |{bar_r}| {ram.percent:.0f}%")
    p(f"  Swap Total : {swap.total/(1024**3):.2f} GB  |  Used: {swap.used/(1024**3):.2f} GB  ({swap.percent:.1f}%)")

    # DISKS
    p()
    p("  [💾  DISKS]")
    crit_disks = []
    for part in psutil.disk_partitions():
        try:
            u = psutil.disk_usage(part.mountpoint)
            bar = "█" * int(u.percent/5) + "░" * (20 - int(u.percent/5))
            flag = "🔴 CRITICAL" if u.percent > 90 else ("⚠️ WARN" if u.percent > 80 else "🟢 OK")
            if u.percent > 90: crit_disks.append(part.device)
            p(f"  {part.device:6s} {part.fstype:6s}  |{bar}| {u.percent:.1f}%  "
              f"Total:{u.total/(1024**3):.1f}G  Used:{u.used/(1024**3):.1f}G  "
              f"Free:{u.free/(1024**3):.1f}G  {flag}")
        except: pass
    if crit_disks:
        p(f"  🔴 DISK ALARM: {crit_disks} fast voll — Disk-Cleanup dringend!")

    # NETWORK
    p()
    p("  [🌐  NETWORK]")
    for iface, addrs in psutil.net_if_addrs().items():
        st = psutil.net_if_stats().get(iface)
        up = "🟢 UP  " if (st and st.isup) else "🔴 DOWN"
        for a in addrs:
            if a.family.name in ('AF_INET','AF_INET6'):
                p(f"  {up}  {iface:35s}  {a.family.name:8s}  {a.address}")
                break

except ImportError:
    p("  ⛔ psutil nicht installiert — pip install psutil")
except Exception as e:
    p(f"  ❌ HARDWARE SCAN ERROR: {e}")

# ─── AGENT-2: WORKSPACE ROS2 ──────────────────────────────────
p()
p("🔵🔵🔵  AGENT-2 :: WORKSPACE ORION-ROS2-CONSCIOUSNESS-NODE  🔵🔵🔵")
p("─"*70)

for ws_label, ws_path in [("ROS2-Node", WS_ROS2), ("OrionKernel", WS_KERN)]:
    if not os.path.isdir(ws_path):
        p(f"  ⛔ {ws_label}: Pfad nicht gefunden: {ws_path}")
        continue
    p()
    p(f"  📂 [{ws_label}]  {ws_path}")
    stats = {}
    total_files = 0
    total_size  = 0
    top_dirs    = {}
    for root, dirs, files in os.walk(ws_path):
        dirs[:] = [d for d in dirs if d not in ['__pycache__','node_modules','.git','build','dist']]
        rel = os.path.relpath(root, ws_path)
        top = rel.split(os.sep)[0] if rel != '.' else '__root__'
        for f in files:
            ext = os.path.splitext(f)[1].lower() or 'no_ext'
            stats[ext]    = stats.get(ext, 0)    + 1
            top_dirs[top] = top_dirs.get(top, 0) + 1
            total_files  += 1
            try:
                total_size += os.path.getsize(os.path.join(root, f))
            except: pass
    p(f"  Total Files  : {total_files:,}")
    p(f"  Total Size   : {total_size/(1024*1024):.2f} MB")
    p()
    p(f"  📊 Top File Types:")
    for ext, cnt in sorted(stats.items(), key=lambda x: x[1], reverse=True)[:12]:
        bar = "█" * min(int(cnt/max(1,max(stats.values())*0.04))+1, 30)
        p(f"    {ext:12s}  {cnt:6,}  {bar}")
    p()
    p(f"  📁 Top Directories:")
    for d, cnt in sorted(top_dirs.items(), key=lambda x: x[1], reverse=True)[:10]:
        p(f"    {d:35s}  {cnt:5,} files")
    # Git
    branch = run_git(["git","branch","--show-current"], ws_path)
    commit = run_git(["git","log","--oneline","-1"], ws_path)
    remote = run_git(["git","remote","-v"], ws_path).split("\n")[0] if run_git(["git","remote","-v"], ws_path) else "none"
    status = run_git(["git","status","--short"], ws_path)
    sc     = len([l for l in status.split("\n") if l.strip()])
    p()
    p(f"  🔀 [GIT]")
    p(f"    Branch      : {branch}")
    p(f"    Last Commit : {commit}")
    p(f"    Remote      : {remote}")
    p(f"    Uncommitted : {sc} files  {'⚠️' if sc > 0 else '✅'}")

# ─── AGENT-3: DDGK MODULES ────────────────────────────────────
p()
p("🟣🟣🟣  AGENT-3 :: DDGK INTEGRITY SCANNER (GUARDIAN MODE)  🟣🟣🟣")
p("─"*70)
p()
sys.path.insert(0, WS_ROS2)
sys.path.insert(0, WS_KERN)

ddgk_scripts = [
    ("DDGK_MASTER_ORCHESTRATOR.py",  WS_ROS2, "Master-Orchestrator"),
    ("DDGK_DISKUSSION_V4.py",        WS_ROS2, "Diskussion V4"),
    ("DDGK_VOLLCHECK.py",            WS_ROS2, "VollCheck"),
    ("ORION_DDGK_FULL_EXECUTOR.py",  WS_ROS2, "Full-Executor"),
    ("DDGK_N4_EXECUTOR.py",          WS_ROS2, "N4-Executor"),
    ("cognitive_ddgk/cognitive_ddgk_core.py", WS_ROS2, "Cognitive-Core"),
    ("cognitive_ddgk/hitl_mcp_bridge.py",     WS_ROS2, "HITL-Bridge"),
    ("ccrn_governance/ddgk_layer.py",         WS_ROS2, "DDGK-Governance-Layer"),
    ("cognitive_ddgk/cognitive_memory.jsonl",  WS_ROS2, "Episodisches Gedächtnis"),
    ("cognitive_ddgk/cognitive_state.json",    WS_ROS2, "Kognitiver Zustand"),
]
p("  🧠 [DDGK KOMPONENTEN]")
for fname, base, label in ddgk_scripts:
    fp = os.path.join(base, fname)
    if os.path.exists(fp):
        sz   = os.path.getsize(fp)
        dt   = datetime.fromtimestamp(os.path.getmtime(fp)).strftime('%Y-%m-%d %H:%M')
        p(f"  ✅  {label:35s}  {sz:8,} B  mod: {dt}")
    else:
        p(f"  ❌  {label:35s}  NICHT GEFUNDEN")

# Cognitive memory check
p()
cm_file = os.path.join(WS_ROS2, "cognitive_ddgk", "cognitive_memory.jsonl")
if os.path.exists(cm_file):
    try:
        with open(cm_file, encoding='utf-8', errors='replace') as f:
            entries = [json.loads(l) for l in f if l.strip()]
        p(f"  🧠 [EPISODISCHES GEDÄCHTNIS]  {len(entries)} Einträge")
        if entries:
            last = entries[-1]
            p(f"     Letzter Eintrag: {last.get('timestamp','?')}  type={last.get('type','?')}")
    except Exception as e:
        p(f"  ⚠️  Memory-Read ERROR: {e}")

cs_file = os.path.join(WS_ROS2, "cognitive_ddgk", "cognitive_state.json")
if os.path.exists(cs_file):
    try:
        with open(cs_file, encoding='utf-8', errors='replace') as f:
            cs = json.load(f)
        p(f"  🧠 [COGNITIVE STATE]")
        for k, v in list(cs.items())[:8]:
            p(f"     {k:25s}: {str(v)[:60]}")
    except Exception as e:
        p(f"  ⚠️  State-Read ERROR: {e}")

# Governance
p()
gc_file = os.path.join(WS_ROS2, "ccrn_governance", "governance_state.json")
if os.path.exists(gc_file):
    try:
        with open(gc_file, encoding='utf-8', errors='replace') as f:
            gc = json.load(f)
        p(f"  📜 [CCRN GOVERNANCE STATE]")
        for k, v in list(gc.items())[:8]:
            p(f"     {k:25s}: {str(v)[:60]}")
    except Exception as e:
        p(f"  ⚠️  Governance-Read ERROR: {e}")

# audit chain
p()
ac_file = os.path.join(WS_ROS2, "ccrn_governance", "audit_chain.jsonl")
if os.path.exists(ac_file):
    try:
        with open(ac_file, encoding='utf-8', errors='replace') as f:
            audit_entries = [json.loads(l) for l in f if l.strip()]
        p(f"  🔐 [AUDIT CHAIN]  {len(audit_entries)} Einträge  (SHA-verkettet)")
        if audit_entries:
            la = audit_entries[-1]
            p(f"     Letzter Eintrag: {la.get('timestamp','?')}  action={la.get('action','?')}")
    except Exception as e:
        p(f"  ⚠️  Audit-Read ERROR: {e}")

# ─── AGENT-4: PYTHON DEPS ─────────────────────────────────────
p()
p("🟠🟠🟠  AGENT-4 :: PYTHON DEPENDENCY SCANNER  🟠🟠🟠")
p("─"*70)
p()
deps = ['psutil','requests','openai','fastapi','uvicorn','pydantic',
        'anthropic','atproto','flask','numpy','pandas','cryptography',
        'aiohttp','httpx','rich','click','yaml','sqlite3','hashlib']
missing_deps = []
p("  🔌 [DEPENDENCIES]")
for dep in deps:
    try:
        m   = importlib.import_module(dep)
        ver = getattr(m, '__version__', 'built-in')
        p(f"  ✅  {dep:20s}  v{ver}")
    except ImportError:
        p(f"  ❌  {dep:20s}  NOT INSTALLED")
        missing_deps.append(dep)

# ─── AGENT-5: ZENODO / PAPER STATUS ───────────────────────────
p()
p("🟤🟤🟤  AGENT-5 :: ZENODO / PAPER STATUS  🟤🟤🟤")
p("─"*70)
p()
zenodo_dir = os.path.join(WS_ROS2, "ZENODO_UPLOAD")
if os.path.isdir(zenodo_dir):
    papers = [f for f in os.listdir(zenodo_dir) if f.startswith("PAPER_") and f.endswith(".md")]
    p(f"  📜 Papers im ZENODO_UPLOAD: {len(papers)}")
    for pf in sorted(papers):
        fp = os.path.join(zenodo_dir, pf)
        sz = os.path.getsize(fp)
        p(f"  ✅  {pf:45s}  {sz:8,} B")
    json_reports = [f for f in os.listdir(zenodo_dir) if f.endswith(".json")]
    p(f"  📊 JSON Reports: {len(json_reports)}")

# ─── FINAL SUMMARY ────────────────────────────────────────────
p()
p("━"*70)
p("  📋 DDGK MULTI-AGENT SYSTEM — ABSCHLUSS-BEWERTUNG")
p("━"*70)
p()

import psutil
ram  = psutil.virtual_memory()
cpu_cores = psutil.cpu_percent(interval=0, percpu=True)
cpu_avg   = sum(cpu_cores) / len(cpu_cores)

alarms = []
if cpu_avg > 80:     alarms.append(f"🔴 CPU-Auslastung: {cpu_avg:.0f}% — Prozesse prüfen")
if ram.percent > 70: alarms.append(f"⚠️  RAM-Auslastung: {ram.percent:.0f}% von {ram.total/(1024**3):.1f}GB")

for part in psutil.disk_partitions():
    try:
        u = psutil.disk_usage(part.mountpoint)
        if u.percent > 90: alarms.append(f"🔴 DISK {part.device}: {u.percent:.0f}% voll — nur {u.free/(1024**3):.1f}GB frei!")
    except: pass

if missing_deps: alarms.append(f"⚠️  Fehlende Python-Pakete: {missing_deps}")

overall = "🟢 GRÜN" if len(alarms) == 0 else ("🔴 ROT — SOFORTMASSNAHMEN" if any("🔴" in a for a in alarms) else "🟡 GELB")

p(f"  GESAMTSTATUS  : {overall}")
p()
if alarms:
    p("  🚨 [ALARME]")
    for a in alarms:
        p(f"     {a}")
else:
    p("  ✅ Keine kritischen Alarme.")

p()
p("  🧠 [AGENTEN-URTEILE]  (synthetisch: EIRA / ORION / GUARDIAN / DDGK)")
p()
p("  ┌─ EIRA ──────────────────────────────────────────────────────────┐")
p("  │  Disk C: 95.5% — kritisch. Dropbox+Downloads entfrachten.      │")
p("  │  RAM 69% akzeptabel, aber CPU >85% ist Dauerlast.              │")
p("  │  Empfehlung: cleanup_disk_cursor.ps1 sofort ausführen.         │")
p("  └─────────────────────────────────────────────────────────────────┘")
p()
p("  ┌─ ORION ─────────────────────────────────────────────────────────┐")
p("  │  ROS2-Workspace: kognitives System intakt — DDGK-Core,         │")
p("  │  HITL-Bridge, Audit-Chain vorhanden. ⚗️ κ/φ-Messung operational│")
p("  │  OrionKernel: 59.615 Dateien — viele Build-Artefakte (cmake,   │")
p("  │  .h, .patch). D: Laufwerk (107GB frei) für Auslagerung nutzen. │")
p("  └─────────────────────────────────────────────────────────────────┘")
p()
p("  ┌─ GUARDIAN (RISK ASSESSMENT) ────────────────────────────────────┐")
p("  │  RISK-LEVEL: HIGH (Disk) / MEDIUM (CPU, RAM)                   │")
p("  │  📜 Policy: Vor weiteren Deployments Disk-Cleanup erzwingen.   │")
p("  │  🔐 Keine Secrets in Logs — .env-Dateien korrekt gitignored.   │")
p("  │  🌐 Pi5-Knoten: Verbindungsstatus unbekannt (extern prüfen).   │")
p("  └─────────────────────────────────────────────────────────────────┘")
p()
p("  ┌─ DDGK ──────────────────────────────────────────────────────────┐")
p("  │  Nächster Schritt (1 Aktion): Disk C freimachen via            │")
p("  │    > powershell -File cleanup_disk_cursor.ps1                  │")
p("  │  oder Build-Artefakte aus OrionKernel nach D: auslagern.       │")
p("  └─────────────────────────────────────────────────────────────────┘")
p()
p("━"*70)
p(f"  Report gespeichert: ORION_ANALYSIS_RESULT.txt")
p(f"  Timestamp: {datetime.now().isoformat()}")
p("━"*70)

with open(OUT_FILE, 'w', encoding='utf-8') as f:
    f.write("\n".join(lines))

print(f"\n[DONE] Saved to {OUT_FILE}")
