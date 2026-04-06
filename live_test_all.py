#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LIVE-TEST: Alle Agenten-Komponenten permanent autonom?
Testet: Ollama, DDGK, FusionKernel, Loop, Nuclear, Pi5
"""
import sys, json, pathlib, datetime, urllib.request, time, os

BASE = pathlib.Path(__file__).parent
sys.path.insert(0, str(BASE))

SEP = "=" * 62
print(f"\n{SEP}")
print("  ORION/DDGK LIVE-TEST — Permanente Autonomie")
print(f"  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(SEP)

results = {}

# ── 1. Ollama lokal ──────────────────────────────────────────
print("\n[1] Ollama (lokal) ...")
try:
    r = urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3)
    models = json.loads(r.read()).get("models", [])
    names = [m["name"] for m in models[:6]]
    print(f"    OK  — {len(models)} Modelle: {names}")
    results["ollama_local"] = f"OK ({len(models)} Modelle)"
except Exception as e:
    print(f"    OFFLINE — {str(e)[:60]}")
    results["ollama_local"] = f"OFFLINE: {str(e)[:40]}"

# ── 2. DDGK Cognitive Memory ─────────────────────────────────
print("\n[2] DDGK Cognitive Memory ...")
mem = BASE / "cognitive_ddgk" / "cognitive_memory.jsonl"
if mem.exists():
    lines = [l for l in mem.read_text("utf-8", errors="replace").splitlines() if l.strip()]
    try:
        last = json.loads(lines[-1]) if lines else {}
        last_action = last.get("action", "?")
        last_ts = last.get("ts", "?")[:19]
        print(f"    OK  — {len(lines)} Eintraege | letzter: {last_action} @ {last_ts}")
        results["ddgk_memory"] = f"OK ({len(lines)} Eintraege)"
    except:
        print(f"    OK  — {len(lines)} Eintraege")
        results["ddgk_memory"] = f"OK ({len(lines)} Eintraege)"
else:
    print("    FEHLT")
    results["ddgk_memory"] = "FEHLT"

# ── 3. Cognitive State (kappa, CCRN, stop_flag) ──────────────
print("\n[3] Cognitive State (kappa / CCRN) ...")
cs = BASE / "cognitive_ddgk" / "cognitive_state.json"
if cs.exists():
    state = json.loads(cs.read_text("utf-8"))
    kappa = state.get("kappa_current", "?")
    ccrn  = state.get("ccrn_active", "?")
    stop  = state.get("stop_flag", "?")
    cycle = state.get("cognitive_cycle", "?")
    print(f"    kappa={kappa} | CCRN={ccrn} | stop_flag={stop} | cycle={cycle}")
    results["cog_state"] = f"kappa={kappa} CCRN={ccrn} stop={stop}"
else:
    print("    FEHLT")
    results["cog_state"] = "FEHLT"

# ── 4. CognitiveDDGK Core — kappa live berechnen ─────────────
print("\n[4] CognitiveDDGK Core — live kappa berechnen ...")
try:
    from cognitive_ddgk.cognitive_ddgk_core import CognitiveDDGK
    ddgk = CognitiveDDGK(agent_id="LIVE-TEST")
    k = ddgk.compute_kappa()
    formula = k.get("formula", "?")
    print(f"    OK  — kappa={k.get('kappa')} | CCRN={k.get('ccrn_active')}")
    print(f"    Formel: {formula}")
    results["ddgk_core"] = f"OK kappa={k.get('kappa')}"
except Exception as e:
    print(f"    FEHLER — {e}")
    results["ddgk_core"] = f"FEHLER: {str(e)[:50]}"

# ── 5. FusionKernel ──────────────────────────────────────────
print("\n[5] FusionKernel (cognitive_ddgk/fusion_kernel.py) ...")
try:
    from cognitive_ddgk.fusion_kernel import FusionKernel
    fk = FusionKernel(agent_id="LIVE-FUSION")
    s = fk.status()
    kappa_fk = s.get("ddgk", {}).get("kappa", "?")
    mem_fk   = s.get("ddgk", {}).get("memory_depth", "?")
    print(f"    OK  — DDGK={s['ddgk_active']} | kappa={kappa_fk} | Memory={mem_fk}")
    results["fusion_kernel"] = f"OK kappa={kappa_fk}"
except Exception as e:
    print(f"    FEHLER — {e}")
    results["fusion_kernel"] = f"FEHLER: {str(e)[:50]}"

# ── 6. Autonomous Loop Memory ─────────────────────────────────
print("\n[6] Autonomous Loop Memory ...")
lm = BASE / "cognitive_ddgk" / "autonomous_loop_memory.jsonl"
if lm.exists():
    ll = [l for l in lm.read_text("utf-8", errors="replace").splitlines() if l.strip()]
    print(f"    OK  — {len(ll)} Eintraege")
    results["loop_memory"] = f"OK ({len(ll)} Eintraege)"
else:
    print("    FEHLT")
    results["loop_memory"] = "FEHLT"

# ── 7. Nuclear Audit Chain ────────────────────────────────────
print("\n[7] Nuclear Safety Audit Chain (IEC 61508) ...")
na = BASE / "cognitive_ddgk" / "nuclear_audit_chain.jsonl"
if na.exists():
    nl = [l for l in na.read_text("utf-8", errors="replace").splitlines() if l.strip()]
    print(f"    OK  — {len(nl)} Eintraege")
    results["nuclear_audit"] = f"OK ({len(nl)} Eintraege)"
else:
    print("    FEHLT (nuclear_safety_simulator.py noch nicht gelaufen)")
    results["nuclear_audit"] = "FEHLT"

# ── 8. Self-Prompting Loop — 2 Zyklen live ───────────────────
print("\n[8] Self-Prompting Autonomous Loop — 2 Zyklen LIVE ...")
try:
    from self_prompting_autonomous_loop import (
        SelfPromptingAutonomousLoop, AutonomyLevel, AutonomousTask, TaskStatus
    )
    loop = SelfPromptingAutonomousLoop(
        autonomy=AutonomyLevel.BALANCED,
        interval=0.2,
        agent_id="LIVE-TEST-LOOP"
    )
    loop.set_goal("System-Status pruefen und CCRN-Kohaerenz validieren")
    loop.add_task(AutonomousTask(
        goal="check_status", tool="check_status", risk_level="LOW"
    ))
    loop.add_task(AutonomousTask(
        goal="kappa_CCRN berechnen", tool="compute_kappa", risk_level="LOW"
    ))
    tasks = loop.run(max_cycles=2)
    done = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
    print(f"    OK  — {done}/{len(tasks)} Tasks completed | {loop._cycle} Zyklen")
    results["auto_loop"] = f"OK {done}/{len(tasks)} completed"
except Exception as e:
    print(f"    FEHLER — {e}")
    results["auto_loop"] = f"FEHLER: {str(e)[:60]}"

# ── 9. Nuclear Simulator — Szenario 1 (Normal) ───────────────
print("\n[9] Nuclear Safety Simulator — Szenario 1 (Normal) ...")
try:
    from nuclear_safety_simulator import NuclearSafetySimulator
    sim = NuclearSafetySimulator(verbose=False)
    r1 = sim.scenario_1_normal_operation(cycles=3)
    r6 = sim.scenario_6_cyber_attack()
    print(f"    Szenario 1 (Normal)  : status={r1['status']} kappa={r1['kappa']:.4f}")
    print(f"    Szenario 6 (Cyber)   : status={r6['status']} replay_blocked={r6.get('replay_blocked')}")
    results["nuclear_sim"] = f"OK S1={r1['status']} S6={r6['status']}"
except Exception as e:
    print(f"    FEHLER — {e}")
    results["nuclear_sim"] = f"FEHLER: {str(e)[:60]}"

# ── 10. Pi5/NEXUS ─────────────────────────────────────────────
print("\n[10] Pi5 / NEXUS (192.168.1.103) ...")
try:
    r2 = urllib.request.urlopen("http://192.168.1.103:11434/api/tags", timeout=3)
    m2 = json.loads(r2.read()).get("models", [])
    names2 = [m["name"] for m in m2]
    print(f"    ONLINE — {len(m2)} Modelle: {names2}")
    results["pi5_nexus"] = f"ONLINE ({len(m2)} Modelle)"
except Exception as e:
    print(f"    OFFLINE — {str(e)[:50]}")
    results["pi5_nexus"] = f"OFFLINE"

# ── ZUSAMMENFASSUNG ───────────────────────────────────────────
print(f"\n{SEP}")
print("  ERGEBNIS-ZUSAMMENFASSUNG")
print(SEP)
ok_count = sum(1 for v in results.values() if v.startswith("OK") or v.startswith("ONLINE"))
total = len(results)
for key, val in results.items():
    icon = "OK " if (val.startswith("OK") or val.startswith("ONLINE")) else "FAIL"
    print(f"  [{icon}] {key:20s}: {val[:50]}")

print(f"\n  Gesamt: {ok_count}/{total} Komponenten aktiv")
if ok_count == total:
    print("  System laeuft vollstaendig autonom!")
elif ok_count >= total - 1:
    print("  System laeuft weitgehend autonom (1 Komponente offline)")
else:
    print(f"  {total - ok_count} Komponenten benoetigen Aufmerksamkeit")
print(SEP + "\n")

# Report speichern
report_path = BASE / "ZENODO_UPLOAD" / "LIVE_TEST_REPORT.json"
report_path.parent.mkdir(exist_ok=True)
report_path.write_text(json.dumps({
    "ts": datetime.datetime.now().isoformat(),
    "results": results,
    "ok_count": ok_count,
    "total": total,
    "fully_autonomous": ok_count == total
}, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"  Report gespeichert: {report_path.name}")
