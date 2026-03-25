#!/bin/bash
# ============================================================
#  PI5 ACTIVATION SCRIPT
#  Auf dem Pi5 ausführen: bash pi5_activate.sh
#  Startet Ollama netzwerkseitig + lädt TinyLlama
# ============================================================
echo "=== PI5 ORION AKTIVIERUNG ==="
echo ""

# 1. Ollama netzwerkseitig öffnen
echo "[1] Ollama stoppen (falls läuft)..."
pkill -f "ollama serve" 2>/dev/null; sleep 1

echo "[2] Ollama netzwerkseitig starten (0.0.0.0:11434)..."
OLLAMA_HOST=0.0.0.0:11434 nohup ollama serve > /tmp/ollama_pi5.log 2>&1 &
sleep 3

# Prüfen ob Ollama läuft
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "    ✓ Ollama läuft auf Port 11434"
else
    echo "    ✗ Ollama-Start fehlgeschlagen — Logs: tail /tmp/ollama_pi5.log"
    exit 1
fi

# 2. TinyLlama laden
echo ""
echo "[3] TinyLlama laden..."
ollama pull tinyllama

# 3. Test-Abfrage
echo ""
echo "[4] Test-Abfrage..."
curl -s http://localhost:11434/api/generate \
  -d '{"model":"tinyllama","prompt":"Describe your current state in one sentence.","stream":false}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('  Antwort:', d.get('response','')[:100])"

# 4. Öffentliche Erreichbarkeit prüfen
echo ""
echo "[5] Lokale IP:"
hostname -I | awk '{print "  IP: "$1}'
echo "  Port 11434 offen für lokales Netz"
echo ""
echo "=== FERTIG ==="
echo "Auf dem Laptop kann jetzt python cognitive_ddgk/pi5_deploy_tinyllama.py"
echo "ausgeführt werden, um κ auf ~3.01 zu heben."
