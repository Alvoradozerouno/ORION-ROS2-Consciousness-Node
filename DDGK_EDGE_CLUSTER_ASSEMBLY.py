#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DDGK EDGE CLUSTER ASSEMBLY — 16 Agenten × Analyse / Einrichtung / Nutzung
==========================================================================
Ein Lauf: Probes (Ollama Laptop·Pi5·Note10, Note10 DDGK-Agent, Laptop-GPU, USB-Pfade),
danach Subprocess agents/agent_1..16.py mit Mission EDGE_CLUSTER.

Ausgabe: ZENODO_UPLOAD/DDGK_EDGE_CLUSTER_ASSEMBLY_REPORT.json
Optional: cognitive_ddgk/cognitive_memory.jsonl (kurzer Eintrag)

Nutzung:
  python DDGK_EDGE_CLUSTER_ASSEMBLY.py
  python DDGK_EDGE_CLUSTER_ASSEMBLY.py --dry-run   # keine Netzwerk-Probes
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent

try:
    from workspace_env import load_workspace_dotenv

    load_workspace_dotenv(override=False)
except ImportError:
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def probe_http_json(url: str, timeout: float = 4.0) -> dict[str, Any]:
    out: dict[str, Any] = {"url": url, "ok": False, "status": None, "body_preview": None}
    if not url or not url.startswith("http"):
        out["error"] = "invalid_or_empty_url"
        return out
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ORION-DDGK-EdgeAssembly/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(8000).decode("utf-8", errors="replace")
            out["ok"] = True
            out["status"] = r.status
            try:
                out["json"] = json.loads(raw)
            except json.JSONDecodeError:
                out["body_preview"] = raw[:400]
    except urllib.error.HTTPError as e:
        out["status"] = e.code
        out["error"] = f"HTTP {e.code}"
    except Exception as ex:
        out["error"] = str(ex)[:200]
    return out


def probe_note10_ddgk(base: str, dry_run: bool) -> dict[str, Any]:
    if dry_run:
        return {"skipped": True, "reason": "dry_run"}
    base = base.rstrip("/")
    if not base:
        return {"skipped": True, "reason": "NOTE10_DDGK_URL unset"}
    return probe_http_json(f"{base}/health", timeout=5.0)


def probe_laptop_gpu() -> dict[str, Any]:
    g: dict[str, Any] = {
        "torch_cuda": False,
        "torch_device": None,
        "nvidia_smi": None,
    }
    try:
        import torch

        g["torch_cuda"] = bool(torch.cuda.is_available())
        if g["torch_cuda"]:
            g["torch_device"] = torch.cuda.get_device_name(0)
    except ImportError:
        g["torch_note"] = "torch_not_installed"
    except Exception as ex:
        g["torch_note"] = str(ex)[:120]
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=8,
        )
        if r.returncode == 0 and r.stdout.strip():
            g["nvidia_smi"] = r.stdout.strip()[:300]
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return g


def usb_snapshot() -> dict[str, Any]:
    """Bekannte externe Pfade (keine Secrets)."""
    candidates = []
    for key in ("ORION_USB_ROOT", "ORION_SEED_SOURCE"):
        v = (os.environ.get(key) or "").strip()
        if v:
            candidates.append({"env": key, "path": v, "exists": Path(v).exists()})
    for p in (Path("E:/"), Path("E:/ORION_SEED_COMPLETE"), Path("E:/attached_assets.zip")):
        candidates.append({"env": None, "path": str(p), "exists": p.exists()})
    return {"paths": candidates}


def ollama_cluster(dry_run: bool) -> dict[str, Any]:
    if dry_run:
        return {"skipped": True, "reason": "dry_run"}
    try:
        from ollama_nodes_scan import _normalize_base, probe_ollama
    except ImportError:
        return {"error": "ollama_nodes_scan_import_failed"}

    laptop = _normalize_base(os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"))
    pi5 = _normalize_base(os.environ.get("OLLAMA_PI5", "http://192.168.1.103:11434"))
    note = _normalize_base(os.environ.get("OLLAMA_NOTE10", ""))
    out: dict[str, Any] = {}
    out["Laptop"] = probe_ollama(laptop, 6.0)
    out["Pi5"] = probe_ollama(pi5, 6.0)
    if note:
        out["Note10"] = probe_ollama(note, 6.0)
    else:
        out["Note10"] = {
            "url": "",
            "skipped": True,
            "einsatzbereit": False,
            "fehler": "OLLAMA_NOTE10 not set",
        }
    return out


def run_agent_subprocess(agent_id: int, payload: dict[str, Any], timeout: int = 90) -> dict[str, Any]:
    script = ROOT / "agents" / f"agent_{agent_id}.py"
    if not script.is_file():
        return {"agent_id": agent_id, "error": "script_missing", "path": str(script)}
    data = json.dumps(payload, ensure_ascii=False)
    try:
        r = subprocess.run(
            [sys.executable, str(script), data],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        if r.returncode != 0:
            return {
                "agent_id": agent_id,
                "returncode": r.returncode,
                "stderr": (r.stderr or "")[:800],
                "stdout": (r.stdout or "")[:800],
            }
        return json.loads(r.stdout)
    except subprocess.TimeoutExpired:
        return {"agent_id": agent_id, "error": "timeout"}
    except json.JSONDecodeError:
        return {"agent_id": agent_id, "error": "json_parse", "stdout": (r.stdout or "")[:600]}
    except Exception as ex:
        return {"agent_id": agent_id, "error": str(ex)[:200]}


def append_memory_line(topic: str, data: dict[str, Any]) -> None:
    mem = ROOT / "cognitive_ddgk" / "cognitive_memory.jsonl"
    mem.parent.mkdir(parents=True, exist_ok=True)
    prev = ""
    if mem.is_file():
        lines = [x for x in mem.read_text(encoding="utf-8", errors="replace").splitlines() if x.strip()]
        if lines:
            try:
                prev = json.loads(lines[-1]).get("hash", "")
            except json.JSONDecodeError:
                prev = ""
    e = {
        "ts": _now_iso(),
        "agent": "DDGK-EDGE-ASSEMBLY",
        "action": topic,
        "data": data,
        "prev": prev,
    }
    raw = json.dumps(e, ensure_ascii=False, sort_keys=True)
    e["hash"] = hashlib.sha256(raw.encode()).hexdigest()
    with mem.open("a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="16-Agenten Edge-Cluster Assembly")
    ap.add_argument("--dry-run", action="store_true", help="Keine HTTP-Ollama/Note10-Probes")
    ap.add_argument(
        "--no-memory",
        action="store_true",
        help="Kein cognitive_memory.jsonl Eintrag",
    )
    args = ap.parse_args()

    note10_ddgk = (os.environ.get("NOTE10_DDGK_URL") or "").strip()

    probes: dict[str, Any] = {
        "ts": _now_iso(),
        "ollama": ollama_cluster(args.dry_run),
        "note10_ddgk": probe_note10_ddgk(note10_ddgk, args.dry_run),
        "laptop_gpu": probe_laptop_gpu(),
        "usb": usb_snapshot(),
        "flywire": {
            "codex_download": "https://codex.flywire.ai/api/download",
            "home": "https://flywire.ai",
            "note": "Connectome auf Laptop laden/auswerten; Note10 fuer Edge-Inference/TFLite",
        },
        "note10_agent_file": str(ROOT / "ddgk_note10_agent.py"),
        "note10_setup": str(ROOT / "NOTE10_SETUP.md"),
    }

    aggregate: dict[str, Any] = {"probes": probes, "agents": {}}
    print("\n=== DDGK EDGE CLUSTER ASSEMBLY (16 Agenten) ===\n", flush=True)

    for phase in range(1, 17):
        payload = {
            "mission": "EDGE_CLUSTER",
            "phase": phase,
            "probes": probes,
            "aggregate_keys": list(aggregate["agents"].keys()),
        }
        print(f"  [Agent {phase:02d}] OK", flush=True)
        res = run_agent_subprocess(phase, payload)
        aggregate["agents"][f"agent_{phase}"] = res

    out_path = ROOT / "ZENODO_UPLOAD" / "DDGK_EDGE_CLUSTER_ASSEMBLY_REPORT.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "timestamp": _now_iso(),
        "mission": "EDGE_CLUSTER",
        "dry_run": args.dry_run,
        "note10_ddgk_url_configured": bool(note10_ddgk),
        "aggregate": aggregate,
    }
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    if not args.no_memory:
        append_memory_line(
            "edge_cluster_assembly",
            {
                "report": str(out_path),
                "ollama_ok": sum(
                    1
                    for v in (probes.get("ollama") or {}).values()
                    if isinstance(v, dict) and v.get("einsatzbereit")
                ),
                "note10_ddgk_ok": bool((probes.get("note10_ddgk") or {}).get("ok")),
            },
        )

    print(f"\nOK Report: {out_path}\n", flush=True)
    o = probes.get("ollama") or {}
    if isinstance(o, dict) and not o.get("skipped"):
        for name in ("Laptop", "Pi5", "Note10"):
            row = o.get(name)
            if isinstance(row, dict):
                st = "OK" if row.get("einsatzbereit") else ("SKIP" if row.get("skipped") else "FAIL")
                print(f"  Ollama [{name}]: {st}", flush=True)
    nd = probes.get("note10_ddgk") or {}
    if nd.get("skipped"):
        print(f"  Note10 DDGK-Agent: skipped ({nd.get('reason')})", flush=True)
    else:
        print(f"  Note10 DDGK-Agent health: {'OK' if nd.get('ok') else 'FAIL'}", flush=True)
    gpu = probes.get("laptop_gpu") or {}
    print(
        f"  Laptop GPU: torch_cuda={gpu.get('torch_cuda')} nvidia_smi={'yes' if gpu.get('nvidia_smi') else 'no'}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
