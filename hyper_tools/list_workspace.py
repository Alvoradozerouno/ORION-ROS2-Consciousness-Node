TOOL_NAME = "list_workspace"
TOOL_DESC = "Workspace-Dateien auflisten"
import pathlib

def run(args: dict) -> dict:
    base = pathlib.Path(__file__).parent.parent
    pattern = args.get("pattern", "*.py")
    files = list(base.glob(pattern))
    return {"status": "OK", "tool": "list_workspace",
            "result": {"count": len(files),
                       "files": [f.name for f in files[:20]],
                       "pattern": pattern}}
