#!/usr/bin/env python3
# Agent 2: Forschungs- & Analyse Agent
# DDGK 3.34 Framework
import datetime
import json
import sys
from pathlib import Path


def execute(payload):
    base = {
        "agent_id": 2,
        "description": "Forschungs- & Analyse Agent",
        "status": "READY",
        "timestamp": datetime.datetime.now().isoformat(),
        "result": payload,
    }
    try:
        p = json.loads(payload) if isinstance(payload, str) else payload
    except json.JSONDecodeError:
        return base
    if isinstance(p, dict) and p.get("mission") == "EDGE_CLUSTER":
        root = Path(__file__).resolve().parent.parent
        files = [
            "ddgk_note10_agent.py",
            "NOTE10_SETUP.md",
            "ollama_nodes_scan.py",
            "DDGK_EDGE_CLUSTER_ASSEMBLY.py",
            "MULTI_AGENT_ASSET_ANALYSIS.py",
        ]
        base["edge_workspace_hits"] = {f: (root / f).is_file() for f in files}
        pr = p.get("probes") or {}
        base["probe_topics"] = list(pr.keys()) if isinstance(pr, dict) else []
    return base


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(json.dumps(execute(sys.argv[1])))
    else:
        print(json.dumps({"status": "AGENT_2_READY"}))
