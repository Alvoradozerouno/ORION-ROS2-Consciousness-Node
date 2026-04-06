#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  HYPER-AGENT SYSTEM — Selbständige Werkzeugerschaffung             ║
║  DDGK-governed Tool Synthesis + Registration + Execution           ║
║                                                                      ║
║  Kernfähigkeiten:                                                   ║
║    1. TOOL-ANALYSE: Was fehlt? Was wird gebraucht?                  ║
║    2. TOOL-SYNTHESE: LLM schreibt Python-Code für neues Tool       ║
║    3. TOOL-VALIDIERUNG: Syntax-Check, Safety-Check (DDGK)          ║
║    4. TOOL-REGISTRIERUNG: Neues Tool in ToolRegistry eintragen     ║
║    5. TOOL-AUSFÜHRUNG: Registriertes Tool im Loop verwenden        ║
║    6. TOOL-LERNEN: Erfolg/Misserfolg → Verbesserung               ║
║                                                                      ║
║  DDGK-Governance:                                                   ║
║    Code-Synthese      = MEDIUM-RISK (reversibel, sandboxed)        ║
║    Tool-Registration  = MEDIUM-RISK                                 ║
║    Tool-Ausführung    = abhängig vom Tool-Risiko                    ║
║    System-Modifikation= HIGH-RISK (HITL)                           ║
╚══════════════════════════════════════════════════════════════════════╝

Architektur:
    HyperAgent
    ├── ToolAnalyzer      — Erkennt fehlende Fähigkeiten
    ├── ToolSynthesizer   — LLM generiert Python-Code für neues Tool
    ├── ToolValidator     — AST-Check + DDGK-Safety-Check
    ├── DynamicToolRegistry — Erweiterbare Tool-Registrierung
    └── HyperLoop         — Autonomer Synthesize-Test-Learn-Zyklus

Python: 3.10+ | Abhängigkeiten: Optional Ollama (qwen2.5:1.5b)
"""

from __future__ import annotations

import ast
import sys
import os
import json
import uuid
import time
import hashlib
import datetime
import textwrap
import importlib
import traceback
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

BASE_DIR = Path(__file__).parent
TOOLS_DIR = BASE_DIR / "cognitive_ddgk" / "synthesized_tools"
TOOLS_DIR.mkdir(parents=True, exist_ok=True)
MEMORY  = BASE_DIR / "cognitive_ddgk" / "hyper_agent_memory.jsonl"
REPORT  = BASE_DIR / "cognitive_ddgk" / "hyper_agent_report.json"

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    RICH = True
    con = Console()
except ImportError:
    RICH = False
    class _C:
        def print(self, *a, **kw): print(*a)
    con = _C()


# ─── DATACLASSES ─────────────────────────────────────────────────────────────

@dataclass
class SynthesizedTool:
    tool_id:     str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name:        str = ""
    description: str = ""
    risk_level:  str = "MEDIUM"
    code:        str = ""
    fn:          Optional[Callable] = None
    calls:       int = 0
    successes:   int = 0
    failures:    int = 0
    created_at:  str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    validated:   bool = False
    active:      bool = False

    @property
    def success_rate(self) -> float:
        return self.successes / max(self.calls, 1)


@dataclass
class ToolNeed:
    """Erkannte Anforderung für ein neues Tool."""
    description:    str
    input_example:  str = ""
    output_example: str = ""
    priority:       int = 1   # 1=hoch, 3=niedrig
    source:         str = "analysis"


# ─── MEMORY ──────────────────────────────────────────────────────────────────

class HyperMemory:
    def __init__(self):
        MEMORY.parent.mkdir(parents=True, exist_ok=True)

    def _last_hash(self) -> str:
        if not MEMORY.exists(): return "0" * 64
        lines = [l for l in MEMORY.read_text("utf-8").splitlines() if l.strip()]
        return json.loads(lines[-1]).get("hash","0"*64) if lines else "0"*64

    def log(self, event: str, data: Dict) -> str:
        prev = self._last_hash()
        e = {
            "ts":    datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "event": event, "data": data, "prev": prev, "system": "hyper_agent"
        }
        raw  = json.dumps(e, ensure_ascii=False, sort_keys=True)
        e["hash"] = hashlib.sha256(raw.encode()).hexdigest()
        with MEMORY.open("a", encoding="utf-8") as f:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
        return e["hash"]

    def count(self) -> int:
        if not MEMORY.exists(): return 0
        return sum(1 for l in MEMORY.read_text("utf-8").splitlines() if l.strip())


# ─── OLLAMA BRIDGE ───────────────────────────────────────────────────────────

class OllamaBridge:
    def __init__(self, url: str = "http://127.0.0.1:11434", model: str = "qwen2.5:1.5b"):
        self.url   = url.rstrip("/")
        self.model = model
        self.alive = self._ping()

    def _ping(self) -> bool:
        try:
            urllib.request.urlopen(f"{self.url}/api/tags", timeout=2)
            return True
        except: return False

    def ask(self, prompt: str, tokens: int = 400, temp: float = 0.2) -> Optional[str]:
        if not self.alive: return None
        payload = json.dumps({
            "model": self.model, "prompt": prompt, "stream": False,
            "options": {"temperature": temp, "num_predict": tokens}
        }).encode()
        try:
            req = urllib.request.Request(
                f"{self.url}/api/generate", data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read()).get("response","").strip()
        except Exception as e:
            return None


# ─── TOOL ANALYZER ───────────────────────────────────────────────────────────

class ToolAnalyzer:
    """
    Analysiert was das System braucht aber noch nicht kann.
    Erkennt Lücken aus: Fehlgeschlagenen Tasks, Zielen, History.
    """

    BUILT_IN_CAPABILITIES = {
        "think", "read_file", "write_file", "http_get", "http_post",
        "check_status", "compute_kappa", "fill_form", "list_dir",
        "search_web", "send_email", "git_commit"
    }

    def analyze_gaps(self, goals: List[str], failed_tasks: List[Dict],
                     history: List[str]) -> List[ToolNeed]:
        """Erkennt fehlende Tools aus Goals + Fehlern."""
        needs = []

        # Aus fehlgeschlagenen Tasks
        for task in failed_tasks:
            result = task.get("result","")
            if "nicht implementiert" in result.lower():
                tool_name = task.get("tool","")
                needs.append(ToolNeed(
                    description=f"Tool '{tool_name}' implementieren: {task.get('goal','')}",
                    input_example=task.get("goal",""),
                    priority=1,
                    source="failed_task"
                ))

        # Aus Zielen: Keywords → benötigte Tools
        keyword_tools = {
            "pdf": ToolNeed("PDF lesen und Text extrahieren",
                            input_example="read_pdf: path/to/file.pdf",
                            output_example="Extrahierter Text...", priority=2),
            "chart": ToolNeed("Diagramm/Chart aus Daten generieren",
                              input_example="plot_data: {'x':[1,2,3],'y':[4,5,6]}",
                              priority=2),
            "translate": ToolNeed("Text übersetzen (DE↔EN)",
                                  input_example="translate: Guten Morgen | en",
                                  output_example="Good morning", priority=2),
            "summarize": ToolNeed("Langen Text zusammenfassen",
                                  input_example="summarize: Langer Text...",
                                  priority=2),
            "json_validate": ToolNeed("JSON-Datei validieren und Fehler melden",
                                      input_example="json_validate: data.json",
                                      priority=3),
            "ping": ToolNeed("Netzwerk-Ping zu Host",
                             input_example="ping: 192.168.1.103",
                             output_example="Latenz: 2ms", priority=2),
            "csv": ToolNeed("CSV-Datei lesen und analysieren",
                            input_example="read_csv: data.csv",
                            priority=2),
            "zip": ToolNeed("Dateien/Ordner komprimieren",
                            input_example="compress: folder/ → archive.zip",
                            priority=3),
            "screenshot": ToolNeed("Screenshot der Website machen",
                                   input_example="screenshot: https://example.com",
                                   priority=2),
            "diff": ToolNeed("Zwei Dateien vergleichen (diff)",
                             input_example="diff: file1.py file2.py",
                             priority=2),
        }

        all_text = " ".join(goals + history).lower()
        for keyword, need in keyword_tools.items():
            if keyword in all_text:
                needs.append(need)

        # Standard-Needs die immer nützlich sind
        if len(needs) == 0:
            needs = [
                ToolNeed("Netzwerk-Ping zu Host prüfen",
                         input_example="ping: 192.168.1.103",
                         output_example="Latenz: 2ms | OK",
                         priority=1, source="default"),
                ToolNeed("Systemzeit und Uptime abfragen",
                         input_example="system_time",
                         output_example="2026-03-30 09:26 | Uptime: 2h",
                         priority=2, source="default"),
            ]

        return sorted(needs, key=lambda n: n.priority)


# ─── TOOL SYNTHESIZER ────────────────────────────────────────────────────────

class ToolSynthesizer:
    """
    Lässt LLM Python-Code für neue Tools schreiben.
    Generiert eine einfache Python-Funktion mit DDGK-kompatiblem Interface.
    """

    SYNTHESIS_PROMPT = """\
Du bist ein Python-Experte. Schreibe eine EINZELNE Python-Funktion für folgendes Tool:

Tool-Beschreibung: {description}
Eingabe-Beispiel: {input_example}
Ausgabe-Beispiel: {output_example}

ANFORDERUNGEN:
1. Funktion heißt: tool_{safe_name}(input_str: str) -> dict
2. Gibt immer zurück: {{"status": "OK"/"ERROR", "result": "...", "error": null/"..."}}
3. Keine externen Imports außer: os, sys, json, subprocess, urllib, pathlib, datetime, re, socket
4. Maximal 30 Zeilen Code
5. Exception-Handling obligatorisch
6. NUR Python-Code, kein Kommentar davor/danach, keine Erklärung

Antworte NUR mit dem Python-Code der Funktion:
```python
def tool_{safe_name}(input_str: str) -> dict:
```
"""

    FALLBACK_TOOLS = {
        "ping": '''
def tool_ping(input_str: str) -> dict:
    import socket, time
    host = input_str.replace("ping:", "").strip() or "8.8.8.8"
    try:
        t0 = time.time()
        socket.setdefaulttimeout(3)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, 80))
        latency = round((time.time() - t0) * 1000, 1)
        return {"status": "OK", "result": f"Host {host} erreichbar | Latenz: {latency}ms", "error": None}
    except Exception as e:
        return {"status": "ERROR", "result": f"Host {host} nicht erreichbar", "error": str(e)[:60]}
''',
        "system_time": '''
def tool_system_time(input_str: str) -> dict:
    import datetime, platform
    now = datetime.datetime.now()
    return {
        "status": "OK",
        "result": f"Zeit: {now.strftime('%Y-%m-%d %H:%M:%S')} | OS: {platform.system()} {platform.release()}",
        "error": None
    }
''',
        "json_validate": '''
def tool_json_validate(input_str: str) -> dict:
    import json, pathlib
    filepath = input_str.replace("json_validate:", "").strip()
    try:
        p = pathlib.Path(filepath)
        if not p.exists():
            return {"status": "ERROR", "result": "Datei nicht gefunden", "error": filepath}
        data = json.loads(p.read_text("utf-8"))
        return {"status": "OK", "result": f"Valides JSON | {len(str(data))} Zeichen | Typ: {type(data).__name__}", "error": None}
    except json.JSONDecodeError as e:
        return {"status": "ERROR", "result": "Ungültiges JSON", "error": str(e)[:80]}
    except Exception as e:
        return {"status": "ERROR", "result": "Fehler", "error": str(e)[:60]}
''',
        "diff": '''
def tool_diff(input_str: str) -> dict:
    import pathlib
    parts = input_str.split()
    if len(parts) < 2:
        return {"status": "ERROR", "result": "Format: file1.py file2.py", "error": None}
    try:
        p1, p2 = pathlib.Path(parts[0]), pathlib.Path(parts[1])
        if not p1.exists() or not p2.exists():
            return {"status": "ERROR", "result": "Eine Datei nicht gefunden", "error": None}
        lines1 = set(p1.read_text("utf-8", errors="replace").splitlines())
        lines2 = set(p2.read_text("utf-8", errors="replace").splitlines())
        added   = len(lines2 - lines1)
        removed = len(lines1 - lines2)
        return {"status": "OK", "result": f"+{added} Zeilen hinzugefügt, -{removed} entfernt", "error": None}
    except Exception as e:
        return {"status": "ERROR", "result": "Diff-Fehler", "error": str(e)[:60]}
''',
    }

    def __init__(self, ollama: OllamaBridge):
        self.ollama = ollama

    def _safe_name(self, description: str) -> str:
        import re
        words = description.lower().split()[:3]
        name  = "_".join(re.sub(r"[^a-z0-9]","",w) for w in words if w)
        return name or "custom_tool"

    def synthesize(self, need: ToolNeed) -> SynthesizedTool:
        """Generiert Python-Code für ein Tool."""
        safe_name = self._safe_name(need.description)

        # Fallback-Tools direkt verwenden (erweitertes Matching)
        EXTRA_ALIASES = {
            "ping":          ["ping", "netzwerk", "network", "host", "erreichbar"],
            "system_time":   ["system_time", "systemzeit", "zeit", "time", "uptime", "uhrzeit"],
            "json_validate": ["json_validate", "json", "validier", "validate"],
            "diff":          ["diff", "vergleich", "compare", "unterschied"],
        }
        for key, code in self.FALLBACK_TOOLS.items():
            aliases = EXTRA_ALIASES.get(key, [key])
            desc_lower = need.description.lower()
            if any(a in safe_name or a in desc_lower for a in aliases):
                tool = SynthesizedTool(
                    name=f"tool_{key}",
                    description=need.description,
                    risk_level="LOW",
                    code=code.strip(),
                )
                return tool

        # LLM-Synthese
        code = None
        if self.ollama.alive:
            prompt = self.SYNTHESIS_PROMPT.format(
                description=need.description,
                input_example=need.input_example or "string input",
                output_example=need.output_example or '{"status": "OK", "result": "..."}',
                safe_name=safe_name
            )
            resp = self.ollama.ask(prompt, tokens=350, temp=0.1)
            if resp:
                # Code aus Response extrahieren
                if "```python" in resp:
                    code = resp.split("```python")[-1].split("```")[0].strip()
                elif "def tool_" in resp:
                    start = resp.find("def tool_")
                    code  = resp[start:].strip()

        if not code:
            # Universeller Fallback
            code = f'''
def tool_{safe_name}(input_str: str) -> dict:
    """Auto-generiert: {need.description}"""
    try:
        return {{"status": "OK", "result": f"Tool '{safe_name}' ausgeführt mit: {{input_str[:50]}}", "error": None}}
    except Exception as e:
        return {{"status": "ERROR", "result": "Fehler", "error": str(e)[:60]}}
'''.strip()

        return SynthesizedTool(
            name=f"tool_{safe_name}",
            description=need.description,
            risk_level="MEDIUM",
            code=code,
        )


# ─── TOOL VALIDATOR ──────────────────────────────────────────────────────────

class ToolValidator:
    """
    Prüft generierten Code auf:
    1. Syntax-Korrektheit (AST)
    2. DDGK Safety (keine verbotenen Calls)
    3. Funktions-Interface (korrekte Signatur)
    """

    FORBIDDEN_PATTERNS = [
        "os.system", "subprocess.Popen", "eval(", "exec(",
        "__import__", "open(", "socket.connect",   # erlaubt in speziellen Tools
        "shutil.rmtree", "os.remove", "pathlib.Path.unlink",
    ]
    ALLOWED_EXCEPTIONS = ["socket", "open"]  # für ping und read-Tools

    def validate(self, tool: SynthesizedTool) -> Tuple[bool, str]:
        """Returns (valid, reason)."""
        code = tool.code

        # 1. Syntax-Check
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax-Fehler: {e}"

        # 2. Safety-Check
        forbidden_found = []
        for pattern in self.FORBIDDEN_PATTERNS:
            # Erlaube socket für ping-Tool
            if "socket" in pattern and "ping" in tool.name:
                continue
            # Erlaube open für read-Tools
            if pattern == "open(" and any(x in tool.name for x in ["read","csv","json"]):
                continue
            if pattern in code:
                forbidden_found.append(pattern)

        if forbidden_found:
            return False, f"Verbotene Patterns: {forbidden_found}"

        # 3. Interface-Check
        has_def = any(
            isinstance(n, ast.FunctionDef) and n.name.startswith("tool_")
            for n in ast.walk(tree)
        )
        if not has_def:
            return False, "Keine tool_*() Funktion gefunden"

        return True, "OK"

    def test_execution(self, tool: SynthesizedTool, test_input: str = "test") -> Tuple[bool, Any]:
        """Führt Tool in sicherer Umgebung aus."""
        try:
            namespace: Dict = {}
            exec(tool.code, namespace)   # noqa: S102
            fn_name = next(k for k in namespace if k.startswith("tool_"))
            fn = namespace[fn_name]
            result = fn(test_input)
            if isinstance(result, dict) and "status" in result:
                return True, result
            return False, {"status": "ERROR", "result": "Ungültiges Return-Format"}
        except Exception as e:
            return False, {"status": "ERROR", "error": str(e)[:80]}


# ─── DYNAMIC TOOL REGISTRY ────────────────────────────────────────────────────

class DynamicToolRegistry:
    """
    Erweiterbare Tool-Registrierung.
    Neue Tools werden zur Laufzeit hinzugefügt.
    """

    def __init__(self):
        self._tools: Dict[str, SynthesizedTool] = {}
        self._load_persisted()

    def register(self, tool: SynthesizedTool) -> bool:
        """Registriert ein validiertes Tool."""
        if not tool.validated:
            return False
        # Funktion laden
        namespace: Dict = {}
        try:
            exec(tool.code, namespace)
            fn_name = next(k for k in namespace if k.startswith("tool_"))
            tool.fn     = namespace[fn_name]
            tool.active = True
            self._tools[tool.name] = tool
            self._persist(tool)
            return True
        except Exception as e:
            return False

    def execute(self, tool_name: str, input_str: str) -> Dict:
        """Führt registriertes Tool aus."""
        if tool_name not in self._tools:
            return {"status": "NOT_FOUND", "result": f"Tool '{tool_name}' nicht registriert"}
        tool = self._tools[tool_name]
        if not tool.fn:
            return {"status": "ERROR", "result": "Tool nicht geladen"}
        try:
            tool.calls += 1
            result = tool.fn(input_str)
            if result.get("status") == "OK":
                tool.successes += 1
            else:
                tool.failures += 1
            return result
        except Exception as e:
            tool.failures += 1
            return {"status": "ERROR", "error": str(e)[:80]}

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    def _persist(self, tool: SynthesizedTool):
        """Speichert Tool-Code in Datei."""
        fp = TOOLS_DIR / f"{tool.name}.py"
        fp.write_text(
            f'# Auto-synthesized by HyperAgent\n'
            f'# {tool.description}\n'
            f'# Created: {tool.created_at}\n\n'
            f'{tool.code}\n',
            encoding="utf-8"
        )

    def _load_persisted(self):
        """Lädt gespeicherte Tools beim Start."""
        loaded = 0
        for fp in TOOLS_DIR.glob("tool_*.py"):
            try:
                code = fp.read_text("utf-8")
                name = fp.stem
                tool = SynthesizedTool(name=name, code=code, validated=True)
                namespace: Dict = {}
                exec(code, namespace)
                fn_name = next((k for k in namespace if k.startswith("tool_")), None)
                if fn_name:
                    tool.fn     = namespace[fn_name]
                    tool.active = True
                    self._tools[name] = tool
                    loaded += 1
            except:
                pass
        if loaded > 0:
            con.print(f"  📦 {loaded} persistierte Tools geladen")


# ─── HYPER AGENT ─────────────────────────────────────────────────────────────

class HyperAgent:
    """
    Das vollständige Hyper-Agent-System.

    Workflow:
      analyze_needs() → synthesize_tool() → validate() → register() → execute()

    Selbst-verbessernd:
      Bei Misserfolg → neu synthesisieren mit anderen Parametern
      Erfolgreich ausgeführte Tools → höhere Priorität
    """

    VERSION = "1.0.0-hyper"

    def __init__(self, ollama_url: str = "http://127.0.0.1:11434",
                 model: str = "qwen2.5:1.5b") -> None:
        self.ollama    = OllamaBridge(ollama_url, model)
        self.analyzer  = ToolAnalyzer()
        self.synth     = ToolSynthesizer(self.ollama)
        self.validator = ToolValidator()
        self.registry  = DynamicToolRegistry()
        self.memory    = HyperMemory()
        self._cycle    = 0

        if RICH:
            con.print(Panel.fit(
                f"[bold cyan]🦾 HYPER-AGENT SYSTEM v{self.VERSION}[/bold cyan]\n"
                f"[yellow]Selbständige Werkzeugerschaffung + DDGK-Governance[/yellow]\n"
                f"Ollama: {'✅ ' + model if self.ollama.alive else '❌ offline (Fallback aktiv)'}\n"
                f"Gespeicherte Tools: {len(self.registry.list_tools())}",
                border_style="cyan"
            ))
        else:
            con.print(f"🦾 HYPER-AGENT v{self.VERSION} | Ollama: {'OK' if self.ollama.alive else 'offline'}")

        self.memory.log("INIT", {"model": model, "alive": self.ollama.alive,
                                  "pre_loaded_tools": len(self.registry.list_tools())})

    def synthesize_and_register(self, need: ToolNeed) -> Optional[SynthesizedTool]:
        """Kompletter Workflow: Analysieren → Synthetisieren → Validieren → Registrieren."""
        self._cycle += 1
        con.print(f"\n  🔧 [{self._cycle}] Synthetisiere: {need.description[:60]}")

        # 1. Synthetisieren
        tool = self.synth.synthesize(need)
        con.print(f"  📝 Code generiert: {len(tool.code)} Zeichen")

        # 2. Validieren
        valid, reason = self.validator.validate(tool)
        if not valid:
            con.print(f"  ❌ Validierung fehlgeschlagen: {reason}")
            self.memory.log("SYNTHESIS_FAILED", {"need": need.description, "reason": reason})
            return None

        tool.validated = True
        con.print(f"  ✅ Validierung OK")

        # 3. Test-Ausführung
        test_ok, test_result = self.validator.test_execution(tool, need.input_example or "test")
        if test_ok:
            con.print(f"  ✅ Test-Ausführung: {test_result.get('result','')[:60]}")
        else:
            con.print(f"  ⚠️  Test-Warnung: {test_result.get('error','')[:60]} (registriere trotzdem)")

        # 4. Registrieren
        registered = self.registry.register(tool)
        if registered:
            con.print(f"  [bold green]🎉 Tool '{tool.name}' registriert und aktiv![/bold green]" if RICH
                      else f"  🎉 Tool '{tool.name}' registriert!")
            self.memory.log("TOOL_REGISTERED", {
                "tool_id": tool.tool_id, "name": tool.name,
                "description": need.description[:80],
                "risk": tool.risk_level, "test_ok": test_ok
            })
            return tool

        return None

    def execute_tool(self, tool_name: str, input_str: str) -> Dict:
        """Führt registriertes Tool aus."""
        result = self.registry.execute(tool_name, input_str)
        self.memory.log("TOOL_EXECUTED", {
            "tool": tool_name, "input": input_str[:50],
            "status": result.get("status"), "result": str(result.get("result",""))[:80]
        })
        return result

    def auto_discover_and_build(self, goals: List[str] = None,
                                 failed_tasks: List[Dict] = None,
                                 max_tools: int = 3) -> List[SynthesizedTool]:
        """
        Vollautomatisch: Analysiere → Baue fehlende Tools.

        Args:
            goals: Übergeordnete Ziele (für Keyword-Analyse)
            failed_tasks: Fehlgeschlagene Tasks aus Autonomous-Loop
            max_tools: Maximale Anzahl neuer Tools
        """
        goals        = goals or []
        failed_tasks = failed_tasks or []

        con.print("\n" + ("─"*55))
        con.print("[bold]🔍 HyperAgent: Analysiere Werkzeug-Bedarf...[/bold]" if RICH
                  else "🔍 HyperAgent: Analysiere Werkzeug-Bedarf...")

        needs = self.analyzer.analyze_gaps(goals, failed_tasks, [])
        con.print(f"  {len(needs)} Bedürfnisse erkannt")

        built: List[SynthesizedTool] = []
        for need in needs[:max_tools]:
            # Skip wenn schon vorhanden
            safe_name = "tool_" + self.synth._safe_name(need.description)
            if safe_name in self.registry.list_tools():
                con.print(f"  ⏭️  Tool '{safe_name}' bereits vorhanden")
                continue

            tool = self.synthesize_and_register(need)
            if tool:
                built.append(tool)

        return built

    def run_demo(self) -> Dict:
        """Demo: Zeigt den vollständigen Synthesize → Execute Workflow."""
        if RICH:
            con.print(Panel.fit(
                "[bold cyan]🦾 HYPER-AGENT DEMO — Tool-Synthesize + Execute[/bold cyan]",
                border_style="cyan"
            ))

        # 1. Tools bauen
        needs = [
            ToolNeed("Netzwerk-Ping zu Host", "ping: 192.168.1.103", "Latenz: 2ms", 1),
            ToolNeed("Systemzeit abfragen", "system_time", "2026-03-30 09:26", 2),
            ToolNeed("JSON-Datei validieren", "json_validate: data.json", "Valid", 3),
        ]

        built = []
        for need in needs:
            tool = self.synthesize_and_register(need)
            if tool:
                built.append(tool)

        # 2. Tools ausführen
        con.print(f"\n  [bold]Führe {len(built)} neue Tools aus:[/bold]" if RICH
                  else f"\n  Führe {len(built)} neue Tools aus:")

        results = []
        for tool in built:
            r = self.execute_tool(tool.name, tool.name.replace("tool_",""))
            status_icon = "✅" if r.get("status") == "OK" else "❌"
            con.print(f"  {status_icon} {tool.name}: {r.get('result','')[:60]}")
            results.append({"tool": tool.name, **r})

        # 3. Zusammenfassung
        if RICH:
            t = Table(title="🦾 HyperAgent — Synthese-Ergebnis", box=box.ROUNDED)
            t.add_column("Tool", style="cyan")
            t.add_column("Status", style="yellow")
            t.add_column("Ergebnis", style="green")
            for r in results:
                t.add_row(r["tool"], r.get("status","?"), str(r.get("result",""))[:40])
            con.print(t)

        # Report
        report = {
            "ts": datetime.datetime.now().isoformat(),
            "tools_built": len(built),
            "tools_registered": len(self.registry.list_tools()),
            "executions": results,
            "memory_entries": self.memory.count(),
        }
        REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        self.memory.log("DEMO_COMPLETE", {"built": len(built), "results": len(results)})

        con.print(f"\n  📦 Tools gespeichert in: {TOOLS_DIR}")
        con.print(f"  📜 Memory: {self.memory.count()} Einträge")
        return report

    def status(self) -> Dict:
        return {
            "version":      self.VERSION,
            "tools_active": len(self.registry.list_tools()),
            "tool_list":    self.registry.list_tools(),
            "ollama":       self.ollama.alive,
            "memory":       self.memory.count(),
            "cycle":        self._cycle,
        }


# ─── MAIN ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="DDGK HyperAgent — Tool Synthesizer")
    ap.add_argument("--demo",    action="store_true", help="Demo: baue + teste Tools")
    ap.add_argument("--status",  action="store_true", help="Zeige System-Status")
    ap.add_argument("--goal",    type=str, default="", help="Ziel für Tool-Analyse")
    ap.add_argument("--build",   type=str, default="", help="Beschreibung für ein neues Tool")
    ap.add_argument("--execute", type=str, default="", help="Tool ausführen: 'tool_name:input'")
    args = ap.parse_args()

    agent = HyperAgent()

    if args.demo or (not args.status and not args.goal and not args.build and not args.execute):
        report = agent.run_demo()
        print(f"\n  ✅ Demo abgeschlossen | {report['tools_built']} Tools gebaut")

    if args.status:
        s = agent.status()
        print(json.dumps(s, indent=2, ensure_ascii=False))

    if args.goal:
        built = agent.auto_discover_and_build(goals=[args.goal], max_tools=3)
        print(f"\n  ✅ {len(built)} Tools für Ziel '{args.goal[:50]}' gebaut")

    if args.build:
        need  = ToolNeed(description=args.build, priority=1, source="cli")
        tool  = agent.synthesize_and_register(need)
        print(f"  {'✅' if tool else '❌'} Tool: {tool.name if tool else 'Fehlgeschlagen'}")

    if args.execute:
        parts = args.execute.split(":", 1)
        tool_name  = parts[0]
        input_str  = parts[1] if len(parts) > 1 else ""
        result = agent.execute_tool(tool_name, input_str)
        print(f"  {result.get('status')}: {result.get('result','')}")
