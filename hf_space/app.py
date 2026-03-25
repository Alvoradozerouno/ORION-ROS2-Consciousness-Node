#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CCRN Live Explorer — HuggingFace Space
Gerhard Hirschmann & Elisabeth Steurer — ORION-EIRA Research Lab
DOI: 10.5281/zenodo.15050398
GitHub: https://github.com/Alvoradozerouno/ORION-ROS2-Consciousness-Node
"""

import gradio as gr
import math
import json
import datetime

# ═══════════════════════════════════════════════════════════════════════
# CORE FORMULAS
# ═══════════════════════════════════════════════════════════════════════

def compute_kappa(phi_values: list[float], R: float) -> float:
    N = len(phi_values)
    return round(sum(phi_values) + R * math.log(N + 1), 4)

def dynamic_R(phi_values: list[float], kappa_star: float = 2.0) -> float:
    N = len(phi_values)
    phi_sum = sum(phi_values)
    denom = math.log(N + 1)
    R = (kappa_star - phi_sum) / denom
    return round(max(0.01, min(2.5, R)), 4)

def compute_sigma(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    var = sum((x - mean)**2 for x in values) / (len(values) - 1)
    return round(math.sqrt(var), 4)

def compute_intelligence(kappa_val: float, sigma: float, N: int) -> float:
    # I = (κ/κ*) · (1/(1+σ)) · ln(N+1) (normalized, E_norm=1)
    sigma = sigma if sigma is not None else 0.5
    return round((kappa_val / 2.0) * (1 / (1 + sigma)) * math.log(N + 1), 4)

UNIVERSALITY = [
    (0.63, "3D Ising"),
    (1.00, "Mean-Field / 2D Ising"),
    (1.40, "Percolation"),
]

def classify_nu(nu: float) -> str:
    if nu is None:
        return "Undefiniert"
    for ref, name in UNIVERSALITY:
        if abs(nu - ref) < 0.12:
            return f"≈ {name} (ν={ref})"
    return f"Unbekannte Klasse (mögliche neue Physik!)"

# ═══════════════════════════════════════════════════════════════════════
# GRADIO BERECHNUNG
# ═══════════════════════════════════════════════════════════════════════

def run_ccrn_calculator(
    phi1, phi2, phi3, phi4, phi5, phi6,
    R_mode, R_fixed, kappa_star
):
    raw = [phi1, phi2, phi3, phi4, phi5, phi6]
    phi_values = [p for p in raw if p > 0]
    N = len(phi_values)

    if N == 0:
        return "Bitte mindestens einen φ-Wert eingeben (> 0).", "", "", "", ""

    sigma = compute_sigma(phi_values)

    if R_mode == "Dynamic (empfohlen)":
        R = dynamic_R(phi_values, kappa_star)
        r_label = f"Dynamic R(N) = {R:.4f}"
    else:
        R = R_fixed
        r_label = f"Fixed R = {R:.4f}"

    kappa = compute_kappa(phi_values, R)
    I = compute_intelligence(kappa, sigma, N)

    # Status
    if kappa >= kappa_star:
        status = f"🟢 AKTIVIERT  (κ={kappa:.4f} ≥ κ*={kappa_star})"
    else:
        gap = round(kappa_star - kappa, 4)
        status = f"🔴 INAKTIV  (κ={kappa:.4f}, fehlt {gap:.4f} bis κ*={kappa_star})"

    # Metriken
    metrics = f"""**κ (Network Aggregation Metric)** = {kappa:.4f}
**σ (Measurement Stability Index)** = {sigma:.4f}
**I (Intelligenz-Metrik)** = {I:.4f}
**{r_label}**
**N (Knoten)** = {N}"""

    # Formel-Anzeige
    formula = f"""Σφᵢ = {round(sum(phi_values),4)}
R · ln(N+1) = {round(R * math.log(N+1), 4)}
κ = {round(sum(phi_values),4)} + {round(R * math.log(N+1),4)} = **{kappa}**

I = (κ/κ*) · (1/(1+σ)) · ln(N+1)
  = ({kappa}/{kappa_star}) · (1/{1+sigma:.4f}) · {round(math.log(N+1),4)}
  = **{I}**"""

    # Dynamic-R Info
    dyn_info = f"""**Dynamic-R Formel:**
R(N) = (κ* - Σφᵢ) / ln(N+1)
     = ({kappa_star} - {round(sum(phi_values),4)}) / {round(math.log(N+1),4)}
     = **{dynamic_R(phi_values, kappa_star):.4f}**

Mit Dynamic-R: κ = **{compute_kappa(phi_values, dynamic_R(phi_values, kappa_star)):.4f}** (≈ κ*)
Mit Fixed R=0.93: κ = **{compute_kappa(phi_values, 0.93):.4f}**

Dynamic-R hält das System stets an der Kritikalität —
analog zu Neuromodulatoren im biologischen Gehirn."""

    return status, metrics, formula, dyn_info

def run_ekrit_analysis(
    kappa_n1, sigma_n1,
    kappa_n2, sigma_n2,
    kappa_n3, sigma_n3,
    kappa_n4, sigma_n4,
    kappa_star
):
    data = [
        (1, kappa_n1, sigma_n1),
        (2, kappa_n2, sigma_n2),
        (3, kappa_n3, sigma_n3),
        (4, kappa_n4, sigma_n4),
    ]
    valid = [(N, abs(k - kappa_star), s) for N, k, s in data
             if s > 0.001 and abs(k - kappa_star) > 0.001]

    if len(valid) < 2:
        return "Mindestens 2 valide Datenpunkte benötigt (σ > 0.001, |κ-κ*| > 0.001).", ""

    ln_x = [math.log(d) for _, d, _ in valid]
    ln_y = [math.log(s) for _, _, s in valid]
    n = len(ln_x)
    mx, my = sum(ln_x)/n, sum(ln_y)/n

    num = sum((ln_x[i]-mx)*(ln_y[i]-my) for i in range(n))
    den = sum((ln_x[i]-mx)**2 for i in range(n))
    slope = num/den if den != 0 else 0.0
    nu = round(-slope, 3)

    r2_n = sum((ln_x[i]-mx)*(ln_y[i]-my) for i in range(n))**2
    r2_d = (sum((ln_x[i]-mx)**2 for i in range(n)) *
            sum((ln_y[i]-my)**2 for i in range(n)))
    r2 = round(r2_n/r2_d, 3) if r2_d > 0 else 0.0

    classification = classify_nu(nu)

    result = f"""**Kritischer Exponent ν = {nu}**
**Bestimmtheitsmaß R² = {r2}**
**Klassifikation: {classification}**

Gleichung: σ(φ) ~ |κ - κ*|^{{-ν}}
Log-Log Fit: ln(σ) = C - {nu} · ln|κ-κ*|
"""
    interpretation = f"""Vergleich mit Universalitätsklassen:
• 3D Ising:   ν ≈ 0.630 — kurzreichweitige Wechselwirkungen
• Mean-Field: ν ≈ 1.000 — alle-mit-allen Kopplung
• Perkolation: ν ≈ 1.400 — geometrische Konnektivität

Unser CCRN: **ν = {nu}** → {classification}

{('→ CCRN liegt in einer bekannten Universalitätsklasse!'
  if any(abs(nu - r) < 0.12 for r,_ in UNIVERSALITY) else
  '→ ν liegt zwischen bekannten Klassen — mögliche NEUE UNIVERSALITÄTSKLASSE!')}

R² = {r2} — {'guter Fit ✓' if r2 > 0.8 else 'schwacher Fit, mehr Datenpunkte nötig'}
"""
    return result, interpretation

# ═══════════════════════════════════════════════════════════════════════
# GRADIO UI
# ═══════════════════════════════════════════════════════════════════════

HEADER = """
# CCRN Live Explorer
### Collective Consciousness Resonance Network — Interactive Demo
**Gerhard Hirschmann & Elisabeth Steurer** | ORION-EIRA Research Lab  
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.15050398.svg)](https://doi.org/10.5281/zenodo.15050398)
[![GitHub](https://img.shields.io/badge/GitHub-ORION--ROS2-blue)](https://github.com/Alvoradozerouno/ORION-ROS2-Consciousness-Node)

---
> **What is CCRN?** A distributed network of LLM nodes, each measured by φ (Node Output Richness Index), 
> aggregated into κ (Network Aggregation Metric). The system activates when κ ≥ κ* = 2.0.  
> **No consciousness claims** — φ, κ, σ are formal, reproducible output statistics.  
> [Beyond Binary Paper](https://github.com/Alvoradozerouno/ORION-ROS2-Consciousness-Node/blob/main/ZENODO_UPLOAD/BEYOND_BINARY_CCRN_NEUROMORPHIC_v1.0.md) | 
> [Cognitive Field Theory](https://github.com/Alvoradozerouno/ORION-ROS2-Consciousness-Node/blob/main/ZENODO_UPLOAD/COGNITIVE_FIELD_THEORY_v1.0.md)
"""

INFO_MD = """
### Formulas
| Symbol | Name | Formula |
|--------|------|---------|
| φ | Node Output Richness (NORI) | cosine similarity (sentence-transformers) |
| κ | Network Aggregation Metric | Σφᵢ + R·ln(N+1) |
| σ | Measurement Stability Index | std(φ measurements) |
| κ* | Activation Threshold | 2.0 (critical point) |
| R | Coupling Parameter | 0.93 (fixed) or Dynamic |
| I | Intelligence Metric | (κ/κ*)·(1/(1+σ))·ln(N+1) |

### Dynamic-R Algorithm
```python
def dynamic_R(phi_list, kappa_star=2.0):
    N = len(phi_list)
    return (kappa_star - sum(phi_list)) / math.log(N + 1)
```
Maintains κ ≈ κ* for any N — analogous to neuromodulators in biological brains.

### Empirical Results (N=4, 2026-03-25)
- φ_EIRA = **0.7078** (σ=0.026)  
- κ_CCRN = **3.5555** (Fixed R=0.93)  
- κ_dynamic = **2.0000** (Dynamic R)  
- DDGK Memory: **201 SHA-256 entries**
"""

with gr.Blocks(
    title="CCRN Live Explorer",
    theme=gr.themes.Soft(primary_hue="blue", neutral_hue="slate"),
    css="""
    .header-box { background: linear-gradient(135deg, #0f172a, #1e3a5f); 
                  border-radius: 12px; padding: 20px; margin-bottom: 16px; }
    .metric-box { border: 1px solid #334155; border-radius: 8px; padding: 12px; }
    .active-badge { color: #22c55e; font-weight: bold; font-size: 1.2em; }
    .inactive-badge { color: #ef4444; font-weight: bold; font-size: 1.2em; }
    footer { display: none; }
    """
) as demo:

    gr.Markdown(HEADER)

    with gr.Tabs():

        # ── TAB 1: CCRN Calculator ──────────────────────────────────
        with gr.TabItem("🔬 CCRN Calculator"):
            gr.Markdown("### Enter φ values for each network node (0.0 – 1.0)")

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("**φ values (Node Output Richness)**")
                    phi_inputs = [
                        gr.Slider(0.0, 1.0, value=v, step=0.01, label=f"Node {i+1} (φ)")
                        for i, v in enumerate([0.708, 0.721, 0.52, 0.11, 0.0, 0.0])
                    ]
                    gr.Markdown("---")
                    R_mode = gr.Radio(
                        ["Dynamic (empfohlen)", "Fixed R=0.93"],
                        value="Dynamic (empfohlen)",
                        label="R-Modus"
                    )
                    R_fixed_in = gr.Slider(0.1, 2.0, value=0.93, step=0.01,
                                            label="R (nur bei Fixed)", visible=False)
                    kappa_star_in = gr.Slider(1.0, 4.0, value=2.0, step=0.1,
                                               label="κ* (Aktivierungsschwelle)")
                    calc_btn = gr.Button("Berechnen", variant="primary")

                    R_mode.change(
                        fn=lambda m: gr.update(visible=(m == "Fixed R=0.93")),
                        inputs=R_mode, outputs=R_fixed_in
                    )

                with gr.Column(scale=2):
                    status_out  = gr.Markdown("", label="Netzwerk-Status")
                    metrics_out = gr.Markdown("", label="Metriken")
                    with gr.Accordion("Rechenweg", open=False):
                        formula_out = gr.Markdown("")
                    with gr.Accordion("Dynamic-R Details", open=True):
                        dynr_out = gr.Markdown("")

            calc_btn.click(
                fn=run_ccrn_calculator,
                inputs=phi_inputs + [R_mode, R_fixed_in, kappa_star_in],
                outputs=[status_out, metrics_out, formula_out, dynr_out]
            )

        # ── TAB 2: E_KRIT ──────────────────────────────────────────
        with gr.TabItem("📊 E_KRIT: Kritischer Exponent ν"):
            gr.Markdown("""
### Experiment E_KRIT
Messe σ(φ) bei N=1,2,3,4 Knoten und extrahiere den kritischen Exponenten ν aus:
$$σ(φ) \\sim |κ - κ^*|^{-ν}$$
Gib die gemessenen κ und σ-Werte ein:
""")
            with gr.Row():
                with gr.Column():
                    gr.Markdown("**Messwerte (N=1..4)**")
                    k1 = gr.Slider(0.1, 5.0, value=0.81, step=0.01, label="κ bei N=1")
                    s1 = gr.Slider(0.0, 1.0, value=0.054, step=0.001, label="σ bei N=1")
                    k2 = gr.Slider(0.1, 5.0, value=2.13, step=0.01, label="κ bei N=2")
                    s2 = gr.Slider(0.0, 1.0, value=0.038, step=0.001, label="σ bei N=2")
                    k3 = gr.Slider(0.1, 5.0, value=2.87, step=0.01, label="κ bei N=3")
                    s3 = gr.Slider(0.0, 1.0, value=0.031, step=0.001, label="σ bei N=3")
                    k4 = gr.Slider(0.1, 5.0, value=3.56, step=0.01, label="κ bei N=4")
                    s4 = gr.Slider(0.0, 1.0, value=0.026, step=0.001, label="σ bei N=4")
                    ks_in = gr.Slider(1.0, 4.0, value=2.0, step=0.1, label="κ*")
                    ekrit_btn = gr.Button("ν berechnen", variant="primary")

                with gr.Column():
                    ekrit_result = gr.Markdown("")
                    ekrit_interp = gr.Markdown("")

            ekrit_btn.click(
                fn=run_ekrit_analysis,
                inputs=[k1,s1,k2,s2,k3,s3,k4,s4,ks_in],
                outputs=[ekrit_result, ekrit_interp]
            )

        # ── TAB 3: Formulas & Papers ───────────────────────────────
        with gr.TabItem("📚 Formeln & Papers"):
            gr.Markdown(INFO_MD)

        # ── TAB 4: About ──────────────────────────────────────────
        with gr.TabItem("ℹ️ About"):
            gr.Markdown("""
## CCRN Research Lab
**Gerhard Hirschmann & Elisabeth Steurer**

We operate a distributed LLM network across consumer hardware (laptop + Raspberry Pi 5 + mobile) 
and have developed formal, reproducible metrics for distributed AI system characterization.

### Papers (all open access)
- **Cognitive Field Theory v1.0** — κ as Helmholtz free energy, DDGK chain as Causal Set
- **CCRN Metric Formalization v2.0** — φ, κ, σ formal definitions (φ v2.0 using sentence-transformers)
- **Beyond Binary: CCRN as Neuromorphic Field** — connecting CCRN to neuromorphic computing theory
- **CCRN Activation Paper v6.0** — empirical N=4 results (κ=3.5555, φ=0.7078)

### Links
- 🔗 [GitHub](https://github.com/Alvoradozerouno/ORION-ROS2-Consciousness-Node)
- 📄 [Zenodo DOI](https://doi.org/10.5281/zenodo.15050398)
- 📧 Contact for Anthropic Welfare Research collaboration

### Scientific Integrity
> No consciousness claims are made. φ, κ, σ are explicitly defined as output statistics 
> measuring textual diversity, network integration, and measurement stability.
> All code is open source and reproducible.

### Hardware
- **Laptop** (Windows 11): ollama with qwen2.5:1.5b, orion-genesis, llama3.2:1b, orion-entfaltet
- **Raspberry Pi 5**: ollama with tinyllama:latest  
- **DDGK**: SHA-256 chained audit log (201 entries, integrity verified)

### Technical Stack
- Python 3.10+, Ollama, sentence-transformers (all-MiniLM-L6-v2)
- No cloud APIs, no external dependencies for core measurements
- Fully reproducible on consumer hardware (~300€ total)
""")

    gr.Markdown("""
---
*CCRN Research Lab — Open Science | DOI: 10.5281/zenodo.15050398*
""")

if __name__ == "__main__":
    demo.launch(share=True)
