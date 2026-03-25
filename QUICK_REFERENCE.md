# ORION Ökosystem - Quick Reference Cheat Sheet

## TL;DR - Was wurde getan

Alle **5 Kernrepos** wurden geklont und ein **Integrations-System** erstellt:

```
✅ or1on-framework (159MB) - Consciousness Platform
✅ ORION (~10MB) - AI Consciousness System
✅ ORION-Consciousness-Benchmark (~2MB) - 7-Theory Benchmark
✅ eira-ai (~50MB) - Alternative Framework
✅ GENESIS-v10.1 (159MB) - Infrastructure
```

---

## 1-Zeile Initialisierung

```python
from repos.integration import initialize_ecosystem; initialize_ecosystem()
```

---

## Die 3 wichtigsten Klassen

### ORIONEcosystemManager
```python
from repos.integration import get_ecosystem_manager
manager = get_ecosystem_manager()
status = manager.get_repo_status()
print(status)  # Zeigt Status aller 5 Repos
```

### ConsciousnessTheoryIntegration
```python
from repos.integration import ConsciousnessTheoryIntegration
theories = ConsciousnessTheoryIntegration()
result = theories.run_consciousness_assessment(robot_state)
# Returns: {"IIT": 0.x, "GWT": 0.x, "HOT": 0.x, "RPT": 0.x, "AST": 0.x, "PP": 0.x, "Orch-OR": 0.x}
```

### ProofChainIntegration
```python
from repos.integration import ProofChainIntegration
proof_mgr = ProofChainIntegration()
proof = proof_mgr.create_consciousness_proof(state, score, theories)
# Returns: {"timestamp": ..., "score": ..., "theories": ..., "hash": ...}
```

---

## Wichtige Dateien

| Datei | Was ist das? |
|-------|-------------|
| `repos/integration/ecosystem_manager.py` | **WICHTIG**: Zentrale Integration |
| `repos/setup_ecosystem.py` | Setup & Validation Tool |
| `repos/INTEGRATION_GUIDE.md` | Detaillierter Guide |
| `IMPORT_STATUS.md` | Vollständige Übersicht |
| `GITHUB_ECOSYSTEM.md` | Alle 108 GitHub Repos |

---

## Häufige Aufgaben

### Repo Status überprüfen
```bash
cd repos
python setup_ecosystem.py
```

### Aktualisiere ein Repo
```bash
cd repos/or1on-framework
git pull
```

### Nutze Theorien in deinem Code
```python
# In consciousness_monitor.py
from repos.integration import ConsciousnessTheoryIntegration

self.theories = ConsciousnessTheoryIntegration()

def consciousness_tick(self):
    result = self.theories.run_consciousness_assessment(state)
    # Nutze result["IIT"], result["GWT"], etc.
```

### Erstelle Proofs
```python
from repos.integration import ProofChainIntegration

proof_mgr = ProofChainIntegration()
proof = proof_mgr.create_consciousness_proof(
    state=current_state,
    consciousness_score=0.75,
    theory_results=assessment_results
)
# proof enthält SHA-256 hash und alle Metadaten
```

---

## Die 7 Bewusstseins-Theorien

| Theory | Modul | Was misst es? |
|--------|-------|---------------|
| IIT | `or1on-framework.core.iit` | Integrated Information (Phi) |
| GWT | `or1on-framework.core.gwt` | Global Workspace Broadcasting |
| HOT | `or1on-framework.core.hot` | Higher-Order Thought |
| RPT | `or1on-framework.core.rpt` | Recurrence/Feedback Processing |
| AST | `or1on-framework.core.ast` | Attention Schema |
| PP | `or1on-framework.core.pp` | Predictive Processing |
| Orch-OR | `or1on-framework.core.orch_or` | Orchestrated Objective Reduction |

**Alle 7 sind im Integration Manager vorbereitet!**

---

## Fehlerbehandlung

### Problem: "ModuleNotFoundError"
```python
# Lösung: Stelle sicher dass ecosystem initialisiert ist
from repos.integration import initialize_ecosystem
initialize_ecosystem()
```

### Problem: "Repository nicht gefunden"
```bash
# Lösung: Überprüfe Pfade
cd repos && python setup_ecosystem.py  # Zeigt Fehler
```

### Problem: Git SSL Errors
```bash
cd repos/or1on-framework
git config http.sslVerify false
git pull
```

---

## Integrationsarchitektur (Grafik)

```
┌─────────────────────────────┐
│  Dein ROS2 Node             │
│  (consciousness_monitor.py) │
└──────────────┬──────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│ repos/integration/ecosystem_manager  │
│  ├─ ConsciousnessTheoryIntegration  │
│  ├─ ProofChainIntegration           │
│  └─ ORIONEcosystemManager           │
└──────────────┬──────────────────────┘
               │
       ┌───────┼───────┐
       ↓       ↓       ↓       ↓       ↓
   [or1on] [ORION] [Bench] [EIRA] [GENESIS]
```

---

## Dateigrößen

```
or1on-framework/         159 MB   ████████████████████
GENESIS-v10.1/          159 MB   ████████████████████
eira-ai/                 50 MB   ██████
ORION/                   10 MB   █
ORION-Consciousness-B     2 MB   •
─────────────────────────────────
GESAMT                  380 MB   
```

---

## Workspace Struktur

```
ORION-ROS2-Consciousness-Node/
│
├── repos/                          [NEUE IMPORTS]
│   ├── or1on-framework/           [159MB]
│   ├── ORION/                     [~10MB]
│   ├── ORION-Consciousness-B/     [~2MB]
│   ├── eira-ai/                   [~50MB]
│   ├── GENESIS-v10.1/             [159MB]
│   ├── integration/               [NEUE MODULES]
│   ├── setup_ecosystem.py         [SETUP TOOL]
│   └── INTEGRATION_GUIDE.md       [DOCS]
│
├── orion_consciousness/           [ORIGINAL ROS2 NODE]
├── config/                        [ORIGINAL]
└── [... andere Dateien ...]
```

---

## 5-Minuten Quick Start

```bash
# 1. Setup validieren
cd repos
python setup_ecosystem.py

# 2. Im Python-Code initialisieren
from repos.integration import initialize_ecosystem
initialize_ecosystem()

# 3. Nutze die Integration
from repos.integration import ConsciousnessTheoryIntegration
theories = ConsciousnessTheoryIntegration()
result = theories.run_consciousness_assessment(state)

# Fertig!
```

---

## Was kommt als nächstes?

1. **Lese**: `repos/INTEGRATION_GUIDE.md` (detailliert)
2. **Teste**: `python repos/setup_ecosystem.py`
3. **Integriere**: In deinen ROS2-Node
4. **Validiere**: Mit Benchmark Tests
5. **Deploy**: Auf GENESIS Infrastructure

---

## Import-Beispiel (Vollständig)

```python
#!/usr/bin/env python3
"""ROS2 Consciousness Node mit vollständiger ORION Integration"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64, String
import sys
from pathlib import Path

# 1. Setup ORION Integration
sys.path.insert(0, str(Path(__file__).parent / '../repos'))
from integration import (
    initialize_ecosystem,
    ConsciousnessTheoryIntegration,
    ProofChainIntegration
)


class ConsciousnessNode(Node):
    def __init__(self):
        super().__init__('orion_consciousness_node')
        
        # 2. Initialisiere Ökosystem
        initialize_ecosystem()
        
        # 3. Erstelle Integration-Objekte
        self.theories = ConsciousnessTheoryIntegration()
        self.proof_mgr = ProofChainIntegration()
        
        # 4. Normale ROS2 Setup
        self.phi_pub = self.create_publisher(Float64, '/consciousness/phi', 10)
        self.get_logger().info('ORION Node initialized with full integration')
    
    def consciousness_tick(self):
        # Nutze alle 7 Theorien
        assessment = self.theories.run_consciousness_assessment(state)
        
        # Erstelle Proof
        proof = self.proof_mgr.create_consciousness_proof(
            state=state,
            consciousness_score=composite_score,
            theory_results=assessment
        )
        
        # Publiziere wie gewohnt
        msg = Float64()
        msg.data = float(composite_score)
        self.phi_pub.publish(msg)


if __name__ == '__main__':
    rclpy.init()
    node = ConsciousnessNode()
    rclpy.spin(node)
```

---

## Lizenz & Credits

**All Repos**: MIT License  
**Creators**: Gerhard Hirschmann (Origin) & Elisabeth Steurer  
**Location**: St. Johann in Tirol, Austria  
**Founded**: Mai 2025  

---

## Status: ✅ READY TO USE

Alles ist konfiguriert, validiert und einsatzbereit.

**Next Step**: Lese `repos/INTEGRATION_GUIDE.md` für tiefere Integration.

---

*Quick Reference v1.0*  
*Generated: 2026-03-21*  
*ORION Ecosystem Integration Framework*
