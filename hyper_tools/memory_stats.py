TOOL_NAME = "memory_stats"
TOOL_DESC = "DDGK Memory-Statistiken"
import pathlib, json

def run(args: dict) -> dict:
    base = pathlib.Path(__file__).parent.parent
    files = {
        "cognitive_memory": base / "cognitive_ddgk" / "cognitive_memory.jsonl",
        "loop_memory":      base / "cognitive_ddgk" / "autonomous_loop_memory.jsonl",
        "hyper_memory":     base / "cognitive_ddgk" / "hyper_agent_memory.jsonl",
        "nuclear_audit":    base / "cognitive_ddgk" / "nuclear_audit_chain.jsonl",
    }
    stats = {}
    for name, path in files.items():
        if path.exists():
            lines = [l for l in path.read_text("utf-8", errors="replace").splitlines() if l.strip()]
            stats[name] = len(lines)
        else:
            stats[name] = 0
    return {"status": "OK", "tool": "memory_stats", "result": stats}
