# Auto-synthesized by HyperAgent
# JSON-Datei validieren
# Created: 2026-03-30T09:51:45.364222

def tool_json_validate(input_str: str) -> dict:
    import json, pathlib
    filepath = input_str.replace("json_validate:", "").strip()
    try:
        p = pathlib.Path(filepath)
        if not p.exists():
            return {"status": "ERROR", "result": "Datei nicht gefunden", "error": filepath}
        data = json.loads(p.read_text("utf-8"))
        return {"status": "OK", "result": f"Valides JSON | {len(str(data))} Zeichen | Typ: {type(data).__name__}", "error": None}
    except json.JSONDecodeError as e:
        return {"status": "ERROR", "result": "Ungültiges JSON", "error": str(e)[:80]}
    except Exception as e:
        return {"status": "ERROR", "result": "Fehler", "error": str(e)[:60]}
