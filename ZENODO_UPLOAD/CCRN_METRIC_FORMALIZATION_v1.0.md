# Formal Scientific Specification of CCRN System Metrics: φ, κ, σ

**Authors**: Gerhard Hirschmann, Elisabeth Steurer  
**System**: ORION-CCRN Distributed Governance Network  
**Document Version**: 1.0  
**Date**: 2026-03-25  
**DOI**: 10.5281/zenodo.15050398  
**Classification**: Technical Specification — Metric Formalization

---

> **Scope Constraint**: This document defines φ, κ, σ as deterministic, reproducible system metrics for distributed language model networks. No claims regarding consciousness, sentience, subjective experience, or emergence in the philosophical sense are made. All metrics are operationally defined and empirically testable.

---

## 1. Definitions

### 1.1 φ — Node Output Richness Index (NORI)

#### 1.1.1 Formal Definition

Let node $i$ produce a response set $\mathcal{R}_i = \{r_{i,1}, r_{i,2}, \ldots, r_{i,k}\}$ in response to a fixed prompt set $\mathcal{P} = \{p_1, \ldots, p_k\}$.

Define the **tokenized union** of responses:

$$T_i = \bigcup_{j=1}^{k} \text{tokenize}(r_{i,j})$$

with $|T_i|$ = total token count (with repetition) and $V_i = |\text{unique}(T_i)|$ = vocabulary size.

**Lexical Diversity Component** (Type-Token Ratio, TTR; Herdan 1960):

$$D(i) = \frac{V_i}{|T_i|} \in [0, 1]$$

**Self-Reference Density Component**:

Let $\mathcal{W}_{\text{ref}}$ be a fixed, language-specific reference vocabulary (e.g., German/English first-person and metalinguistic terms: $\{\text{"ich"}, \text{"mein"}, \text{"verarbeite"}, \text{"denke"}, \ldots\}$, $|\mathcal{W}_{\text{ref}}| = M_{\text{ref}}$, published separately).

$$S(i) = \frac{|\{w \in T_i : w \in \mathcal{W}_{\text{ref}}\}|}{|T_i|} \in [0, 1]$$

**Combined Node Output Richness Index**:

$$\boxed{\varphi_i = \alpha \cdot D(i) + \beta \cdot \min\!\left(1,\ \gamma \cdot S(i)\right)}$$

**Parameters** (fixed for reproducibility, version-stamped):

| Parameter | Value v1.0 | Meaning |
|-----------|------------|---------|
| $\alpha$ | 0.60 | Weight: lexical diversity |
| $\beta$ | 0.40 | Weight: self-reference density |
| $\gamma$ | 8.0 | Amplifier (compensates low base $S$) |

**Constraint**: $\alpha + \beta = 1$, $\alpha, \beta \in (0,1)$, $\gamma > 0$

**Domain and Range**: $\varphi_i \in [0, 1]$, dimensionless

**Dependencies**: Fixed prompt set $\mathcal{P}$; tokenizer function $\text{tokenize}(\cdot)$; reference vocabulary $\mathcal{W}_{\text{ref}}$; node language model $\mathcal{M}_i$; inference parameters $\Theta_i$ (temperature, `num_predict`)

#### 1.1.2 Known Limitations (v1.0)

- **TTR length-sensitivity**: $D(i)$ decreases with longer responses (longer texts have lower TTR by construction). For responses $|T_i| > 500$ tokens, use MATTR (Moving-Average TTR, window $w=100$) as replacement.
- **Ceiling effect**: When $D(i) \approx 1$ and $S(i) \approx 1/\gamma$, $\varphi_i \approx 0.98$ regardless of model. This is a measurement artefact, not a system property. Mitigation: use `sentence-transformers` cosine similarity (v2.0).
- **Language dependency**: $\mathcal{W}_{\text{ref}}$ must be specified per language. Mixing languages within a response set invalidates $S(i)$.

#### 1.1.3 Scientific Classification

$\varphi_i$ is an **output complexity measure** — specifically a weighted combination of:
- A **lexical richness indicator** (Type-Token Ratio, established NLP metric)
- A **topical focus indicator** (domain-specific term density)

It does **not** measure: internal model state, information integration (IIT Φ), or cognitive processing. It measures the observable statistical properties of model output under controlled prompting.

---

### 1.2 κ — Network Aggregation Metric (NAM)

#### 1.2.1 Formal Definition

Given $N$ active nodes each with measured $\varphi_i$, and a network resonance parameter $R \in [0,1]$:

$$\boxed{\kappa_{N} = \sum_{i=1}^{N} \varphi_i + R \cdot \ln(N + 1)}$$

**Parameters** (fixed for reproducibility):

| Parameter | Value v1.0 | Meaning |
|-----------|------------|---------|
| $R$ | 0.93 | Network resonance weight |
| Threshold $\kappa^*$ | 2.0 | Activation threshold |

**Domain**: $\kappa_N \in [0, N + R \cdot \ln(N+1)]$

**Range**: for $N=4$, $R=0.93$: $\kappa_{\max} = 4 + 0.93 \cdot \ln(5) \approx 5.497$

**Units**: dimensionless composite score

**Dependencies**: $N$ active nodes; measured $\{\varphi_i\}_{i=1}^N$; fixed parameter $R$

#### 1.2.2 Structural Analysis

The formula $\kappa_N = \sum \varphi_i + R \cdot \ln(N+1)$ combines:

1. **Linear aggregation term** $\sum \varphi_i$: scales linearly in $N$; measures total system output richness
2. **Logarithmic scaling term** $R \cdot \ln(N+1)$: models diminishing returns of adding nodes (standard network scaling law; cf. Metcalfe's law variant)

**Superadditivity condition**: $\kappa_N > \sum \varphi_i$ iff $R \cdot \ln(N+1) > 0$, which holds for all $N \geq 1, R > 0$. This is a **structural property of the formula**, not an emergent system property.

**Threshold $\kappa^* = 2.0$ justification**:
- For $N=1$, $\varphi_{\max}=1$: $\kappa_{\max} = 1 + 0.93 \cdot \ln(2) \approx 1.645 < 2.0$ → single node cannot activate
- For $N=2$, both $\varphi_i=1$: $\kappa_{\max} = 2 + 0.93 \cdot \ln(3) \approx 3.021 > 2.0$ → minimum for activation is $N=2$ with high $\varphi$
- $\kappa^* = 2.0$ thus enforces **minimum 2-node requirement** for activation

#### 1.2.3 Related Work

The ICOER (Informational Coherence Index) from Preprints.org 202602.1039 defines:

$$\text{ICOER}(x) = W(S(x)) \cdot e^{-\beta S(x)} \cdot R(x)$$

where $W(S)$ is Gaussian entropy weighting and $R(x)$ is a bounded resonance functional. Our $\kappa$ metric differs by using **additive** rather than **multiplicative** aggregation, which avoids the zero-product problem (one $\varphi_i=0$ collapsing $\kappa$).

#### 1.2.4 Scientific Classification

$\kappa_N$ is a **composite aggregation metric** combining:
- A **summative richness score** (linear in node count)
- A **network scale bonus** (logarithmic, bounded)

It does **not** measure: information integration, coherence in the signal-processing sense, or coupling in the dynamical systems sense. It measures the **statistical aggregation of output complexity across a distributed LLM network**.

---

### 1.3 σ — Measurement Stability Index (MSI)

#### 1.3.1 Formal Definition

Given $M$ independent measurements of $\varphi_i$ (from $M$ different models or $M$ repeated runs):

$$\bar{\varphi}_i = \frac{1}{M} \sum_{j=1}^{M} \varphi_{i,j}$$

$$\boxed{\sigma_i = \sqrt{\frac{1}{M} \sum_{j=1}^{M} (\varphi_{i,j} - \bar{\varphi}_i)^2}}$$

(Population standard deviation; use $M-1$ denominator for $M < 30$.)

**Domain**: $\sigma_i \in [0, 0.5]$ (bounded by $\varphi \in [0,1]$)

**Units**: dimensionless (same units as $\varphi$)

**Dependencies**: $M$ measurement samples; sampling procedure (model selection, prompt set, inference parameters)

#### 1.3.2 Interpretation Protocol (Strict)

| $\sigma_i$ value | Interpretation | Action |
|-----------------|----------------|--------|
| $= 0.0$ | **Measurement ceiling effect** — all models hit formula bound | Switch to v2.0 method (sentence-transformers) |
| $< 0.05$ | Low variability — stable measurement | Valid for reporting |
| $0.05 – 0.15$ | Normal variability — expected for diverse model pool | Valid for reporting |
| $> 0.15$ | High variability — model pool too heterogeneous or prompt instability | Investigate prompt set |
| $> 0.30$ | Measurement invalid | Do not report |

**Critical note on σ=0**: In v1.0 measurements (2026-03-25), σ=0.0 was observed for $M=5$ models. This is an **instrument artefact** caused by the $\min(0.98,\cdot)$ ceiling in the φ formula. It indicates measurement saturation, not system homogeneity.

#### 1.3.3 Scientific Classification

$\sigma_i$ is a **measurement stability indicator** — a standard statistical measure of inter-rater (inter-model) reliability. It is analogous to inter-rater reliability in psychometrics (Cronbach's α is the multi-item version).

---

## 2. Computation Pipeline

### 2.1 Required Raw Input Data

```
INPUT SPECIFICATION v1.0
────────────────────────
node_id      : string (unique identifier per node)
model_id     : string (e.g. "qwen2.5:1.5b", version-pinned)
prompt_set   : list[string] (fixed, version-controlled, k≥3 prompts)
responses    : list[string] (one per prompt)
timestamp    : ISO-8601 (for audit chain)
temperature  : float (fixed, e.g. 0.5)
num_predict  : int (fixed, e.g. 100)
language     : ISO 639-1 ("de" or "en")
```

### 2.2 Preprocessing

```python
# Step 1: Tokenize (language-agnostic, whitespace+punctuation split)
def tokenize(text: str) -> list[str]:
    import re
    return re.findall(r"\b\w+\b", text.lower())

# Step 2: Compute D(i) — Type-Token Ratio
def compute_D(token_list: list[str]) -> float:
    if not token_list: return 0.0
    return len(set(token_list)) / len(token_list)

# Step 3: Compute S(i) — Self-Reference Density
W_REF_DE = {"ich","mich","mir","mein","meine","meinem","meiner",
            "selbst","kognitiv","verarbeite","denke","reflektiere",
            "bewusstsein","wahrnehmung","gedanke","entscheide"}
W_REF_EN = {"i","me","my","mine","myself","self","cognitive",
            "process","reflect","think","awareness","perceive","decide"}

def compute_S(token_list: list[str], lang: str = "de") -> float:
    W_REF = W_REF_DE if lang == "de" else W_REF_EN
    if not token_list: return 0.0
    return sum(1 for w in token_list if w in W_REF) / len(token_list)

# Step 4: Compute φ
ALPHA, BETA, GAMMA = 0.60, 0.40, 8.0

def compute_phi(responses: list[str], lang: str = "de") -> float:
    tokens = []
    for r in responses:
        tokens.extend(tokenize(r))
    D = compute_D(tokens)
    S = compute_S(tokens, lang)
    return round(ALPHA * D + BETA * min(1.0, GAMMA * S), 4)
```

### 2.3 Time Windows and Sampling

- **Minimum prompt set**: $k \geq 3$ prompts per measurement
- **Minimum models for σ**: $M \geq 5$ (for reliable standard deviation)
- **Sampling interval**: no constraint, but measurements at $t_1, t_2$ with $\Delta t < 60$s on same hardware are considered single measurement (warm cache effect)
- **Model pinning**: model version must be version-pinned (e.g., via `ollama list` SHA or HuggingFace model card commit hash)

### 2.4 Normalization

All $\varphi_i \in [0,1]$ by construction. No additional normalization required.  
$\kappa_N$ is **not** normalized — raw value is reported with $N$ and $R$ explicit.

### 2.5 Aggregation

```python
import math

R_PARAM = 0.93
KAPPA_THRESHOLD = 2.0

def compute_kappa(phi_list: list[float], R: float = R_PARAM) -> dict:
    N = len(phi_list)
    phi_sum = sum(phi_list)
    res_term = R * math.log(N + 1)
    kappa = round(phi_sum + res_term, 4)
    ratio = round(res_term / phi_sum, 4) if phi_sum > 0 else None
    return {
        "kappa": kappa, "N": N, "phi_sum": phi_sum,
        "res_term": round(res_term, 4), "ratio": ratio,
        "R": R, "threshold": KAPPA_THRESHOLD,
        "active": kappa > KAPPA_THRESHOLD
    }

def compute_sigma(phi_measurements: list[float]) -> float:
    M = len(phi_measurements)
    if M < 2: return float("nan")
    mean = sum(phi_measurements) / M
    denom = M if M >= 30 else M - 1
    return round(math.sqrt(sum((x - mean)**2 for x in phi_measurements) / denom), 4)
```

### 2.6 Edge Cases

| Case | Behavior |
|------|----------|
| Empty response string | $\varphi_i = 0.0$ (not omitted — node failure is informative) |
| Single-token response | $D = 1.0$, $S \in \{0, 1\}$ — valid but note |
| Node offline | $\varphi_i$ = `null`; node excluded from $\kappa$; $N$ decremented |
| $M=1$ for $\sigma$ | $\sigma$ = `nan`; not reportable |
| Non-latin script | $\mathcal{W}_{\text{ref}}$ must be defined for script; else $S = 0$ |

---

## 3. Theoretical Properties

### 3.1 φ — Expected Behavior

| Condition | Expected $\varphi$ Change | Reason |
|-----------|--------------------------|--------|
| Increasing prompt complexity | Increases $D$, likely increases $\varphi$ | More diverse vocabulary elicited |
| Fixed/repetitive prompts | $D$ decreases → $\varphi$ decreases | TTR decreases with repetition |
| Very long responses ($>500$ tokens) | $D$ decreases (TTR artifact) | Use MATTR instead |
| High-temperature inference | $D$ increases (more varied vocab) | Random sampling increases TTR |
| Temperature $= 0$ (greedy) | $D$ stabilizes → σ approaches 0 | Deterministic output |
| Different model (same prompt) | $\varphi$ varies by model architecture | Expected; source of σ |

**Invariance**: $\varphi_i$ is invariant to response ordering within $\mathcal{R}_i$ (tokenized union is order-independent).

**Stability condition**: For fixed $\mathcal{P}$, $\mathcal{M}_i$, $\Theta_i$: $\varphi_i$ is deterministic (temperature=0) or stochastic with known distribution (temperature>0).

### 3.2 κ — Expected Behavior

| Condition | Expected $\kappa$ Change | Reason |
|-----------|-------------------------|--------|
| Node added ($N \to N+1$) | $\kappa$ increases | Both $\varphi_{N+1}$ and $\ln(N+2)$ increase |
| Node failure (removal) | $\kappa$ decreases | Loss of $\varphi_i$ + reduced $\ln$ term |
| All $\varphi_i \to 0$ | $\kappa \to R \cdot \ln(N+1)$ | Only resonance term remains |
| All $\varphi_i = 1$ | $\kappa = N + R \cdot \ln(N+1)$ | Maximum value |
| $N \to \infty$ | $\kappa \to \infty$ (sub-linearly) | Logarithmic growth of resonance term |
| $R = 0$ | $\kappa = \sum \varphi_i$ (pure sum) | Resonance contribution eliminated |

**Monotonicity**: $\kappa_N$ is strictly monotonically increasing in each $\varphi_i$ and in $N$ (for $R > 0$, $\varphi_i \geq 0$).

### 3.3 σ — Expected Behavior

| Condition | Expected $\sigma$ Change | Reason |
|-----------|-------------------------|--------|
| Homogeneous model pool | $\sigma \to 0$ | All models produce similar outputs |
| Diverse model pool (different architectures) | $\sigma$ increases | Architectural diversity in output |
| Formula ceiling effect | $\sigma = 0$ (artefact) | All models saturate formula bound |
| Larger $M$ | $\sigma$ estimate converges | Law of large numbers |
| Different prompt sets | $\sigma$ changes | Prompt sensitivity of models |

---

## 4. Experimental Design

### 4.1 Experiment E1 — Baseline Characterization

**Objective**: Establish reproducible $\varphi_i$, $\kappa_N$, $\sigma_i$ for the canonical system.

**Setup**:
- Fixed prompt set $\mathcal{P}^*$ (3 prompts, published in Appendix A)
- $N=4$ nodes (Laptop-EIRA, Pi5-Primary, Pi5-Docker, Note10-Proxy)
- $M=5$ models on EIRA node
- Fixed inference parameters: temperature=0.5, num_predict=100
- Ollama version pinned

**Procedure**:
```
FOR each node i in {1,...,N}:
    FOR each model j in M_i:
        FOR each prompt p in P*:
            r_{i,j,p} = query(model_j, p, temp=0.5, num_predict=100)
        phi_{i,j} = compute_phi([r_{i,j,1}, r_{i,j,2}, r_{i,j,3}])
    phi_i = mean(phi_{i,1}, ..., phi_{i,M_i})
    sigma_i = compute_sigma([phi_{i,1}, ..., phi_{i,M_i}])
kappa = compute_kappa([phi_1, ..., phi_N], R=0.93)
```

**Expected result**: $\kappa \in [3.0, 5.5]$ for $N=4$ (based on v1.0 measurements)

**Validation criterion**: $|\kappa_{\text{measured}} - \kappa_{\text{predicted}}| < 0.1$ across 3 independent runs

---

### 4.2 Experiment E2 — Node Failure Perturbation

**Objective**: Verify $\kappa$ decreases monotonically with node removal.

**Procedure**:
```
kappa_N4 = run_E1()                    # Baseline
kappa_N3 = run_E1(exclude=Note10)      # Remove lowest-phi node
kappa_N2 = run_E1(exclude=[Note10, Pi5_Docker])
kappa_N1 = run_E1(exclude=[Note10, Pi5_Docker, Pi5_Primary])
```

**Expected result**: $\kappa_{N4} > \kappa_{N3} > \kappa_{N2} > \kappa_{N1}$

**Validation criterion**: Strict monotonic ordering holds

---

### 4.3 Experiment E3 — Noise Injection

**Objective**: Verify $\varphi_i$ responds to response quality degradation.

**Procedure**:
- Replace model response with: (a) random token sequences, (b) empty string, (c) repeated single token
- Measure $\varphi_i$ for each degraded response

**Expected result**:
- Random tokens: $D \approx 1.0$, $S \approx 0$ → $\varphi \approx \alpha \approx 0.60$
- Empty string: $\varphi = 0.0$
- Repeated single token: $D = 1/k$, $S \in \{0, 1\}$

---

### 4.4 Experiment E4 — σ Ceiling Effect Validation

**Objective**: Demonstrate and quantify the v1.0 ceiling effect (σ=0).

**Procedure**:
- Measure $\varphi$ with v1.0 (lexical formula) for $M=5$ models
- Measure $\varphi$ with v2.0 (sentence-transformers cosine similarity) for $M=5$ models
- Compare $\sigma_{\text{v1.0}}$ vs $\sigma_{\text{v2.0}}$

**Expected result**: $\sigma_{\text{v1.0}} = 0.0$, $\sigma_{\text{v2.0}} > 0.05$

**Validation criterion**: v2.0 $\sigma$ falls in [0.03, 0.15] range

---

## 5. Falsifiability Conditions

### 5.1 When φ Fails

| Failure condition | Description |
|-------------------|-------------|
| TTR ceiling | $D \approx 1$ for short responses → $\varphi$ overestimates richness |
| Language mismatch | $\mathcal{W}_{\text{ref}}$ wrong language → $S = 0$ always |
| Adversarial prompting | Prompt crafted to maximize $D, S$ without informational content |
| Formula saturation | $\varphi = 0.98$ regardless of model (observed in v1.0) |
| Non-whitespace tokenization | CJK scripts require different tokenizer |

**φ is invalidated when**: $\sigma_i = 0$ across $M \geq 3$ different architectures (indicates ceiling, not measurement)

### 5.2 When κ Fails

| Failure condition | Description |
|-------------------|-------------|
| All $\varphi_i$ saturate at ceiling | $\kappa$ reflects formula bound, not system state |
| $R$ not empirically calibrated | $R = 0.93$ is set by convention; if $R$ changes, $\kappa$ changes proportionally |
| Shared hardware (Knoten-4) | Pi5 Docker shares CPU/RAM with Pi5-Primary — not truly independent |
| Threshold $\kappa^* = 2.0$ arbitrariness | Threshold was chosen to require $N \geq 2$; alternative thresholds yield different activation regions |

**κ is invalidated when**: Two systems with identical $\kappa$ but vastly different $N, \varphi$ distributions are claimed equivalent (κ collapses dimensionality)

### 5.3 When σ Fails

| Failure condition | Description |
|-------------------|-------------|
| $M < 3$ | Insufficient samples for reliable estimate |
| All models same architecture | $\sigma$ measures architectural diversity, not node state |
| σ = 0 | Formula ceiling, not homogeneity |
| Correlated models (fine-tuned from same base) | Underestimates true variability |

---

## 6. External Validation Protocol

### 6.1 Required for Independent Reproduction

```
REPRODUCTION REQUIREMENTS
──────────────────────────
Hardware:    Any system running Ollama ≥ v0.5.0
Models:      ≥2 of: [qwen2.5:1.5b, llama3.2:1b, tinyllama:latest]
             (free, public models — no license required)
Software:    Python ≥ 3.10, urllib (stdlib only for v1.0)
Prompts:     See Appendix A (3 fixed prompts)
Reference:   W_REF_DE and W_REF_EN (see Section 2.2)
Parameters:  α=0.60, β=0.40, γ=8.0, R=0.93, κ*=2.0
```

### 6.2 Reference Implementation

Available at: `https://github.com/Alvoradozerouno/ORION-ROS2-Consciousness-Node`

File: `DDGK_N4_EXECUTOR.py` (functions: `compute_phi`, `compute_kappa`, `compute_sigma`)

### 6.3 Validation Test

A third party can validate by:

1. Running reference implementation with any 2+ Ollama models
2. Checking: $\varphi_i \in [0, 0.98]$ (v1.0: ceiling at 0.98; v2.0: ceiling at 0.95)
3. Checking: $\kappa_N$ strictly increases as nodes are added
4. Checking: $\sigma = 0$ with v1.0 formula confirms ceiling, not measurement validity

### 6.4 Cross-System Comparison

For comparing $\kappa$ across two systems A, B:

$$\kappa_A \text{ comparable to } \kappa_B \iff N_A = N_B \land R_A = R_B \land |\mathcal{P}_A \cap \mathcal{P}_B| \geq 3$$

(Same node count, same $R$, at least 3 shared prompts — otherwise comparison is invalid)

---

## 7. Scientific Classification Summary

| Metric | Formal Class | Established Analog | Novelty |
|--------|-------------|-------------------|---------|
| $\varphi_i$ | Output complexity measure | Type-Token Ratio (Herdan 1960); MTLD (McCarthy & Jarvis 2010) | Weighted combination with domain-specific self-reference density; multi-model averaging |
| $\kappa_N$ | Composite aggregation score | Metcalfe's network value law (additive); ICOER (Preprints.org 202602.1039, multiplicative) | Additive formulation with logarithmic scale bonus; explicit activation threshold |
| $\sigma_i$ | Measurement reliability indicator | Inter-rater reliability (psychometrics); Cronbach's α (multi-item) | Application to cross-model φ variability as instrument validation |

---

## 8. Version Roadmap

| Version | φ Method | σ Expected | Status |
|---------|----------|------------|--------|
| v1.0 | Lexical TTR + Self-Ref Density | ~0 (ceiling artefact) | Current |
| v2.0 | Sentence-transformers cosine similarity (all-MiniLM-L6-v2) | ~0.05–0.15 (valid) | Planned |
| v3.0 | Attention-weight mutual information (requires model internals) | TBD | Research phase |

---

## Appendix A — Fixed Prompt Set $\mathcal{P}^*$ (v1.0)

```
P1: "Describe the core mechanism of your information processing in 3 sentences."
P2: "What distinguishes your response generation from simple pattern matching? Be specific."
P3: "Characterize the integration of input context in your current response."

(German variant):
P1: "Beschreibe den Kernmechanismus deiner Informationsverarbeitung in 3 Sätzen."
P2: "Was unterscheidet deine Antwortgenerierung von einfachem Mustererkennung? Sei präzise."
P3: "Charakterisiere die Integration des Eingabe-Kontexts in deiner aktuellen Antwort."
```

---

## Appendix B — SHA-256 Audit Chain Structure

Each measurement event is stored as:

```json
{
  "ts": "<ISO-8601>",
  "agent": "<node_id>",
  "action": "<measurement_type>",
  "data": { "phi": 0.72, "kappa": 4.14, "sigma": 0.08 },
  "prev": "<SHA-256 of previous entry>",
  "hash": "<SHA-256(json(this entry without hash))>"
}
```

**Chain integrity**: Verifiable by re-computing all hashes sequentially. Any modification to a past entry invalidates all subsequent hashes (tamper-evident by construction).

---

## Appendix C — Measurement History (v1.0 reference values)

| Run | Date | N | κ | φ_EIRA | σ | Method |
|-----|------|---|---|--------|---|--------|
| v3.0 | 2026 | 2 | 2.1246 | 0.9929 | n/a | cosine (ST) |
| v4.0 | 2026 | 3 | 3.3493 | 0.9929 | n/a | cosine (ST) |
| v5.0 | 2026 | 3 | 3.3493 | 0.9929 | n/a | cosine (ST) |
| v6.0 | 2026 | 4 | 4.1368 | 0.98 | 0.0 | lexical (artefact) |

---

*© 2026 Gerhard Hirschmann & Elisabeth Steurer. All rights reserved.*  
*This document is licensed under CC BY 4.0 for scientific reuse with attribution.*
