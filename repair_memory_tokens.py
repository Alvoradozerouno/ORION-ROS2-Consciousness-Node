#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entfernt Secrets aus cognitive_memory.jsonl und rebuilt die SHA-256 Kette.
Ersetzt GitHub PAT und HF Token durch Platzhalter.
"""
import json, hashlib, pathlib, re

MEM = pathlib.Path(r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\ORION-ROS2-Consciousness-Node\cognitive_ddgk\cognitive_memory.jsonl")

# Backup
backup = MEM.with_suffix(".jsonl.bak2")
import shutil
shutil.copy2(MEM, backup)
print(f"Backup: {backup}")

# Laden
lines = [l for l in MEM.read_text("utf-8").splitlines() if l.strip()]
print(f"Eintraege geladen: {len(lines)}")

# Bereinigen: GitHub Token (ghp_...) und HF Token (hf_...) ersetzen
def redact_secrets(obj):
    """Rekursiv Secrets in dict/str ersetzen"""
    if isinstance(obj, dict):
        return {k: redact_secrets(v) for k, v in obj.items()}
    elif isinstance(obj, str):
        # GitHub PAT (ghp_...)
        obj = re.sub(r'ghp_[A-Za-z0-9]{36,}', 'ghp_REDACTED', obj)
        # HF Token (hf_...)
        obj = re.sub(r'hf_[A-Za-z0-9]{20,}', 'hf_REDACTED', obj)
        # Zenodo Token (falls vorhanden)
        obj = re.sub(r'[A-Za-z0-9]{40,}(?=[^A-Za-z0-9]|$)', lambda m: m.group() if len(m.group()) < 60 else 'TOKEN_REDACTED', obj)
        return obj
    elif isinstance(obj, list):
        return [redact_secrets(i) for i in obj]
    return obj

# Alle Eintraege bereinigen und Kette neu aufbauen
entries = []
for line in lines:
    try:
        e = json.loads(line)
        # Secrets entfernen
        e = redact_secrets(e)
        entries.append(e)
    except Exception as ex:
        print(f"Parse-Fehler: {ex}")

# Chain neu aufbauen
print("Rebuilding SHA-256 chain...")
prev_hash = ""
for i, e in enumerate(entries):
    e["prev"] = prev_hash
    # Hash berechnen ohne "hash" Feld
    e_for_hash = {k: v for k, v in e.items() if k != "hash"}
    raw = json.dumps(e_for_hash, ensure_ascii=False, sort_keys=True)
    new_hash = hashlib.sha256(raw.encode()).hexdigest()
    e["hash"] = new_hash
    prev_hash = new_hash

print(f"Chain rebuilt: {len(entries)} Eintraege")

# Datei schreiben
MEM.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in entries) + "\n", encoding="utf-8")
print(f"Gespeichert: {MEM}")

# Verifizierung
lines_new = [l for l in MEM.read_text("utf-8").splitlines() if l.strip()]
breaks = 0
prev = ""
for line in lines_new:
    try:
        e = json.loads(line)
        if e.get("prev", "") != prev and prev != "":
            breaks += 1
        prev = e.get("hash", "")
    except: pass
print(f"Chain-Integritaet: {breaks} Brueche (sollte 0 sein)")
print(f"Eintraege: {len(lines_new)}")

# Pruefen ob Secrets noch vorhanden
content = MEM.read_text("utf-8")
if "ghp_S5Z" in content or "hf_OZRr" in content:
    print("WARNUNG: Secrets noch vorhanden!")
else:
    print("OK: Keine Secrets mehr in der Datei.")
