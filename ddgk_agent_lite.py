#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  DDGK AGENT LITE — Für Pi5, Note10+, Edge Devices                 ║
║                                                                    ║
║  Minimaler REST-Agent für alle Edge-Nodes im DDGK-Netz            ║
║  Kein Start. Kein Ende. Permanent.                                 ║
║                                                                    ║
║  Endpoints:                                                        ║
║   GET  /health        → Node Status + Capabilities                ║
║   GET  /metrics       → CPU/RAM/Disk                               ║
║   POST /task          → Task empfangen und ausführen               ║
║   GET  /guardian      → Guardian Light-Version                     ║
║                                                                    ║
║  Start: python ddgk_agent_lite.py --port 8001                     ║
║  Permanent: nohup python ddgk_agent_lite.py --port 8001 &         ║
╚══════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import sys, os, json, datetime, socket, platform, threading, time
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import subprocess

sys.stdout.reconfigure(encoding='utf-8', errors='replace') if hasattr(sys.stdout, 'reconfigure') else None

PORT = 8001
for a in sys.argv:
    if a.startswith('--port='): PORT = int(a.split('=')[1])
    elif a == '--port' and sys.argv.index(a)+1 < len(sys.argv):
        PORT = int(sys.argv[sys.argv.index(a)+1])

NODE_ID   = socket.gethostname()
NODE_TYPE = "pi5" if "raspberry" in platform.machine().lower() or "aarch64" in platform.machine().lower() else "edge"
START_TS  = datetime.datetime.now()
TASKS_DONE = 0

# Capabilities erkennen
CAPS = ["guardian_lite", "heartbeat", "metrics"]
try:
    result = subprocess.run(["ollama", "list"], capture_output=True, timeout=2)
    if result.returncode == 0: CAPS.append("ollama_inference")
except: pass
try:
    import psutil; CAPS.append("psutil_metrics")
except: pass


def get_metrics() -> dict:
    m = {
        "cpu_pct": 0, "ram_total": 0, "ram_free": 0,
        "disk_free": 0, "uptime": str(datetime.datetime.now() - START_TS).split(".")[0]
    }
    try:
        import psutil
        m["cpu_pct"] = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        m["ram_total"] = round(ram.total / 1024**3, 2)
        m["ram_free"]  = round(ram.available / 1024**3, 2)
        disk = psutil.disk_usage('/')
        m["disk_free"] = round(disk.free / 1024**3, 2)
    except:
        try:
            with open('/proc/meminfo') as f:
                lines = f.read().splitlines()
            for l in lines:
                if 'MemTotal' in l:   m['ram_total'] = int(l.split()[1]) // 1024
                if 'MemAvailable' in l: m['ram_free'] = int(l.split()[1]) // 1024
        except: pass
    return m


def guardian_lite(action: str) -> dict:
    """Mini-Guardian für Edge Nodes."""
    deny = ["rm -rf", "format", "dd if=", "mkfs", "shutdown", "reboot"]
    if any(d in action.lower() for d in deny):
        return {"decision": "DENY", "score": 95}
    return {"decision": "AUTO_APPROVE", "score": 15}


class AgentHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass  # suppress logs

    def _respond(self, data: dict, code: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        global TASKS_DONE
        path = urlparse(self.path).path

        if path == "/health" or path == "/":
            self._respond({
                "status": "online",
                "node_id": NODE_ID,
                "node_type": NODE_TYPE,
                "capabilities": CAPS,
                "tasks_done": TASKS_DONE,
                "uptime": str(datetime.datetime.now() - START_TS).split(".")[0],
                "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "ddgk_version": "lite-1.0",
            })
        elif path == "/metrics":
            m = get_metrics()
            m["node_id"] = NODE_ID
            m["ts"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            self._respond(m)
        elif path == "/guardian":
            q = parse_qs(urlparse(self.path).query)
            action = q.get("action", ["test"])[0]
            result = guardian_lite(action)
            result["node_id"] = NODE_ID
            self._respond(result)
        else:
            self._respond({"error": "not found"}, 404)

    def do_POST(self):
        global TASKS_DONE
        path = urlparse(self.path).path

        if path == "/task":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
            action = body.get("action", "")
            g = guardian_lite(action)

            if g["decision"] == "DENY":
                self._respond({"status": "denied", "guardian": g, "node_id": NODE_ID})
                return

            # Einfache Task-Ausführung
            result = {"status": "executed", "action": action, "node_id": NODE_ID}
            if action == "check_disk":
                result["metrics"] = get_metrics()
            elif action == "ping":
                result["pong"] = True
            elif action.startswith("echo:"):
                result["echo"] = action[5:]

            TASKS_DONE += 1
            result["tasks_done"] = TASKS_DONE
            result["ts"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            self._respond(result)
        else:
            self._respond({"error": "not found"}, 404)


def run():
    server = HTTPServer(("0.0.0.0", PORT), AgentHandler)
    local_ip = socket.gethostbyname(socket.gethostname())
    print(f"\n  🟢 DDGK Agent Lite gestartet")
    print(f"  Node:  {NODE_ID} ({NODE_TYPE})")
    print(f"  URL:   http://{local_ip}:{PORT}/health")
    print(f"  Caps:  {', '.join(CAPS)}")
    print(f"  Permanent — CTRL+C zum Stoppen\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n  Shutdown nach {TASKS_DONE} Tasks.")


if __name__ == "__main__":
    run()
