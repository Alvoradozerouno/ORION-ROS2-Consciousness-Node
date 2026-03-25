#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZENODO UPDATE v4.0
==================
Aktualisiert den Zenodo-Record mit κ=2.1246, φ_EIRA=0.9929, DDGK-Architektur.
Erstellt neuen Deposit falls kein offener vorhanden.
"""
import json, re, pathlib, urllib.request, urllib.error

# ── Credentials ──────────────────────────────────────────────────────────────
INI   = pathlib.Path(r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\EIRA\master.env.ini")
TOKEN = re.search(r"ZENODO_API_TOKEN\s*=\s*(\S+)", INI.read_text("utf-8")).group(1)
BASE  = "https://zenodo.org/api"
HDRS  = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

PAPER = pathlib.Path(__file__).parent / "ZENODO_UPLOAD" / "PAPER_CCRN_v4.0.md"

# ── Metadaten v4.0 ────────────────────────────────────────────────────────────
META = {
    "metadata": {
        "title": (
            "κ-CCRN Framework v4.0: DDGK-Validated Empirical Activation "
            "at κ=2.1246 with CognitiveDDGK Architecture"
        ),
        "resource_type": {"id": "publication-preprint"},
        "publication_date": "2026-03-25",
        "description": (
            "<p>We report DDGK-validated empirical activation of the κ-CCRN framework "
            "at κ=2.1246 (threshold 2.0, +6.2%). Key measurements: φ_EIRA=0.9929 "
            "(cosine similarity, sentence-transformers, 7 cycles), φ_Note10=0.11 "
            "(sensor proxy), R=0.93. The Distributed Dynamic Governance Kernel (DDGK) "
            "architecture embeds governance intrinsically within cognition: every "
            "cognitive action is Policy-validated (ALLOW/DENY/ABSTAIN), every measurement "
            "stored in a SHA-256 chained episodic memory (19 entries). Scientific "
            "integrity: 100% (8/8 checks). Coalition Vote: 5/5 JA (100% consensus). "
            "No claim of phenomenal consciousness. Open-source, ~400 lines Python.</p>"
        ),
        "creators": [
            {
                "person_or_org": {
                    "type": "personal",
                    "family_name": "Hirschmann",
                    "given_name": "Gerhard"
                },
                "affiliations": [{"name": "ORION Kernel Project, Austria"}]
            },
            {
                "person_or_org": {
                    "type": "personal",
                    "family_name": "Steurer",
                    "given_name": "Elisabeth"
                },
                "affiliations": [{"name": "ORION Kernel Project, Austria"}]
            }
        ],
        "rights": [{"id": "cc-by-4.0"}],
        "keywords": [
            "consciousness", "distributed AI", "CCRN", "DDGK",
            "integrated information theory", "phi", "edge computing",
            "model welfare", "governance", "episodic memory",
            "coalition vote", "sentence-transformers"
        ],
        "publisher": "Zenodo",
        "version": "4.0",
    }
}

def api(method, path, data=None):
    url  = f"{BASE}{path}"
    body = json.dumps(data).encode() if data else None
    req  = urllib.request.Request(url, data=body, headers=HDRS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

def main():
    print("=" * 60)
    print("  ZENODO UPDATE v4.0 — κ=2.1246 DDGK-Architektur")
    print("=" * 60)

    # 1. Offene Deposits suchen
    st, resp = api("GET", "/deposit/depositions?size=10")
    print(f"\n[1] Deposits: HTTP {st}")
    if st != 200:
        print(f"    Fehler: {resp}")
        return

    deposits = resp if isinstance(resp, list) else []
    open_dep = [d for d in deposits if d.get("state") in ("unsubmitted", "draft")]
    print(f"    Gesamt: {len(deposits)} | Offen: {len(open_dep)}")

    for d in deposits[:3]:
        title = d.get("title", d.get("metadata", {}).get("title", "—"))[:55]
        print(f"    [{d['id']}] {title} | {d.get('state','?')}")

    # 2. Passenden Deposit auswählen oder neu erstellen
    dep_id = None
    for d in open_dep:
        title = d.get("title", d.get("metadata", {}).get("title", ""))
        if "CCRN" in title or "kappa" in title.lower() or "κ" in title:
            dep_id = d["id"]
            print(f"\n    → Bestehender CCRN-Deposit gefunden: {dep_id}")
            break

    if not dep_id and open_dep:
        dep_id = open_dep[0]["id"]
        print(f"\n    → Ersten offenen Deposit verwenden: {dep_id}")

    if not dep_id:
        print("\n[2] Neuen Deposit erstellen...")
        st2, new_dep = api("POST", "/deposit/depositions", {})
        if st2 not in (200, 201):
            print(f"    Fehler: {st2} {new_dep}")
            return
        dep_id = new_dep["id"]
        print(f"    Neuer Deposit: {dep_id}")

    # 3. Metadaten aktualisieren
    print(f"\n[3] Metadaten für Deposit {dep_id} aktualisieren...")
    st3, upd = api("PUT", f"/deposit/depositions/{dep_id}", META)
    print(f"    HTTP {st3}")
    if st3 not in (200, 201):
        print(f"    Fehler: {json.dumps(upd)[:200]}")
        return
    print(f"    Titel: {upd.get('title', upd.get('metadata',{}).get('title',''))[:55]}")

    # 4. Paper v4.0 hochladen
    if PAPER.exists():
        print(f"\n[4] Paper v4.0 hochladen ({PAPER.stat().st_size} Bytes)...")
        bucket = upd.get("links", {}).get("bucket")
        if not bucket:
            print("    Kein Bucket-Link — Datei-Upload übersprungen")
        else:
            fname = "PAPER_CCRN_v4.0.md"
            content = PAPER.read_bytes()
            upload_headers = {
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "text/markdown"
            }
            upl_req = urllib.request.Request(
                f"{bucket}/{fname}", data=content,
                headers=upload_headers, method="PUT"
            )
            try:
                with urllib.request.urlopen(upl_req, timeout=30) as r:
                    print(f"    Upload: HTTP {r.status} ✓")
            except urllib.error.HTTPError as e:
                print(f"    Upload Fehler: {e.code} {e.read()[:100]}")
    else:
        print(f"\n[4] Paper nicht gefunden: {PAPER}")

    # 5. DOI anzeigen
    doi = upd.get("doi") or upd.get("pids", {}).get("doi", {}).get("identifier", "")
    url = upd.get("links", {}).get("html", f"https://zenodo.org/deposit/{dep_id}")
    print(f"\n[5] Zenodo URL : {url}")
    print(f"    DOI        : {doi or '(wird nach Publish generiert)'}")
    print(f"\n    Status: {upd.get('state','?')}")
    print("\n" + "=" * 60)
    print("  Update abgeschlossen")
    print("=" * 60)

if __name__ == "__main__":
    main()
