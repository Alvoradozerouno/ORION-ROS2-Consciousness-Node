#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  DDGK LIVE-DASHBOARD — HTTP Server                                  ║
║  Zeigt: κ_CCRN · Decision Chain · Memory · Tools · Agenten         ║
║  Auto-Refresh alle 5 Sekunden                                       ║
╚══════════════════════════════════════════════════════════════════════╝
Start: python ddgk_dashboard.py
Öffne: http://localhost:7860
"""

import json, pathlib, datetime, http.server, threading, urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

BASE = pathlib.Path(__file__).parent

HTML = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="5">
<title>DDGK Live Dashboard</title>
<style>
  :root { --bg:#0d1117;--card:#161b22;--border:#30363d;--text:#e6edf3;
          --green:#3fb950;--yellow:#d29922;--red:#f85149;--blue:#58a6ff;
          --purple:#bc8cff;--cyan:#79c0ff; }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:var(--bg); color:var(--text); font-family:'Segoe UI',monospace;
         font-size:13px; padding:16px; }
  h1 { color:var(--cyan); font-size:1.4em; margin-bottom:4px; }
  .subtitle { color:#7d8590; margin-bottom:16px; font-size:.85em; }
  .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:12px; }
  .card { background:var(--card); border:1px solid var(--border); border-radius:8px;
          padding:14px; }
  .card h2 { font-size:.9em; color:var(--blue); margin-bottom:10px; letter-spacing:.05em; }
  .kappa-big { font-size:2.8em; font-weight:700; color:var(--green); }
  .kappa-bad { color:var(--red); }
  .kappa-warn { color:var(--yellow); }
  .row { display:flex; justify-content:space-between; padding:3px 0;
         border-bottom:1px solid #21262d; }
  .row:last-child { border-bottom:none; }
  .label { color:#7d8590; }
  .val { color:var(--text); font-family:monospace; }
  .ok { color:var(--green); }
  .warn { color:var(--yellow); }
  .err { color:var(--red); }
  .badge { display:inline-block; padding:2px 8px; border-radius:12px;
           font-size:.75em; font-weight:600; }
  .badge-low { background:#1a472a; color:#3fb950; }
  .badge-med { background:#3d2c00; color:#d29922; }
  .badge-hi  { background:#3d0000; color:#f85149; }
  .badge-ok  { background:#1a472a; color:#3fb950; }
  .badge-denied { background:#3d0000; color:#f85149; }
  .badge-hitl { background:#3d2c00; color:#d29922; }
  .dec-row { padding:6px 0; border-bottom:1px solid #21262d; font-size:.82em; }
  .dec-id { color:#7d8590; font-size:.75em; font-family:monospace; }
  .dec-goal { color:var(--cyan); margin:2px 0; }
  .dec-reason { color:#8b949e; font-style:italic; }
  .footer { margin-top:16px; color:#7d8590; font-size:.8em; text-align:center; }
  .chain-ok { color:var(--green); }
  .chain-bad { color:var(--red); }
  .tool-row { display:flex; align-items:center; gap:8px; padding:4px 0;
              border-bottom:1px solid #21262d; }
  .tool-row:last-child { border-bottom:none; }
  .tool-name { color:var(--cyan); font-family:monospace; flex:1; }
  .pulse { animation:pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.5} }
</style>
</head>
<body>
<h1>🧠 DDGK Live Dashboard — ORION/CCRN</h1>
<div class="subtitle">Auto-Refresh alle 5s · {ts}</div>

<div class="grid">

<!-- κ CCRN -->
<div class="card">
  <h2>⚡ κ_CCRN — Kohaerenz-Index</h2>
  <div class="kappa-big {kappa_class}">{kappa}</div>
  <div style="margin:8px 0 12px;color:#7d8590;font-size:.85em">{kappa_formula}</div>
  <div class="row"><span class="label">CCRN aktiv</span><span class="val">{ccrn}</span></div>
  <div class="row"><span class="label">Stop-Flag</span><span class="val">{stop_flag}</span></div>
  <div class="row"><span class="label">Kognitions-Zyklus</span><span class="val">{cycle}</span></div>
  <div class="row"><span class="label">Schwellwert</span><span class="val">3.0 (NORMAL)</span></div>
</div>

<!-- MEMORY STATS -->
<div class="card">
  <h2>📜 Memory-Statistiken (SHA-256 Ketten)</h2>
  {memory_rows}
</div>

<!-- DECISION TRACE -->
<div class="card" style="grid-column:span 2">
  <h2>🔍 Decision Trace — letzte 5 Entscheidungen <span class="{chain_class}">{chain_status}</span></h2>
  {decision_rows}
</div>

<!-- TOOL REGISTRY -->
<div class="card">
  <h2>🔧 HyperAgent Tool-Registry</h2>
  {tool_rows}
</div>

<!-- SYSTEM STATUS -->
<div class="card">
  <h2>🔌 System-Status</h2>
  {system_rows}
</div>

</div>
<div class="footer">ORION-CCRN v2.0 · DDGK Governance · XAI Decision Trace · IEC 61508</div>
</body>
</html>"""


def _badge(risk):
    if risk == "LOW":    return f'<span class="badge badge-low">LOW</span>'
    if risk == "MEDIUM": return f'<span class="badge badge-med">MED</span>'
    return f'<span class="badge badge-hi">HIGH</span>'

def _val_badge(v):
    if v == "passed":  return f'<span class="badge badge-ok">passed</span>'
    if v == "denied":  return f'<span class="badge badge-denied">denied</span>'
    return f'<span class="badge badge-hitl">{v}</span>'


def build_html() -> str:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── κ / Cognitive State ──────────────────────────────────────────────────
    cs_file = BASE / "cognitive_ddgk" / "cognitive_state.json"
    kappa = "N/A"; ccrn = "?"; stop_flag = "?"; cycle = "?"; formula = "?"
    kappa_class = ""
    if cs_file.exists():
        try:
            st = json.loads(cs_file.read_text("utf-8"))
            kv = st.get("kappa_current", 0)
            kappa = f"{kv:.4f}"
            kappa_class = "ok" if kv >= 3.0 else ("kappa-warn" if kv >= 2.0 else "kappa-bad")
            ccrn = "✅ AKTIV" if st.get("ccrn_active") else "❌ INAKTIV"
            stop_flag = "🔴 TRUE" if st.get("stop_flag") else "✅ FALSE"
            cycle = str(st.get("cognitive_cycle","?"))
            formula = st.get("kappa_formula", f"κ = 2.060 + 0.930·ln(N)")
        except: pass

    # ── Memory Stats ─────────────────────────────────────────────────────────
    mem_files = {
        "Cognitive Memory": "cognitive_ddgk/cognitive_memory.jsonl",
        "Loop Memory":      "cognitive_ddgk/autonomous_loop_memory.jsonl",
        "HyperAgent Memory":"cognitive_ddgk/hyper_agent_memory.jsonl",
        "Nuclear Audit":    "cognitive_ddgk/nuclear_audit_chain.jsonl",
        "Decision Trace":   "cognitive_ddgk/decision_trace.jsonl",
    }
    mem_rows = ""
    total_entries = 0
    for label, rel in mem_files.items():
        p = BASE / rel
        if p.exists():
            c = sum(1 for l in p.read_text("utf-8", errors="replace").splitlines() if l.strip())
            total_entries += c
            mem_rows += f'<div class="row"><span class="label">{label}</span><span class="val ok">{c} Einträge</span></div>'
        else:
            mem_rows += f'<div class="row"><span class="label">{label}</span><span class="val warn">fehlt</span></div>'
    mem_rows += f'<div class="row" style="margin-top:4px"><span class="label"><b>Gesamt</b></span><span class="val"><b>{total_entries}</b></span></div>'

    # ── Decision Trace ───────────────────────────────────────────────────────
    dt_file = BASE / "cognitive_ddgk" / "decision_trace.jsonl"
    decision_rows = "<div style='color:#7d8590'>Noch keine Entscheidungen</div>"
    chain_status = "keine Daten"; chain_class = "warn"
    if dt_file.exists():
        lines = [l for l in dt_file.read_text("utf-8", errors="replace").splitlines() if l.strip()]
        if lines:
            records = []
            for l in lines:
                try: records.append(json.loads(l))
                except: pass
            # Chain verify
            broken = False
            for i in range(1, len(records)):
                if records[i-1].get("decision_id") != records[i].get("prev_decision_id"):
                    broken = True; break
            chain_class = "chain-ok" if not broken else "chain-bad"
            chain_status = f"✅ integer ({len(records)} Einträge)" if not broken else f"❌ BROKEN bei #{i}"

            decision_rows = ""
            for r in records[-5:]:
                ts_s = r.get("timestamp","?")[:19]
                did  = r.get("decision_id","?")[:20]
                goal = r.get("goal_representation","?")[:70]
                reas = r.get("reasoning_trace","?")[:90]
                act  = r.get("selected_action","?")
                alts = ", ".join(r.get("alternatives_considered",[])[:3])
                vres = r.get("validation_result","?")
                risk = r.get("risk_level","?")
                decision_rows += f"""
<div class="dec-row">
  <div class="dec-id">{did}... · {ts_s} · Agent: {r.get("agent_id","?")}</div>
  <div class="dec-goal">🎯 {goal}</div>
  <div class="dec-reason">💭 {reas}...</div>
  <div style="margin-top:4px;display:flex;gap:8px;flex-wrap:wrap">
    <span>→ <b style="color:var(--cyan)">{act}</b></span>
    {_badge(risk)} {_val_badge(vres)}
    <span style="color:#7d8590">Alt: {alts or 'keine'}</span>
  </div>
</div>"""

    # ── Tool Registry ────────────────────────────────────────────────────────
    reg_file = BASE / "cognitive_ddgk" / "hyper_tool_registry.json"
    tool_rows = "<div style='color:#7d8590'>Keine Tools registriert</div>"
    if reg_file.exists():
        try:
            reg = json.loads(reg_file.read_text("utf-8"))
            tools = list(reg.get("tools",{}).values())
            if tools:
                tool_rows = ""
                for t in tools:
                    val_icon = "✅" if t.get("validated") else "⚠️"
                    runs = t.get("run_count",0)
                    tool_rows += f"""<div class="tool-row">
                      <span class="tool-name">{t['name']}</span>
                      {_badge(t.get('risk_level','?'))}
                      <span>{val_icon}</span>
                      <span style="color:#7d8590">{runs}x</span>
                    </div>"""
        except: pass

    # ── System Status ────────────────────────────────────────────────────────
    import urllib.request as ur
    ollama_ok = False
    try:
        ur.urlopen("http://127.0.0.1:11434/api/tags", timeout=1)
        ollama_ok = True
    except: pass
    pi5_ok = False
    try:
        ur.urlopen("http://192.168.1.103:11434/api/tags", timeout=1)
        pi5_ok = True
    except: pass

    py_files = list(BASE.glob("*.py"))
    md_files = list(BASE.glob("*.md"))
    zenodo_files = list((BASE / "ZENODO_UPLOAD").glob("*.json")) if (BASE/"ZENODO_UPLOAD").exists() else []

    system_rows = f"""
<div class="row"><span class="label">Ollama (lokal)</span>
  <span class="val {'ok' if ollama_ok else 'err'}">{'✅ ONLINE' if ollama_ok else '❌ OFFLINE'}</span></div>
<div class="row"><span class="label">Pi5/NEXUS</span>
  <span class="val {'ok' if pi5_ok else 'warn'}">{'✅ ONLINE' if pi5_ok else '⚠️ OFFLINE'}</span></div>
<div class="row"><span class="label">Python-Dateien</span><span class="val">{len(py_files)}</span></div>
<div class="row"><span class="label">Markdown-Docs</span><span class="val">{len(md_files)}</span></div>
<div class="row"><span class="label">Zenodo-Reports</span><span class="val">{len(zenodo_files)}</span></div>
<div class="row"><span class="label">HyperTools</span>
  <span class="val">{len(list((BASE/'hyper_tools').glob('*.py')) if (BASE/'hyper_tools').exists() else [])}</span></div>
"""

    # str.replace statt .format() — damit CSS-Variablen (--bg etc.) nicht kollidieren
    replacements = {
        "{ts}": ts, "{kappa}": kappa, "{kappa_class}": kappa_class,
        "{kappa_formula}": formula, "{ccrn}": ccrn, "{stop_flag}": stop_flag,
        "{cycle}": cycle, "{memory_rows}": mem_rows,
        "{decision_rows}": decision_rows, "{chain_status}": chain_status,
        "{chain_class}": chain_class, "{tool_rows}": tool_rows,
        "{system_rows}": system_rows,
    }
    result = HTML
    for k, v in replacements.items():
        result = result.replace(k, str(v))
    return result


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            html = build_html().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
        elif self.path == "/api/status":
            # JSON API für externe Tools
            cs = BASE / "cognitive_ddgk" / "cognitive_state.json"
            data = json.loads(cs.read_text("utf-8")) if cs.exists() else {}
            dt = BASE / "cognitive_ddgk" / "decision_trace.jsonl"
            decisions = sum(1 for l in dt.read_text("utf-8",errors="replace").splitlines() if l.strip()) if dt.exists() else 0
            resp = json.dumps({
                "kappa": data.get("kappa_current"),
                "ccrn_active": data.get("ccrn_active"),
                "stop_flag": data.get("stop_flag"),
                "decisions": decisions,
                "ts": datetime.datetime.now().isoformat()
            }, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.end_headers()
            self.wfile.write(resp)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *a): pass   # Kein Log-Spam


if __name__ == "__main__":
    import argparse, webbrowser
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=7860)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()

    server = HTTPServer(("0.0.0.0", args.port), DashboardHandler)
    url = f"http://localhost:{args.port}"
    print(f"\n  🖥️  DDGK Dashboard gestartet")
    print(f"  URL : {url}")
    print(f"  API : {url}/api/status")
    print(f"  Stop: Ctrl+C\n")
    if not args.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Dashboard gestoppt.")
