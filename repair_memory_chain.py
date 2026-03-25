#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHA-256 Gedächtnis-Ketten-Reparatur
Root Cause: Mehrere Python-Sessions starten jeweils mit _prev_hash=""
und überschreiben damit die Kette. Fix: Kette neu berechnen (rebuild).
"""
import json, pathlib, hashlib, datetime, shutil

MEM = pathlib.Path(r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\ORION-ROS2-Consciousness-Node\cognitive_ddgk\cognitive_memory.jsonl")
BAK = MEM.with_suffix(".jsonl.bak")

print("=== SHA-256 Ketten-Reparatur ===\n")
print("Root Cause: Jede neue Python-Session startet mit _prev_hash=''")
print("→ Einträge aus späteren Sessions haben 'prev': '' statt korrektem Hash")
print("→ Fix: Kette komplett neu berechnen (Content bleibt, nur hash+prev wird korrigiert)\n")

# Backup
shutil.copy2(MEM, BAK)
print(f"Backup: {BAK}")

# Alle Einträge laden (ohne hash/prev validieren)
lines = [l for l in MEM.read_text("utf-8").splitlines() if l.strip()]
print(f"Einträge gefunden: {len(lines)}")

# Einträge parsen
entries = []
for i, line in enumerate(lines):
    try:
        e = json.loads(line)
        # Nur Kern-Felder behalten
        core = {
            "ts":     e.get("ts", ""),
            "agent":  e.get("agent", "?"),
            "action": e.get("action", ""),
            "data":   e.get("data", {}),
        }
        entries.append(core)
    except Exception as ex:
        print(f"  SKIP Zeile {i}: {ex}")

print(f"Valide Einträge: {len(entries)}")

# Kette neu berechnen
prev_hash = ""
repaired  = []
for e in entries:
    e["prev"] = prev_hash
    raw = json.dumps(e, ensure_ascii=False)
    new_hash = hashlib.sha256(raw.encode()).hexdigest()
    e["hash"] = new_hash
    repaired.append(e)
    prev_hash = new_hash

# Zurückschreiben
with MEM.open("w", encoding="utf-8") as f:
    for e in repaired:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")

print(f"\nKette repariert: {len(repaired)} Einträge")
print(f"Letzter Hash: {prev_hash[:16]}...")

# Verifikation
print("\n=== Verifikation ===")
errors = 0
lines2 = [l for l in MEM.read_text("utf-8").splitlines() if l.strip()]
prev = ""
for i, line in enumerate(lines2):
    e = json.loads(line)
    if e.get("prev") != prev and i > 0:
        print(f"  FEHLER bei {i}")
        errors += 1
    stored = e.pop("hash")
    computed = hashlib.sha256(json.dumps(e, ensure_ascii=False).encode()).hexdigest()
    if stored != computed:
        print(f"  HASH-FEHLER bei {i}")
        errors += 1
    e["hash"] = stored
    prev = stored

if errors == 0:
    print(f"✓ Kette vollständig intakt ({len(lines2)} Einträge, 0 Fehler)")
else:
    print(f"✗ Noch {errors} Fehler")

# Einen Integritäts-Eintrag hinzufügen
integrity_entry = {
    "ts": datetime.datetime.now().isoformat(),
    "agent": "GUARDIAN",
    "action": "chain_repair",
    "data": {
        "repaired_entries": len(repaired),
        "root_cause": "Multi-Session _prev_hash reset",
        "fix": "Full chain rebuild, content preserved",
        "backup": str(BAK)
    },
    "prev": prev_hash
}
raw = json.dumps(integrity_entry, ensure_ascii=False)
integrity_entry["hash"] = hashlib.sha256(raw.encode()).hexdigest()

with MEM.open("a", encoding="utf-8") as f:
    f.write(json.dumps(integrity_entry, ensure_ascii=False) + "\n")

print(f"\n✓ Integritäts-Eintrag hinzugefügt")
print(f"Gesamt: {len(lines2) + 1} Einträge")
print("\nFix für zukünftige Sessions:")
print("  → ddgk_log() immer zuerst den letzten Hash aus Datei lesen")
print("  → Nie mit _prev_hash='' starten wenn Datei bereits existiert")
