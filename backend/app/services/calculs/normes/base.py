"""
Classe abstraite de base pour les normes de calcul béton.

Toutes les normes doivent implémenter cette interface pour assurer
la compatibilité avec le moteur de calcul.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, List


@dataclass
class BetonProperties:
    """Propriétés du béton selon la norme."""
    classe: str
    fck: float  # Résistance caractéristique cylindrique (MPa)
    fcm: float  # Résistance moyenne (MPa)
    fctm: float  # Résistance moyenne en traction (MPa)
    fctk_005: float  # Fractile 5% traction (MPa)
    Ecm: float  # Module d'élasticité (GPa)
    epsilon_cu: float  # Déformation ultime (‰)


@dataclass
class AcierProperties:
    """Propriétés de l'acier pour armatures."""
    classe: str
    fy: float  # Limite d'élasticité caractéristique (MPa)
    fu: float  # Résistance en traction (MPa)
    Es: float  # Module d'élasticité (GPa)
    epsilon_uk: float  # Déformation ultime caractéristique (‰)


@dataclass
class FlexionResult:
    """Résultat d'un calcul de flexion."""
    moment_resistant: float  # kN.m
    section_acier: float  # cm²
    profondeur_axe_neutre: float  # m
    bras_levier: float  # m
    mu: float  # moment réduit
    mu_limite: float  # moment réduit limite
    verification_ok: bool
    message: str


@dataclass
class CisaillementResult:
    """Résultat d'un calcul de cisaillement."""
    effort_sollicitant: float  # kN
    effort_resistant_beton: float  # kN
    effort_resistant_acier: float  # kN
    section_armatures_transversales: float  # cm²/m
    espacement_cadres: float  # mm
    verification_ok: bool
    message: str


@dataclass
class FlecheResult:
    """Résultat d'un calcul de flèche."""
    fleche_instantanee: float  # mm
    fleche_differee: float  # mm
    fleche_totale: float  # mm
    fleche_limite: float  # mm
    verification_ok: bool
    message: str


class NormeBase(ABC):
    """
    Classe abstraite pour les normes de calcul béton.

    Chaque norme doit implémenter les méthodes de calcul
    selon ses propres formules et coefficients.
    """

    def __init__(self):
        self._beton: Optional[BetonProperties] = None
        self._acier: Optional[AcierProperties] = None

    @property
    @abstractmethod
    def code(self) -> str:
        """Code court de la norme (ex: EC2, ACI318)."""
        pass

    @property
    @abstractmethod
    def nom_complet(self) -> str:
        """Nom complet de la norme."""
        pass

    @property
    @abstractmethod
    def region(self) -> str:
        """Région d'application."""
        pass

    # ==================== Coefficients de sécurité ====================

    @property
    @abstractmethod
    def gamma_c(self) -> float:
        """Coefficient partiel de sécurité pour le béton."""
        pass

    @property
    @abstractmethod
    def gamma_s(self) -> float:
        """Coefficient partiel de sécurité pour l'acier."""
        pass

    @property
    @abstractmethod
    def gamma_g(self) -> float:
        """Coefficient partiel pour les charges permanentes."""
        pass

    @property
    @abstractmethod
    def gamma_q(self) -> float:
        """Coefficient partiel pour les charges variables."""
        pass

    # ==================== Classes de matériaux ====================

    @abstractmethod
    def get_classes_beton(self) -> List[str]:
        """Retourne la liste des classes de béton disponibles."""
        pass

    @abstractmethod
    def get_classes_acier(self) -> List[str]:
        """Retourne la liste des classes d'acier disponibles."""
        pass

    @abstractmethod
    def set_beton(self, classe: str) -> None:
        """Définit la classe de béton à utiliser."""
        pass

    @abstractmethod
    def set_acier(self, classe: str) -> None:
        """Définit la classe d'acier à utiliser."""
        pass

    # ==================== Propriétés de calcul ====================

    @property
    def beton(self) -> BetonProperties:
        """Propriétés du béton sélectionné."""
        if self._beton is None:
            raise ValueError("Béton non défini. Appeler set_beton() d'abord.")
        return self._beton

    @property
    def acier(self) -> AcierProperties:
        """Propriétés de l'acier sélectionné."""
        if self._acier is None:
            raise ValueError("Acier non défini. Appeler set_acier() d'abord.")
        return self._acier

    @property
    def fcd(self) -> float:
        """Résistance de calcul du béton en compression (MPa)."""
        return self.beton.fck / self.gamma_c

    @property
    def fyd(self) -> float:
        """Résistance de calcul de l'acier (MPa)."""
        return self.acier.fy / self.gamma_s

    @property
    def coefficient_equivalence(self) -> float:
        """Coefficient d'équivalence acier/béton."""
        return self.acier.Es / self.beton.Ecm

    # ==================== Calculs de flexion ====================

    @abstractmethod
    def calcul_flexion(
        self,
        moment_elu: float,  # kN.m
        largeur: float,  # m
        hauteur: float,  # m
        enrobage: float = 0.03  # m
    ) -> FlexionResult:
        """
        Calcule la section d'acier nécessaire en flexion simple.

        Args:
            moment_elu: Moment fléchissant à l'ELU (kN.m)
            largeur: Largeur de la section (m)
            hauteur: Hauteur totale de la section (m)
            enrobage: Enrobage des armatures (m)

        Returns:
            FlexionResult avec section d'acier et vérifications
        """
        pass

    @abstractmethod
    def calcul_moment_resistant(
        self,
        section_acier: float,  # cm²
        largeur: float,  # m
        hauteur: float,  # m
        enrobage: float = 0.03  # m
    ) -> float:
        """
        Calcule le moment résistant pour une section d'acier donnée.

        Args:
            section_acier: Section d'acier (cm²)
            largeur: Largeur de la section (m)
            hauteur: Hauteur totale de la section (m)
            enrobage: Enrobage des armatures (m)

        Returns:
            Moment résistant (kN.m)
        """
        pass

    # ==================== Calculs de cisaillement ====================

    @abstractmethod
    def calcul_cisaillement(
        self,
        effort_tranchant: float,  # kN
        largeur: float,  # m
        hauteur: float,  # m
        enrobage: float = 0.03,  # m
        section_acier_tendu: float = 0  # cm²
    ) -> CisaillementResult:
        """
        Calcule les armatures de cisaillement nécessaires.

        Args:
            effort_tranchant: Effort tranchant à l'ELU (kN)
            largeur: Largeur de la section (m)
            hauteur: Hauteur totale de la section (m)
            enrobage: Enrobage des armatures (m)
            section_acier_tendu: Section d'acier longitudinal tendu (cm²)

        Returns:
            CisaillementResult avec armatures transversales
        """
        pass

    # ==================== Calculs de flèche ====================

    @abstractmethod
    def calcul_fleche(
        self,
        portee: float,  # m
        moment_els: float,  # kN.m
        largeur: float,  # m
        hauteur: float,  # m
        section_acier: float,  # cm²
        enrobage: float = 0.03  # m
    ) -> FlecheResult:
        """
        Calcule la flèche et vérifie les limites.

        Args:
            portee: Portée de l'élément (m)
            moment_els: Moment à l'ELS (kN.m)
            largeur: Largeur de la section (m)
            hauteur: Hauteur totale de la section (m)
            section_acier: Section d'acier tendu (cm²)
            enrobage: Enrobage des armatures (m)

        Returns:
            FlecheResult avec flèches et vérification
        """
        pass

    @abstractmethod
    def fleche_limite(self, portee: float) -> float:
        """
        Retourne la flèche limite admissible selon la norme.

        Args:
            portee: Portée de l'élément (m)

        Returns:
            Flèche limite (mm)
        """
        pass

    # ==================== Enrobage ====================

    @abstractmethod
    def enrobage_minimal(
        self,
        classe_exposition: str,
        diametre_barre: float = 12  # mm
    ) -> float:
        """
        Calcule l'enrobage minimal selon la classe d'exposition.

        Args:
            classe_exposition: Classe d'exposition (XC1, XC2, etc.)
            diametre_barre: Diamètre des armatures (mm)

        Returns:
            Enrobage minimal (mm)
        """
        pass

    # ==================== Combinaisons de charges ====================

    def combinaison_elu(
        self,
        g: float,  # Charges permanentes (kN/m ou kN/m²)
        q: float   # Charges d'exploitation (kN/m ou kN/m²)
    ) -> float:
        """
        Calcule la combinaison ELU fondamentale.

        Args:
            g: Charges permanentes
            q: Charges d'exploitation

        Returns:
            Charge combinée ELU
        """
        return self.gamma_g * g + self.gamma_q * q

    def combinaison_els(
        self,
        g: float,  # Charges permanentes
        q: float   # Charges d'exploitation
    ) -> float:
        """
        Calcule la combinaison ELS caractéristique.

        Args:
            g: Charges permanentes
            q: Charges d'exploitation

        Returns:
            Charge combinée ELS
        """
        return g + q

    # ==================== Utilitaires ====================

    def to_dict(self) -> Dict:
        """Retourne les paramètres de la norme sous forme de dictionnaire."""
        return {
            "code": self.code,
            "nom_complet": self.nom_complet,
            "region": self.region,
            "coefficients": {
                "gamma_c": self.gamma_c,
                "gamma_s": self.gamma_s,
                "gamma_g": self.gamma_g,
                "gamma_q": self.gamma_q,
            },
            "beton": self._beton.__dict__ if self._beton else None,
            "acier": self._acier.__dict__ if self._acier else None,
        }
