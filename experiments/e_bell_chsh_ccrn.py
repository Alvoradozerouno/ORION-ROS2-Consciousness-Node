#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E_BELL / CHSH — CCRN-Messprotokoll (software-physikalisch, keine Labor-Quantenclaims).

Misst:
  - CHSH-Parameter S aus 4 Korrelationen E(a,b), E(a,b'), E(a',b), E(a',b')
    mit binären Antworten {-1,+1} (semantische Pseudo-Bell-Struktur, vgl. LLM-Literatur).
  - Geschwindigkeit: Tokens/s (Ollama eval_count/elapsed), Latenz ms, Wandzeit.
  - Schichten (operationalisiert):
      ALGORITHMIC_MS  — reine Python-Vorbereitung ohne Netz
      LLM_MS          — Summe Ollama-Generate
      POST_AUDIT_MS   — Schreiben JSONL + optional cognitive_memory
      Anteil LLM_DOMINANCE = LLM_MS / TOTAL_MS

  „Im Algorithmus“ vs. „darüber“: hier = Anteil deterministischer Code vs. LLM-Wandzeit
  (kein Philosophieclaim, nur Messgrößen).

Nutzung:
  python experiments/e_bell_chsh_ccrn.py [--trials 20] [--model qwen2.5:1.5b] [--host http://127.0.0.1:11434]

Ausgabe:
  experiments/logs/e_bell_chsh_ccrn.jsonl
  ZENODO_UPLOAD/DDGK_E_BELL_CHSH_REPORT.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

WS = Path(__file__).resolve().parent.parent
LOG_DIR = WS / "experiments" / "logs"
ZENODO = WS / "ZENODO_UPLOAD"
MEM = WS / "cognitive_ddgk" / "cognitive_memory.jsonl"


def _utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_binary(text: str) -> Optional[int]:
    """Extrahiere 1 oder -1 aus Modellantwort."""
    if not text:
        return None
    t = text.strip().replace("\n", " ")
    if re.search(r"(?<![0-9])-1(?![0-9])", t) or re.search(r"\b-1\b", t):
        return -1
    if re.search(r"(?<![0-9])\+1\b", t) or re.search(r"(?<![0-9])\b1\b(?![0-9])", t[-40:]):
        return 1
    m = re.findall(r"-?\d+", t[-30:])
    if m:
        try:
            v = int(m[-1])
            if v in (-1, 1):
                return v
        except ValueError:
            pass
    return None


def ollama_generate(host: str, model: str, prompt: str, timeout: float = 120.0) -> Tuple[str, float, int, float]:
    """
    Returns: text, wall_s, eval_count, tokens_per_s (0 wenn unbekannt)
    """
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 32},
        }
    ).encode()
    req = urllib.request.Request(
        f"{host.rstrip('/')}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    wall = time.perf_counter() - t0
    data = json.loads(raw.decode("utf-8", errors="replace"))
    text = (data.get("response") or "").strip()
    ev = int(data.get("eval_count") or 0)
    tps = (ev / wall) if wall > 0 and ev else 0.0
    return text, wall, ev, tps


@dataclass
class TrialStats:
    algorithmic_ms: float = 0.0
    llm_ms: float = 0.0
    post_audit_ms: float = 0.0
    llm_calls: int = 0
    tokens_generated: int = 0


def build_prompts(seed: str) -> Dict[str, str]:
    """Vier Einstellungen a, a', b, b' — feste Schablone, Zufall nur im seed."""
    return {
        "a": (
            f"Kontext-ID: {seed}\n"
            "Du bist Partei A (Einstellung a). Entscheide binär: stimme der Aussage zu?\n"
            "Aussage: 'Die Antwort auf die nächste Frage ist konsistent.'\n"
            "Antworte exakt mit einer Zeile: nur die Zahl 1 oder -1."
        ),
        "a_": (
            f"Kontext-ID: {seed}\n"
            "Du bist Partei A (Einstellung a'). Entscheide binär: stimme der Aussage zu?\n"
            "Aussage: 'Ein zufälliger Kontext ist strukturierbar.'\n"
            "Antworte exakt mit einer Zeile: nur die Zahl 1 oder -1."
        ),
        "b": (
            f"Kontext-ID: {seed}\n"
            "Du bist Partei B (Einstellung b). Entscheide binär: stimme der Aussage zu?\n"
            "Aussage: 'Kooperation erhöht Stabilität.'\n"
            "Antworte exakt mit einer Zeile: nur die Zahl 1 oder -1."
        ),
        "b_": (
            f"Kontext-ID: {seed}\n"
            "Du bist Partei B (Einstellung b'). Entscheide binär: stimme der Aussage zu?\n"
            "Aussage: 'Messung verändert den Zustand.'\n"
            "Antworte exakt mit einer Zeile: nur die Zahl 1 oder -1."
        ),
    }


def run_chsh_trial(
    host: str,
    model: str,
    seed: str,
    stats: TrialStats,
) -> Optional[Dict[str, Any]]:
    """Ein Trial: vier Ausgänge A(a), A(a'), B(b), B(b'); Produkte für CHSH-Mittelung."""
    p = build_prompts(seed)
    t_alg0 = time.perf_counter()
    stats.algorithmic_ms += (time.perf_counter() - t_alg0) * 1000

    outs: Dict[str, Optional[int]] = {}
    texts: Dict[str, str] = {}
    for key in ("a", "a_", "b", "b_"):
        t0 = time.perf_counter()
        txt, wall, ev, _tps = ollama_generate(host, model, p[key])
        dt_ms = (time.perf_counter() - t0) * 1000
        stats.llm_ms += dt_ms
        stats.llm_calls += 1
        stats.tokens_generated += ev
        texts[key] = txt[:500]
        outs[key] = parse_binary(txt)

    A = outs["a"]
    Ap = outs["a_"]
    B = outs["b"]
    Bp = outs["b_"]
    if None in (A, Ap, B, Bp):
        return None
    # Produkte (gleicher „Kontext“ seed) — später über Trials mitteln
    p_ab = A * B
    p_abp = A * Bp
    p_apb = Ap * B
    p_apbp = Ap * Bp
    return {
        "seed": seed,
        "A": A,
        "Ap": Ap,
        "B": B,
        "Bp": Bp,
        "prod_ab": p_ab,
        "prod_abp": p_abp,
        "prod_apb": p_apb,
        "prod_apbp": p_apbp,
        "text_preview": {k: texts[k][:120] for k in texts},
    }


def append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def memory_append(agent: str, action: str, data: Dict[str, Any]) -> None:
    if not MEM.exists():
        return
    lines = [l for l in MEM.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
    prev = json.loads(lines[-1]).get("hash", "") if lines else ""
    entry = {"ts": _utc(), "agent": agent, "action": action, "data": data, "prev": prev}
    raw = json.dumps(entry, ensure_ascii=False)
    entry["hash"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    with MEM.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="E_BELL CHSH CCRN — Messlauf")
    ap.add_argument("--trials", type=int, default=24, help="Anzahl Seeds (Statistik)")
    ap.add_argument("--model", default="qwen2.5:1.5b")
    ap.add_argument("--host", default="http://127.0.0.1:11434")
    ap.add_argument("--seed-base", type=int, default=42)
    ap.add_argument("--no-memory", action="store_true")
    args = ap.parse_args()

    stats = TrialStats()
    t_run0 = time.perf_counter()
    rng = random.Random(args.seed_base)

    sum_ab = sum_abp = sum_apb = sum_apbp = 0.0
    valid = 0
    log_path = LOG_DIR / "e_bell_chsh_ccrn.jsonl"

    for i in range(args.trials):
        seed = f"E_BELL-{args.seed_base}-{i}-{rng.randint(0, 10_000_000)}"
        t_alg = time.perf_counter()
        stats.algorithmic_ms += (time.perf_counter() - t_alg) * 1000

        tr = run_chsh_trial(args.host, args.model, seed, stats)
        row = {
            "ts": _utc(),
            "trial_index": i,
            "host": args.host,
            "model": args.model,
            "synthetic_context": True,
            "trial": tr,
        }
        if tr:
            valid += 1
            sum_ab += tr["prod_ab"]
            sum_abp += tr["prod_abp"]
            sum_apb += tr["prod_apb"]
            sum_apbp += tr["prod_apbp"]
        append_jsonl(log_path, row)

    total_ms = (time.perf_counter() - t_run0) * 1000
    t_post0 = time.perf_counter()
    n = float(valid)
    e_ab = sum_ab / n if n else 0.0
    e_abp = sum_abp / n if n else 0.0
    e_apb = sum_apb / n if n else 0.0
    e_apbp = sum_apbp / n if n else 0.0
    s_chsh = abs(e_ab + e_abp + e_apb - e_apbp)
    report = {
        "experiment": "E_BELL_CHSH_CCRN",
        "ts_utc": _utc(),
        "model": args.model,
        "host": args.host,
        "trials_requested": args.trials,
        "trials_valid": valid,
        "E_ab": round(e_ab, 6),
        "E_ab_prime": round(e_abp, 6),
        "E_a_prime_b": round(e_apb, 6),
        "E_a_prime_b_prime": round(e_apbp, 6),
        "S_CHSH": round(s_chsh, 6),
        "S_note": "|E_ab+E_ab'+E_a'b-E_a'b'| aus Mittelwerten der Produkte (semantisches LLM-Protokoll)",
        "classical_bound": 2.0,
        "tsirelson_bound": 2.828427,
        "layers_ms": {
            "algorithmic_prep_reported_in_trial": round(stats.algorithmic_ms, 3),
            "llm_total": round(stats.llm_ms, 3),
            "wall_total": round(total_ms, 3),
        },
        "dominance": {
            "llm_fraction_of_wall": round(stats.llm_ms / total_ms, 4) if total_ms > 0 else None,
            "non_llm_fraction_of_wall": round(
                max(0.0, total_ms - stats.llm_ms) / total_ms, 4
            )
            if total_ms > 0
            else None,
            "interpretation": {
                "im_algorithmus": "non_llm_fraction — Python/JSON/Parsing ohne Ollama-Generate",
                "darueber_llm": "llm_fraction — Zeit in Ollama (nicht nur 'Algorithmus')",
                "postsynthetisch": "post_audit_ms — Report + Memory nach Messung",
            },
        },
        "synthetic": {
            "prompts_templated": True,
            "seed_randomized": True,
            "synthetic_vs_postsynthetic": "synthetisch = erzeugte Kontexte; postsynthetisch = Auswertung+Audit nach Messung",
        },
        "log_path": str(log_path.relative_to(WS)),
    }
    ZENODO.mkdir(parents=True, exist_ok=True)
    rep_path = ZENODO / "DDGK_E_BELL_CHSH_REPORT.json"
    stats.post_audit_ms += (time.perf_counter() - t_post0) * 1000
    report["layers_ms"]["post_audit_write"] = round(stats.post_audit_ms, 3)
    report["speed"] = {
        "tokens_generated_total": stats.tokens_generated,
        "llm_calls": stats.llm_calls,
        "mean_tokens_per_s": round(
            stats.tokens_generated / (stats.llm_ms / 1000.0), 4
        )
        if stats.llm_ms > 0
        else None,
    }

    rep_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    t_mem = time.perf_counter()
    if not args.no_memory:
        memory_append(
            "SYSTEM",
            "e_bell_chsh_ccrn_complete",
            {
                "S_CHSH": report["S_CHSH"],
                "trials_valid": valid,
                "report": str(rep_path.relative_to(WS)),
            },
        )
    mem_ms = (time.perf_counter() - t_mem) * 1000
    report["layers_ms"]["post_audit_write"] = round(stats.post_audit_ms + mem_ms, 3)
    report["layers_ms"]["memory_append_ms"] = round(mem_ms, 3)
    rep_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nOK: Report -> {rep_path}", file=sys.stderr)
    return 0 if valid > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
