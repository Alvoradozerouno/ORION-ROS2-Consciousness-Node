#!/data/data/com.termux/files/usr/bin/bash
# Termux: prüft python3, optional CRLF am Agent-Skript, startet DDGK Note10-Agent.
# Nutzung im Repo-Root:  bash scripts/termux_note10_bootstrap.sh
set -e
cd "$(dirname "$0")/.." || exit 1
ROOT="$(pwd)"
AGENT="$ROOT/ddgk_note10_agent.py"

echo "[termux-bootstrap] ROOT=$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[termux-bootstrap] FEHLER: python3 nicht gefunden. Ausfuehren: pkg install python"
  exit 2
fi

if [[ ! -f "$AGENT" ]]; then
  echo "[termux-bootstrap] FEHLER: Datei fehlt: $AGENT (cd ins Repo? git clone?)"
  exit 2
fi

# CRLF von Windows oft -> Errno 2 beim ./ddgk_note10_agent.py
if command -v sed >/dev/null 2>&1; then
  sed -i 's/\r$//' "$AGENT" 2>/dev/null || true
fi

python3 -m pip install --user --quiet requests psutil 2>/dev/null || python3 -m pip install --user requests psutil

echo "[termux-bootstrap] Starte Agent ..."
exec python3 "$AGENT"
