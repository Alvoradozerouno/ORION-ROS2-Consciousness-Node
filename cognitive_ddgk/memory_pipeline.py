#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  DDGK 2-PHASEN MEMORY PIPELINE                                     ║
║                                                                      ║
║  Inspiriert von: openai/codex memories/ (Phase1 + Phase2)          ║
║  DDGK-Erweiterung: Secret Redaction + Decision Chain               ║
║                                                                      ║
║  PHASE 1 — Per-Session Extraction:                                  ║
║    Input:  cognitive_memory.jsonl (flat log)                        ║
║    Filter: Eligible sessions (age, not already processed)           ║
║    Output: cognitive_memory_stage1.jsonl                            ║
║    Extra:  Secret Redaction (API Keys entfernen)                    ║
║                                                                      ║
║  PHASE 2 — Global Consolidation:                                    ║
║    Input:  Stage-1 Outputs                                          ║
║    Output: cognitive_memory.md  (human-readable, gerankt)          ║
║    Diff:   added / retained / removed                               ║
║    Watermark: Verhindert Doppel-Verarbeitung                        ║
╚══════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import json, re, hashlib, datetime, os
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field

BASE     = Path(__file__).parent
MEM_RAW  = BASE / "cognitive_memory.jsonl"
STAGE1   = BASE / "cognitive_memory_stage1.jsonl"
STAGE2   = BASE / "cognitive_memory.md"
ROLLUPS  = BASE / "rollout_summaries"
WATERMARK= BASE / ".memory_watermark.json"
ROLLUPS.mkdir(exist_ok=True)

# Secret redaction patterns (nach Codex memories Phase2-Vorbild)
SECRET_PATTERNS = [
    (r"ghp_[A-Za-z0-9]{36,}", "[REDACTED:github_token]"),
    (r"sk-[A-Za-z0-9]{48,}", "[REDACTED:openai_key]"),
    (r"hf_[A-Za-z0-9]{36,}", "[REDACTED:hf_token]"),
    (r"(GITHUB_TOKEN|HF_TOKEN|SUPABASE_ANON_KEY|ZENODO_TOKEN)\s*=\s*\S+",
     r"\1=[REDACTED]"),
    (r"password\s*=\s*['\"]?\w+['\"]?", "password=[REDACTED]"),
    (r"(Bearer|token)\s+[A-Za-z0-9_\-\.]{20,}", r"\1 [REDACTED]"),
]

try:
    from rich.console import Console
    RICH = True; con = Console()
except ImportError:
    RICH = False
    class _C:
        def print(self, *a, **kw): print(*a)
    con = _C()


def _redact(text: str) -> str:
    """Entfernt alle bekannten Secrets aus Text."""
    out = text
    for pat, repl in SECRET_PATTERNS:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out

def _hash(obj: dict) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]

def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


@dataclass
class Stage1Record:
    """Output von Phase 1 — extrahiertes Session-Memory."""
    session_id:     str
    ts:             str
    raw_memory:     str   # Detailed memory (redacted)
    rollout_summary: str  # Compact summary
    rollout_slug:   str   # Short label
    usage_count:    int = 0
    last_usage:     str = ""
    selected_for_phase2: bool = False
    record_hash:    str = ""


# ─── PHASE 1: SESSION EXTRACTION ─────────────────────────────────────────────

class Phase1Extractor:
    """
    Extrahiert strukturierte Memories aus rohen Session-Logs.
    Inspiriert von: codex memories/phase1.rs

    Unterschied zu Codex:
    - Kein SQLite State DB (nutzt JSONL)
    - DDGK Decision Chain Hash als session_id
    - Secret Redaction in Python (statt Rust)
    """

    def __init__(self, max_age_days: int = 30, max_sessions: int = 50):
        self.max_age_days = max_age_days
        self.max_sessions = max_sessions
        self._processed: set = self._load_processed()

    def _load_processed(self) -> set:
        if STAGE1.exists():
            processed = set()
            for line in STAGE1.read_text("utf-8").splitlines():
                try:
                    processed.add(json.loads(line).get("session_id",""))
                except:
                    pass
            return processed
        return set()

    def run(self) -> List[Stage1Record]:
        """Phase 1: Verarbeitet ungesehene Sessions aus cognitive_memory.jsonl"""
        if not MEM_RAW.exists():
            con.print("  [dim]Phase 1: Kein cognitive_memory.jsonl gefunden[/dim]" if RICH
                      else "  Phase 1: Kein cognitive_memory.jsonl")
            return []

        # Lade alle rohen Memory-Einträge
        entries = []
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=self.max_age_days)
        for line in MEM_RAW.read_text("utf-8").splitlines():
            try:
                e = json.loads(line)
                ts_str = e.get("ts", e.get("timestamp", ""))
                if ts_str:
                    try:
                        ts = datetime.datetime.fromisoformat(ts_str.replace("Z","+00:00"))
                        if ts < cutoff:
                            continue  # Zu alt
                    except:
                        pass
                entries.append(e)
            except:
                pass

        # Gruppiere nach Session/Tag
        sessions: Dict[str, List[dict]] = {}
        for e in entries:
            sid = e.get("session_id") or e.get("ts", "")[:10]  # Datum als Fallback
            if sid not in sessions:
                sessions[sid] = []
            sessions[sid].append(e)

        # Verarbeite noch nicht gesehene Sessions
        records = []
        processed_count = 0
        for sid, evts in sessions.items():
            if sid in self._processed:
                continue
            if processed_count >= self.max_sessions:
                break

            record = self._extract_session(sid, evts)
            if record:
                records.append(record)
                self._processed.add(sid)
                processed_count += 1

        # Stage-1 Outputs speichern
        if records:
            with STAGE1.open("a", encoding="utf-8") as f:
                for r in records:
                    d = {
                        "session_id": r.session_id,
                        "ts": r.ts,
                        "raw_memory": r.raw_memory,
                        "rollout_summary": r.rollout_summary,
                        "rollout_slug": r.rollout_slug,
                        "usage_count": r.usage_count,
                        "record_hash": r.record_hash,
                    }
                    f.write(json.dumps(d, ensure_ascii=False) + "\n")

        msg = f"Phase 1: {len(records)} neue Sessions extrahiert ({processed_count} verarbeitet)"
        con.print(f"  🧠 {msg}" if not RICH else f"  [cyan]🧠 {msg}[/cyan]")
        return records

    def _extract_session(self, session_id: str, events: List[dict]) -> Optional[Stage1Record]:
        """Extrahiert Memory aus einer Session."""
        if not events:
            return None

        # Relevante Ereignisse filtern
        relevant = [e for e in events if e.get("type") not in ["debug", "heartbeat", "ping"]]

        # raw_memory: alle relevanten Events zusammengeführt
        raw_parts = []
        for e in relevant[:20]:  # Max 20 Events
            text = e.get("content") or e.get("message") or e.get("action") or ""
            if text:
                raw_parts.append(f"[{e.get('type','event')}] {text[:200]}")

        raw_memory = _redact("\n".join(raw_parts))

        # rollout_summary: komprimierte Zusammenfassung
        types = [e.get("type","?") for e in events]
        type_counts = {t: types.count(t) for t in set(types)}
        summary_parts = [f"{t}×{c}" for t, c in sorted(type_counts.items(), key=lambda x: -x[1])[:5]]

        # Wichtigste Aktionen
        decisions = [e for e in events if e.get("type") in ["decision", "action", "tool_call"]]
        if decisions:
            key_actions = [d.get("action") or d.get("content", "")[:50] for d in decisions[:3]]
            summary_parts.extend([f"→ {a}" for a in key_actions if a])

        rollout_summary = _redact(" | ".join(summary_parts))

        # Slug: kurzes Label
        first_action = next((e.get("action") or e.get("content","") for e in relevant if e.get("action") or e.get("content")), "")
        slug_words = re.sub(r'[^a-zA-Z0-9\s]', '', first_action[:30]).strip().split()[:3]
        rollout_slug = "_".join(slug_words).lower() or session_id[:8]

        record = Stage1Record(
            session_id=session_id,
            ts=_now(),
            raw_memory=raw_memory,
            rollout_summary=rollout_summary,
            rollout_slug=rollout_slug,
        )
        record.record_hash = _hash({"sid": session_id, "raw": raw_memory[:100]})
        return record


# ─── PHASE 2: GLOBAL CONSOLIDATION ───────────────────────────────────────────

class Phase2Consolidator:
    """
    Konsolidiert Stage-1 Outputs in globale Memory-Artefakte.
    Inspiriert von: codex memories/phase2.rs

    Output:
    - cognitive_memory.md         (merged, ranked, human-readable)
    - rollout_summaries/<slug>.md (individual summaries)
    - .memory_watermark.json      (verhindert Doppel-Verarbeitung)
    """

    def __init__(self, max_memories: int = 20, max_unused_days: int = 30):
        self.max_memories = max_memories
        self.max_unused_days = max_unused_days
        self.prev_watermark = self._load_watermark()

    def _load_watermark(self) -> Dict:
        if WATERMARK.exists():
            try:
                return json.loads(WATERMARK.read_text("utf-8"))
            except:
                pass
        return {"last_ts": "", "selected_ids": []}

    def _save_watermark(self, ts: str, selected_ids: List[str]):
        WATERMARK.write_text(json.dumps({
            "last_ts": ts, "selected_ids": selected_ids,
            "updated": _now()
        }, indent=2, ensure_ascii=False), "utf-8")

    def run(self) -> Dict:
        """Phase 2: Konsolidiert alle Stage-1 Outputs."""
        # Stage-1 Records laden
        all_records: List[Stage1Record] = []
        if STAGE1.exists():
            for line in STAGE1.read_text("utf-8").splitlines():
                try:
                    d = json.loads(line)
                    r = Stage1Record(**{k: d.get(k, v)
                                       for k, v in Stage1Record.__dataclass_fields__.items()
                                       if k in d})
                    all_records.append(r)
                except:
                    pass

        if not all_records:
            con.print("  [dim]Phase 2: Keine Stage-1 Records[/dim]" if RICH
                      else "  Phase 2: keine Records")
            return {"status": "no_input"}

        # Eligibility: nicht zu alt, nach usage_count sortiert
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=self.max_unused_days)
        eligible = []
        for r in all_records:
            try:
                ts = datetime.datetime.fromisoformat(r.ts.replace("Z","+00:00"))
                if ts >= cutoff:
                    eligible.append(r)
            except:
                eligible.append(r)

        # Top-N nach usage_count (häufig genutzte Memories bleiben)
        eligible.sort(key=lambda r: (-r.usage_count, r.ts), reverse=False)
        selected = eligible[:self.max_memories]
        selected_ids = [r.session_id for r in selected]

        # Diff: added / retained / removed
        prev_ids = set(self.prev_watermark.get("selected_ids", []))
        curr_ids = set(selected_ids)
        added    = curr_ids - prev_ids
        retained = curr_ids & prev_ids
        removed  = prev_ids - curr_ids

        # Rollout Summaries schreiben
        for r in selected:
            slug_file = ROLLUPS / f"{r.rollout_slug}_{r.session_id[:8]}.md"
            slug_file.write_text(
                f"# Rollout: {r.rollout_slug}\n"
                f"**Session:** {r.session_id}  **Erstellt:** {r.ts}\n\n"
                f"## Summary\n{r.rollout_summary}\n\n"
                f"## Raw Memory\n{r.raw_memory}\n",
                encoding="utf-8"
            )

        # Veraltete Summaries entfernen (Codex prune)
        for f in ROLLUPS.glob("*.md"):
            slug = f.stem.split("_")[0] if "_" in f.stem else f.stem
            if not any(r.rollout_slug == slug for r in selected):
                f.unlink(missing_ok=True)

        # cognitive_memory.md schreiben (Hauptartefakt)
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [
            f"# 🧠 DDGK Cognitive Memory",
            f"**Generiert:** {now_str}  **Sessions:** {len(selected)}  "
            f"**Diff:** +{len(added)} /{len(retained)} −{len(removed)}\n",
            "---\n",
        ]
        for r in selected:
            diff_marker = "🟢 NEU" if r.session_id in added else "🔄 AKTUELL"
            lines.extend([
                f"## {diff_marker} [{r.rollout_slug}]",
                f"*Session: {r.session_id[:12]} | {r.ts[:10]}*\n",
                f"**Summary:** {r.rollout_summary}\n",
                f"```\n{r.raw_memory[:500]}\n```\n",
            ])
        if removed:
            lines.append(f"\n---\n### 🗑️ Entfernte Sessions: {len(removed)}")

        STAGE2.write_text("\n".join(lines), encoding="utf-8")

        # Watermark aktualisieren
        self._save_watermark(_now(), selected_ids)

        result = {
            "status":   "ok",
            "selected": len(selected),
            "added":    len(added),
            "retained": len(retained),
            "removed":  len(removed),
            "output":   str(STAGE2),
        }

        msg = (f"Phase 2: {len(selected)} Memories konsolidiert "
               f"(+{len(added)} neu, -{len(removed)} entfernt)")
        con.print(f"  🧠 {msg}" if not RICH else f"  [green]🧠 {msg}[/green]")
        return result


# ─── FULL PIPELINE ────────────────────────────────────────────────────────────

class DDGKMemoryPipeline:
    """
    2-Phasen Memory Pipeline — läuft bei jedem Session-Start.
    """

    def __init__(self):
        self.phase1 = Phase1Extractor()
        self.phase2 = Phase2Consolidator()

    def run(self, verbose: bool = True) -> Dict:
        if verbose:
            con.print("\n  [bold cyan]🧠 DDGK Memory Pipeline[/bold cyan]" if RICH
                      else "\n  DDGK Memory Pipeline")

        # Phase 1: Extraktion
        stage1_records = self.phase1.run()

        # Phase 2: Konsolidierung
        result = self.phase2.run()
        result["stage1_new"] = len(stage1_records)

        if verbose:
            con.print(f"  ✅ Pipeline fertig → {STAGE2.name}" if not RICH
                      else f"  [green]✅ Pipeline fertig → {STAGE2.name}[/green]")

        return result


if __name__ == "__main__":
    pipeline = DDGKMemoryPipeline()
    result = pipeline.run(verbose=True)
    print(f"\n  Ergebnis: {result}")
