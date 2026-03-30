# Auto-synthesized by HyperAgent
# Systemzeit abfragen
# Created: 2026-03-30T09:51:45.145815

def tool_system_time(input_str: str) -> dict:
    import datetime, platform
    now = datetime.datetime.now()
    return {
        "status": "OK",
        "result": f"Zeit: {now.strftime('%Y-%m-%d %H:%M:%S')} | OS: {platform.system()} {platform.release()}",
        "error": None
    }
