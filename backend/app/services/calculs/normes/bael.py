"""
BAEL 91 - Béton Armé aux États Limites
Ancienne norme française (révisée 99)

Référence: BAEL 91 révisé 99 (DTU P18-702)

Note: Cette norme a été remplacée par l'Eurocode 2 en France mais reste
utilisée pour certains projets historiques ou dans d'autres pays francophones.
"""

import math
from typing import Dict, List

from .base import (
    NormeBase,
    BetonProperties,
    AcierProperties,
    FlexionResult,
    CisaillementResult,
    FlecheResult,
)


# Classes de béton BAEL (fc28 = résistance caractéristique à 28 jours)
BETON_BAEL: Dict[str, BetonProperties] = {
    "B20": BetonProperties("B20", 20, 27, 1.8, 1.3, 29.0, 3.5),
    "B25": BetonProperties("B25", 25, 32, 2.1, 1.5, 32.0, 3.5),
    "B30": BetonProperties("B30", 30, 38, 2.4, 1.7, 35.0, 3.5),
    "B35": BetonProperties("B35", 35, 43, 2.7, 1.9, 37.0, 3.5),
    "B40": BetonProperties("B40", 40, 48, 3.0, 2.1, 39.0, 3.5),
    "B45": BetonProperties("B45", 45, 53, 3.3, 2.3, 41.0, 3.5),
    "B50": BetonProperties("B50", 50, 58, 3.5, 2.5, 43.0, 3.5),
}

# Classes d'acier BAEL
ACIER_BAEL: Dict[str, AcierProperties] = {
    "FeE400": AcierProperties("FeE400", 400, 480, 200, 10),
    "FeE500": AcierProperties("FeE500", 500, 550, 200, 10),
    "HA400": AcierProperties("HA400 (haute adhérence)", 400, 480, 200, 10),
    "HA500": AcierProperties("HA500 (haute adhérence)", 500, 550, 200, 10),
}


class BAELNorme(NormeBase):
    """
    Implémentation de la norme BAEL 91 révisé 99.

    Principales différences avec l'Eurocode:
    - Notation fc28 au lieu de fck
    - Coefficient θ pour la durée d'application des charges
    - Diagramme parabole-rectangle pour le béton
    - Coefficient 0.85 sur fbu
    """

    def __init__(self):
        super().__init__()
        # Coefficient de durée d'application des charges
        self._theta = 1.0  # 1.0 pour t > 24h, 0.9 pour 1h < t < 24h, 0.85 pour t < 1h

    # ==================== Identité de la norme ====================

    @property
    def code(self) -> str:
        return "BAEL91"

    @property
    def nom_complet(self) -> str:
        return "BAEL 91 révisé 99 (France)"

    @property
    def region(self) -> str:
        return "France (historique)"

    # ==================== Coefficients de sécurité ====================

    @property
    def gamma_c(self) -> float:
        """Coefficient γb pour le béton (BAEL A.4.3.2)."""
        return 1.5

    @property
    def gamma_s(self) -> float:
        """Coefficient γs pour l'acier (BAEL A.4.3.2)."""
        return 1.15

    @property
    def gamma_g(self) -> float:
        """Coefficient pour charges permanentes G (BAEL A.3.1)."""
        return 1.35

    @property
    def gamma_q(self) -> float:
        """Coefficient pour charges variables Q (BAEL A.3.1)."""
        return 1.5

    # ==================== Classes de matériaux ====================

    def get_classes_beton(self) -> List[str]:
        return list(BETON_BAEL.keys())

    def get_classes_acier(self) -> List[str]:
        return list(ACIER_BAEL.keys())

    def set_beton(self, classe: str) -> None:
        if classe not in BETON_BAEL:
            raise ValueError(
                f"Classe de béton '{classe}' non reconnue pour BAEL. "
                f"Classes disponibles: {', '.join(BETON_BAEL.keys())}"
            )
        self._beton = BETON_BAEL[classe]

    def set_acier(self, classe: str) -> None:
        if classe not in ACIER_BAEL:
            raise ValueError(
                f"Classe d'acier '{classe}' non reconnue pour BAEL. "
                f"Classes disponibles: {', '.join(ACIER_BAEL.keys())}"
            )
        self._acier = ACIER_BAEL[classe]

    # ==================== Propriétés de calcul ====================

    @property
    def fcd(self) -> float:
        """Résistance de calcul fbu (BAEL A.4.3.4)."""
        # fbu = 0.85 × fc28 / (θ × γb)
        return 0.85 * self.beton.fck / (self._theta * self.gamma_c)

    @property
    def fbu(self) -> float:
        """Alias pour fcd en notation BAEL."""
        return self.fcd

    @property
    def fyd(self) -> float:
        """Résistance de calcul de l'acier σs (BAEL A.4.3.2)."""
        return self.acier.fy / self.gamma_s

    @property
    def sigma_s(self) -> float:
        """Alias pour fyd en notation BAEL."""
        return self.fyd

    # ==================== Calculs de flexion ====================

    def calcul_flexion(
        self,
        moment_elu: float,
        largeur: float,
        hauteur: float,
        enrobage: float = 0.03
    ) -> FlexionResult:
        """
        Calcul de flexion simple selon BAEL A.4.3.

        Utilise le diagramme rectangulaire simplifié.
        """
        b = largeur * 1000  # mm
        d = (hauteur - enrobage) * 1000  # mm (hauteur utile)
        Mu = moment_elu * 1e6  # N.mm

        fbu = self.fbu  # MPa
        sigma_s = self.sigma_s  # MPa

        # Moment réduit μbu = Mu / (b × d² × fbu)
        mu_bu = Mu / (b * d**2 * fbu)

        # Moment réduit limite (pivot B)
        # Pour FeE500: εsu = 10‰, εbc = 3.5‰
        # αB = εbc / (εbc + εsu) = 3.5 / (3.5 + 10) = 0.259
        # μlim = αB × (1 - 0.4 × αB) = 0.186
        epsilon_s_limite = 10  # ‰ pour aciers HA
        epsilon_bc = 3.5  # ‰
        alpha_limite = epsilon_bc / (epsilon_bc + epsilon_s_limite)
        mu_limite = alpha_limite * (1 - 0.4 * alpha_limite)

        if mu_bu > mu_limite:
            return FlexionResult(
                moment_resistant=0,
                section_acier=0,
                profondeur_axe_neutre=0,
                bras_levier=0,
                mu=mu_bu,
                mu_limite=mu_limite,
                verification_ok=False,
                message=f"Section insuffisante (BAEL): μbu = {mu_bu:.3f} > μlim = {mu_limite:.3f}. "
                        f"Augmenter les dimensions ou ajouter des aciers comprimés (A')."
            )

        # Profondeur relative de l'axe neutre
        # α = 1.25 × (1 - √(1 - 2μbu))
        alpha = 1.25 * (1 - math.sqrt(1 - 2 * mu_bu))

        # Bras de levier z = d × (1 - 0.4α)
        z = d * (1 - 0.4 * alpha)

        # Section d'acier As = Mu / (z × σs)
        As = Mu / (z * sigma_s)  # mm²
        As_cm2 = As / 100  # cm²

        # Moment résistant
        Mr = As * z * sigma_s / 1e6  # kN.m

        return FlexionResult(
            moment_resistant=Mr,
            section_acier=As_cm2,
            profondeur_axe_neutre=alpha * d / 1000,  # m
            bras_levier=z / 1000,  # m
            mu=mu_bu,
            mu_limite=mu_limite,
            verification_ok=True,
            message=f"Flexion vérifiée (BAEL): μbu = {mu_bu:.3f} ≤ μlim = {mu_limite:.3f}"
        )

    def calcul_moment_resistant(
        self,
        section_acier: float,
        largeur: float,
        hauteur: float,
        enrobage: float = 0.03
    ) -> float:
        """Calcule le moment résistant pour une section d'acier donnée."""
        As = section_acier * 100  # cm² -> mm²
        b = largeur * 1000  # mm
        d = (hauteur - enrobage) * 1000  # mm

        fbu = self.fbu
        sigma_s = self.sigma_s

        # Position de l'axe neutre par équilibre
        # 0.8 × y × b × fbu = As × σs
        y = As * sigma_s / (0.8 * b * fbu)

        # Bras de levier
        z = d - 0.4 * y

        # Moment résistant
        Mr = As * z * sigma_s / 1e6  # kN.m

        return Mr

    # ==================== Calculs de cisaillement ====================

    def calcul_cisaillement(
        self,
        effort_tranchant: float,
        largeur: float,
        hauteur: float,
        enrobage: float = 0.03,
        section_acier_tendu: float = 0
    ) -> CisaillementResult:
        """
        Calcul de l'effort tranchant selon BAEL A.5.1.

        Vérifie τu ≤ τu_lim et calcule les armatures transversales.
        """
        Vu = effort_tranchant * 1000  # N
        b0 = largeur * 1000  # mm
        d = (hauteur - enrobage) * 1000  # mm

        fc28 = self.beton.fck  # MPa

        # Contrainte tangente conventionnelle
        tau_u = Vu / (b0 * d)  # MPa

        # Contrainte limite (BAEL A.5.1.2)
        # τu_lim = min(0.2 × fc28 / γb, 5 MPa) pour fissuration peu préjudiciable
        tau_u_lim = min(0.2 * fc28 / self.gamma_c, 5.0)

        if tau_u > tau_u_lim:
            return CisaillementResult(
                effort_sollicitant=effort_tranchant,
                effort_resistant_beton=0,
                effort_resistant_acier=0,
                section_armatures_transversales=0,
                espacement_cadres=0,
                verification_ok=False,
                message=f"Section insuffisante pour cisaillement (BAEL): τu = {tau_u:.2f} MPa > "
                        f"τu,lim = {tau_u_lim:.2f} MPa"
            )

        # Résistance du béton seul
        # τu0 = 0.07 × fc28 / γb (sans armatures d'effort tranchant)
        tau_u0 = 0.07 * fc28 / self.gamma_c

        Vu0 = tau_u0 * b0 * d / 1000  # kN

        if effort_tranchant <= Vu0:
            return CisaillementResult(
                effort_sollicitant=effort_tranchant,
                effort_resistant_beton=Vu0,
                effort_resistant_acier=0,
                section_armatures_transversales=0,
                espacement_cadres=0,
                verification_ok=True,
                message=f"Cisaillement vérifié par le béton (BAEL): Vu = {effort_tranchant:.1f} kN ≤ "
                        f"Vu0 = {Vu0:.1f} kN"
            )

        # Armatures transversales nécessaires
        # At/st = (τu - τu0) × b0 / (0.9 × fe/γs)
        # Avec fe = limite élastique des cadres
        fe_cadres = min(self.acier.fy, 400)  # Limité à 400 MPa pour les cadres
        sigma_st = fe_cadres / self.gamma_s

        At_st = (tau_u - tau_u0) * b0 / (0.9 * sigma_st)  # mm²/mm

        # Convertir en cm²/m
        At_m = At_st * 1000 / 100  # cm²/m

        # Espacement pour cadres HA8 (2 brins = 100.6 mm²)
        At_cadre = 100.6  # mm²
        st = At_cadre / At_st  # mm

        # Espacement max (BAEL A.5.1.2.3)
        st_max = min(0.9 * d, 400)  # mm
        st = min(st, st_max)

        # Résistance avec ces armatures
        Vt = (At_cadre / st) * 0.9 * d * sigma_st / 1000  # kN
        Vu_resist = Vu0 + Vt

        return CisaillementResult(
            effort_sollicitant=effort_tranchant,
            effort_resistant_beton=Vu0,
            effort_resistant_acier=Vt,
            section_armatures_transversales=At_m,
            espacement_cadres=round(st, 0),
            verification_ok=True,
            message=f"Cisaillement vérifié avec armatures (BAEL): Vu = {effort_tranchant:.1f} kN ≤ "
                    f"Vn = {Vu_resist:.1f} kN. Cadres HA8 @ {st:.0f} mm"
        )

    # ==================== Calculs de flèche ====================

    def calcul_fleche(
        self,
        portee: float,
        moment_els: float,
        largeur: float,
        hauteur: float,
        section_acier: float,
        enrobage: float = 0.03
    ) -> FlecheResult:
        """
        Calcul de flèche selon BAEL B.6.5.

        Méthode simplifiée avec coefficient de flèche.
        """
        L = portee * 1000  # mm
        b = largeur * 1000  # mm
        h = hauteur * 1000  # mm
        d = h - enrobage * 1000  # mm
        As = section_acier * 100  # mm²
        M_ser = moment_els * 1e6  # N.mm

        fc28 = self.beton.fck
        # Module instantané Ei = 11000 × fc28^(1/3)
        Ei = 11000 * fc28**(1/3)  # MPa
        Es = self.acier.Es * 1000  # MPa
        n = Es / Ei  # Coefficient d'équivalence instantané

        # Inertie de la section brute
        I0 = b * h**3 / 12  # mm⁴

        # Moment de fissuration
        # ft28 = 0.6 + 0.06 × fc28
        ft28 = 0.6 + 0.06 * fc28  # MPa
        v = h / 2  # mm
        Mcr = ft28 * I0 / v  # N.mm

        if M_ser <= 0:
            return FlecheResult(
                fleche_instantanee=0,
                fleche_differee=0,
                fleche_totale=0,
                fleche_limite=self.fleche_limite(portee),
                verification_ok=True,
                message="Pas de moment appliqué"
            )

        # Inertie fissurée
        rho = As / (b * d)
        alpha = -n * rho + math.sqrt((n * rho)**2 + 2 * n * rho)
        y1 = alpha * d
        If = b * y1**3 / 3 + n * As * (d - y1)**2  # mm⁴

        # Coefficient μ (BAEL B.6.5.2)
        if M_ser < Mcr:
            mu = 1.0
            I_eff = I0
        else:
            mu = max(0, 1 - 1.75 * ft28 / (4 * rho * (M_ser * v / I0) + ft28))
            I_eff = 1.1 * I0 / (1 + (1.1 * I0 / If - 1) * mu)

        # Flèche instantanée (poutre simple, charge uniforme)
        q_eq = 8 * M_ser / L**2
        f_inst = 5 * q_eq * L**4 / (384 * Ei * I_eff)  # mm

        # Flèche différée
        # Module différé Ev = Ei / 3 (approximation)
        lambda_v = 2.0  # Coefficient de fluage
        f_diff = f_inst * lambda_v

        f_totale = f_inst + f_diff
        f_limite = self.fleche_limite(portee)

        return FlecheResult(
            fleche_instantanee=round(f_inst, 2),
            fleche_differee=round(f_diff, 2),
            fleche_totale=round(f_totale, 2),
            fleche_limite=f_limite,
            verification_ok=f_totale <= f_limite,
            message=f"Flèche totale = {f_totale:.1f} mm {'≤' if f_totale <= f_limite else '>'} "
                    f"L/500 = {f_limite:.1f} mm (BAEL)"
        )

    def fleche_limite(self, portee: float) -> float:
        """Flèche limite selon BAEL B.6.5.3: L/500 + 0.5 cm."""
        # BAEL: max(L/500, 0.5 cm) pour les planchers
        return max(portee * 1000 / 500, 5)  # mm

    # ==================== Enrobage ====================

    def enrobage_minimal(
        self,
        classe_exposition: str,
        diametre_barre: float = 12
    ) -> float:
        """
        Enrobage minimal selon BAEL A.7.1.

        Les classes d'exposition BAEL sont plus simples que celles de l'Eurocode.
        """
        # Enrobage minimal pour adhérence
        c_min = max(diametre_barre, 10)  # mm

        # Enrobage selon l'environnement (BAEL A.7.1)
        # Conversion approximative depuis classes EC2
        enrobage_table = {
            "XC1": 20,   # Intérieur sec
            "XC2": 30,   # Intérieur humide / enterré
            "XC3": 30,   # Extérieur abrité
            "XC4": 40,   # Extérieur exposé
            "XD1": 40,   # Chlorures modéré
            "XD2": 50,   # Chlorures élevé
            "XS1": 40,   # Marin aérien
            "XS2": 50,   # Marin immergé
            # Catégories BAEL traditionnelles
            "1": 20,     # Milieu non agressif
            "2": 30,     # Milieu moyennement agressif
            "3": 40,     # Milieu fortement agressif
            "4": 50,     # Milieu très fortement agressif
        }

        c_env = enrobage_table.get(classe_exposition.upper(), 30)

        return max(c_min, c_env)
