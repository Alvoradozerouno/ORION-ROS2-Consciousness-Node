import pathlib, re, json

ws = pathlib.Path(r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\ORION-ROS2-Consciousness-Node")

files = [
    "zenodo_update_v4.py",
    "ORION_DDGK_SSH_ORCHESTRATOR.py",
    "ORION_DDGK_FULL_EXECUTOR.py",
    "ZENODO_UPLOAD/zenodo_deposit_result.json",
    "ZENODO_UPLOAD/zenodo_metadata.json",
    "ZENODO_UPLOAD/ORION_SSH_REPORT.json",
]

found = {}
for fn in files:
    f = ws / fn
    if not f.exists():
        print(f"  FEHLT: {fn}")
        continue
    txt = f.read_text("utf-8", errors="ignore")
    hits = {}
    patterns = [
        (r"hf_[A-Za-z0-9]{20,}", "HF_TOKEN"),
        (r"ghp_[A-Za-z0-9]{36}", "GITHUB_PAT"),
        (r"github_pat_[A-Za-z0-9_]{40,}", "GITHUB_PAT2"),
        (r'"access_token"\s*:\s*"([^"]{10,})"', "ZENODO_ACCESS"),
        (r'ZENODO_API_TOKEN\s*=\s*["\']?([A-Za-z0-9]{20,})', "ZENODO_API"),
        (r'token\s*=\s*["\']([A-Za-z0-9\-_]{20,})["\']', "TOKEN_VAR"),
    ]
    for pat, name in patterns:
        m = re.search(pat, txt)
        if m:
            g = m.group(1) if m.lastindex and m.lastindex >= 1 else m.group()
            hits[name] = g[:24] + "..."
    if hits:
        found[fn] = hits
        print(f"[FOUND] {fn}: {hits}")
    else:
        print(f"  geprüft: {fn} ({len(txt)} chars) — keine Tokens")

print("\n--- JSON Deposit ---")
dep = ws / "ZENODO_UPLOAD" / "zenodo_deposit_result.json"
if dep.exists():
    d = json.loads(dep.read_text("utf-8", errors="ignore"))
    print(f"  deposit_id: {d.get('id','?')}")
    print(f"  doi: {d.get('doi','?') or d.get('metadata',{}).get('doi','?')}")
    print(f"  links: {list(d.get('links',{}).keys())[:5]}")
