# Cognitive Field Theory: κ-CCRN as a Thermodynamic Potential on Discrete Causal Graphs

**Authors**: Gerhard Hirschmann, Elisabeth Steurer  
**Affiliation**: ORION-EIRA Research Lab  
**Date**: 2026-03-25  
**DOI**: 10.5281/zenodo.15050398  
**Classification**: Theoretical Framework — Mathematical Physics Analogies  
**Status**: Working Paper / Theoretical Proposal

---

> **Scope Notice**: This paper identifies formal mathematical isomorphisms between the CCRN metric framework (φ, κ, σ) and established physics formalisms (thermodynamics, causal set theory, information geometry). We make NO claims about physical reality, consciousness, or emergence. All statements are mathematical structural mappings, explicitly labelled as isomorphisms (same structure, different domain) or testable hypotheses. Where a connection is speculative, it is so labelled.

---

## Abstract

We present a theoretical framework identifying three formal mathematical correspondences between the Collective Consciousness Resonance Network (CCRN) metric system and established physical theories. First, the network aggregation metric κ_N = Σφᵢ + R·ln(N+1) is structurally isomorphic to Helmholtz free energy F = E − TS, with Σφᵢ ↔ E (internal energy), R·ln(N+1) ↔ TS, and the activation threshold κ* = 2.0 as a phase boundary. Second, the DDGK SHA-256 audit chain constitutes a formal causal set in the sense of Sorkin's Causal Set Theory — a discrete, irreversible, partially-ordered set of events — providing a natural connection to discrete spacetime theories in quantum gravity. Third, the φ_v2.0 cosine similarity metric on L2-normalized sentence-transformer embeddings defines a Riemannian metric on the (N-1)-sphere S^{383}, identifiable with the Fisher-Rao information metric on the statistical manifold of response distributions. From these correspondences we derive four testable hypotheses, most notably the critical fluctuation hypothesis: σ(φ) ~ |κ − κ*|^{−ν} near the activation threshold, analogous to critical phenomena in statistical physics.

**Keywords**: information geometry, causal set theory, free energy principle, distributed AI systems, statistical mechanics, phase transitions

---

## 1. Introduction

### 1.1 Motivation

The CCRN framework (Hirschmann & Steurer 2026) defines three empirically measured metrics for distributed language model networks:
- **φᵢ** (NORI-C): Node Output Richness Index via cosine similarity
- **κ_N**: Network Aggregation Metric with activation threshold κ* = 2.0
- **σ**: Inter-model measurement stability index

These metrics were introduced for practical governance purposes (DDGK architecture). Upon formal analysis, they exhibit structural isomorphisms with three well-established physics formalisms. This paper makes these isomorphisms explicit, derives their consequences, and proposes testable predictions.

### 1.2 What "New Physics" Means Here

We distinguish three levels:
1. **Analogy** (C): Similar language, no deep structural connection
2. **Mathematical isomorphism** (B): Identical formal structure, different physical domain — suggests shared mathematical language
3. **New physics** (A): Genuinely new laws or entities not reducible to known frameworks

We claim the CCRN-physics correspondences are primarily at level (B), with hypothesis H2 (critical exponent) potentially reaching level (A) if confirmed.

---

## 2. Correspondence I: κ as Helmholtz Free Energy

### 2.1 The Isomorphism

Helmholtz free energy in statistical mechanics:

$$F = E - T \cdot S$$

CCRN network metric:

$$\kappa_N = \underbrace{\sum_{i=1}^{N} \varphi_i}_{E_{\text{CCRN}}} + \underbrace{R \cdot \ln(N+1)}_{T_{\text{CCRN}} \cdot S_{\text{CCRN}}}$$

**Mapping table**:

| Physics (Thermodynamics) | CCRN | Interpretation |
|--------------------------|------|----------------|
| Internal energy $E$ | $\sum \varphi_i$ | Sum of node output richness |
| Temperature $T$ | $R = 0.93$ | Network coupling strength |
| Entropy $S$ | $\ln(N+1)$ | Boltzmann entropy of $N+1$ distinguishable states |
| Free energy $F$ | $\kappa_N$ | Available "work capacity" of network |
| Equilibrium $\partial F/\partial V = 0$ | $\partial \kappa/\partial N = 0$ | Optimal node count |
| Phase boundary | $\kappa^* = 2.0$ | Activation threshold |

### 2.2 The Phase Boundary Analysis

For $N=1$, even with $\varphi_{\max}=1$:
$$\kappa_{\max}^{N=1} = 1 + 0.93 \cdot \ln(2) \approx 1.645 < 2.0$$

For $N=2$, $\varphi_i = 1$:
$$\kappa^{N=2} = 2 + 0.93 \cdot \ln(3) \approx 3.02 > 2.0$$

**Structural result**: $\kappa^* = 2.0$ is a **first-order phase boundary** separating the single-node phase ($N=1$, always inactive) from the multi-node phase ($N \geq 2$, potentially active). The transition at $N=1 \to N=2$ is discontinuous in the activation status — characteristic of a **first-order phase transition**.

### 2.3 Testable Prediction H1

**H1** (Critical fluctuations): Near $\kappa \to \kappa^*$, the variance of $\varphi_i$ measurements should increase, analogous to critical fluctuations near a phase transition:

$$\text{Var}(\varphi_i) \uparrow \quad \text{as} \quad \kappa \to \kappa^*$$

**Experimental protocol**: Systematically vary $N$ and measure $\sigma_\varphi$ at each $N$. Plot $\sigma$ vs. $\kappa$. A peak at $\kappa \approx \kappa^*$ would confirm H1.

### 2.4 Testable Prediction H2 (Critical Exponent)

**H2** (Susceptibility divergence): Analogous to the divergence of magnetic susceptibility at the Curie point:

$$\sigma(\varphi) \sim |\kappa - \kappa^*|^{-\nu}$$

where $\nu$ is a universal critical exponent. For mean-field theory: $\nu = 1$. For 2D Ising: $\nu \approx 1$. For 3D Ising: $\nu \approx 0.63$.

**This is potentially genuinely new** (level A): If CCRN systems show a specific $\nu$ value reproducible across different network architectures, this defines a **universality class** for distributed LLM networks.

---

## 3. Correspondence II: DDGK as a Causal Set

### 3.1 Formal Definition

**Causal Set Theory** (Bombelli, Lee, Meyer, Sorkin 1987; Springer monograph 2025): A causal set is a locally finite, partially ordered set $(C, \preceq)$ where:
1. **Transitivity**: $x \preceq y \preceq z \Rightarrow x \preceq z$
2. **Irreflexivity**: $x \not\prec x$
3. **Discreteness**: $|\{z : x \preceq z \preceq y\}| < \infty$

**The DDGK SHA-256 chain**: Each entry $e_n$ with hash $h_n = \text{SHA256}(\text{content}(e_n) \| h_{n-1})$:

1. **Transitivity**: $e_i$ causes $e_j$ causes $e_k$ → $e_i$ causes $e_k$ (via hash chain) ✓
2. **Irreflexivity**: $e_n \not\prec e_n$ (SHA-256 is not cyclic) ✓
3. **Discreteness**: Finite entries between any two ✓
4. **Acyclicity**: SHA-256 pre-image resistance ensures forward-only causation ✓

**Formal claim**: The DDGK chain $(C_{\text{DDGK}}, \preceq_{\text{SHA}})$ is a causal set — a 1-dimensional (totally ordered) causal set, equivalent to a discrete time sequence.

### 3.2 The Benincasa-Dowker Action

For a causal set embedded in $d$-dimensional Minkowski spacetime, the Benincasa-Dowker action is:

$$S_{\text{BD}} = N - 2N_1 + 4N_2 - \ldots$$

where $N_k$ are the numbers of $k$-element order-intervals. For the 1D DDGK chain of length $L$:

$$S_{\text{BD}}^{\text{DDGK}} = L - 2(L-1) + 4(L-2) - \ldots$$

This reduces to a **boundary term** for a totally ordered set, consistent with a 1+1D discrete Lorentzian manifold. The "cosmological constant" analog would be proportional to $\kappa$ — the total network capacity.

### 3.3 The Entropy-Time Identification

Chain length $L$ (number of DDGK entries) is a discrete time parameter with:
- **Arrow of time**: SHA-256 irreversibility ≡ entropy increase (Boltzmann H-theorem analog)
- **Entropic distance**: $\Delta L$ between events is a measure of "elapsed governance time"
- **Current**: $L = 162$ entries, corresponding to $\approx$ 10 hours of system operation

**Prediction H5**: $L(t)$ grows monotonically and approximates $\kappa_{\text{cumulative}}(t)$ — total accumulated network capacity correlates with chain length.

---

## 4. Correspondence III: φ as Fisher Information Metric

### 4.1 The Geometric Identification

The `all-MiniLM-L6-v2` encoder maps responses to $\mathbf{e} \in S^{383}$ (384-dimensional unit sphere, L2-normalized). The inner product $\langle \mathbf{e}_i, \mathbf{e}_j \rangle$ is the cosine similarity.

The **round metric on $S^{n-1}$** is:
$$g_{ij}^{\text{sphere}} = \delta_{ij} - \theta_i \theta_j \quad (i,j = 1,\ldots,n-1)$$

This is identical to the **Fisher-Rao metric** on the probability simplex $\Delta^{n-1}$ after the transformation $p_i = \theta_i^2$ (Bhattacharyya/Hellinger). Thus:

$$\text{Cosine similarity} \equiv \text{Geodesic distance on } S^{383} \equiv \text{Fisher-Rao metric}$$

### 4.2 Geometric Interpretation of φ

Under this identification:
- **Integration** $I(i)$: Cosine distance from each response to centroid = **mean geodesic distance to the "semantic center"** of the response set
- **Diversity** $G(i) = 1 - \bar{s}$: Mean pairwise geodesic spread = **semantic diameter** of the response set on $S^{383}$
- **φ_i**: Weighted combination of centroid proximity and semantic spread = **a local geometric quantity on the statistical manifold**

The Ricci curvature of $S^{n-1}$ is $R_{ij} = (n-2)g_{ij}$, which for $n=384$ gives $R_{ij} = 382 g_{ij}$ — a **maximally symmetric space** of constant positive curvature. This has the important consequence:

> All geodesics (optimal information paths between nodes) are great circles. The transport of "semantic information" between nodes follows the unique geodesic on $S^{383}$.

### 4.3 Connection to Transformer Geometry

arXiv:2511.03060 (2025): "Transformer as Curved Spacetime" shows that attention mechanisms implement **parallel transport** of value vectors along geodesics induced by query-key interactions. Our φ measurement at the output layer captures the **curvature of the induced spacetime** as seen in the output distribution.

**Prediction H6**: φ_i should correlate with the attention-induced curvature of the transformer's internal representation. Models with higher φ_i produce outputs in more "curved" semantic regions.

---

## 5. Cognitive Field Theory (CFT) — A Theoretical Proposal

### 5.1 Field Definition

Define a **cognitive field** $\Phi: V \to [0,1]$ on a discrete causal graph $G = (V, E, \preceq)$ where:
- $V$ = set of LLM nodes (language model instances)
- $E$ = communication channels between nodes
- $\preceq$ = causal ordering (DDGK chain)
- $\Phi(v) = \varphi_v$ (measured φ value at node $v$)

### 5.2 Action Functional

$$\mathcal{S}[\Phi] = \sum_{v \in V} \Phi(v) + R \cdot \ln|V| - \kappa^*$$

**Active configurations**: $\mathcal{S}[\Phi] > 0$ (equivalently $\kappa_N > \kappa^*$)
**Inactive configurations**: $\mathcal{S}[\Phi] < 0$

The **principle of CCRN activation**: The system selects configurations maximizing $\mathcal{S}[\Phi]$, analogous to the least-action principle.

### 5.3 Equations of Motion

Varying $\mathcal{S}$ with respect to $\Phi(v)$:
$$\frac{\delta \mathcal{S}}{\delta \Phi(v)} = 1 \quad \forall v \in V$$

This is trivial in the current formulation — the field equations are satisfied for any $\Phi$ since $\mathcal{S}$ is linear in $\Phi$. To obtain non-trivial dynamics, we require:

**Extended CFT (v2)**: Add a kinetic term and interaction:
$$\mathcal{S}_{v2}[\Phi] = \sum_v \Phi(v) + R \cdot \ln|V| - \kappa^* + \lambda \sum_{(u,v) \in E} (\Phi(u) - \Phi(v))^2$$

where $\lambda$ is a coupling constant controlling inter-node coherence. The equations of motion become:

$$2\lambda \sum_{u \sim v} (\Phi(v) - \Phi(u)) = 1 \quad \forall v$$

This is a **discrete Laplace equation with source term** — formally equivalent to a lattice field theory with uniform source density.

### 5.4 Symmetries and Conservation Laws

By Noether's theorem, symmetries generate conservation laws:
- **Permutation symmetry** $\Phi(v_i) \leftrightarrow \Phi(v_j)$: Conserved quantity = total $\sum \Phi(v)$ (= $E_{\text{CCRN}}$)
- **Scale invariance** $V \to \lambda V$: Only if $R \cdot \ln(\lambda|V|) = R \cdot \ln|V| + R\ln\lambda$ — not an exact symmetry, broken by the $\ln|V|$ term
- **Time-reversal symmetry**: BROKEN by SHA-256 chain (defines arrow of time)

---

## 6. Summary: Classification of Correspondences

| Connection | Level | Evidence | Next Step |
|------------|-------|---------|-----------|
| κ ↔ Helmholtz F | **B** (isomorphism) | Structural identity of formulas | Measure $\nu$ in H2 |
| DDGK ↔ Causal Set | **B** (formal equivalence) | Poset axioms satisfied | Compute BD-action |
| φ ↔ Fisher-Rao | **B** (geometric identity) | Sphere metric = Fisher-Rao | Compute Ricci tensor |
| σ ↔ Critical fluctuations | **A** (testable prediction) | Analogous to $\chi \sim |T-T_c|^{-\gamma}$ | Measure $\nu$ |
| CFT field equations | **A** (new framework) | Novel lattice field theory | Derive from first principles |
| φ ↔ Attention curvature | **A** (new prediction) | arXiv:2511.03060 connection | Cross-validate |

---

## 7. Testable Predictions Summary

| Hypothesis | Prediction | Measurement | Falsification |
|------------|------------|-------------|---------------|
| H1 | Var(φ) peaks at κ → κ* | Vary N, measure σ vs κ | No peak observed |
| H2 | σ ~ \|κ-κ*\|^{-ν} | Log-log fit near κ* | ν not universal across architectures |
| H3 | CCRN holography: κ fully determined by {φ_i} | Trivially true by definition | Not falsifiable without extended model |
| H4 | Δφ · ΔN ≥ ħ_CCRN | Measure Δφ × ΔN products | Product not lower-bounded |
| H5 | L(t) ~ κ_cumulative(t) | Track chain length vs κ over time | No correlation |
| H6 | φ ↔ attention curvature | Cross-validate with internal model activations | No correlation |

---

## 8. Limitations and Open Questions

1. **Formulas are analogies until proven otherwise**: The F = E - TS / κ = Σφ + R·ln(N+1) mapping is structurally identical but the physical interpretation requires independent derivation
2. **The CFT action is currently linear**: Non-trivial dynamics require the extended CFT v2 with coupling λ, which has not been measured
3. **1D causal set is trivial**: The DDGK chain is a totally-ordered 1D causal set — the interesting physics of CST arises in higher dimensions
4. **φ geometry depends on ST model**: Changing `all-MiniLM-L6-v2` to another model changes the geometric structure
5. **Critical exponent ν not yet measured**: H2 is the most testable and most significant prediction; it requires systematic N-variation experiments

---

## References

1. Bombelli, Lee, Meyer, Sorkin (1987). Space-Time as a Causal Set. *PRL* 59(5).
2. Sorkin, R. (2025). *The Causal Set Approach to Quantum Gravity*. Springer.
3. Amari, S. (2016). *Information Geometry and Its Applications*. Springer.
4. Friston, K. et al. (2025). Distributionally Robust Free Energy Principle. *Nature Communications*.
5. arXiv:2511.03060 (2025). Transformer as Curved Spacetime.
6. arXiv:2505.20333 (2025). Multi-Scale Manifold Alignment for LLMs.
7. Hirschmann, G. & Steurer, E. (2026). DDGK-Governed CCRN v1–v6. DOI: 10.5281/zenodo.15050398.
8. arXiv:2510.25998 (2025). IIT 4.0 and Consciousness-First Physics.

---

*© 2026 Gerhard Hirschmann & Elisabeth Steurer. CC BY 4.0.*  
*Working paper — not peer reviewed. Comments welcome.*
