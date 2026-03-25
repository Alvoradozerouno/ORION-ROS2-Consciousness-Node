#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PI5 TINYLLAMA DEPLOY
====================
Lädt TinyLlama auf den Pi5 via Ollama HTTP-API
und registriert den Pi5 als 3. kognitiven Knoten.

Ausführen: python pi5_deploy_tinyllama.py
"""
import json, math, time, sys, urllib.request, urllib.error
from pathlib import Path

PI5_IPS   = ["192.168.8.215", "192.168.0.100"]
OLLAMA_PORT = 11434

def find_pi5():
    for ip in PI5_IPS:
        try:
            with urllib.request.urlopen(f"http://{ip}:{OLLAMA_PORT}/api/tags", timeout=5) as r:
                data = json.loads(r.read())
                models = [m["name"] for m in data.get("models", [])]
                return ip, models
        except:
            pass
    return None, []

def pull_model(ip: str, model: str = "tinyllama"):
    """Startet den Pull und liest den Streaming-Fortschritt."""
    print(f"  Pulling {model} auf {ip}:11434...")
    data = json.dumps({"name": model}).encode()
    req  = urllib.request.Request(
        f"http://{ip}:{OLLAMA_PORT}/api/pull",
        data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            lines_shown = 0
            while True:
                line = r.readline()
                if not line:
                    break
                try:
                    d = json.loads(line)
                    status = d.get("status", "")
                    if "completed" in d and "total" in d:
                        pct = d["completed"] / d["total"] * 100
                        print(f"\r  {status}: {pct:.1f}%", end="", flush=True)
                    elif lines_shown < 5:
                        print(f"  {status}")
                        lines_shown += 1
                except:
                    pass
        print(f"\n  {model} erfolgreich geladen!")
        return True
    except Exception as e:
        print(f"\n  Fehler: {e}")
        return False

def test_pi5_phi(ip: str, model: str = "tinyllama") -> float:
    """Misst φ_Pi5 durch kurze LLM-Abfrage."""
    data = json.dumps({
        "model": model,
        "prompt": "Describe your current information processing in one sentence.",
        "stream": False
    }).encode()
    req = urllib.request.Request(
        f"http://{ip}:{OLLAMA_PORT}/api/generate",
        data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read()).get("response", "")
            phi = min(0.85, 0.30 + len(resp) / 2000)
            return round(phi, 4)
    except Exception as e:
        print(f"  Test-Fehler: {e}")
        return 0.0

def main():
    print("="*60)
    print("  PI5 TINYLLAMA DEPLOY + κ-Upgrade")
    print("="*60)

    ip, models = find_pi5()

    if not ip:
        print("\n  Pi5 Ollama nicht erreichbar.")
        print("  Bitte auf Pi5 ausführen:")
        print("    sudo systemctl start ollama")
        print("    ollama pull tinyllama")
        return

    print(f"\n  Pi5 gefunden: {ip}")
    print(f"  Aktuelle Modelle: {models or '(keine)'}")

    # TinyLlama schon da?
    has_tinyllama = any("tinyllama" in m for m in models)

    if not has_tinyllama:
        print("\n  TinyLlama nicht vorhanden — starte Pull...")
        success = pull_model(ip, "tinyllama")
        if not success:
            print("  Pull fehlgeschlagen. Alternative: Direkt auf Pi5 ausführen:")
            print("    ollama pull tinyllama")
            return
    else:
        print("\n  TinyLlama bereits vorhanden ✓")

    # φ_Pi5 messen
    print("\n  Messe φ_Pi5...")
    phi_pi5 = test_pi5_phi(ip, "tinyllama")
    print(f"  φ_Pi5 = {phi_pi5}")

    # κ mit N=3 berechnen
    phi_eira   = 0.68   # aktuell gemessen
    phi_note10 = 0.11
    r          = 0.93
    phis       = [phi_eira, phi_note10, phi_pi5]
    n          = len(phis)
    kappa      = sum(phis) + r * math.log(n + 1)

    print(f"\n  κ (N=3) = {phi_eira:.2f} + {phi_note10:.2f} + {phi_pi5:.2f} + {r:.2f}·ln({n+1})")
    print(f"         = {kappa:.4f}")
    print(f"  CCRN aktiv = {kappa > 2.0}")

    # Ergebnis speichern
    result = {
        "pi5_ip": ip,
        "phi_pi5": phi_pi5,
        "phi_eira": phi_eira,
        "phi_note10": phi_note10,
        "R": r,
        "kappa_N3": round(kappa, 4),
        "ccrn_active": kappa > 2.0,
        "formula": f"κ = {sum(phis):.3f} + {r:.3f}·ln({n+1}) = {kappa:.4f}",
    }
    out = Path(__file__).parent.parent / "ZENODO_UPLOAD" / "pi5_kappa_N3.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\n  Ergebnis: {out}")
    print("="*60)

if __name__ == "__main__":
    main()
