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
python3 -m pip install --user requests psutil
```

### 3. Agent-Script kopieren
```bash
# Option A: Via Git (wenn WLAN mit Laptop im selben Netz)
# pkg install git   # falls "git: not found" / Errno 2
git clone https://github.com/Alvoradozerouno/ORION-ROS2-Consciousness-Node
cd ORION-ROS2-Consciousness-Node
python3 ddgk_note10_agent.py

# Option B: Via USB (adb)
adb push ddgk_note10_agent.py /data/data/com.termux/files/home/
# In Termux: python3 ~/ddgk_note10_agent.py
```

### 4. Agent starten
```bash
python3 ddgk_note10_agent.py
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

## Fehlersuche: **Errno 2** („No such file or directory“) in Termux

**Bedeutung:** Der Kernel findet **keine ausführbare Datei** oder **keinen Dateipfad** — nicht zu verwechseln mit „Permission denied“ (EACCES).

| Meldung / Kontext | Typische Ursache | Was tun |
|-------------------|------------------|---------|
| `python: command not found` oder `cannot execute … python` | Nur **`python3`** installiert (häufig) | `pkg install python` · Aufruf: **`python3`** statt `python` · Prüfen: `command -v python3` |
| `python3: command not found` | Python-Paket fehlt | `pkg update && pkg install python` |
| `./ddgk_note10_agent.py: No such file or directory` (trotz `ls` zeigt Datei) | **Windows-Zeilenumbrüche (CRLF)** in der ersten Zeile / Shebang kaputt | Auf Laptop: Datei als **LF** speichern oder in Termux: `sed -i 's/\r$//' ddgk_note10_agent.py` · Start stets: `python3 ddgk_note10_agent.py` (ohne `./`) |
| `ddgk_note10_agent.py: No such file or directory` | **Falsches Verzeichnis** | `pwd` · `ls` · `cd ~/ORION-ROS2-Consciousness-Node` (nach `git clone`) |
| `git: command not found` bei `git clone` | Git nicht installiert | `pkg install git` |
| `pip: command not found` | `pip` nicht im PATH | **`python3 -m pip install requests psutil`** (immer zuverlässig) |
| `/usr/bin/env: 'python3': No such file or directory` beim `./script.py` | `python3` fehlt oder kaputt | `pkg reinstall python` |
| Nach `adb push … /data/data/com.termux/files/home/` | Datei liegt in **Home**, du startest aber **ohne** `cd` woanders | In Termux: `ls ~` · `python3 ~/ddgk_note10_agent.py` oder ins Repo-Verzeichnis wechseln |
| Ollama / anderes Binary | Binary nicht für **aarch64 Termux** gebaut oder nicht installiert | Eigenes Paket über `pkg` oder offizielle ARM64-Binaries; Pfade prüfen mit `which ollama` |

**Minimal-Checkliste (Termux, nacheinander):**

```bash
command -v python3
python3 --version
pwd
ls -la
# im Repo-Root:
python3 -m pip install --user requests psutil
python3 ddgk_note10_agent.py
```

**Optional:** Repo-Skript **`scripts/termux_note10_bootstrap.sh`** auf das Handy kopieren, ausführbar machen (`chmod +x`), einmal ausführen — prüft `python3` und ob `ddgk_note10_agent.py` im aktuellen Verzeichnis liegt.

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
python3 ddgk_note10_agent.py >> /tmp/ddgk_note10.log 2>&1 &
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

## SSH: „Connection timed out“ (Laptop → Note10)

1. **IP prüfen** (auf dem Phone, Termux): `ip addr` oder `ifconfig` — **WLAN-IP** oft `wlan0`, nicht Loopback.
2. **sshd läuft?** `sshd` — lauscht standardmäßig auf **8022**.
3. **Gleiches Netz:** kein **Gäste-WLAN** mit **Client-Isolation**; Laptop und Phone dieselbe SSID.
4. **Scan:** `python note10_lan_discover.py` — zeigt u. a. offene **8022**.
5. **Diagnose:** `python note10_ssh_check.py` — TCP-Test zu `NOTE10_SSH_HOST` / Port + optional `/health`.

---

## Windows PowerShell: **kein** `sshd` eingeben

`sshd` ist der SSH-**Server** unter **Termux (Android)** — unter Windows gibt es diesen Befehl in der Regel **nicht**.  
Auf dem Laptop brauchst du nur den **OpenSSH-Client** (`ssh`, `scp`) und startest **`python note10_start_from_laptop.py`** im Repo.

---

## Wichtig: `note10_start_from_laptop.py` **nicht** in Termux starten

Dieses Skript liegt nur auf dem **Laptop** (Repo-Clone) und nutzt **SSH/SCP zum Handy**.  
Wenn du in Termux `python note10_start_from_laptop.py` ausführst → **Errno 2** (Datei fehlt).

- **Laptop:** `python note10_start_from_laptop.py` (im Projektordner, `.env` mit `NOTE10_SSH_*`)
- **Termux (Note10):** nach dem Kopieren nur `python3 ddgk_note10_agent.py`

---

## Start vom Laptop (SCP + SSH)

Auf dem Note10: **`pkg install openssh python`**, **`passwd`**, **`sshd`** (Port **8022**). `whoami` → `NOTE10_SSH_USER`.

Im Laptop-Repo `.env` setzen: `NOTE10_SSH_HOST`, `NOTE10_SSH_PORT`, `NOTE10_SSH_USER` (siehe `.env.example`).

```bash
# Windows PowerShell / CMD (OpenSSH-Client):
python note10_start_from_laptop.py
# Vordergrund zum Debuggen:
python note10_start_from_laptop.py --foreground
# Agent stoppen:
python note10_start_from_laptop.py --kill
```

Das Skript kopiert `ddgk_note10_agent.py` (und optional `scripts/termux_note10_bootstrap.sh`) per **SCP**, installiert auf dem Phone per **`python3 -m pip install --user requests psutil`**, startet den Server auf **Port 5001**. Anschließend: `NOTE10_DDGK_URL=http://<IP>:5001` in `.env`.

---

## 🔍 Note10 / Ollama im LAN automatisch finden (WLAN + USB)

Vom Repo-Root (nutzt `OLLAMA_PI5` aus `.env`, schlägt **anderes** Ollama als Note10 vor):

```bash
python note10_lan_discover.py
```

Optional Report: `python note10_lan_discover.py --json-out ZENODO_UPLOAD/NOTE10_LAN_DISCOVER.json`

Sucht TCP **5001** (DDGK-Agent), **11434** (Ollama), **8022** (Termux-SSH) auf allen lokalen **192.168.x.0/24**-Subnetzen (mehrere Adapter = USB-Tethering + WLAN möglich).

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
