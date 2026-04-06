#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  DDGK NOTE 10 AGENT — Mobile Node                                  ║
║                                                                    ║
║  Läuft auf dem Samsung Note 10 via Termux.                        ║
║  Macht das Note10 zum vollwertigen DDGK-Node.                     ║
║                                                                    ║
║  Capabilities:                                                     ║
║   • Heartbeat / Health API (Port 5001)                            ║
║   • NPU/CPU Vitality Report                                       ║
║   • Vision: IP Webcam Integration (Port 8080)                     ║
║   • Guardian Check (lokal, ohne Cloud)                            ║
║   • Task Accept + Result zurück                                    ║
║                                                                    ║
║  Starten auf Note10 (Termux):                                     ║
║    python3 ddgk_note10_agent.py                                   ║
║                                                                    ║
║  Test vom Laptop:                                                  ║
║    curl http://192.168.1.101:5001/health                          ║
╚══════════════════════════════════════════════════════════════════════╝

INSTALLATION (Termux auf Note10):
  pkg install python
  python3 -m pip install --user requests psutil
  # Optional für Vision:
  # IP Webcam App installieren (Play Store) → Port 8080 starten
  python3 ddgk_note10_agent.py
  # Bei Errno 2: siehe NOTE10_SETUP.md — oft CRLF (sed) oder nur python3 statt python
"""
from __future__ import annotations
import sys, os, json, time, datetime, socket, hashlib, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
try:
    from urllib.request import urlopen
    import urllib.request
except ImportError:
    pass

# ─── KONFIGURATION ───────────────────────────────────────────────────────────
PORT          = 5001
HOST          = "0.0.0.0"     # Alle Interfaces
NODE_NAME     = "Note10-Mobile"
NODE_TYPE     = "mobile"
WATT_LIMIT    = 5.0
VISION_PORT   = 8080           # IP Webcam App Standard-Port
VISION_HOST   = "localhost"    # Lokal auf Note10

# Guardian Rules (lokal, kein Cloud-Aufruf)
DENY_PATTERNS    = ["rm -rf", "format", "wipe", "factory_reset", "delete_all"]
REQUIRE_PATTERNS = ["email_send", "payment", "deploy"]

# ─── HEALTH CHECK HELPER ─────────────────────────────────────────────────────
def get_vitality() -> dict:
    """Misst CPU/RAM wenn psutil verfügbar (Termux: pip install psutil)."""
    try:
        import psutil
        cpu  = psutil.cpu_percent(interval=0.5)
        ram  = psutil.virtual_memory()
        batt = None
        try:
            batt = psutil.sensors_battery()
        except: pass
        return {
            "cpu_pct":  round(cpu, 1),
            "ram_used": round(ram.used / (1024**2), 1),
            "ram_total":round(ram.total / (1024**2), 1),
            "ram_pct":  round(ram.percent, 1),
            "battery":  round(batt.percent, 1) if batt else None,
            "charging": batt.power_plugged if batt else None,
            "vitality": round(max(0, 100 - cpu * 0.6 - ram.percent * 0.4), 1),
        }
    except ImportError:
        # psutil nicht installiert → Fallback
        return {"vitality": 70.0, "note": "psutil nicht installiert (pip install psutil)"}

def probe_ml_edge() -> dict:
    """Termux/Android: welche Laufzeiten fuer NPU/NNAPI/TFLite erkennbar sind (ohne Modellpfad)."""
    info: dict = {
        "tflite_runtime": False,
        "tensorflow": False,
        "tensorflow_lite": False,
    }
    try:
        import tflite_runtime.interpreter as _tfl  # noqa: F401

        info["tflite_runtime"] = True
    except ImportError:
        pass
    try:
        import tensorflow as tf

        info["tensorflow"] = True
        info["tensorflow_lite"] = hasattr(tf, "lite")
    except ImportError:
        pass
    return info


def check_vision() -> dict:
    """Prüft ob IP Webcam App auf Port 8080 läuft."""
    try:
        url = f"http://{VISION_HOST}:{VISION_PORT}/status.json"
        resp = urllib.request.urlopen(url, timeout=2)
        data = json.loads(resp.read())
        return {"available": True, "url": f"http://{VISION_HOST}:{VISION_PORT}/shot.jpg",
                "status": data}
    except Exception as e:
        return {"available": False, "note": f"IP Webcam App nicht aktiv: {e}",
                "url": f"http://{VISION_HOST}:{VISION_PORT}/shot.jpg"}

def guardian_check(action: str) -> dict:
    """Lokaler Guardian-Check ohne Cloud."""
    a = action.lower()
    if any(p in a for p in DENY_PATTERNS):
        return {"decision": "DENY", "risk_score": 95, "reason": "Destruktive Aktion erkannt"}
    if any(p in a for p in REQUIRE_PATTERNS):
        return {"decision": "REQUIRE_HUMAN", "risk_score": 70, "reason": "Externe Aktion → HITL"}
    return {"decision": "AUTO_APPROVE", "risk_score": 10, "reason": "Safe operation"}


# ─── HTTP HANDLER ─────────────────────────────────────────────────────────────
class Note10Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Kompaktes Logging
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"  [{ts}] {self.client_address[0]} {args[0]}")

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-DDGK-Node", NODE_NAME)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/") or "/"

        # GET /health — Heartbeat für Arbitrage Engine
        if path in ("/health", "/"):
            vitality = get_vitality()
            self._send_json({
                "node":      NODE_NAME,
                "type":      NODE_TYPE,
                "status":    "online",
                "watt_limit":WATT_LIMIT,
                "vitality":  vitality,
                "ml_edge":   probe_ml_edge(),
                "ts":        datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "strengths": ["vision", "npu_inference", "mobile_test", "camera"],
                "ip":        socket.gethostbyname(socket.gethostname()),
                "port":      PORT,
            })

        # GET /npu — ML/TFLite-Laufzeit-Status (kein Benchmark, keine Secrets)
        elif path == "/npu":
            self._send_json({"node": NODE_NAME, "ml_edge": probe_ml_edge()})

        # GET /vision — IP Webcam Status
        elif path == "/vision":
            self._send_json(check_vision())

        # GET /vision/snapshot — Bild-URL für Vision-Modelle
        elif path == "/vision/snapshot":
            v = check_vision()
            if v["available"]:
                self._send_json({
                    "available": True,
                    "snapshot_url": v["url"],
                    "note": "Bild direkt abrufbar: GET " + v["url"]
                })
            else:
                self._send_json({"available": False, "setup": "IP Webcam App starten"}, 503)

        # GET /status — Vollständiger Node-Status
        elif path == "/status":
            vitality = get_vitality()
            vision   = check_vision()
            self._send_json({
                "node":      NODE_NAME,
                "type":      NODE_TYPE,
                "watt_limit":WATT_LIMIT,
                "vitality":  vitality,
                "vision":    vision,
                "guardian":  "active",
                "strengths": ["vision", "npu_inference", "mobile_test", "camera"],
                "endpoints": ["/health", "/status", "/npu", "/vision", "/task", "/guardian"],
                "ts":        datetime.datetime.now(datetime.timezone.utc).isoformat(),
            })

        else:
            self._send_json({"error": f"Unknown path: {path}"}, 404)

    def do_POST(self):
        parsed   = urlparse(self.path)
        path     = parsed.path.rstrip("/")
        length   = int(self.headers.get("Content-Length", 0))
        body     = json.loads(self.rfile.read(length)) if length else {}

        # POST /task — Task annehmen (von Arbitrage Engine)
        if path == "/task":
            task_type = body.get("task_type", "unknown")
            payload   = body.get("payload", {})

            start = time.perf_counter()

            # Task-Ausführung basierend auf Typ
            if task_type == "vision_analysis":
                v = check_vision()
                result = {
                    "task_type": task_type,
                    "vision_available": v["available"],
                    "snapshot_url": v.get("url"),
                    "note": "Vision-Analyse bereit" if v["available"]
                            else "IP Webcam App starten für Kamera-Zugriff"
                }
            elif task_type == "mobile_testing":
                result = {
                    "task_type": task_type,
                    "vitality":  get_vitality(),
                    "screen_res": "2280x1080",   # Note10 Standard
                    "note": "Mobile UI-Test bereit"
                }
            elif task_type == "guardian_check":
                action = body.get("action", payload.get("action", ""))
                result = guardian_check(action)
            else:
                result = {
                    "task_type": task_type,
                    "status": "accepted",
                    "vitality": get_vitality(),
                }

            ms = (time.perf_counter() - start) * 1000
            result["latency_ms"]  = round(ms, 2)
            result["executed_by"] = NODE_NAME
            result["ts"]          = datetime.datetime.now(datetime.timezone.utc).isoformat()

            # SHA-Proof
            proof_str = json.dumps(result, sort_keys=True)
            result["chain_hash"] = hashlib.sha256(proof_str.encode()).hexdigest()[:16]

            self._send_json(result)

        # POST /guardian — Guardian-Check
        elif path == "/guardian":
            action = body.get("action", "")
            result = guardian_check(action)
            result["node"] = NODE_NAME
            result["ts"]   = datetime.datetime.now(datetime.timezone.utc).isoformat()
            self._send_json(result)

        else:
            self._send_json({"error": f"Unknown POST path: {path}"}, 404)


# ─── SERVER START ─────────────────────────────────────────────────────────────
def main():
    # IP-Adresse ermitteln
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "127.0.0.1"

    print(f"\n  📱 DDGK NOTE 10 AGENT")
    print(f"  " + "="*45)
    print(f"  Node:    {NODE_NAME}")
    print(f"  IP:      {local_ip}:{PORT}")
    print(f"  Watt:    max {WATT_LIMIT}W")
    print()

    # Vitality Check
    vitality = get_vitality()
    print(f"  Vitalität: {vitality.get('vitality', '?')}%")
    if "cpu_pct" in vitality:
        print(f"  CPU:       {vitality['cpu_pct']}%")
        print(f"  RAM:       {vitality['ram_pct']}%")
    if vitality.get("battery"):
        plug = "🔌" if vitality.get("charging") else "🔋"
        print(f"  Akku:      {plug} {vitality['battery']}%")

    # Vision Check
    vision = check_vision()
    v_status = "✅ BEREIT" if vision["available"] else "⚠️ IP Webcam App starten"
    print(f"  Vision:    {v_status}")
    print()
    print(f"  Endpoints:")
    print(f"    GET  http://{local_ip}:{PORT}/health")
    print(f"    GET  http://{local_ip}:{PORT}/status")
    print(f"    GET  http://{local_ip}:{PORT}/npu")
    print(f"    GET  http://{local_ip}:{PORT}/vision")
    print(f"    POST http://{local_ip}:{PORT}/task")
    print(f"    POST http://{local_ip}:{PORT}/guardian")
    print()
    print(f"  📋 Laptop: ddgk_arbitrage.py → Note10 auf {local_ip}:5001 eintragen!")
    print()
    print(f"  [CTRL+C zum Beenden]")
    print(f"  " + "="*45)

    server = HTTPServer((HOST, PORT), Note10Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  [NOTE10] Agent gestoppt.")
        server.server_close()


if __name__ == "__main__":
    main()
