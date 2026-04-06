import json
from pathlib import Path
from datetime import datetime
from math import ceil, floor
from hashlib import sha256
from urllib.request import urlopen

def run(args):
    TOOL_NAME = "zaehle_wie_viele_jsonl_eintrae"
    TOOL_DESC = "Zaehlt die Anzahl und die Größe der JSONL-Einträge in Cognitive Memory."

    # Check if the input file exists and is a valid path
    if not Path(args.input_file).exists():
        return {"status": "ERROR", "result": None, "tool": TOOL_NAME}

    try:
        with urlopen(args.input_file) as response:
            data = json.load(response)
    except Exception as e:
        return {"status": "ERROR", "result": str(e), "tool": TOOL_NAME}

    # Calculate the total size of all JSONL entries
    total_size = 0
    for entry in data:
        if isinstance(entry, dict) and "text" in entry:
            text = entry["text"]
            total_size += len(text.encode("utf-8"))

    return {"status": "OK", "result": total_size / (1024 * 1024), "tool": TOOL_NAME}