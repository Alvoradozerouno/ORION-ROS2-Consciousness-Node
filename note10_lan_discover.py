#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Note10 im privaten Netz (WLAN + USB-Tethering) finden.

Sucht auf allen lokalen IPv4-/24-Subnetzen nach:
  - TCP 5001  → DDGK note10 agent (HTTP /health)
  - TCP 11434 → Ollama
  - TCP 8022  → Termux sshd (optionaler Hinweis)

Nur RFC1918-Adressen; keine öffentlichen Ranges. Liest optional .env (workspace_env).

Ausgabe: Vorschläge für OLLAMA_NOTE10 und NOTE10_DDGK_URL (keine Secrets).

  python note10_lan_discover.py
  python note10_lan_discover.py --timeout 0.35 --workers 64
"""
from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

try:
    from workspace_env import load_workspace_dotenv

    load_workspace_dotenv(override=False)
except ImportError:
    pass


def _host_from_base_url(url: str) -> str | None:
    u = (url or "").strip().rstrip("/")
    if not u:
        return None
    u = u.replace("http://", "").replace("https://", "")
    if "/" in u:
        u = u.split("/", 1)[0]
    if ":" in u:
        u = u.rsplit(":", 1)[0]
    return u if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", u) else None

PORTS_DDGK = 5001
PORTS_OLLAMA = 11434
PORTS_TERMUX_SSH = 8022


def _is_private_ipv4(ip: str) -> bool:
    p = ip.split(".")
    if len(p) != 4:
        return False
    try:
        a, b, c, d = (int(x) for x in p)
    except ValueError:
        return False
    if a == 10:
        return True
    if a == 172 and 16 <= b <= 31:
        return True
    if a == 192 and b == 168:
        return True
    return False


def local_ipv4_addresses() -> list[str]:
    ips: list[str] = []
    try:
        import psutil

        for addrs in psutil.net_if_addrs().values():
            for a in addrs:
                if getattr(a, "family", None) != socket.AF_INET:
                    continue
                ip = (a.address or "").strip()
                if ip and not ip.startswith("127.") and _is_private_ipv4(ip):
                    ips.append(ip)
    except ImportError:
        pass
    if sys.platform == "win32":
        try:
            r = subprocess.run(
                ["ipconfig"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
            )
            for m in re.finditer(
                r"IPv4[^:\r\n]*:\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",
                r.stdout or "",
                re.I,
            ):
                ip = m.group(1)
                if not ip.startswith("127.") and _is_private_ipv4(ip) and ip not in ips:
                    ips.append(ip)
        except (subprocess.TimeoutExpired, OSError):
            pass
    return list(dict.fromkeys(ips))


def subnet_bases_from_ips(ips: list[str]) -> list[str]:
    bases: list[str] = []
    for ip in ips:
        parts = ip.split(".")
        if len(parts) == 4:
            b = f"{parts[0]}.{parts[1]}.{parts[2]}."
            if b not in bases:
                bases.append(b)
    return bases


def tcp_open(host: str, port: int, timeout: float) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            return s.connect_ex((host, port)) == 0
        finally:
            s.close()
    except OSError:
        return False


def fetch_ddgk_health(ip: str, port: int, timeout: float) -> dict[str, Any]:
    url = f"http://{ip}:{port}/health"
    out: dict[str, Any] = {"url": url, "ok": False}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ORION-note10-discover/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(12000).decode("utf-8", errors="replace")
            data = json.loads(raw)
            out["ok"] = True
            out["node"] = data.get("node")
            out["type"] = data.get("type")
            out["status"] = data.get("status")
    except Exception as ex:
        out["error"] = str(ex)[:120]
    return out


def fetch_ollama_version(ip: str, port: int, timeout: float) -> dict[str, Any]:
    url = f"http://{ip}:{port}/api/version"
    out: dict[str, Any] = {"url": url, "ok": False}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ORION-note10-discover/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(4000).decode("utf-8", errors="replace")
            out["json"] = json.loads(raw)
            out["ok"] = True
    except Exception as ex:
        out["error"] = str(ex)[:120]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Note10 / Edge-Gerät im LAN suchen")
    ap.add_argument("--timeout", type=float, default=0.35, help="TCP connect timeout (s)")
    ap.add_argument("--http-timeout", type=float, default=3.0, help="HTTP probe timeout (s)")
    ap.add_argument("--workers", type=int, default=48, help="Parallel TCP probes")
    ap.add_argument("--json-out", type=str, default="", help="Optional: Report-JSON Pfad")
    args = ap.parse_args()

    my_ips = local_ipv4_addresses()
    bases = subnet_bases_from_ips(my_ips)
    if not bases:
        print("[note10-discover] Keine privaten IPv4-Adressen gefunden (WLAN/USB aktiv?).", flush=True)
        return 2

    print(f"[note10-discover] Lokale IPs: {', '.join(my_ips)}", flush=True)
    print(f"[note10-discover] Scanne /24-Subnetze: {[b + '0/24' for b in bases]}", flush=True)

    candidates: list[tuple[str, int]] = []
    for base in bases:
        for i in range(1, 255):
            host = f"{base}{i}"
            if host in my_ips:
                continue
            for port in (PORTS_DDGK, PORTS_OLLAMA, PORTS_TERMUX_SSH):
                candidates.append((host, port))

    open_ports: list[tuple[str, int]] = []
    with ThreadPoolExecutor(max_workers=max(8, min(args.workers, 128))) as ex:
        futs = {
            ex.submit(tcp_open, h, p, args.timeout): (h, p) for h, p in candidates
        }
        for fut in as_completed(futs):
            h, p = futs[fut]
            try:
                if fut.result():
                    open_ports.append((h, p))
            except Exception:
                pass

    by_ip: dict[str, set[int]] = {}
    for h, p in open_ports:
        by_ip.setdefault(h, set()).add(p)

    ddgk_hits: list[dict[str, Any]] = []
    ollama_hits: list[dict[str, Any]] = []
    for ip, ports in sorted(by_ip.items(), key=lambda x: x[0]):
        if PORTS_DDGK in ports:
            info = fetch_ddgk_health(ip, PORTS_DDGK, args.http_timeout)
            info["ip"] = ip
            ddgk_hits.append(info)
        if PORTS_OLLAMA in ports:
            ov = fetch_ollama_version(ip, PORTS_OLLAMA, args.http_timeout)
            ov["ip"] = ip
            ollama_hits.append(ov)

    print("\n=== Ergebnis ===\n", flush=True)
    note10_ip: str | None = None
    for h in ddgk_hits:
        node = (h.get("node") or "").lower()
        if h.get("ok") and ("note10" in node or "mobile" in node or "ddgk" in node):
            print(f"  DDGK-Mobile-Kandidat: http://{h['ip']}:{PORTS_DDGK}/health", flush=True)
            print(f"    node={h.get('node')!r} type={h.get('type')!r} status={h.get('status')!r}", flush=True)
            if note10_ip is None:
                note10_ip = h["ip"]
        elif h.get("ok"):
            print(f"  HTTP :{PORTS_DDGK} auf {h['ip']} (anderer Dienst): node={h.get('node')!r}", flush=True)
        else:
            print(f"  TCP :{PORTS_DDGK} offen auf {h['ip']}, HTTP nicht DDGK: {h.get('error')}", flush=True)

    for o in ollama_hits:
        if o.get("ok"):
            print(
                f"  Ollama: http://{o['ip']}:{PORTS_OLLAMA}  version={o.get('json', {}).get('version', '?')}",
                flush=True,
            )
        else:
            print(f"  TCP :{PORTS_OLLAMA} offen auf {o['ip']}, HTTP: {o.get('error')}", flush=True)

    for ip, ports in sorted(by_ip.items(), key=lambda x: x[0]):
        if PORTS_TERMUX_SSH in ports and PORTS_DDGK not in ports and PORTS_OLLAMA not in ports:
            print(f"  Termux-SSH moeglich: {ip}:{PORTS_TERMUX_SSH} (nur Port offen)", flush=True)

    if not open_ports:
        print("  Keine offenen Ports 5001/11434/8022 auf den gescannten Subnetzen.", flush=True)

    print("\n--- .env (Vorschlag, Werte anpassen) ---\n", flush=True)
    if note10_ip:
        print(f"NOTE10_DDGK_URL=http://{note10_ip}:{PORTS_DDGK}", flush=True)
    elif ddgk_hits and ddgk_hits[0].get("ok"):
        ip0 = ddgk_hits[0]["ip"]
        print(f"NOTE10_DDGK_URL=http://{ip0}:{PORTS_DDGK}", flush=True)
    else:
        print("# NOTE10_DDGK_URL=   # kein DDGK /health gefunden", flush=True)

    # Pi5 aus .env; falls leer: gleicher Default wie ollama_nodes_scan (nur fuer Ausschluss-Vorschlag)
    _pi5_url = (os.environ.get("OLLAMA_PI5") or "").strip() or "http://192.168.1.103:11434"
    pi5_ip = _host_from_base_url(_pi5_url)
    laptop_ip = _host_from_base_url(os.environ.get("OLLAMA_HOST", "")) or _host_from_base_url(
        "http://127.0.0.1:11434"
    )
    skip_ollama = {x for x in (pi5_ip, "127.0.0.1", "localhost") if x}
    skip_ollama.update(my_ips)  # Laptop selbst nicht als „Note10“

    ollama_ip = note10_ip
    if not ollama_ip and ollama_hits:
        ddgk_ips = {h["ip"] for h in ddgk_hits if h.get("ok")}
        for o in ollama_hits:
            if o.get("ok") and o["ip"] in ddgk_ips:
                ollama_ip = o["ip"]
                break
        if not ollama_ip:
            others = [o["ip"] for o in ollama_hits if o.get("ok") and o["ip"] not in skip_ollama]
            if others:
                ollama_ip = others[0]
            else:
                ollama_ip = next((o["ip"] for o in ollama_hits if o.get("ok")), None)
    if ollama_ip:
        print(f"OLLAMA_NOTE10=http://{ollama_ip}:{PORTS_OLLAMA}", flush=True)
        if pi5_ip and ollama_ip == pi5_ip:
            print("# Hinweis: Treffer entspricht OLLAMA_PI5 — zweites Ollama-Gerät suchen oder Agent auf Note10 starten.", flush=True)
    else:
        if ollama_hits:
            print(
                "# OLLAMA_NOTE10=   # nur Pi5/Laptop als Ollama erkannt — Note10: Ollama in Termux starten oder USB-Subnetz prüfen",
                flush=True,
            )
        else:
            print("# OLLAMA_NOTE10=   # kein Ollama auf 11434 gefunden", flush=True)

    report = {
        "local_ips": my_ips,
        "subnets": [b + "0/24" for b in bases],
        "open_port_hits": [{"ip": h, "port": p} for h, p in sorted(open_ports)],
        "ddgk_health": ddgk_hits,
        "ollama_version": ollama_hits,
    }
    if args.json_out:
        p = os.path.abspath(args.json_out)
        os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\nJSON: {p}\n", flush=True)

    return 0 if (ddgk_hits or ollama_hits) else 1


if __name__ == "__main__":
    sys.exit(main())
