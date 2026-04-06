import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from orion_autorun import action_log_rotate
action_log_rotate()
print("Log-Rotation abgeschlossen.")
import psutil
d = psutil.disk_usage("C:\\")
r = psutil.virtual_memory()
print(f"Disk: {d.percent:.1f}% | {d.free/(1024**3):.1f}GB frei")
print(f"RAM:  {r.percent:.1f}% | {r.available/(1024**3):.1f}GB frei")
