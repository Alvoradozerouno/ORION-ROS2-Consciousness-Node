# 🔐 ORION DDGK — SICHERHEITS-ARCHITEKTUR FÜR VOLLAUTONOM

## Schichten (Defense in Depth)

### 1️⃣ **POLICY LAYER** (ccrn_governance/)
```python
PolicyEngine.evaluate(action, risk_level):
  if risk_level == "HIGH":
    requires_human_approval()  # HITL-Token nötig!
  elif risk_level == "MEDIUM":
    require_human_token() OR auto_allow_if_trust > 70%
  else:  # LOW
    proceed_autonomous()
```
📍 Datei: `ccrn_governance/ddgk_layer.py`

### 2️⃣ **GOVERNANCE TOKENS** (Authentifizierung)
```
.env: HITL_ENABLED = true
      DDGK_RISK_LOW = 40
      DDGK_RISK_HIGH = 70
```
- **LOW (< 40)**: Autonome Exekution
- **MEDIUM (40-70)**: Braucht `human_token` ODER κ > Schwelle
- **HIGH (> 70)**: Nur mit expliziter menschlicher Freigabe

📍 Datei: `cognitive_ddgk/hitl_mcp_bridge.py`

### 3️⃣ **AUDIT CHAIN** (Unveränderliche Logs)
```jsonl
# cognitive_ddgk/audit_chain.jsonl
{"ts": "2026-04-03T22:10:00Z", "action": "PyPI upload", "κ": 83.3, "decision": "ALLOW", "human_token": null, "proof": "sha256:abc..."}
```
- **SHA-256 verkette**: jedes Event hängt am vorherigen
- **Replay-Schutz**: Timestamps + Nonce
- **Immutable**: nur append, nie löschen

📍 Datei: `ccrn_governance/audit_chain.jsonl`

### 4️⃣ **COGNITIVE STATE** (Decision Memory)
```json
{
  "kappa": 2.9114,
  "trust_level": 83.3,
  "service_availability": {"github": true, "zenodo": true, "ollama": true},
  "last_human_approval": "2026-04-02T17:47:00Z",
  "autonomous_actions_since_approval": 3,
  "escalation_threshold": 10
}
```
📍 Datei: `cognitive_ddgk/cognitive_state.json`

### 5️⃣ **NOTIFIER CHAIN** (Alerts & Logs)
```
.env: NOTIFY_EMAIL = elisabethsteurer@paradoxonai.at
      TELEGRAM_BOT_TOKEN = 8510125844:AAGkHOY...
      SLACK_WEBHOOK_URL = https://hooks.slack.com/...
      DISCORD_BOT_TOKEN = f9a9bb3ff...
```
- **Email**: problematische Entscheidungen (κ < 60)
- **Telegram**: High-Risk Actions
- **Slack**: Audit Trail für Team
- **Discord**: Live-Status im privaten Channel

📍 Tools: `ddgk_notifier.py`, `ddgk_guardian_v2.py`

---

## Vollautonome Dauerausführung (Full Self-Acting)

### 🔄 **3-Schicht Loop**

```
┌─────────────────────────────────────────────────────────┐
│ LAYER 1: SELF-PROMPTING (Alle 5 Min)                   │
│ → _token_test.py                                         │
│   Ergebnis: κ, trust_level, next_actions                │
│   Decision: ALLOW / REQUIRE_HUMAN / DENY                │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ LAYER 2: GOVERNANCE CHECK (PolicyEngine)                │
│ → decision_chain.py                                      │
│   Risk = extract_risk(next_action)                      │
│   if HIGH: escalate_to_human() + notify()               │
│   if MEDIUM: check_human_token() OR κ-threshold         │
│   if LOW: proceed()                                      │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ LAYER 3: EXECUTION (mit Audit-Trail)                    │
│ → action_executor.py                                     │
│   log_to_audit_chain(action, κ, decision)               │
│   execute_with_rollback_plan()                          │
│   notify(status) → Email/Telegram/Discord               │
└─────────────────────────────────────────────────────────┘
```

### 📅 **Permanente Ausführung — 3 Optionen**

#### Option A: **Windows Task Scheduler** (Laptop)
```batch
# autostart.bat (Windows Startup)
@echo off
cd C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\ORION-ROS2-Consciousness-Node
python self_prompting_autonomous_loop.py --infinite
```
- Startet beim Hochfahren
- Lädt .env automatisch
- Tokenisiert alle Aktionen

#### Option B: **Systemd Daemon** (Pi5)
```ini
# /etc/systemd/system/orion-ddgk.service
[Unit]
Description=ORION DDGK Autonomous Loop
After=network.target

[Service]
Type=simple
User=alvoradozerouno
WorkingDirectory=/home/alvoradozerouno/ORION-ROS2-Consciousness-Node
ExecStart=/usr/bin/python3 self_prompting_autonomous_loop.py --infinite
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable orion-ddgk
sudo systemctl start orion-ddgk
sudo journalctl -u orion-ddgk -f  # Live-Logs
```

#### Option C: **Docker + Cron** (Cloud)
```dockerfile
FROM python:3.14-slim
WORKDIR /app
COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["python", "self_prompting_autonomous_loop.py", "--infinite"]
```
```bash
docker build -t orion-ddgk:latest .
docker run -d --env-file .env --name orion-daemon orion-ddgk:latest
docker logs -f orion-daemon
```

---

## 🚨 GUARDRAILS (was stoppt den Daemon?)

### Automatische Eskalation
```python
if consecutive_DENY_decisions >= 5:
    # Menschliche Überprüfung erzwungen
    notify(ORION_MAIL_GUARDIAN, "5 Verweigerungen — System pausiert")
    sys.exit(1)  # STOP bis Manual Review

if autonomous_actions_without_human_approval >= 50:
    # Re-Baseline nötig
    notify("κ-Driftschutz: manueller Baselines-Check erforderlich")
    pause_for_human_review()

if audit_chain_corruption_detected():
    # Sofort System-Stop
    notify("KRITISCH: Audit-Trail beschädigt — Zugriff verweigert")
    sys.exit(2)
```

### Explizite Stop-Signale
```bash
# SYSTEM SOFORT PAUSIEREN:
echo "PAUSED" > /tmp/orion_daemon.status

# Dann manuell:
python self_prompting_autonomous_loop.py --status
# → Zeigt aktuelle κ, letzte 10 Aktionen, nächste geplante

# Neu starten:
rm /tmp/orion_daemon.status
systemctl restart orion-ddgk  # oder docker restart orion-daemon
```

---

## 📊 Monitoring (wer überwacht die Überwacher?)

### Live Dashboard
```bash
python ddgk_dashboard.py --port 8000
# → http://localhost:8000/monitor
# Shows: κ, trust_level, audit_chain, next_actions, alert_history
```

### Telegram Alerts
```
Bot: @orion_ddgk_bot (8510125844)
Chat: 6913045983
```
Jede Stunde: κ-Status + letzte 3 Aktionen
HIGH-Risk: sofort notifiziert

### Email Digest
```
An: elisabethsteurer@paradoxonai.at
Täglich 06:00 UTC: 
  - Autonome Aktionen seit gestern
  - Alle Entscheidungen κ < 75 (MEDIUM)
  - Fehlgeschlagene Versuche
```

---

## ✅ CHECKLISTE FÜR VOLLAUTONOM

- [ ] `.env` alle Tokens eingetragen (HF, SMTP, Discord, Supabase)
- [ ] `HITL_ENABLED = true` (Human-in-the-Loop aktiv)
- [ ] `cognitive_ddgk/cognitive_state.json` existiert
- [ ] `ccrn_governance/audit_chain.jsonl` existiert + lesbar
- [ ] Telegram/Email/Discord Kanäle konfiguriert
- [ ] Autostart-Script aktiv (Windows/Linux/Docker)
- [ ] `self_prompting_autonomous_loop.py --test` erfolgreich
- [ ] Notfall-Stop verfügbar (`/tmp/orion_daemon.status`)

---

## 🔑 Zusammenfassung

| Ebene | Funktion | Auslöser | Stopp-Bedingung |
|-------|----------|----------|-----------------|
| Policy | Risk-Bewertung | DDGK κ-Formel | HIGH-Risk → Human |
| Tokens | Authentifizierung | .env-Secrets | Ungültig → Eskalation |
| Audit | Nachverfolgung | SHA-256-Kette | Corruption → STOP |
| Notify | Benachrichtigung | Email/Tel/Discord | Stille > 2h → Alert |
| Daemon | Dauerbetrieb | systemd/cron/docker | Kill-Signal → Pause |

**Trust Level = Service Availability %** (GitHub, Zenodo, Ollama, API)
**κ = Informations-Akkumulation** (2.060 + 0.930·ln(N)·φ̄)
**Decision = ALLOW (κ > 70%) / REQUIRE_HUMAN (50-70%) / DENY (< 50%)**

---

🚀 **Vollautonomer Betrieb aktiv sobald:**
1. ✅ .env vollständig
2. ✅ Autostart-Script startet
3. ✅ Erste κ-Messung erfolgreich
4. ✅ Human-in-the-Loop Token registriert
