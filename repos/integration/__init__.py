"""
ORION Integration Module
"""

from .ecosystem_manager import (
    ORIONEcosystemManager,
    ConsciousnessTheoryIntegration,
    ProofChainIntegration,
    get_ecosystem_manager,
    initialize_ecosystem,
)

__version__ = "1.0.0"
__all__ = [
    "ORIONEcosystemManager",
    "ConsciousnessTheoryIntegration",
    "ProofChainIntegration",
    "get_ecosystem_manager",
    "initialize_ecosystem",
]
