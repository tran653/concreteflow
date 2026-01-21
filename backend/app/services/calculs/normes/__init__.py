"""
Module de calcul multi-normes pour structures béton.

Normes supportées:
- Eurocode 2 (EC2) : Norme européenne actuelle
- ACI 318 : American Concrete Institute (USA)
- BAEL 91 : Béton Armé aux États Limites (France, historique)
- BS 8110 : British Standard (UK, historique)
- CSA A23.3 : Canadian Standards Association
"""

from enum import Enum


class NormeType(str, Enum):
    """Types de normes de calcul supportées."""
    # Les noms correspondent aux valeurs stockées en DB
    EC2 = "EC2"
    ACI318 = "ACI318"
    BAEL91 = "BAEL91"
    BS8110 = "BS8110"
    CSA_A23 = "CSA_A23"

    @property
    def display_name(self) -> str:
        """Nom d'affichage de la norme."""
        names = {
            "EC2": "Eurocode 2 (EN 1992-1-1)",
            "ACI318": "ACI 318 (USA)",
            "BAEL91": "BAEL 91 (France)",
            "BS8110": "BS 8110 (UK)",
            "CSA_A23": "CSA A23.3 (Canada)",
        }
        return names.get(self.value, self.value)

    @property
    def region(self) -> str:
        """Région d'application de la norme."""
        regions = {
            "EC2": "Europe",
            "ACI318": "États-Unis",
            "BAEL91": "France",
            "BS8110": "Royaume-Uni",
            "CSA_A23": "Canada",
        }
        return regions.get(self.value, "International")


from .base import NormeBase
from .eurocode import EurocodeNorme
from .aci318 import ACI318Norme
from .bael import BAELNorme
from .factory import NormeFactory

__all__ = [
    "NormeType",
    "NormeBase",
    "EurocodeNorme",
    "ACI318Norme",
    "BAELNorme",
    "NormeFactory",
]
