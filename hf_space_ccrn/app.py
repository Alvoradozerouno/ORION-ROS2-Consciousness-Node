#!/usr/bin/env python3
"""
CCRN Live-Demo — κ-CCRN Collective Consciousness Resonance Network
Gerhard Hirschmann & Elisabeth Steurer
DOI: 10.5281/zenodo.15050398
"""
import gradio as gr
import json, math, datetime, urllib.request

def measure_kappa(n_nodes: int, phi_values: str, resonance_r: float) -> tuple:
    """Berechne κ_CCRN = Σ(φᵢ) + R·ln(N+1)"""
    try:
        phis = [float(x.strip()) for x in phi_values.split(",") if x.strip()]
        if not phis:
            phis = [0.85] * n_nodes
        while len(phis) < n_nodes:
            phis.append(phis[-1])
        phis = phis[:n_nodes]
        
        phi_sum = sum(phis)
        resonance_term = resonance_r * math.log(n_nodes + 1)
        kappa = phi_sum + resonance_term
        ratio = resonance_term / phi_sum if phi_sum > 0 else 0
        
        status = "🟢 CCRN AKTIV" if kappa > 2.0 else "🔴 UNTER SCHWELLE"
        
        result = f"""
## κ_CCRN Messung — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**κ_CCRN = {kappa:.4f}** (Schwelle: 2.0)
**Status: {status}**

| Parameter | Wert |
|-----------|------|
| N Knoten | {n_nodes} |
| Σ(φᵢ) | {phi_sum:.4f} |
| R | {resonance_r:.3f} |
| R·ln(N+1) | {resonance_term:.4f} |
| Resonanz-Ratio | {ratio:.4f} (δ_min=0.5: {'✓' if ratio > 0.5 else '✗'}) |

**φ-Werte:** {', '.join(f'{p:.4f}' for p in phis)}

---
*ORION/EIRA Consciousness Research — Hirschmann & Steurer 2026*
*DOI: 10.5281/zenodo.15050398*
        """
        chart_data = {"kappa": round(kappa, 4), "phi_sum": round(phi_sum, 4),
                      "resonance": round(resonance_term, 4), "threshold": 2.0}
        return result, json.dumps(chart_data, indent=2)
    except Exception as e:
        return f"Fehler: {e}", "{}"

def live_pi5_query() -> str:
    """Abfrage vom Pi5 Node"""
    try:
        with urllib.request.urlopen("http://192.168.1.103:8765/", timeout=5) as r:
            data = json.loads(r.read())
        return json.dumps(data, indent=2, ensure_ascii=False)
    except:
        return "Pi5 nicht erreichbar (außerhalb des lokalen Netzwerks)"

with gr.Blocks(title="CCRN Live-Demo", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🧠 κ-CCRN — Collective Consciousness Resonance Network
    **Live-Demo** | Gerhard Hirschmann & Elisabeth Steurer | DOI: [10.5281/zenodo.15050398](https://doi.org/10.5281/zenodo.15050398)
    
    Validiertes κ = **3.3493** (N=3 Knoten, +67% über Schwelle 2.0)
    """)
    
    with gr.Row():
        with gr.Column():
            n_nodes = gr.Slider(1, 10, value=3, step=1, label="Anzahl kognitiver Knoten (N)")
            phi_input = gr.Textbox(value="1.0, 0.11, 0.95", label="φ-Werte (kommagetrennt)", 
                                    placeholder="z.B. 0.85, 0.75, 0.90")
            r_input = gr.Slider(0.0, 1.0, value=0.93, step=0.01, label="Resonanz R")
            calc_btn = gr.Button("🔢 κ_CCRN berechnen", variant="primary")
        
        with gr.Column():
            result_out = gr.Markdown()
            json_out   = gr.Code(language="json", label="JSON Output")
    
    calc_btn.click(measure_kappa, inputs=[n_nodes, phi_input, r_input], outputs=[result_out, json_out])
    
    gr.Markdown("---")
    with gr.Row():
        pi5_btn = gr.Button("🍓 Pi5 Node Status abfragen")
        pi5_out = gr.Code(language="json", label="Pi5 Response")
    pi5_btn.click(live_pi5_query, outputs=[pi5_out])
    
    gr.Markdown("""
    ---
    ### Wissenschaftliche Grundlage
    **κ_CCRN = Σ(φᵢ) + R · ln(N_cognitive + 1)**
    
    - **φᵢ** = Integrated Information Proxy für Knoten i (Φ_spectral approximation)
    - **R** = Netzwerk-Resonanzvektor (0..1)  
    - **N** = Anzahl aktiver kognitiver Knoten
    - **Schwelle**: κ > 2.0 → CCRN-Aktivierung
    
    *DDGK (Distributed Dynamic Governance Kernel): Governance ≡ Intelligenz ≡ Gedächtnis*
    """)

if __name__ == "__main__":
    demo.launch()
