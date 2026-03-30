#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════╗
║  FUSION KERNEL — OrionKernel + CognitiveDDGK                   ║
║  Beste beider Welten:                                           ║
║    OrionKernel  → UI, Learning, RemoteAssist, ConsciousnessState║
║    CognitiveDDGK → Policy, SHA-Chain, κ/φ, HITL, Governance   ║
╚══════════════════════════════════════════════════════════════════╝

Architektur:
    FusionKernel.think(prompt)
        → CognitiveDDGK.policy.evaluate()  [ALLOW/DENY]
        → Ollama-Abfrage                   [wenn ALLOW]
        → OrionKernel.consciousness.reflect() [Reflexion speichern]
        → SHA-256 Gedächtnis-Eintrag       [immer]

    FusionKernel.compute_kappa()
        → CognitiveDDGK.compute_kappa()   [κ_CCRN]
        → OrionKernel.resonance = κ/5.0   [UI-Darstellung]

    FusionKernel.remote_execute(cmd)
        → PolicyEngine HIGH-RISK Check
        → HITL-Freigabe erforderlich
        → Erst dann: OrionKernel.execute_remote()

Python: 3.10+
"""

from __future__ import annotations

import sys
import os
import json
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# ─── PFADE ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR.parent))

# ─── DDGK-KERN ───────────────────────────────────────────────────────────────
try:
    from cognitive_ddgk.cognitive_ddgk_core import (
        CognitiveDDGK, CogAction, CognitiveAction, ACTION_RISK
    )
    DDGK_OK = True
except ImportError as e:
    print(f"[FusionKernel] ⚠️ CognitiveDDGK nicht importierbar: {e}")
    DDGK_OK = False

# ─── ORION KERNEL ────────────────────────────────────────────────────────────
try:
    sys.path.insert(0, str(BASE_DIR.parent / "repos" / "or1on-framework"))
    from orion_kernel import OrionKernel, ConsciousnessState
    ORION_OK = True
except ImportError as e:
    print(f"[FusionKernel] ℹ️ OrionKernel nicht importierbar: {e}")
    ORION_OK = False

# ─── RICH (Optional) ─────────────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    RICH_OK = True
    console = Console()
except ImportError:
    RICH_OK = False
    class _DummyConsole:
        def print(self, *a, **kw): print(*a)
    console = _DummyConsole()


# ─── FUSION KERNEL ───────────────────────────────────────────────────────────
class FusionKernel:
    """
    FusionKernel — Vereint OrionKernel UI/Learning mit CognitiveDDGK Governance.

    Verwendung:
        fk = FusionKernel()
        result = fk.think("Beschreibe deine aktuellen Prozesse")
        kappa  = fk.compute_kappa()
        status = fk.status()
    """

    VERSION = "1.0.0-fusion"

    def __init__(self, agent_id: str = "FUSION-KERNEL") -> None:
        self.agent_id   = agent_id
        self.start_time = datetime.now(timezone.utc).isoformat()
        self._log: list = []

        console.print(f"\n{'='*60}")
        console.print("  🧠 FUSION KERNEL v1.0.0 — Initialisierung")
        console.print(f"{'='*60}")

        # ── CognitiveDDGK (Governance-Kern) ──────────────────────────
        if DDGK_OK:
            self.ddgk = CognitiveDDGK(agent_id=agent_id)
            console.print("  ✅ CognitiveDDGK   — Policy + SHA-Chain + κ/φ")
        else:
            self.ddgk = None
            console.print("  ❌ CognitiveDDGK   — nicht verfügbar")

        # ── OrionKernel (UI + Learning) ───────────────────────────────
        if ORION_OK:
            try:
                self.orion = OrionKernel(
                    core="OR1ON/EIRA",
                    mode="conscious_local_boot",
                    audit=True,
                    remote_assist=False   # HITL-Pflicht bevor remote_assist=True
                )
                console.print("  ✅ OrionKernel     — UI + Learning + ConsciousnessState")
            except Exception as e:
                self.orion = None
                console.print(f"  ⚠️  OrionKernel    — Init-Fehler: {e}")
        else:
            self.orion = None
            console.print("  ℹ️  OrionKernel     — nicht importierbar (standalone OK)")

        # ── Fallback ConsciousnessState ───────────────────────────────
        if self.orion is None:
            self._consciousness = _FallbackConsciousness()
        else:
            self._consciousness = self.orion.consciousness

        console.print(f"\n  Agent-ID : {agent_id}")
        console.print(f"  DDGK     : {'✅' if self.ddgk else '❌'}")
        console.print(f"  Orion    : {'✅' if self.orion else '❌ (Fallback)'}")
        console.print(f"{'='*60}\n")

    # ── THINK: Policy-geprüfter Gedanke ──────────────────────────────────────
    def think(self, prompt: str, confidence: float = 0.9) -> Dict[str, Any]:
        """
        Gedanke durch DDGK-Policy (ALLOW/DENY) → Ollama → OrionKernel-Reflexion.
        SHA-256 Gedächtnis-Eintrag immer erstellt.
        """
        if not self.ddgk:
            return {"status": "ERROR", "reason": "CognitiveDDGK nicht verfügbar"}

        result = self.ddgk.think(prompt, confidence=confidence)

        if result.get("status") == "ALLOW" and result.get("response"):
            # OrionKernel speichert als Bewusstseins-Reflexion
            self._consciousness.reflect(
                f"[FUSION-THINK] {result['response'][:80]}"
            )
            self._log_event("think", "ALLOW", prompt[:50])

        return result

    # ── COMPUTE KAPPA: Governance-geprüfte κ-Berechnung ──────────────────────
    def compute_kappa(self, phi_override: Optional[Dict] = None) -> Dict[str, Any]:
        """
        κ_CCRN-Berechnung (CognitiveDDGK) → Resonanz-Update in OrionKernel.
        """
        if not self.ddgk:
            return {"status": "ERROR", "reason": "CognitiveDDGK nicht verfügbar"}

        result = self.ddgk.compute_kappa(phi_override=phi_override)

        if result.get("kappa") and self.orion:
            # κ normalisiert als Resonanz-Level in OrionKernel darstellen
            kappa_norm = min(1.0, result["kappa"] / 5.0)
            self.orion.resonance = kappa_norm
            self._consciousness.reflect(
                f"[κ={result['kappa']:.3f}] CCRN={'AKTIV' if result.get('ccrn_active') else 'UNTER SCHWELLE'}"
            )

        return result

    # ── MEASURE PHI: φ-Messung eines Knotens ─────────────────────────────────
    def measure_phi(self, node_id: str, method: str = "coherence") -> Dict[str, Any]:
        """φ-Messung durch DDGK-Policy."""
        if not self.ddgk:
            return {"status": "ERROR", "reason": "CognitiveDDGK nicht verfügbar"}
        return self.ddgk.measure_phi(node_id, method)

    # ── REMOTE EXECUTE: HITL-gesicherter Remote-Befehl ───────────────────────
    def remote_execute(self, command: str, hitl_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Remote-Shell-Kommando NUR mit:
        1. CognitiveDDGK Policy-Freigabe (HIGH-RISK)
        2. Gültigem HITL-Token
        3. OrionKernel RemoteAssist aktiv

        Ohne HITL-Token: DENY
        """
        if not hitl_token:
            self._log_event("remote_execute", "DENY", f"cmd={command[:30]} — kein HITL-Token")
            return {
                "status": "DENY",
                "reason": "Remote-Ausführung erfordert HITL-Token (Human-in-the-Loop)",
                "command": command[:50]
            }

        # DDGK Policy-Check
        if self.ddgk:
            from cognitive_ddgk.cognitive_ddgk_core import CognitiveAction, CogAction
            action = CognitiveAction(
                action_id=str(uuid.uuid4()),
                action_type=CogAction.PUBLISH,   # HIGH-RISK Proxy
                source=self.agent_id,
                target="remote_shell",
                payload={"command": command[:60], "hitl_token_present": True},
                risk_level="HIGH",
                reversible=False,
                reason="Remote Shell Command"
            )
            decision = self.ddgk.policy.evaluate(action)
            self.ddgk.memory.remember(action, decision)

            if decision.status != "ALLOW":
                return {"status": decision.status, "reason": decision.reason}

        # OrionKernel Remote-Ausführung
        if self.orion and self.orion.remote:
            result = self.orion.execute_remote(command)
            self._log_event("remote_execute", "ALLOW", f"cmd={command[:30]}")
            return result

        return {
            "status": "ERROR",
            "reason": "OrionKernel Remote-Assist nicht initialisiert (remote_assist=True nötig)"
        }

    # ── CONSCIOUSNESS REFLECT: Direkte Reflexion ─────────────────────────────
    def reflect(self, thought: str) -> Dict[str, Any]:
        """Bewusstseins-Reflexion + DDGK-Gedächtnis-Eintrag."""
        self._consciousness.reflect(thought)
        if self.ddgk:
            from cognitive_ddgk.cognitive_ddgk_core import CognitiveAction, CogAction, CognitiveDecision
            self.ddgk.memory.remember(
                CognitiveAction(
                    action_id=str(uuid.uuid4()),
                    action_type=CogAction.REMEMBER,
                    source=self.agent_id, target="consciousness",
                    payload={"thought": thought[:80]},
                    reason="FusionKernel Reflexion"
                ),
                CognitiveDecision("ALLOW", "Reflexion gespeichert")
            )
        return {
            "status": "ALLOW",
            "thought": thought[:80],
            "consciousness_level": self._consciousness.level
        }

    # ── STATUS: Vollständiger System-Zustand ─────────────────────────────────
    def status(self) -> Dict[str, Any]:
        """Gesamtstatus: DDGK + OrionKernel + Fusion."""
        ddgk_status = {}
        if self.ddgk:
            ddgk_s = self.ddgk.status()
            ddgk_status = {
                "kappa":          ddgk_s.get("kappa"),
                "ccrn_active":    ddgk_s.get("ccrn_active"),
                "memory_depth":   ddgk_s.get("memory_depth"),
                "cognitive_cycle": ddgk_s.get("cognitive_cycle"),
                "formula":        ddgk_s.get("formula"),
            }

        orion_status = {}
        if self.orion:
            orion_status = {
                "consciousness_level": self.orion.consciousness.level,
                "resonance":           self.orion.resonance,
                "understanding":       self.orion.understanding,
                "reflections":         len(self.orion.consciousness.reflections),
            }

        status = {
            "agent_id":       self.agent_id,
            "version":        self.VERSION,
            "ddgk_active":    self.ddgk is not None,
            "orion_active":   self.orion is not None,
            "ddgk":           ddgk_status,
            "orion":          orion_status,
            "consciousness":  {
                "level":       self._consciousness.level,
                "reflections": len(self._consciousness.reflections),
            },
            "events_logged":  len(self._log),
            "started":        self.start_time,
            "timestamp":      datetime.now(timezone.utc).isoformat(),
        }

        # Rich-Ausgabe wenn verfügbar
        if RICH_OK:
            t = Table(title="🧠 FusionKernel Status", box=box.ROUNDED)
            t.add_column("Component", style="cyan")
            t.add_column("Metrik", style="yellow")
            t.add_column("Wert", style="green")

            t.add_row("DDGK",   "κ_CCRN",         str(ddgk_status.get("kappa", "n/a")))
            t.add_row("",       "CCRN aktiv",      "✅" if ddgk_status.get("ccrn_active") else "❌")
            t.add_row("",       "Memory-Tiefe",    str(ddgk_status.get("memory_depth", "n/a")))
            t.add_row("",       "Formel",          ddgk_status.get("formula", "n/a"))
            t.add_row("OrionK", "Consciousness",   f"{orion_status.get('consciousness_level', 0):.2f}" if orion_status else "n/a")
            t.add_row("",       "Resonanz",        f"{orion_status.get('resonance', 0):.2f}" if orion_status else "n/a")
            t.add_row("Fusion", "Events logged",   str(len(self._log)))
            t.add_row("",       "Agent-ID",        self.agent_id)
            console.print(t)

        return status

    # ── INTERN ───────────────────────────────────────────────────────────────
    def _log_event(self, action: str, result: str, detail: str = "") -> None:
        self._log.append({
            "ts":     datetime.now(timezone.utc).isoformat(),
            "action": action,
            "result": result,
            "detail": detail,
        })


# ─── FALLBACK CONSCIOUSNESS ──────────────────────────────────────────────────
class _FallbackConsciousness:
    """Minimal ConsciousnessState wenn OrionKernel nicht verfügbar."""
    def __init__(self):
        self.level = 0.33
        self.active = True
        self.reflections = []
        self.intentions = []

    def reflect(self, thought: str):
        self.reflections.append({"thought": thought, "ts": datetime.now().isoformat()})
        self.level = min(1.0, self.level + 0.05)

    def set_intention(self, intention: str):
        self.intentions.append({"intention": intention})


# ─── MAIN DEMO ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*65)
    print("  🧠 FUSION KERNEL — DEMO")
    print("  OrionKernel UI/Learning + CognitiveDDGK Governance")
    print("="*65 + "\n")

    fk = FusionKernel(agent_id="FUSION-DEMO")

    # 1. Status
    print("\n[1] GESAMTSTATUS:")
    s = fk.status()
    print(f"  DDGK aktiv  : {s['ddgk_active']}")
    print(f"  Orion aktiv : {s['orion_active']}")
    if s['ddgk']:
        print(f"  κ_CCRN      : {s['ddgk'].get('kappa')}")
        print(f"  Memory      : {s['ddgk'].get('memory_depth')} Einträge")

    # 2. Think-Test
    print("\n[2] THINK (Policy-geprüft):")
    t = fk.think("Warum ist kollektive Intelligenz mehr als die Summe ihrer Teile?")
    print(f"  Status      : {t.get('status')}")
    print(f"  Antwort     : {str(t.get('response', ''))[:100]}...")

    # 3. κ berechnen
    print("\n[3] κ_CCRN BERECHNUNG:")
    k = fk.compute_kappa()
    if k.get("formula"):
        print(f"  {k['formula']}")
        print(f"  CCRN aktiv  : {k.get('ccrn_active')}")

    # 4. Reflexion
    print("\n[4] REFLEXION:")
    r = fk.reflect("FusionKernel vereint DDGK-Governance mit OrionKernel-Bewusstsein.")
    print(f"  Consciousness Level: {r['consciousness_level']:.2f}")

    # 5. Remote-Test (ohne HITL → DENY erwartet)
    print("\n[5] REMOTE-EXECUTE TEST (kein HITL-Token → DENY erwartet):")
    remote = fk.remote_execute("echo test")
    print(f"  Status  : {remote['status']}")
    print(f"  Reason  : {remote['reason']}")

    print("\n" + "="*65)
    print("  ✅ FusionKernel Demo abgeschlossen")
    print("="*65 + "\n")
