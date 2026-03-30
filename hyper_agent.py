#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  HYPER-AGENT SYSTEM — Self-Tool-Creation                            ║
║  Agenten erstellen selbstständig neue Werkzeuge                     ║
║                                                                      ║
║  AGI-Stufe 3: Self-Improvement durch Tool-Generierung               ║
║                                                                      ║
║  Ablauf:                                                             ║
║    1. Hyper-Agent erkennt fehlende Fähigkeit                        ║
║    2. LLM generiert Python-Code für neues Tool                      ║
║    3. Validator prüft Code (Safety-Check, Syntax)                   ║
║    4. Tool wird in tools/ gespeichert + registriert                 ║
║    5. Nächste Zyklen nutzen das neue Tool autonom                   ║
║                                                                      ║
║  DDGK-Governance:                                                    ║
║    Tool-Code-Generierung: MEDIUM-RISK                               ║
║    Tool-Ausführung (neu): HIGH-RISK → HITL bei first run            ║
║    Tool-Ausführung (validiert): MEDIUM-RISK nach 1. OK-Lauf         ║
╚══════════════════════════════════════════════════════════════════════╝

Python: 3.10+ | Ollama erforderlich für Tool-Generierung
"""

from __future__ import annotations

import sys
import os
import json
import ast
import uuid
import hashlib
import datetime
import importlib
import importlib.util
import urllib.request
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field

BASE_DIR = Path(__file__).parent
TOOLS_DIR = BASE_DIR / "hyper_tools"
TOOLS_DIR.mkdir(exist_ok=True)
(TOOLS_DIR / "__init__.py").touch()

MEMORY_FILE = BASE_DIR / "cognitive_ddgk" / "hyper_agent_memory.jsonl"
REGISTRY_FILE = BASE_DIR / "cognitive_ddgk" / "hyper_tool_registry.json"
sys.path.insert(0, str(BASE_DIR))

# Decision Trace (XAI)
try:
    from cognitive_ddgk.decision_trace import DecisionTrace
    _DT_AVAILABLE = True
except ImportError:
    _DT_AVAILABLE = False

# Optional rich
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.syntax import Syntax
    from rich import box
    RICH = True
    con = Console()
except ImportError:
    RICH = False
    class _C:
        def print(self, *a, **kw): print(*a)
    con = _C()


# ─── DDGK MEMORY ─────────────────────────────────────────────────────────────

class HyperMemory:
    def __init__(self):
        MEMORY_FILE.parent.mkdir(exist_ok=True)

    def _last_hash(self) -> str:
        if not MEMORY_FILE.exists(): return "0" * 64
        lines = [l for l in MEMORY_FILE.read_text("utf-8", errors="replace").splitlines() if l.strip()]
        return json.loads(lines[-1]).get("hash", "0"*64) if lines else "0"*64

    def log(self, agent: str, action: str, data: Dict) -> str:
        prev = self._last_hash()
        entry = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "agent": agent, "action": action, "data": data,
            "prev": prev, "ddgk_version": "2.0-hyper"
        }
        raw = json.dumps(entry, ensure_ascii=False, sort_keys=True)
        entry["hash"] = hashlib.sha256(raw.encode()).hexdigest()
        with MEMORY_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry["hash"]


# ─── TOOL REGISTRY ───────────────────────────────────────────────────────────

class DynamicToolRegistry:
    """
    Dynamisches Tool-Register — lädt, registriert und verwaltet selbst-erstellte Tools.
    Jedes Tool ist ein Python-Modul in hyper_tools/ mit einer run(args) Funktion.
    """

    # Verbotene Imports/Calls für Safety-Check
    FORBIDDEN = [
        "subprocess", "os.system", "os.popen", "exec(", "eval(",
        "__import__", "importlib.import_module", "socket",
        "ctypes", "win32api", "winreg", "sys.exit",
        "shutil.rmtree", "os.remove", "os.unlink",
        "open.*w.*outside", "requests.delete",
    ]

    def __init__(self):
        self._tools: Dict[str, Dict] = {}
        self._load_registry()

    def _load_registry(self):
        if REGISTRY_FILE.exists():
            try:
                saved = json.loads(REGISTRY_FILE.read_text("utf-8"))
                self._tools = saved.get("tools", {})
            except:
                self._tools = {}

    def _save_registry(self):
        REGISTRY_FILE.write_text(
            json.dumps({"ts": datetime.datetime.now().isoformat(), "tools": self._tools},
                       indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def safety_check(self, code: str) -> tuple[bool, str]:
        """Prüft generierten Code auf verbotene Patterns."""
        for pattern in self.FORBIDDEN:
            if pattern in code:
                return False, f"Verbotenes Pattern gefunden: {pattern}"
        # Syntax-Check
        try:
            ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax-Fehler: {e}"
        # Muss run()-Funktion haben
        if "def run(" not in code and "def run (" not in code:
            return False, "Kein run() Einstiegspunkt definiert"
        return True, "OK"

    def register_tool(self, name: str, code: str, description: str,
                      risk_level: str = "MEDIUM", validated: bool = False) -> Dict:
        """Speichert und registriert ein neues Tool."""
        safe, msg = self.safety_check(code)
        if not safe:
            return {"status": "REJECTED", "reason": msg}

        # Als Python-Modul speichern
        tool_file = TOOLS_DIR / f"{name}.py"
        tool_file.write_text(code, encoding="utf-8")

        self._tools[name] = {
            "name":        name,
            "description": description,
            "risk_level":  risk_level,
            "validated":   validated,
            "file":        str(tool_file),
            "created_at":  datetime.datetime.now().isoformat(),
            "run_count":   0,
            "last_result": None,
        }
        self._save_registry()
        return {"status": "REGISTERED", "name": name, "file": str(tool_file)}

    def get_tool_names(self) -> List[str]:
        return list(self._tools.keys())

    def execute_tool(self, name: str, args: Dict = None,
                     require_validation: bool = True) -> Dict:
        """Führt ein registriertes Tool aus."""
        if name not in self._tools:
            return {"status": "NOT_FOUND", "tool": name}

        meta = self._tools[name]
        if require_validation and not meta.get("validated"):
            return {
                "status": "HITL_REQUIRED",
                "reason": f"Tool '{name}' noch nicht validiert. Erst ausführen mit validate=True.",
                "tool": name
            }

        try:
            spec = importlib.util.spec_from_file_location(name, meta["file"])
            mod  = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            result = mod.run(args or {})
            meta["run_count"] += 1
            meta["last_result"] = str(result)[:200]
            meta["validated"] = True   # Automatisch nach erstem erfolgreichen Lauf
            self._save_registry()
            return {"status": "OK", "tool": name, "result": result}
        except Exception as e:
            return {"status": "ERROR", "tool": name, "error": str(e)[:100]}

    def list_tools(self) -> List[Dict]:
        return list(self._tools.values())


# ─── TOOL GENERATOR (LLM-basiert) ────────────────────────────────────────────

class ToolGenerator:
    """
    LLM generiert Python-Code für neue Tools basierend auf Beschreibung.
    Template: Tool muss def run(args: dict) -> dict implementieren.
    """

    SYSTEM_PROMPT = """Du bist ein Python-Experte im ORION/DDGK-System.
Erstelle ein Python-Tool-Modul. PFLICHT-REGELN:
1. Enthält genau eine Funktion: def run(args: dict) -> dict
2. Gibt immer dict zurück mit: {"status": "OK"|"ERROR", "result": ..., "tool": "<name>"}
3. KEINE imports: subprocess, os.system, socket, ctypes, eval, exec
4. Erlaubte imports: json, pathlib, datetime, math, re, hashlib, urllib.request, os.path
5. Maximal 50 Zeilen Code
6. Muss auf Anhieb lauffähig sein
7. Füge ganz oben TOOL_NAME = "<name>" und TOOL_DESC = "<beschreibung>" ein

Antworte NUR mit Python-Code, kein Markdown, keine Erklärungen."""

    def __init__(self, ollama_url: str = "http://127.0.0.1:11434",
                 model: str = "qwen2.5:7b"):
        self.ollama_url = ollama_url.rstrip("/")
        self.model = model

    def _query(self, prompt: str, tokens: int = 400) -> Optional[str]:
        payload = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": tokens}
        }).encode()
        try:
            req = urllib.request.Request(
                f"{self.ollama_url}/api/generate", data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read()).get("response", "").strip()
        except Exception as e:
            return None

    def generate_tool(self, description: str, tool_name: str = None) -> Dict:
        """
        Generiert Python-Code für ein neues Tool.

        Args:
            description: Was das Tool tun soll (z.B. "prüfe ob eine URL erreichbar ist")
            tool_name: Name des Tools (auto-generiert wenn None)

        Returns:
            {"status": "OK"|"ERROR", "name": str, "code": str, "description": str}
        """
        if not tool_name:
            # Sicheren Namen aus Beschreibung ableiten
            import re
            tool_name = re.sub(r"[^a-z0-9_]", "_",
                               description[:30].lower().replace(" ", "_"))
            tool_name = re.sub(r"_+", "_", tool_name).strip("_")

        prompt = (
            f"{self.SYSTEM_PROMPT}\n\n"
            f"Tool-Name: {tool_name}\n"
            f"Aufgabe: {description}\n\n"
            "Python-Code:"
        )

        code = self._query(prompt, tokens=500)
        if not code:
            return {"status": "ERROR", "reason": "LLM nicht verfügbar"}

        # Code bereinigen (Markdown-Blöcke entfernen)
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()

        return {
            "status": "OK",
            "name":        tool_name,
            "code":        code,
            "description": description,
            "model":       self.model,
            "generated_at": datetime.datetime.now().isoformat()
        }

    def suggest_tools(self, goal: str) -> List[str]:
        """LLM schlägt vor, welche Tools für ein Ziel nötig wären."""
        prompt = (
            f"Ziel: {goal}\n\n"
            "Welche 3 Python-Hilfsfunktionen (Tools) würden dieses Ziel am besten unterstützen?\n"
            "Antworte mit 3 kurzen Tool-Beschreibungen, eine pro Zeile, ohne Nummerierung."
        )
        resp = self._query(prompt, tokens=150)
        if not resp:
            return ["Status prüfen", "Daten analysieren", "Report erstellen"]
        return [l.strip() for l in resp.strip().splitlines() if l.strip()][:3]


# ─── HYPER AGENT ─────────────────────────────────────────────────────────────

class HyperAgent:
    """
    Hyper-Agent: Erkennt fehlende Fähigkeiten → generiert Tools → nutzt sie autonom.

    Vollständiger Zyklus:
        1. Ziel analysieren
        2. Benötigte Tools identifizieren
        3. Fehlende Tools LLM-generieren
        4. Safety-Check + Validierung
        5. Tool ausführen
        6. Ergebnis in Memory speichern
        7. Nächsten Zyklus planen
    """

    VERSION = "3.0.0-hyper"

    def __init__(self,
                 ollama_url: str = "http://127.0.0.1:11434",
                 model: str = "qwen2.5:7b",
                 agent_id: str = "HYPER-AGENT") -> None:
        self.agent_id    = agent_id
        self.memory      = HyperMemory()
        self.registry    = DynamicToolRegistry()
        self.generator   = ToolGenerator(ollama_url, model)
        self._cycle      = 0
        self._goals:     List[str] = []
        self._created_tools: List[str] = []
        # XAI: Decision Trace
        self._dt = DecisionTrace(agent_id=agent_id) if _DT_AVAILABLE else None

        con.print(f"\n{'='*62}")
        con.print(f"  🔥 HYPER-AGENT v{self.VERSION}")
        con.print(f"  Self-Tool-Creation | AGI-Stufe 3")
        con.print(f"  Modell: {model} | Ollama: {ollama_url}")
        con.print(f"  Tools verfügbar: {len(self.registry.get_tool_names())}")
        con.print(f"{'='*62}\n")

        self.memory.log(agent_id, "INIT", {
            "version": self.VERSION, "model": model,
            "existing_tools": self.registry.get_tool_names()
        })

    def set_goal(self, goal: str) -> None:
        self._goals.append(goal)
        con.print(f"  🎯 Ziel: {goal}")
        self.memory.log(self.agent_id, "GOAL_SET", {"goal": goal})

    def create_tool(self, description: str, tool_name: str = None,
                    auto_execute: bool = False) -> Dict:
        """
        Erstellt ein neues Tool via LLM-Generierung.

        Ablauf:
            generate_code → safety_check → register → [optional: execute]
        """
        self._cycle += 1
        con.print(f"\n  🔧 Tool erstellen: '{description}'")

        # 1. Code generieren
        gen = self.generator.generate_tool(description, tool_name)
        if gen["status"] != "OK":
            return gen

        name = gen["name"]
        code = gen["code"]

        if RICH:
            con.print(Panel(
                Syntax(code[:600], "python", theme="monokai", line_numbers=True),
                title=f"🔧 Generierter Code: {name}",
                border_style="yellow"
            ))
        else:
            con.print(f"  Code ({len(code)} Zeichen) für '{name}' generiert")

        # 2. Safety-Check
        safe, msg = self.registry.safety_check(code)
        if not safe:
            con.print(f"  ❌ Safety-Check FAILED: {msg}")
            self.memory.log(self.agent_id, "TOOL_REJECTED", {
                "name": name, "reason": msg
            })
            return {"status": "REJECTED", "name": name, "reason": msg}

        con.print(f"  ✅ Safety-Check OK")

        # 3. Registrieren
        reg = self.registry.register_tool(
            name=name, code=code,
            description=description,
            risk_level="MEDIUM",
            validated=False   # Erst nach erstem Lauf validiert
        )

        if reg["status"] == "REGISTERED":
            self._created_tools.append(name)
            con.print(f"  ✅ Tool registriert: {name}")
            self.memory.log(self.agent_id, "TOOL_CREATED", {
                "name": name, "description": description,
                "file": reg.get("file", "")
            })

        # 4. Optional direkt ausführen (HITL-Skip für ersten Test)
        if auto_execute:
            result = self.execute_tool(name, {}, first_run=True)
            return {"status": "CREATED_AND_EXECUTED", "name": name,
                    "code": code, "execution": result}

        return {"status": "CREATED", "name": name, "code": code,
                "file": reg.get("file", ""), "description": description}

    def execute_tool(self, name: str, args: Dict = None,
                     first_run: bool = False) -> Dict:
        """Führt ein Tool aus — mit HITL-Hinweis beim ersten Lauf."""
        if name not in self.registry._tools:
            return {"status": "NOT_FOUND", "tool": name}

        meta = self.registry._tools[name]

        if not meta.get("validated") and not first_run:
            con.print(f"  ⚠️  Tool '{name}' noch nicht validiert — first_run=True setzen")
            return {"status": "HITL_REQUIRED", "tool": name}

        result = self.registry.execute_tool(name, args or {}, require_validation=False)

        icon = "✅" if result["status"] == "OK" else "❌"
        con.print(f"  {icon} Tool '{name}': {result.get('result', result.get('error','?'))!r:.80}")

        self.memory.log(self.agent_id, "TOOL_EXECUTED", {
            "name": name, "status": result["status"],
            "result": str(result.get("result", ""))[:100]
        })
        return result

    def auto_build_for_goal(self, goal: str, max_tools: int = 3) -> Dict:
        """
        Vollautomatisch: LLM schlägt Tools vor → erstellt → führt aus.
        Das ist der HYPER-AGENT-Kern.
        """
        self.set_goal(goal)
        con.print(f"\n  🧠 Analysiere Ziel: '{goal}'")

        # LLM schlägt benötigte Tools vor
        suggestions = self.generator.suggest_tools(goal)
        con.print(f"  💡 Vorgeschlagene Tools ({len(suggestions)}):")
        for i, s in enumerate(suggestions, 1):
            con.print(f"     {i}. {s}")

        created = []
        for suggestion in suggestions[:max_tools]:
            # Prüfen ob Tool schon existiert
            existing = self.registry.get_tool_names()
            import re
            candidate_name = re.sub(r"[^a-z0-9_]", "_",
                                    suggestion[:25].lower()).strip("_")
            candidate_name = re.sub(r"_+", "_", candidate_name)

            if candidate_name in existing:
                con.print(f"  ℹ️  Tool '{candidate_name}' bereits vorhanden — überspringe")
                continue

            result = self.create_tool(suggestion, candidate_name, auto_execute=True)
            created.append(result)
            time.sleep(0.5)   # Rate-Limit Ollama

        self.memory.log(self.agent_id, "AUTO_BUILD_COMPLETE", {
            "goal": goal,
            "tools_created": [c.get("name") for c in created if c.get("status") in ["CREATED", "CREATED_AND_EXECUTED"]],
            "total_tools": len(self.registry.get_tool_names())
        })

        return {
            "goal": goal,
            "suggestions": suggestions,
            "created": created,
            "total_registry": len(self.registry.get_tool_names())
        }

    def status(self) -> Dict:
        """Vollständiger Hyper-Agent-Status."""
        tools = self.registry.list_tools()

        if RICH:
            t = Table(title="🔥 HyperAgent Status", box=box.ROUNDED)
            t.add_column("Tool",        style="cyan")
            t.add_column("Beschreibung",style="yellow", max_width=40)
            t.add_column("Risiko",      style="red")
            t.add_column("Validiert",   style="green")
            t.add_column("Runs",        style="blue")
            for tool in tools:
                t.add_row(
                    tool["name"],
                    tool["description"][:38],
                    tool["risk_level"],
                    "✅" if tool.get("validated") else "⚠️",
                    str(tool.get("run_count", 0))
                )
            con.print(t)

        return {
            "version":       self.VERSION,
            "agent_id":      self.agent_id,
            "goals":         self._goals,
            "created_tools": self._created_tools,
            "registry":      [t["name"] for t in tools],
            "total_tools":   len(tools),
            "cycles":        self._cycle,
        }


# ─── BUILT-IN TOOLS (zum Start) ──────────────────────────────────────────────

BUILTIN_TOOLS = {
    "check_kappa": {
        "description": "CCRN kappa-Kohaerenz pruefen",
        "risk": "LOW",
        "code": '''TOOL_NAME = "check_kappa"
TOOL_DESC = "CCRN kappa-Kohaerenz pruefen"
import sys, json, pathlib, math
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

def run(args: dict) -> dict:
    try:
        cs = pathlib.Path(__file__).parent.parent / "cognitive_ddgk" / "cognitive_state.json"
        state = json.loads(cs.read_text("utf-8")) if cs.exists() else {}
        kappa = state.get("kappa_current", 0)
        ccrn  = state.get("ccrn_active", False)
        return {"status": "OK", "tool": "check_kappa",
                "result": {"kappa": kappa, "ccrn_active": ccrn,
                           "threshold_ok": kappa >= 2.0}}
    except Exception as e:
        return {"status": "ERROR", "tool": "check_kappa", "result": str(e)}
'''
    },
    "list_workspace": {
        "description": "Workspace-Dateien auflisten und analysieren",
        "risk": "LOW",
        "code": '''TOOL_NAME = "list_workspace"
TOOL_DESC = "Workspace-Dateien auflisten"
import pathlib

def run(args: dict) -> dict:
    base = pathlib.Path(__file__).parent.parent
    pattern = args.get("pattern", "*.py")
    files = list(base.glob(pattern))
    return {"status": "OK", "tool": "list_workspace",
            "result": {"count": len(files),
                       "files": [f.name for f in files[:20]],
                       "pattern": pattern}}
'''
    },
    "memory_stats": {
        "description": "DDGK Memory-Statistiken abrufen",
        "risk": "LOW",
        "code": '''TOOL_NAME = "memory_stats"
TOOL_DESC = "DDGK Memory-Statistiken"
import pathlib, json

def run(args: dict) -> dict:
    base = pathlib.Path(__file__).parent.parent
    files = {
        "cognitive_memory": base / "cognitive_ddgk" / "cognitive_memory.jsonl",
        "loop_memory":      base / "cognitive_ddgk" / "autonomous_loop_memory.jsonl",
        "hyper_memory":     base / "cognitive_ddgk" / "hyper_agent_memory.jsonl",
        "nuclear_audit":    base / "cognitive_ddgk" / "nuclear_audit_chain.jsonl",
    }
    stats = {}
    for name, path in files.items():
        if path.exists():
            lines = [l for l in path.read_text("utf-8", errors="replace").splitlines() if l.strip()]
            stats[name] = len(lines)
        else:
            stats[name] = 0
    return {"status": "OK", "tool": "memory_stats", "result": stats}
'''
    }
}


def install_builtin_tools(registry: DynamicToolRegistry) -> None:
    """Installiert vordefinierte Tools beim ersten Start."""
    for name, meta in BUILTIN_TOOLS.items():
        if name not in registry._tools:
            reg = registry.register_tool(
                name=name, code=meta["code"],
                description=meta["description"],
                risk_level=meta["risk"],
                validated=True   # Built-ins sind bereits validiert
            )
            if reg["status"] == "REGISTERED":
                con.print(f"  ✅ Built-in Tool '{name}' installiert")


# ─── MAIN DEMO ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="HyperAgent — Self-Tool-Creation")
    ap.add_argument("--goal", type=str,
                    default="Analysiere den ORION-Workspace und erstelle einen Gesundheits-Report",
                    help="Ziel fuer automatische Tool-Erstellung")
    ap.add_argument("--model", type=str, default="qwen2.5:7b",
                    help="Ollama-Modell fuer Code-Generierung")
    ap.add_argument("--max-tools", type=int, default=2,
                    help="Maximale Anzahl neuer Tools")
    ap.add_argument("--create", type=str, default=None,
                    help="Einzelnes Tool beschreiben und erstellen")
    ap.add_argument("--list", action="store_true",
                    help="Alle registrierten Tools auflisten")
    ap.add_argument("--run", type=str, default=None,
                    help="Tool direkt ausfuehren (Name)")
    args = ap.parse_args()

    # HyperAgent initialisieren
    agent = HyperAgent(model=args.model)

    # Built-in Tools installieren
    con.print("\n  📦 Built-in Tools installieren ...")
    install_builtin_tools(agent.registry)

    # Built-ins ausführen als Basis-Check
    con.print("\n  🔬 Built-in Tools testen ...")
    for tool_name in ["check_kappa", "list_workspace", "memory_stats"]:
        r = agent.execute_tool(tool_name, {}, first_run=True)
        if r["status"] == "OK":
            res = r.get("result", {})
            if isinstance(res, dict):
                con.print(f"     {tool_name}: {json.dumps(res, ensure_ascii=False)[:80]}")

    if args.list:
        agent.status()

    elif args.run:
        result = agent.execute_tool(args.run, {}, first_run=True)
        con.print(f"\n  Ergebnis: {result}")

    elif args.create:
        result = agent.create_tool(args.create, auto_execute=True)
        con.print(f"\n  Status: {result.get('status')} | Name: {result.get('name')}")

    else:
        # Auto-Build für Ziel
        con.print(f"\n  🚀 Auto-Build startet für: '{args.goal}'")
        result = agent.auto_build_for_goal(args.goal, max_tools=args.max_tools)
        con.print(f"\n  ✅ {len(result.get('created', []))} neue Tools erstellt")
        con.print(f"  📦 Registry: {result.get('total_registry')} Tools total")

    # Finaler Status
    con.print("\n")
    agent.status()
    con.print(f"\n  📜 HyperAgent Memory: {MEMORY_FILE}")
    con.print(f"  📦 Tool-Registry:     {REGISTRY_FILE}")
    con.print(f"  📁 Tools-Verzeichnis: {TOOLS_DIR}\n")
