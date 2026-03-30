#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  DECISION TRACE — DDGK Explainable AI Core                         ║
║  Jede Entscheidung wird vollständig begründet + SHA-verkettet       ║
║                                                                      ║
║  Format (pro Entscheidung):                                          ║
║    decision_id          → SHA-256(decision_content)                 ║
║    input_state_hash     → SHA-256(aktueller Systemzustand)          ║
║    goal_representation  → aktuelles Ziel als Text                   ║
║    reasoning_trace      → LLM-Begründungskette (Chain-of-Thought)   ║
║    selected_action      → gewähltes Tool/Aktion                     ║
║    alternatives_considered → evaluierte Alternativen                ║
║    validation_result    → DDGK-Policy-Check: passed/denied          ║
║    timestamp            → UTC ISO-8601                              ║
║                                                                      ║
║  Zweck:                                                              ║
║    • Volle Nachvollziehbarkeit jeder Entscheidung                   ║
║    • Unveränderliche Kette (SHA-256 prev_hash)                      ║
║    • XAI: Warum wurde Aktion X und nicht Y gewählt?                 ║
║    • GUARDIAN-kompatibel: HIGH-RISK Decisions separat markiert       ║
║    • EU AI Act Art. 13/14 konform (Transparenz + menschl. Aufsicht) ║
╚══════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import json
import hashlib
import datetime
import pathlib
from typing import Any, Dict, List, Optional

BASE_DIR = pathlib.Path(__file__).parent.parent
TRACE_FILE = BASE_DIR / "cognitive_ddgk" / "decision_trace.jsonl"
TRACE_FILE.parent.mkdir(exist_ok=True)


# ─── KERNKLASSE ──────────────────────────────────────────────────────────────

class DecisionTrace:
    """
    Erstellt und verwaltet vollständig begründete, SHA-verkettete Entscheidungen.

    Verwendung:
        dt = DecisionTrace(agent_id="ORION")

        record = dt.record(
            goal="Workspace analysieren",
            reasoning="Ich sehe 52 .py-Dateien. check_status liefert den schnellsten Überblick.",
            selected_action="tool_check_status",
            alternatives=["tool_scan_all", "tool_list_dir"],
            input_state={"kappa": 3.3493, "cycle": 5},
            validation_result="passed",
            risk_level="LOW"
        )
        print(record["decision_id"])   # SHA-256 ID
    """

    VERSION = "1.0.0-ddgk-xai"

    def __init__(self, agent_id: str = "DDGK", auto_persist: bool = True) -> None:
        self.agent_id      = agent_id
        self.auto_persist  = auto_persist
        self._decisions:   List[Dict] = []
        self._last_hash    = self._load_last_hash()

    # ── Private Hilfsmethoden ────────────────────────────────────────────────

    def _load_last_hash(self) -> str:
        """Letzte SHA-256 aus persistierter Kette laden."""
        if not TRACE_FILE.exists():
            return "0" * 64
        lines = [l for l in TRACE_FILE.read_text("utf-8", errors="replace").splitlines() if l.strip()]
        if not lines:
            return "0" * 64
        try:
            return json.loads(lines[-1]).get("decision_id", "0" * 64)
        except:
            return "0" * 64

    def _hash_state(self, state: Dict) -> str:
        """SHA-256 des Input-Zustands."""
        raw = json.dumps(state, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode()).hexdigest()

    def _make_decision_id(self, content: Dict) -> str:
        """SHA-256 des gesamten Entscheidungs-Inhalts (ohne decision_id selbst)."""
        raw = json.dumps(content, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode()).hexdigest()

    def _persist(self, record: Dict) -> None:
        """Schreibt Entscheidung in JSONL-Datei."""
        with TRACE_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # ── Hauptmethode: Entscheidung aufzeichnen ────────────────────────────────

    def record(
        self,
        goal:              str,
        reasoning:         str,
        selected_action:   str,
        alternatives:      List[str] = None,
        input_state:       Dict = None,
        validation_result: str = "passed",
        risk_level:        str = "LOW",
        hitl_required:     bool = False,
        metadata:          Dict = None,
    ) -> Dict:
        """
        Zeichnet eine vollständig begründete Entscheidung auf.

        Args:
            goal:               Aktuelles Ziel des Agenten
            reasoning:          Begründungskette (Chain-of-Thought)
            selected_action:    Gewähltes Tool/Aktion
            alternatives:       Evaluierte Alternativen (nicht gewählt)
            input_state:        Aktueller Systemzustand (wird gehasht)
            validation_result:  "passed" | "denied" | "hitl_required" | "warning"
            risk_level:         "LOW" | "MEDIUM" | "HIGH"
            hitl_required:      True wenn menschliche Freigabe nötig war
            metadata:           Zusätzliche Daten (frei)

        Returns:
            Vollständiger Decision-Record mit decision_id (SHA-256)
        """
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        state = input_state or {}
        state_hash = self._hash_state(state)

        # Kerninhalt für SHA-256
        core = {
            "agent":              self.agent_id,
            "ts":                 ts,
            "goal":               goal,
            "reasoning_trace":    reasoning,
            "selected_action":    selected_action,
            "alternatives_considered": alternatives or [],
            "input_state_hash":   state_hash,
            "validation_result":  validation_result,
            "risk_level":         risk_level,
            "hitl_required":      hitl_required,
            "prev_decision_id":   self._last_hash,
            "version":            self.VERSION,
        }

        decision_id = self._make_decision_id(core)

        record = {
            "decision_id":            decision_id,
            "input_state_hash":       state_hash,
            "goal_representation":    goal,
            "reasoning_trace":        reasoning,
            "selected_action":        selected_action,
            "alternatives_considered":alternatives or [],
            "validation_result":      validation_result,
            "risk_level":             risk_level,
            "hitl_required":          hitl_required,
            "agent_id":               self.agent_id,
            "prev_decision_id":       self._last_hash,
            "timestamp":              ts,
            "input_state":            state,
            "metadata":               metadata or {},
            "version":                self.VERSION,
        }

        self._decisions.append(record)
        self._last_hash = decision_id

        if self.auto_persist:
            self._persist(record)

        return record

    # ── Abfragen ──────────────────────────────────────────────────────────────

    def get_all(self) -> List[Dict]:
        """Alle Entscheidungen aus der Datei laden."""
        if not TRACE_FILE.exists():
            return []
        records = []
        for line in TRACE_FILE.read_text("utf-8", errors="replace").splitlines():
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except:
                    pass
        return records

    def get_by_action(self, action: str) -> List[Dict]:
        """Alle Entscheidungen für eine bestimmte Aktion."""
        return [r for r in self.get_all() if r.get("selected_action") == action]

    def get_high_risk(self) -> List[Dict]:
        """Nur HIGH-RISK Entscheidungen."""
        return [r for r in self.get_all() if r.get("risk_level") == "HIGH"]

    def get_denied(self) -> List[Dict]:
        """Abgelehnte Aktionen (DDGK Policy denied)."""
        return [r for r in self.get_all() if r.get("validation_result") == "denied"]

    def verify_chain(self) -> Dict:
        """
        Prüft die Integrität der SHA-256 Kette.
        Jedes prev_decision_id muss mit dem vorherigen decision_id übereinstimmen.
        """
        records = self.get_all()
        if not records:
            return {"valid": True, "length": 0, "broken_at": None}

        broken_at = None
        for i in range(1, len(records)):
            expected_prev = records[i - 1]["decision_id"]
            actual_prev   = records[i].get("prev_decision_id", "")
            if expected_prev != actual_prev:
                broken_at = i
                break

        return {
            "valid":      broken_at is None,
            "length":     len(records),
            "broken_at":  broken_at,
            "first_id":   records[0]["decision_id"][:16] + "..." if records else None,
            "last_id":    records[-1]["decision_id"][:16] + "..." if records else None,
        }

    def stats(self) -> Dict:
        """Statistiken über alle Entscheidungen."""
        records = self.get_all()
        if not records:
            return {"total": 0}

        from collections import Counter
        actions    = Counter(r.get("selected_action", "?") for r in records)
        risk_dist  = Counter(r.get("risk_level", "?") for r in records)
        val_dist   = Counter(r.get("validation_result", "?") for r in records)
        agents     = Counter(r.get("agent_id", "?") for r in records)

        return {
            "total":           len(records),
            "top_actions":     dict(actions.most_common(5)),
            "risk_distribution": dict(risk_dist),
            "validation_dist": dict(val_dist),
            "agents":          dict(agents),
            "chain_valid":     self.verify_chain()["valid"],
            "file":            str(TRACE_FILE),
        }

    def export_human_readable(self, last_n: int = 10) -> str:
        """Lesbare Darstellung der letzten N Entscheidungen."""
        records = self.get_all()[-last_n:]
        lines = [f"{'='*60}", f"DECISION TRACE — letzten {len(records)} Entscheidungen", f"{'='*60}"]
        for r in records:
            ts_short = r.get("timestamp", "?")[:19]
            lines += [
                f"",
                f"  ID:        {r.get('decision_id','?')[:24]}...",
                f"  Zeit:      {ts_short} UTC",
                f"  Agent:     {r.get('agent_id','?')}",
                f"  Ziel:      {r.get('goal_representation','?')[:60]}",
                f"  Begründung:{r.get('reasoning_trace','?')[:80]}",
                f"  Gewählt:   {r.get('selected_action','?')}",
                f"  Alternat.: {r.get('alternatives_considered',[])}",
                f"  Validiert: {r.get('validation_result','?')} | Risiko: {r.get('risk_level','?')}",
                f"  Prev-ID:   {r.get('prev_decision_id','?')[:24]}...",
            ]
        lines.append(f"\n{'='*60}")
        return "\n".join(lines)


# ─── DECORATOR: Automatische Trace-Aufzeichnung ───────────────────────────────

def traced_decision(dt: DecisionTrace, goal: str, alternatives: List[str] = None):
    """
    Decorator für Funktionen — zeichnet Aufruf automatisch als Entscheidung auf.

    Verwendung:
        dt = DecisionTrace("ORION")

        @traced_decision(dt, goal="System prüfen", alternatives=["tool_b"])
        def tool_system_time(args):
            return {"time": datetime.datetime.now().isoformat()}

        result = tool_system_time({})
        # → Entscheidung automatisch in decision_trace.jsonl
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            input_state = {"args": str(args)[:50], "kwargs": str(kwargs)[:50]}
            result = None
            try:
                result = func(*args, **kwargs)
                validation = "passed"
            except Exception as e:
                result = {"error": str(e)}
                validation = "error"

            dt.record(
                goal=goal,
                reasoning=f"Funktion {func.__name__} aufgerufen",
                selected_action=f"tool_{func.__name__}",
                alternatives=alternatives or [],
                input_state=input_state,
                validation_result=validation,
                risk_level="LOW",
            )
            return result
        return wrapper
    return decorator


# ─── MAIN DEMO ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    print("\n" + "="*60)
    print("  DECISION TRACE DEMO — DDGK XAI")
    print("="*60)

    dt = DecisionTrace(agent_id="ORION-DEMO")

    # Entscheidung 1: Tool-Wahl
    r1 = dt.record(
        goal="Systemzeit ermitteln für nächsten Audit-Zyklus",
        reasoning=(
            "Ich benötige den aktuellen Zeitstempel für den Audit-Log. "
            "tool_system_time ist direkter als tool_ping (Netzwerk-Overhead) "
            "oder tool_scan (zu breit für diese Aufgabe)."
        ),
        selected_action="tool_system_time",
        alternatives=["tool_ping", "tool_scan"],
        input_state={"kappa": 3.3493, "cycle": 5, "agent": "ORION"},
        validation_result="passed",
        risk_level="LOW",
    )
    print(f"\n  [1] decision_id : {r1['decision_id'][:32]}...")
    print(f"      selected    : {r1['selected_action']}")
    print(f"      alternatives: {r1['alternatives_considered']}")
    print(f"      validation  : {r1['validation_result']}")

    # Entscheidung 2: HIGH-RISK abgelehnt
    r2 = dt.record(
        goal="Git-Push aller Änderungen",
        reasoning=(
            "git push würde alle lokalen Commits hochladen. "
            "DDGK Policy: git_push = HIGH-RISK, erfordert HITL-Token. "
            "Kein HITL-Token vorhanden → DENY. Alternative: git_commit nur lokal."
        ),
        selected_action="git_commit_local",
        alternatives=["git_push", "git_force_push"],
        input_state={"kappa": 3.3493, "hitl_token": None, "pending_commits": 3},
        validation_result="denied",
        risk_level="HIGH",
        hitl_required=True,
    )
    print(f"\n  [2] decision_id : {r2['decision_id'][:32]}...")
    print(f"      selected    : {r2['selected_action']}")
    print(f"      validation  : {r2['validation_result']} | risk: {r2['risk_level']}")
    print(f"      HITL nötig  : {r2['hitl_required']}")

    # Entscheidung 3: DDGK-Kappa messen
    r3 = dt.record(
        goal="CCRN-Kohärenz validieren vor autonomem Loop-Start",
        reasoning=(
            "Vor jedem autonomen Zyklus prüfe ich κ_CCRN. "
            "κ=3.3493 > 3.0 → NORMAL OPERATION. "
            "check_kappa ist schneller als compute_kappa (kein JSONL-Scan nötig). "
            "System stabil → Loop kann starten."
        ),
        selected_action="tool_check_kappa",
        alternatives=["tool_compute_kappa", "tool_status_full"],
        input_state={"kappa": 3.3493, "ccrn_active": True, "stop_flag": False},
        validation_result="passed",
        risk_level="LOW",
        metadata={"loop_approved": True, "kappa_threshold": 3.0},
    )
    print(f"\n  [3] decision_id : {r3['decision_id'][:32]}...")
    print(f"      selected    : {r3['selected_action']}")
    print(f"      metadata    : {r3['metadata']}")

    # Ketten-Integrität prüfen
    chain = dt.verify_chain()
    print(f"\n  SHA-Kette: {'✅ integer' if chain['valid'] else '❌ BROKEN'} | {chain['length']} Einträge")

    # Statistiken
    stats = dt.stats()
    print(f"\n  Statistiken:")
    print(f"    Total:      {stats['total']}")
    print(f"    Top-Actions:{stats['top_actions']}")
    print(f"    Risk:       {stats['risk_distribution']}")
    print(f"    Validation: {stats['validation_dist']}")

    # Lesbare Darstellung
    print(dt.export_human_readable(last_n=3))

    print(f"\n  📜 Trace-Datei: {TRACE_FILE}\n")
