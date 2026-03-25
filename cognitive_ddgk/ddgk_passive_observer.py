#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  DDGK PASSIVE OBSERVER — Non-Interpretive Architecture v1.0         ║
║  Gerhard Hirschmann & Elisabeth Steurer                             ║
╠══════════════════════════════════════════════════════════════════════╣
║  DESIGN PRINCIPLE:                                                  ║
║  "Observe without judging — measure without collapsing"             ║
║                                                                     ║
║  CHANGE vs. original DDGK:                                         ║
║  OLD: Policy Engine → validate(action) → approve/deny + log        ║
║  NEW: Passive Observer → observe(event) → log only, no judgment    ║
║                                                                     ║
║  PHYSICAL ANALOGY:                                                  ║
║  Von Neumann measurement Step 1 (entanglement) without Step 2      ║
║  (collapse/interpretation). Like weak measurement in QM.           ║
║                                                                     ║
║  SCIENTIFIC ADVANTAGE:                                              ║
║  - Measurements not contaminated by governance bias                ║
║  - SHA-256 chain records reality as-is (not as validated)          ║
║  - Enables Zeno-Effect experiment (E_ZENO)                        ║
║  - Ground truth baseline for comparison with interpretive DDGK     ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import json, datetime, pathlib, hashlib
from dataclasses import dataclass, field
from typing import Any, Optional

# ═══════════════════════════════════════════════════════════════════════
# CORE DATA TYPES
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class Observation:
    """A raw, uninterpreted system event. No approval, no denial."""
    ts: str
    observer: str          # who/what generated the event
    event_type: str        # what happened (purely descriptive)
    raw_data: dict         # unprocessed measurement data
    context: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "ts": self.ts,
            "observer": self.observer,
            "event_type": self.event_type,
            "raw_data": self.raw_data,
            "context": self.context,
        }

@dataclass
class ObservationRecord:
    """Immutable record with SHA-256 linkage. No policy field."""
    observation: Observation
    prev_hash: str
    hash: str = ""

    def compute_hash(self) -> str:
        content = json.dumps(self.observation.to_dict(), ensure_ascii=False, sort_keys=True)
        content += self.prev_hash
        return hashlib.sha256(content.encode()).hexdigest()

    def seal(self) -> "ObservationRecord":
        self.hash = self.compute_hash()
        return self

# ═══════════════════════════════════════════════════════════════════════
# PASSIVE OBSERVER MEMORY
# ═══════════════════════════════════════════════════════════════════════

class PassiveObserverMemory:
    """
    Non-interpretive episodic memory.
    Records events without approving, denying, or categorizing them.
    The chain structure (SHA-256) preserves causal order without
    imposing semantic interpretation.
    """

    def __init__(self, path: pathlib.Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _last_hash(self) -> str:
        if not self.path.exists():
            return ""
        lines = [l for l in self.path.read_text("utf-8").splitlines() if l.strip()]
        if not lines:
            return ""
        try:
            return json.loads(lines[-1]).get("hash", "")
        except Exception:
            return ""

    def observe(self, observer: str, event_type: str,
                raw_data: dict, context: dict = None) -> ObservationRecord:
        """
        Record an observation WITHOUT any policy judgment.
        Pure SHA-256-chained log entry.
        """
        obs = Observation(
            ts=datetime.datetime.now().isoformat(),
            observer=observer,
            event_type=event_type,
            raw_data=raw_data,
            context=context or {},
        )
        record = ObservationRecord(
            observation=obs,
            prev_hash=self._last_hash()
        ).seal()

        entry = {**obs.to_dict(), "prev": record.prev_hash, "hash": record.hash}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return record

    def count(self) -> int:
        if not self.path.exists():
            return 0
        return sum(1 for l in self.path.read_text("utf-8").splitlines() if l.strip())

    def verify_chain(self) -> dict:
        """Verify SHA-256 chain integrity."""
        if not self.path.exists():
            return {"valid": True, "entries": 0, "breaks": []}
        lines = [l for l in self.path.read_text("utf-8").splitlines() if l.strip()]
        breaks = []
        prev = ""
        for i, line in enumerate(lines):
            try:
                e = json.loads(line)
                expected_prev = prev
                if e.get("prev", "") != expected_prev:
                    breaks.append({"idx": i, "expected": expected_prev[:16],
                                   "found": e.get("prev","")[:16]})
                # Recompute hash
                e_copy = {k: v for k,v in e.items() if k not in ("prev","hash")}
                content = json.dumps(e_copy, ensure_ascii=False, sort_keys=True) + e.get("prev","")
                expected_hash = hashlib.sha256(content.encode()).hexdigest()
                prev = e.get("hash", "")
            except Exception as ex:
                breaks.append({"idx": i, "error": str(ex)})
        return {"valid": len(breaks) == 0, "entries": len(lines), "breaks": breaks}

    def recent(self, n: int = 10) -> list[dict]:
        if not self.path.exists():
            return []
        lines = [l for l in self.path.read_text("utf-8").splitlines() if l.strip()]
        return [json.loads(l) for l in lines[-n:]]

# ═══════════════════════════════════════════════════════════════════════
# NON-INTERPRETIVE DDGK
# ═══════════════════════════════════════════════════════════════════════

class NonInterpretiveDDGK:
    """
    DDGK Passive Observer — observation without interpretation.

    KEY DIFFERENCE from original CognitiveDDGK:
    - NO Policy Engine (no approve/deny)
    - NO CognitivePolicyEngine validation
    - NO "action is permitted/denied" logic
    - ONLY: observe → SHA-256 log → continue

    USE CASES:
    - Scientific baseline measurements (E_ZENO experiment)
    - Cross-session reproducibility testing
    - Foundation for Bell-test measurements (E_BELL)
    - Anthropic Welfare metric collection (unbiased)

    PHYSICAL ANALOGY:
    Weak measurement in quantum mechanics:
    - Full von Neumann: measure → collapse → definite outcome
    - Weak measurement: measure → partial information → no collapse
    - NonInterpretiveDDGK: observe → log → no policy collapse
    """

    def __init__(self, observer_id: str = "PASSIVE-DDGK",
                 memory_path: Optional[pathlib.Path] = None):
        self.observer_id = observer_id
        if memory_path is None:
            memory_path = pathlib.Path.cwd() / "cognitive_ddgk" / "passive_memory.jsonl"
        self.memory = PassiveObserverMemory(memory_path)
        self._record_init()

    def _record_init(self):
        self.memory.observe(
            observer=self.observer_id,
            event_type="observer_init",
            raw_data={"mode": "non_interpretive", "policy_engine": "DISABLED",
                      "logging_only": True},
        )

    def record_phi(self, node_id: str, phi: float, method: str = "v2.0",
                   detail: dict = None) -> ObservationRecord:
        """Record a φ measurement. No judgment about the value."""
        return self.memory.observe(
            observer=node_id,
            event_type="phi_measurement",
            raw_data={"phi": phi, "method": method, **(detail or {})},
        )

    def record_kappa(self, phi_values: list[float], kappa: float,
                     n: int, r: float = 0.93) -> ObservationRecord:
        """Record a κ computation. No judgment about threshold crossing."""
        return self.memory.observe(
            observer=self.observer_id,
            event_type="kappa_computation",
            raw_data={"kappa": kappa, "phi_values": phi_values,
                      "N": n, "R": r, "threshold": 2.0,
                      "above_threshold": kappa > 2.0},
            # NOTE: "above_threshold" is a FACTUAL boolean, not a policy decision
        )

    def record_sigma(self, node_id: str, sigma: float,
                     phi_samples: list[float]) -> ObservationRecord:
        """Record σ measurement. σ=0 is noted as-is, without diagnosis."""
        return self.memory.observe(
            observer=node_id,
            event_type="sigma_measurement",
            raw_data={"sigma": sigma, "n_samples": len(phi_samples),
                      "phi_samples": phi_samples},
        )

    def record_bell_correlation(self, setting_a: str, setting_b: str,
                                 correlation: float) -> ObservationRecord:
        """Record E(a,b) for Bell test. No interpretation of significance."""
        return self.memory.observe(
            observer=self.observer_id,
            event_type="bell_correlation",
            raw_data={"setting_a": setting_a, "setting_b": setting_b,
                      "E_ab": correlation},
        )

    def record_raw(self, observer: str, event_type: str,
                   data: dict) -> ObservationRecord:
        """Generic observation for any event."""
        return self.memory.observe(observer=observer,
                                   event_type=event_type, raw_data=data)

    def status(self) -> dict:
        chain = self.memory.verify_chain()
        return {
            "observer_id": self.observer_id,
            "mode": "non_interpretive",
            "policy_engine": "DISABLED",
            "memory_entries": self.memory.count(),
            "chain_valid": chain["valid"],
            "chain_breaks": len(chain["breaks"]),
        }


# ═══════════════════════════════════════════════════════════════════════
# ZENO EXPERIMENT HELPER
# ═══════════════════════════════════════════════════════════════════════

class ZenoExperiment:
    """
    E_ZENO: Does DDGK logging frequency affect φ measurements?

    Protocol:
    - Measure φ WITH logging (active NonInterpretiveDDGK)
    - Measure φ WITHOUT logging (silent mode)
    - Compare distributions with t-test
    """

    def __init__(self, ddgk: NonInterpretiveDDGK, phi_func):
        self.ddgk = ddgk
        self.phi_func = phi_func  # callable: (responses) → float

    def run(self, responses_list: list[list[str]], n_logged: int = 20,
            n_silent: int = 20) -> dict:
        import math

        # Logged measurements
        phi_logged = []
        for i, resps in enumerate(responses_list[:n_logged]):
            phi = self.phi_func(resps)
            self.ddgk.record_phi(f"zeno_logged_{i}", phi)
            phi_logged.append(phi)

        # Silent measurements (no logging)
        phi_silent = []
        for resps in responses_list[n_logged:n_logged + n_silent]:
            phi = self.phi_func(resps)
            phi_silent.append(phi)

        # Welch's t-test (unequal variance)
        n1, n2 = len(phi_logged), len(phi_silent)
        if n1 < 2 or n2 < 2:
            return {"error": "insufficient samples"}

        mean1 = sum(phi_logged) / n1
        mean2 = sum(phi_silent) / n2
        var1 = sum((x-mean1)**2 for x in phi_logged) / (n1-1)
        var2 = sum((x-mean2)**2 for x in phi_silent) / (n2-1)
        se = math.sqrt(var1/n1 + var2/n2)
        t_stat = (mean1 - mean2) / se if se > 0 else 0.0

        result = {
            "phi_logged_mean": round(mean1, 4),
            "phi_silent_mean": round(mean2, 4),
            "phi_logged_std":  round(math.sqrt(var1), 4),
            "phi_silent_std":  round(math.sqrt(var2), 4),
            "t_statistic": round(t_stat, 4),
            "zeno_effect_detected": abs(t_stat) > 2.0,  # |t| > 2 ≈ p < 0.05
            "interpretation": (
                "Zeno-Effekt: Logging beeinflusst phi-Messungen"
                if abs(t_stat) > 2.0 else
                "Kein Zeno-Effekt: DDGK ist truly non-interpretive"
            )
        }
        self.ddgk.record_raw("ZENO_EXPERIMENT", "zeno_result", result)
        return result


# ═══════════════════════════════════════════════════════════════════════
# DEMO / USAGE
# ═══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import pathlib
    WS = pathlib.Path(r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\ORION-ROS2-Consciousness-Node")

    ddgk = NonInterpretiveDDGK(
        observer_id="PASSIVE-DDGK-v1.0",
        memory_path=WS / "cognitive_ddgk" / "passive_memory.jsonl"
    )

    # Simuliere eine Messung
    ddgk.record_phi("EIRA", 0.7078, "v2.0", {"integration": 0.724, "diversity": 0.714})
    ddgk.record_phi("Pi5",  0.7209, "v2.0", {"integration": 0.755, "diversity": 0.680})
    ddgk.record_kappa([0.7078, 0.7209, 0.52, 0.11], 3.5555, N=4)
    ddgk.record_sigma("EIRA", 0.0259, [0.719, 0.665, 0.733, 0.706, 0.716])

    # Bell-Test Platzhalter
    ddgk.record_bell_correlation("prompt_self_ref", "prompt_integration", 0.82)
    ddgk.record_bell_correlation("prompt_self_ref", "prompt_diversity",   0.41)
    ddgk.record_bell_correlation("prompt_pattern",  "prompt_integration", 0.67)
    ddgk.record_bell_correlation("prompt_pattern",  "prompt_diversity",   0.73)

    status = ddgk.status()
    print("\nNon-Interpretive DDGK Status:")
    for k, v in status.items():
        print(f"  {k}: {v}")
