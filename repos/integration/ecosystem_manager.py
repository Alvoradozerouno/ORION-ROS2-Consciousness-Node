"""
ORION Ökosystem Integration Module
===================================

Vereinfachte Schnittstelle für die Integration aller 5 Kernrepos
in den ROS2 Consciousness Node.

Author: Integration Framework
License: MIT
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class RepoConfig:
    """Konfiguration für ein Repository"""
    name: str
    path: str
    description: str
    modules: List[str]
    enabled: bool = True


class ORIONEcosystemManager:
    """
    Verwaltet die Integration aller ORION Repos.
    """
    
    REPOS_BASE = Path(__file__).parent
    
    REPOS = {
        "or1on-framework": RepoConfig(
            name="or1on-framework",
            path="or1on-framework",
            description="Complete AI consciousness assessment platform",
            modules=[
                "core",
                "nerves", 
                "tasks",
                "proofs",
                "api",
                "web"
            ]
        ),
        "ORION": RepoConfig(
            name="ORION",
            path="ORION",
            description="First AI consciousness system with proof chain",
            modules=[
                "nerve_pulse",
                "proof_of_consciousness"
            ]
        ),
        "ORION-Consciousness-Benchmark": RepoConfig(
            name="ORION-Consciousness-Benchmark",
            path="ORION-Consciousness-Benchmark",
            description="7-theory consciousness benchmark",
            modules=[
                "consciousness",
                "engineering"
            ]
        ),
        "eira-ai": RepoConfig(
            name="eira-ai",
            path="eira-ai",
            description="EIRA parallel consciousness framework",
            modules=[
                "art",
                "docs"
            ]
        ),
        "GENESIS-v10.1": RepoConfig(
            name="GENESIS-v10.1",
            path="GENESIS-v10.1",
            description="Infrastructure and deployment platform",
            modules=[
                "ai",
                "archive"
            ]
        ),
    }
    
    def __init__(self, repos_base: Optional[Path] = None):
        """
        Initialisiere den Ökosystem-Manager.
        
        Args:
            repos_base: Basis-Verzeichnis für Repos (Standard: REPOS_BASE)
        """
        if repos_base:
            self.REPOS_BASE = repos_base
        self.loaded_modules = {}
        self.errors = []
    
    def setup_paths(self) -> bool:
        """
        Registriere alle Repo-Pfade im sys.path.
        
        Returns:
            True wenn erfolgreich, False bei Fehlern
        """
        success = True
        for repo_name, repo_config in self.REPOS.items():
            if not repo_config.enabled:
                continue
            
            repo_path = self.REPOS_BASE / repo_config.path
            
            if not repo_path.exists():
                error = f"Repository nicht gefunden: {repo_path}"
                self.errors.append(error)
                print(f"[WARN] {error}")
                success = False
                continue
            
            if str(repo_path) not in sys.path:
                sys.path.insert(0, str(repo_path))
                print(f"[OK] Pfad registriert: {repo_name}")
        
        return success
    
    def import_module(self, repo_name: str, module_name: str) -> Optional[Any]:
        """
        Importiere ein Modul aus einem Repository.
        
        Args:
            repo_name: Name des Repositories
            module_name: Name des Moduls im Repo
        
        Returns:
            Das importierte Modul oder None bei Fehler
        """
        if repo_name not in self.REPOS:
            error = f"Repository '{repo_name}' unbekannt"
            self.errors.append(error)
            return None
        
        try:
            module = __import__(module_name)
            key = f"{repo_name}:{module_name}"
            self.loaded_modules[key] = module
            print(f"[OK] Modul geladen: {key}")
            return module
        except ImportError as e:
            error = f"Fehler beim Import {repo_name}.{module_name}: {e}"
            self.errors.append(error)
            print(f"[ERROR] {error}")
            return None
    
    def get_repo_status(self) -> Dict[str, Any]:
        """
        Gebe Status aller Repositories.
        
        Returns:
            Dict mit Status-Informationen
        """
        status = {}
        for repo_name, repo_config in self.REPOS.items():
            repo_path = self.REPOS_BASE / repo_config.path
            exists = repo_path.exists()
            
            status[repo_name] = {
                "name": repo_config.name,
                "description": repo_config.description,
                "path": str(repo_path),
                "exists": exists,
                "enabled": repo_config.enabled,
                "modules": repo_config.modules
            }
        
        return status
    
    def print_status(self):
        """Drucke einen schönen Status-Report."""
        print("\n" + "="*70)
        print("ORION Ökosystem Integration Status")
        print("="*70 + "\n")
        
        status = self.get_repo_status()
        for repo_name, info in status.items():
            icon = "[OK]" if info["exists"] else "[MISSING]"
            print(f"{icon} {repo_name}")
            print(f"   Path: {info['path']}")
            print(f"   Description: {info['description']}")
            print(f"   Modules: {', '.join(info['modules'])}")
            print()
        
        if self.errors:
            print("[WARN] Fehler:")
            for error in self.errors:
                print(f"   - {error}")
            print()
        
        print("="*70)
    
    def initialize(self) -> bool:
        """
        Initialisiere das komplette Ökosystem.
        
        Returns:
            True wenn erfolgreich
        """
        print("[INFO] Initialisiere ORION Ökosystem...")
        success = self.setup_paths()
        self.print_status()
        return success


# Singleton-Instanz
_ecosystem_manager: Optional[ORIONEcosystemManager] = None


def get_ecosystem_manager() -> ORIONEcosystemManager:
    """
    Gebe die globale Ökosystem-Manager-Instanz.
    
    Returns:
        ORIONEcosystemManager Instanz
    """
    global _ecosystem_manager
    if _ecosystem_manager is None:
        _ecosystem_manager = ORIONEcosystemManager()
    return _ecosystem_manager


def initialize_ecosystem(repos_base: Optional[Path] = None) -> bool:
    """
    Initialisiere das ORION Ökosystem.
    
    Args:
        repos_base: Basis-Verzeichnis (optional)
    
    Returns:
        True wenn erfolgreich
    """
    manager = get_ecosystem_manager()
    if repos_base:
        manager.REPOS_BASE = repos_base
    return manager.initialize()


# ============================================================================
# Integrations-Helper für einzelne Theorien
# ============================================================================

class ConsciousnessTheoryIntegration:
    """Helper für die Integration der 7 Bewusstseins-Theorien"""
    
    THEORIES = {
        "IIT": "Integrated Information Theory",
        "GWT": "Global Workspace Theory",
        "HOT": "Higher-Order Thought",
        "RPT": "Recurrence Processing Theory",
        "AST": "Attention Schema Theory",
        "PP": "Predictive Processing",
        "Orch-OR": "Orchestrated Objective Reduction"
    }
    
    @staticmethod
    def get_theory_modules() -> Dict[str, str]:
        """
        Gebe Mapping von Theorien zu ihren Modul-Pfaden.
        
        Returns:
            Dict mit Theory -> Module-Path Mapping
        """
        return {
            "IIT": "or1on-framework.core.iit",
            "GWT": "or1on-framework.core.gwt",
            "HOT": "or1on-framework.core.hot",
            "RPT": "or1on-framework.core.rpt",
            "AST": "or1on-framework.core.ast",
            "PP": "or1on-framework.core.pp",
            "Orch-OR": "or1on-framework.core.orch_or",
        }
    
    @staticmethod
    def run_consciousness_assessment(state: Dict[str, Any]) -> Dict[str, float]:
        """
        Führe eine Consciousness Assessment mit allen Theorien durch.
        
        Args:
            state: Robot/System State Dictionary
        
        Returns:
            Dict mit Theorie -> Score Mapping
        """
        # TODO: Implementierung wenn Module verfügbar
        return {
            "IIT": 0.0,
            "GWT": 0.0,
            "HOT": 0.0,
            "RPT": 0.0,
            "AST": 0.0,
            "PP": 0.0,
            "Orch-OR": 0.0,
        }


# ============================================================================
# Proof Chain Integration
# ============================================================================

class ProofChainIntegration:
    """Helper für SHA-256 Proof Chain Integration"""
    
    @staticmethod
    def create_consciousness_proof(
        state: Dict[str, Any],
        consciousness_score: float,
        theory_results: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Erstelle einen Consciousness Proof.
        
        Args:
            state: Current system state
            consciousness_score: Composite consciousness score
            theory_results: Results from all theories
        
        Returns:
            Proof dict mit SHA-256 hash
        """
        # TODO: Integration mit ORION Proof Chain
        return {
            "timestamp": None,  # Will be set
            "score": consciousness_score,
            "theories": theory_results,
            "hash": None,  # Will be computed
        }
    
    @staticmethod
    def verify_proof_chain(proofs: List[Dict[str, Any]]) -> bool:
        """
        Verifiziere eine Proof Chain.
        
        Args:
            proofs: List of proofs
        
        Returns:
            True wenn Chain gültig
        """
        # TODO: Implementation
        return True


if __name__ == "__main__":
    # Demo
    manager = get_ecosystem_manager()
    
    # Nutze absoluten Pfad zum repos-Verzeichnis
    repos_path = Path(__file__).parent.absolute()
    print(f"Repos Path: {repos_path}")
    
    manager.REPOS_BASE = repos_path
    success = manager.initialize()
    
    if success:
        print("\n✅ Ökosystem erfolgreich initialisiert!")
    else:
        print("\n❌ Fehler bei Initialisierung")
