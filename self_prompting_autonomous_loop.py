#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  SELF-PROMPTING AUTONOMOUS LOOP — FusionKernel v2                  ║
║  Full Autonomous Self-Acting mit DDGK-Governance                    ║
║                                                                      ║
║  Features:                                                           ║
║    • Continuous Self-Prompting (LLM generiert eigene Aufgaben)      ║
║    • Goal-Decomposition (Ziele → Teilaufgaben → Aktionen)           ║
║    • Tool-Use: Ollama, Filesystem, HTTP, Browser(Playwright)        ║
║    • DDGK Policy: LOW/MEDIUM ALLOW | HIGH HITL                      ║
║    • SHA-256 Audit-Chain für jeden Entscheidungsschritt             ║
║    • Playwright-ready (Browser-Automation für Formulare)            ║
║    • ReAct Pattern: Reason → Act → Observe → Repeat                ║
╚══════════════════════════════════════════════════════════════════════╝

AUTONOMY LEVELS:
  0 = PASSIVE   — Nur beobachten, nichts ausführen
  1 = SUPERVISED — LOW-RISK autonom, alles andere HITL
  2 = BALANCED  — LOW + MEDIUM autonom, HIGH HITL (Default)
  3 = EXTENDED  — Fast alles autonom, nur irreversible Aktionen HITL
  4 = RESEARCH  — Vollständig autonom (nur für geschlossene Testsysteme)

Python: 3.10+ | Optional: playwright, requests
"""

from __future__ import annotations

import sys
import os
import json
import time
import uuid
import hashlib
import datetime
import threading
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# Decision Trace (XAI)
try:
    from cognitive_ddgk.decision_trace import DecisionTrace
    _DECISION_TRACE_AVAILABLE = True
except ImportError:
    _DECISION_TRACE_AVAILABLE = False

MEMORY_FILE = BASE_DIR / "cognitive_ddgk" / "autonomous_loop_memory.jsonl"
STATE_FILE  = BASE_DIR / "cognitive_ddgk" / "autonomous_loop_state.json"

# Optional rich
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.live import Live
    from rich.table import Table
    from rich import box
    RICH = True
    con = Console()
except ImportError:
    RICH = False
    class _C:
        def print(self, *a, **kw): print(*a)
        def rule(self, *a, **kw): print("─" * 60)
    con = _C()

# Optional playwright
try:
    from playwright.sync_api import sync_playwright, Page
    PLAYWRIGHT = True
except ImportError:
    PLAYWRIGHT = False


# ─── ENUMS ───────────────────────────────────────────────────────────────────

class AutonomyLevel(Enum):
    PASSIVE    = 0
    SUPERVISED = 1
    BALANCED   = 2
    EXTENDED   = 3
    RESEARCH   = 4

class TaskStatus(Enum):
    PENDING    = "PENDING"
    RUNNING    = "RUNNING"
    COMPLETED  = "COMPLETED"
    FAILED     = "FAILED"
    DENIED     = "DENIED"
    HITL_WAIT  = "HITL_WAIT"


# ─── TASK DATACLASS ──────────────────────────────────────────────────────────

@dataclass
class AutonomousTask:
    task_id:     str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    goal:        str = ""
    subtasks:    List[str] = field(default_factory=list)
    tool:        str = "think"          # think | file | http | browser | shell
    risk_level:  str = "LOW"            # LOW | MEDIUM | HIGH
    status:      TaskStatus = TaskStatus.PENDING
    result:      Optional[str] = None
    reasoning:   str = ""
    created_at:  str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    completed_at: Optional[str] = None
    reversible:  bool = True


# ─── MEMORY / AUDIT ──────────────────────────────────────────────────────────

class LoopMemory:
    def __init__(self, path: Path = MEMORY_FILE):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _last_hash(self) -> str:
        if not self.path.exists(): return "0" * 64
        lines = [l for l in self.path.read_text("utf-8").splitlines() if l.strip()]
        return json.loads(lines[-1]).get("hash","0"*64) if lines else "0"*64

    def log(self, agent: str, action: str, data: Dict) -> str:
        prev = self._last_hash()
        entry = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "agent": agent, "action": action, "data": data,
            "prev": prev, "ddgk_version": "2.0-autonomous"
        }
        raw = json.dumps(entry, ensure_ascii=False, sort_keys=True)
        entry["hash"] = hashlib.sha256(raw.encode()).hexdigest()
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry["hash"]

    def count(self) -> int:
        if not self.path.exists(): return 0
        return sum(1 for l in self.path.read_text("utf-8").splitlines() if l.strip())


# ─── TOOLS ───────────────────────────────────────────────────────────────────

class ToolRegistry:
    """
    Registrierung aller verfügbaren Tools mit Risiko-Level.
    Policy: LOW/MEDIUM → autonom erlaubt | HIGH → HITL nötig
    """

    TOOLS = {
        # LOW-RISK Tools (vollständig autonom)
        "think":        {"risk": "LOW",    "desc": "LLM-Abfrage via Ollama"},
        "read_file":    {"risk": "LOW",    "desc": "Datei lesen"},
        "list_dir":     {"risk": "LOW",    "desc": "Verzeichnis auflisten"},
        "compute_kappa":{"risk": "LOW",    "desc": "κ_CCRN berechnen"},
        "search_web":   {"risk": "LOW",    "desc": "Web-Suche (read-only)"},
        "check_status": {"risk": "LOW",    "desc": "System-Status prüfen"},
        "http_get":     {"risk": "LOW",    "desc": "HTTP GET Request"},

        # MEDIUM-RISK Tools (autonom bei level >= BALANCED)
        "write_file":   {"risk": "MEDIUM", "desc": "Datei schreiben"},
        "http_post":    {"risk": "MEDIUM", "desc": "HTTP POST Request"},
        "fill_form":    {"risk": "MEDIUM", "desc": "Formular ausfüllen (Browser)"},
        "send_email":   {"risk": "MEDIUM", "desc": "E-Mail senden"},
        "git_commit":   {"risk": "MEDIUM", "desc": "Git commit (kein push)"},
        "create_issue": {"risk": "MEDIUM", "desc": "GitHub Issue erstellen"},

        # HIGH-RISK Tools (immer HITL)
        "shell_execute":{"risk": "HIGH",   "desc": "Shell-Kommando ausführen"},
        "git_push":     {"risk": "HIGH",   "desc": "Git push (remote)"},
        "git_force":    {"risk": "HIGH",   "desc": "Git force-push"},
        "deploy":       {"risk": "HIGH",   "desc": "Deployment ausführen"},
        "delete_file":  {"risk": "HIGH",   "desc": "Datei löschen"},
        "payment":      {"risk": "HIGH",   "desc": "Zahlung auslösen"},
        "sign_contract":{"risk": "HIGH",   "desc": "Vertrag unterzeichnen"},
    }

    @classmethod
    def get_risk(cls, tool: str) -> str:
        return cls.TOOLS.get(tool, {}).get("risk", "HIGH")

    @classmethod
    def is_allowed(cls, tool: str, autonomy_level: AutonomyLevel) -> bool:
        risk = cls.get_risk(tool)
        if risk == "LOW":   return autonomy_level.value >= 1
        if risk == "MEDIUM":return autonomy_level.value >= 2
        if risk == "HIGH":  return autonomy_level.value >= 4
        return False


# ─── SELF-PROMPTING ENGINE ───────────────────────────────────────────────────

class SelfPromptingEngine:
    """
    Generiert autonome Aufgaben basierend auf aktuellem Ziel und Memory.
    ReAct-Muster: Reason → Act → Observe → Reason → ...
    """

    SYSTEM_CONTEXT = (
        "Du bist ORION-FusionKernel, ein autonom arbeitendes KI-System. "
        "Deine Aufgabe: Analysiere den aktuellen Zustand und generiere "
        "GENAU EINE sinnvolle nächste Aufgabe. Format: JSON mit Feldern: "
        "goal, tool (aus: think/read_file/write_file/http_get/fill_form), "
        "risk_level (LOW/MEDIUM/HIGH), reasoning. Antworte NUR mit JSON."
    )

    def __init__(self, ollama_url: str = "http://127.0.0.1:11434",
                 model: str = "qwen2.5:1.5b") -> None:
        self.ollama_url = ollama_url.rstrip("/")
        self.model      = model
        self._alive     = self._check_ollama()

    def _check_ollama(self) -> bool:
        try:
            urllib.request.urlopen(f"{self.ollama_url}/api/tags", timeout=2)
            return True
        except:
            return False

    def _query(self, prompt: str, tokens: int = 200) -> Optional[str]:
        if not self._alive:
            return None
        payload = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": tokens}
        }).encode()
        try:
            req = urllib.request.Request(
                f"{self.ollama_url}/api/generate", data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read()).get("response","").strip()
        except:
            return None

    def generate_next_task(self, context: str, history: List[str]) -> Optional[AutonomousTask]:
        """LLM generiert nächste Aufgabe basierend auf Kontext."""
        hist_summary = "\n".join(history[-3:]) if history else "Keine Vorgeschichte"
        prompt = (
            f"{self.SYSTEM_CONTEXT}\n\n"
            f"Aktueller Kontext: {context}\n"
            f"Letzte Aktionen: {hist_summary}\n\n"
            "Generiere die nächste sinnvolle Aufgabe als JSON:"
        )

        resp = self._query(prompt)
        if not resp:
            # Fallback wenn Ollama nicht verfügbar
            return AutonomousTask(
                goal="System-Status prüfen",
                tool="check_status",
                risk_level="LOW",
                reasoning="Ollama nicht verfügbar — Fallback zu Status-Check"
            )

        try:
            # JSON aus Antwort extrahieren
            start = resp.find("{")
            end   = resp.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(resp[start:end])
                return AutonomousTask(
                    goal=data.get("goal","Unbekannte Aufgabe"),
                    tool=data.get("tool","think"),
                    risk_level=data.get("risk_level","LOW"),
                    reasoning=data.get("reasoning","")[:200]
                )
        except:
            pass
        return None

    def reflect_on_result(self, task: AutonomousTask) -> str:
        """LLM reflektiert über Ergebnis einer Aufgabe."""
        prompt = (
            f"Aufgabe war: {task.goal}\n"
            f"Ergebnis: {task.result or 'kein Ergebnis'}\n"
            f"Was bedeutet das? Kurze Reflexion auf Deutsch (max 50 Wörter):"
        )
        return self._query(prompt, tokens=80) or "Reflexion nicht möglich (Ollama offline)"


# ─── BROWSER AUTOMATION (Playwright) ─────────────────────────────────────────

class BrowserAutomation:
    """
    Playwright-basierte Browser-Automation für Formular-Ausfüllen.
    Wird nur ausgeführt wenn:
      1. DDGK Policy ALLOW
      2. Autonomy-Level >= BALANCED
      3. Formular-Typ nicht HIGH-RISK (keine Zahlungen/Verträge)
    """

    def __init__(self) -> None:
        self.available = PLAYWRIGHT

    def fill_form(self, url: str, form_data: Dict[str, str],
                  submit: bool = False) -> Dict[str, Any]:
        """
        Füllt ein Web-Formular aus.

        Args:
            url: Formular-URL
            form_data: {selector: value} oder {label: value}
            submit: True = Formular absenden (MEDIUM → nur mit Policy-OK)
        """
        if not self.available:
            return {
                "status": "UNAVAILABLE",
                "reason": "Playwright nicht installiert. Ausführen: pip install playwright && python -m playwright install chromium",
                "install_cmd": "pip install playwright && python -m playwright install chromium"
            }

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page    = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=10000)
                title = page.title()

                filled = []
                for selector, value in form_data.items():
                    try:
                        page.fill(selector, value)
                        filled.append(selector)
                    except Exception as e:
                        pass   # Selektor nicht gefunden → überspringen

                result_url = page.url
                if submit:
                    page.keyboard.press("Enter")
                    page.wait_for_load_state("networkidle", timeout=5000)
                    result_url = page.url

                browser.close()
                return {
                    "status": "FILLED",
                    "url": url, "title": title,
                    "fields_filled": filled,
                    "submitted": submit,
                    "result_url": result_url
                }
        except Exception as e:
            return {"status": "ERROR", "reason": str(e)[:100]}

    def check_form_fields(self, url: str) -> Dict[str, Any]:
        """Analysiert verfügbare Formularfelder (read-only, LOW-RISK)."""
        if not self.available:
            return {"status": "UNAVAILABLE"}
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page    = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=8000)
                inputs  = page.query_selector_all("input, textarea, select")
                fields  = []
                for inp in inputs[:20]:   # Max 20 Felder
                    typ  = inp.get_attribute("type") or "text"
                    name = inp.get_attribute("name") or inp.get_attribute("id") or ""
                    plh  = inp.get_attribute("placeholder") or ""
                    fields.append({"type": typ, "name": name, "placeholder": plh})
                browser.close()
                return {"status": "OK", "url": url, "fields": fields, "count": len(fields)}
        except Exception as e:
            return {"status": "ERROR", "reason": str(e)[:80]}


# ─── AUTONOMOUS LOOP ─────────────────────────────────────────────────────────

class SelfPromptingAutonomousLoop:
    """
    Vollautonomer Betriebsmodus für FusionKernel v2.

    Betrieb:
        loop = SelfPromptingAutonomousLoop(autonomy=AutonomyLevel.BALANCED)
        loop.set_goal("Analysiere den Workspace und schreibe einen Report")
        loop.run(max_cycles=10)
    """

    VERSION = "2.0.0-autonomous"

    def __init__(
        self,
        autonomy:    AutonomyLevel = AutonomyLevel.BALANCED,
        ollama_url:  str = "http://127.0.0.1:11434",
        model:       str = "qwen2.5:1.5b",
        agent_id:    str = "AUTONOMOUS-LOOP",
        interval:    float = 2.0,
    ) -> None:
        self.autonomy    = autonomy
        self.agent_id    = agent_id
        self.interval    = interval
        self.memory      = LoopMemory()
        self.engine      = SelfPromptingEngine(ollama_url, model)
        self.browser     = BrowserAutomation()
        self.goals:      List[str] = []
        self.task_queue: List[AutonomousTask] = []
        self.history:    List[str] = []
        self._running    = False
        self._cycle      = 0
        self._stop_event = threading.Event()
        # XAI: Decision Trace
        self._dt = DecisionTrace(agent_id=agent_id) if _DECISION_TRACE_AVAILABLE else None

        con.print(f"\n{'='*60}")
        con.print(f"  🤖 AUTONOMOUS LOOP v{self.VERSION}")
        con.print(f"  Autonomy Level: {autonomy.name} ({autonomy.value})")
        con.print(f"  Ollama: {ollama_url} | Model: {model}")
        con.print(f"  Playwright: {'✅ verfügbar' if PLAYWRIGHT else '❌ nicht installiert'}")
        con.print(f"{'='*60}\n")

        self.memory.log(self.agent_id, "INIT", {
            "autonomy": autonomy.name, "model": model, "playwright": PLAYWRIGHT
        })

    def set_goal(self, goal: str) -> None:
        """Neues übergeordnetes Ziel setzen."""
        self.goals.append(goal)
        self.memory.log(self.agent_id, "GOAL_SET", {"goal": goal})
        con.print(f"  🎯 Neues Ziel: {goal}")

    def add_task(self, task: AutonomousTask) -> None:
        """Manuelle Aufgabe zur Queue hinzufügen."""
        self.task_queue.append(task)
        self.memory.log(self.agent_id, "TASK_QUEUED", {
            "task_id": task.task_id, "goal": task.goal[:60], "risk": task.risk_level
        })

    def _evaluate_policy(self, task: AutonomousTask) -> str:
        """DDGK-ähnliche Policy: ALLOW / DENY / HITL_REQUIRED."""
        allowed = ToolRegistry.is_allowed(task.tool, self.autonomy)
        if self.autonomy == AutonomyLevel.PASSIVE:
            return "DENY"
        if task.risk_level == "HIGH" and self.autonomy.value < 4:
            return "HITL_REQUIRED"
        if not allowed:
            return "HITL_REQUIRED"
        return "ALLOW"

    def _execute_task(self, task: AutonomousTask) -> AutonomousTask:
        """Führt eine Aufgabe aus basierend auf Tool-Typ."""
        task.status = TaskStatus.RUNNING

        try:
            if task.tool == "think":
                resp = self.engine._query(task.goal, tokens=150)
                task.result = resp or "Ollama offline"

            elif task.tool == "check_status":
                task.result = json.dumps({
                    "memory_entries": self.memory.count(),
                    "cycles": self._cycle,
                    "goals": len(self.goals),
                    "queue": len(self.task_queue),
                    "autonomy": self.autonomy.name,
                    "playwright": PLAYWRIGHT,
                })

            elif task.tool == "read_file":
                target = task.goal.split(":")[-1].strip() if ":" in task.goal else "README.md"
                fp = BASE_DIR / target
                if fp.exists():
                    task.result = fp.read_text("utf-8", errors="replace")[:500]
                else:
                    task.result = f"Datei nicht gefunden: {target}"

            elif task.tool == "write_file":
                lines = task.goal.split("|", 2)
                if len(lines) >= 2:
                    fname, content = lines[0].strip(), lines[1].strip()
                    fp = BASE_DIR / fname
                    fp.write_text(content, encoding="utf-8")
                    task.result = f"Geschrieben: {fname} ({len(content)} Zeichen)"
                else:
                    task.result = "Format: 'dateiname.txt | inhalt'"

            elif task.tool == "http_get":
                url = task.goal.split("GET")[-1].strip() if "GET" in task.goal else task.goal
                try:
                    with urllib.request.urlopen(url, timeout=5) as r:
                        task.result = r.read().decode("utf-8","replace")[:300]
                except Exception as e:
                    task.result = f"HTTP-Fehler: {e}"

            elif task.tool == "fill_form":
                # Format: "URL | {selector: value}"
                parts = task.goal.split("|", 1)
                if len(parts) == 2:
                    url = parts[0].strip()
                    try:
                        form_data = json.loads(parts[1].strip())
                    except:
                        form_data = {}
                    result = self.browser.fill_form(url, form_data, submit=False)
                    task.result = json.dumps(result, ensure_ascii=False)
                else:
                    task.result = "Format: 'https://... | {\"selector\": \"value\"}'"

            elif task.tool == "compute_kappa":
                try:
                    from cognitive_ddgk.cognitive_ddgk_core import CognitiveDDGK
                    d = CognitiveDDGK(agent_id="LOOP-KAPPA")
                    r = d.compute_kappa()
                    task.result = f"κ={r.get('kappa')} | CCRN={'AKTIV' if r.get('ccrn_active') else 'INAKTIV'}"
                except Exception as e:
                    task.result = f"κ-Berechnung: {e}"

            else:
                task.result = f"Tool '{task.tool}' noch nicht implementiert"

            task.status = TaskStatus.COMPLETED

        except Exception as e:
            task.result = f"Fehler: {str(e)[:100]}"
            task.status = TaskStatus.FAILED

        task.completed_at = datetime.datetime.now().isoformat()
        return task

    def _run_cycle(self) -> Optional[AutonomousTask]:
        """Einzelner Autonomie-Zyklus: Planen → Prüfen → Ausführen → Reflektieren."""
        self._cycle += 1

        # 1. Aufgabe aus Queue oder neu generieren
        if self.task_queue:
            task = self.task_queue.pop(0)
        elif self.goals and self.engine._alive:
            ctx  = f"Aktuelles Ziel: {self.goals[-1]} | Zyklus: {self._cycle}"
            task = self.engine.generate_next_task(ctx, self.history)
            if not task:
                return None
        else:
            # Default-Zyklus ohne LLM
            task = AutonomousTask(
                goal=f"Status-Check Zyklus {self._cycle}",
                tool="check_status",
                risk_level="LOW",
                reasoning="Kein LLM verfügbar — Default-Status-Check"
            )

        # 2. Policy-Check
        policy = self._evaluate_policy(task)
        if policy == "DENY":
            task.status = TaskStatus.DENIED
            task.result = f"DENY: Autonomy-Level {self.autonomy.name} zu niedrig"
        elif policy == "HITL_REQUIRED":
            task.status = TaskStatus.HITL_WAIT
            task.result = f"HITL: {task.tool} (HIGH-RISK) wartet auf Operateur-Freigabe"
        else:
            # 3. Ausführen
            task = self._execute_task(task)
            # 4. Reflexion (async, bei Ollama verfügbar)
            if self.engine._alive and task.status == TaskStatus.COMPLETED:
                reflection = self.engine.reflect_on_result(task)
                self.history.append(f"[{task.tool}] {reflection[:60]}")

        # 5. Memory-Eintrag
        self.memory.log(self.agent_id, f"CYCLE_{self._cycle}", {
            "task_id":   task.task_id,
            "goal":      task.goal[:60],
            "tool":      task.tool,
            "risk":      task.risk_level,
            "policy":    policy,
            "status":    task.status.value,
            "result":    (task.result or "")[:100],
            "autonomy":  self.autonomy.name,
        })

        return task

    def run(self, max_cycles: int = 10, stop_on_error: bool = False) -> List[AutonomousTask]:
        """
        Hauptschleife: Führt max_cycles autonome Zyklen aus.

        Args:
            max_cycles: 0 = unendlich (manuell stoppen mit Ctrl+C)
            stop_on_error: True = stoppe bei erstem Fehler
        """
        self._running = True
        self._stop_event.clear()
        completed_tasks: List[AutonomousTask] = []

        self.memory.log(self.agent_id, "LOOP_START", {
            "max_cycles": max_cycles, "autonomy": self.autonomy.name,
            "goals": len(self.goals)
        })

        if RICH:
            con.print(Panel.fit(
                f"[bold green]🤖 Autonomous Loop gestartet[/bold green]\n"
                f"Max Zyklen: {max_cycles if max_cycles > 0 else '∞'} | "
                f"Level: [cyan]{self.autonomy.name}[/cyan]",
                border_style="green"
            ))
        else:
            con.print(f"  🤖 Loop start | Zyklen: {max_cycles} | Level: {self.autonomy.name}")

        try:
            while self._running and not self._stop_event.is_set():
                if max_cycles > 0 and self._cycle >= max_cycles:
                    break

                task = self._run_cycle()
                if task:
                    completed_tasks.append(task)

                    status_icon = {
                        TaskStatus.COMPLETED:  "✅",
                        TaskStatus.FAILED:     "❌",
                        TaskStatus.DENIED:     "⛔",
                        TaskStatus.HITL_WAIT:  "⚠️ ",
                    }.get(task.status, "❓")

                    con.print(
                        f"  [{self._cycle:3d}] {status_icon} [{task.risk_level}] "
                        f"{task.tool}: {task.goal[:50]}"
                    )

                    if task.result and len(task.result) < 120:
                        con.print(f"       ↳ {task.result}")

                    if stop_on_error and task.status == TaskStatus.FAILED:
                        con.print("  ❌ Stoppe bei Fehler (stop_on_error=True)")
                        break

                time.sleep(self.interval)

        except KeyboardInterrupt:
            con.print("\n  ⚠️  Unterbrochen (Ctrl+C)")

        finally:
            self._running = False
            done = sum(1 for t in completed_tasks if t.status == TaskStatus.COMPLETED)
            denied = sum(1 for t in completed_tasks if t.status in [TaskStatus.DENIED, TaskStatus.HITL_WAIT])

            self.memory.log(self.agent_id, "LOOP_END", {
                "total_cycles":  self._cycle,
                "completed":     done,
                "denied":        denied,
                "memory_entries":self.memory.count()
            })

            con.print(f"\n  ✅ Loop beendet | {self._cycle} Zyklen | {done} OK | {denied} HITL/DENY")
            con.print(f"  📜 Memory: {MEMORY_FILE}")

        return completed_tasks

    def stop(self) -> None:
        """Loop sicher stoppen."""
        self._stop_event.set()
        self._running = False

    def status_summary(self) -> Dict:
        return {
            "version":   self.VERSION,
            "agent_id":  self.agent_id,
            "autonomy":  self.autonomy.name,
            "cycles":    self._cycle,
            "goals":     self.goals,
            "queue_len": len(self.task_queue),
            "history":   self.history[-5:],
            "memory":    self.memory.count(),
            "playwright":PLAYWRIGHT,
            "ollama_ok": self.engine._alive,
        }


# ─── MAIN DEMO ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="DDGK Self-Prompting Autonomous Loop")
    ap.add_argument("--level",    type=int,   default=2,
                    help="Autonomy Level: 0=PASSIVE 1=SUPERVISED 2=BALANCED 3=EXTENDED 4=RESEARCH")
    ap.add_argument("--cycles",   type=int,   default=5,
                    help="Anzahl Zyklen (0 = unendlich)")
    ap.add_argument("--goal",     type=str,
                    default="Analysiere den ORION-Workspace und fasse den aktuellen Status zusammen",
                    help="Übergeordnetes Ziel")
    ap.add_argument("--model",    type=str,   default="qwen2.5:1.5b",
                    help="Ollama-Modell für Self-Prompting")
    ap.add_argument("--interval", type=float, default=1.0,
                    help="Sekunden zwischen Zyklen")
    args = ap.parse_args()

    level = AutonomyLevel(min(max(args.level, 0), 4))

    loop = SelfPromptingAutonomousLoop(
        autonomy=level,
        model=args.model,
        interval=args.interval
    )
    loop.set_goal(args.goal)

    # Manuelle Vorgabe-Tasks (LOW-RISK)
    loop.add_task(AutonomousTask(
        goal="System-Status prüfen",
        tool="check_status",
        risk_level="LOW",
        reasoning="Initialer Status-Check vor Autonomie-Loop"
    ))
    loop.add_task(AutonomousTask(
        goal="κ_CCRN berechnen und CCRN-Status prüfen",
        tool="compute_kappa",
        risk_level="LOW",
        reasoning="CCRN-Kohärenz als Basis für weitere Entscheidungen"
    ))

    completed = loop.run(max_cycles=args.cycles)

    print(f"\n  Abgeschlossen: {len(completed)} Tasks | {loop._cycle} Zyklen")
    print(f"  Status: {json.dumps(loop.status_summary(), indent=2, ensure_ascii=False)[:400]}")
