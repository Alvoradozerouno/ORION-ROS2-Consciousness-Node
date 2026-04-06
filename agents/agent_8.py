#!/usr/bin/env python3
# Agent 8: Hardware Optimierer Agent
# DDGK 3.34 Framework
import datetime
import json
import sys


def execute(payload):
    base = {
        "agent_id": 8,
        "description": "Hardware Optimierer Agent",
        "status": "READY",
        "timestamp": datetime.datetime.now().isoformat(),
        "result": payload,
    }
    try:
        p = json.loads(payload) if isinstance(payload, str) else payload
    except json.JSONDecodeError:
        return base
    if isinstance(p, dict) and p.get("mission") == "EDGE_CLUSTER":
        g = (p.get("probes") or {}).get("laptop_gpu") or {}
        base["edge_hardware"] = {
            "laptop_torch_cuda": g.get("torch_cuda"),
            "laptop_gpu_name": g.get("torch_device") or g.get("nvidia_smi"),
            "note10_ml_hint": "Auf Geraet: pip install tflite-runtime / tensorflow — siehe ddgk_note10_agent /health ml_edge",
        }
    return base


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(json.dumps(execute(sys.argv[1])))
    else:
        print(json.dumps({"status": "AGENT_8_READY"}))
