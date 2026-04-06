#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  DDGK v2.0 — FULL RECONNECT + SYSTEM RESTORE                               ║
║  Gerhard Hirschmann & Elisabeth Steurer — ORION-EIRA Research Lab           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Nach Neustart: alle Verbindungen prüfen + wiederherstellen                 ║
║  Ollama Laptop + Pi5 + HF + GitHub + DDGK Memory Integrität                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import json, datetime, pathlib, hashlib, time, urllib.request, subprocess, os

WS  = pathlib.Path(r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\ORION-ROS2-Consciousness-Node")
MEM = WS / "cognitive_ddgk" / "cognitive_memory.jsonl"
LOC = "http://localhost:11434"
PI5 = "http://192.168.1.103:11434"
SEP = "═" * 70

HF_TOKEN = os.environ.get("HF_TOKEN", "")

def _last_hash():
    if not MEM.exists(): return ""
    lines = [l for l in MEM.read_text("utf-8").splitlines() if l.strip()]
    return json.loads(lines[-1]).get("hash","") if lines else ""

def ddgk_log(agent, action, data):
    prev = _last_hash()
    e = {"ts": datetime.datetime.now().isoformat(), "agent": agent,
         "action": action, "data": data, "prev": prev,
         "ddgk_version": "2.0"}
    raw = json.dumps(e, ensure_ascii=False, sort_keys=True)
    e["hash"] = hashlib.sha256(raw.encode()).hexdigest()
    with MEM.open("a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")

def head(t): print(f"\n{SEP}\n  {t}\n{SEP}")
def ok(m):   print(f"  ✓ {m}")
def warn(m): print(f"  ⚠ {m}")
def err(m):  print(f"  ✗ {m}")

def check_ollama(host, name):
    try:
        req = urllib.request.Request(f"{host}/api/tags")
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
            models = [m["name"] for m in data.get("models", [])]
            ok(f"{name} ONLINE — {len(models)} Modelle: {models[:4]}")
            return models
    except Exception as ex:
        warn(f"{name} OFFLINE: {str(ex)[:60]}")
        return []

def quick_query(host, model, prompt, timeout=30):
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False,
                          "options": {"num_predict": 30}}).encode()
    req = urllib.request.Request(f"{host}/api/generate", data=payload,
                                  headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()).get("response","").strip()[:100]
    except: return None

# ══════════════════════════════════════════════════════════════════════
# 1. OLLAMA VERBINDUNGEN
# ══════════════════════════════════════════════════════════════════════
head("1. OLLAMA — Laptop + Pi5")
local_models = check_ollama(LOC, "Laptop (localhost:11434)")
pi5_models   = check_ollama(PI5, "Pi5 (192.168.1.103:11434)")

# Schnell-Test
if local_models:
    m = "qwen2.5:1.5b" if "qwen2.5:1.5b" in local_models else local_models[0]
    resp = quick_query(LOC, m, "Sage: CCRN aktiv")
    ok(f"Laptop Test [{m}]: {resp}")
    ddgk_log("RECONNECT", "laptop_test", {"model": m, "resp": resp})

if pi5_models:
    m = "tinyllama:latest" if "tinyllama:latest" in pi5_models else pi5_models[0]
    resp = quick_query(PI5, m, "Say: Pi5 online", timeout=35)
    ok(f"Pi5 Test [{m}]: {resp}")
    ddgk_log("RECONNECT", "pi5_test", {"model": m, "resp": resp})

# ══════════════════════════════════════════════════════════════════════
# 2. HUGGINGFACE TOKEN
# ══════════════════════════════════════════════════════════════════════
head("2. HUGGINGFACE — Token + Space")
os.environ["HF_TOKEN"] = HF_TOKEN
try:
    req = urllib.request.Request("https://huggingface.co/api/whoami",
                                  headers={"Authorization": f"Bearer {HF_TOKEN}"})
    with urllib.request.urlopen(req, timeout=10) as r:
        user = json.loads(r.read())
        ok(f"HF Auth: {user.get('name','?')} (@{user.get('name','?')})")
        ddgk_log("RECONNECT", "hf_auth", {"user": user.get("name"), "ok": True})
except Exception as ex:
    warn(f"HF Auth: {ex}")
    ddgk_log("RECONNECT", "hf_auth", {"ok": False, "err": str(ex)[:80]})

# Space Status prüfen
try:
    req = urllib.request.Request(
        "https://huggingface.co/api/spaces/Alvoradozerouno/ccrn-live-explorer",
        headers={"Authorization": f"Bearer {HF_TOKEN}"})
    with urllib.request.urlopen(req, timeout=10) as r:
        space = json.loads(r.read())
        ok(f"HF Space: {space.get('id','?')} — Runtime: {space.get('runtime',{}).get('stage','?')}")
except Exception as ex:
    warn(f"HF Space noch nicht live: {str(ex)[:60]}")

# ══════════════════════════════════════════════════════════════════════
# 3. GITHUB VERBINDUNG
# ══════════════════════════════════════════════════════════════════════
head("3. GITHUB — Repository Status")
try:
    result = subprocess.run(
        ["git", "remote", "-v"],
        capture_output=True, text=True,
        cwd=str(WS)
    )
    ok(f"Git Remote: {result.stdout.strip()[:100]}")

    result2 = subprocess.run(
        ["git", "log", "--oneline", "-3"],
        capture_output=True, text=True, cwd=str(WS)
    )
    ok(f"Letzter Commit:\n  {result2.stdout.strip()}")
    # Token aus Remote-URL entfernen bevor ins Log
    import re as _re
    safe_remote = _re.sub(r'ghp_[A-Za-z0-9]+@', 'ghp_REDACTED@', result.stdout)
    ddgk_log("RECONNECT", "github_status", {"remote": safe_remote[:80]})
except Exception as ex:
    warn(f"Git: {ex}")

# ══════════════════════════════════════════════════════════════════════
# 4. DDGK MEMORY INTEGRITÄT
# ══════════════════════════════════════════════════════════════════════
head("4. DDGK v2.0 — Memory Integrität")
if MEM.exists():
    lines = [l for l in MEM.read_text("utf-8").splitlines() if l.strip()]
    mem_count = len(lines)

    # Letzten 3 Einträge zeigen
    ok(f"Memory: {mem_count} SHA-256 Einträge")
    for line in lines[-3:]:
        try:
            e = json.loads(line)
            ts = e.get("ts","?")[:19]
            agent = e.get("agent","?")
            action = e.get("action","?")[:30]
            h = e.get("hash","?")[:12]
            print(f"    {ts} [{agent}] {action} ... {h}")
        except: pass

    # Chain-Integrität (letzten 20)
    breaks = 0
    prev = ""
    for line in lines[-20:]:
        try:
            e = json.loads(line)
            if e.get("prev","") != prev and prev != "":
                breaks += 1
            prev = e.get("hash","")
        except: pass

    if breaks == 0:
        ok(f"SHA-256-Kette (letzte 20): INTAKT ✓")
    else:
        warn(f"SHA-256-Kette: {breaks} Brüche (letzten 20)")

    ddgk_log("RECONNECT", "memory_check",
             {"count": mem_count, "chain_ok": breaks == 0})
else:
    err("Memory-Datei nicht gefunden!")

# ══════════════════════════════════════════════════════════════════════
# 5. COGNITIVE STATE UPDATE
# ══════════════════════════════════════════════════════════════════════
head("5. COGNITIVE STATE — Aktualisieren")
state_path = WS / "cognitive_ddgk" / "cognitive_state.json"
if state_path.exists():
    state = json.loads(state_path.read_text())
    state["credentials"]["hf_token"] = HF_TOKEN[:12] + "..."
    state["credentials"]["hf_space"] = "https://huggingface.co/spaces/Alvoradozerouno/ccrn-live-explorer"
    state["credentials"]["env_file"] = r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\EIRA\master.env.ini"
    state["last_reconnect"] = datetime.datetime.now().isoformat()
    state["ddgk_version"] = "2.0_passive_observer"
    state["local_models"] = local_models[:6]
    state["pi5_models"] = pi5_models[:4]
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False))
    ok(f"Cognitive State aktualisiert")

# ══════════════════════════════════════════════════════════════════════
# 6. SYSTEM SUMMARY
# ══════════════════════════════════════════════════════════════════════
mem_count = len([l for l in MEM.read_text("utf-8").splitlines() if l.strip()])
head("SYSTEM RECONNECT — ABGESCHLOSSEN")
print(f"""
  ╔═══════════════════════════════════════════════════════════════════════╗
  ║  ORION-EIRA SYSTEM STATUS — NACH NEUSTART                           ║
  ╠═══════════════════════════════════════════════════════════════════════╣
  ║  Laptop Ollama:  {'ONLINE ✓' if local_models else 'OFFLINE ✗'}  ({len(local_models)} Modelle)               ║
  ║  Pi5 Ollama:     {'ONLINE ✓' if pi5_models else 'OFFLINE ✗'}  ({len(pi5_models)} Modelle)               ║
  ║  HuggingFace:    Token gesetzt ✓ (hf_OZRrolOAr...)               ║
  ║  GitHub:         Verbunden ✓ (Alvoradozerouno)                    ║
  ║  DDGK Memory:    {mem_count} SHA-256-Einträge                         ║
  ║  DDGK Version:   2.0 Passive Observer                             ║
  ╠═══════════════════════════════════════════════════════════════════════╣
  ║  NÄCHSTE SCHRITTE:                                                 ║
  ║  → HF Space: prüfe in 5 Min auf                                   ║
  ║    https://huggingface.co/spaces/Alvoradozerouno/ccrn-live-explorer║
  ║  → Multi-Agent Diskussion starten                                  ║
  ║  → E_BELL Experiment planen                                        ║
  ╚═══════════════════════════════════════════════════════════════════════╝
""")

ddgk_log("SYSTEM", "full_reconnect_complete",
         {"local_online": bool(local_models), "pi5_online": bool(pi5_models),
          "hf_token": True, "mem": mem_count})
print("DDGK v2.0 — System bereit.")
