"""
Eurocode 2 (EC2) - Calcul des structures en béton.
NF EN 1992-1-1 : Règles générales et règles pour les bâtiments.

Ce module implémente les paramètres et coefficients de l'Eurocode 2.
"""
import math
from typing import Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class BetonProperties:
    """Propriétés du béton selon EC2 Table 3.1."""
    classe: str
    fck: float  # Résistance caractéristique cylindrique (MPa)
    fck_cube: float  # Résistance caractéristique cubique (MPa)
    fcm: float  # Résistance moyenne (MPa)
    fctm: float  # Résistance moyenne en traction (MPa)
    fctk_005: float  # Fractile 5% traction (MPa)
    fctk_095: float  # Fractile 95% traction (MPa)
    Ecm: float  # Module d'élasticité sécant (GPa)
    epsilon_c1: float  # Déformation au pic (‰)
    epsilon_cu1: float  # Déformation ultime (‰)


# Table 3.1 EC2 - Propriétés des bétons
BETON_PROPERTIES: Dict[str, BetonProperties] = {
    "C20/25": BetonProperties("C20/25", 20, 25, 28, 2.2, 1.5, 2.9, 30, 2.0, 3.5),
    "C25/30": BetonProperties("C25/30", 25, 30, 33, 2.6, 1.8, 3.3, 31, 2.1, 3.5),
    "C30/37": BetonProperties("C30/37", 30, 37, 38, 2.9, 2.0, 3.8, 33, 2.2, 3.5),
    "C35/45": BetonProperties("C35/45", 35, 45, 43, 3.2, 2.2, 4.2, 34, 2.25, 3.5),
    "C40/50": BetonProperties("C40/50", 40, 50, 48, 3.5, 2.5, 4.6, 35, 2.3, 3.5),
    "C45/55": BetonProperties("C45/55", 45, 55, 53, 3.8, 2.7, 4.9, 36, 2.4, 3.5),
    "C50/60": BetonProperties("C50/60", 50, 60, 58, 4.1, 2.9, 5.3, 37, 2.45, 3.5),
}


@dataclass
class AcierProperties:
    """Propriétés de l'acier pour armatures."""
    classe: str
    fyk: float  # Limite d'élasticité caractéristique (MPa)
    ftk: float  # Résistance en traction (MPa)
    Es: float  # Module d'élasticité (GPa)
    epsilon_uk: float  # Déformation ultime caractéristique (‰)


ACIER_PROPERTIES: Dict[str, AcierProperties] = {
    "S400": AcierProperties("S400", 400, 440, 200, 25),
    "S500": AcierProperties("S500", 500, 550, 200, 25),
    "S500B": AcierProperties("S500B", 500, 540, 200, 50),
    "S500C": AcierProperties("S500C", 500, 575, 200, 75),
}


class EurocodeCalculator:
    """
    Calculateur selon Eurocode 2.
    Gère les paramètres nationaux français (AN).
    """

    def __init__(self, norme: str = "EC2"):
        self.norme = norme

        # Coefficients partiels (AN français)
        self.gamma_c = 1.5  # Béton (situations durables)
        self.gamma_s = 1.15  # Acier (situations durables)
        self.gamma_g = 1.35  # Actions permanentes (défavorables)
        self.gamma_q = 1.5  # Actions variables (défavorables)

        # Coefficients pour ELS
        self.psi_0 = 0.7  # Valeur de combinaison
        self.psi_1 = 0.5  # Valeur fréquente
        self.psi_2 = 0.3  # Valeur quasi-permanente

        # Propriétés matériaux par défaut
        self.beton: BetonProperties = BETON_PROPERTIES["C30/37"]
        self.acier: AcierProperties = ACIER_PROPERTIES["S500"]

    def set_materials(self, classe_beton: str, classe_acier: str = "S500"):
        """Définit les matériaux utilisés."""
        if classe_beton in BETON_PROPERTIES:
            self.beton = BETON_PROPERTIES[classe_beton]
        else:
            raise ValueError(f"Classe de béton inconnue: {classe_beton}")

        if classe_acier in ACIER_PROPERTIES:
            self.acier = ACIER_PROPERTIES[classe_acier]
        else:
            raise ValueError(f"Classe d'acier inconnue: {classe_acier}")

    @property
    def fck(self) -> float:
        """Résistance caractéristique du béton (MPa)."""
        return self.beton.fck

    @property
    def fcd(self) -> float:
        """Résistance de calcul du béton en compression (MPa)."""
        alpha_cc = 1.0  # Coefficient AN français
        return alpha_cc * self.fck / self.gamma_c

    @property
    def fctm(self) -> float:
        """Résistance moyenne en traction du béton (MPa)."""
        return self.beton.fctm

    @property
    def fctd(self) -> float:
        """Résistance de calcul en traction du béton (MPa)."""
        alpha_ct = 1.0
        return alpha_ct * self.beton.fctk_005 / self.gamma_c

    @property
    def Ecm(self) -> float:
        """Module d'élasticité du béton (GPa)."""
        return self.beton.Ecm

    @property
    def fyk(self) -> float:
        """Limite d'élasticité caractéristique de l'acier (MPa)."""
        return self.acier.fyk

    @property
    def fyd(self) -> float:
        """Résistance de calcul de l'acier (MPa)."""
        return self.fyk / self.gamma_s

    @property
    def Es(self) -> float:
        """Module d'élasticité de l'acier (GPa)."""
        return self.acier.Es

    def coefficient_equivalence(self) -> float:
        """Coefficient d'équivalence acier/béton n = Es/Ecm."""
        return self.Es / self.Ecm

    def profondeur_axe_neutre(
        self,
        moment_elu: float,  # kN.m
        largeur: float,  # m
        hauteur_utile: float  # m
    ) -> Tuple[float, float]:
        """
        Calcule la profondeur de l'axe neutre et le bras de levier.

        Returns:
            (x, z) : profondeur axe neutre et bras de levier en m
        """
        b = largeur * 1000  # mm
        d = hauteur_utile * 1000  # mm
        Mu = moment_elu * 1e6  # N.mm

        # Moment réduit
        mu = Mu / (b * d**2 * self.fcd)

        # Vérification mu < mu_lim (pivot B)
        mu_lim = 0.372  # Pour bétons <= C50/60

        if mu > mu_lim:
            raise ValueError(
                f"Section insuffisante: μ={mu:.3f} > μ_lim={mu_lim}"
            )

        # Profondeur relative de l'axe neutre
        alpha = 1.25 * (1 - math.sqrt(1 - 2 * mu))

        # Bras de levier
        z = d * (1 - 0.4 * alpha)

        return alpha * d / 1000, z / 1000  # Retour en m

    def section_acier_flexion(
        self,
        moment_elu: float,  # kN.m
        bras_levier: float  # m
    ) -> float:
        """
        Calcule la section d'acier nécessaire en flexion simple.

        Returns:
            Section d'acier en cm²
        """
        Mu = moment_elu * 1e3  # kN.m -> N.m
        z = bras_levier  # m
        fyd = self.fyd * 1e6  # MPa -> Pa

        As = Mu / (z * fyd)  # m²
        return As * 1e4  # cm²

    def verification_fleche(
        self,
        portee: float,  # m
        fleche_calculee: float  # mm
    ) -> Tuple[bool, float]:
        """
        Vérifie la flèche selon EC2 §7.4.

        Returns:
            (ok, fleche_limite) : vérification et limite en mm
        """
        # Limite EC2 : L/250 pour aspect + L/500 pour dommages
        # On prend généralement L/250
        limite = portee * 1000 / 250  # mm

        return fleche_calculee <= limite, limite

    def enrobage_minimal(
        self,
        classe_exposition: str = "XC1",
        diametre_barre: float = 12  # mm
    ) -> float:
        """
        Calcule l'enrobage minimal selon EC2 §4.4.

        Returns:
            Enrobage minimal en mm
        """
        # Enrobage minimal pour adhérence
        c_min_b = diametre_barre

        # Enrobage minimal pour durabilité (simplifié)
        c_min_dur = {
            "XC1": 15,
            "XC2": 25,
            "XC3": 25,
            "XC4": 30,
            "XD1": 35,
            "XD2": 40,
            "XS1": 35,
            "XS2": 40,
        }.get(classe_exposition, 25)

        c_min = max(c_min_b, c_min_dur, 10)

        # Marge (AN français)
        delta_c_dev = 10  # mm

        return c_min + delta_c_dev
