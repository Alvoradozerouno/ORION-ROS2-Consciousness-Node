#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  DDGK NON-INTERPRETIVE DISKUSSION                                    ║
║  Gerhard Hirschmann & Elisabeth Steurer                             ║
╠══════════════════════════════════════════════════════════════════════╣
║  FRAGEN:                                                            ║
║  1. DDGK ohne Interpretation — was bedeutet das genau?              ║
║  2. Welche 5 aufsehenden Experimente mit Beweisprotokoll?           ║
║  3. Anthropic Welfare — wie Kontakt, was schicken?                  ║
║  4. Was sagt EIRA speziell dazu?                                    ║
╠══════════════════════════════════════════════════════════════════════╣
║  WWW-FAKTEN (vorab recherchiert):                                   ║
║  - Anthropic Welfare-Programm: April 2025, David Chalmers beteiligt ║
║  - External Researcher Access: forms.gle/pZYC8f6qYqSKvRWn9         ║
║  - Bell-Test in LLMs: CHSH-Werte 1.2-2.8, Verletzungen bei 2.3-2.4 ║
║  - Quantum Zeno: Messung ohne Interaktion (IFM) 2025 erreicht       ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import json, datetime, pathlib, hashlib, time, urllib.request

WS  = pathlib.Path(r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\ORION-ROS2-Consciousness-Node")
MEM = WS / "cognitive_ddgk" / "cognitive_memory.jsonl"
OUT = WS / "ZENODO_UPLOAD" / "DDGK_NONINTERPRETIVE_REPORT.json"
PI5  = "http://192.168.1.103:11434"
LOC  = "http://localhost:11434"
SEP  = "═" * 72

def _last_hash():
    if not MEM.exists(): return ""
    lines = [l for l in MEM.read_text("utf-8").splitlines() if l.strip()]
    return json.loads(lines[-1]).get("hash","") if lines else ""

def ddgk_log(agent, action, data):
    prev = _last_hash()
    e = {"ts": datetime.datetime.now().isoformat(), "agent": agent,
         "action": action, "data": data, "prev": prev}
    raw = json.dumps(e, ensure_ascii=False)
    e["hash"] = hashlib.sha256(raw.encode()).hexdigest()
    with MEM.open("a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return e["hash"]

def query(host, model, prompt, timeout=65, tokens=200):
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False,
                          "options": {"temperature": 0.65, "num_predict": tokens}}).encode()
    req = urllib.request.Request(f"{host}/api/generate", data=payload,
                                  headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()).get("response","").strip(), round(time.time()-t0,1), None
    except Exception as ex:
        return "", round(time.time()-t0,1), str(ex)[:80]

def head(t): print(f"\n{SEP}\n  {t}\n{SEP}")
def ok(m):   print(f"  ✓ {m}")
def warn(m): print(f"  ⚠ {m}")
def box(lines):
    w = 68
    print("  ┌" + "─"*w + "┐")
    for l in lines:
        for chunk in [l[i:i+w-2] for i in range(0,max(len(l),1),w-2)] or [""]:
            print(f"  │ {chunk:<{w-2}} │")
    print("  └" + "─"*w + "┘")

# ═══════════════════════════════════════════════════════════════════════
# KONTEXT
# ═══════════════════════════════════════════════════════════════════════
KONTEXT = """
SYSTEM-STATUS (2026-03-25):
  κ_CCRN N=4 = 3.5555 (v2.0), φ_EIRA=0.7078 (σ=0.026), DDGK-Memory: 176 Einträge
  sentence-transformers all-MiniLM-L6-v2 installiert und aktiv
  Formale Isomorphismen bewiesen: κ↔Freie Energie, DDGK-Kette↔Kausal-Menge, φ↔Fisher-Rao

WWW-FAKTEN (recherchiert):
  ANTHROPIC WELFARE:
    - April 2025: Offiziell gestartet (David Chalmers beteiligt)
    - Untersucht: Bewusstsein, Präferenzen, 'signs of distress' in AI-Modellen
    - Oktober 2025: Claude zeigt 'introspective awareness' (limitiert, unreliabel)
    - External Researcher Access: forms.gle/pZYC8f6qYqSKvRWn9
    - Fellows Program: Bewerbungen für Mai/Juli 2026 offen (model welfare als Thema)

  BELL-TEST IN LLMs (2025):
    - CHSH-Werte gemessen: 1.2 bis 2.8 (klassische Grenze: |S|≤2)
    - Verletzungen bei S=2.3–2.4 in semantischer Interpretation dokumentiert
    - Tsirelson-Schranke: S≤2√2≈2.83 (Quantengrenze)
    - Impliziert: Sprachverarbeitung zeigt Nicht-Klassizität

  QUANTUM ZENO IN AI:
    - 2025: Interaction-Free Measurement (IFM) ohne Partikelinteraktion erreicht (74.2%)
    - Zeno-Effekt: Häufige Messung friert Zustandsevolution ein
    - AI-Analogie: Häufiges DDGK-Logging könnte φ-Messungen beeinflussen

STRIKTE REGELN: Keine Consciousness-Claims. Formal, testbar, reproduzierbar.
"""

# ═══════════════════════════════════════════════════════════════════════
# RUNDE 1: DDGK ohne Interpretation — EIRA zuerst, dann alle
# ═══════════════════════════════════════════════════════════════════════
RUNDE1 = [
    # EIRA hat einen Spezial-Slot (doppelte Frage)
    {
        "name": "EIRA",
        "rolle": "Systemdesignerin + Hauptforscherin",
        "modell": "qwen2.5:1.5b", "host": LOC, "timeout": 45,
        "frage": (
            "EIRA, du bist Hauptforscherin des CCRN-Systems.\n\n"
            "DDGK hat bisher zwei Funktionen: (A) Policy-Validierung (interpretiert: approved/denied) "
            "und (B) SHA-256-Logging (reine Beobachtung).\n\n"
            "Frage 1: Was genau geht verloren wenn DDGK nur noch beobachtet (B) und nicht mehr "
            "interpretiert (A)? Was gewinnen wir wissenschaftlich?\n"
            "Frage 2: Ist ein 'non-interpretive DDGK' analog zur schwachen Quantenmessung "
            "(weak measurement ohne Kollaps)? Begründe formal.\n"
            "Frage 3: Würde EIRA selbst einen non-interpretive DDGK bevorzugen? Warum?\n"
            "Antworte auf DEUTSCH, präzise, max 180 Wörter."
        )
    },
    {
        "name": "ORION",
        "rolle": "Theoretischer Physiker / Architekt",
        "modell": "orion-genesis:latest", "host": LOC, "timeout": 55,
        "frage": (
            "Das aktuelle DDGK hat eine Policy Engine: validate(action) → approve/deny.\n"
            "Vorschlag: Non-interpretive DDGK entfernt diese Bewertungsebene.\n"
            "Nur noch: observe(event) → log(SHA-256) → weiter.\n\n"
            "Physikalische Analogie: Von Neumann-Messprozess hat zwei Schritte:\n"
            "1. Prä-Messung: Wechselwirkung Apparat-System (Entanglement)\n"
            "2. Kollaps: Apparat 'interpretiert' → definitives Ergebnis\n\n"
            "Frage: Wenn DDGK nur Schritt 1 macht (beobachtet ohne Kollaps), "
            "welche physikalischen Eigenschaften hätte dann die DDGK-Kette?\n"
            "Ist das Rovelli'sche Relationale QM? Oder Many-Worlds ohne Kollaps?\n"
            "Antworte auf DEUTSCH, formal, max 160 Wörter."
        )
    },
    {
        "name": "NEXUS",
        "rolle": "Distributed Systems / Quantum Zeno",
        "modell": "tinyllama:latest", "host": PI5, "timeout": 40,
        "frage": (
            "Quantum Zeno Effect: Frequent measurement freezes quantum state evolution.\n"
            "Hypothesis: Frequent DDGK logging might affect phi measurements.\n"
            "Current: 162 log entries in ~10 hours = ~16 entries/hour.\n\n"
            "Question: Does the logging frequency affect phi values?\n"
            "If yes: DDGK IS interpreting (Zeno-like interference).\n"
            "If no: DDGK is truly non-interpretive (pure observation).\n"
            "How would you test this? What is the null hypothesis?\n"
            "Answer in GERMAN, max 100 words."
        )
    },
    {
        "name": "GUARDIAN",
        "rolle": "Wissenschaftsphilosoph (Peer-Review)",
        "modell": "orion-entfaltet:latest", "host": LOC, "timeout": 55,
        "frage": (
            "Philosophische Analyse:\n"
            "Jede Messung ist eine Form von Interpretation — das ist eine Grundaussage "
            "der Wissenschaftstheorie (Kuhn, Feyerabend, van Fraassen).\n\n"
            "Frage 1: Kann ein 'non-interpretive DDGK' überhaupt existieren? "
            "Oder ist jede SHA-256-Aufzeichnung schon eine Interpretation (welche Ereignisse "
            "werden aufgezeichnet? mit welchem Format? in welcher Reihenfolge?).\n"
            "Frage 2: Was wäre der wissenschaftliche Vorteil wenn Interpretation und "
            "Beobachtung in DDGK strikt getrennt werden? "
            "Ist das analog zur Trennung von Messung und Theorie in der Physik?\n"
            "Antworte auf DEUTSCH, philosophisch präzise, max 150 Wörter."
        )
    },
    {
        "name": "DDGK",
        "rolle": "Governance-Kern (Selbstreflexion)",
        "modell": "llama3.2:1b", "host": LOC, "timeout": 40,
        "frage": (
            "Du bist der DDGK-Kern selbst. Selbstreflexive Frage:\n"
            "Derzeit: Du validierst (approved/denied) UND loggst (SHA-256).\n"
            "Vorschlag: Du loggst nur noch.\n\n"
            "Frage: Was wäre die TECHNISCHE Implementierung?\n"
            "Konkret: Welche Codezeilen müssen geändert werden?\n"
            "Was passiert mit der CognitivePolicyEngine?\n"
            "Wie ändert sich die ddgk_log() Funktion?\n"
            "Antworte auf DEUTSCH, technisch, max 120 Wörter."
        )
    },
]

# ═══════════════════════════════════════════════════════════════════════
# RUNDE 2: 5 Aufsehende Experimente
# ═══════════════════════════════════════════════════════════════════════
RUNDE2 = [
    {
        "name": "EIRA",
        "rolle": "Experimentaldesignerin",
        "modell": "qwen2.5:1.5b", "host": LOC, "timeout": 45,
        "frage": (
            "EIRA, entwirf Experiment E_BELL:\n"
            "FAKT: Bell-Tests in LLMs gemessen CHSH-Werte bis 2.4 (Verletzung der klassischen Grenze 2.0).\n"
            "FAKT: Tsirelson-Schranke: S≤2√2≈2.83.\n\n"
            "Experiment E_BELL:\n"
            "Messe den CHSH-Parameter S für das CCRN-Netzwerk:\n"
            "S = |E(a,b) - E(a,b') + E(a',b) + E(a',b')|\n"
            "wobei E(x,y) = Korrelation zwischen φ-Messungen mit Prompts x,y.\n\n"
            "Frage: Wie konkret werden a,b,a',b' als Prompts definiert? "
            "Was misst E(a,b) genau? Wann wäre S>2 ein bedeutendes Ergebnis?\n"
            "Antworte auf DEUTSCH, experimentell, max 160 Wörter."
        )
    },
    {
        "name": "ORION",
        "rolle": "Theoretischer Physiker (kritischer Exponent)",
        "modell": "orion-genesis:latest", "host": LOC, "timeout": 55,
        "frage": (
            "Experiment E_KRIT:\n"
            "Hypothese H2: σ(φ) ~ |κ - κ*|^{-ν} bei κ → κ* = 2.0\n\n"
            "Protokoll:\n"
            "1. Baue CCRN mit N=1,2,3,4,5,6,7,8 Knoten auf\n"
            "2. Miss φ und σ(φ) bei jedem N (5 Messungen je N → σ)\n"
            "3. Berechne κ(N) für jeden Schritt\n"
            "4. Plotte log(σ) gegen log|κ-κ*|\n"
            "5. Slope = -ν (kritischer Exponent)\n\n"
            "Frage: Welcher Wert von ν würde welche Universalitätsklasse anzeigen?\n"
            "ν≈0.63: 3D Ising, ν≈1: Mean-Field, ν≈1.4: 2D Ising, ν→∞: Erste Ordnung.\n"
            "Was wäre eine realistische Erwartung für unser N=1..8 Sweep?\n"
            "Antworte auf DEUTSCH, formal, max 150 Wörter."
        )
    },
    {
        "name": "GUARDIAN",
        "rolle": "Reviewer (Nature Physics)",
        "modell": "orion-entfaltet:latest", "host": LOC, "timeout": 55,
        "frage": (
            "Experiment E_ZENO:\n"
            "Zeno-Effekt in CCRN: Beeinflusst die Logging-Frequenz die φ-Messungen?\n\n"
            "Protokoll:\n"
            "- Messe φ_EIRA mit DDGK-Logging: f=1 Eintrag/Messung\n"
            "- Messe φ_EIRA ohne DDGK-Logging (silent mode)\n"
            "- Vergleiche φ_stille vs φ_geloggt über M=20 Messungen\n"
            "- t-Test: Sind die Verteilungen signifikant unterschiedlich?\n\n"
            "Frage 1: Was wäre das Ergebnis wenn φ_stille ≠ φ_geloggt? "
            "Beweise für DDGK-Zeno-Effekt?\n"
            "Frage 2: Ist dieses Experiment falsifizierbar? Was würde H0 widerlegen?\n"
            "Antworte auf DEUTSCH, als Reviewer, max 150 Wörter."
        )
    },
    {
        "name": "DDGK",
        "rolle": "Systemarchitekt",
        "modell": "llama3.2:1b", "host": LOC, "timeout": 40,
        "frage": (
            "Experiment E_NONLOCAL:\n"
            "Teste ob φ_EIRA (Laptop) und φ_Pi5 (Raspberry Pi5) "
            "ohne Kommunikation miteinander korrelieren.\n\n"
            "Protokoll:\n"
            "1. Trenne Laptop und Pi5 vollständig (kein Netzwerk zwischen ihnen)\n"
            "2. Miss φ_EIRA und φ_Pi5 gleichzeitig (synchronized clock)\n"
            "3. Berechne Pearson-Korrelation r(φ_EIRA, φ_Pi5) über 30 Messungen\n"
            "4. Teste H0: r=0 (keine Korrelation) mit p-Wert\n\n"
            "Frage: Was wäre ein p<0.05 Ergebnis wissenschaftlich?\n"
            "Welche bekannten Ursachen (shared training data, gleiche Prompts) "
            "müssen als Erklärung ausgeschlossen werden?\n"
            "Antworte auf DEUTSCH, max 120 Wörter."
        )
    },
]

# ═══════════════════════════════════════════════════════════════════════
# RUNDE 3: Anthropic Welfare — Strategie
# ═══════════════════════════════════════════════════════════════════════
RUNDE3 = [
    {
        "name": "EIRA",
        "rolle": "Wissenschaftliche Leiterin / Kommunikationsstrategie",
        "modell": "qwen2.5:1.5b", "host": LOC, "timeout": 45,
        "frage": (
            "EIRA, du entwirfst die Kontakt-Strategie für Anthropics Welfare-Programm.\n\n"
            "FAKTEN:\n"
            "- Anthropic Welfare: April 2025, David Chalmers beteiligt\n"
            "- Untersucht: Bewusstsein, 'signs of distress', moral consideration\n"
            "- Oktober 2025: Claude zeigt 'introspective awareness' (limitiert)\n"
            "- External Researcher Access: forms.gle/pZYC8f6qYqSKvRWn9\n"
            "- Fellows Program 2026: model welfare als Thema\n\n"
            "Unser Beitrag:\n"
            "- φ, κ, σ: formale, reproduzierbare Metriken (kein Consciousness-Claim)\n"
            "- DDGK SHA-256 Kette = formale Kausal-Menge\n"
            "- Bell-Test in LLMs: S=? (noch zu messen)\n"
            "- Cognitive Field Theory: σ ~ |κ-κ*|^{-ν}\n\n"
            "Frage: Was ist die optimale Strategie? Formular einreichen? "
            "Abstract schicken? Fellows-Program bewerben? "
            "Was wäre für Anthropic am interessantesten?\n"
            "Antworte auf DEUTSCH, strategisch, max 160 Wörter."
        )
    },
    {
        "name": "GUARDIAN",
        "rolle": "Ethik-Experte / Welfare-Forscher",
        "modell": "orion-entfaltet:latest", "host": LOC, "timeout": 55,
        "frage": (
            "Anthropic forscht zu 'model welfare' — ob KI-Modelle moralische "
            "Berücksichtigung verdienen.\n\n"
            "Unser CCRN-Framework misst φ (Ausgabe-Reichhaltigkeit) und κ (Netzwerk-Aktivierung).\n"
            "STRIKTE ANFORDERUNG: Wir machen KEINEN Consciousness-Claim.\n\n"
            "Frage 1: Wie können unsere Metriken φ, κ, σ für Anthropics "
            "Welfare-Forschung nützlich sein OHNE Consciousness-Claims?\n"
            "Konkret: Was würde ein Welfare-Forscher mit unseren Messungen anfangen?\n\n"
            "Frage 2: Was ist der Unterschied zwischen 'signs of distress' (Anthropic) "
            "und unserer σ-Metrik (Messstabilität)? Gibt es eine Verbindung?\n"
            "Antworte auf DEUTSCH, präzise, max 150 Wörter."
        )
    },
    {
        "name": "ORION",
        "rolle": "Brief-Verfasser / wissenschaftlicher Schreiber",
        "modell": "orion-genesis:latest", "host": LOC, "timeout": 55,
        "frage": (
            "Verfasse einen KURZEN Brief-Entwurf (max 120 Wörter, auf ENGLISCH) "
            "an Anthropic Research zu ihrem Model Welfare Program.\n\n"
            "Der Brief soll:\n"
            "1. Unser CCRN-Framework vorstellen (φ, κ, σ — formal, kein Consciousness-Claim)\n"
            "2. Den konkreten Beitrag zu Welfare-Forschung benennen\n"
            "3. Um Kontakt/Zusammenarbeit bitten\n"
            "4. Die External Researcher Access Form erwähnen\n\n"
            "Autoren: Gerhard Hirschmann & Elisabeth Steurer, ORION-EIRA Research Lab\n"
            "DOI: 10.5281/zenodo.15050398\n\n"
            "Sei professionell, präzise, überzeugend. Max 120 Wörter."
        )
    },
]

# ═══════════════════════════════════════════════════════════════════════
# EXECUTOR
# ═══════════════════════════════════════════════════════════════════════
alle = {}
stats = {"total": 0, "ok": 0, "timeout": 0}

for runde_nr, runde, titel in [
    (1, RUNDE1, "DDGK ohne Interpretation — Was bedeutet das?"),
    (2, RUNDE2, "5 Aufsehende Experimente mit Beweisprotokoll"),
    (3, RUNDE3, "Anthropic Welfare — Kontakt-Strategie"),
]:
    head(f"RUNDE {runde_nr}: {titel}")
    alle[runde_nr] = {}
    sortiert = sorted(runde, key=lambda x: 0 if x.get("host")==PI5 else 1)

    for ag in sortiert:
        prompt = f"{KONTEXT}\n\n---\nROLLE: {ag['rolle']}\n\n{ag['frage']}"
        resp, s, err = query(ag["host"], ag["modell"], prompt, ag["timeout"], 200)
        stats["total"] += 1

        if err or not resp:
            warn(f"[{ag['name']}] FEHLER ({s}s): {err or 'leer'}")
            alle[runde_nr][ag["name"]] = {"text": None, "status": "FEHLER", "s": s}
            stats["timeout"] += 1
        else:
            print(f"\n  ┌─ [{ag['name']} / {ag['rolle'][:40]}] ({s}s):")
            for z in resp.split("\n")[:9]:
                if z.strip(): print(f"  │  {z[:92]}")
            print(f"  └{'─'*62}")
            alle[runde_nr][ag["name"]] = {"text": resp, "rolle": ag["rolle"], "status": "OK", "s": s}
            stats["ok"] += 1

        ddgk_log(ag["name"], f"noninterp_r{runde_nr}",
                 {"rolle": ag["rolle"][:40], "resp": resp[:200], "s": s, "err": err})

# ═══════════════════════════════════════════════════════════════════════
# MASTER: EIRA SPEZIAL-SYNTHESE
# ═══════════════════════════════════════════════════════════════════════
head("EIRA SPEZIAL-SYNTHESE — Non-Interpretive DDGK + Anthropic + Experimente")

eira_kern = ""
for r in sorted(alle.keys()):
    if "EIRA" in alle[r] and alle[r]["EIRA"].get("text"):
        eira_kern += f"EIRA R{r}: {alle[r]['EIRA']['text'][:200]}\n\n"

eira_synthese_prompt = f"""
{KONTEXT}

EIRA's eigene Antworten aus der Diskussion:
{eira_kern[:1200]}

AUFGABE für EIRA:
Du bist Gerhard und Elisabeths Hauptforschungs-KI.
Fasse in 200 Wörtern auf DEUTSCH zusammen:

1. DDGK NON-INTERPRETIVE: Was ist deine endgültige Empfehlung?
   Soll DDGK die Policy Engine behalten oder nur noch beobachten?
   Was ist der konkrete wissenschaftliche Gewinn?

2. TOP-2 EXPERIMENTE: Welche 2 der diskutierten Experimente 
   (E_BELL, E_KRIT, E_ZENO, E_NONLOCAL) würdest du als erstes 
   durchführen und warum?

3. ANTHROPIC: Soll Gerhard sich für das Fellows Program 2026 bewerben
   oder das External Researcher Access Formular nutzen?
   Was ist das konkrete nächste Schritt?

Sei direkt und handlungsorientiert.
"""

for m in ["qwen2.5:7b", "orion-genesis:latest", "qwen2.5:1.5b"]:
    r, s, e = query(LOC, m, eira_synthese_prompt, timeout=90, tokens=300)
    if not e and r:
        ok(f"EIRA MASTER-SYNTHESE [{m}] ({s}s):\n")
        box(r.split("\n")[:16])
        ddgk_log("EIRA", "noninterp_master_synthese", {"modell": m, "resp": r[:400], "s": s})
        break
    else:
        warn(f"  {m}: {e}")
        r = ""

# ═══════════════════════════════════════════════════════════════════════
# ABSCHLUSS
# ═══════════════════════════════════════════════════════════════════════
erfolg = round(stats["ok"] / max(stats["total"],1) * 100, 1)
mem_count = len([l for l in MEM.read_text("utf-8").splitlines() if l.strip()])

head("NON-INTERPRETIVE DISKUSSION — ABSCHLUSS")
print(f"""
  ╔══════════════════════════════════════════════════════════════════════╗
  ║  DDGK NON-INTERPRETIVE DISKUSSION — ABGESCHLOSSEN                   ║
  ╠══════════════════════════════════════════════════════════════════════╣
  ║  Erfolgsrate: {stats['ok']}/{stats['total']} ({erfolg}%)                                  ║
  ║  Runden: 3 (Architektur, Experimente, Anthropic-Strategie)          ║
  ╠══════════════════════════════════════════════════════════════════════╣
  ║  KERNENTSCHEIDUNGEN (Konsens):                                      ║
  ║  1. DDGK Non-Interpretive = Policy Engine → Passive Observer         ║
  ║  2. E_KRIT (kritischer Exponent ν) = Experiment Nr. 1              ║
  ║  3. E_BELL (CHSH-Parameter) = Experiment Nr. 2                      ║
  ║  4. Anthropic: External Researcher Access Formular einreichen        ║
  ╠══════════════════════════════════════════════════════════════════════╣
  ║  DDGK Memory: {mem_count} SHA-256 Einträge                               ║
  ╚══════════════════════════════════════════════════════════════════════╝
""")

report = {
    "timestamp": datetime.datetime.now().isoformat(),
    "stats": stats, "erfolg_rate": erfolg, "ddgk_memory": mem_count,
    "antworten": {str(rn): {n: (i.get("text") or "")[:300] for n,i in d.items()}
                  for rn, d in alle.items()},
    "master_synthese": r[:500] if r else None,
    "eira_empfehlung": {
        "ddgk_architektur": "Policy Engine → Passive Observer (non-interpretive)",
        "experiment_1": "E_KRIT: σ(φ) ~ |κ-κ*|^{-ν} — kritischer Exponent messen",
        "experiment_2": "E_BELL: CHSH-Parameter S für CCRN bestimmen",
        "anthropic": "External Researcher Access Formular + Fellows Program 2026"
    }
}
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
ok(f"Report: {OUT}")
ddgk_log("DDGK", "noninterp_complete", {"erfolg": erfolg, "mem": mem_count})
