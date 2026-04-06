# Cursor, GitHub, Hugging Face & APIs — Settings-Übersicht (ohne Secrets)

**🔐 Niemals** echte Tokens in diese Datei, in `settings.json` oder ins Git schreiben. Werte nur in **`.env`** (gitignored) oder **`EIRA/master.env.ini`** (gitignored) bzw. **GitHub → Settings → Secrets**.

---

## 1. Lokales Projekt: `.env` (empfohlen)

- Datei: **Workspace-Root** `.env` (Kopie von `.env.example`, dann ausfüllen).
- **Cursor / VS Code:** `.vscode/settings.json` lädt `.env` automatisch für das **integrierte Terminal** (`terminal.integrated.envFile`).
- **Python:** `workspace_env.py` lädt `.env` per `python-dotenv`; danach optional **Allowlist** aus `master.env.ini` (nur Pfade/Hosts).

---

## 2. Cursor IDE (User Settings)

**Keine** Secrets in `~/.cursor/` JSON ablegen, wenn das Profil synchronisiert wird.

| Thema | Wo | Inhalt |
|--------|-----|--------|
| Allgemein | Cursor → **Settings** | Theme, Font, Format on Save |
| **MCP-Server** | Settings → **MCP** | Pro Server **Umgebungsvariablen** (z. B. `HF_TOKEN`) nur als **Namen**; Werte aus OS-Umgebung oder `.env` laden, die Cursor beim Start des Servers einblendet (je nach Version: „Env“-Feld oder Shell-Profil). |
| **Rules** | `.cursor/rules/*.mdc` (lokal, oft gitignored) + **`AGENTS.md`** im Repo | Verhalten der KI, kein Klartext-Token. |

Optional: In **Windows** Systemumgebungsvariablen setzen, wenn MCP-Prozesse **nicht** das Workspace-Terminal nutzen.

---

## 3. GitHub

| Verwendung | Variable / Ort | Hinweis |
|------------|----------------|---------|
| `git push` / HTTPS | **Credential Manager**, **SSH-Key**, oder kurzlebiger **Fine-grained PAT** | PAT nicht in Remote-URL dauerhaft; `gh auth login` |
| **GitHub CLI** `gh` | `GH_TOKEN` (von `gh auth` gesetzt) | |
| **REST/API** in Skripten | `GITHUB_TOKEN` oder `GH_TOKEN` | Oft von Actions injiziert |
| **Actions** | Repo → **Settings → Secrets and variables → Actions** | z. B. `HF_TOKEN`, `ZENODO_API_TOKEN` für spätere Workflows |

---

## 4. Hugging Face

| Variable | Nutzung |
|----------|---------|
| `HUGGINGFACE_TOKEN` | API `whoami`, Hub-Uploads (von `hf_healthcheck.py` / HF-Skills bevorzugt genannt) |
| `HF_TOKEN` | Viele Skripte / MCP / ältere Beispiele (gleiche Rolle wie oben — **ein** Token reicht, konsistent benennen) |

**Regeln:** Read für Modelle, Write nur mit HITL; Token unter https://huggingface.co/settings/tokens rotieren bei Leak.

---

## 5. Weitere APIs / Dienste (Platzhalter in `.env`)

| Variable | Dienst |
|----------|--------|
| `ZENODO_API_TOKEN` | Zenodo-Upload (`zenodo_upload_package.py`) |
| `SERPAPI_KEY` | WWW-Recherche (`www_research_fetch.py`) |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` | Outreach (`ddgk_outreach_engine.py`) |
| `EMAIL_ADDRESS`, `EMAIL_PASSWORD` | Fallback-Aliase für SMTP |
| `DISCORD_WEBHOOK_URL` | Discord-Benachrichtigungen (falls genutzt) |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Telegram (falls genutzt) |
| `IBM_QUANTUM_TOKEN` | IBM Quantum |
| `NASA_API_KEY` | NASA API (falls genutzt) |
| `SUPABASE_URL`, `SUPABASE_ANON_KEY` / projektspezifisch | Supabase (falls genutzt) |

**AOIs / Endpoints (nur URLs, keine Keys):** `https://huggingface.co`, `https://api.github.com`, `https://zenodo.org`, `https://serpapi.com`, `https://huggingface.co/api/whoami`.

---

## 6. Pfade & Cluster (keine Secrets)

| Variable | Zweck |
|----------|--------|
| `ORION_SEED_SOURCE` | Quelle für `sync_orion_seed_complete.py` |
| `OLLAMA_HOST`, `OLLAMA_PI5`, `OLLAMA_NOTE10` | Ollama-HTTP |
| `MASTER_ENV_INI` | Expliziter Pfad zu `master.env.ini` |

---

## 7. Checkliste nach Token-Leak

1. Token auf **GitHub / HF / Zenodo / SMTP** **widerrufen** und **neu** erzeugen.  
2. Nur in **`.env`** / **`master.env.ini`** eintragen.  
3. **Nicht** erneut in Markdown oder Commits.  
4. `git push` mit **Secret-Scan** von GitHub beachten.

---

*Generiert als Projektdoku — keine echten Credentials.*
