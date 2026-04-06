#!/data/data/com.termux/files/usr/bin/bash
# Auf dem NOTE10 in Termux ausfuehren (ein Block):
#   curl -sL ... > t.sh && bash t.sh
# oder Datei aus Repo:  bash scripts/termux_install_minimum.sh
set -e
echo "=== Termux: Minimal-Install (SSH + Python) ==="
pkg update -y && pkg upgrade -y
pkg install -y openssh python
echo ""
echo "Jetzt: passwd setzen, dann whoami merken, dann:"
echo "  sshd"
echo "Pruefen: ss -tlnp | grep 8022"
echo ""
python3 -m pip install --user requests psutil
echo "OK: pip deps"
echo "Fertig. sshd nicht vergessen!"
