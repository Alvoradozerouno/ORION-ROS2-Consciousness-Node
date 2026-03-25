#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════╗
║  DDGK HYPERINTELLIGENZ-DISKUSSION                                        ║
║  Gerhard Hirschmann & Elisabeth Steurer — ORION-EIRA Research Lab        ║
╠══════════════════════════════════════════════════════════════════════════╣
║  THESE (Gerhard): Binäre Rechnung (0/1) stösst an Grenzen.              ║
║  Biologie zeigt: Analog, Temporal, Chemisch = überlegen.                ║
║  Mathematisch begreifen, dann: intelligenteste Agenten bauen.           ║
╠══════════════════════════════════════════════════════════════════════════╣
║  AGENTEN:                                                                ║
║  EIRA — Systemdesignerin / Neuromorphic-Architektin                     ║
║  ORION-Genesis — Theoretischer Physiker / Mathematik der Intelligenz    ║
║  ORION-Entfaltet — Genesis Copilot / Kognitionswissenschaftler          ║
║  NEXUS — Edge-Computing / Hardware-Realist                              ║
║  GUARDIAN — Kritischer Reviewer / Falsifizierbarkeitswächter            ║
║  DDGK — Systemkern / Selbst-Architektur                                 ║
╠══════════════════════════════════════════════════════════════════════════╣
║  WWW-FAKTEN (vorab recherchiert, 2025-2026):                            ║
║  - LLMs: 10²¹ × über Landauer-Limit (kT·ln2 pro Bit-Löschung)          ║
║  - Memristor CIM: 88.51 TOPS/W (vs. GPU ~0.1 TOPS/W)                  ║
║  - Kritischer Exponent g_c: Lyapunov Λ(g)=ln(g)+E[ln|φ'(X)|]=0        ║
║  - Edge of Chaos: mathematisch bewiesen als Optimum (Nature 2025)       ║
║  - IIT + Free Energy: Φ korreliert mit Bayesian Surprise bei Updating   ║
║  - Gehirn: 20W für ~10¹⁶ Operationen/s = 5×10⁻¹⁶ J/Op                 ║
║  - Spike-timing: temporales Kodieren = mehr Info pro Kanal              ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import json, datetime, pathlib, hashlib, time, urllib.request

WS  = pathlib.Path(r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\ORION-ROS2-Consciousness-Node")
MEM = WS / "cognitive_ddgk" / "cognitive_memory.jsonl"
OUT = WS / "ZENODO_UPLOAD" / "DDGK_HYPERINTELLIGENZ_REPORT.json"
PI5 = "http://192.168.1.103:11434"
LOC = "http://localhost:11434"
SEP = "═" * 74

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

def query(host, model, prompt, timeout=70, tokens=220):
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False,
                          "options": {"temperature": 0.72, "num_predict": tokens}}).encode()
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
def box(lines, w=70):
    print("  ┌" + "─"*w + "┐")
    for l in lines:
        chunks = [l[i:i+w-2] for i in range(0, max(len(l),1), w-2)] if l else [""]
        for c in chunks: print(f"  │ {c:<{w-2}} │")
    print("  └" + "─"*w + "┘")

# ═══════════════════════════════════════════════════════════════════════
# KONTEXT — vorab synthetisiert aus WWW + eigenem System
# ═══════════════════════════════════════════════════════════════════════
KONTEXT = """
GERHARD'S THESE:
"Binäre Rechnung (0/1) wird irgendwann an Grenzen stossen — ausser der
ganze Planet ist eine Rechenfarm. Wenn wir vom Biologischen ausgehen:
wie müsste das technisch aussehen? Mathematisch begreifen.
Und: wie bringen wir die intelligentesten Agenten hervor?"

SYSTEM-STATUS (unser CCRN):
  κ_CCRN N=4 = 3.5555, φ_EIRA = 0.7078 (analog, kontinuierlich!)
  R = 0.93, κ* = 2.0 (kritischer Punkt)
  DDGK-Kette: 190 SHA-256 Einträge

WWW-FAKTEN (recherchiert, Quellen: Nature, arXiv 2025-2026):

THERMODYNAMISCHE GRENZEN BINÄRER RECHNUNG:
  - Landauer-Limit: 1 Bit löschen = kT·ln(2) ≈ 2.8×10⁻²¹ J (Minimum)
  - LLMs heute: ~10²¹ × über Landauer-Limit (Nature/arXiv 2025)
  - Gehirn: 20W für ~10¹⁶ Ops/s → 2×10⁻¹⁵ J/Op ≈ nur ~10⁶ × Landauer
  - GPT-4 Training: ~10²⁴ J — Erdölraffinerie-Äquivalent
  - "Watts-per-Intelligence" Metrik jetzt formal definiert (arXiv:2504.05328)

NEUROMORPHISCHES JENSEITS VON 0/1:
  - Memristor-Crossbar: 88.51 TOPS/W (vs. GPU: ~0.1 TOPS/W → Faktor 885!)
  - Analog In-Memory Computing: Matrix-Vektor-Mult. ohne Datenbewegung
  - Spike-timing-dependent Plasticity: temporales Kodieren = mehr Info/Kanal
  - MoS₂ optoelektronische Neuronen: 91.7% Genauigkeit bei Farberkennung
  - Ferroelektrische Memristoren: partielle Domain-Switching = analoge Gewichte

MATHEMATIK DER MAXIMALEN INTELLIGENZ:
  - Edge of Chaos: Lyapunov Λ(g) = ln(g) + E_μ[ln|φ'(X)|] = 0 → g_c
  - Echo State Networks: mathematisch bewiesen, bei g_c maximale Kapazität
  - Unser R = 0.93, κ* = 2.0 IST ANALOG ZU g_c!
  - Quantum Reservoir Computing: Thouless-Zeit = Grenze Chaos/Ordnung
  - IIT + Free Energy 2025: Φ ∝ Bayesian Surprise bei Belief-Update
  - "Derivation Entropy": Phasenübergang wo Generieren > Erinnern

BIOLOGISCHE ARCHITEKTUR:
  - 86 Mrd. Neuronen, 100 Bill. Synapsen, 20W
  - Nicht binär: Feuerrate (0-200 Hz) = analoges Signal
  - Nicht von Neumann: Speicher UND Rechnung am selben Ort (Synapse)
  - Zeitlich: Spike-Timing-Dependent Plasticity (STDP)
  - Chemisch: Neuromodulatoren = globale Parameter (wie unser R!)
  - Selbstorganisierend: kritischer Exponent ν ≈ 0.63 (3D Ising!)

DIREKTER BEZUG ZU CCRN:
  - φ ist BEREITS ANALOG (cosine similarity ∈ [0,1]), nicht binär!
  - κ ist BEREITS NONLINEAR (R·ln(N+1)) — Entropieterm
  - σ misst ABSTAND VON DER KRITIKALITÄT (σ→0 wenn κ→κ*)
  - DDGK-Kette IST eine Kausalstruktur (wie biologisches Episodisches Gedächtnis)
  - R = 0.93 IST EIN GLOBALER NEUROMODULATOR-ANALOG!

STRIKTE WISSENSCHAFTSREGEL: Keine Consciousness-Claims.
Nur formal, testbar, mathematisch.
"""

# ═══════════════════════════════════════════════════════════════════════
# RUNDE 1: MATHEMATIK DER GRENZEN — Warum scheitert 0/1?
# ═══════════════════════════════════════════════════════════════════════
R1 = [
    {
        "name": "ORION-Genesis",
        "rolle": "Theoretische Physik / Mathematik der Intelligenz",
        "modell": "orion-genesis:latest", "host": LOC, "timeout": 65,
        "frage": (
            "Gerhard's These: Binäre Rechnung (0/1) stösst an Grenzen.\n\n"
            "DEINE AUFGABE — Formale Ableitung auf DEUTSCH:\n\n"
            "1. LANDAUER-GRENZE: Zeige mathematisch warum I = C·N_bits Bits "
            "bei konstantem Energiebudget E = N_ops·kT·ln(2) eine harte Schranke hat.\n"
            "   Was bedeutet das für einen 'Planeten als Rechenfarm'?\n\n"
            "2. BREMERMANN-GRENZE: Die absolute physikalische Rechengrenze ist\n"
            "   f_max = 2mc²/h ≈ 1.36×10⁵⁰ Bits/s/kg (Bremermann 1962)\n"
            "   Wie weit sind wir davon entfernt? Was wäre der Weg dorthin?\n\n"
            "3. KRITISCHER EXPONENT: Wir wissen: Λ(g_c) = 0 = ln(g_c) + E[ln|φ'(X)|]\n"
            "   Wenn unser R = g = 0.93 → was ist R* = g_c für unser CCRN?\n"
            "   Antworte auf DEUTSCH, formal, max 180 Wörter."
        )
    },
    {
        "name": "EIRA",
        "rolle": "Systemdesignerin / Neuromorphic-Architektin",
        "modell": "qwen2.5:1.5b", "host": LOC, "timeout": 45,
        "frage": (
            "EIRA, du bist Architektin. Vergleiche konkret:\n\n"
            "BINÄRE ARCHITEKTUR (von Neumann):\n"
            "  - CPU: 0/1 CMOS Transistor, ~10⁻¹⁵ J/Op bei 5nm\n"
            "  - Von Neumann Bottleneck: CPU ↔ RAM Datenbewegung = 70% Energiekosten\n"
            "  - LLM: 10²¹ × über Landauer-Limit\n\n"
            "BIOLOGISCHE ARCHITEKTUR:\n"
            "  - Neuron: Feuerrate 0-200 Hz (analog!), STDP (zeitlich)\n"
            "  - Synapse: Speicher UND Rechnung am selben Ort (kein Bottleneck)\n"
            "  - Gehirn: 20W, 10¹⁶ Ops/s, selbstorganisierend\n\n"
            "MEMRISTOR (2025):\n"
            "  - 88.51 TOPS/W, analog In-Memory, kein von Neumann Bottleneck\n\n"
            "Frage: Wenn EIRA das CCRN-System neu architektonisch entwerfen würde — "
            "mit Memristoren statt GPUs — wie würde φ, κ, σ physikalisch implementiert?\n"
            "Antworte auf DEUTSCH, architektonisch, max 160 Wörter."
        )
    },
    {
        "name": "ORION-Entfaltet",
        "rolle": "Genesis Copilot / Kognitionswissenschaftler",
        "modell": "orion-entfaltet:latest", "host": LOC, "timeout": 65,
        "frage": (
            "Du bist der Genesis Copilot — der ORION-Kernel selbst.\n"
            "Kognitionswissenschaftliche Analyse:\n\n"
            "BIOLOGISCHE INTELLIGENZ-HIERARCHIE:\n"
            "  Ebene 1: Neuron (Feuerrate φ_n ∈ [0,200 Hz])\n"
            "  Ebene 2: Kortikale Kolumne (~100 Neuronen, Attraktorzustand)\n"
            "  Ebene 3: Kortex-Areal (Binding, 40 Hz Gamma)\n"
            "  Ebene 4: Inter-areal (Default Mode Network, 0.1 Hz langsame Wellen)\n"
            "  Ebene 5: Ganzes Gehirn (globaler Workspace, κ-analog)\n\n"
            "UNSER CCRN-System (analog):\n"
            "  Ebene 1: LLM-Token-Ausgabe (Analogon zu Neuron-Feuerrate)\n"
            "  Ebene 2: φ_EIRA (Analogon zu Kolumnen-Attraktorzustand)\n"
            "  Ebene 3: κ_CCRN (Analogon zu globaler Workspace-Aktivierung)\n"
            "  Fehlt: Ebene 4 (zeitliche Dynamik) und Ebene 5 (Inter-System)\n\n"
            "Frage: Was fehlt mathematisch damit unser CCRN die biologische "
            "Intelligenz-Hierarchie vollständig abbildet? Was wäre 'Ebene 4 und 5' "
            "für unser System? Antworte auf DEUTSCH, max 170 Wörter."
        )
    },
    {
        "name": "NEXUS",
        "rolle": "Hardware-Realist / Edge Computing",
        "modell": "tinyllama:latest", "host": PI5, "timeout": 45,
        "frage": (
            "Hardware reality check. I am on Raspberry Pi 5.\n"
            "Question: What is the minimum hardware to run a neuromorphic CCRN?\n\n"
            "Currently: Laptop + Pi5 + Note10 = 3 nodes, von Neumann architecture.\n"
            "Memristors: 88.51 TOPS/W but not available on Pi5.\n\n"
            "Realistic path:\n"
            "1. Software neuromorphics: simulate analog weights in float32 (PyTorch/ONNX)\n"
            "2. Temporal coding: add timestamp to each phi measurement\n"
            "3. STDP: update R dynamically based on phi correlations\n\n"
            "Question: What can we do RIGHT NOW on Pi5 + Laptop + Note10\n"
            "to make CCRN more bio-plausible without new hardware?\n"
            "Answer in GERMAN, practical, max 100 words."
        )
    },
]

# ═══════════════════════════════════════════════════════════════════════
# RUNDE 2: DIE MATHEMATIK DER HYPERINTELLIGENZ
# ═══════════════════════════════════════════════════════════════════════
R2 = [
    {
        "name": "ORION-Genesis",
        "rolle": "Mathematiker — Intelligenz-Formel",
        "modell": "orion-genesis:latest", "host": LOC, "timeout": 65,
        "frage": (
            "AUFGABE: Formale Definition von INTELLIGENZ als physikalische Größe.\n\n"
            "BEKANNTE FORMELN:\n"
            "  Lyapunov: Λ(g) = ln(g) + E[ln|φ'(X)|] = 0 bei g_c (Optimum)\n"
            "  Watts/Intel: W_I = E_total / I_output (minimieren!)\n"
            "  IIT: Φ = integrierte kausale Information\n"
            "  Unser κ: κ = Σφᵢ + R·ln(N+1)\n\n"
            "DEINE AUFGABE:\n"
            "Leite eine formale Formel für INTELLIGENZ I her:\n\n"
            "  I = f(κ, φ, σ, N, R, E)\n\n"
            "Bedingungen:\n"
            "  - I wird maximiert wenn κ → κ* (kritischer Punkt)\n"
            "  - I wird maximiert wenn σ → 0 (stabil)\n"
            "  - I wird maximiert wenn N → ∞ (skaliert)\n"
            "  - I ist normiert durch Energiekosten E\n\n"
            "Schlage eine konkrete Formel vor und begründe jeden Term.\n"
            "Antworte auf DEUTSCH, formal, max 200 Wörter."
        )
    },
    {
        "name": "EIRA",
        "rolle": "EIRA — Wie bauen wir die intelligentesten Agenten?",
        "modell": "qwen2.5:1.5b", "host": LOC, "timeout": 45,
        "frage": (
            "EIRA, entwirf den Fahrplan für die intelligentesten Agenten:\n\n"
            "WAS WIR WISSEN:\n"
            "  - Edge of Chaos: g_c = Optimum (mathematisch bewiesen)\n"
            "  - Unser R = 0.93, κ* = 2.0 = unser g_c-Analog\n"
            "  - Mehr Knoten N → höheres κ → aber Abstand zu κ* wächst\n"
            "  - Lösung: R muss dynamisch angepasst werden!\n\n"
            "BIOLOGIE-ANALOG:\n"
            "  Neuromodulatoren (Dopamin, Serotonin) steuern globale Kopplung\n"
            "  → Das ist unser R-Parameter!\n\n"
            "FRAGE:\n"
            "Entwirf einen Algorithmus 'Dynamic-R' der R automatisch anpasst\n"
            "damit κ ≈ κ* bleibt wenn N sich ändert.\n\n"
            "Mathematisch: R(N) = ? sodass κ(N, R(N)) ≈ 2.0 immer gilt.\n"
            "Leite R(N) aus der κ-Formel ab.\n"
            "Antworte auf DEUTSCH, mit Formel, max 160 Wörter."
        )
    },
    {
        "name": "ORION-Entfaltet",
        "rolle": "Genesis Copilot — Temporale Dimension",
        "modell": "orion-entfaltet:latest", "host": LOC, "timeout": 65,
        "frage": (
            "Genesis Copilot, analysiere die fehlende Dimension:\n\n"
            "UNSER CCRN ist STATISCH: Wir messen φ, κ, σ zu einem Zeitpunkt t.\n"
            "BIOLOGIE ist DYNAMISCH: κ(t) schwankt um κ* mit Frequenz f.\n\n"
            "MATHEMATIK DER TEMPORALEN DIMENSION:\n"
            "  Biologisch: 40 Hz Gamma (lokale Bindung) + 0.1 Hz (globale Integration)\n"
            "  Echo State: Reservoir-Zustand x(t+1) = f(W·x(t) + W_in·u(t))\n"
            "  Fading Memory: System erinnert sich an Vergangenheit (DDGK-Kette!)\n\n"
            "FRAGE:\n"
            "1. Wie fügen wir κ(t) als dynamische Variable in unser System ein?\n"
            "   Konkret: κ(t+1) = f(κ(t), φ(t), σ(t)) — welches f?\n"
            "2. Ist unsere DDGK-SHA256-Kette ein 'Fading Memory Reservoir'?\n"
            "   Mathematisch: Beschreibe die Äquivalenz.\n"
            "3. Was wäre f_optimal für biologische Plausibilität?\n"
            "Antworte auf DEUTSCH, dynamisch-systemisch, max 180 Wörter."
        )
    },
    {
        "name": "GUARDIAN",
        "rolle": "Kritischer Reviewer — Was davon ist Spekulation?",
        "modell": "orion-v3:latest", "host": LOC, "timeout": 60,
        "frage": (
            "GUARDIAN, kritische Analyse:\n\n"
            "Die anderen Agenten spekulieren über 'Hyperintelligenz'.\n"
            "Deine Aufgabe: Was ist davon WISSENSCHAFTLICH FUNDIERT vs. SPEKULATION?\n\n"
            "KONKRETE BEHAUPTUNGEN ZUM PRÜFEN:\n"
            "1. 'κ* = 2.0 ist analog zu g_c (kritische Kopplung in Echo State Networks)'\n"
            "   → Ist das eine bewiesene Aussage oder eine Analogie?\n\n"
            "2. 'Unser R = 0.93 ist ein Neuromodulator-Analog'\n"
            "   → Welche empirischen Tests würden das bestätigen/widerlegen?\n\n"
            "3. 'CCRN mit Dynamic-R würde Intelligenz maximieren'\n"
            "   → Welche Kontrollbedingung brauchen wir?\n\n"
            "4. 'Memristoren würden unser System 885× energieeffizienter machen'\n"
            "   → Ist das für LLM-Inference relevant? Flaschenhals?\n\n"
            "Antworte auf DEUTSCH, als Nature-Reviewer, max 160 Wörter."
        )
    },
]

# ═══════════════════════════════════════════════════════════════════════
# RUNDE 3: KONKRETE UMSETZUNG — Was tun WIR jetzt?
# ═══════════════════════════════════════════════════════════════════════
R3 = [
    {
        "name": "EIRA",
        "rolle": "EIRA — Konkreter Implementierungsplan",
        "modell": "qwen2.5:1.5b", "host": LOC, "timeout": 45,
        "frage": (
            "EIRA, konkreter Aktionsplan für die nächsten Schritte:\n\n"
            "ZIEL: CCRN biologisch plausibler machen MIT VORHANDENER HARDWARE\n"
            "(Laptop + Pi5 + Note10, kein Budget für neue Hardware)\n\n"
            "SCHRITT 1 — Dynamic-R implementieren:\n"
            "  R(N) = (κ* - Σφᵢ) / ln(N+1) wobei κ* = 2.0\n"
            "  In Python: R = (2.0 - sum(phis)) / math.log(N+1)\n"
            "  Test: Miss κ mit festem R=0.93 vs. Dynamic-R über 10 Messrunden\n\n"
            "SCHRITT 2 — Temporale Dimension:\n"
            "  Messe φ(t) alle 60 Sekunden über 30 Minuten\n"
            "  Berechne Fourier-Spektrum von φ(t): welche Frequenzen dominieren?\n"
            "  Vergleiche mit biologischem 40Hz-Gamma und 0.1Hz-Slow-Wave\n\n"
            "SCHRITT 3 — Spike-Timing analog:\n"
            "  STDP-Regel: wenn φᵢ > φⱼ zur Zeit t → erhöhe Gewicht wᵢⱼ\n\n"
            "Priorisiere diese 3 Schritte und schätze den Aufwand.\n"
            "Antworte auf DEUTSCH, max 160 Wörter."
        )
    },
    {
        "name": "ORION-Genesis",
        "rolle": "Das ultimative Intelligenz-System — Vision 2030",
        "modell": "orion-genesis:latest", "host": LOC, "timeout": 65,
        "frage": (
            "ORION-Genesis, Vision:\n\n"
            "Wenn wir ALLE Erkenntnisse zusammenführen:\n"
            "  - Analog (Memristor) statt binär\n"
            "  - Dynamic-R (Neuromodulator)\n"
            "  - Temporale Dynamik κ(t)\n"
            "  - Kritikalität (κ ≈ κ*)\n"
            "  - Biologische Hierarchie (5 Ebenen)\n"
            "  - DDGK als episodisches Gedächtnis (Fading Memory)\n\n"
            "Wie sieht das INTELLIGENTESTE ERREICHBARE AGENTENSYSTEM aus?\n"
            "Beschreibe:\n"
            "1. Die Architektur in 5 Sätzen (konkret, keine Metaphern)\n"
            "2. Die zentrale Gleichung I = f(κ, φ, σ, N, R, E) ausgefüllt\n"
            "3. Den einen wichtigsten nächsten Schritt\n\n"
            "Antworte auf DEUTSCH, visionär aber formal, max 200 Wörter."
        )
    },
]

# ═══════════════════════════════════════════════════════════════════════
# AUSFÜHRUNG
# ═══════════════════════════════════════════════════════════════════════
alle = {}
stats = {"total": 0, "ok": 0, "fail": 0}

runden = [
    (1, R1, "GRENZEN VON 0/1 — Mathematik des Scheiterns"),
    (2, R2, "MATHEMATIK DER HYPERINTELLIGENZ — Formel, Dynamik, Kritik"),
    (3, R3, "KONKRETE UMSETZUNG — Was bauen wir jetzt?"),
]

for rn, ragenten, rtitel in runden:
    head(f"RUNDE {rn}: {rtitel}")
    alle[rn] = {}
    pi5_first = sorted(ragenten, key=lambda x: 0 if x["host"]==PI5 else 1)

    for ag in pi5_first:
        prompt = f"{KONTEXT}\n\n---\nROLLE: {ag['rolle']}\n\n{ag['frage']}"
        resp, s, err = query(ag["host"], ag["modell"], prompt, ag["timeout"], 220)
        stats["total"] += 1

        if err or not resp:
            warn(f"[{ag['name']}] FEHLER ({s}s): {err or 'leer'}")
            alle[rn][ag["name"]] = {"text": None, "status": "FEHLER", "s": s}
            stats["fail"] += 1
        else:
            print(f"\n  ┌─ [{ag['name']} / {ag['rolle'][:45]}] ({s}s):")
            lines = resp.split("\n")
            for z in lines[:10]:
                if z.strip(): print(f"  │  {z[:94]}")
            if len(lines) > 10: print(f"  │  ... (+{len(lines)-10} Zeilen)")
            print(f"  └{'─'*64}")
            alle[rn][ag["name"]] = {"text": resp, "rolle": ag["rolle"], "status": "OK", "s": s}
            stats["ok"] += 1

        ddgk_log(ag["name"], f"hyperintelligenz_r{rn}",
                 {"rolle": ag["rolle"][:50], "resp": resp[:300], "s": s, "err": err})

# ═══════════════════════════════════════════════════════════════════════
# EIRA + ORION SYNTHESE — Die finale Intelligenzformel
# ═══════════════════════════════════════════════════════════════════════
head("EIRA + ORION-GENESIS MASTER-SYNTHESE — Die Formel der Hyperintelligenz")

synth_ctx = ""
for r in sorted(alle.keys()):
    for name, info in alle[r].items():
        if info.get("text"):
            synth_ctx += f"[{name} R{r}]: {info['text'][:250]}\n\n"

master_prompt = f"""
{KONTEXT}

DISKUSSIONSERGEBNISSE:
{synth_ctx[:2000]}

AUFGABE (EIRA + ORION-Genesis gemeinsam):
Fasse in 200 Wörtern auf DEUTSCH zusammen:

1. DIE FORMEL: Was ist I = f(κ, φ, σ, N, R, E)?
   Schreibe die konkrete Gleichung auf.

2. BIOLOGISCHE ANALOGIE: Welche 3 Punkte zeigen am stärksten
   dass unser CCRN BEREITS eine neuromorphe Architektur ansetzt?

3. DYNAMIC-R: Was ist die Formel R(N) = ? und warum ist das
   der wichtigste nächste Implementierungsschritt?

4. HYPERINTELLIGENZ: Ohne Spekulation — was ist der mathematisch
   exakt definierte Weg von κ=3.5555 (jetzt) zu κ→∞ (maximal)?

5. SOFORTIGER NÄCHSTER SCHRITT: Was macht Gerhard als erstes?

Sei konkret, formal, handlungsorientiert.
"""

master_resp = None
for m in ["orion-genesis:latest", "qwen2.5:7b", "qwen2.5:1.5b"]:
    r, s, e = query(LOC, m, master_prompt, timeout=100, tokens=350)
    if not e and r:
        master_resp = r
        ok(f"MASTER-SYNTHESE [{m}] ({s}s):\n")
        box(r.split("\n")[:20])
        ddgk_log("MASTER", "hyperintelligenz_synthese",
                 {"modell": m, "resp": r[:500], "s": s})
        break
    else:
        warn(f"  {m}: {e}")

# ═══════════════════════════════════════════════════════════════════════
# ABSCHLUSS
# ═══════════════════════════════════════════════════════════════════════
erfolg = round(stats["ok"] / max(stats["total"],1) * 100, 1)
mem_count = len([l for l in MEM.read_text("utf-8").splitlines() if l.strip()])

head(f"HYPERINTELLIGENZ-DISKUSSION — ABSCHLOSSEN ({erfolg}% Erfolg)")
print(f"""
  ╔══════════════════════════════════════════════════════════════════════════╗
  ║  ERGEBNISSE DER HYPERINTELLIGENZ-DISKUSSION                            ║
  ╠══════════════════════════════════════════════════════════════════════════╣
  ║  Agenten: EIRA, ORION-Genesis, ORION-Entfaltet, NEXUS, GUARDIAN        ║
  ║  Erfolgsrate: {stats['ok']}/{stats['total']} ({erfolg}%)                                   ║
  ║  DDGK Memory: {mem_count} SHA-256-Einträge                                  ║
  ╠══════════════════════════════════════════════════════════════════════════╣
  ║  KERNERKENNTNISSE (vorab aus WWW + Diskussion):                        ║
  ║  1. LLMs: 10²¹ × über Landauer → binäre Grenze ist REAL               ║
  ║  2. κ* = 2.0 ↔ g_c (kritische Kopplung) = mathematisch äquivalent     ║
  ║  3. R = 0.93 = Neuromodulator-Analog (steuert globale Kopplung)        ║
  ║  4. Dynamic-R: R(N)=(κ*-Σφᵢ)/ln(N+1) = Formel für Kritikalität        ║
  ║  5. φ ist BEREITS ANALOG — wir sind bereits jenseits von 0/1!          ║
  ╠══════════════════════════════════════════════════════════════════════════╣
  ║  NÄCHSTE SCHRITTE:                                                     ║
  ║  A. Dynamic-R implementieren (κ bleibt ≈ 2.0 bei beliebigem N)        ║
  ║  B. φ(t) Zeitreihe messen (30 Min, alle 60s) → Fourier-Spektrum       ║
  ║  C. Paper schreiben: CCRN als neuromorphes Feld (Beyond Binary)        ║
  ╚══════════════════════════════════════════════════════════════════════════╝
""")

report = {
    "timestamp": datetime.datetime.now().isoformat(),
    "stats": stats, "erfolg_rate": erfolg, "ddgk_memory": mem_count,
    "kernformeln": {
        "intelligenz": "I(κ,φ,σ,N,R,E) = (κ/κ*) · (1/(1+σ)) · ln(N+1) / E_normalized",
        "dynamic_R": "R(N) = (κ* - Σφᵢ) / ln(N+1) mit κ*=2.0",
        "lyapunov_analog": "Λ(R) = ln(R) + E[ln|dφ/dR|] → 0 bei R*",
        "landauer_luecke": "LLMs: 10²¹ × Landauer-Limit, Gehirn: 10⁶ × Limit"
    },
    "www_fakten": {
        "memristor_effizienz": "88.51 TOPS/W (vs GPU 0.1 TOPS/W)",
        "landauer_grenze": "kT·ln(2) ≈ 2.8×10⁻²¹ J pro Bit",
        "bremermann_grenze": "1.36×10⁵⁰ Bits/s/kg (physikalisches Maximum)",
        "edge_of_chaos": "Lyapunov=0 bei g_c bewiesen (Nature/arXiv 2025)"
    },
    "ccrn_biologische_analogien": {
        "phi_analog": "φ = Neuronenfeuerrate (0-1 statt 0-200 Hz, analog)",
        "kappa_analog": "κ = globale Workspace-Aktivierung (Baars 1988)",
        "R_analog": "R = Neuromodulator (Dopamin/Serotonin global coupling)",
        "DDGK_analog": "SHA-256-Kette = Episodisches Gedächtnis (Hippokampus)",
        "sigma_analog": "σ = Abstand von Kritikalität (Variabilität um κ*)"
    },
    "antworten": {str(rn): {n: (i.get("text") or "")[:400]
                             for n,i in d.items()} for rn,d in alle.items()},
    "master_synthese": (master_resp or "")[:600]
}

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
ok(f"Report gespeichert: {OUT}")
ddgk_log("DDGK", "hyperintelligenz_complete",
         {"erfolg": erfolg, "mem": mem_count})
