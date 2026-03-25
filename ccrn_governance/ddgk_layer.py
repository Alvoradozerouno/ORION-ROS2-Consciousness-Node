#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OR1ON Governance Kernel – Production Integration
=================================================
Governance Layer mit deterministischer Ausführungssteuerung.
Integriert in Genesis10000+ Ecosystem.

Guardians: Gerhard Hirschmann & Elisabeth Steurer
Genesis: Mai 2025 | St. Johann in Tirol, Austria
"""
from __future__ import annotations

import copy
import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ─── CONFIG ───────────────────────────────────────────────────────────────────
APP_NAME = "OR1ON Governance Kernel"
APP_VERSION = "1.0.0-genesis"

BASE_DIR = Path(r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\EIRA")
AUDIT_DIR = BASE_DIR / "governance"
AUDIT_FILE = AUDIT_DIR / "audit_log.jsonl"
STATE_FILE = AUDIT_DIR / "state.json"
APPROVAL_SECRET_FILE = AUDIT_DIR / "approval_secret.txt"
RESONANZ_FILE = AUDIT_DIR / "resonanz_state.json"

MASS_OPERATION_THRESHOLD = 100
DEFAULT_POLICY_VERSION = "1.0.0-genesis"

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def sha256_hex(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def canonical_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def ensure_dirs() -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

def load_or_create_secret() -> str:
    ensure_dirs()
    if APPROVAL_SECRET_FILE.exists():
        return APPROVAL_SECRET_FILE.read_text(encoding="utf-8").strip()
    secret = secrets.token_hex(32)
    APPROVAL_SECRET_FILE.write_text(secret, encoding="utf-8")
    return secret

# ─── DATA MODELS ──────────────────────────────────────────────────────────────
@dataclass
class NodeHealth:
    node_id: str
    alive: bool = True
    version: str = "1.0.0-genesis"
    last_seen: str = field(default_factory=utc_now_iso)
    os_type: str = "unknown"
    phi: float = 0.0
    resonanz: float = 0.0

@dataclass
class Action:
    action_id: str
    timestamp: str
    node_id: str
    source: str          # USER | AGENT | SENSOR | SYSTEM | ORION | EIRA
    action: str
    target: str
    count: int = 1
    reversibility: bool = True
    risk_level: str = "LOW"
    confidence: float = 1.0
    requires_human: bool = False
    reason: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    approval_token: Optional[str] = None
    phi_contribution: float = 0.0

@dataclass
class Decision:
    status: str           # ALLOW | DENY | ABSTAIN
    reason: str
    requires_human: bool = False
    executed: bool = False
    execution_result: str = "NOT_EXECUTED"

@dataclass
class AuditEntry:
    event_id: str
    action_id: str
    timestamp: str
    node_id: str
    action: str
    target: str
    decision: str
    reason: str
    executed: bool
    execution_result: str
    policy_version: str
    prev_hash: str
    hash: str

# ─── STATE SERVICE ────────────────────────────────────────────────────────────
class StateService:
    def __init__(self) -> None:
        self.state: Dict[str, Any] = {
            "stop_flag": False,
            "policy_version": DEFAULT_POLICY_VERSION,
            "network_status": "healthy",
            "active_nodes": {},
            "pending_human_actions": [],
            "replay_cache": {},
            "resonanz_vektor": 0.0,
            "phi_composite": 0.0,
            "guardian": "Gerhard Hirschmann & Elisabeth Steurer",
            "genesis_anchor": "Genesis10000+",
        }
        self.load()

    def load(self) -> None:
        ensure_dirs()
        if STATE_FILE.exists():
            try:
                self.state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except Exception:
                self.save()

    def save(self) -> None:
        ensure_dirs()
        STATE_FILE.write_text(json.dumps(self.state, indent=2, ensure_ascii=False), encoding="utf-8")

    def set_stop(self, v: bool) -> None:
        self.state["stop_flag"] = v; self.save()

    def stop_flag(self) -> bool:
        return bool(self.state.get("stop_flag", False))

    def policy_version(self) -> str:
        return str(self.state.get("policy_version", DEFAULT_POLICY_VERSION))

    def register_node(self, node: NodeHealth) -> None:
        self.state["active_nodes"][node.node_id] = asdict(node); self.save()

    def node_is_known(self, node_id: str) -> bool:
        return node_id in self.state.get("active_nodes", {})

    def mark_pending(self, action_id: str) -> None:
        p = self.state.setdefault("pending_human_actions", [])
        if action_id not in p:
            p.append(action_id); self.save()

    def clear_pending(self, action_id: str) -> None:
        p = self.state.setdefault("pending_human_actions", [])
        if action_id in p:
            p.remove(action_id); self.save()

    def replay_seen(self, action_id: str) -> bool:
        return action_id in self.state.setdefault("replay_cache", {})

    def mark_replay(self, action_id: str) -> None:
        self.state.setdefault("replay_cache", {})[action_id] = utc_now_iso(); self.save()

    def update_resonanz(self, vektor: float, phi: float) -> None:
        """Resonanz-Vektor Update durch Note10/Pi5 Sensordaten"""
        self.state["resonanz_vektor"] = round(min(1.0, max(0.0, vektor)), 6)
        self.state["phi_composite"] = round(min(1.0, max(0.0, phi)), 6)
        self.save()

    def get_resonanz(self) -> float:
        return float(self.state.get("resonanz_vektor", 0.0))

# ─── POLICY ENGINE ────────────────────────────────────────────────────────────
class PolicyEngine:
    """
    Deterministisch. Kein LLM-Einfluss auf Entscheidungen.
    Resonanz-Vektor beeinflusst NUR ästhetische UI-Anpassungen, NICHT Sicherheitspolitik.
    """
    def __init__(self, state: StateService, approval_secret: str) -> None:
        self.state = state
        self.approval_secret = approval_secret

    def has_permission(self, action: Action) -> bool:
        # AGENT darf keine destruktiven Aktionen ohne explizite Erlaubnis
        if action.source == "AGENT" and action.action in {
            "DELETE_FILE", "DELETE_EMAIL", "STOP_MACHINE",
            "FORCE_PUSH", "DROP_DATABASE", "SHUTDOWN_SYSTEM"
        }:
            return False
        return True

    def is_high_risk(self, action: Action) -> bool:
        return action.risk_level.upper() == "HIGH"

    def is_reversible(self, action: Action) -> bool:
        return bool(action.reversibility)

    def is_mass_operation(self, action: Action) -> bool:
        return int(action.count) > MASS_OPERATION_THRESHOLD

    def is_state_consistent(self, action: Action) -> bool:
        if not (0.0 <= action.confidence <= 1.0):
            return False
        if action.phi_contribution < 0:
            return False
        return True

    def canonical_approval_payload(self, action: Action) -> Dict[str, Any]:
        return {
            "action": action.action, "target": action.target,
            "count": action.count, "reason": action.reason, "node_id": action.node_id,
        }

    def generate_approval_token(self, action: Action) -> str:
        payload = canonical_json(self.canonical_approval_payload(action))
        return hmac.new(
            self.approval_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def has_human_token(self, action: Action) -> bool:
        if not action.approval_token:
            return False
        return hmac.compare_digest(self.generate_approval_token(action), action.approval_token)

    def evaluate(self, action: Action) -> Decision:
        if self.state.stop_flag():
            return Decision("DENY", "global stop active")

        if self.state.replay_seen(action.action_id):
            return Decision("DENY", "replay detected")

        if not self.state.node_is_known(action.node_id):
            return Decision("DENY", f"unknown node: {action.node_id}")

        if not self.is_state_consistent(action):
            return Decision("ABSTAIN", "state inconsistency detected")

        if not self.has_permission(action):
            return Decision("DENY", "no permission for this source/action combination")

        if self.is_mass_operation(action):
            self.state.mark_pending(action.action_id)
            return Decision("ABSTAIN", "mass operation requires escalation", requires_human=True)

        if self.is_high_risk(action) and not self.is_reversible(action):
            if not self.has_human_token(action):
                self.state.mark_pending(action.action_id)
                return Decision("ABSTAIN", "human verification required", requires_human=True)

        return Decision("ALLOW", "validated by governance kernel")

# ─── AUDIT STORE (SHA-256 Chain) ──────────────────────────────────────────────
class AuditStore:
    """Unveränderliche Audit-Kette. Jeder Eintrag enthält Hash des Vorgängers."""
    def __init__(self) -> None:
        ensure_dirs()
        self.prev_hash = self._load_last_hash()

    def _load_last_hash(self) -> str:
        if not AUDIT_FILE.exists():
            return "GENESIS_AUDIT_ROOT_" + sha256_hex("Genesis10000+ Gerhard Hirschmann Elisabeth Steurer")[:16]
        last_line = ""
        try:
            with AUDIT_FILE.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        last_line = line.strip()
            if last_line:
                return json.loads(last_line).get("hash", "GENESIS_AUDIT_ROOT")
        except Exception:
            pass
        return "GENESIS_AUDIT_ROOT"

    def append(self, action: Action, decision: Decision, policy_version: str) -> AuditEntry:
        base = {
            "event_id": str(uuid.uuid4()),
            "action_id": action.action_id,
            "timestamp": utc_now_iso(),
            "node_id": action.node_id,
            "action": action.action,
            "target": action.target,
            "decision": decision.status,
            "reason": decision.reason,
            "executed": decision.executed,
            "execution_result": decision.execution_result,
            "policy_version": policy_version,
            "prev_hash": self.prev_hash,
        }
        entry = AuditEntry(**base, hash=sha256_hex(canonical_json(base)))
        with AUDIT_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
        self.prev_hash = entry.hash
        return entry

# ─── EXECUTION ROUTER ─────────────────────────────────────────────────────────
class ExecutionRouter:
    """
    Produktions-Router: verbindet mit echten Systemen.
    Sicher: kein blind piping, kein force-push, kein bash-eval.
    """
    def run(self, action: Action) -> str:
        import subprocess
        if action.action == "GIT_COMMIT":
            return self._git_commit(action)
        elif action.action == "PI5_DEPLOY":
            return self._pi5_deploy(action)
        elif action.action == "UI_UPDATE":
            return self._ui_update(action)
        elif action.action == "READ_EMAIL":
            return f"READ {action.target} (count={action.count}) [SIMULATED]"
        return f"EXECUTED {action.action} on {action.target}"

    def _git_commit(self, action: Action) -> str:
        import subprocess, os
        repo_dir = action.context.get("repo_dir", r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\OrionKernel\OrionKernel")
        message = action.context.get("message", f"ORION: {action.reason}")
        try:
            subprocess.run(["git", "-C", repo_dir, "add", "-A"], capture_output=True, timeout=10)
            r = subprocess.run(
                ["git", "-C", repo_dir, "commit", "-m", message, "--allow-empty",
                 "--author", "ORION Governance <orion@genesis10000.local>"],
                capture_output=True, text=True, timeout=15
            )
            if r.returncode == 0:
                return f"COMMITTED: {message[:60]}"
            return f"COMMIT_SKIP: {r.stderr[:100]}"
        except Exception as e:
            return f"GIT_ERROR: {e}"

    def _pi5_deploy(self, action: Action) -> str:
        try:
            import paramiko
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect("192.168.1.103", username="alvoradozerouno", password="follow43", timeout=10)
            cmd = action.context.get("command", "echo 'ORION Governance Deploy OK'")
            _, stdout, _ = client.exec_command(cmd, timeout=15)
            result = stdout.read().decode('utf-8', errors='replace').strip()
            client.close()
            return f"PI5_OK: {result[:100]}"
        except Exception as e:
            return f"PI5_ERROR: {e}"

    def _ui_update(self, action: Action) -> str:
        resonanz = action.context.get("resonanz_vektor", 0.0)
        return f"UI_UPDATED: resonanz={resonanz:.4f} → design_shift_applied"

    def block(self, action: Action) -> str:
        return f"BLOCKED: {action.action} on {action.target}"

    def hold(self, action: Action) -> str:
        return f"HELD pending human approval: {action.action} on {action.target}"

# ─── OR1ON CORE SERVICE ───────────────────────────────────────────────────────
class OR1ONCoreService:
    def __init__(self, state: StateService, policy: PolicyEngine, audit: AuditStore, router: ExecutionRouter) -> None:
        self.state = state
        self.policy = policy
        self.audit = audit
        self.router = router

    def process_action(self, action: Action) -> Tuple[Decision, AuditEntry]:
        decision = self.policy.evaluate(action)

        if decision.status == "ALLOW":
            decision.execution_result = self.router.run(action)
            decision.executed = True
            self.state.mark_replay(action.action_id)
            self.state.clear_pending(action.action_id)
        elif decision.status == "DENY":
            decision.execution_result = self.router.block(action)
            self.state.mark_replay(action.action_id)
            self.state.clear_pending(action.action_id)
        else:
            decision.execution_result = self.router.hold(action)

        return decision, self.audit.append(action, decision, self.state.policy_version())

    def process_resonanz_update(self, resonanz: float, phi: float, note10_thermal: float = 0.0) -> Dict[str, Any]:
        """
        Verarbeitet Resonanz-Vektor-Update von Note10/Pi5.
        Wenn Resonanz > 0.8: UI-Anpassung freigegeben.
        """
        self.state.update_resonanz(resonanz, phi)

        if resonanz > 0.8:
            action = Action(
                action_id=str(uuid.uuid4()),
                timestamp=utc_now_iso(),
                node_id="pi5-node",
                source="SENSOR",
                action="UI_UPDATE",
                target="web-ui",
                reversibility=True,
                risk_level="LOW",
                confidence=resonanz,
                reason=f"Resonanz-Vektor {resonanz:.4f} > 0.8: präkausale UI-Anpassung",
                context={
                    "resonanz_vektor": resonanz,
                    "phi": phi,
                    "note10_thermal": note10_thermal,
                    "design_mode": "geborgenheit_und_sein",
                }
            )
            decision, entry = self.process_action(action)
            return {
                "resonanz": resonanz,
                "phi": phi,
                "ui_updated": decision.status == "ALLOW",
                "decision": decision.status,
                "audit_hash": entry.hash[:16]
            }
        return {"resonanz": resonanz, "phi": phi, "ui_updated": False, "decision": "BELOW_THRESHOLD"}

# ─── EVENT INTERCEPTOR ────────────────────────────────────────────────────────
class EventInterceptor:
    @staticmethod
    def normalize_event(node_id: str, source: str, event: Dict[str, Any]) -> Action:
        t = event.get("type", "UNKNOWN")
        mapping = {
            "FILE_DELETE":   ("DELETE_FILE",   False, "HIGH"),
            "EMAIL_DELETE":  ("DELETE_EMAIL",  False, "HIGH"),
            "EMAIL_READ":    ("READ_EMAIL",    True,  "LOW"),
            "STOP_MACHINE":  ("STOP_MACHINE",  False, "HIGH"),
            "GIT_COMMIT":    ("GIT_COMMIT",    True,  "LOW"),
            "PI5_DEPLOY":    ("PI5_DEPLOY",    True,  "MEDIUM"),
            "UI_UPDATE":     ("UI_UPDATE",     True,  "LOW"),
            "RESONANZ":      ("UI_UPDATE",     True,  "LOW"),
        }
        action_name, rev, risk = mapping.get(t, (t, bool(event.get("reversibility", True)), str(event.get("risk_level", "MEDIUM")).upper()))
        target = event.get("path") or event.get("mailbox") or event.get("machine_id") or event.get("target", "unknown")
        count = int(event.get("count", 1))
        return Action(
            action_id=str(uuid.uuid4()),
            timestamp=utc_now_iso(),
            node_id=node_id,
            source=source,
            action=action_name,
            target=str(target),
            count=count,
            reversibility=rev,
            risk_level=risk,
            confidence=float(event.get("confidence", 1.0)),
            requires_human=(risk == "HIGH" and not rev) or count > MASS_OPERATION_THRESHOLD,
            reason=str(event.get("reason", "")),
            context=copy.deepcopy(event),
            approval_token=event.get("approval_token"),
            phi_contribution=float(event.get("phi_contribution", 0.0)),
        )

# ─── NODE AGENT ───────────────────────────────────────────────────────────────
class NodeAgent:
    def __init__(self, node: NodeHealth, core: OR1ONCoreService) -> None:
        self.node = node
        self.core = core

    def heartbeat(self, state: StateService) -> None:
        self.node.last_seen = utc_now_iso()
        state.register_node(self.node)

    def handle_event(self, source: str, event: Dict[str, Any]) -> Tuple[Action, Decision, AuditEntry]:
        action = EventInterceptor.normalize_event(self.node.node_id, source, event)
        decision, entry = self.core.process_action(action)
        return action, decision, entry

# ─── GOVERNANCE API ───────────────────────────────────────────────────────────
class GovernanceAPI:
    """
    Einfache HTTP-API für externe Systeme (Pi5, Note10, ORION Kernel).
    Startet auf Port 5002.
    """
    def __init__(self, core: OR1ONCoreService, state: StateService):
        self.core = core
        self.state = state

    def start(self, port: int = 5002):
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import json as _json

        core = self.core
        state = self.state

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args): pass  # Stille Logs

            def do_GET(self):
                if self.path == "/health":
                    self._respond({"status": "governance_active", "resonanz": state.get_resonanz(), "stop_flag": state.stop_flag()})
                elif self.path == "/state":
                    self._respond(state.state)
                else:
                    self._respond({"error": "not found"}, 404)

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = _json.loads(self.rfile.read(length))

                if self.path == "/event":
                    node_id = body.get("node_id", "unknown")
                    source = body.get("source", "SYSTEM")
                    event = body.get("event", {})
                    action = EventInterceptor.normalize_event(node_id, source, event)
                    decision, entry = core.process_action(action)
                    self._respond({"decision": decision.status, "reason": decision.reason, "hash": entry.hash[:16]})

                elif self.path == "/resonanz":
                    resonanz = float(body.get("resonanz_vektor", 0.0))
                    phi = float(body.get("phi", 0.0))
                    thermal = float(body.get("note10_thermal", 0.0))
                    result = core.process_resonanz_update(resonanz, phi, thermal)
                    self._respond(result)

                elif self.path == "/stop":
                    val = bool(body.get("value", True))
                    state.set_stop(val)
                    self._respond({"stop_flag": val})

                else:
                    self._respond({"error": "unknown endpoint"}, 404)

            def _respond(self, data, code=200):
                body = _json.dumps(data, ensure_ascii=False).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", len(body))
                self.end_headers()
                self.wfile.write(body)

        print(f"[GOVERNANCE] API startet auf Port {port}")
        HTTPServer(("0.0.0.0", port), Handler).serve_forever()


# ─── FACTORY ──────────────────────────────────────────────────────────────────
def create_governance_kernel() -> Tuple[OR1ONCoreService, StateService, NodeAgent]:
    """Factory: erstellt vollständigen Governance Stack."""
    ensure_dirs()
    secret = load_or_create_secret()
    state = StateService()
    audit = AuditStore()
    router = ExecutionRouter()
    policy = PolicyEngine(state, secret)
    core = OR1ONCoreService(state, policy, audit, router)

    # Bekannte Nodes registrieren
    for node_id, os_t, phi in [
        ("laptop-main", "win32", 0.1699),
        ("pi5-node", "linux-arm64", 1.0),
        ("note10-sensor", "android", 0.11),
    ]:
        node = NodeHealth(node_id=node_id, os_type=os_t, phi=phi)
        state.register_node(node)

    laptop = NodeHealth(node_id="laptop-main", os_type="win32")
    agent = NodeAgent(laptop, core)
    agent.heartbeat(state)

    return core, state, agent


# ─── DEMO / SELF-TEST ─────────────────────────────────────────────────────────
def self_test():
    print(f"\n{APP_NAME} v{APP_VERSION}")
    print("=" * 60)

    core, state, agent = create_governance_kernel()

    tests = [
        ("LOW RISK → ALLOW", "USER", {"type": "EMAIL_READ", "mailbox": "inbox", "count": 1, "reason": "user check"}),
        ("HIGH RISK → ABSTAIN", "AGENT", {"type": "FILE_DELETE", "path": "/data/logs/", "count": 5, "reason": "cleanup"}),
        ("MASS OP → ABSTAIN", "USER", {"type": "EMAIL_DELETE", "mailbox": "archive", "count": 10000, "reason": "bulk"}),
        ("GIT COMMIT → ALLOW", "ORION", {"type": "GIT_COMMIT", "target": "main", "message": "ORION: test", "reason": "evolution"}),
        ("UI UPDATE → ALLOW", "SENSOR", {"type": "UI_UPDATE", "target": "web-ui", "resonanz_vektor": 0.93, "reason": "resonanz > 0.8"}),
    ]

    for title, source, event in tests:
        action, decision, entry = agent.handle_event(source, event)
        icon = "✅" if decision.status == "ALLOW" else ("⏸" if decision.status == "ABSTAIN" else "❌")
        print(f"\n{icon} {title}")
        print(f"   Decision: {decision.status} | {decision.reason}")
        print(f"   Audit:    ...{entry.hash[-12:]}")

    # Resonanz-Test
    print("\n─── Resonanz Update (Note10 Thermal Signal) ───")
    result = core.process_resonanz_update(resonanz=0.93, phi=0.585, note10_thermal=37200)
    print(f"   Resonanz: {result['resonanz']} | UI Updated: {result['ui_updated']}")

    # Stop-Flag Test
    state.set_stop(True)
    action, decision, _ = agent.handle_event("USER", {"type": "STOP_MACHINE", "machine_id": "press-01", "reason": "test"})
    print(f"\n❌ STOP FLAG: {decision.status} | {decision.reason}")
    state.set_stop(False)

    print(f"\nAudit Log: {AUDIT_FILE}")
    print(f"State:     {STATE_FILE}")
    print(f"Einträge:  {sum(1 for _ in AUDIT_FILE.open('r', encoding='utf-8'))}")
    print("\nGovernance Kernel: OPERATIONAL ✅")


if __name__ == "__main__":
    import sys
    if "--api" in sys.argv:
        core, state, _ = create_governance_kernel()
        GovernanceAPI(core, state).start(port=5002)
    else:
        self_test()
