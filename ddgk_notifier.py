#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  DDGK NOTIFIER — Benachrichtigungen bei wichtigen Ereignissen      ║
║                                                                    ║
║  Wann benachrichtigt:                                              ║
║   • REQUIRE_HUMAN Entscheidung → Email + optional Slack           ║
║   • Node OFFLINE → sofort Alert                                    ║
║   • κ < 1.5 → Warnung                                             ║
║   • Neuer Pilot-Lead → Sofort-Email                               ║
║   • Disk > 90% → Warnung                                          ║
║                                                                    ║
║  Konfiguration: .env → NOTIFY_EMAIL, SMTP_HOST, SMTP_USER         ║
║  Kein .env → lokales Log (degraded mode)                          ║
╚══════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import sys, os, json, datetime, smtplib, socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE      = Path(__file__).parent
NOTIFY_LOG = BASE / "cognitive_ddgk" / "notifications.jsonl"
NOTIFY_LOG.parent.mkdir(exist_ok=True)

# Konfiguration aus .env (oder Environment)
def _env(key: str, default: str = "") -> str:
    # Versuche .env zu lesen
    env_file = BASE / ".env"
    if env_file.exists():
        for line in env_file.read_text("utf-8", errors="replace").splitlines():
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(key, default)

SMTP_HOST  = _env("SMTP_HOST",  "smtp.world4you.com")
SMTP_PORT  = int(_env("SMTP_PORT", "587"))
SMTP_USER  = _env("SMTP_USER",  "")  # office@paradoxonai.at
SMTP_PASS  = _env("SMTP_PASS",  "")
NOTIFY_TO  = _env("NOTIFY_EMAIL", "")
SLACK_URL  = _env("SLACK_WEBHOOK", "")

ENABLED = bool(SMTP_USER and SMTP_PASS and NOTIFY_TO)


class DDGKNotifier:
    """
    Zentraler DDGK Notifier.
    Wenn SMTP nicht konfiguriert → nur lokales Log (kein Crash).
    """

    @staticmethod
    def _log(event_type: str, message: str, metadata: dict = None):
        entry = {
            "ts":         datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "type":       event_type,
            "message":    message[:500],
            "metadata":   metadata or {},
            "delivered":  ENABLED,
            "node":       socket.gethostname(),
        }
        with NOTIFY_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    @staticmethod
    def _send_email(subject: str, body: str, to: str = None) -> bool:
        if not ENABLED:
            print(f"  [NOTIFIER] Email nicht konfiguriert — Log only: {subject}")
            return False
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[DDGK] {subject}"
            msg["From"]    = SMTP_USER
            msg["To"]      = to or NOTIFY_TO

            html = f"""
<html><body style="font-family:monospace;background:#0d1117;color:#e6edf3;padding:20px">
<h2 style="color:#58a6ff">🧠 DDGK Notification</h2>
<p style="color:#8b949e">{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {socket.gethostname()}</p>
<pre style="background:#161b22;padding:15px;border-radius:6px;color:#e6edf3">{body}</pre>
<hr style="border-color:#30363d">
<p style="color:#8b949e;font-size:12px">Paradoxon AI | paradoxonai.at | DDGK v2.0</p>
</body></html>"""

            msg.attach(MIMEText(body, "plain"))
            msg.attach(MIMEText(html, "html"))

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as s:
                s.ehlo(); s.starttls(); s.ehlo()
                s.login(SMTP_USER, SMTP_PASS)
                s.sendmail(SMTP_USER, to or NOTIFY_TO, msg.as_string())
            return True
        except Exception as e:
            print(f"  [NOTIFIER] Email-Fehler: {e}")
            return False

    @classmethod
    def require_human(cls, action: str, agent: str, risk_score: int,
                      chain_hash: str = "", details: str = "") -> dict:
        """Sendet sofortige Benachrichtigung wenn HITL benötigt wird."""
        subject = f"REQUIRE_HUMAN: {action} (Score={risk_score})"
        body = f"""
🛡️ DDGK GUARDIAN: MENSCHLICHE FREIGABE BENÖTIGT

Aktion:      {action}
Agent:       {agent}
Risk Score:  {risk_score}/100
Chain Hash:  {chain_hash or 'N/A'}
Zeitpunkt:   {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Details:
{details or 'Keine weiteren Details.'}

AKTION ERFORDERLICH:
  Prüfe die Aktion und gib Freigabe oder lehne ab.
  Dashboard: http://localhost:7860
  API:       http://localhost:8000/docs

Paradoxon AI | DDGK Governance System
        """
        cls._log("REQUIRE_HUMAN", subject, {"action": action, "agent": agent, "score": risk_score})
        cls._send_email(subject, body.strip())
        return {"notified": True, "type": "REQUIRE_HUMAN", "action": action}

    @classmethod
    def node_offline(cls, node_name: str, host: str, last_seen: str = "") -> dict:
        """Alert wenn Node offline geht."""
        subject = f"NODE OFFLINE: {node_name}"
        body = f"""
🔴 DDGK NODE OFFLINE

Node:       {node_name}
Host:       {host}
Last Seen:  {last_seen or 'unbekannt'}
Zeitpunkt:  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Das DDGK-Netzwerk hat einen Node verloren.
Prüfe: ssh {host} | ping {host}

Orchestrator läuft weiter — dieser Node wird überbrückt.
        """
        cls._log("NODE_OFFLINE", subject, {"node": node_name, "host": host})
        cls._send_email(subject, body.strip())
        return {"notified": True, "type": "NODE_OFFLINE", "node": node_name}

    @classmethod
    def low_kappa(cls, kappa: float, threshold: float = 1.5) -> dict:
        """Warnung wenn κ unter Schwellwert fällt."""
        subject = f"κ WARNUNG: κ={kappa:.3f} (Schwelle={threshold})"
        body = f"""
⚠️ DDGK KOHÄRENZ-WARNUNG

κ (Kohärenz):  {kappa:.4f}
Schwelle:      {threshold}
Zeitpunkt:     {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Das System zeigt reduzierte Kohärenz.
Mögliche Ursachen:
  • Memory Pipeline nicht gelaufen
  • Modell-Diskrepanz
  • Netzwerk-Partition

Empfehlung: python cognitive_ddgk/memory_pipeline.py
        """
        cls._log("LOW_KAPPA", subject, {"kappa": kappa, "threshold": threshold})
        cls._send_email(subject, body.strip())
        return {"notified": True, "type": "LOW_KAPPA", "kappa": kappa}

    @classmethod
    def new_pilot_lead(cls, company: str, contact: str, source: str = "") -> dict:
        """Sofort-Alert wenn neuer Pilot-Lead identifiziert."""
        subject = f"🚀 NEUER PILOT LEAD: {company}"
        body = f"""
🚀 NEUER PILOT LEAD!

Unternehmen: {company}
Kontakt:     {contact}
Quelle:      {source or 'Market Trajectory Scan'}
Zeitpunkt:   {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SOFORT-AKTION:
  Email innerhalb 24h senden!
  Template: DDGK_TIWAG_PITCH_EMAIL.md (anpassen)
  Preis: €5.000 Pilot / 3 Monate

Paradoxon AI | Elisabeth Steurer | paradoxonai.at
        """
        cls._log("PILOT_LEAD", subject, {"company": company, "contact": contact})
        cls._send_email(subject, body.strip())
        return {"notified": True, "type": "PILOT_LEAD", "company": company}

    @classmethod
    def disk_warning(cls, disk_pct: float, path: str = "C:") -> dict:
        """Warnung bei Disk > 90%."""
        subject = f"DISK WARNUNG: {path} = {disk_pct:.1f}%"
        body = f"""
⚠️ DISK-AUSLASTUNG KRITISCH

Pfad:        {path}
Auslastung:  {disk_pct:.1f}%
Zeitpunkt:   {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Empfehlung:
  python _disk_check.py  (Cleanup)
  Alte Logs löschen: cognitive_ddgk/*.jsonl (Backup zuerst!)
        """
        cls._log("DISK_WARNING", subject, {"disk_pct": disk_pct, "path": path})
        cls._send_email(subject, body.strip())
        return {"notified": True, "type": "DISK_WARNING", "disk_pct": disk_pct}

    @classmethod
    def get_log(cls, last_n: int = 20) -> list:
        """Letzte N Notifikationen aus dem Log."""
        try:
            with NOTIFY_LOG.open("r") as f:
                lines = f.readlines()[-last_n:]
            return [json.loads(l) for l in lines]
        except: return []


# ─── SELF-TEST ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    n = DDGKNotifier()
    print("\n  🔔 DDGK NOTIFIER — Self-Test")
    print(f"  SMTP:    {'KONFIGURIERT' if ENABLED else 'NICHT konfiguriert (Log-Only Modus)'}")
    print(f"  An:      {NOTIFY_TO or '(nicht gesetzt)'}")
    print(f"  Host:    {SMTP_HOST}:{SMTP_PORT}")
    print()

    # Teste alle Event-Typen
    events = [
        n.require_human("email_send_tiwag", "EIRA", 75, "abc123", "TIWAG Pitch Email warten auf Freigabe"),
        n.node_offline("ORIONEIRARASPBERRYPI", "192.168.1.103"),
        n.low_kappa(1.2),
        n.new_pilot_lead("TIWAG AG", "cto@tiwag.at", "Market Scan"),
        n.disk_warning(92.5, "C:"),
    ]

    print("  Test-Events geloggt:")
    for e in events:
        print(f"    {e['type']:20s}: notified={e['notified']}")

    log = n.get_log(5)
    print(f"\n  Log: {len(log)} Einträge in {NOTIFY_LOG.name}")
    print(f"\n  Setup: Trage in .env ein:")
    print(f"    SMTP_HOST=smtp.world4you.com")
    print(f"    SMTP_PORT=587")
    print(f"    SMTP_USER=office@paradoxonai.at")
    print(f"    SMTP_PASS=<dein-passwort>")
    print(f"    NOTIFY_EMAIL=elisabethsteurer@paradoxonai.at")
    print(f"  → Dann: python ddgk_notifier.py → echte Emails!")
