# 📱 Note10 → DDGK Node — Setup-Anleitung

**Ziel:** Note10 als vollwertigen DDGK-Node einbinden (Vision + Guardian + Vitality)

---

## ⚡ SCHNELLSTART (5 Minuten)

### 1. Termux installieren
```
Play Store → "Termux" (von F-Droid Team, nicht Termux legacy!)
Oder: f-droid.org → Termux
```

### 2. Python + Abhängigkeiten
```bash
# In Termux eingeben:
pkg update && pkg upgrade -y
pkg install python python-pip -y
pip install requests psutil
```

### 3. Agent-Script kopieren
```bash
# Option A: Via Git (wenn WLAN mit Laptop im selben Netz)
git clone https://github.com/Alvoradozerouno/ORION-ROS2-Consciousness-Node
cd ORION-ROS2-Consciousness-Node
python ddgk_note10_agent.py

# Option B: Via USB (adb)
adb push ddgk_note10_agent.py /data/data/com.termux/files/home/
# In Termux: python ddgk_note10_agent.py
```

### 4. Agent starten
```bash
python ddgk_note10_agent.py
```
**Ausgabe:**
```
  📱 DDGK NOTE 10 AGENT
  =============================================
  Node:    Note10-Mobile
  IP:      192.168.1.101:5001
  Watt:    max 5.0W
  
  Vitalität: 78.5%
  CPU:       25.0%
  RAM:       65.0%
  Akku:      🔋 82%
  Vision:    ⚠️ IP Webcam App starten
  
  Endpoints:
    GET  http://192.168.1.101:5001/health
    GET  http://192.168.1.101:5001/status
    POST http://192.168.1.101:5001/task
```

### 5. Vom Laptop testen
```bash
# Heartbeat:
curl http://192.168.1.101:5001/health

# Erwartete Antwort:
{
  "node": "Note10-Mobile",
  "type": "mobile",
  "status": "online",
  "vitality": {"vitality": 78.5, "cpu_pct": 25.0, ...}
}

# Arbitrage Engine neu starten → Note10 sollte ONLINE sein:
python ddgk_arbitrage.py
```

---

## 📷 VISION AKTIVIEREN (Optional, aber MÄCHTIG)

### 1. IP Webcam App installieren
```
Play Store → "IP Webcam" (von Pavel Khlebovich)
Kostenlos, kein Account nötig
```

### 2. IP Webcam starten
```
App öffnen → "Server starten" (unten)
Standard Port: 8080
→ Zeigt: "http://192.168.1.101:8080"
```

### 3. Vision testen
```bash
# Vom Laptop:
curl http://192.168.1.101:5001/vision
# → {"available": true, "snapshot_url": "http://localhost:8080/shot.jpg"}

# Snapshot direkt (erstes Bild):
curl http://192.168.1.101:8080/shot.jpg --output test.jpg
```

### 4. Vision in DDGK nutzen
```python
# Auf Laptop: Bild analysieren mit Ollama
import requests, base64

# Bild von Note10 holen
img = requests.get("http://192.168.1.101:8080/shot.jpg").content
img_b64 = base64.b64encode(img).decode()

# Lokales Vision-Modell (Ollama)
r = requests.post("http://localhost:11434/api/generate", json={
    "model": "llava",       # oder llama3.2-vision
    "prompt": "Beschreibe was du siehst.",
    "images": [img_b64],
    "stream": False
})
print(r.json()["response"])
```

---

## 🔧 IP-ADRESSE ANPASSEN

Wenn Note10 eine andere IP hat:

```python
# In ddgk_arbitrage.py, Zeile ~56:
NodeProfile("Note10-Mobile", "192.168.1.101",  # ← Deine Note10-IP
            5001, "mobile", ...)

# IP auf Note10 finden (in Termux):
ifconfig 2>/dev/null | grep "inet " | head -5
# oder:
ip addr show wlan0
```

---

## 🔄 AUTOSTART (Termux beim Einschalten)

```bash
# Termux:Boot App installieren (F-Droid)
mkdir -p ~/.termux/boot/
cat > ~/.termux/boot/ddgk_start.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/ORION-ROS2-Consciousness-Node
python ddgk_note10_agent.py >> /tmp/ddgk_note10.log 2>&1 &
EOF
chmod +x ~/.termux/boot/ddgk_start.sh
```

---

## ✅ VOLLSTÄNDIGER NETZWERK-TEST

```bash
# Auf Laptop — alle 4 Nodes testen:
python ddgk_arbitrage.py

# Erwartetes Ergebnis nach Note10-Setup:
# NODE                 TYPE       STATUS     VITALITÄT  W-LIMIT
# PC-Master            master     online     ████████░░   150W
# Pi5-Edge             pi5        online     ███████░░░    20W
# Note10-Mobile        mobile     online     ███████░░░     5W  ← NEU!
# Laptop-Dev           laptop     online     ████████░░    45W
```

---

## 🤖 16-Agenten Edge-Assembly (Laptop)

Vom Repo-Root (nach `.env` mit `OLLAMA_*`, optional `NOTE10_DDGK_URL`):

```bash
python DDGK_EDGE_CLUSTER_ASSEMBLY.py
```

Report: `ZENODO_UPLOAD/DDGK_EDGE_CLUSTER_ASSEMBLY_REPORT.json` — prüft Ollama-Knoten, optional Note10-HTTP-Agent, Laptop-GPU, USB-Pfade; ruft `agents/agent_1..16.py` mit Mission `EDGE_CLUSTER` auf.

---

## 🎯 Was das Note10 für DDGK bringt

| Feature | Ohne Note10 | Mit Note10 |
|---------|------------|-----------|
| Vision | ❌ Kein Kamera-Node | ✅ Live-Kamera im Netz |
| Mobile Testing | ❌ Nur Simulator | ✅ Echtes Android-Device |
| NPU Inference | ❌ | ✅ Exynos NPU (TFLite) |
| 4-Node-Netz | ⚠️ 3 Nodes | ✅ Vollständig: PC+Pi5+Note10+Laptop |
| Investor-Demo | Komplex zu erklären | **"4 Devices, 1 System, live"** |

---

## 🔐 Sicherheitshinweis

```
Das Note10 ist im lokalen WLAN — Port 5001 nur intern erreichbar.
NIEMALS Port-Forwarding auf Note10 einrichten!
Für externe Demos: nur Pi5 oder Laptop exponieren (mit Auth).
```

---

*Paradoxon AI | paradoxonai.at*
