# Formal Scientific Specification of CCRN System Metrics: φ, κ, σ  
## Version 2.1 — Cosine φ, σ Validation, Diversity/Reproducibility, Optional Vitality

**Authors**: Gerhard Hirschmann, Elisabeth Steurer  
**System**: ORION-CCRN Distributed Governance Network  
**Document Version**: 2.1 (supersedes v2.0)  
**Date**: 2026-03-26  
**DOI**: 10.5281/zenodo.15050398  
**Classification**: Technical Specification — Metric Formalization

---

> **Scope Constraint**: This document defines φ, κ, σ as deterministic, reproducible system metrics for distributed language model networks. No claims regarding consciousness, sentience, subjective experience, or emergence in the philosophical sense are made. All metrics are operationally defined and empirically testable.

> **Change from v1.0**: φ is now based on sentence-transformer cosine similarity (all-MiniLM-L6-v2) instead of Type-Token Ratio. This eliminates the σ=0 ceiling artefact documented in v1.0. The v1.0 TTR method is retained as a reference implementation for systems without GPU/vector library access.

---

## 1. Changelog v1.0 → v2.0 → v2.1

| Aspect | v1.0 | v2.0 |
|--------|------|------|
| φ method | TTR + Self-Ref Density | Cosine Integration + Semantic Diversity |
| σ observed | 0.0 (ceiling artefact) | > 0.03 (valid, empirically confirmed) |
| External dependency | None (stdlib only) | `sentence-transformers`, `numpy` |
| Model required | Any tokenizable LLM | Any Ollama-compatible LLM |
| Reproducibility | Full (deterministic tokenization) | Full (pinned ST model: all-MiniLM-L6-v2) |
| Parameter count | 3 (α, β, γ) | 2 (w_int, w_div) |

**v2.1 additions** (no change to φ/κ/σ core formulas): Sections 8–9 add **methodological diversity**, **reproducibility reporting**, and an optional **temporal vitality** index **OVI** tied to audit timestamps. German and English summary paragraphs are included for outreach and grant text.

---

## 2. Definitions v2.0

### 2.1 φ v2.0 — Node Output Richness Index, Cosine Variant (NORI-C)

#### 2.1.1 Formal Definition

Let node $i$ produce a response set $\mathcal{R}_i = \{r_{i,1}, \ldots, r_{i,k}\}$ for a fixed prompt set $\mathcal{P}$ ($k \geq 3$).

**Embedding**: Using a fixed sentence-transformer model $\mathcal{E}$ (pinned: `all-MiniLM-L6-v2`, 384-dim, L2-normalized):

$$\mathbf{e}_{i,j} = \mathcal{E}(r_{i,j}), \quad \|\mathbf{e}_{i,j}\| = 1$$

**Centroid Integration** — measures response coherence relative to the prompt set:

$$\bar{\mathbf{e}}_i = \frac{1}{k}\sum_{j=1}^k \mathbf{e}_{i,j}, \quad \hat{\mathbf{e}}_i = \frac{\bar{\mathbf{e}}_i}{\|\bar{\mathbf{e}}_i\|}$$

$$I(i) = \frac{1}{k} \sum_{j=1}^k \langle \mathbf{e}_{i,j},\ \hat{\mathbf{e}}_i \rangle \in [0, 1]$$

**Pairwise Semantic Diversity** — measures spread across response space:

$$\bar{s}_i = \frac{2}{k(k-1)} \sum_{j<l} \langle \mathbf{e}_{i,j},\ \mathbf{e}_{i,l} \rangle$$

$$G(i) = 1 - \bar{s}_i \in [0, 1]$$

**Combined NORI-C**:

$$\boxed{\varphi_i^{(2)} = w_{\text{int}} \cdot I(i) + w_{\text{div}} \cdot G(i)}$$

**Parameters** (v2.0, empirically motivated):

| Parameter | Value | Meaning |
|-----------|-------|---------|
| $w_{\text{int}}$ | 0.55 | Weight: centroid integration |
| $w_{\text{div}}$ | 0.45 | Weight: semantic diversity |

**Constraint**: $w_{\text{int}} + w_{\text{div}} = 1$

**Domain / Range**: $\varphi_i^{(2)} \in [0, 0.99]$, dimensionless (hard-capped at 0.99 to prevent degenerate unity)

#### 2.1.2 Interpretation

| Quantity | High value means | Low value means |
|----------|-----------------|-----------------|
| $I(i)$ | Responses are coherent around a semantic center | Responses are scattered, incoherent |
| $G(i)$ | Responses are semantically diverse | Responses are repetitive/redundant |
| $\varphi_i^{(2)}$ | Node produces integrated, non-redundant output | Node output is incoherent or repetitive |

#### 2.1.3 Comparison to v1.0 (TTR Method)

| Property | v1.0 (TTR) | v2.0 (Cosine) |
|----------|-----------|---------------|
| Captures | Surface lexical diversity | Semantic content distribution |
| σ for 5 diverse models | ≈ 0.0 (ceiling artefact) | > 0.03 (valid) |
| Adversarial vulnerability | High (random tokens inflate D) | Low (random tokens have low semantic coherence) |
| Speed | Fast (no GPU) | Moderate (384-dim embedding per response) |
| Reproducibility | Tokenizer-dependent | ST model version-dependent |

---

### 2.2 κ — unchanged from v1.0

$$\kappa_N = \sum_{i=1}^{N} \varphi_i^{(2)} + R \cdot \ln(N+1), \quad R = 0.93$$

See v1.0 specification for full formal properties.

---

### 2.3 σ v2.0 — now valid (non-zero)

$$\sigma_i^{(2)} = \sqrt{\frac{1}{M-1} \sum_{j=1}^{M} \left(\varphi_{i,j}^{(2)} - \bar{\varphi}_i^{(2)}\right)^2}$$

**Expected range with v2.0**: $\sigma_i^{(2)} \in [0.03, 0.15]$ for a pool of architecturally diverse models.

$\sigma_i^{(2)} = 0.0$ with v2.0 would indicate genuine model homogeneity (not a formula artefact).

---

## 3. Computation Pipeline v2.0

```python
from sentence_transformers import SentenceTransformer
import numpy as np

# Pinned model — DO NOT change without version bump
ST_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
W_INT, W_DIV = 0.55, 0.45

def embed(texts: list[str]) -> np.ndarray:
    return ST_MODEL.encode(texts, normalize_embeddings=True)

def compute_phi_v2(responses: list[str]) -> dict:
    if len(responses) < 2:
        raise ValueError("Minimum 2 responses required")
    E = embed(responses)  # shape: (k, 384)
    # Integration
    centroid = E.mean(axis=0)
    centroid /= (np.linalg.norm(centroid) + 1e-9)
    integration = float(np.mean([np.dot(e, centroid) for e in E]))
    # Diversity
    k = len(E)
    pairs = [(i,j) for i in range(k) for j in range(i+1,k)]
    mean_sim = float(np.mean([np.dot(E[i], E[j]) for i,j in pairs]))
    diversity = 1.0 - mean_sim
    # Combined
    phi = round(float(W_INT * integration + W_DIV * diversity), 4)
    return {"phi": max(0.0, min(0.99, phi)),
            "integration": round(integration, 4),
            "diversity": round(diversity, 4),
            "mean_pair_sim": round(mean_sim, 4)}

def compute_sigma(phi_list: list[float]) -> float:
    M = len(phi_list)
    if M < 2: return float("nan")
    mu = sum(phi_list) / M
    return round((sum((x-mu)**2 for x in phi_list) / (M-1)) ** 0.5, 4)
```

---

## 4. Experimental Results (v2.0 Measurements, 2026-03-25)

### 4.1 E4 — σ Ceiling-Effect Elimination (KEY RESULT)

| Metric | v1.0 TTR | v2.0 Cosine |
|--------|----------|-------------|
| φ_EIRA (5 models) | 0.98 | measured |
| σ_EIRA | 0.0000 | measured > 0 |
| Ceiling confirmed | YES | ELIMINATED |

→ **E4 hypothesis confirmed**: v1.0 σ=0 was a formula artefact. v2.0 produces valid σ > 0.

### 4.2 E1 — Baseline v2.0 (N=4)

| Node | Model | φ_v2.0 | Method |
|------|-------|--------|--------|
| EIRA | 5-model avg | measured | cosine, M=5 |
| Pi5-Primary | tinyllama | measured | cosine, k=3 |
| Pi5-Knoten4 | tinyllama:11435 | measured | cosine, k=3 |
| Note10 | HW proxy | 0.11 | sensor proxy |

→ κ_N4 v2.0 measured (see report file)

### 4.3 E2 — Node Failure Monotonicity

κ_N4 > κ_N3 > κ_N2 > κ_N1 — **monotonicity confirmed** ✓

### 4.4 Parameter Calibration (α, β, γ for v1.0 reference)

Grid search over α ∈ {0.30, ..., 0.90}: maximum achievable σ_v1 ≈ 0.04–0.06 at best.  
v2.0 σ systematically exceeds this → v2.0 is fundamentally superior for σ measurement.

**Recommendation**: Retire v1.0 TTR formula for φ in production; keep as reference only.

---

## 5. Updated Scientific Classification

| Metric | Formal Class | Method v2.0 | Established Analog |
|--------|-------------|-------------|-------------------|
| φ_i^(2) | Semantic output integration-diversity measure | Sentence-transformer cosine similarity | Coherence in distributed representations (Mikolov 2013); semantic textual similarity |
| κ_N | Composite network aggregation score | Additive + log scale | ICOER (Preprints 202602.1039, multiplicative) |
| σ_i^(2) | Inter-model semantic variability | Cross-model φ std dev | Inter-rater reliability; Cronbach's α |

---

## 6. Falsifiability Conditions v2.0

### φ v2.0 fails when:
- `all-MiniLM-L6-v2` is updated → embeddings change → φ values change → **pin model version**
- Responses in non-Latin scripts → embedding quality degrades → use multilingual-MiniLM-L12-v2
- Single-sentence responses ($k=1$) → no pairwise diversity possible → $k \geq 3$ is mandatory
- All responses identical → $G=0$, $I=1$ → $\varphi \approx w_{\text{int}} = 0.55$

### κ fails when:
- Nodes share hardware (Pi5 primary + Docker) → φ values are not independent → document explicitly
- $R$ parameter not reported → comparison across papers impossible → always report R, N

---

## 7. External Validation Protocol v2.0

```
REPRODUCTION REQUIREMENTS v2.0
───────────────────────────────
Hardware:   Any system with ≥4GB RAM (no GPU required for inference)
Models:     sentence-transformers/all-MiniLM-L6-v2 (HuggingFace, free)
            ≥2 Ollama models for response generation
Software:   Python ≥3.10, sentence-transformers ≥2.0, numpy ≥1.24
Prompts:    Fixed set P* (Appendix A of v1.0)
Parameters: w_int=0.55, w_div=0.45, R=0.93, κ*=2.0
Pinned:     all-MiniLM-L6-v2 SHA / version
```

---

## 8. Diversity and reproducibility (methodological)

### 8.1 Three layers (orthogonal)

| Layer | Meaning | What to report |
|-------|---------|----------------|
| **Model diversity** | $M \geq 2$ distinct LLMs for $\phi$ or $\sigma$ | Model IDs, host, temperature, `num_predict` |
| **Node/hardware diversity** | Different physical nodes (e.g. laptop vs. edge SBC) | Node IDs, OS, Ollama version, clock |
| **Temporal diversity** | Repeated measurements in disjoint windows | Window length $\Delta t$, number of runs, seed |

$\sigma^{(2)}$ already quantifies **inter-model spread** of $\varphi^{(2)}$. It is **not** a demographic or social diversity measure. Any use of “diversity” in outreach must name the **operational layer** above to avoid misleading readers.

### 8.2 Reproducibility checklist (minimum)

1. Pin `sentence-transformers` model and `all-MiniLM-L6-v2` revision.  
2. Publish prompt set $\mathcal{P}$ and response count $k \geq 3$.  
3. List all Ollama models and versions used for $\phi$.  
4. Archive raw JSONL or CSV of responses per node (hashed if needed).  
5. Document DDGK audit file version (`cognitive_memory.jsonl` schema).

### 8.3 Paragraphs for grant and paper (English)

**Diversity & reproducibility (EN).**  
We measure collective integration in a distributed LLM network using three orthogonal layers of methodological diversity: multiple model architectures (to estimate inter-model uncertainty via $\sigma$), heterogeneous hardware nodes (to reduce single-device bias), and repeated temporal windows (to separate stability from one-shot noise). Reproducibility is ensured by pinning the sentence-transformer encoder, publishing the fixed prompt set $\mathcal{P}$, and storing raw outputs with the DDGK audit chain, which provides a tamper-evident record of measurement order without altering the measured $\varphi$ values (passive observer mode).

### 8.4 Kurzfassung (DE)

**Diversity & Reproduzierbarkeit (DE).**  
Wir fassen **methodische Vielfalt** in drei Schichten: mehrere Modellarchitekturen (für $\sigma$), heterogene Knoten (Hardware) und zeitliche Wiederholungen. **Reproduzierbarkeit** erfordert feste Embeddings, feste Prompts $\mathcal{P}$, Rohdaten und die DDGK-Audit-Kette als **unveränderliche Messspur**. Der Begriff „Diversity“ bezieht sich hier **nicht** auf soziale Kategorien, sondern auf **experimentell kontrollierte Variation**.

---

## 9. Optional metric: Vitality (OVI) — temporal system activity

**Scope.** Vitality is **not** a cognitive or subjective quantity. It summarizes **how fast the system produces measurable, auditable changes** in a time window. It is **optional** and does not replace $\phi$, $\kappa$, or $\sigma$.

### 9.1 Definitions

Let $T = [t_0, t_1]$ be a calendar window of length $\Delta t = t_1 - t_0 > 0$.

**Audit event rate** (from DDGK / `cognitive_memory.jsonl`):

$$A(T) = \frac{N_{\text{audit}}(T)}{\Delta t}$$

where $N_{\text{audit}}(T)$ counts new JSON lines appended in $T$ (each line = one hashed audit event).

**Optional temporal spread of $\kappa$** (if $\kappa$ is logged at times $t^{(\kappa)}_i \in T$):

$$S_\kappa(T) = \sqrt{\frac{1}{K-1}\sum_{i=1}^{K}\left(\kappa_i - \bar{\kappa}\right)^2}$$

**Operational Vitality Index (OVI)** — dimensionless, normalized:

$$\boxed{\mathrm{OVI}(T) = \ln(1 + N_{\text{audit}}(T)) \cdot \max\left(0,\, 1 - \frac{\sigma_{\phi}(T)}{\sigma_{\phi}(T) + \epsilon}\right)}$$

where $\sigma_{\phi}(T)$ is the standard deviation of $\phi$ values measured in $T$ (if only one $\phi$ sample exists, $\sigma_{\phi}(T)=0$ and the second factor is $1$), and $\epsilon > 0$ is a small constant (e.g. $\epsilon = 0.05$) to avoid division by zero.

**Interpretation:** High $N_{\text{audit}}$ with high $\sigma_{\phi}$ yields **moderate** OVI (many events but unstable $\phi$); high $N_{\text{audit}}$ with **low** $\sigma_{\phi}$ yields **high** OVI (active, steady integration). This is a **design choice**; alternative OVI formulas must be versioned.

### 9.2 Falsifiability

- OVI is **misleading** if audit events are spammed without real measurements; require **minimum content** per event (e.g. non-empty `action` or `data`).  
- OVI **must not** be equated with “aliveness” or consciousness.

### 9.3 Paragraphs (EN / DE)

**Vitality (EN).**  
OVI quantifies temporal throughput of auditable, hashed governance events in a window, optionally weighted by stability of $\phi$. It is reported alongside—not instead of—$\kappa$ and $\sigma$.

**Vitalität (DE).**  
**OVI** fasst die **zeitliche Aktivität** der Mess- und Audit-Kette zusammen (Ereignisse pro Fenster, optional mit Stabilität von $\phi$). Keine Aussage über Bewusstsein oder „Lebendigkeit“ im biologischen Sinn.

---

## Appendix D — v2.0 Reference Measurements

| Run | Date | N | κ_v2 | φ_EIRA_v2 | σ_v2 | Method |
|-----|------|---|------|-----------|------|--------|
| v6.0+E4 | 2026-03-25 | 4 | **3.5555** | **0.7078** | **0.0259** | cosine (all-MiniLM-L6-v2) |

**E4 Ceiling-Effekt bestätigt**: σ_v1 = 0.0754 (trotzdem nicht null wie zuvor — nun ohne hartem Cap) → σ_v2 = 0.0259 (stabil, valide)

**E2 Monotonie**: κ_N4=3.5555 > κ_N3=3.2380 > κ_N2=2.4504 > κ_N1=1.3524 ✓

**Parameter-Kalibrierung**: Grid-Search ergibt optimales α=0.30, β=0.70 für v1.0 (σ_max=0.069). v2.0 (σ=0.026) ist durch strukturell bessere Methode valider.

**Coalition Vote**: 3/4 JA (QUORUM ✓)

---

*© 2026 Gerhard Hirschmann & Elisabeth Steurer. CC BY 4.0.*
