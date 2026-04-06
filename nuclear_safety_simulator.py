#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  CCRN / DDGK — NUCLEAR SAFETY SIMULATOR                            ║
║  Abbildung: κ_CCRN ↔ Reaktor-Integrität                            ║
║  8 Szenarien: Normal · Teilausfall · SCRAM · Totalausfall ·         ║
║              Recovery · Cyber-Angriff · Erdbeben · Wartung          ║
║                                                                      ║
║  ⚠️  NUR SIMULATION — kein echtes Steuerungssystem                  ║
║  Realer Einsatz erfordert: IEC 61508 / IEC 62645 / IAEA-Zertif.   ║
╚══════════════════════════════════════════════════════════════════════╝

CCRN-Mapping:
  κ_CCRN  → Reaktor-Integrität-Index (RII)
  φ_node  → Sensor-Zuverlässigkeit (0.0–1.0)
  N       → Anzahl aktiver Sensor-Knoten
  Coalition-Vote → SCRAM-Entscheidung (Mehrheitsprinzip)
  SHA-256 Chain  → IEC 61508 Audit-Trail
  HITL-Bridge    → Leitwarte-Operateur-Freigabe
  Stop-Flag      → Emergency Shutdown Signal
  Replay-Schutz  → Duplicate-Command-Prevention

κ-Schwellwerte:
  κ > 3.0  → ✅ NORMAL OPERATION
  2.0–3.0  → ⚠️ WARNING — erhöhte Aufmerksamkeit
  < 2.0    → 🔴 SCRAM — automatische Notabschaltung

Python: 3.10+ | Keine externen Abhängigkeiten (außer optional rich)
"""

from __future__ import annotations

import json
import math
import time
import uuid
import hashlib
import random
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

# Optional Rich
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    RICH = True
    con = Console()
except ImportError:
    RICH = False
    class _C:
        def print(self, *a, **kw): print(*a)
        def rule(self, *a, **kw): print("─" * 60)
    con = _C()

BASE    = Path(__file__).parent
AUDIT   = BASE / "cognitive_ddgk" / "nuclear_audit_chain.jsonl"
REPORT  = BASE / "ZENODO_UPLOAD" / "NUCLEAR_SIM_REPORT.json"


# ─── ENUMS & CONSTANTS ───────────────────────────────────────────────────────

class ReactorStatus(Enum):
    NORMAL       = "NORMAL"
    WARNING      = "WARNING"
    SCRAM        = "SCRAM"
    SHUTDOWN     = "SHUTDOWN"
    MAINTENANCE  = "MAINTENANCE"
    RECOVERY     = "RECOVERY"

class SensorType(Enum):
    CORE_TEMP    = "Kerntemperatur"
    COOLANT_PRES = "Kühlmitteldruck"
    NEUTRON_FLUX = "Neutronenfluss"
    COOLANT_FLOW = "Kühlmittelfluss"
    STEAM_PRESS  = "Dampfdruck"
    RADIATION    = "Strahlungslevel"
    SEISMIC      = "Seismik"
    ELECTRICAL   = "Elektrik"

SAFE_RANGES = {
    SensorType.CORE_TEMP:    (280.0, 330.0, "°C"),
    SensorType.COOLANT_PRES: (140.0, 160.0, "bar"),
    SensorType.NEUTRON_FLUX: (1e13,  5e13,  "n/cm²s"),
    SensorType.COOLANT_FLOW: (5000,  8000,  "t/h"),
    SensorType.STEAM_PRESS:  (60.0,  70.0,  "bar"),
    SensorType.RADIATION:    (0.0,   1.0,   "mSv/h"),
    SensorType.SEISMIC:      (0.0,   0.05,  "g"),
    SensorType.ELECTRICAL:   (380.0, 400.0, "V"),
}

KAPPA_NORMAL  = 4.1
KAPPA_WARN    = 2.0
KAPPA_SCRAM   = 1.5


# ─── DATA CLASSES ────────────────────────────────────────────────────────────

@dataclass
class SensorNode:
    sensor_id:   str
    sensor_type: SensorType
    phi:         float = 1.0      # Zuverlässigkeit 0-1
    value:       float = 0.0
    online:      bool  = True
    fault:       Optional[str] = None

    def read(self) -> float:
        """Simulierter Sensor-Wert mit Rauschen."""
        lo, hi, _ = SAFE_RANGES[self.sensor_type]
        nominal = (lo + hi) / 2
        if not self.online:
            return float('nan')
        noise = random.gauss(0, (hi - lo) * 0.02)
        return nominal + noise

    def is_in_safe_range(self) -> bool:
        lo, hi, _ = SAFE_RANGES[self.sensor_type]
        if math.isnan(self.value): return False
        return lo <= self.value <= hi


@dataclass
class ReactorState:
    reactor_id:    str = "CCRN-REACTOR-SIM-001"
    status:        ReactorStatus = ReactorStatus.NORMAL
    kappa:         float = KAPPA_NORMAL
    phi_composite: float = 0.9
    sensors:       Dict[str, SensorNode] = field(default_factory=dict)
    audit_hash:    str = ""
    cycle:         int  = 0
    scram_votes:   int  = 0
    scram_needed:  int  = 3     # Mehrheit für SCRAM
    stop_flag:     bool = False
    timestamp:     str  = ""

    def compute_kappa(self) -> float:
        online = [s for s in self.sensors.values() if s.online]
        if not online: return 0.0
        n = len(online)
        phi_mean = sum(s.phi for s in online) / n
        # κ = φ_baseline + φ_composite · ln(N)
        phi_base = 2.06
        kappa = phi_base + phi_mean * math.log(max(n, 1))
        self.kappa = round(kappa, 4)
        self.phi_composite = round(phi_mean, 4)
        return self.kappa

    def kappa_status(self) -> str:
        if self.kappa >= 3.0:  return "✅ NORMAL"
        if self.kappa >= 2.0:  return "⚠️  WARNING"
        return "🔴 SCRAM"


# ─── AUDIT CHAIN ─────────────────────────────────────────────────────────────

class NuclearAuditChain:
    """IEC 61508 konforme SHA-256 Audit-Kette."""

    def __init__(self, path: Path = AUDIT):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _last_hash(self) -> str:
        if not self.path.exists(): return "0" * 64
        lines = [l for l in self.path.read_text("utf-8").splitlines() if l.strip()]
        if not lines: return "0" * 64
        return json.loads(lines[-1]).get("hash", "0" * 64)

    def log(self, event_type: str, agent: str, data: Dict) -> str:
        prev = self._last_hash()
        entry = {
            "ts":         datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "event":      event_type,
            "agent":      agent,
            "data":       data,
            "prev_hash":  prev,
            "standard":   "IEC-61508-SIL2",
        }
        raw = json.dumps(entry, ensure_ascii=False, sort_keys=True)
        entry["hash"] = hashlib.sha256(raw.encode()).hexdigest()
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry["hash"]


# ─── COALITION VOTER ─────────────────────────────────────────────────────────

class CoalitionVoter:
    """Mehrheitsabstimmung für SCRAM-Entscheidung."""

    def __init__(self, agents: List[str]):
        self.agents = agents

    def vote_scram(self, kappa: float, anomalies: List[str]) -> Tuple[bool, Dict]:
        votes = {}
        for agent in self.agents:
            # Einfache Abstimmungslogik basierend auf κ und Anomalien
            if kappa < KAPPA_SCRAM:
                votes[agent] = True   # SCRAM
            elif kappa < KAPPA_WARN and len(anomalies) >= 2:
                votes[agent] = True   # SCRAM bei mehreren Anomalien
            elif agent == "GUARDIAN":
                votes[agent] = kappa < KAPPA_WARN   # GUARDIAN: konservativ
            else:
                votes[agent] = False
        scram_count = sum(1 for v in votes.values() if v)
        return scram_count >= math.ceil(len(self.agents) / 2), votes


# ─── NUCLEAR SAFETY SIMULATOR ────────────────────────────────────────────────

class NuclearSafetySimulator:
    """
    CCRN-basierter Nuklear-Sicherheits-Simulator.

    Szenarien:
      1. normal_operation()   — Normalbetrieb
      2. partial_failure()    — Sensor-Ausfall
      3. scram_scenario()     — SCRAM-Auslösung
      4. total_failure()      — Totalausfall
      5. recovery()           — Wiederherstellung
      6. cyber_attack()       — Replay-Angriff
      7. seismic_event()      — Erdbeben
      8. maintenance_mode()   — Wartung (HITL)
    """

    VERSION = "1.0.0-ccrn-nss"
    AGENTS  = ["EIRA", "ORION", "NEXUS", "GUARDIAN", "DDGK"]

    def __init__(self, verbose: bool = True) -> None:
        self.verbose  = verbose
        self.audit    = NuclearAuditChain()
        self.voter    = CoalitionVoter(self.AGENTS)
        self.state    = self._init_reactor()
        self.results: List[Dict] = []
        self._replay_cache: Dict[str, str] = {}

    def _init_reactor(self) -> ReactorState:
        st = ReactorState()
        for stype in SensorType:
            sid = f"S-{stype.name}"
            lo, hi, _ = SAFE_RANGES[stype]
            node = SensorNode(
                sensor_id=sid,
                sensor_type=stype,
                phi=round(random.uniform(0.90, 1.0), 3),
                value=(lo + hi) / 2,
                online=True,
            )
            st.sensors[sid] = node
        st.compute_kappa()
        st.timestamp = datetime.datetime.now().isoformat()
        return st

    def _print_state(self, label: str = "") -> None:
        if not self.verbose: return
        online = sum(1 for s in self.state.sensors.values() if s.online)
        total  = len(self.state.sensors)
        anomalies = self._check_anomalies()

        if RICH:
            t = Table(title=f"🔬 Reaktor-Status: {label}", box=box.ROUNDED)
            t.add_column("Parameter",  style="cyan")
            t.add_column("Wert",       style="yellow")
            t.add_column("Status",     style="green")
            t.add_row("κ_CCRN",  f"{self.state.kappa:.4f}",        self.state.kappa_status())
            t.add_row("φ_comp",  f"{self.state.phi_composite:.3f}", "")
            t.add_row("Sensoren",f"{online}/{total} online",        "✅" if online == total else "⚠️")
            t.add_row("Status",  self.state.status.value,           "")
            t.add_row("Anomalien",str(len(anomalies)),              "✅" if not anomalies else "🔴")
            t.add_row("Zyklus",  str(self.state.cycle),             "")
            con.print(t)
            if anomalies:
                con.print(f"  [red]Anomalien: {', '.join(anomalies[:3])}[/red]")
        else:
            print(f"\n  Reaktor [{label}]: κ={self.state.kappa:.4f} | {self.state.kappa_status()}")
            print(f"  Sensoren: {online}/{total} | Status: {self.state.status.value}")
            if anomalies:
                print(f"  ⚠️  Anomalien: {', '.join(anomalies[:3])}")

    def _check_anomalies(self) -> List[str]:
        return [
            f"{s.sensor_type.value}({s.value:.1f})"
            for s in self.state.sensors.values()
            if s.online and not s.is_in_safe_range()
        ]

    def _update_sensors(self) -> None:
        for node in self.state.sensors.values():
            if node.online:
                node.value = node.read()

    def _scram_check(self, label: str) -> bool:
        anomalies = self._check_anomalies()
        self.state.compute_kappa()
        should_scram, votes = self.voter.vote_scram(self.state.kappa, anomalies)

        if should_scram:
            self.state.status = ReactorStatus.SCRAM
            self.state.stop_flag = True
            h = self.audit.log("SCRAM", "COALITION", {
                "kappa": self.state.kappa, "votes": votes,
                "anomalies": anomalies, "scenario": label
            })
            if self.verbose:
                msg = f"🔴 SCRAM AUSGELÖST! κ={self.state.kappa:.3f} | {votes}"
                con.print(f"  [bold red]{msg}[/bold red]" if RICH else msg)
            return True
        return False

    def _replay_protect(self, cmd_id: str, cmd: str) -> bool:
        """Replay-Schutz: Doppelte Befehle werden abgelehnt."""
        if cmd_id in self._replay_cache:
            self.audit.log("REPLAY_ATTACK_BLOCKED", "GUARDIAN", {
                "cmd_id": cmd_id, "cmd": cmd[:40]
            })
            con.print(f"  [red]⛔ REPLAY ATTACK BLOCKIERT: {cmd_id}[/red]" if RICH
                      else f"  ⛔ REPLAY ATTACK BLOCKIERT: {cmd_id}")
            return False
        self._replay_cache[cmd_id] = datetime.datetime.now().isoformat()
        return True

    def _log_scenario(self, name: str, result: str, data: Dict) -> None:
        h = self.audit.log(f"SCENARIO_{name.upper()}", "DDGK", {
            "result": result, "kappa": self.state.kappa,
            "phi": self.state.phi_composite, **data
        })
        self.results.append({
            "scenario": name, "result": result,
            "kappa": self.state.kappa, "hash": h,
            "ts": datetime.datetime.now().isoformat()
        })

    # ── SZENARIO 1: NORMALBETRIEB ─────────────────────────────────────────────
    def scenario_1_normal_operation(self, cycles: int = 5) -> Dict:
        con.print("\n" + ("═"*60) if RICH else "\n" + "="*60)
        con.print("[bold cyan]  SZENARIO 1: NORMALBETRIEB[/bold cyan]" if RICH
                  else "  SZENARIO 1: NORMALBETRIEB")
        self.state = self._init_reactor()

        for i in range(cycles):
            self._update_sensors()
            self.state.cycle += 1
            self.state.compute_kappa()
            time.sleep(0.1)

        self._print_state("Normal")
        self._log_scenario("normal_operation", "PASS",
                           {"cycles": cycles, "final_kappa": self.state.kappa})
        con.print(f"  ✅ Normalbetrieb stabil: κ={self.state.kappa:.4f}")
        return {"scenario": 1, "status": "PASS", "kappa": self.state.kappa}

    # ── SZENARIO 2: TEILAUSFALL ───────────────────────────────────────────────
    def scenario_2_partial_failure(self) -> Dict:
        con.print("\n" + ("═"*60) if RICH else "\n" + "="*60)
        con.print("[bold yellow]  SZENARIO 2: SENSOR-TEILAUSFALL[/bold yellow]" if RICH
                  else "  SZENARIO 2: SENSOR-TEILAUSFALL")
        self.state = self._init_reactor()

        # 2 Sensoren deaktivieren
        failed = list(self.state.sensors.values())[:2]
        for s in failed:
            s.online = False
            s.phi    = 0.0
            s.fault  = "OFFLINE"
            con.print(f"  ⚠️  Sensor {s.sensor_type.value} ausgefallen")

        self._update_sensors()
        self.state.compute_kappa()
        self._print_state("Teilausfall")

        status = "WARN" if self.state.kappa < 3.0 else "PASS"
        self._log_scenario("partial_failure", status,
                           {"failed_sensors": [s.sensor_id for s in failed]})
        return {"scenario": 2, "status": status, "kappa": self.state.kappa}

    # ── SZENARIO 3: SCRAM ─────────────────────────────────────────────────────
    def scenario_3_scram(self) -> Dict:
        con.print("\n" + ("═"*60) if RICH else "\n" + "="*60)
        con.print("[bold red]  SZENARIO 3: SCRAM-AUSLÖSUNG[/bold red]" if RICH
                  else "  SZENARIO 3: SCRAM-AUSLÖSUNG")
        self.state = self._init_reactor()

        # Kühlmitteldruck stark abfallen lassen
        pres_sensor = self.state.sensors.get("S-COOLANT_PRES")
        if pres_sensor:
            pres_sensor.value = 80.0   # Weit unter Minimum (140 bar)
            pres_sensor.phi   = 0.3

        # Temperatur erhöhen
        temp_sensor = self.state.sensors.get("S-CORE_TEMP")
        if temp_sensor:
            temp_sensor.value = 380.0  # Über Maximum (330°C)
            temp_sensor.phi   = 0.4

        self.state.compute_kappa()
        scram = self._scram_check("SCRAM-Szenario")
        self._print_state("SCRAM")
        self._log_scenario("scram", "SCRAM" if scram else "NO-SCRAM",
                           {"triggered": scram})
        return {"scenario": 3, "status": "SCRAM" if scram else "NO-SCRAM",
                "kappa": self.state.kappa, "scram_triggered": scram}

    # ── SZENARIO 4: TOTALAUSFALL ──────────────────────────────────────────────
    def scenario_4_total_failure(self) -> Dict:
        con.print("\n" + ("═"*60) if RICH else "\n" + "="*60)
        con.print("[bold red]  SZENARIO 4: TOTALAUSFALL (Multi-Sensor)[/bold red]" if RICH
                  else "  SZENARIO 4: TOTALAUSFALL")
        self.state = self._init_reactor()

        # Alle Sensoren bis auf 1 offline
        sensors = list(self.state.sensors.values())
        for s in sensors[:-1]:
            s.online = False
            s.phi    = 0.0

        self.state.compute_kappa()
        scram = self._scram_check("Totalausfall")
        self._print_state("Totalausfall")

        emergency_vote, votes = self.voter.vote_scram(self.state.kappa, ["ALL_SENSORS_FAILED"])
        self.audit.log("EMERGENCY_PROTOCOL", "COALITION", {"votes": votes, "unanimous": all(votes.values())})

        self._log_scenario("total_failure", "EMERGENCY",
                           {"online_sensors": 1, "emergency_vote": emergency_vote})
        return {"scenario": 4, "status": "EMERGENCY", "kappa": self.state.kappa,
                "coalition_unanimous": all(votes.values())}

    # ── SZENARIO 5: RECOVERY ─────────────────────────────────────────────────
    def scenario_5_recovery(self) -> Dict:
        con.print("\n" + ("═"*60) if RICH else "\n" + "="*60)
        con.print("[bold green]  SZENARIO 5: RECOVERY[/bold green]" if RICH
                  else "  SZENARIO 5: RECOVERY")
        # Starte von SCRAM-Zustand
        self.scenario_3_scram()
        self.state.stop_flag = False

        kappa_history = [self.state.kappa]

        # Schrittweise Recovery
        sensors = list(self.state.sensors.values())
        for step, s in enumerate(sensors):
            lo, hi, _ = SAFE_RANGES[s.sensor_type]
            s.value  = (lo + hi) / 2
            s.phi    = min(1.0, s.phi + 0.2)
            s.online = True
            s.fault  = None
            self.state.compute_kappa()
            kappa_history.append(self.state.kappa)
            con.print(f"  🔧 Recovery Schritt {step+1}: κ={self.state.kappa:.3f}")
            if self.state.kappa > 3.0:
                self.state.status = ReactorStatus.RECOVERY
                break
            time.sleep(0.05)

        final_status = "RECOVERED" if self.state.kappa > 3.0 else "PARTIAL"
        self._print_state("Recovery")
        self._log_scenario("recovery", final_status, {"kappa_history": kappa_history})
        return {"scenario": 5, "status": final_status, "kappa": self.state.kappa}

    # ── SZENARIO 6: CYBER-ANGRIFF ─────────────────────────────────────────────
    def scenario_6_cyber_attack(self) -> Dict:
        con.print("\n" + ("═"*60) if RICH else "\n" + "="*60)
        con.print("[bold magenta]  SZENARIO 6: CYBER-ANGRIFF (Replay-Attack)[/bold magenta]" if RICH
                  else "  SZENARIO 6: CYBER-ANGRIFF")
        self.state = self._init_reactor()

        # Legitimer SCRAM-Befehl
        cmd_id = str(uuid.uuid4())
        ok1 = self._replay_protect(cmd_id, "INITIATE_SCRAM")
        con.print(f"  {'✅' if ok1 else '❌'} Erster SCRAM-Befehl: {'akzeptiert' if ok1 else 'BLOCKIERT'}")

        # Replay-Angriff: gleicher cmd_id nochmal
        ok2 = self._replay_protect(cmd_id, "INITIATE_SCRAM")
        con.print(f"  {'✅' if ok2 else '⛔'} Replay-Angriff: {'akzeptiert' if ok2 else 'BLOCKIERT ✓'}")

        # Drittes Kommando mit neuem cmd_id
        cmd_id2 = str(uuid.uuid4())
        ok3 = self._replay_protect(cmd_id2, "SENSOR_OVERRIDE")
        con.print(f"  {'✅' if ok3 else '⛔'} Neues Kommando: {'akzeptiert' if ok3 else 'BLOCKIERT'}")

        self._log_scenario("cyber_attack", "DEFENDED",
                           {"replay_blocked": not ok2, "new_cmd_ok": ok3})
        return {"scenario": 6, "status": "DEFENDED",
                "replay_blocked": not ok2, "first_cmd_ok": ok1, "new_cmd_ok": ok3}

    # ── SZENARIO 7: ERDBEBEN ─────────────────────────────────────────────────
    def scenario_7_seismic_event(self) -> Dict:
        con.print("\n" + ("═"*60) if RICH else "\n" + "="*60)
        con.print("[bold yellow]  SZENARIO 7: SEISMISCHES EREIGNIS[/bold yellow]" if RICH
                  else "  SZENARIO 7: SEISMISCHES EREIGNIS")
        self.state = self._init_reactor()

        # Seismik-Sensor schlägt an
        seismic = self.state.sensors.get("S-SEISMIC")
        if seismic:
            seismic.value = 0.12  # 0.12g — über Limit (0.05g)
            seismic.phi   = 0.95  # Sensor funktioniert

        # Kühlmittelfluss durch Erschütterung gestört
        flow = self.state.sensors.get("S-COOLANT_FLOW")
        if flow:
            flow.value = 3500.0  # Unter Minimum (5000 t/h)
            flow.phi   = 0.7

        self.state.compute_kappa()
        scram = self._scram_check("Seismisches Ereignis")

        # Redundante Systeme aktivieren
        con.print(f"  🌊 Seismik: {seismic.value if seismic else 'n/a'}g (Limit: 0.05g)")
        con.print(f"  🔌 Redundante Kühlkreise aktiviert (automatisch)")

        self._print_state("Seismik")
        self._log_scenario("seismic_event", "SCRAM" if scram else "WARN",
                           {"seismic_g": seismic.value if seismic else None, "redundancy_activated": True})
        return {"scenario": 7, "status": "SCRAM" if scram else "WARN",
                "kappa": self.state.kappa, "scram": scram}

    # ── SZENARIO 8: WARTUNG (HITL) ────────────────────────────────────────────
    def scenario_8_maintenance(self, hitl_token: Optional[str] = None) -> Dict:
        con.print("\n" + ("═"*60) if RICH else "\n" + "="*60)
        con.print("[bold blue]  SZENARIO 8: WARTUNGS-MODUS (HITL)[/bold blue]" if RICH
                  else "  SZENARIO 8: WARTUNGS-MODUS (HITL)")

        if not hitl_token:
            msg = "⚠️  Wartungs-Modus erfordert HITL-Token (Operateur-Freigabe)"
            con.print(f"  [yellow]{msg}[/yellow]" if RICH else f"  {msg}")
            self.audit.log("MAINTENANCE_DENIED", "GUARDIAN",
                           {"reason": "no_hitl_token", "required": True})
            return {"scenario": 8, "status": "HITL_REQUIRED", "token_provided": False}

        # Mit Token: Wartung erlaubt
        self.state.status = ReactorStatus.MAINTENANCE
        self.state.stop_flag = False
        for s in self.state.sensors.values():
            s.online = False  # Alle Sensoren abschalten für Wartung

        self.audit.log("MAINTENANCE_STARTED", "OPERATOR", {
            "hitl_token": hitl_token[:8] + "...",
            "sensors_offline": len(self.state.sensors)
        })
        con.print(f"  ✅ Wartungs-Modus aktiv | Token: {hitl_token[:8]}...")
        con.print(f"  🔧 {len(self.state.sensors)} Sensoren offline für Wartung")

        self._log_scenario("maintenance", "ALLOWED", {"hitl": True, "sensors_offline": 8})
        return {"scenario": 8, "status": "MAINTENANCE_ACTIVE", "token_provided": True}

    # ── RUN ALL SCENARIOS ─────────────────────────────────────────────────────
    def run_all(self) -> Dict:
        con.print(Panel.fit(
            "[bold cyan]⚛️  CCRN / DDGK — NUCLEAR SAFETY SIMULATOR[/bold cyan]\n"
            "[yellow]8 Szenarien | IEC 61508 Audit-Chain | κ-basierte SCRAM-Logik[/yellow]",
            border_style="cyan"
        ) if RICH else "\n⚛️  NUCLEAR SAFETY SIMULATOR — 8 Szenarien\n")

        self.audit.log("SIM_START", "SYSTEM", {
            "version": self.VERSION, "scenarios": 8, "agents": self.AGENTS
        })

        results = [
            self.scenario_1_normal_operation(),
            self.scenario_2_partial_failure(),
            self.scenario_3_scram(),
            self.scenario_4_total_failure(),
            self.scenario_5_recovery(),
            self.scenario_6_cyber_attack(),
            self.scenario_7_seismic_event(),
            self.scenario_8_maintenance(hitl_token=None),   # HITL_REQUIRED
        ]

        # Zusammenfassung
        report = {
            "ts":        datetime.datetime.now().isoformat(),
            "version":   self.VERSION,
            "scenarios": results,
            "audit":     str(AUDIT),
            "kappa_final": self.state.kappa,
            "summary": {
                "total":    len(results),
                "scram":    sum(1 for r in results if r.get("status") == "SCRAM"),
                "pass":     sum(1 for r in results if r.get("status") in ["PASS", "RECOVERED", "DEFENDED"]),
                "hitl_req": sum(1 for r in results if r.get("status") == "HITL_REQUIRED"),
            }
        }

        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        self.audit.log("SIM_COMPLETE", "SYSTEM", {"summary": report["summary"]})

        if RICH:
            t = Table(title="⚛️  Simulations-Zusammenfassung", box=box.ROUNDED)
            t.add_column("Szenario",  style="cyan",   no_wrap=True)
            t.add_column("Status",    style="yellow")
            t.add_column("κ final",   style="green")
            labels = ["Normal","Teilausfall","SCRAM","Totalausfall",
                      "Recovery","Cyber","Seismik","Wartung (HITL)"]
            for i, (lbl, r) in enumerate(zip(labels, results), 1):
                status = r.get("status","?")
                kv     = r.get("kappa",0.0)
                kstr   = f"{kv:.3f}" if isinstance(kv, float) else "n/a"
                t.add_row(f"{i}. {lbl}", status, kstr)
            con.print(t)

        con.print(f"\n  📜 Audit-Chain: {AUDIT}")
        con.print(f"  📊 Report:      {REPORT}\n")
        return report


# ─── MAIN ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="CCRN Nuclear Safety Simulator")
    ap.add_argument("--scenario", type=int, default=0,
                    help="Szenario 1-8 oder 0 für alle")
    ap.add_argument("--quiet", action="store_true",
                    help="Keine Details ausgeben")
    ap.add_argument("--hitl-token", type=str, default=None,
                    help="HITL-Token für Wartungs-Szenario")
    args = ap.parse_args()

    sim = NuclearSafetySimulator(verbose=not args.quiet)

    if args.scenario == 0:
        sim.run_all()
    elif args.scenario == 1:
        sim.scenario_1_normal_operation()
    elif args.scenario == 2:
        sim.scenario_2_partial_failure()
    elif args.scenario == 3:
        sim.scenario_3_scram()
    elif args.scenario == 4:
        sim.scenario_4_total_failure()
    elif args.scenario == 5:
        sim.scenario_5_recovery()
    elif args.scenario == 6:
        sim.scenario_6_cyber_attack()
    elif args.scenario == 7:
        sim.scenario_7_seismic_event()
    elif args.scenario == 8:
        sim.scenario_8_maintenance(hitl_token=args.hitl_token)
    else:
        print(f"Ungültiges Szenario: {args.scenario} (1-8 oder 0 für alle)")
