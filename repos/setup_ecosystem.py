#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ORION Ökosystem Setup & Validierung
====================================

Führe dieses Skript aus um die Integration zu testen.
"""

import sys
import os
from pathlib import Path

# Stelle sicher dass Unicode auf Windows funktioniert
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Füge Integrations-Modul zum Path hinzu
integration_path = Path(__file__).parent / "integration"
sys.path.insert(0, str(integration_path))

from ecosystem_manager import initialize_ecosystem


def main():
    """Hauptprogramm"""
    print("\n" + "="*70)
    print("[SETUP] ORION Ökosystem Setup")
    print("="*70 + "\n")
    
    # Bestimme Repos-Verzeichnis
    repos_dir = Path(__file__).parent
    
    print(f"[INFO] Repos Verzeichnis: {repos_dir}\n")
    
    # Initialisiere Ökosystem
    success = initialize_ecosystem(repos_dir)
    
    if success:
        print("\n[OK] Setup erfolgreich abgeschlossen!")
        print("\nDu kannst jetzt folgende Imports verwenden:")
        print("  from repos.integration import get_ecosystem_manager")
        print("  from repos.integration import ConsciousnessTheoryIntegration")
        print("  from repos.integration import ProofChainIntegration")
        return 0
    else:
        print("\n[ERROR] Setup mit Fehlern abgeschlossen")
        print("Überprüfe die Ausgabe oben für Details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
