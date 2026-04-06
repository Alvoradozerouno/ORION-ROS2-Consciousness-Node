# Globale Entwickler-Umgebung (Windows / Cursor / GitHub / HF / APIs)

**🔐** Echte Werte nur lokal: **`.env`** (Repo-Root, gitignored), optional **`master.env.ini`** (Repo oder `../EIRA/`), **`MASTER_ENV_INI`** für einen absoluten Pfad. Nicht in Git, nicht in Chat-Kopien.

---

## 1. Multi-Agent-Überblick (dieses Workspace)

| Bereich | Skript / Modul | Kurzbeschreibung |
|--------|----------------|------------------|
| Agent 1–4 | `MULTI_AGENT_ASSET_ANALYSIS.py` | Asset-Katalog, Impact, Integrität, Empfehlungen; nutzt `workspace_env` + Credential-Zeile |
| Agent 5–8 | `workspace_cleanup_agents.py` (via `--workspace-cleanup`) | Cache-Hygiene, Git-Inventar, `.gitignore`-Block |
| Hyper-Agent | `hyper_agent_system.py` | Tool-Synthese / Loop; lädt jetzt `.env` über `workspace_env` |
| Seed-Sync | `sync_orion_seed_complete.py` | `ORION_SEED_SOURCE` / `E:\ORION_SEED_COMPLETE` → `external/` |
| Credential-Status | `scripts/env_credential_status.py` | Welche Env-Keys gesetzt sind (ohne Werte) |
| Netzwerk-Health | `DDGK_DEV_NEXT_STEP.py` | HF/GitHub/SerpAPI/News/Zenodo/Ollama; INI-Pfad portabel |
| HF-Check | `hf_healthcheck.py` | whoami; Quelle: `.env` → `master.env.ini` |

---

## 2. Einmalig pro Maschine (oder pro User)

1. **Python 3.10+** installieren; im Repo:  
   `pip install -r requirements.txt`  
   (optional: venv unter `.venv` anlegen und in Cursor als Interpreter wählen).

2. **`.env` anlegen:** Kopie von `.env.example` → `.env`, alle benötigten Keys ausfüllen (GitHub, HF, Zenodo, …).

3. **`master.env.ini`:** Falls du weiterhin die große INI nutzt: entweder im Repo-Root, oder unter `…/EIRA/master.env.ini`, oder `MASTER_ENV_INI=C:\pfad\master.env.ini` setzen.  
   **Hinweis:** `workspace_env` spiegelt aus der INI **nur** die Allowlist-Keys (Pfade/Hosts: `ORION_SEED_SOURCE`, `OLLAMA_*`) nach `os.environ`. **Tokens** kommen zuverlässig über **`.env`** oder manuelles Exportieren / Terminal-`envFile`.

4. **Cursor / VS Code (Workspace):**  
   - `.vscode/settings.json`: `terminal.integrated.envFile` und **`python.envFile`** zeigen auf `${workspaceFolder}/.env` (Debugger + Tests sehen dieselben Variablen wie das Terminal).  
   - Empfohlene Extensions: `.vscode/extensions.json` (Python, Pylance, GitLens).

5. **Cursor User Settings (global):** Snippet in `docs/cursor-user-settings.snippet.json` — z. B. `terminal.integrated.envFile` nur sinnvoll, wenn du **immer** in diesem Repo arbeitest; sonst Workspace-Settings bevorzugen.

6. **PowerShell ohne Cursor:** Session mit Repo-`.env` füllen:  
   `. .\scripts\load-workspace-env.ps1`  
   (Dot-Source im Repo ausführen.)

7. **GitHub:** `gh auth login` und/oder SSH-Remote; für Skripte `GITHUB_TOKEN` / `GH_TOKEN` / `GITHUB_PAT` in `.env`.

8. **Hugging Face:** In `.env` mindestens **`HUGGINGFACE_TOKEN`** *oder* **`HF_TOKEN`** setzen (viele Tools akzeptieren beides; `hf_healthcheck` bevorzugt `HUGGINGFACE_TOKEN`, fällt sonst auf `HF_TOKEN` zurück). Optional: `huggingface-cli login` → `~/.cache/huggingface/token`.

9. **MCP-Server in Cursor:** In den MCP-Einstellungen **nur Variablennamen** referenzieren; Werte aus OS-Umgebung oder daraus, dass Cursor den Server mit geladener `.env` startet (je nach Version ggf. zusätzlich Windows-Benutzer-Umgebungsvariablen setzen).

10. **Node/npm:** Im Root gibt es kein zentrales `package.json`; Unterprojekte (z. B. `repos/or1on-framework`) jeweils mit `npm install` im jeweiligen Ordner — **kein** globales `npm install -g` nötig, außer ein Tool explizit `-g` verlangt.

---

## 3. AOIs / Endpoints (nur URLs, keine Keys)

- `https://huggingface.co` · `https://huggingface.co/api/whoami`  
- `https://api.github.com`  
- `https://zenodo.org/api`  
- `https://serpapi.com`  
- `https://newsapi.org`  
- Ollama: `http://127.0.0.1:11434` bzw. `OLLAMA_PI5` / `OLLAMA_NOTE10`

---

## 4. Nach Token-Leak

Token auf dem jeweiligen Dienst **rotieren**, `.env` aktualisieren, **nie** erneut in Markdown committen (GitHub Secret Scanning).

---

## 5. Verwandte Doku

- `docs/CURSOR_GITHUB_HF_SETTINGS.md` — Kurzüberblick Cursor/GitHub/HF  
- `workspace_credentials.py` — kanonische Liste der Env-Key-Namen  
- `AGENTS.md` — Agenten-Verhalten im Repo
