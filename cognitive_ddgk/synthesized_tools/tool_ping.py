# Auto-synthesized by HyperAgent
# Netzwerk-Ping zu Host
# Created: 2026-03-30T09:51:43.048619

def tool_ping(input_str: str) -> dict:
    import socket, time
    host = input_str.replace("ping:", "").strip() or "8.8.8.8"
    try:
        t0 = time.time()
        socket.setdefaulttimeout(3)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, 80))
        latency = round((time.time() - t0) * 1000, 1)
        return {"status": "OK", "result": f"Host {host} erreichbar | Latenz: {latency}ms", "error": None}
    except Exception as e:
        return {"status": "ERROR", "result": f"Host {host} nicht erreichbar", "error": str(e)[:60]}
