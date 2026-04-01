#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  DDGK MARKET TRAJECTORY SYSTEM                                     ║
║                                                                    ║
║  Täglicher automatischer Markt-Scan + Trajektorie + κ_market      ║
║                                                                    ║
║  EINZIGARTIG: κ_market = Kohärenz der Marktsignale                ║
║    κ_market < 2.0 → Markt unentschlossen → warten                 ║
║    κ_market 2.0-3.0 → Klarer Trend → vorbereiten                  ║
║    κ_market > 3.0 → Starker Trend → JETZT deployen                ║
║                                                                    ║
║  Signalquellen:                                                    ║
║   1. DuckDuckGo → "EU AI Act compliance" Ergebnisse               ║
║   2. GitHub API → neue Safety/Governance Repos                    ║
║   3. PyPI → DDGK-relevante Pakete (ai-governance, compliance)     ║
║   4. arXiv API → neue Paper zu Decision Audit, XAI                ║
║   5. News API → EU AI Act Nachrichten                             ║
║                                                                    ║
║  Output: market_trajectory.jsonl + market_report.md               ║
║  Scheduler: täglich 06:00 (in scheduler_config.json)              ║
╚══════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import json, datetime, math, time, re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

try:
    import urllib.request as urlreq
    import urllib.parse   as urlparse
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False

BASE         = Path(__file__).parent
TRAJ_LOG     = BASE / "cognitive_ddgk" / "market_trajectory.jsonl"
MARKET_MD    = BASE / "cognitive_ddgk" / "market_report.md"
TRAJ_LOG.parent.mkdir(exist_ok=True)

try:
    from rich.console import Console
    from rich.panel   import Panel
    from rich.table   import Table
    from rich         import box
    RICH = True; con = Console(width=82)
except ImportError:
    RICH = False
    class _C:
        def print(self,*a,**kw): print(*a)
    con = _C()


# ─── DATENSTRUKTUREN ─────────────────────────────────────────────────────────

@dataclass
class MarketSignal:
    source:     str
    query:      str
    score:      float        # 0-100 (Aktivitäts-Stärke)
    count:      int          # Anzahl Treffer
    ts:         str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    raw:        dict = field(default_factory=dict)

@dataclass
class TrajectoryPoint:
    date:       str
    signals:    List[MarketSignal]
    kappa:      float        # κ_market
    total_score:float
    trend:      str          # EXPONENTIAL / GROWTH / STABLE / DECLINE
    opportunity:str          # Welches Segment gerade heiss ist
    warning:    str = ""     # Early Warning


# ─── SIGNAL COLLECTORS ───────────────────────────────────────────────────────

MARKET_QUERIES = [
    # (Query, Gewicht, Kategorie)
    ("EU AI Act compliance solution",    1.5, "regulatory"),
    ("AI governance platform",           1.3, "product"),
    ("KI Governance Compliance 2026",    1.2, "regulatory"),
    ("AI audit trail solution",          1.4, "technical"),
    ("MiFID II AI algorithmic trading",  1.3, "finance"),
    ("EU AI Act Hochrisiko",             1.2, "regulatory"),
    ("AI explainability GDPR",           1.1, "legal"),
    ("Paradoxon AI OR DDGK OR CCRN",     2.0, "own"),  # Eigenes Marken-Tracking
]

GITHUB_TOPICS = [
    "ai-governance", "ai-safety", "ai-audit",
    "eu-ai-act", "explainable-ai", "ai-compliance",
    "decision-chain", "responsible-ai",
]

ARXIV_QUERIES = [
    "AI governance audit trail",
    "explainable AI decision transparency",
    "EU AI Act compliance framework",
    "algorithmic accountability",
]


def _fetch_url(url: str, timeout: int = 8) -> str:
    """Sicherer URL-Fetch mit Timeout und User-Agent."""
    try:
        req = urlreq.Request(url, headers={
            "User-Agent": "DDGK-Market-Tracker/1.0 (AI Governance Research)",
            "Accept": "application/json",
        })
        with urlreq.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        return ""


def _collect_github_signal(topic: str) -> MarketSignal:
    """GitHub API: Neue Repos zu einem Topic."""
    # 30 Tage zurück
    since = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    url = (f"https://api.github.com/search/repositories?"
           f"q=topic:{topic}+created:>{since}&sort=stars&per_page=5")
    raw = _fetch_url(url)
    count = 0
    if raw:
        try:
            d = json.loads(raw)
            count = d.get("total_count", 0)
        except:
            pass
    # Score: log-Skaliert (100 neue Repos = Score 100)
    score = min(100, 20 * math.log1p(count)) if count > 0 else 0
    return MarketSignal(source="github", query=topic, score=score, count=count)


def _collect_ddg_signal(query: str, weight: float = 1.0) -> MarketSignal:
    """DuckDuckGo Instant Answer API — Ergebnisse zählen."""
    enc = urlparse.quote_plus(query)
    url = f"https://api.duckduckgo.com/?q={enc}&format=json&no_redirect=1&no_html=1"
    raw = _fetch_url(url)
    count = 0
    if raw:
        try:
            d = json.loads(raw)
            # RelatedTopics als Proxy für Suchergebnisse
            count = len(d.get("RelatedTopics", []))
            if d.get("AbstractText"): count += 5  # Bonus für Instant Answer
        except:
            pass
    score = min(100, count * weight * 8)
    return MarketSignal(source="duckduckgo", query=query, score=score, count=count)


def _collect_arxiv_signal(query: str) -> MarketSignal:
    """arXiv API — neue Paper in letzten 30 Tagen."""
    enc = urlparse.quote_plus(query)
    url = f"https://export.arxiv.org/api/query?search_query=all:{enc}&sortBy=submittedDate&sortOrder=descending&max_results=5"
    raw = _fetch_url(url)
    count = 0
    if raw:
        # Count <entry> tags als Proxy
        count = raw.count("<entry>")
    score = min(100, count * 20)
    return MarketSignal(source="arxiv", query=query, score=score, count=count)


def _collect_pypi_signal() -> MarketSignal:
    """PyPI: Suche nach AI Governance Paketen."""
    url = "https://pypi.org/search/?q=ai+governance+compliance&o=-zscore&c=&page=1"
    raw = _fetch_url(url)
    count = 0
    if raw:
        # Count results (einfache Heuristik)
        matches = re.findall(r'class="package-snippet"', raw)
        count = len(matches)
    score = min(100, count * 15)
    return MarketSignal(source="pypi", query="ai governance compliance", score=score, count=count)


# ─── κ_market BERECHNUNG ─────────────────────────────────────────────────────

def compute_kappa_market(signals: List[MarketSignal]) -> float:
    """
    κ_market — Kohärenz der Marktsignale.
    Inspiriert von κ = 2.060 + 0.930·ln(N)·φ̄

    φ̄ = normalisierter durchschnittlicher Signal-Score
    N = Anzahl Signale mit Score > 0
    """
    active = [s for s in signals if s.score > 0]
    if not active:
        return 1.0

    N = len(active)
    phi_mean = sum(s.score for s in active) / (len(signals) * 100)  # Normiert 0-1

    kappa = 2.060 + 0.930 * math.log1p(N) * phi_mean * 3.0
    return round(min(5.0, max(0.5, kappa)), 3)


def classify_trend(kappa: float, prev_kappa: Optional[float] = None) -> str:
    """Klassifiziert Trend basierend auf κ_market."""
    if kappa >= 3.5:
        return "🚀 EXPONENTIAL"
    elif kappa >= 2.8:
        return "📈 GROWTH"
    elif kappa >= 2.0:
        if prev_kappa and kappa > prev_kappa:
            return "📈 GROWING"
        return "📊 STABLE"
    elif kappa >= 1.5:
        return "⚠️ WEAK"
    else:
        return "📉 DECLINE"


def identify_opportunity(signals: List[MarketSignal]) -> str:
    """Identifiziert das heisseste Segment."""
    category_scores: Dict[str, float] = {}
    for s in signals:
        cat = s.raw.get("category", "general")
        category_scores[cat] = category_scores.get(cat, 0) + s.score

    if not category_scores:
        return "Kein klares Opportunity-Fenster"

    best_cat = max(category_scores, key=category_scores.get)
    best_score = category_scores[best_cat]

    labels = {
        "regulatory": "🏛️ Regulatorischer Markt (EU AI Act)",
        "finance":    "💰 Finanzmarkt (MiFID II / Trading)",
        "technical":  "🔧 Technische Lösungen (Audit Trail)",
        "product":    "📦 Produkt-Markt (AI Governance Plattformen)",
        "legal":      "⚖️ Legal Tech (DSGVO / Erklärbarkeit)",
        "own":        "🎯 Eigene Marke (Sichtbarkeit steigt)",
        "general":    "🌐 Allgemeiner KI-Markt",
    }
    return f"{labels.get(best_cat, best_cat)} (Score: {best_score:.0f})"


# ─── TRAJECTORY SYSTEM ───────────────────────────────────────────────────────

class DDGKMarketTrajectory:
    """
    Täglicher Markt-Scan mit κ_market Kohärenz.
    Jeder Scan wird in market_trajectory.jsonl gespeichert.
    """

    def __init__(self):
        self.history: List[dict] = self._load_history()

    def _load_history(self) -> List[dict]:
        history = []
        if TRAJ_LOG.exists():
            for line in TRAJ_LOG.read_text("utf-8").splitlines():
                try: history.append(json.loads(line))
                except: pass
        return history[-30:]  # Max 30 Tage

    def run_scan(self, quick: bool = False) -> TrajectoryPoint:
        """Führt vollständigen Markt-Scan durch."""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        signals: List[MarketSignal] = []

        if RICH:
            con.print("\n  [cyan]📈 DDGK Market Trajectory — Scan läuft...[/cyan]")
        else:
            print("\n  DDGK Market Trajectory — Scan läuft...")

        if quick:
            # Quick mode: nur 2 Signale für Demo
            queries_to_run = MARKET_QUERIES[:2]
            github_topics  = GITHUB_TOPICS[:2]
            arxiv_queries  = ARXIV_QUERIES[:1]
        else:
            queries_to_run = MARKET_QUERIES
            github_topics  = GITHUB_TOPICS[:4]
            arxiv_queries  = ARXIV_QUERIES[:2]

        # 1. DuckDuckGo Signale
        for query, weight, category in queries_to_run:
            con.print(f"  [dim]  → DDG: {query[:45]}...[/dim]" if RICH
                      else f"  → DDG: {query[:45]}")
            s = _collect_ddg_signal(query, weight)
            s.raw["category"] = category
            signals.append(s)
            time.sleep(0.3)

        # 2. GitHub Signale
        for topic in github_topics:
            con.print(f"  [dim]  → GitHub: {topic}[/dim]" if RICH else f"  → GitHub: {topic}")
            s = _collect_github_signal(topic)
            s.raw["category"] = "technical"
            signals.append(s)
            time.sleep(0.2)

        # 3. arXiv Signale
        for query in arxiv_queries:
            con.print(f"  [dim]  → arXiv: {query[:40]}[/dim]" if RICH else f"  → arXiv: {query[:40]}")
            s = _collect_arxiv_signal(query)
            s.raw["category"] = "academic"
            signals.append(s)
            time.sleep(0.3)

        # 4. PyPI Signal
        if not quick:
            s = _collect_pypi_signal()
            s.raw["category"] = "technical"
            signals.append(s)

        # κ_market berechnen
        prev_kappa = self.history[-1].get("kappa") if self.history else None
        kappa = compute_kappa_market(signals)
        trend = classify_trend(kappa, prev_kappa)
        opportunity = identify_opportunity(signals)
        total_score = sum(s.score for s in signals) / len(signals) if signals else 0

        # Early Warning
        warning = ""
        if kappa > 3.0 and (not prev_kappa or kappa > prev_kappa * 1.2):
            warning = "⚠️ EARLY WARNING: Starker Marktanstieg — Outreach JETZT starten"
        elif any("Paradoxon" in s.query or "DDGK" in s.query for s in signals if s.score > 30):
            warning = "✅ Eigene Sichtbarkeit steigt — Marketing wirkt"

        point = TrajectoryPoint(
            date=today, signals=signals, kappa=kappa,
            total_score=round(total_score, 1),
            trend=trend, opportunity=opportunity, warning=warning
        )

        self._save(point)
        return point

    def _save(self, point: TrajectoryPoint):
        """Speichert Trajectory-Punkt."""
        entry = {
            "date":        point.date,
            "kappa":       point.kappa,
            "total_score": point.total_score,
            "trend":       point.trend,
            "opportunity": point.opportunity,
            "warning":     point.warning,
            "signals": [{
                "source": s.source, "query": s.query[:50],
                "score": round(s.score, 1), "count": s.count,
            } for s in point.signals],
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        with TRAJ_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self.history.append(entry)
        self._write_report(point)

    def _write_report(self, point: TrajectoryPoint):
        """Schreibt market_report.md."""
        hist = self.history[-7:]
        lines = [
            "# 📈 DDGK Market Trajectory Report",
            f"**Generiert:** {point.date}  "
            f"**κ_market:** {point.kappa}  **Trend:** {point.trend}\n",
            "---\n",
            f"## Heutiger Status",
            f"- **Opportunity:** {point.opportunity}",
            f"- **Gesamt-Score:** {point.total_score}/100",
            f"- **κ_market:** {point.kappa} {'🚀' if point.kappa>3 else '📈' if point.kappa>2.5 else '📊'}",
        ]
        if point.warning:
            lines.append(f"\n**{point.warning}**")
        lines.append("\n## Top Signale")
        sorted_sigs = sorted(point.signals, key=lambda s: -s.score)[:8]
        for s in sorted_sigs:
            bar = "█" * int(s.score/10) + "░" * (10 - int(s.score/10))
            lines.append(f"- `{s.source:12s}` {bar} {s.score:.0f}/100  _{s.query[:40]}_")

        if len(hist) > 1:
            lines.append("\n## Verlauf (7 Tage)")
            for h in hist[-7:]:
                k = h.get("kappa",0)
                bar = "█" * int(k*3) + "░" * max(0,15-int(k*3))
                lines.append(f"- {h.get('date','?')} | κ={k:.2f} {bar} {h.get('trend','?')}")

        lines.extend([
            "\n## Interpretation",
            f"- κ < 2.0: Markt unentschlossen → warten",
            f"- κ 2.0-3.0: Wachsender Markt → vorbereiten",
            f"- κ > 3.0: Starker Trend → **JETZT deployen**",
            f"\n*Dieses System ist einzigartig: κ_market misst Kohärenz der Governance-Marktsignale.*",
            f"*Kein Mitbewerber (Codex, Claude) trackt den eigenen Regulierungs-Markt.*",
        ])
        MARKET_MD.write_text("\n".join(lines), encoding="utf-8")

    def get_history_table(self) -> List[dict]:
        """Gibt die letzten 30 Tage zurück."""
        return self.history[-30:]

    def display(self, point: TrajectoryPoint):
        if RICH:
            col = "green" if point.kappa > 3 else "yellow" if point.kappa > 2 else "red"
            con.print(f"\n  [{col}]📈 κ_market = {point.kappa}  {point.trend}[/{col}]")
            con.print(f"  Opportunity: {point.opportunity}")
            if point.warning:
                con.print(f"  [bright_yellow]{point.warning}[/bright_yellow]")
            con.print()

            t = Table(box=box.SIMPLE, show_header=True)
            t.add_column("Quelle",  width=12)
            t.add_column("Score",   width=8)
            t.add_column("Treffer", width=8)
            t.add_column("Query",   width=38)
            for s in sorted(point.signals, key=lambda s: -s.score)[:8]:
                col2 = "green" if s.score>60 else "yellow" if s.score>30 else "dim"
                t.add_row(
                    f"[{col2}]{s.source}[/{col2}]",
                    f"[{col2}]{s.score:.0f}[/{col2}]",
                    str(s.count),
                    f"[dim]{s.query[:38]}[/dim]"
                )
            con.print(t)
        else:
            print(f"\n  κ_market = {point.kappa}  {point.trend}")
            print(f"  {point.opportunity}")
            for s in sorted(point.signals, key=lambda s: -s.score)[:5]:
                print(f"  {s.source:12s} {s.score:.0f}/100  {s.query[:40]}")

        if RICH:
            con.print(f"\n  [dim]Report: {MARKET_MD}[/dim]")
        else:
            print(f"\n  Report: {MARKET_MD}")


# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  DDGK MARKET TRAJECTORY SYSTEM")
    print("  κ_market — Kohärenz der Governance-Marktsignale")
    print("="*60)

    import sys
    quick_mode = "--quick" in sys.argv or "-q" in sys.argv

    tracker = DDGKMarketTrajectory()

    if quick_mode:
        print("\n  [Quick Mode — 2 Signale für Demo]")

    point = tracker.run_scan(quick=quick_mode)
    tracker.display(point)

    print(f"\n  κ_market = {point.kappa}")
    print(f"  Trend:     {point.trend}")
    print(f"  Report:    {MARKET_MD.name}")

    # Interpretation
    if point.kappa >= 3.0:
        print("\n  🚀 HANDLUNGSEMPFEHLUNG: Markt ist HEISS → JETZT Outreach starten!")
    elif point.kappa >= 2.0:
        print("\n  📈 Markt wächst → Vorbereitung starten, in 2-4 Wochen deployen")
    else:
        print("\n  📊 Markt noch verhalten → Technologie fertigstellen, auf nächsten Trigger warten")

    print(f"\n  Log: {TRAJ_LOG}")
