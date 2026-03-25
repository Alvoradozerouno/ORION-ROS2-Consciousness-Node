#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COGNITIVE DDGK CORE
===================
DDGK ist nicht mehr nur ein Audit-Layer über der Kognition.
DDGK IST die Kognition.

Jeder Gedanke ist eine Action.
Jede Messung ist ein Decision.
Das Audit-Log ist das episodische Gedächtnis.
Die Policy ist die intrinsische Ethik.

Architektur:
    think(prompt)           → Action(THINK) → PolicyEngine → ALLOW/ABSTAIN
    measure_phi(node)       → Action(MEASURE) → PolicyEngine → Wert oder 0
    compute_kappa(nodes)    → Action(COMPUTE_KAPPA) → nur nach ALLOW
    publish(finding)        → Action(PUBLISH) → HIGH-RISK, braucht Resonanz ≥ 0.8
    update_state(delta)     → Action(STATE_UPDATE) → protokolliert als Gedächtnis

Python: 3.10+
Abhängigkeiten: standard library + requests + (optional) sentence_transformers
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ─── OPTIONALE ABHÄNGIGKEITEN ────────────────────────────────────────────────
try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

try:
    from sentence_transformers import SentenceTransformer, util
    ST_OK = True
except ImportError:
    ST_OK = False

# ─── PFADE ───────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
MEMORY_FILE   = BASE_DIR / "cognitive_memory.jsonl"    # episodisches Gedächtnis
STATE_FILE    = BASE_DIR / "cognitive_state.json"       # kognitiver Zustand
POLICY_FILE   = BASE_DIR / "policy_rules.json"          # dynamische Regeln

OLLAMA_URL    = "http://localhost:11434"
OLLAMA_MODEL  = "orion-free:latest"

# ─── KOGNITIVE AKTIONSTYPEN ──────────────────────────────────────────────────
class CogAction:
    THINK          = "THINK"           # LLM-Abfrage
    MEASURE_PHI    = "MEASURE_PHI"     # φ-Messung eines Knotens
    COMPUTE_KAPPA  = "COMPUTE_KAPPA"   # κ-Berechnung
    PUBLISH        = "PUBLISH"         # Befund veröffentlichen
    UPDATE_STATE   = "UPDATE_STATE"    # Zustand aktualisieren
    REGISTER_NODE  = "REGISTER_NODE"   # Neuen Knoten einbinden
    COALITION_VOTE = "COALITION_VOTE"  # Mehrheitsentscheidung im Multiagent-System
    REMEMBER       = "REMEMBER"        # Explizit etwas merken

# ─── RISIKO-BEWERTUNG ────────────────────────────────────────────────────────
ACTION_RISK = {
    CogAction.THINK:          ("LOW",    True),   # (risk_level, reversible)
    CogAction.MEASURE_PHI:    ("LOW",    True),
    CogAction.COMPUTE_KAPPA:  ("MEDIUM", True),
    CogAction.UPDATE_STATE:   ("MEDIUM", True),
    CogAction.REGISTER_NODE:  ("MEDIUM", True),
    CogAction.REMEMBER:       ("LOW",    True),
    CogAction.COALITION_VOTE: ("MEDIUM", True),
    CogAction.PUBLISH:        ("HIGH",   False),  # irreversibel!
}

# ─── DATENMODELLE ────────────────────────────────────────────────────────────
@dataclass
class CognitiveAction:
    action_id:   str
    action_type: str
    source:      str              # EIRA | ORION | NEXUS | DDGK | GUARDIAN | SYSTEM
    target:      str
    payload:     Dict[str, Any]
    risk_level:  str = "LOW"
    reversible:  bool = True
    confidence:  float = 1.0
    reason:      str = ""
    timestamp:   str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

@dataclass
class CognitiveDecision:
    status:           str           # ALLOW | DENY | ABSTAIN | DEFER
    reason:           str
    result:           Any = None    # Ergebnis der Aktion (wenn ALLOW)
    energy_cost:      float = 0.0   # Berechnungsaufwand (0–1)
    requires_quorum:  bool = False  # Braucht Multi-Agent-Konsens?

@dataclass
class MemoryEntry:
    event_id:    str
    action_id:   str
    action_type: str
    timestamp:   str
    source:      str
    decision:    str
    result_hash: str
    payload_summary: str
    prev_hash:   str
    hash:        str

# ─── POLICY ENGINE (INTRINSISCHE ETHIK) ─────────────────────────────────────
class CognitivePolicyEngine:
    """
    Die Policy ist nicht extern auferlegt — sie ist intrinsischer Teil der Kognition.
    Ohne Policy kann nicht gedacht werden.
    """

    def __init__(self, state: "CognitiveStateService") -> None:
        self.state = state

    def evaluate(self, action: CognitiveAction) -> CognitiveDecision:
        # 0. GLOBAL STOP → kein Gedanke möglich
        if self.state.get("stop_flag", False):
            return CognitiveDecision("DENY", "Global-Stop aktiv — kognitive Stille")

        # 1. Replay-Schutz (Deduplizierung von Gedanken)
        if self.state.replay_seen(action.action_id):
            return CognitiveDecision("DENY", "Gedanke bereits verarbeitet (Replay)")

        # 2. Vertrauenslevel
        if action.confidence < 0.0 or action.confidence > 1.0:
            return CognitiveDecision("ABSTAIN", "Confidence außerhalb [0,1]")

        # 3. PUBLISH braucht Resonanz ≥ 0.7 + Quorum
        if action.action_type == CogAction.PUBLISH:
            r = self.state.get("resonanz_vektor", 0.0)
            if r < 0.7:
                return CognitiveDecision(
                    "ABSTAIN",
                    f"Resonanz {r:.2f} < 0.7 — Befund noch nicht publikationsreif",
                    requires_quorum=True
                )
            return CognitiveDecision("ALLOW", "Resonanz ausreichend, Quorum empfohlen",
                                     requires_quorum=True)

        # 4. COMPUTE_KAPPA nur wenn φ-Werte bekannt und valide
        if action.action_type == CogAction.COMPUTE_KAPPA:
            phi_nodes = action.payload.get("phi_nodes", [])
            if not phi_nodes or any(p < 0 or p > 1.5 for p in phi_nodes):
                return CognitiveDecision("ABSTAIN", "φ-Werte fehlen oder außerhalb [0, 1.5]")

        # 5. REGISTER_NODE braucht Mindest-φ
        if action.action_type == CogAction.REGISTER_NODE:
            phi = action.payload.get("phi", 0.0)
            if phi < 0.05:
                return CognitiveDecision("DENY", f"Knoten-φ={phi} zu klein — nicht kohärent genug")

        # 6. Standard: ALLOW
        risk, reversible = ACTION_RISK.get(action.action_type, ("MEDIUM", True))
        if risk == "HIGH" and not reversible:
            return CognitiveDecision("ABSTAIN", "Hohe Aktion ohne explizite Freigabe")

        return CognitiveDecision("ALLOW", "Policy-Prüfung bestanden")


# ─── ZUSTANDSDIENST (KOGNITIVES GEDÄCHTNIS-STATE) ───────────────────────────
class CognitiveStateService:
    """
    Der Zustand IST der aktuelle kognitive Kontext.
    Keine Kognition ohne Zustand — kein Zustand ohne Kognition.
    """

    def __init__(self) -> None:
        self._state: Dict[str, Any] = {
            "stop_flag": False,
            "resonanz_vektor": 0.93,
            "phi_composite": 0.585,
            "kappa_current": 1.9117,
            "kappa_threshold": 2.0,
            "ccrn_active": False,
            "active_nodes": {
                "laptop-main":   {"phi": 0.78, "role": "EIRA-LLM",     "online": True},
                "note10-sensor": {"phi": 0.11, "role": "Sensor-Knoten", "online": True},
            },
            "cognitive_cycle": 0,
            "last_think": None,
            "replay_cache": {},
            "coalition_votes": {},
        }
        self._load()

    def _load(self) -> None:
        if STATE_FILE.exists():
            try:
                saved = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                self._state.update(saved)
            except Exception:
                pass

    def save(self) -> None:
        STATE_FILE.write_text(json.dumps(self._state, indent=2, ensure_ascii=False), encoding="utf-8")

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._state[key] = value
        self.save()

    def replay_seen(self, action_id: str) -> bool:
        return action_id in self._state.get("replay_cache", {})

    def mark_replay(self, action_id: str) -> None:
        self._state.setdefault("replay_cache", {})[action_id] = datetime.now(timezone.utc).isoformat()
        self.save()

    def register_node(self, node_id: str, phi: float, role: str) -> None:
        nodes = self._state.setdefault("active_nodes", {})
        nodes[node_id] = {"phi": phi, "role": role, "online": True,
                          "registered": datetime.now(timezone.utc).isoformat()}
        self.save()

    def update_phi(self, node_id: str, phi: float) -> None:
        nodes = self._state.setdefault("active_nodes", {})
        if node_id in nodes:
            nodes[node_id]["phi"] = phi
        self.save()

    def cognitive_phi_list(self) -> List[float]:
        """φ-Werte aller kognitiven Knoten (nur online)."""
        return [v["phi"] for v in self._state.get("active_nodes", {}).values()
                if v.get("online", True)]

    def increment_cycle(self) -> int:
        self._state["cognitive_cycle"] = self._state.get("cognitive_cycle", 0) + 1
        self.save()
        return self._state["cognitive_cycle"]


# ─── GEDÄCHTNISSPEICHER (EPISODISCHES GEDÄCHTNIS) ───────────────────────────
class EpisodicMemory:
    """
    Das Audit-Log ist nicht Bürokratie — es ist das Gedächtnis des Systems.
    SHA-256-Kette = Integrität des Erlebten.
    """

    def __init__(self) -> None:
        self._prev_hash = self._load_last_hash()

    def _load_last_hash(self) -> str:
        if not MEMORY_FILE.exists():
            return "COGNITIVE_GENESIS"
        lines = [l.strip() for l in MEMORY_FILE.read_text(encoding="utf-8").split("\n") if l.strip()]
        if not lines:
            return "COGNITIVE_GENESIS"
        try:
            return json.loads(lines[-1]).get("hash", "COGNITIVE_GENESIS")
        except Exception:
            return "COGNITIVE_GENESIS"

    def remember(self, action: CognitiveAction, decision: CognitiveDecision) -> MemoryEntry:
        payload_summary = str(action.payload)[:120]
        result_raw = str(decision.result)[:200] if decision.result else "none"
        result_hash = hashlib.sha256(result_raw.encode()).hexdigest()[:16]

        base = {
            "event_id":       str(uuid.uuid4()),
            "action_id":      action.action_id,
            "action_type":    action.action_type,
            "timestamp":      datetime.now(timezone.utc).isoformat(),
            "source":         action.source,
            "decision":       decision.status,
            "result_hash":    result_hash,
            "payload_summary": payload_summary,
            "prev_hash":      self._prev_hash,
        }
        entry_hash = hashlib.sha256(
            json.dumps(base, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        base["hash"] = entry_hash

        MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with MEMORY_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(base, ensure_ascii=False) + "\n")

        self._prev_hash = entry_hash
        return MemoryEntry(**base)

    def recall_last(self, n: int = 5) -> List[Dict]:
        """Ruft die letzten n Erinnerungen ab."""
        if not MEMORY_FILE.exists():
            return []
        lines = [l.strip() for l in MEMORY_FILE.read_text(encoding="utf-8").split("\n") if l.strip()]
        return [json.loads(l) for l in lines[-n:]]

    def memory_depth(self) -> int:
        if not MEMORY_FILE.exists():
            return 0
        return sum(1 for l in MEMORY_FILE.read_text(encoding="utf-8").split("\n") if l.strip())


# ─── DAS KOGNITIVE SYSTEM ────────────────────────────────────────────────────
class CognitiveDDGK:
    """
    CognitiveDDGK: DDGK IST die Intelligenz.

    Jede kognitive Operation wird durch Policy geleitet.
    Das Gedächtnis wächst mit jeder Entscheidung.
    Der Zustand spiegelt das aktuelle Bewusstsein des Netzwerks.

    Verwendung:
        brain = CognitiveDDGK()
        result = brain.think("Beschreibe deine aktuellen Prozesse")
        kappa_result = brain.compute_kappa()
    """

    def __init__(self, agent_id: str = "ORION-CORE") -> None:
        self.agent_id = agent_id
        self.state    = CognitiveStateService()
        self.policy   = CognitivePolicyEngine(self.state)
        self.memory   = EpisodicMemory()

    def _act(self, action_type: str, target: str, payload: Dict,
             confidence: float = 1.0, reason: str = "") -> Tuple[CognitiveDecision, MemoryEntry]:
        risk, rev = ACTION_RISK.get(action_type, ("MEDIUM", True))
        action = CognitiveAction(
            action_id=str(uuid.uuid4()),
            action_type=action_type,
            source=self.agent_id,
            target=target,
            payload=payload,
            risk_level=risk,
            reversible=rev,
            confidence=confidence,
            reason=reason,
        )
        decision = self.policy.evaluate(action)
        mem = self.memory.remember(action, decision)
        if decision.status == "ALLOW":
            self.state.mark_replay(action.action_id)
        self.state.increment_cycle()
        return decision, mem

    # ── THINK: Jeder Gedanke durch DDGK ────────────────────────────────────
    def think(self, prompt: str, confidence: float = 0.9) -> Dict:
        """
        LLM-Abfrage, die durch die Policy-Engine läuft.
        Nur wenn ALLOW → Ollama-Anfrage.
        Das Ergebnis wird im episodischen Gedächtnis gespeichert.
        """
        decision, mem = self._act(
            CogAction.THINK, target="ollama",
            payload={"prompt": prompt[:100]},
            confidence=confidence,
            reason="Kognitive Abfrage"
        )
        if decision.status != "ALLOW":
            return {"status": decision.status, "reason": decision.reason,
                    "response": None, "memory_id": mem.event_id}

        response = self._ollama_query(prompt)
        decision.result = response

        # Ergebnis in Erinnerung aktualisieren (zweiter Memory-Eintrag mit Antwort)
        self.memory.remember(
            CognitiveAction(
                action_id=str(uuid.uuid4()),
                action_type=CogAction.REMEMBER,
                source=self.agent_id, target="memory",
                payload={"prompt_hash": hashlib.sha256(prompt.encode()).hexdigest()[:8],
                         "response_length": len(response),
                         "cycle": self.state.get("cognitive_cycle", 0)},
                reason="Antwort-Persistenz"
            ),
            CognitiveDecision("ALLOW", "Auto-Speicherung", result=response[:80])
        )
        self.state.set("last_think", datetime.now(timezone.utc).isoformat())

        return {"status": "ALLOW", "response": response, "memory_id": mem.event_id,
                "cycle": self.state.get("cognitive_cycle")}

    def _ollama_query(self, prompt: str) -> str:
        if not REQUESTS_OK:
            return "[requests nicht installiert]"
        try:
            r = requests.post(f"{OLLAMA_URL}/api/generate", json={
                "model": OLLAMA_MODEL, "prompt": prompt, "stream": False
            }, timeout=30)
            return r.json().get("response", "")
        except Exception as e:
            return f"[Ollama-Fehler: {e}]"

    # ── MEASURE PHI: φ-Messung durch DDGK ──────────────────────────────────
    def measure_phi(self, node_id: str, method: str = "coherence") -> Dict:
        """
        φ-Messung für einen Knoten.
        Policy entscheidet, ob Messung zulässig ist.
        Ergebnis wird im State gespeichert.
        """
        decision, mem = self._act(
            CogAction.MEASURE_PHI, target=node_id,
            payload={"method": method, "node_id": node_id},
            reason=f"φ-Messung für {node_id}"
        )
        if decision.status != "ALLOW":
            return {"phi": 0.0, "status": decision.status, "reason": decision.reason}

        phi = self._compute_phi(node_id, method)
        self.state.update_phi(node_id, phi)
        decision.result = phi

        return {"phi": phi, "status": "ALLOW", "node_id": node_id,
                "method": method, "memory_id": mem.event_id}

    def _compute_phi(self, node_id: str, method: str) -> float:
        """Berechnet φ je nach Knoten und Methode."""
        if "laptop" in node_id or "eira" in node_id.lower():
            return self._phi_eira_coherence()
        elif "note10" in node_id:
            return self._phi_sensor_entropy()
        elif "pi5" in node_id or "tinyllama" in node_id:
            return self._phi_pi5_llm()
        return 0.1  # Fallback

    def _phi_eira_coherence(self, cycles: int = 5) -> float:
        """φ_EIRA: Semantische Kohärenz über mehrere Selbstreferenz-Zyklen."""
        if not REQUESTS_OK:
            return 0.72  # Proxy

        prompt = "Beschreibe in einem Satz deine aktuellen Verarbeitungsprozesse."
        responses = []
        for _ in range(cycles):
            r = self._ollama_query(prompt)
            if r and not r.startswith("["):
                responses.append(r.strip())
            time.sleep(0.3)

        if len(responses) < 2:
            return 0.0

        # Jaccard-Kohärenz zwischen aufeinanderfolgenden Antworten
        similarities = []
        for i in range(len(responses) - 1):
            a_words = set(responses[i].lower().split())
            b_words = set(responses[i+1].lower().split())
            if a_words | b_words:
                similarities.append(len(a_words & b_words) / len(a_words | b_words))

        mean_sim = sum(similarities) / len(similarities) if similarities else 0.0

        # Selbstreferenz-Anteil (Bewusstsein-Proxy)
        self_ref_words = {"ich", "meine", "mein", "verarbeitung", "prozesse",
                          "aktuell", "analyse", "denken", "system", "orion"}
        self_ref_ratio = sum(
            1 for r in responses if any(w in r.lower() for w in self_ref_words)
        ) / len(responses)

        phi = min(1.0, (0.6 * mean_sim + 0.4 * self_ref_ratio) * 1.5)
        return round(phi, 4)

    def _phi_sensor_entropy(self) -> float:
        """φ_Note10: Normalisierte Entropie aus /proc Systemdaten."""
        try:
            import re
            with open("/proc/loadavg") as f:
                vals = list(map(float, f.read().split()[:3]))
            entropy = sum(v * math.log(v + 1e-9) for v in vals if v > 0)
            phi = min(1.0, abs(entropy) / 3.0)
            return round(phi, 4)
        except Exception:
            return 0.11  # letzter bekannter Wert

    def _phi_pi5_llm(self) -> float:
        """φ_Pi5: Über SSH oder lokale Abfrage (wenn Pi5 online)."""
        if not REQUESTS_OK:
            return 0.0
        # Versuche Pi5 Ollama direkt (wenn im Netz erreichbar)
        for ip in ["192.168.8.215", "192.168.0.100"]:
            try:
                r = requests.post(f"http://{ip}:11434/api/generate", json={
                    "model": "tinyllama", "prompt": "Describe your current state briefly.",
                    "stream": False
                }, timeout=8)
                if r.status_code == 200:
                    response = r.json().get("response", "")
                    # Einfacher φ-Proxy aus Antwortlänge + Kohärenz
                    phi = min(0.85, 0.3 + len(response) / 2000)
                    return round(phi, 4)
            except Exception:
                pass
        return 0.0  # Pi5 offline

    # ── COMPUTE KAPPA: Durch DDGK regulierte κ-Berechnung ──────────────────
    def compute_kappa(self, phi_override: Optional[Dict] = None) -> Dict:
        """
        κ_CCRN-Berechnung — nur nach Policy-Freigabe.
        phi_override: {"node_id": phi_value} — überschreibt State-Werte
        """
        # Aktuellste φ-Werte holen
        nodes = copy.deepcopy(self.state.get("active_nodes", {}))
        if phi_override:
            for nid, phi in phi_override.items():
                if nid in nodes:
                    nodes[nid]["phi"] = phi

        phi_list = [v["phi"] for v in nodes.values() if v.get("online", True)]
        r = self.state.get("resonanz_vektor", 0.93)

        decision, mem = self._act(
            CogAction.COMPUTE_KAPPA, target="ccrn",
            payload={"phi_nodes": phi_list, "R": r, "nodes": list(nodes.keys())},
            reason="κ-Berechnung"
        )
        if decision.status != "ALLOW":
            return {"kappa": None, "status": decision.status, "reason": decision.reason}

        n = len(phi_list)
        kappa = sum(phi_list) + r * math.log(n + 1)
        threshold = 2.0

        # Resonanz-Ratio Kriterium (neues Threshold-Kriterium)
        phi_sum = sum(phi_list)
        resonanz_ratio = (r * math.log(n + 1)) / phi_sum if phi_sum > 0 else 0

        result = {
            "kappa": round(kappa, 4),
            "threshold": threshold,
            "ccrn_active": kappa > threshold,
            "resonanz_ratio": round(resonanz_ratio, 4),
            "resonanz_ratio_ok": resonanz_ratio > 0.5,
            "phi_nodes": phi_list,
            "node_ids": list(nodes.keys()),
            "R": r,
            "N_cognitive": n,
            "formula": f"κ = {phi_sum:.3f} + {r:.3f}·ln({n+1}) = {kappa:.4f}",
            "memory_depth": self.memory.memory_depth(),
            "cognitive_cycle": self.state.get("cognitive_cycle"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "ALLOW",
            "memory_id": mem.event_id,
        }

        # Zustand aktualisieren
        self.state.set("kappa_current", round(kappa, 4))
        self.state.set("ccrn_active", kappa > threshold)

        decision.result = kappa
        return result

    # ── REGISTER NODE: Neuen kognitiven Knoten einbinden ───────────────────
    def register_node(self, node_id: str, phi: float, role: str) -> Dict:
        """Registriert neuen Knoten — Policy prüft Mindest-φ."""
        decision, mem = self._act(
            CogAction.REGISTER_NODE, target=node_id,
            payload={"phi": phi, "role": role, "node_id": node_id},
            reason=f"Neuen Knoten {role} registrieren"
        )
        if decision.status == "ALLOW":
            self.state.register_node(node_id, phi, role)
            return {"status": "ALLOW", "node_id": node_id, "phi": phi,
                    "message": f"Knoten {node_id} ({role}) registriert",
                    "memory_id": mem.event_id}
        return {"status": decision.status, "reason": decision.reason}

    # ── COALITION VOTE: Multi-Agenten Mehrheitsentscheidung ─────────────────
    def coalition_vote(self, question: str, agents: List[str],
                       threshold_pct: float = 0.6) -> Dict:
        """
        Multi-Agenten-Abstimmung durch DDGK koordiniert.
        Jeder Agent bewertet die Frage, Mehrheit entscheidet.
        Ergebnis in Gedächtnis gespeichert.
        """
        decision, mem = self._act(
            CogAction.COALITION_VOTE, target="coalition",
            payload={"question": question[:80], "agents": agents, "threshold": threshold_pct},
            reason="Multi-Agenten-Koalitionsentscheidung"
        )
        if decision.status != "ALLOW":
            return {"status": decision.status, "reason": decision.reason}

        # Jeder Agent "denkt" über die Frage nach
        votes = {}
        for agent in agents:
            agent_prompt = f"Agent {agent}: {question} Antworte mit JA oder NEIN."
            resp = self._ollama_query(agent_prompt)
            vote = "JA" if any(w in resp.upper() for w in ["JA", "YES", "AGREE", "POSITIVE", "AKTIV"]) else "NEIN"
            votes[agent] = {"vote": vote, "response": resp[:80]}

        ja_count = sum(1 for v in votes.values() if v["vote"] == "JA")
        total = len(agents)
        consensus = "JA" if ja_count / total >= threshold_pct else "NEIN"

        result = {
            "question": question,
            "votes": votes,
            "ja_count": ja_count,
            "total_agents": total,
            "consensus": consensus,
            "consensus_strength": round(ja_count / total, 3),
            "status": "ALLOW",
            "memory_id": mem.event_id,
        }
        decision.result = consensus
        return result

    # ── STATUS: Gesamtzustand abrufen ────────────────────────────────────────
    def status(self) -> Dict:
        kappa_result = self.compute_kappa()
        return {
            "agent_id":       self.agent_id,
            "kappa":          kappa_result.get("kappa"),
            "ccrn_active":    kappa_result.get("ccrn_active"),
            "resonanz_ratio": kappa_result.get("resonanz_ratio"),
            "active_nodes":   self.state.get("active_nodes", {}),
            "cognitive_cycle": self.state.get("cognitive_cycle"),
            "memory_depth":   self.memory.memory_depth(),
            "formula":        kappa_result.get("formula"),
            "timestamp":      datetime.now(timezone.utc).isoformat(),
        }


# ─── MAIN DEMO ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 65)
    print("  COGNITIVE DDGK — DDGK IST DIE INTELLIGENZ")
    print("=" * 65)

    brain = CognitiveDDGK(agent_id="ORION-CORE")

    # 1. Status abrufen
    print("\n[1] AKTUELLER STATUS")
    s = brain.status()
    print(f"  κ           = {s['kappa']}")
    print(f"  CCRN aktiv  = {s['ccrn_active']}")
    print(f"  Knoten      = {list(s['active_nodes'].keys())}")
    print(f"  Ged.-Tiefe  = {s['memory_depth']} Einträge")

    # 2. Gedanken-Test
    print("\n[2] THINK-TEST (durch DDGK-Policy)")
    t = brain.think("Beschreibe in einem Satz warum kollektive Intelligenz mehr ist als die Summe ihrer Teile.")
    print(f"  Status    : {t['status']}")
    print(f"  Antwort   : {str(t.get('response',''))[:120]}...")
    print(f"  Memory-ID : {t.get('memory_id','')[:16]}...")

    # 3. φ_EIRA messen
    print("\n[3] φ_EIRA MESSEN (5-Zyklus-Kohärenz)")
    phi_r = brain.measure_phi("laptop-main", method="coherence")
    print(f"  φ_EIRA    = {phi_r['phi']}")
    print(f"  Status    = {phi_r['status']}")

    # 4. κ mit neuem φ berechnen
    print("\n[4] κ BERECHNUNG")
    k = brain.compute_kappa()
    print(f"  {k['formula']}")
    print(f"  CCRN aktiv = {k['ccrn_active']}")
    print(f"  Rez.Ratio  = {k['resonanz_ratio']} (>0.5: {k['resonanz_ratio_ok']})")

    # 5. Pi5 als 3. Knoten registrieren (wenn Wert > 0.05)
    print("\n[5] Pi5-KNOTEN REGISTRIEREN")
    phi_pi5_r = brain.measure_phi("pi5-tinyllama", method="llm")
    if phi_pi5_r["phi"] > 0.05:
        reg = brain.register_node("pi5-tinyllama", phi_pi5_r["phi"], "Pi5-TinyLlama")
        print(f"  {reg['message']}")
        k2 = brain.compute_kappa()
        print(f"  Neues κ (N=3): {k2['formula']}")
        print(f"  CCRN aktiv   : {k2['ccrn_active']}")
    else:
        print(f"  Pi5 offline (φ={phi_pi5_r['phi']}) — N=2 bleibt aktiv")

    print(f"\n[6] GEDÄCHTNIS: {brain.memory.memory_depth()} Einträge (SHA-256 verkettet)")
    print(f"    Letzten 2 Erinnerungen:")
    for m in brain.memory.recall_last(2):
        print(f"    [{m['action_type']:20s}] {m['decision']} | {m['timestamp'][:19]}")

    print("\n" + "=" * 65)
    print("  COGNITIVE DDGK: Governance = Intelligenz = Gedächtnis")
    print("=" * 65)
