#!/usr/bin/env python3
# Agent 16: Performance Monitor Agent
# DDGK 3.34 Framework
import datetime
import json
import sys


def execute(payload):
    base = {
        "agent_id": 16,
        "description": "Performance Monitor Agent",
        "status": "READY",
        "timestamp": datetime.datetime.now().isoformat(),
        "result": payload,
    }
    try:
        p = json.loads(payload) if isinstance(payload, str) else payload
    except json.JSONDecodeError:
        return base
    if isinstance(p, dict) and p.get("mission") == "EDGE_CLUSTER":
        pr = p.get("probes") or {}
        oll = pr.get("ollama") if isinstance(pr, dict) else None
        ok_ct = 0
        checked = 0
        if isinstance(oll, dict) and not oll.get("skipped"):
            for _n, row in oll.items():
                if isinstance(row, dict):
                    if not row.get("skipped"):
                        checked += 1
                    if row.get("einsatzbereit"):
                        ok_ct += 1
        nd = pr.get("note10_ddgk") if isinstance(pr, dict) else {}
        base["edge_performance"] = {
            "phase": p.get("phase"),
            "prior_agent_phases": p.get("aggregate_keys"),
            "ollama_reachable_nodes": ok_ct,
            "ollama_checked_nodes": checked,
            "note10_ddgk_reachable": bool(nd.get("ok")),
        }
    return base


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(json.dumps(execute(sys.argv[1])))
    else:
        print(json.dumps({"status": "AGENT_16_READY"}))
