#!/usr/bin/env python3
import pathlib, json, re, os

results = {}

def scan(path, txt):
    p = str(path)
    for m in re.findall(r'hf_[A-Za-z0-9]{20,}', txt):
        results[p] = {"type": "HF_TOKEN", "full": m}
    for m in re.findall(r'ghp_[A-Za-z0-9]{36,}', txt):
        results[p+"_gh"] = {"type": "GITHUB", "full": m}
    for m in re.findall(r'(?i)ZENODO[_A-Z]*[\s:=]+([A-Za-z0-9\-]{20,})', txt):
        results[p+"_z"] = {"type": "ZENODO", "full": m}
    for m in re.findall(r'(?i)SERPAPI[_A-Z]*[\s:=]+([A-Za-z0-9]{20,})', txt):
        results[p+"_s"] = {"type": "SERP", "full": m}

# MCP Config
mcp = pathlib.Path(r"C:\Users\annah\.cursor\mcp.json")
if mcp.exists():
    txt = mcp.read_text(errors="ignore")
    scan(mcp, txt)
    print("MCP.JSON gelesen")

# EIRA Ordner
eira = pathlib.Path(r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\ORION-ROS2-Consciousness-Node\EIRA")
if eira.exists():
    for f in eira.rglob("*"):
        if f.is_file():
            try:
                scan(f, f.read_text(errors="ignore")[:3000])
            except: pass

# Repos Ordner
repos = pathlib.Path(r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\ORION-ROS2-Consciousness-Node\repos")
if repos.exists():
    for f in list(repos.rglob("*.env"))[:20] + list(repos.rglob("*.ini"))[:20]:
        try:
            scan(f, f.read_text(errors="ignore")[:3000])
        except: pass

# Downloads direkt
dl = pathlib.Path(r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads")
for f in list(dl.glob("*.env")) + list(dl.glob("*.ini")) + list(dl.glob("*.txt")):
    try:
        scan(f, f.read_text(errors="ignore")[:2000])
    except: pass

# HF CLI Token-Datei
for p in [
    pathlib.Path(r"C:\Users\annah\.cache\huggingface\token"),
    pathlib.Path(r"C:\Users\annah\.huggingface\token"),
]:
    if p.exists():
        tok = p.read_text().strip()
        results[str(p)] = {"type": "HF_TOKEN", "full": tok}
        print(f"HF CLI Token gefunden: {p}")

# Andere Cursor-Projekte
cursor_proj = pathlib.Path(r"C:\Users\annah\.cursor\projects")
if cursor_proj.exists():
    for proj in cursor_proj.iterdir():
        for f in list(proj.glob("*.env"))[:3] + list(proj.glob("*.ini"))[:3]:
            try:
                scan(f, f.read_text(errors="ignore")[:3000])
            except: pass

print("\n=== ERGEBNIS ===")
if results:
    for k, v in results.items():
        fname = str(k)[-50:]
        print(f"[{v['type']}] ...{fname}")
        print(f"   -> {v['full'][:20]}...")
else:
    print("Keine API-Tokens gefunden.")
    print("\nFazit: Bitte manuell HuggingFace-Token erstellen:")
    print("  1. https://huggingface.co/settings/tokens")
    print("  2. Token in .env Datei eintragen")
    print("  3. Oder: hf auth login im Terminal")
