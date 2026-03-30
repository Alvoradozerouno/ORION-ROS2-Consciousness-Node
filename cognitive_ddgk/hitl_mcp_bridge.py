#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HITL MCP Bridge — Human-in-the-Loop für MCP-/Agent-Aktionen (ORION/DDGK).

Warteschlange: hitl_pending.jsonl  |  Geheimnis: .hitl_secret (nicht committen)

Typischer Ablauf:
  1) Agent/Cursor:  python cognitive_ddgk/hitl_mcp_bridge.py request --tool SLACK_POST --summary "Nachricht X"
  2) Mensch:        python cognitive_ddgk/hitl_mcp_bridge.py list
  3) Mensch:        python cognitive_ddgk/hitl_mcp_bridge.py approve <request_id>
  4) Ausgabe:       approval_token — diesen Wert bei der echten MCP-Aktion mitschicken oder im Log verankern.

Freigabe erfolgt nur mit lokalem Secret; keine Tokens in Git.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import secrets
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

WS = Path(__file__).resolve().parent
PENDING_FILE = WS / "hitl_pending.jsonl"
SECRET_FILE = WS / ".hitl_secret"
MEM_LOG = WS / "cognitive_memory.jsonl"


def _utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_or_create_secret() -> str:
    if SECRET_FILE.exists():
        return SECRET_FILE.read_text(encoding="utf-8").strip()
    SECRET_FILE.write_text(secrets.token_hex(32), encoding="utf-8")
    return SECRET_FILE.read_text(encoding="utf-8").strip()


def _token_for(req_id: str, tool: str, summary: str) -> str:
    secret = load_or_create_secret()
    payload = f"{req_id}|{tool}|{summary}"
    return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def _read_all() -> List[Dict[str, Any]]:
    if not PENDING_FILE.exists():
        return []
    out: List[Dict[str, Any]] = []
    for line in PENDING_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _latest_by_id() -> Dict[str, Dict[str, Any]]:
    """Letzter Eintrag pro id gewinnt (JSONL-append-semantik)."""
    latest: Dict[str, Dict[str, Any]] = {}
    for row in _read_all():
        rid = row.get("id")
        if isinstance(rid, str) and rid:
            latest[rid] = row
    return latest


def _append(entry: Dict[str, Any]) -> None:
    PENDING_FILE.parent.mkdir(parents=True, exist_ok=True)
    with PENDING_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _optional_memory_note(agent: str, action: str, data: Dict[str, Any]) -> None:
    if not MEM_LOG.exists():
        return
    try:
        prev = ""
        lines = [l for l in MEM_LOG.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
        if lines:
            prev = json.loads(lines[-1]).get("hash", "")
        raw = json.dumps(
            {"ts": _utc(), "agent": agent, "action": action, "data": data, "prev": prev},
            ensure_ascii=False,
            sort_keys=True,
        )
        h = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        entry = json.loads(raw)
        entry["hash"] = h
        with MEM_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def cmd_request(args: argparse.Namespace) -> int:
    rid = str(uuid.uuid4())
    entry: Dict[str, Any] = {
        "id": rid,
        "ts": _utc(),
        "tool": args.tool,
        "summary": args.summary,
        "risk": args.risk or "MEDIUM",
        "source": args.source or "AGENT",
        "status": "pending",
        "approval_token": None,
    }
    _append(entry)
    print(f"[HITL] Angelegt request_id={rid}")
    print(f"       Naechster Schritt: python cognitive_ddgk/hitl_mcp_bridge.py approve {rid}")
    return 0


def cmd_list(_: argparse.Namespace) -> int:
    latest = _latest_by_id()
    pending = [r for r in latest.values() if r.get("status") == "pending"]
    if not pending:
        print("[HITL] Keine pending Eintraege.")
        return 0
    print(f"[HITL] Pending ({len(pending)}):")
    for r in pending[-20:]:
        print(f"  {r.get('id')} | {r.get('tool')} | {r.get('risk')} | {r.get('summary', '')[:80]}")
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    rid = args.request_id.strip()
    target = _latest_by_id().get(rid)
    if not target or target.get("status") != "pending":
        print(f"[HITL] FEHLER: pending Request {rid} nicht gefunden.", file=sys.stderr)
        return 1
    token = _token_for(rid, str(target.get("tool", "")), str(target.get("summary", "")))
    target["status"] = "approved"
    target["approved_ts"] = _utc()
    target["approval_token"] = token
    target["approved_by"] = args.by or "human"
    _append(target)
    print(f"[HITL] Freigegeben request_id={rid}")
    print(f"       approval_token={token}")
    print("       Diesen Token bei der MCP-/Tool-Aktion dokumentieren oder als Payload-Feld mitsenden.")
    _optional_memory_note("HITL", "approve", {"request_id": rid, "tool": target.get("tool")})
    return 0


def cmd_reject(args: argparse.Namespace) -> int:
    rid = args.request_id.strip()
    entry: Dict[str, Any] = {
        "id": rid,
        "ts": _utc(),
        "status": "rejected",
        "rejected_ts": _utc(),
        "reason": args.reason or "no reason",
    }
    _append(entry)
    print(f"[HITL] Abgelehnt request_id={rid}")
    _optional_memory_note("HITL", "reject", {"request_id": rid})
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="HITL MCP Bridge (ORION/DDGK)")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("request", help="Neue Freigabe anfordern")
    pr.add_argument("--tool", required=True, help="z.B. MCP-Tool-Name oder Kernel-Call")
    pr.add_argument("--summary", required=True, help="Kurzbeschreibung der geplanten Aktion")
    pr.add_argument("--risk", default="MEDIUM", help="LOW|MEDIUM|HIGH")
    pr.add_argument("--source", default="AGENT", help="Quelle")
    pr.set_defaults(func=cmd_request)

    pl = sub.add_parser("list", help="Pending anzeigen")
    pl.set_defaults(func=cmd_list)

    pa = sub.add_parser("approve", help="Freigabe erteilen")
    pa.add_argument("request_id", help="UUID aus request")
    pa.add_argument("--by", default="", help="Name Kennung Mensch")
    pa.set_defaults(func=cmd_approve)

    prj = sub.add_parser("reject", help="Ablehnen")
    prj.add_argument("request_id")
    prj.add_argument("--reason", default="")
    prj.set_defaults(func=cmd_reject)

    args = p.parse_args()
    load_or_create_secret()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
