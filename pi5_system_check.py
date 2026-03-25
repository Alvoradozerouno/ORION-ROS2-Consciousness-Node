#!/usr/bin/env python3
import paramiko, sys

PI5  = "192.168.1.103"
USER = "alvoradozerouno"
PASS = "follow43"

def ssh_run(c, cmd, timeout=10):
    si, so, se = c.exec_command(cmd, timeout=timeout)
    out = so.read().decode("utf-8", errors="replace").strip()
    err = se.read().decode("utf-8", errors="replace").strip()
    return out, err

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(PI5, 22, USER, PASS, timeout=8)
print("=== PI5 SYSTEM-CHECK ===\n")

checks = [
    ("Hostname",          "hostname"),
    ("Ollama Version",    "ollama --version 2>/dev/null || echo NOT_INSTALLED"),
    ("Ollama Modelle",    "ollama list 2>/dev/null || echo NO_MODELS"),
    ("Ollama Prozess",    "pgrep -a ollama 2>/dev/null || echo not_running"),
    ("Ollama Port 11434", "ss -tlnp 2>/dev/null | grep 11434 || echo closed"),
    ("Python3",           "python3 --version"),
    ("pip3",              "pip3 --version 2>/dev/null | head -1"),
    ("RAM",               "free -h | head -2"),
    ("CPU Kerne",         "nproc"),
    ("Disk",              "df -h / | tail -1"),
    ("IP Adressen",       "hostname -I"),
    ("ORION Ordner",      "ls ~/orion 2>/dev/null || ls ~/ORION 2>/dev/null || echo no_orion_dir"),
    ("Home Inhalt",       "ls ~ | head -15"),
    ("Systemd Ollama",    "systemctl is-active ollama 2>/dev/null || echo no_service"),
]

for title, cmd in checks:
    out, err = ssh_run(c, cmd)
    combined = out or err or "(leer)"
    print(f"  [{title}]")
    for line in combined.split("\n")[:3]:
        print(f"    {line}")
    print()

c.close()
print("=== ENDE ===")
