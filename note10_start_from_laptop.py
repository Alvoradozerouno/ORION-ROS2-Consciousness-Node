#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Note10 DDGK-Agent vom Laptop starten (SSH + SCP).

!!! NUR AUF DEM LAPTOP / PC AUSFUEHREN (Windows PowerShell im Repo-Ordner) !!!
    NICHT in Termux auf dem Handy — dort gibt es diese Datei nicht und sie gehoert dort nicht hin.
    Auf dem Phone nur:  python3 ddgk_note10_agent.py  (nach git clone oder nach SCP vom Laptop)

Voraussetzung auf dem Note10 (Termux):
  pkg install openssh python
  passwd && sshd
  whoami  -> NOTE10_SSH_USER

Umgebung (.env):
  NOTE10_SSH_HOST=192.168.1.88
  NOTE10_SSH_PORT=8022
  NOTE10_SSH_USER=u0_a123
  NOTE10_REMOTE_DIR=~/ORION-ROS2-Consciousness-Node   (optional)

Windows: OpenSSH-Client aktivieren (Einstellungen -> Optionale Features -> OpenSSH Client).

  python note10_start_from_laptop.py
  python note10_start_from_laptop.py --foreground    # blockiert, Log im Terminal
  python note10_start_from_laptop.py --no-sync       # nur starten (Datei schon auf dem Phone)
  python note10_start_from_laptop.py --kill          # laufenden Agent beenden
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "ddgk_note10_agent.py"
BOOT = ROOT / "scripts" / "termux_note10_bootstrap.sh"

try:
    from workspace_env import load_workspace_dotenv

    load_workspace_dotenv(override=False)
except ImportError:
    pass


def _need(var: str) -> str:
    v = (os.environ.get(var) or "").strip()
    if not v:
        print(f"[note10-start] FEHL: Umgebungsvariable {var} nicht gesetzt (siehe .env.example).", flush=True)
        sys.exit(2)
    return v


def ssh_base(host: str, port: int, user: str) -> list[str]:
    return ["ssh", "-p", str(port), "-o", "StrictHostKeyChecking=accept-new", f"{user}@{host}"]


def scp_file(local: Path, remote_path: str, host: str, port: int, user: str) -> None:
    dst = f"{user}@{host}:{remote_path}"
    cmd = ["scp", "-P", str(port), "-o", "StrictHostKeyChecking=accept-new", str(local), dst]
    print(f"[note10-start] {' '.join(cmd[:5])} ... -> {remote_path}", flush=True)
    subprocess.run(cmd, check=True)


def _running_inside_termux() -> bool:
    pfx = (os.environ.get("PREFIX") or "").replace("\\", "/")
    return pfx.startswith("/data/data/com.termux")


def main() -> int:
    if _running_inside_termux():
        print(
            "[note10-start] FEHL: Dieses Skript laeuft auf TERMUX (Phone).\n"
            "  Es muss auf dem LAPTOP im geklonten Repo gestartet werden:\n"
            "    cd .../ORION-ROS2-Consciousness-Node\n"
            "    python note10_start_from_laptop.py\n"
            "  Auf dem Note10 danach nur den Agenten:\n"
            "    python3 ~/.../ddgk_note10_agent.py\n",
            flush=True,
        )
        return 2

    ap = argparse.ArgumentParser(description="DDGK Note10-Agent vom Laptop per SSH starten")
    ap.add_argument("--host", default=os.environ.get("NOTE10_SSH_HOST", "").strip())
    ap.add_argument("--port", type=int, default=int(os.environ.get("NOTE10_SSH_PORT") or "8022"))
    ap.add_argument("--user", default=os.environ.get("NOTE10_SSH_USER", "").strip())
    ap.add_argument(
        "--remote-dir",
        default=(os.environ.get("NOTE10_REMOTE_DIR") or "~/ORION-ROS2-Consciousness-Node").strip(),
        help="Zielverzeichnis auf Termux (wird per ssh mkdir -p angelegt)",
    )
    ap.add_argument("--no-sync", action="store_true", help="Kein SCP (Skript liegt schon auf dem Phone)")
    ap.add_argument("--foreground", action="store_true", help="Nicht nohup — blockiert (Strg+C stoppt)")
    ap.add_argument("--kill", action="store_true", help="Nur laufende ddgk_note10_agent.py beenden")
    args = ap.parse_args()

    host = args.host or _need("NOTE10_SSH_HOST")
    user = args.user or _need("NOTE10_SSH_USER")
    port = args.port
    rdir = args.remote_dir.replace("\\", "/")

    if not AGENT.is_file():
        print(f"[note10-start] FEHL: {AGENT} fehlt.", flush=True)
        return 2

    ssh = ssh_base(host, port, user)

    if args.kill:
        cmd = ssh + [
            "bash",
            "-lc",
            "pkill -f ddgk_note10_agent.py 2>/dev/null; echo OK",
        ]
        print("[note10-start] kill ...", flush=True)
        subprocess.run(cmd)
        return 0

    if not args.no_sync:
        mk = ssh + ["bash", "-lc", f"mkdir -p {rdir}/scripts"]
        print("[note10-start] Remote-Verzeichnis ...", flush=True)
        subprocess.run(mk, check=True)
        agent_name = AGENT.name
        scp_file(AGENT, f"{rdir}/{agent_name}", host, port, user)
        if BOOT.is_file():
            try:
                scp_file(BOOT, f"{rdir}/scripts/termux_note10_bootstrap.sh", host, port, user)
                subprocess.run(
                    ssh + ["bash", "-lc", f"chmod +x {rdir}/scripts/termux_note10_bootstrap.sh"],
                    check=False,
                )
            except subprocess.CalledProcessError:
                pass

    remote_cmd = (
        f"cd {rdir} && sed -i 's/\\r$//' {AGENT.name} 2>/dev/null; "
        f"python3 -m pip install --user -q requests psutil 2>/dev/null; "
    )
    if args.foreground:
        remote_cmd += f"exec python3 {AGENT.name}"
        print("[note10-start] SSH (foreground, Strg+C beendet) ...", flush=True)
        return subprocess.run(ssh + ["bash", "-lc", remote_cmd]).returncode

    remote_cmd += (
        f"nohup python3 {AGENT.name} >> /tmp/ddgk_note10.log 2>&1 & echo STARTED_PID_$!"
    )
    print("[note10-start] SSH start (Hintergrund, Log /tmp/ddgk_note10.log) ...", flush=True)
    r = subprocess.run(ssh + ["bash", "-lc", remote_cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout or r.stderr or "", flush=True)
    if r.returncode != 0:
        return r.returncode

    print(f"[note10-start] Health test: curl http://{host}:5001/health  (NOTE10_DDGK_URL=http://{host}:5001)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
