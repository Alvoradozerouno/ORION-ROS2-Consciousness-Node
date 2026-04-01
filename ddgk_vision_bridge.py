#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  DDGK VISION BRIDGE — Note10 Kamera → Ollama → Text               ║
║                                                                    ║
║  Idee: Note10 vor Bildschirm stellen → KI "sieht" den Screen      ║
║                                                                    ║
║  Ablauf:                                                           ║
║   1. Note10 Kamera (IP Webcam App, Port 8080) → JPEG              ║
║   2. Laptop holt das Bild per HTTP                                 ║
║   3. Bild → Ollama Vision (llava / llama3.2-vision)               ║
║   4. Ollama beschreibt was sichtbar ist → Text                     ║
║   5. Text → DDGK Audit-Log + zurück in Chat                       ║
║                                                                    ║
║  Was das BEDEUTET:                                                 ║
║   → Das System kann den physischen Bildschirm "lesen"             ║
║   → Formulare erkennen, Status prüfen, Dashboard lesen            ║
║   → Vision-basierter Feedback-Loop ohne Cloud                     ║
║                                                                    ║
║  Starten:                                                         ║
║    python ddgk_vision_bridge.py                                   ║
║    python ddgk_vision_bridge.py --watch   (Live-Loop)             ║
╚══════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import sys, os, json, time, base64, datetime, hashlib, argparse
from pathlib import Path
from urllib import request as urllib_request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE        = Path(__file__).parent
VISION_LOG  = BASE / "cognitive_ddgk" / "vision_log.jsonl"
VISION_LOG.parent.mkdir(exist_ok=True)

# ─── KONFIGURATION ───────────────────────────────────────────────────────────
NOTE10_IP      = "192.168.1.101"    # ← Note10-IP (in Termux: ip addr show wlan0)
NOTE10_PORT    = 8080               # IP Webcam App Standard
OLLAMA_HOST    = "localhost"
OLLAMA_PORT    = 11434
VISION_MODEL   = "llava"           # oder "llama3.2-vision" oder "llava:13b"
WATCH_INTERVAL = 10                 # Sekunden zwischen Aufnahmen im --watch Modus


def get_snapshot(note10_ip: str = NOTE10_IP, port: int = NOTE10_PORT) -> bytes | None:
    """Holt ein JPEG von der Note10 IP Webcam App."""
    url = f"http://{note10_ip}:{port}/shot.jpg"
    try:
        req = urllib_request.Request(url, headers={"User-Agent": "DDGK/2.0"})
        resp = urllib_request.urlopen(req, timeout=5)
        data = resp.read()
        print(f"  📷 Snapshot: {len(data)//1024}KB von {url}")
        return data
    except Exception as e:
        print(f"  ❌ Kamera nicht erreichbar: {e}")
        print(f"  ℹ️  Note10: IP Webcam App starten → Port 8080 → 'Server starten'")
        return None


def ask_vision(image_bytes: bytes, prompt: str,
               model: str = VISION_MODEL) -> str | None:
    """Sendet Bild + Prompt an Ollama Vision-Modell."""
    img_b64 = base64.b64encode(image_bytes).decode()

    payload = json.dumps({
        "model":  model,
        "prompt": prompt,
        "images": [img_b64],
        "stream": False,
        "options": {"temperature": 0.1}  # Deterministisch
    }).encode("utf-8")

    url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/generate"
    try:
        req = urllib_request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"}
        )
        resp = urllib_request.urlopen(req, timeout=60)
        result = json.loads(resp.read())
        return result.get("response", "").strip()
    except Exception as e:
        print(f"  ❌ Ollama nicht erreichbar: {e}")
        print(f"  ℹ️  Ollama starten: ollama serve")
        print(f"  ℹ️  Modell laden: ollama pull {model}")
        return None


def log_vision(prompt: str, response: str, img_bytes: bytes, note10_ip: str):
    """Speichert Vision-Ergebnis im DDGK Audit-Log."""
    img_hash = hashlib.md5(img_bytes).hexdigest()[:12]
    entry = {
        "ts":       datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source":   f"http://{note10_ip}:{NOTE10_PORT}",
        "prompt":   prompt[:200],
        "response": response[:1000],
        "img_hash": img_hash,
        "model":    VISION_MODEL,
    }
    with VISION_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return img_hash


def analyze_screen(note10_ip: str = NOTE10_IP,
                   custom_prompt: str = None) -> dict:
    """
    Komplette Pipeline: Note10 → Snapshot → Ollama → Ergebnis.
    
    Standard-Prompts für DDGK Use Cases:
    - Was ist auf dem Bildschirm sichtbar?
    - Gibt es Fehlermeldungen?
    - Welcher DDGK-Status wird angezeigt?
    """
    prompt = custom_prompt or (
        "Beschreibe präzise was auf dem Laptop-Bildschirm sichtbar ist. "
        "Fokus auf: Text, Code, Fehlermeldungen, Status-Anzeigen, Dashboard-Werte. "
        "Antworte auf Deutsch, kurz und strukturiert."
    )

    print(f"\n  🔭 DDGK VISION BRIDGE")
    print(f"  " + "="*48)
    print(f"  Note10:  http://{note10_ip}:{NOTE10_PORT}")
    print(f"  Ollama:  http://{OLLAMA_HOST}:{OLLAMA_PORT}")
    print(f"  Modell:  {VISION_MODEL}")
    print(f"  Prompt:  {prompt[:60]}...")
    print()

    # 1. Snapshot holen
    img = get_snapshot(note10_ip)
    if not img:
        return {"error": "no_snapshot", "note10_ip": note10_ip}

    # 2. Vision-Analyse
    print(f"  🧠 Analysiere mit {VISION_MODEL}...")
    start = time.perf_counter()
    response = ask_vision(img, prompt)
    ms = (time.perf_counter() - start) * 1000

    if not response:
        return {"error": "no_vision_response", "img_bytes": len(img)}

    # 3. Log
    img_hash = log_vision(prompt, response, img, note10_ip)

    print(f"\n  ─── VISION ANTWORT ({ms:.0f}ms) ────────────────────────")
    print()
    for line in response.split("\n"):
        print(f"  {line}")
    print()
    print(f"  Bild-Hash: {img_hash}")
    print(f"  Log: {VISION_LOG.name}")

    return {
        "response": response,
        "img_hash": img_hash,
        "latency_ms": round(ms),
        "model": VISION_MODEL,
    }


def watch_mode(note10_ip: str = NOTE10_IP, interval: int = WATCH_INTERVAL):
    """
    Live-Loop: Alle N Sekunden Bildschirm analysieren.
    Ideal für autonomes Monitoring oder Demo.
    """
    print(f"\n  👁️  DDGK VISION WATCH — alle {interval}s")
    print(f"  Note10: {note10_ip}:{NOTE10_PORT}")
    print(f"  [CTRL+C zum Stoppen]")
    print()

    count = 0
    try:
        while True:
            count += 1
            print(f"\n  [Aufnahme #{count} — {datetime.datetime.now().strftime('%H:%M:%S')}]")
            result = analyze_screen(note10_ip)
            if "error" in result:
                print(f"  ⚠️  Fehler: {result['error']} — warte {interval}s...")
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n  Vision Watch gestoppt. {count} Aufnahmen gemacht.")
        print(f"  Log: {VISION_LOG}")


# ─── OLLAMA MODELL CHECK ─────────────────────────────────────────────────────
def check_ollama_models() -> list[str]:
    """Prüft welche Vision-Modelle in Ollama verfügbar sind."""
    try:
        url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/tags"
        resp = urllib_request.urlopen(url, timeout=3)
        data = json.loads(resp.read())
        models = [m["name"] for m in data.get("models", [])]
        vision_models = [m for m in models
                        if any(v in m.lower() for v in ["llava", "vision", "bakllava"])]
        return vision_models
    except:
        return []


# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DDGK Vision Bridge")
    parser.add_argument("--note10",  default=NOTE10_IP,
                        help=f"Note10 IP (default: {NOTE10_IP})")
    parser.add_argument("--watch",   action="store_true",
                        help="Live-Monitoring Modus")
    parser.add_argument("--interval",type=int, default=WATCH_INTERVAL,
                        help=f"Watch-Intervall in Sekunden (default: {WATCH_INTERVAL})")
    parser.add_argument("--prompt",  type=str, default=None,
                        help="Eigener Vision-Prompt")
    parser.add_argument("--model",   default=VISION_MODEL,
                        help=f"Ollama Modell (default: {VISION_MODEL})")
    args = parser.parse_args()

    VISION_MODEL = args.model

    # Ollama Vision-Modelle prüfen
    models = check_ollama_models()
    if models:
        print(f"\n  ✅ Ollama Vision-Modelle verfügbar: {', '.join(models)}")
        if args.model not in models and models:
            print(f"  ℹ️  Verwende: {models[0]}")
            VISION_MODEL = models[0]
    else:
        print(f"\n  ⚠️  Kein Ollama Vision-Modell gefunden.")
        print(f"  Installieren: ollama pull llava")
        print(f"  Oder:        ollama pull llama3.2-vision")
        print()

    if args.watch:
        watch_mode(args.note10, args.interval)
    else:
        analyze_screen(args.note10, args.prompt)
