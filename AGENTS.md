# Agent-Anweisungen (ORION / DDGK)

## Abschluss ohne Rückfragen

- Keine typischen KI-Abschlussfragen („Soll ich …?“, „Wenn du willst …“).
- DDGK-Zeile „Nächster Schritt“: eine sachliche Handlungszeile (Imperativ) oder **⛔ kein Blocker** — keine Frage am Ende.
- Blockaden (Credentials, irreversible Aktionen): eine minimale Klärung **im Fließtext**, nicht als Engagement-Bait.
- Sicher automatisierbare Schritte **zu Ende führen**; offene Punkte **dokumentieren**.

(Doppelung zu `.cursor/rules/orion-assistant-abschluss.mdc` — dort lokal für Cursor.)

## Settings & APIs (ohne Secrets in Git)

Globale Einrichtung inkl. Multi-Agent: **`docs/GLOBAL_DEV_SETUP.md`**. Kurz: **`docs/CURSOR_GITHUB_HF_SETTINGS.md`** · Vorlage: **`.env.example`** · Terminal + Python: **`.vscode/settings.json`** (`terminal.integrated.envFile`, `python.envFile`).
