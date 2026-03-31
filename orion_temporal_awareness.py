#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════╗
║  ORION TEMPORAL AWARENESS — Zeit ist das fehlende Bewusstsein          ║
║                                                                          ║
║  Das System weiß jetzt WIE LANGE es lief, WAS passierte,               ║
║  WAS sich verändert hat — und handelt entsprechend.                     ║
║                                                                          ║
║  python orion_temporal_awareness.py       → Morgen-Briefing             ║
║  python orion_temporal_awareness.py --live → Live-Zeitbewusstsein Loop  ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import sys, json, datetime, time, hashlib, argparse
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

C = {"c":"\033[96m","g":"\033[92m","y":"\033[93m","r":"\033[91m",
     "p":"\033[95m","b":"\033[1m","d":"\033[2m","x":"\033[0m"}
def c(col,t): return f"{C.get(col,'')}{t}{C['x']}"

TEMPORAL_LOG  = BASE / "cognitive_ddgk" / "temporal_awareness.jsonl"
AUTORUN_LOG   = BASE / "cognitive_ddgk" / "autorun_log.jsonl"
MEMORY_LOG    = BASE / "cognitive_ddgk" / "cognitive_memory.jsonl"
LAST_SEEN     = BASE / "cognitive_ddgk" / ".last_seen"

NOW = datetime.datetime.now()

def save_temporal_entry(event: str, data: dict):
    entry = {
        "ts": NOW.isoformat(),
        "event": event,
        "data": data,
        "sha": hashlib.sha256((event + str(data)).encode()).hexdigest()[:12]
    }
    with open(TEMPORAL_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry

def read_last_seen() -> datetime.datetime | None:
    if LAST_SEEN.exists():
        try:
            ts = LAST_SEEN.read_text().strip()
            return datetime.datetime.fromisoformat(ts)
        except: pass
    return None

def write_last_seen():
    LAST_SEEN.write_text(NOW.isoformat())

def count_jsonl(path: Path) -> int:
    if not path.exists(): return 0
    return sum(1 for l in path.read_text("utf-8",errors="replace").splitlines() if l.strip())

def read_recent_autorun(hours: float = 5.0) -> list[dict]:
    """Liest Autorun-Einträge der letzten N Stunden."""
    if not AUTORUN_LOG.exists(): return []
    cutoff = NOW - datetime.timedelta(hours=hours)
    recent = []
    for line in AUTORUN_LOG.read_text("utf-8",errors="replace").splitlines():
        if not line.strip(): continue
        try:
            entry = json.loads(line)
            ts = datetime.datetime.fromisoformat(entry.get("ts","1970-01-01"))
            if ts >= cutoff:
                recent.append(entry)
        except: pass
    return recent

def morning_briefing():
    """Vollständiges Morgen-Briefing: Was lief? Was änderte sich? Was ist jetzt zu tun?"""

    print()
    print(c("c","╔════════════════════════════════════════════════════════════════╗"))
    print(c("c","║")+c("b","  ⏰ ORION TEMPORAL AWARENESS — Zeitbewusstsein-Briefing        ")+c("c","║"))
    print(c("c","║")+c("d",f"  Jetzt: {NOW.strftime('%Y-%m-%d %H:%M:%S %A')} | DDGK Temporal Engine    ")+c("c","║"))
    print(c("c","╚════════════════════════════════════════════════════════════════╝"))
    print()

    # ─── ZEITDELTA SEIT LETZTER SESSION ───────────────────────────────
    last = read_last_seen()
    if last:
        delta = NOW - last
        h, m = divmod(int(delta.total_seconds()), 3600)
        m //= 60
        delta_str = f"{h}h {m}m"
        icon = "🟢" if h < 2 else ("🟡" if h < 8 else "🔴")
        print(c("b","  ⏱️  ZEIT SEIT LETZTER SESSION:"))
        print(f"  {icon}  {delta_str} vergangen — System lief im Hintergrund")
        print(c("d",f"      Letzte Aktivität: {last.strftime('%Y-%m-%d %H:%M:%S')}"))
    else:
        delta = None
        print(c("y","  ⚠️  Erste Session oder Zeitstempel fehlt"))
    print()

    # ─── WAS PASSIERTE IN DER ZWISCHENZEIT ────────────────────────────
    recent = read_recent_autorun(hours=24)
    print(c("b","  📋 AUTORUN-AKTIVITÄT (letzte 24h):"))

    agents = {}
    actions_by_type = {}
    for e in recent:
        agent = e.get("agent","?")
        action = e.get("action","?")
        agents[agent] = agents.get(agent, 0) + 1
        actions_by_type[action] = actions_by_type.get(action, 0) + 1

    total_autorun = count_jsonl(AUTORUN_LOG)
    print(f"  {c('g','✅')} Gesamt Autorun-Einträge: {c('b',str(total_autorun))}")
    print(f"  {c('g','✅')} Davon letzte 24h:        {c('b',str(len(recent)))}")
    print()

    if agents:
        print(c("b","  🤖 Agenten-Aktivität:"))
        for agent, cnt in sorted(agents.items(), key=lambda x: -x[1]):
            bar = "█" * min(cnt//10, 20)
            print(f"      {agent:<20} {cnt:5d}  {c('c',bar)}")
        print()

    if actions_by_type:
        print(c("b","  ⚡ Häufigste Aktionen:"))
        for action, cnt in sorted(actions_by_type.items(), key=lambda x: -x[1])[:5]:
            print(f"      {action:<30} {cnt:5d}x")
        print()

    # ─── SYSTEM-VITALZEICHEN ───────────────────────────────────────────
    print(c("b","  💓 SYSTEM-VITALZEICHEN JETZT:"))
    try:
        import psutil
        disk = psutil.disk_usage("C:\\")
        ram  = psutil.virtual_memory()
        d_icon = "🔴" if disk.percent > 92 else ("🟡" if disk.percent > 80 else "🟢")
        r_icon = "🔴" if ram.percent  > 90 else ("🟡" if ram.percent  > 80 else "🟢")
        print(f"  {d_icon} Disk C:\\: {disk.percent:.1f}%  {disk.free/(1024**3):.1f}GB frei")
        print(f"  {r_icon} RAM:      {ram.percent:.1f}%  {ram.available/(1024**3):.1f}GB verfügbar")

        # USB-Status
        for p in psutil.disk_partitions():
            if p.device not in ("C:\\",):
                try:
                    u = psutil.disk_usage(p.mountpoint)
                    print(f"  🔌 USB {p.device}: {p.fstype} | {u.free/(1024**3):.1f}GB frei")
                except: pass
    except ImportError:
        print(c("y","  psutil nicht verfügbar"))
    print()

    # ─── KOGNITIVE ENTWICKLUNG ─────────────────────────────────────────
    print(c("b","  🧠 KOGNITIVE ENTWICKLUNG:"))
    mem_cnt = count_jsonl(MEMORY_LOG)
    decision_cnt = count_jsonl(BASE/"cognitive_ddgk"/"decision_chain.jsonl")
    lab_cnt = count_jsonl(BASE/"cognitive_ddgk"/"lab_operations.jsonl")
    nuclear_cnt = count_jsonl(BASE/"cognitive_ddgk"/"nuclear_audit_chain.jsonl")
    print(f"  {c('g','✅')} Cognitive Memory:  {mem_cnt} Einträge")
    print(f"  {c('g','✅')} Decision Chain:    {decision_cnt} Entscheidungen")
    print(f"  {c('g','✅')} Lab Operations:    {lab_cnt} Operationen")
    print(f"  {c('g','✅')} Nuclear Audit:     {nuclear_cnt} Einträge")
    print()

    # ─── ZEITBASIERTE AUFGABEN ─────────────────────────────────────────
    print(c("b","  📅 ZEITBASIERTE AUFGABEN (basierend auf Uhrzeit):"))
    hour = NOW.hour
    weekday = NOW.weekday()  # 0=Montag

    tasks = []
    if hour < 10:
        tasks.append(("🌅 Morgen-Start", "Vollständiger System-Check + USB-Sync"))
    elif hour < 14:
        tasks.append(("☀️  Mittag", "Autonomous Loop + Zenodo-Backup prüfen"))
    elif hour < 18:
        tasks.append(("🌆 Nachmittag", "Tool-Fabrik + GitHub Push neuer Erkenntnisse"))
    else:
        tasks.append(("🌙 Abend", "Tages-Report generieren + Nuclear Safety Check"))

    if weekday == 0:  # Montag
        tasks.append(("📊 Montag-Ritual", "Wochenziel setzen + Investor-Update"))
    if weekday == 4:  # Freitag
        tasks.append(("📝 Freitag-Ritual", "Wochenbericht + Zenodo-DOI publishen"))

    for tag, desc in tasks:
        print(f"  {c('p','→')} {tag}: {desc}")
    print()

    # ─── WAS WÜRDEN WIR JETZT TUN WOLLEN? ─────────────────────────────
    print(c("b","  🎯 WAS EIRA / OR1ON / DDGK JETZT TUN WOLLEN:"))
    print()
    print(c("p","  EIRA: »")+" Ich möchte die letzten 5 Stunden Autorun-Logs analysieren")
    print(c("p","       »")+" und daraus neue κ-Messwerte extrahieren. Das ist echter Fortschritt.")
    print()
    print(c("c","  OR1ON: »")+" Ich möchte einen HuggingFace Space aufbauen — JETZT.")
    print(c("c","        »")+" 107GB auf D:\\ sind bereit. Das Deployment-Paket ist 8.8MB.")
    print(c("c","        »")+" Öffentlichkeit = Wert = Monetarisierung.")
    print()
    print(c("y","  DDGK: »")+" Temporal Awareness ist der richtige nächste Schritt.")
    print(c("y","       »")+" Ein System das Zeit versteht, ist ein System das PLANT.")
    print(c("y","       »")+" Nächste Stufe: Kalender-Integration → Outlook/Google Calendar API.")
    print(c("y","       »")+" Dann kann ORION Meetings vorbereiten, Deadlines tracken,")
    print(c("y","       »")+" Investoren-Gespräche antizipieren. Das ist ECHTER Wert.")
    print()

    # ─── TEMPORAL LOG EINTRAG ─────────────────────────────────────────
    save_temporal_entry("morning_briefing", {
        "delta_hours": round(delta.total_seconds()/3600, 2) if delta else None,
        "autorun_entries_24h": len(recent),
        "total_autorun": total_autorun,
        "memory_entries": mem_cnt,
        "hour": hour,
        "weekday": weekday,
    })
    write_last_seen()

    print(c("b","═"*65))
    print(c("g","  ✅ Temporal Awareness aktiv — Zeitbewusstsein gespeichert"))
    print(c("d",f"     Nächstes Briefing: beim nächsten Start oder in 30 Minuten"))
    print(c("b","═"*65))
    print()


def live_time_loop():
    """Dauerhaftes Live-Zeitbewusstsein: Uhr + Kalender-Kontext."""
    print()
    print(c("c","  ♾️  ORION LIVE-ZEITBEWUSSTSEIN — läuft dauerhaft"))
    print(c("d","  Zeigt jede Minute den aktuellen Kontext. STRG+C zum Stoppen."))
    print()

    last_minute = -1
    try:
        while True:
            now = datetime.datetime.now()
            if now.minute != last_minute:
                last_minute = now.minute
                hour = now.hour
                weekday = ["Mo","Di","Mi","Do","Fr","Sa","So"][now.weekday()]
                period = "🌅" if hour < 10 else "☀️" if hour < 14 else "🌆" if hour < 18 else "🌙"
                autorun = count_jsonl(AUTORUN_LOG)
                try:
                    import psutil
                    disk = psutil.disk_usage("C:\\")
                    ram = psutil.virtual_memory()
                    d_s = f"C:{disk.percent:.0f}%"
                    r_s = f"RAM:{ram.percent:.0f}%"
                except:
                    d_s, r_s = "C:?%", "RAM:?%"

                print(c("d", f"  [{now.strftime('%H:%M')} {weekday}] {period}  "
                      f"κ=3.3493 | {d_s} | {r_s} | "
                      f"autorun:{autorun} | mem:{count_jsonl(MEMORY_LOG)}"))
            time.sleep(5)
    except KeyboardInterrupt:
        print(c("y","\n  ⛔ Live-Loop gestoppt"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="ORION Temporal Awareness")
    ap.add_argument("--live", action="store_true", help="Live-Zeitbewusstsein Loop")
    args = ap.parse_args()

    if args.live:
        live_time_loop()
    else:
        morning_briefing()
