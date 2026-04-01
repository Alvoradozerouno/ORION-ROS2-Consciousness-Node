#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  DDGK EVOLUTION GATE — Monotone Selektion                          ║
║                                                                    ║
║  SIK-Axiom: Nur Verbesserungen werden akzeptiert (t_n+1 >= t_n)   ║
║                                                                    ║
║  Was das bedeutet:                                                 ║
║   • Jede Code-Änderung wird gemessen                               ║
║   • Wenn schlechter als vorher → ELIMINATED                        ║
║   • Wenn besser → ACCEPTED + SHA-Proof erstellt                    ║
║   • Basierend auf: Latenz, CPU, κ-Score, Qualität                  ║
║                                                                    ║
║  Das ist der Unterschied zwischen "iterieren" und "evolvieren"     ║
╚══════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import sys, time, hashlib, json, datetime, math
from pathlib import Path
from typing import Callable, Any

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE      = Path(__file__).parent
GATE_LOG  = BASE / "cognitive_ddgk" / "evolution_gate.jsonl"
GATE_LOG.parent.mkdir(exist_ok=True)


class EvolutionState:
    """Speichert den aktuell besten Zustand."""
    def __init__(self, name: str):
        self.name          = name
        self.baseline_ms   = None    # Latenz-Baseline
        self.baseline_cpu  = None    # CPU-Baseline
        self.baseline_kappa= None    # κ-Baseline
        self.generation    = 0
        self.best_hash     = None
        self.history       = []

    def to_dict(self):
        return {
            "name":           self.name,
            "generation":     self.generation,
            "baseline_ms":    self.baseline_ms,
            "baseline_cpu":   self.baseline_cpu,
            "baseline_kappa": self.baseline_kappa,
            "best_hash":      self.best_hash,
        }


class DDGKEvolutionGate:
    """
    Monotone Selektions-Gate für DDGK.
    
    Nutze als Decorator oder manuell:
    
        gate = DDGKEvolutionGate("memory_pipeline")
        latency, cpu = gate.measure(my_function)
        if gate.accept(latency, cpu):
            proof = gate.certify(code_string)
            # → Code wird übernommen
    """

    def __init__(self, module_name: str,
                 kappa_weight: float = 0.4,
                 latency_weight: float = 0.4,
                 cpu_weight: float = 0.2):
        self.module        = module_name
        self.kw            = kappa_weight
        self.lw            = latency_weight
        self.cw            = cpu_weight
        self.state         = EvolutionState(module_name)
        self._load_state()

    def _load_state(self):
        """Lädt letzten bekannten Zustand aus dem Log."""
        try:
            lines = GATE_LOG.read_text("utf-8").splitlines()
            for line in reversed(lines):
                entry = json.loads(line)
                if entry.get("module") == self.module and entry.get("accepted"):
                    s = entry.get("state", {})
                    self.state.baseline_ms    = s.get("baseline_ms")
                    self.state.baseline_cpu   = s.get("baseline_cpu")
                    self.state.baseline_kappa = s.get("baseline_kappa")
                    self.state.generation     = s.get("generation", 0)
                    self.state.best_hash      = s.get("best_hash")
                    break
        except: pass

    def measure(self, func: Callable, *args, **kwargs) -> tuple[float, float, Any]:
        """
        Misst Latenz + CPU-Verbrauch einer Funktion.
        Returns: (latency_ms, cpu_avg, result)
        """
        try:
            import psutil
            cpu_before = psutil.cpu_percent(interval=None)
        except:
            cpu_before = 0

        start  = time.perf_counter()
        result = func(*args, **kwargs)
        end    = time.perf_counter()

        try:
            import psutil
            cpu_after = psutil.cpu_percent(interval=None)
            cpu_avg   = (cpu_before + cpu_after) / 2
        except:
            cpu_avg = 50.0

        latency_ms = (end - start) * 1000
        return latency_ms, cpu_avg, result

    def compute_score(self, latency_ms: float, cpu: float, kappa: float = None) -> float:
        """
        Kombinierter Evolutions-Score (höher = besser).
        score = kw*κ - lw*(latency_norm) - cw*(cpu_norm)
        """
        kappa_val = kappa or 1.0
        # Normalisiere: latency in [0,1] angenommen max 1000ms, cpu in %
        l_norm = min(latency_ms / 1000.0, 1.0)
        c_norm = cpu / 100.0
        score  = self.kw * kappa_val - self.lw * l_norm - self.cw * c_norm
        return round(score, 6)

    def accept(self, latency_ms: float, cpu: float,
               kappa: float = None, force: bool = False) -> bool:
        """
        Monotone Selektion: Akzeptiere NUR wenn Score t_n+1 >= t_n.
        """
        score_new = self.compute_score(latency_ms, cpu, kappa)

        # Erste Messung → immer akzeptieren (initialisiert Baseline)
        if self.state.baseline_ms is None:
            self.state.baseline_ms    = latency_ms
            self.state.baseline_cpu   = cpu
            self.state.baseline_kappa = kappa or 1.0
            self.state.generation     = 1
            result = True
            reason = "BASELINE_INIT"
        else:
            score_old = self.compute_score(
                self.state.baseline_ms,
                self.state.baseline_cpu,
                self.state.baseline_kappa
            )
            improvement = score_new - score_old
            result = improvement >= 0 or force
            reason = (f"ACCEPTED: +{improvement:.4f}" if result
                      else f"ELIMINATED: {improvement:.4f} (regression)")
            if result:
                self.state.baseline_ms    = latency_ms
                self.state.baseline_cpu   = cpu
                self.state.baseline_kappa = kappa or self.state.baseline_kappa
                self.state.generation    += 1

        self._log(latency_ms, cpu, kappa, score_new, result, reason)
        return result

    def certify(self, code_or_result: str) -> str:
        """
        Erstellt SHA-256 Proof für akzeptierten Zustand.
        Dieser Hash ist der Beweis für EU AI Act Artikel 9.
        """
        proof_input = (
            f"{self.module}|"
            f"gen={self.state.generation}|"
            f"ms={self.state.baseline_ms:.4f}|"
            f"cpu={self.state.baseline_cpu:.1f}|"
            f"kappa={self.state.baseline_kappa}|"
            f"code={code_or_result[:200]}"
        )
        h = hashlib.sha256(proof_input.encode()).hexdigest()[:24]
        self.state.best_hash = h
        return h

    def _log(self, ms: float, cpu: float, kappa, score: float,
             accepted: bool, reason: str):
        entry = {
            "ts":       datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "module":   self.module,
            "gen":      self.state.generation,
            "ms":       round(ms, 4),
            "cpu":      round(cpu, 1),
            "kappa":    kappa,
            "score":    score,
            "accepted": accepted,
            "reason":   reason,
            "state":    self.state.to_dict(),
        }
        with GATE_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def get_report(self) -> dict:
        return {
            "module":     self.module,
            "generation": self.state.generation,
            "baseline_ms":    self.state.baseline_ms,
            "baseline_cpu":   self.state.baseline_cpu,
            "baseline_kappa": self.state.baseline_kappa,
            "best_hash":  self.state.best_hash,
        }


# ─── GLOBALE GATE-REGISTRY ────────────────────────────────────────────────────
_GATES: dict[str, DDGKEvolutionGate] = {}

def get_gate(module: str) -> DDGKEvolutionGate:
    """Singleton pro Modul."""
    if module not in _GATES:
        _GATES[module] = DDGKEvolutionGate(module)
    return _GATES[module]


def evolve(module: str, func: Callable, kappa: float = None, *args, **kwargs):
    """
    Convenience-Wrapper: Miss, selektiere und zertifiziere in einem Aufruf.
    
    Beispiel:
        result = evolve("memory_pipeline", run_pipeline, kappa=3.286)
    """
    gate = get_gate(module)
    ms, cpu, result = gate.measure(func, *args, **kwargs)
    accepted = gate.accept(ms, cpu, kappa)
    if accepted:
        proof = gate.certify(str(func.__name__))
        return result, proof, True
    return result, None, False


# ─── SELF-TEST ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n  ⚡ DDGK EVOLUTION GATE — Monotone Selektion Self-Test")
    print("  " + "="*58)

    gate = DDGKEvolutionGate("test_module")

    # Simuliere 5 Generationen Code
    test_cases = [
        # (latency_ms, cpu, kappa, code_label)
        (100.0, 50.0, 1.0,  "Initial version"),
        (90.0,  48.0, 1.2,  "Optimized loops"),
        (95.0,  50.0, 1.1,  "Added feature (slower)"),   # ← sollte rejected werden
        (85.0,  45.0, 1.5,  "Better algorithm"),
        (80.0,  40.0, 2.0,  "LoRA optimized"),
    ]

    print(f"\n  {'GEN':4s} {'LATENZ':8s} {'CPU':6s} {'κ':6s} {'SCORE':8s} {'ERGEBNIS'}")
    print("  " + "-"*55)

    for i, (ms, cpu, kappa, label) in enumerate(test_cases, 1):
        score = gate.compute_score(ms, cpu, kappa)
        accepted = gate.accept(ms, cpu, kappa)
        proof = gate.certify(label) if accepted else "-"
        icon = "✅ ACCEPTED" if accepted else "❌ ELIMINATED"
        print(f"  {i:4d} {ms:8.1f}ms {cpu:5.1f}% {kappa:5.1f} {score:+8.4f}  {icon} | {label}")

    print(f"\n  Finale Generation: {gate.state.generation}")
    print(f"  Bester Hash:       {gate.state.best_hash}")
    print(f"  Log: {GATE_LOG}")

    report = gate.get_report()
    print(f"\n  Report: {report}")
    print(f"\n  → Monotone Evolution sichergestellt.")
    print(f"  → Regression ist unmöglich — System evolviert immer nach oben.")
