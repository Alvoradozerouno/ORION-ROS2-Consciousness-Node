#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Laedt aktuelle Artefakte auf einen Zenodo-Draft-Deposit hoch.
Token: ZENODO_API_TOKEN oder ZENODO_TOKEN (Umgebung) bzw. in master.env.ini (siehe workspace_env).
"""
import json, os, pathlib, re, urllib.request, urllib.error

WS = pathlib.Path(__file__).resolve().parent
try:
    from workspace_env import load_workspace_dotenv, resolve_master_ini_path

    load_workspace_dotenv(override=False)
except ImportError:
    pass
BASE = "https://zenodo.org/api"

FILES = [
    WS / "ZENODO_UPLOAD" / "CCRN_METRIC_FORMALIZATION_v2.1.md",
    WS / "ZENODO_UPLOAD" / "OVI_WINDOWS_REPORT.json",
    WS / "ZENODO_UPLOAD" / "ovi_by_day.csv",
    WS / "ZENODO_UPLOAD" / "WORKSPACE_SCAN_DDGK.json",
    WS / "ZENODO_UPLOAD" / "WWW_RESEARCH_SNAPSHOT.json",
    WS / "ZENODO_UPLOAD" / "WWW_RESEARCH_LIVE.json",
    WS / "ZENODO_UPLOAD" / "DDGK_FORTSCHRITT_REPORT.json",
    WS / "fortschritt_runden_output.txt",
    WS / "ZENODO_UPLOAD" / "DDGK_CURSOR_NETZ_REPORT.json",
    WS / "cursor_netz_diskussion_output.txt",
]

def token() -> str | None:
    for key in ("ZENODO_API_TOKEN", "ZENODO_TOKEN"):
        t = os.environ.get(key, "").strip()
        if t:
            return t
    try:
        from workspace_env import resolve_master_ini_path

        ini = resolve_master_ini_path()
    except ImportError:
        ini = None
    if ini is None or not ini.is_file():
        return None
    txt = ini.read_text("utf-8", errors="replace")
    for pat in (r"ZENODO_API_TOKEN\s*=\s*(\S+)", r"ZENODO_TOKEN\s*=\s*(\S+)"):
        m = re.search(pat, txt)
        if m:
            return m.group(1).strip()
    return None

def api(tok: str, method: str, path: str, data=None):
    hdrs = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
    url = f"{BASE}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=35) as r:
            return r.status, json.loads(r.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8", errors="replace"))

def main():
    tok = token()
    if not tok:
        print("ZENODO_API_TOKEN fehlt — lege Dateien lokal ab (bereits im Workspace).")
        print("Optional: export ZENODO_API_TOKEN=... und Skript erneut starten.")
        return
    st, resp = api(tok, "GET", "/deposit/depositions?size=15")
    if st != 200:
        print("Deposits:", st, resp)
        return
    deps = resp if isinstance(resp, list) else []
    open_d = [d for d in deps if d.get("state") in ("unsubmitted", "draft")]
    dep_id = None
    for d in open_d:
        title = (d.get("title") or d.get("metadata", {}).get("title") or "")
        if "CCRN" in title or "kappa" in title.lower() or "κ" in title:
            dep_id = d["id"]
            break
    if not dep_id and open_d:
        dep_id = open_d[0]["id"]
    if not dep_id:
        st2, nd = api(tok, "POST", "/deposit/depositions", {})
        if st2 not in (200, 201):
            print("Neuer Deposit fehlgeschlagen:", st2, nd)
            return
        dep_id = nd["id"]
    st3, dep = api(tok, "GET", f"/deposit/depositions/{dep_id}")
    if st3 != 200:
        print("Deposit GET", st3, dep)
        return
    bucket = dep.get("links", {}).get("bucket")
    if not bucket:
        print("Kein bucket")
        return
    for fp in FILES:
        if not fp.exists():
            print("Ueberspringe (fehlt):", fp.name)
            continue
        data = fp.read_bytes()
        name = fp.name
        req = urllib.request.Request(
            f"{bucket}/{name}",
            data=data,
            headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/octet-stream"},
            method="PUT",
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                print(f"OK {name} HTTP {r.status}")
        except urllib.error.HTTPError as e:
            print(f"FAIL {name} {e.code}")

if __name__ == "__main__":
    main()
