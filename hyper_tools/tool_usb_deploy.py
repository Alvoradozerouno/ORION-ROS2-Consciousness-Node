#!/usr/bin/env python3
"""Auto-fabriziert von ORION Lab | 2026-03-30T16:50:23.607050
Tool: tool_usb_deploy
Funktion: USB deployment: copy ORION to USB stick
"""
import os, shutil, psutil, json
from pathlib import Path

def run(params=None):
    params = params or {}
    BASE = Path(__file__).parent.parent.parent

    if "tool_usb_deploy" == "tool_usb_deploy":
        # Finde USB-Laufwerke
        usbs = []
        for p in psutil.disk_partitions():
            try:
                u = psutil.disk_usage(p.mountpoint)
                if p.device != "C:\\" and u.free > 2*1024**3:
                    usbs.append({"dev": p.device, "free_gb": round(u.free/1024**3,1)})
            except: pass
        return {"status":"OK","tool":"tool_usb_deploy","usb_drives":usbs,
                "message":f"{len(usbs)} USB-fähige Laufwerke gefunden"}

    elif "tool_usb_deploy" == "tool_disk_monitor":
        results = {}
        for p in psutil.disk_partitions():
            try:
                u = psutil.disk_usage(p.mountpoint)
                results[p.device] = {"percent":u.percent,"free_gb":round(u.free/1024**3,1),
                    "status":"KRIT" if u.percent>90 else ("WARN" if u.percent>75 else "OK")}
            except: pass
        return {"status":"OK","tool":"tool_usb_deploy","disks":results}

    elif "tool_usb_deploy" == "tool_lab_report":
        logs = list(BASE.rglob("*.jsonl"))
        total = sum(sum(1 for l in f.read_text("utf-8",errors="replace").splitlines() if l.strip())
                    for f in logs if f.exists())
        return {"status":"OK","tool":"tool_usb_deploy","jsonl_files":len(logs),"total_entries":total}

    return {"status":"OK","tool":"tool_usb_deploy"}

if __name__ == "__main__":
    print(run())
