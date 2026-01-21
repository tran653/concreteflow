"""
ACI 318 - Building Code Requirements for Structural Concrete
American Concrete Institute (USA)

Référence: ACI 318-19 (2019)

Note: Les unités internes sont en SI (MPa, mm, kN) mais les classes
de béton utilisent la notation américaine (f'c en psi converti en MPa).
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


# Classes de béton ACI (f'c en MPa, équivalent psi entre parenthèses)
# f'c = résistance caractéristique cylindrique à 28 jours
BETON_ACI: Dict[str, BetonProperties] = {
    "C20": BetonProperties("C20 (3000 psi)", 20, 26, 2.2, 1.5, 21.5, 3.0),
    "C25": BetonProperties("C25 (3500 psi)", 25, 32, 2.5, 1.7, 23.5, 3.0),
    "C28": BetonProperties("C28 (4000 psi)", 28, 35, 2.7, 1.9, 25.0, 3.0),
    "C30": BetonProperties("C30 (4500 psi)", 30, 37, 2.9, 2.0, 26.0, 3.0),
    "C35": BetonProperties("C35 (5000 psi)", 35, 42, 3.1, 2.2, 28.0, 3.0),
    "C40": BetonProperties("C40 (6000 psi)", 40, 47, 3.4, 2.4, 30.0, 3.0),
    "C45": BetonProperties("C45 (6500 psi)", 45, 52, 3.6, 2.5, 32.0, 3.0),
}

# Classes d'acier ACI (Grade en ksi)
ACIER_ACI: Dict[str, AcierProperties] = {
    "Grade40": AcierProperties("Grade 40 (40 ksi)", 276, 414, 200, 12),
    "Grade60": AcierProperties("Grade 60 (60 ksi)", 414, 620, 200, 12),
    "Grade75": AcierProperties("Grade 75 (75 ksi)", 517, 690, 200, 10),
    "Grade80": AcierProperties("Grade 80 (80 ksi)", 552, 689, 200, 10),
}


class ACI318Norme(NormeBase):
    """
    Implémentation de la norme ACI 318.

    Principales différences avec l'Eurocode:
    - Facteurs de charge différents (1.2D + 1.6L vs 1.35G + 1.5Q)
    - Facteurs phi (φ) au lieu de coefficients partiels γ
    - Approche "Strength Design Method"
    - Whitney stress block pour le béton
    """

    def __init__(self):
        super().__init__()
        # Facteur phi pour flexion (ACI 318-19 Table 21.2.1)
        self._phi_flexion = 0.90
        self._phi_cisaillement = 0.75
        # Beta1 pour Whitney stress block
        self._beta1 = 0.85  # Pour f'c ≤ 28 MPa

    # ==================== Identité de la norme ====================

    @property
    def code(self) -> str:
        return "ACI318"

    @property
    def nom_complet(self) -> str:
        return "ACI 318-19 (American Concrete Institute)"

    @property
    def region(self) -> str:
        return "États-Unis"

    # ==================== Coefficients de sécurité ====================
    # Note: ACI utilise des facteurs φ sur la résistance, pas sur les matériaux

    @property
    def gamma_c(self) -> float:
        """ACI n'utilise pas gamma_c, retourne 1.0 pour compatibilité."""
        return 1.0

    @property
    def gamma_s(self) -> float:
        """ACI n'utilise pas gamma_s, retourne 1.0 pour compatibilité."""
        return 1.0

    @property
    def gamma_g(self) -> float:
        """Facteur de charge pour permanentes (Dead load D) - ACI §5.3.1."""
        return 1.2

    @property
    def gamma_q(self) -> float:
        """Facteur de charge pour variables (Live load L) - ACI §5.3.1."""
        return 1.6

    @property
    def phi_flexion(self) -> float:
        """Facteur de réduction pour flexion (tension-controlled)."""
        return self._phi_flexion

    @property
    def phi_cisaillement(self) -> float:
        """Facteur de réduction pour cisaillement."""
        return self._phi_cisaillement

    # ==================== Classes de matériaux ====================

    def get_classes_beton(self) -> List[str]:
        return list(BETON_ACI.keys())

    def get_classes_acier(self) -> List[str]:
        return list(ACIER_ACI.keys())

    def set_beton(self, classe: str) -> None:
        if classe not in BETON_ACI:
            raise ValueError(
                f"Classe de béton '{classe}' non reconnue pour ACI 318. "
                f"Classes disponibles: {', '.join(BETON_ACI.keys())}"
            )
        self._beton = BETON_ACI[classe]
        # Mettre à jour beta1 selon f'c
        fc = self._beton.fck
        if fc <= 28:
            self._beta1 = 0.85
        elif fc >= 55:
            self._beta1 = 0.65
        else:
            self._beta1 = 0.85 - 0.05 * (fc - 28) / 7

    def set_acier(self, classe: str) -> None:
        if classe not in ACIER_ACI:
            raise ValueError(
                f"Classe d'acier '{classe}' non reconnue pour ACI 318. "
                f"Classes disponibles: {', '.join(ACIER_ACI.keys())}"
            )
        self._acier = ACIER_ACI[classe]

    # ==================== Propriétés de calcul ====================

    @property
    def fcd(self) -> float:
        """f'c directement (pas de réduction sur le matériau en ACI)."""
        return self.beton.fck

    @property
    def fyd(self) -> float:
        """fy directement (pas de réduction sur le matériau en ACI)."""
        return self.acier.fy

    # ==================== Calculs de flexion ====================

    def calcul_flexion(
        self,
        moment_elu: float,
        largeur: float,
        hauteur: float,
        enrobage: float = 0.04  # 1.5 pouces typique
    ) -> FlexionResult:
        """
        Calcul de flexion selon ACI 318 §22.2.

        Utilise le Whitney rectangular stress block.
        Mu ≤ φMn où φ = 0.90 pour sections tension-controlled.
        """
        b = largeur * 1000  # mm
        d = (hauteur - enrobage) * 1000  # mm
        Mu = moment_elu * 1e6  # N.mm

        fc = self.beton.fck  # MPa (f'c)
        fy = self.acier.fy  # MPa

        # Moment réduit nominal requis
        Mn_requis = Mu / self.phi_flexion  # N.mm

        # Coefficient Rn = Mn / (b × d²)
        Rn = Mn_requis / (b * d**2)

        # Taux d'armature ρ
        # ρ = (0.85 × f'c / fy) × [1 - √(1 - 2Rn/(0.85×f'c))]
        term = 2 * Rn / (0.85 * fc)
        if term > 1:
            return FlexionResult(
                moment_resistant=0,
                section_acier=0,
                profondeur_axe_neutre=0,
                bras_levier=0,
                mu=term,
                mu_limite=1.0,
                verification_ok=False,
                message=f"Section insuffisante. Augmenter les dimensions."
            )

        rho = (0.85 * fc / fy) * (1 - math.sqrt(1 - term))

        # Vérifier ρ_min et ρ_max
        # ρ_min = max(3√f'c/fy, 200/fy) - ACI §9.6.1.2
        rho_min = max(3 * math.sqrt(fc) / fy, 200 / fy) / 1000  # Conversion

        # ρ_max pour section tension-controlled (εt ≥ 0.005)
        epsilon_t_min = 0.005
        epsilon_cu = 0.003  # Déformation ultime béton ACI
        rho_max = 0.85 * self._beta1 * (fc / fy) * (epsilon_cu / (epsilon_cu + epsilon_t_min))

        if rho < rho_min:
            rho = rho_min
        elif rho > rho_max:
            return FlexionResult(
                moment_resistant=0,
                section_acier=rho * b * d / 100,  # cm²
                profondeur_axe_neutre=0,
                bras_levier=0,
                mu=rho / rho_max,
                mu_limite=1.0,
                verification_ok=False,
                message=f"Section compression-controlled (ρ = {rho:.4f} > ρ_max = {rho_max:.4f}). "
                        f"Augmenter les dimensions ou utiliser des aciers comprimés."
            )

        # Section d'acier
        As = rho * b * d  # mm²
        As_cm2 = As / 100  # cm²

        # Profondeur du bloc de compression
        a = As * fy / (0.85 * fc * b)  # mm
        c = a / self._beta1  # Profondeur axe neutre

        # Bras de levier
        z = d - a / 2

        # Moment nominal résistant
        Mn = As * fy * z  # N.mm
        Mu_resist = self.phi_flexion * Mn / 1e6  # kN.m

        # Vérifier εt (déformation de l'acier tendu)
        epsilon_t = epsilon_cu * (d - c) / c

        return FlexionResult(
            moment_resistant=Mu_resist,
            section_acier=As_cm2,
            profondeur_axe_neutre=c / 1000,  # m
            bras_levier=z / 1000,  # m
            mu=rho / rho_max,
            mu_limite=1.0,
            verification_ok=True,
            message=f"Flexion vérifiée (ACI 318): φMn = {Mu_resist:.1f} kN.m ≥ Mu = {moment_elu:.1f} kN.m. "
                    f"εt = {epsilon_t:.4f} (tension-controlled si ≥ 0.005)"
        )

    def calcul_moment_resistant(
        self,
        section_acier: float,
        largeur: float,
        hauteur: float,
        enrobage: float = 0.04
    ) -> float:
        """Calcule le moment résistant φMn pour une section d'acier donnée."""
        As = section_acier * 100  # cm² -> mm²
        b = largeur * 1000  # mm
        d = (hauteur - enrobage) * 1000  # mm

        fc = self.beton.fck
        fy = self.acier.fy

        # Profondeur du bloc de compression
        a = As * fy / (0.85 * fc * b)

        # Bras de levier
        z = d - a / 2

        # Moment nominal
        Mn = As * fy * z  # N.mm

        return self.phi_flexion * Mn / 1e6  # kN.m

    # ==================== Calculs de cisaillement ====================

    def calcul_cisaillement(
        self,
        effort_tranchant: float,
        largeur: float,
        hauteur: float,
        enrobage: float = 0.04,
        section_acier_tendu: float = 0
    ) -> CisaillementResult:
        """
        Calcul du cisaillement selon ACI 318 §22.5.

        Vu ≤ φVn où φ = 0.75 et Vn = Vc + Vs
        """
        Vu = effort_tranchant  # kN
        bw = largeur * 1000  # mm
        d = (hauteur - enrobage) * 1000  # mm

        fc = self.beton.fck  # MPa
        fy = min(self.acier.fy, 420)  # ACI limite fy à 420 MPa pour cisaillement

        # Résistance du béton Vc (§22.5.5.1)
        # Vc = 0.17 × λ × √f'c × bw × d (simplifié)
        lambda_concrete = 1.0  # Béton normal
        Vc = 0.17 * lambda_concrete * math.sqrt(fc) * bw * d / 1000  # kN

        phi_Vc = self.phi_cisaillement * Vc

        if Vu <= phi_Vc:
            return CisaillementResult(
                effort_sollicitant=Vu,
                effort_resistant_beton=phi_Vc,
                effort_resistant_acier=0,
                section_armatures_transversales=0,
                espacement_cadres=0,
                verification_ok=True,
                message=f"Cisaillement vérifié par le béton: Vu = {Vu:.1f} kN ≤ φVc = {phi_Vc:.1f} kN"
            )

        # Armatures nécessaires
        # Vs = (Vu/φ) - Vc
        Vs_requis = Vu / self.phi_cisaillement - Vc  # kN

        # Vérifier Vs max = 0.66 × √f'c × bw × d
        Vs_max = 0.66 * math.sqrt(fc) * bw * d / 1000  # kN

        if Vs_requis > Vs_max:
            return CisaillementResult(
                effort_sollicitant=Vu,
                effort_resistant_beton=phi_Vc,
                effort_resistant_acier=0,
                section_armatures_transversales=0,
                espacement_cadres=0,
                verification_ok=False,
                message=f"Section insuffisante pour le cisaillement: Vs requis = {Vs_requis:.1f} kN > "
                        f"Vs,max = {Vs_max:.1f} kN. Augmenter les dimensions."
            )

        # Av/s = Vs / (fy × d)
        Av_s = Vs_requis * 1000 / (fy * d)  # mm²/mm

        # Convertir en cm²/m
        Av_m = Av_s * 1000 / 100  # cm²/m

        # Espacement pour cadres HA8 (2 brins = 100.6 mm²)
        Av_cadre = 100.6  # mm²
        s = Av_cadre / Av_s  # mm

        # Espacement max (§9.7.6.2.2)
        if Vs_requis <= Vs_max / 2:
            s_max = min(d / 2, 600)
        else:
            s_max = min(d / 4, 300)
        s = min(s, s_max)

        # Résistance avec ces armatures
        Vs = (Av_cadre / s) * fy * d / 1000  # kN
        phi_Vn = self.phi_cisaillement * (Vc + Vs)

        return CisaillementResult(
            effort_sollicitant=Vu,
            effort_resistant_beton=phi_Vc,
            effort_resistant_acier=self.phi_cisaillement * Vs,
            section_armatures_transversales=Av_m,
            espacement_cadres=round(s, 0),
            verification_ok=True,
            message=f"Cisaillement vérifié avec armatures: Vu = {Vu:.1f} kN ≤ φVn = {phi_Vn:.1f} kN. "
                    f"Cadres @ {s:.0f} mm"
        )

    # ==================== Calculs de flèche ====================

    def calcul_fleche(
        self,
        portee: float,
        moment_els: float,
        largeur: float,
        hauteur: float,
        section_acier: float,
        enrobage: float = 0.04
    ) -> FlecheResult:
        """
        Calcul de flèche selon ACI 318 §24.2.

        Utilise le moment d'inertie effectif Ie.
        """
        L = portee * 1000  # mm
        b = largeur * 1000  # mm
        h = hauteur * 1000  # mm
        d = h - enrobage * 1000  # mm
        As = section_acier * 100  # mm²
        Ma = moment_els * 1e6  # N.mm (moment de service)

        fc = self.beton.fck
        # Module Ec selon ACI: Ec = 4700√f'c (MPa)
        Ec = 4700 * math.sqrt(fc)  # MPa
        Es = self.acier.Es * 1000  # MPa
        n = Es / Ec

        # Inertie brute
        Ig = b * h**3 / 12  # mm⁴

        # Moment de fissuration
        # fr = 0.62λ√f'c (ACI §19.2.3.1)
        fr = 0.62 * 1.0 * math.sqrt(fc)  # MPa
        yt = h / 2
        Mcr = fr * Ig / yt  # N.mm

        if Ma <= 0:
            return FlecheResult(
                fleche_instantanee=0,
                fleche_differee=0,
                fleche_totale=0,
                fleche_limite=self.fleche_limite(portee),
                verification_ok=True,
                message="Pas de moment appliqué"
            )

        # Inertie de la section fissurée
        rho = As / (b * d)
        k = math.sqrt(2 * rho * n + (rho * n)**2) - rho * n
        Icr = b * (k * d)**3 / 3 + n * As * (d - k * d)**2  # mm⁴

        # Moment d'inertie effectif (ACI §24.2.3.5)
        if Ma < Mcr:
            Ie = Ig
        else:
            Ie = Icr / (1 - (1 - Icr/Ig) * (Mcr/Ma)**3)
            Ie = min(Ie, Ig)

        # Flèche instantanée (poutre simple, charge uniforme)
        q_eq = 8 * Ma / L**2
        f_inst = 5 * q_eq * L**4 / (384 * Ec * Ie)  # mm

        # Flèche différée (ACI §24.2.4)
        # λΔ = ξ / (1 + 50ρ')
        xi = 2.0  # Pour 5 ans ou plus
        rho_prime = 0  # Pas d'armatures comprimées
        lambda_delta = xi / (1 + 50 * rho_prime)
        f_diff = f_inst * lambda_delta

        f_totale = f_inst + f_diff
        f_limite = self.fleche_limite(portee)

        return FlecheResult(
            fleche_instantanee=round(f_inst, 2),
            fleche_differee=round(f_diff, 2),
            fleche_totale=round(f_totale, 2),
            fleche_limite=f_limite,
            verification_ok=f_totale <= f_limite,
            message=f"Flèche totale = {f_totale:.1f} mm {'≤' if f_totale <= f_limite else '>'} "
                    f"L/240 = {f_limite:.1f} mm (ACI)"
        )

    def fleche_limite(self, portee: float) -> float:
        """Flèche limite selon ACI 318 Table 24.2.2: L/240 pour planchers."""
        return portee * 1000 / 240  # mm

    # ==================== Enrobage ====================

    def enrobage_minimal(
        self,
        classe_exposition: str,
        diametre_barre: float = 16
    ) -> float:
        """
        Enrobage minimal selon ACI 318 §20.5.1.

        Note: ACI utilise des catégories d'exposition différentes.
        """
        # ACI utilise des "exposure categories" différentes
        # Simplifié ici avec correspondance approximative
        enrobage_table = {
            "XC1": 38,   # Intérieur sec
            "XC2": 38,   # Intérieur humide
            "XC3": 50,   # Extérieur
            "XC4": 50,   # Alternance
            "XD1": 50,   # Chlorures modéré
            "XD2": 63,   # Chlorures élevé
            "XS1": 50,   # Marin aérien
            "XS2": 63,   # Marin immergé
            # Catégories ACI natives
            "F0": 38,    # Non exposé gel
            "F1": 38,    # Gel modéré
            "F2": 50,    # Gel sévère
            "F3": 50,    # Gel très sévère
            "S0": 38,    # Pas de sulfates
            "S1": 38,    # Sulfates modérés
            "S2": 50,    # Sulfates sévères
            "S3": 63,    # Sulfates très sévères
            "C0": 38,    # Pas de corrosion
            "C1": 38,    # Corrosion carbonatation
            "C2": 50,    # Corrosion chlorures
        }

        return enrobage_table.get(classe_exposition.upper(), 50)  # 2 pouces par défaut
