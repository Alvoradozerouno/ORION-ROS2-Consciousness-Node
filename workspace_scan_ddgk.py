#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Workspace + Schlagwort-Scan (Note10, NPU, Termux, Ollama, Pi5) -> JSON fuer DDGK."""
import json, hashlib, pathlib, re, datetime

WS = pathlib.Path(__file__).resolve().parent
OUT = WS / "ZENODO_UPLOAD" / "WORKSPACE_SCAN_DDGK.json"
MEM = WS / "cognitive_ddgk" / "cognitive_memory.jsonl"

KEYWORDS = {
    "note10": re.compile(r"(?i)\b(note\s*10|note10|galaxy\s*note)\b"),
    "npu": re.compile(r"\bNPU\b|neural\s*process|exynos\s*9820|dsp", re.I),
    "termux": re.compile(r"termux", re.I),
    "ollama": re.compile(r"ollama", re.I),
    "pi5|raspberry": re.compile(r"pi\s*5|raspberry|192\.168", re.I),
    "ddgk": re.compile(r"DDGK|cognitive_memory", re.I),
    "phi_kappa": re.compile(r"\bkappa\b|\bphi\b|σ|sigma", re.I),
}

SKIP_DIRS = {".git", "node_modules", ".mypy_cache", "__pycache__", ".venv", "venv", "repos"}

def scan_file(path: pathlib.Path, max_bytes: int = 400_000) -> str | None:
    try:
        if path.stat().st_size > max_bytes:
            return None
        return path.read_text("utf-8", errors="replace")
    except OSError:
        return None

def ddgk_append(event: str, data: dict):
    def _last_hash():
        if not MEM.exists():
            return ""
        ls = [x for x in MEM.read_text("utf-8").splitlines() if x.strip()]
        return json.loads(ls[-1]).get("hash", "") if ls else ""
    prev = _last_hash()
    e = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "agent": "WORKSPACE-SCAN",
        "action": event,
        "data": data,
        "prev": prev,
        "ddgk_version": "2.0_passive_observer",
    }
    raw = json.dumps(e, ensure_ascii=False, sort_keys=True)
    e["hash"] = hashlib.sha256(raw.encode()).hexdigest()
    with MEM.open("a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")

def main():
    hits = {k: [] for k in KEYWORDS}
    files_scanned = 0
    for p in WS.rglob("*"):
        if files_scanned >= 6000:
            break
        if not p.is_file():
            continue
        parts = set(p.parts)
        if parts & SKIP_DIRS:
            continue
        if p.suffix.lower() not in {".py", ".md", ".json", ".jsonl", ".txt", ".yaml", ".yml", ".ini", ".env"}:
            continue
        text = scan_file(p)
        if text is None:
            continue
        files_scanned += 1
        rel = str(p.relative_to(WS))
        for name, rx in KEYWORDS.items():
            if rx.search(text):
                if len(hits[name]) < 40:
                    hits[name].append(rel)

    report = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "workspace": str(WS),
        "files_scanned_approx": files_scanned,
        "hits_by_keyword": hits,
        "note_on_note10_npu": (
            "Galaxy Note 10 (Exynos-Variante): SoC Exynos 9820 mit integrierter NPU laut "
            "Hersteller-/Presseinfos; fuer On-Device-Inferenz (Kamera/AR) nutzbar. "
            "Termux/Android: nativelles Ollama ggf. eingeschraenkt — typisch CPU/NNAPI."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    ddgk_append("workspace_scan_complete", {"out": str(OUT), "keywords": {k: len(v) for k, v in hits.items()}})
    print(f"OK {files_scanned} Dateien -> {OUT.name}")

if __name__ == "__main__":
    main()
