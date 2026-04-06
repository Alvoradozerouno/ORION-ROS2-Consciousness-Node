#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Note10 SSH / DDGK-Port pruefen (vom Laptop, gleiches WLAN).

  python note10_ssh_check.py

Nutzt NOTE10_SSH_HOST, NOTE10_SSH_PORT (Default 8022), optional NOTE10_DDGK_URL fuer Port 5001.
"""
from __future__ import annotations

import os
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
try:
    from workspace_env import load_workspace_dotenv

    load_workspace_dotenv(override=False)
except ImportError:
    pass


def tcp_ok(host: str, port: int, timeout: float = 3.0) -> tuple[bool, str]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        return True, "TCP connect OK"
    except socket.timeout:
        return False, "timeout (keine Antwort / geblockt)"
    except OSError as e:
        return False, str(e)[:120]


def main() -> int:
    host = (os.environ.get("NOTE10_SSH_HOST") or "").strip()
    port = int((os.environ.get("NOTE10_SSH_PORT") or "8022").strip() or "8022")
    ddgk = (os.environ.get("NOTE10_DDGK_URL") or "").strip()

    print("\n=== Note10 Erreichbarkeit (LAN) ===\n", flush=True)
    if not host:
        print("FEHL: NOTE10_SSH_HOST in .env setzen (oder note10_lan_discover.py).", flush=True)
        return 2

    print(f"Ziel: {host}", flush=True)
    ok, msg = tcp_ok(host, port, 4.0)
    print(f"  SSH ({port}/tcp):  {'OK' if ok else 'FAIL'} — {msg}", flush=True)

    if ddgk:
        p = urlparse(ddgk if "://" in ddgk else f"http://{ddgk}")
        h = p.hostname or host
        pr = p.port or 5001
        ok2, msg2 = tcp_ok(h, pr, 4.0)
        print(f"  DDGK ({pr}/tcp):  {'OK' if ok2 else 'FAIL'} — {msg2}", flush=True)
        if ok2:
            try:
                req = urllib.request.Request(
                    f"http://{h}:{pr}/health",
                    headers={"User-Agent": "note10_ssh_check/1"},
                )
                with urllib.request.urlopen(req, timeout=4) as r:
                    print(f"  HTTP /health:   HTTP {r.status}", flush=True)
            except urllib.error.HTTPError as e:
                print(f"  HTTP /health:   HTTP {e.code}", flush=True)
            except Exception as ex:
                print(f"  HTTP /health:   {ex}", flush=True)

    if not ok:
        print(
            "\n--- Typische Ursachen bei TIMEOUT ---\n"
            "  1) Falsche IP (DHCP): auf dem Phone in Termux: ip addr | grep inet\n"
            "  2) sshd laeuft nicht: termux -> sshd\n"
            "  3) WLAN Client-Isolation / Gaeste-WLAN: Laptop und Phone muessen sich sehen\n"
            "  4) Android Firewall / VPN am Phone oder Laptop testweise aus\n"
            "  5) Termux im Hintergrund gekillt: Akku-Optimierung fuer Termux aus\n"
            "  6) Anderer SSH-Port: in .env NOTE10_SSH_PORT anpassen\n"
            "  Scan: python note10_lan_discover.py\n",
            flush=True,
        )
        return 1

    print("\nTCP offen — wenn ssh trotzdem haengt: Passwort/SSH-Key pruefen.\n", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
