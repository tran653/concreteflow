"""
Eurocode 2 (EC2) - NF EN 1992-1-1
Calcul des structures en béton - Règles générales et règles pour les bâtiments.

Référence: NF EN 1992-1-1:2005 + Annexe Nationale française
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


# Table 3.1 EC2 - Propriétés des bétons
BETON_EC2: Dict[str, BetonProperties] = {
    "C20/25": BetonProperties("C20/25", 20, 28, 2.2, 1.5, 30, 3.5),
    "C25/30": BetonProperties("C25/30", 25, 33, 2.6, 1.8, 31, 3.5),
    "C30/37": BetonProperties("C30/37", 30, 38, 2.9, 2.0, 33, 3.5),
    "C35/45": BetonProperties("C35/45", 35, 43, 3.2, 2.2, 34, 3.5),
    "C40/50": BetonProperties("C40/50", 40, 48, 3.5, 2.5, 35, 3.5),
    "C45/55": BetonProperties("C45/55", 45, 53, 3.8, 2.7, 36, 3.5),
    "C50/60": BetonProperties("C50/60", 50, 58, 4.1, 2.9, 37, 3.5),
}

# Propriétés des aciers selon EC2
ACIER_EC2: Dict[str, AcierProperties] = {
    "S400": AcierProperties("S400", 400, 440, 200, 25),
    "S500": AcierProperties("S500", 500, 550, 200, 25),
    "S500B": AcierProperties("S500B", 500, 540, 200, 50),
    "S500C": AcierProperties("S500C", 500, 575, 200, 75),
}


class EurocodeNorme(NormeBase):
    """
    Implémentation de l'Eurocode 2 (EN 1992-1-1).

    Utilise les paramètres de l'Annexe Nationale française par défaut.
    """

    def __init__(self):
        super().__init__()
        # Coefficients par défaut selon AN français
        self._alpha_cc = 1.0  # Coefficient pour effet de durée de chargement

    # ==================== Identité de la norme ====================

    @property
    def code(self) -> str:
        return "EC2"

    @property
    def nom_complet(self) -> str:
        return "Eurocode 2 (EN 1992-1-1)"

    @property
    def region(self) -> str:
        return "Europe"

    # ==================== Coefficients de sécurité ====================

    @property
    def gamma_c(self) -> float:
        """Coefficient partiel béton - situations durables (§2.4.2.4)."""
        return 1.5

    @property
    def gamma_s(self) -> float:
        """Coefficient partiel acier - situations durables (§2.4.2.4)."""
        return 1.15

    @property
    def gamma_g(self) -> float:
        """Coefficient pour actions permanentes défavorables (§Table A1.2(B))."""
        return 1.35

    @property
    def gamma_q(self) -> float:
        """Coefficient pour actions variables défavorables (§Table A1.2(B))."""
        return 1.5

    # ==================== Classes de matériaux ====================

    def get_classes_beton(self) -> List[str]:
        return list(BETON_EC2.keys())

    def get_classes_acier(self) -> List[str]:
        return list(ACIER_EC2.keys())

    def set_beton(self, classe: str) -> None:
        if classe not in BETON_EC2:
            raise ValueError(
                f"Classe de béton '{classe}' non reconnue pour EC2. "
                f"Classes disponibles: {', '.join(BETON_EC2.keys())}"
            )
        self._beton = BETON_EC2[classe]

    def set_acier(self, classe: str) -> None:
        if classe not in ACIER_EC2:
            raise ValueError(
                f"Classe d'acier '{classe}' non reconnue pour EC2. "
                f"Classes disponibles: {', '.join(ACIER_EC2.keys())}"
            )
        self._acier = ACIER_EC2[classe]

    # ==================== Propriétés de calcul ====================

    @property
    def fcd(self) -> float:
        """Résistance de calcul du béton (§3.1.6)."""
        return self._alpha_cc * self.beton.fck / self.gamma_c

    @property
    def fctd(self) -> float:
        """Résistance de calcul en traction du béton."""
        alpha_ct = 1.0
        return alpha_ct * self.beton.fctk_005 / self.gamma_c

    # ==================== Calculs de flexion ====================

    def calcul_flexion(
        self,
        moment_elu: float,
        largeur: float,
        hauteur: float,
        enrobage: float = 0.03
    ) -> FlexionResult:
        """
        Calcul de flexion simple selon EC2 §6.1.

        Utilise le diagramme rectangulaire simplifié (§3.1.7).
        """
        b = largeur * 1000  # mm
        d = (hauteur - enrobage) * 1000  # mm (hauteur utile)
        Mu = moment_elu * 1e6  # N.mm

        fcd_mpa = self.fcd  # MPa
        fyd_mpa = self.fyd  # MPa

        # Moment réduit μ = Mu / (b × d² × fcd)
        mu = Mu / (b * d**2 * fcd_mpa)

        # Moment réduit limite (pivot B, bétons ≤ C50/60)
        # Pour εcu = 3.5‰ et εyd = fyd/Es ≈ 2.17‰
        mu_lim = 0.372

        if mu > mu_lim:
            return FlexionResult(
                moment_resistant=0,
                section_acier=0,
                profondeur_axe_neutre=0,
                bras_levier=0,
                mu=mu,
                mu_limite=mu_lim,
                verification_ok=False,
                message=f"Section insuffisante: μ = {mu:.3f} > μ_lim = {mu_lim:.3f}. "
                        f"Augmenter les dimensions ou ajouter des aciers comprimés."
            )

        # Profondeur relative de l'axe neutre
        alpha = 1.25 * (1 - math.sqrt(1 - 2 * mu))

        # Bras de levier
        z = d * (1 - 0.4 * alpha)

        # Section d'acier
        As = Mu / (z * fyd_mpa)  # mm²
        As_cm2 = As / 100  # cm²

        # Moment résistant
        Mr = As * z * fyd_mpa / 1e6  # kN.m

        return FlexionResult(
            moment_resistant=Mr,
            section_acier=As_cm2,
            profondeur_axe_neutre=alpha * d / 1000,  # m
            bras_levier=z / 1000,  # m
            mu=mu,
            mu_limite=mu_lim,
            verification_ok=True,
            message=f"Flexion vérifiée: μ = {mu:.3f} ≤ μ_lim = {mu_lim:.3f}"
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

        fcd_mpa = self.fcd
        fyd_mpa = self.fyd

        # Profondeur de l'axe neutre par équilibre
        # 0.8 × x × b × fcd = As × fyd
        x = As * fyd_mpa / (0.8 * b * fcd_mpa)

        # Bras de levier
        z = d - 0.4 * x

        # Moment résistant
        Mr = As * z * fyd_mpa / 1e6  # kN.m

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
        Calcul de l'effort tranchant selon EC2 §6.2.

        Vérifie VRd,c (béton seul) et calcule VRd,s si nécessaire.
        """
        Ved = effort_tranchant  # kN
        bw = largeur * 1000  # mm
        d = (hauteur - enrobage) * 1000  # mm
        Asl = section_acier_tendu * 100  # mm²

        fck = self.beton.fck  # MPa

        # Taux d'armatures longitudinales
        rho_l = min(Asl / (bw * d), 0.02)

        # Coefficient k
        k = min(1 + math.sqrt(200 / d), 2.0)

        # Valeur minimale
        v_min = 0.035 * k**(3/2) * math.sqrt(fck)

        # Résistance sans armatures transversales (§6.2.2)
        CRd_c = 0.18 / self.gamma_c
        k1 = 0.15
        sigma_cp = 0  # Sans précontrainte

        VRd_c = max(
            (CRd_c * k * (100 * rho_l * fck)**(1/3) + k1 * sigma_cp) * bw * d,
            (v_min + k1 * sigma_cp) * bw * d
        ) / 1000  # kN

        if Ved <= VRd_c:
            return CisaillementResult(
                effort_sollicitant=Ved,
                effort_resistant_beton=VRd_c,
                effort_resistant_acier=0,
                section_armatures_transversales=0,
                espacement_cadres=0,
                verification_ok=True,
                message=f"Cisaillement vérifié sans armatures: VEd = {Ved:.1f} kN ≤ VRd,c = {VRd_c:.1f} kN"
            )

        # Calcul avec armatures transversales (§6.2.3)
        # Inclinaison des bielles θ = 45° (cot θ = 1) pour simplifier
        cot_theta = 1.0
        fywd = self.fyd  # MPa

        # Section d'armatures nécessaire: Asw/s = VEd / (z × fywd × cot_theta)
        z = 0.9 * d  # mm
        Asw_s = Ved * 1000 / (z * fywd * cot_theta)  # mm²/mm

        # Convertir en cm²/m
        Asw_m = Asw_s * 1000 / 100  # cm²/m

        # Espacement pour HA8 (50.3 mm² par brin, 2 brins = 100.6 mm²)
        Asw_cadre = 100.6  # mm² pour un cadre HA8
        s = Asw_cadre / Asw_s  # mm

        # Espacement max selon EC2
        s_max = min(0.75 * d, 400)  # mm
        s = min(s, s_max)

        # Résistance avec ces armatures
        VRd_s = (Asw_cadre / s) * z * fywd * cot_theta / 1000  # kN

        # Vérification de la bielle comprimée
        alpha_cw = 1.0
        nu1 = 0.6 * (1 - fck / 250)
        VRd_max = alpha_cw * bw * z * nu1 * fck / (cot_theta + 1/cot_theta) / 1000 / self.gamma_c

        if Ved > VRd_max:
            return CisaillementResult(
                effort_sollicitant=Ved,
                effort_resistant_beton=VRd_c,
                effort_resistant_acier=VRd_s,
                section_armatures_transversales=Asw_m,
                espacement_cadres=s,
                verification_ok=False,
                message=f"Bielle comprimée insuffisante: VEd = {Ved:.1f} kN > VRd,max = {VRd_max:.1f} kN. "
                        f"Augmenter les dimensions de la section."
            )

        return CisaillementResult(
            effort_sollicitant=Ved,
            effort_resistant_beton=VRd_c,
            effort_resistant_acier=VRd_s,
            section_armatures_transversales=Asw_m,
            espacement_cadres=round(s, 0),
            verification_ok=True,
            message=f"Cisaillement vérifié avec armatures: VEd = {Ved:.1f} kN ≤ VRd,s = {VRd_s:.1f} kN. "
                    f"Cadres HA8 @ {s:.0f} mm"
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
        Calcul simplifié de la flèche selon EC2 §7.4.

        Utilise la méthode du coefficient de flèche.
        """
        L = portee * 1000  # mm
        b = largeur * 1000  # mm
        h = hauteur * 1000  # mm
        d = h - enrobage * 1000  # mm
        As = section_acier * 100  # mm²
        M_els = moment_els * 1e6  # N.mm

        Ecm = self.beton.Ecm * 1000  # MPa
        Es = self.acier.Es * 1000  # MPa
        n = Es / Ecm  # Coefficient d'équivalence

        # Inertie de la section fissurée (simplifiée)
        # Position de l'axe neutre en section fissurée
        rho = As / (b * d)
        alpha_e = n * rho
        x_fiss = d * (-alpha_e + math.sqrt(alpha_e**2 + 2 * alpha_e))

        # Inertie fissurée
        I_fiss = b * x_fiss**3 / 3 + n * As * (d - x_fiss)**2

        # Inertie brute
        I_brut = b * h**3 / 12

        # Moment de fissuration
        fctm = self.beton.fctm  # MPa
        W_inf = b * h**2 / 6
        Mcr = fctm * W_inf  # N.mm

        # Coefficient de répartition ζ
        if M_els < Mcr:
            zeta = 0  # Section non fissurée
            I_eff = I_brut
        else:
            beta = 1.0  # Chargement de courte durée
            zeta = 1 - beta * (Mcr / M_els)**2
            zeta = max(0, min(zeta, 1))
            I_eff = I_fiss / (1 - zeta * (1 - I_fiss / I_brut))

        # Flèche instantanée (poutre sur appuis simples, charge uniforme)
        # f = 5 × q × L⁴ / (384 × E × I)
        # Avec M = q × L² / 8 => q = 8 × M / L²
        q_eq = 8 * M_els / L**2
        f_inst = 5 * q_eq * L**4 / (384 * Ecm * I_eff)  # mm

        # Flèche différée (fluage + retrait) - coefficient approximatif
        phi_fluage = 2.5  # Coefficient de fluage à long terme
        f_diff = f_inst * phi_fluage * 0.5  # Approximation

        f_totale = f_inst + f_diff

        # Limite
        f_limite = self.fleche_limite(portee)

        return FlecheResult(
            fleche_instantanee=round(f_inst, 2),
            fleche_differee=round(f_diff, 2),
            fleche_totale=round(f_totale, 2),
            fleche_limite=f_limite,
            verification_ok=f_totale <= f_limite,
            message=f"Flèche totale = {f_totale:.1f} mm {'≤' if f_totale <= f_limite else '>'} "
                    f"L/250 = {f_limite:.1f} mm"
        )

    def fleche_limite(self, portee: float) -> float:
        """Flèche limite selon EC2 §7.4.1: L/250 pour l'aspect."""
        return portee * 1000 / 250  # mm

    # ==================== Enrobage ====================

    def enrobage_minimal(
        self,
        classe_exposition: str,
        diametre_barre: float = 12
    ) -> float:
        """
        Enrobage minimal selon EC2 §4.4.1.

        Args:
            classe_exposition: XC1, XC2, XC3, XC4, XD1, XD2, XS1, XS2, etc.
            diametre_barre: Diamètre des armatures (mm)

        Returns:
            Enrobage nominal (mm)
        """
        # Enrobage minimal pour adhérence
        c_min_b = diametre_barre

        # Enrobage minimal pour durabilité (Table 4.4N simplifié)
        c_min_dur_table = {
            "XC1": 15,
            "XC2": 25,
            "XC3": 25,
            "XC4": 30,
            "XD1": 35,
            "XD2": 40,
            "XD3": 45,
            "XS1": 35,
            "XS2": 40,
            "XS3": 45,
        }
        c_min_dur = c_min_dur_table.get(classe_exposition.upper(), 25)

        # Enrobage minimal
        c_min = max(c_min_b, c_min_dur, 10)

        # Marge de tolérance (AN français)
        delta_c_dev = 10  # mm

        return c_min + delta_c_dev
