TOOL_NAME = "check_kappa"
TOOL_DESC = "CCRN kappa-Kohaerenz pruefen"
import sys, json, pathlib, math
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

def run(args: dict) -> dict:
    try:
        cs = pathlib.Path(__file__).parent.parent / "cognitive_ddgk" / "cognitive_state.json"
        state = json.loads(cs.read_text("utf-8")) if cs.exists() else {}
        kappa = state.get("kappa_current", 0)
        ccrn  = state.get("ccrn_active", False)
        return {"status": "OK", "tool": "check_kappa",
                "result": {"kappa": kappa, "ccrn_active": ccrn,
                           "threshold_ok": kappa >= 2.0}}
    except Exception as e:
        return {"status": "ERROR", "tool": "check_kappa", "result": str(e)}
