#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Credential-Scanner: alle Workspaces, Extensions, System"""
import re, pathlib, json, os

found = {}

def check_text(path, txt):
    for tok in re.findall(r'hf_[A-Za-z0-9]{20,}', txt):
        found[str(path)] = {"type": "HF_TOKEN", "val": tok}
    for tok in re.findall(r'ghp_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,}', txt):
        if str(path) not in found:
            found[str(path)] = {"type": "GITHUB_TOKEN", "val": tok}
    for tok in re.findall(r'zenodo[_\-]?token["\s:=]+([A-Za-z0-9\-]{20,})', txt, re.IGNORECASE):
        found[str(path) + "_ZENODO"] = {"type": "ZENODO_TOKEN", "val": tok[:16] + "..."}
    for tok in re.findall(r'serpapi[_\-]?key["\s:=]+([A-Za-z0-9]{20,})', txt, re.IGNORECASE):
        found[str(path) + "_SERP"] = {"type": "SERPAPI_KEY", "val": tok[:12] + "..."}

# 1. System-Umgebungsvariablen
print("=== SYSTEM ENV VARS ===")
for key in ["HF_TOKEN", "HUGGINGFACE_TOKEN", "HUGGING_FACE_HUB_TOKEN",
            "GITHUB_TOKEN", "ZENODO_TOKEN", "SERPAPI_KEY"]:
    val = os.environ.get(key, "")
    if val:
        found[f"ENV:{key}"] = {"type": key, "val": val[:8] + "..."}
        print(f"  {key} = {val[:8]}...")
    else:
        print(f"  {key} = (nicht gesetzt)")

# 2. Cursor Global Settings
print("\n=== CURSOR/VSCODE SETTINGS ===")
for p in [
    pathlib.Path.home() / "AppData/Roaming/Cursor/User/settings.json",
    pathlib.Path.home() / "AppData/Roaming/Code/User/settings.json",
    pathlib.Path.home() / ".cursor/mcp.json",
]:
    if p.exists():
        try:
            txt = p.read_text(errors="ignore")[:8000]
            check_text(p, txt)
            print(f"  Gelesen: {p}")
            for tok in re.findall(r'hf_[A-Za-z0-9]{20,}', txt):
                print(f"    HF_TOKEN gefunden: {tok[:12]}...")
            for tok in re.findall(r'ghp_[A-Za-z0-9]{36,}', txt):
                print(f"    GITHUB_TOKEN: {tok[:12]}...")
        except Exception as ex:
            print(f"  Fehler: {p}: {ex}")

# 3. Alle .cursor/projects Workspaces
print("\n=== ANDERE CURSOR-WORKSPACES ===")
cursor_projects = pathlib.Path(r"C:\Users\annah\.cursor\projects")
if cursor_projects.exists():
    for proj in sorted(cursor_projects.iterdir()):
        if not proj.is_dir(): continue
        for ext in ["*.ini", "*.env", "*.json", "*.txt", "*.cfg"]:
            for f in list(proj.glob(ext))[:5]:
                try:
                    txt = f.read_text(errors="ignore")[:5000]
                    before = len(found)
                    check_text(f, txt)
                    if len(found) > before:
                        print(f"  TREFFER: {f}")
                except: pass

# 4. ORION-ROS2 Workspace komplett
print("\n=== ORION-ROS2 WORKSPACE ===")
ws = pathlib.Path(r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\ORION-ROS2-Consciousness-Node")
for pattern in ["*.ini", "*.env", "*.txt", "*.json", "*.cfg", "*.key"]:
    for f in ws.rglob(pattern):
        if any(x in str(f) for x in ["node_modules", ".git", "__pycache__", "output"]): continue
        try:
            txt = f.read_text(errors="ignore")[:5000]
            before = len(found)
            check_text(f, txt)
            if len(found) > before:
                print(f"  TREFFER: {f.name}")
        except: pass

# 5. HuggingFace CLI Cache
print("\n=== HUGGINGFACE CLI TOKEN ===")
hf_token_paths = [
    pathlib.Path.home() / ".cache/huggingface/token",
    pathlib.Path.home() / ".huggingface/token",
]
for p in hf_token_paths:
    if p.exists():
        try:
            tok = p.read_text().strip()
            found[str(p)] = {"type": "HF_TOKEN", "val": tok}
            print(f"  HF Token in {p}: {tok[:12]}...")
        except: pass
    else:
        print(f"  Nicht vorhanden: {p}")

# 6. Git-Credential-Manager
print("\n=== GIT CREDENTIALS ===")

# Zusammenfassung
print("\n" + "="*60)
print("ZUSAMMENFASSUNG GEFUNDENE CREDENTIALS:")
if found:
    for k, v in found.items():
        pth = str(k)[-60:] if len(str(k)) > 60 else str(k)
        print(f"  [{v['type']}] ...{pth}")
else:
    print("  Keine automatisch gefunden")
print("="*60)
