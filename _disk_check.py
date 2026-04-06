import os, psutil
from pathlib import Path

def sz(b): return f"{b/(1024**3):.2f}GB"

print("="*55)
print("  ORION DISK ANALYSE — schnell + präzise")
print("="*55)

d = psutil.disk_usage("C:\\")
print(f"\n  C:\\ gesamt: {sz(d.total)} | genutzt: {sz(d.used)} | frei: {sz(d.free)} | {d.percent:.1f}%")

# Bekannte Groß-Verzeichnisse direkt prüfen
targets = [
    Path(r"C:\Users\annah\.ollama"),
    Path(r"C:\Users\annah\AppData\Local\Temp"),
    Path(r"C:\Users\annah\AppData\Local\pip"),
    Path(r"C:\Users\annah\AppData\Roaming\Cursor"),
    Path(r"C:\Users\annah\AppData\Local\cursor-updater"),
    Path(r"C:\Windows\Temp"),
    Path(r"C:\Users\annah\AppData\Local\Programs\Ollama"),
]

print("\n  [BEKANNTE PLATZKILLER]")
for t in targets:
    if not t.exists():
        print(f"  {'n/a':>8}  {t}")
        continue
    total = 0
    count = 0
    try:
        for f in t.rglob("*"):
            try:
                if f.is_file():
                    total += f.stat().st_size
                    count += 1
            except: pass
        icon = "🔴" if total > 5*(1024**3) else "🟡" if total > 1*(1024**3) else "🟢"
        print(f"  {icon} {sz(total):>8}  ({count} Dateien)  {t}")
    except Exception as e:
        print(f"  ⚠️  {t}: {e}")

# Ollama Modelle details
print("\n  [OLLAMA MODELLE]")
ollama_models = Path(r"C:\Users\annah\.ollama\models\blobs")
if ollama_models.exists():
    models = []
    for f in ollama_models.glob("sha256-*"):
        if f.is_file():
            models.append((f.stat().st_size, f.name[:30]))
    for s, n in sorted(models, reverse=True)[:10]:
        print(f"    {sz(s):>8}  {n}")
    print(f"    GESAMT: {sz(sum(s for s,_ in models))} — {len(models)} Blobs")
else:
    print("  ollama/models/blobs nicht gefunden")

print("\n  [EMPFEHLUNG — Sofort freigeben]")
print("  1. Ollama-Modelle entfernen die nicht genutzt werden:")
print("     ollama list  →  ollama rm <modell>")
print("  2. Windows Temp bereinigen: cleanmgr /sagerun:1")
print("  3. Cursor-Cache in AppData/Roaming/Cursor leeren")
print("="*55)
