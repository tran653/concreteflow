"""
Calcul de flèche selon Eurocode 2.
NF EN 1992-1-1 §7.4

Méthode simplifiée basée sur le rapport portée/hauteur utile
et méthode détaillée avec calcul d'inertie fissurée.
"""
import math
from typing import Dict, Any


def calcul_fleche(
    portee: float,  # m
    largeur: float,  # m
    hauteur: float,  # m
    q_els: float,  # kN/m (charge ELS quasi-permanente)
    fck: float,  # MPa
    as_tension: float,  # mm² (section d'acier tendu)
    enrobage: float = 0.03,  # m
    coefficient_fluage: float = 2.0  # φ(∞,t0)
) -> Dict[str, Any]:
    """
    Calcul de flèche pour une poutre/dalle isostatique.

    Args:
        portee: Portée de la travée (m)
        largeur: Largeur de la section (m)
        hauteur: Hauteur totale (m)
        q_els: Charge quasi-permanente ELS (kN/m)
        fck: Résistance caractéristique béton (MPa)
        as_tension: Section d'acier tendu (mm²)
        enrobage: Enrobage (m)
        coefficient_fluage: Coefficient de fluage

    Returns:
        Dictionnaire avec résultats détaillés
    """
    # Conversion
    L = portee * 1000  # mm
    b = largeur * 1000  # mm
    h = hauteur * 1000  # mm
    c = enrobage * 1000  # mm
    d = h - c - 10  # mm

    # Module d'élasticité
    Ecm = 22000 * (fck / 10)**0.3  # MPa (EC2 Table 3.1)
    Es = 200000  # MPa

    # Coefficient d'équivalence
    n = Es / Ecm

    # Coefficient d'équivalence effectif (fluage)
    n_eff = n * (1 + coefficient_fluage)

    # === Méthode 1: Vérification simplifiée EC2 §7.4.2 ===
    # Rapport L/d limite
    rho = as_tension / (b * d)  # taux d'armatures
    rho_0 = math.sqrt(fck) / 1000  # taux de référence

    # Facteurs K selon type de système
    K = 1.0  # Poutre isostatique

    if rho <= rho_0:
        # Section faiblement armée
        L_d_limite = K * (11 + 1.5 * math.sqrt(fck) * rho_0 / rho +
                         3.2 * math.sqrt(fck) * (rho_0 / rho - 1)**1.5)
    else:
        # Section fortement armée
        L_d_limite = K * (11 + 1.5 * math.sqrt(fck) * rho_0 / (rho - rho_0))

    L_d_reel = L / d
    verification_simplifiee = L_d_reel <= L_d_limite

    # === Méthode 2: Calcul détaillé de la flèche ===

    # Moment ELS
    M_els = (q_els * portee**2) / 8  # kN.m
    M_els_Nmm = M_els * 1e6  # N.mm

    # Résistance en traction du béton
    fctm = 0.3 * fck**(2/3) if fck <= 50 else 2.12 * math.log(1 + fck/10)

    # Moment de fissuration
    W_el = b * h**2 / 6  # mm³
    M_cr = fctm * W_el  # N.mm

    # === Inertie section non fissurée ===
    I_I = b * h**3 / 12  # mm⁴

    # === Inertie section fissurée ===
    # Position axe neutre (section fissurée)
    # b*x²/2 = n*As*(d-x)
    # Résolution équation du 2nd degré
    a_eq = b / 2
    b_eq = n_eff * as_tension
    c_eq = -n_eff * as_tension * d

    delta = b_eq**2 - 4 * a_eq * c_eq
    x = (-b_eq + math.sqrt(delta)) / (2 * a_eq)  # mm

    # Inertie fissurée
    I_II = b * x**3 / 3 + n_eff * as_tension * (d - x)**2  # mm⁴

    # === Coefficient de distribution (EC2 §7.4.3) ===
    # ζ = 1 - β * (M_cr / M)²
    beta = 1.0  # Chargement de longue durée

    if M_els_Nmm <= M_cr:
        # Section non fissurée
        zeta = 0
        I_eff = I_I
    else:
        zeta = 1 - beta * (M_cr / M_els_Nmm)**2
        zeta = max(0, min(1, zeta))
        # Inertie effective
        I_eff = I_II / (zeta + (1 - zeta) * I_II / I_I)

    # === Calcul flèche ===
    # Flèche instantanée: f = 5*q*L⁴ / (384*E*I)
    q_Nmm = q_els / 1000  # N/mm

    # Module effectif (fluage)
    E_eff = Ecm / (1 + coefficient_fluage)

    # Flèche totale (instantanée + différée)
    f_total = 5 * q_Nmm * L**4 / (384 * E_eff * I_eff)  # mm

    # Flèche instantanée seule
    f_inst = 5 * q_Nmm * L**4 / (384 * Ecm * I_eff)  # mm

    # === Limites EC2 §7.4.1 ===
    f_limite_aspect = L / 250  # Aspect général
    f_limite_dommages = L / 500  # Dommages aux cloisons

    # Vérification
    verification_aspect = f_total <= f_limite_aspect
    verification_dommages = f_inst <= f_limite_dommages
    verification_ok = verification_aspect  # On prend le critère principal

    return {
        "moment_els_kNm": round(M_els, 2),
        "moment_fissuration_kNm": round(M_cr / 1e6, 2),
        "section_fissuree": M_els_Nmm > M_cr,
        "coefficient_distribution": round(zeta, 3),
        "inertie_non_fissuree_mm4": round(I_I, 0),
        "inertie_fissuree_mm4": round(I_II, 0),
        "inertie_effective_mm4": round(I_eff, 0),
        "position_axe_neutre_mm": round(x, 1),
        "fleche_instantanee_mm": round(f_inst, 2),
        "fleche_totale_mm": round(f_total, 2),
        "fleche_limite_mm": round(f_limite_aspect, 2),
        "rapport_L_d_reel": round(L_d_reel, 1),
        "rapport_L_d_limite": round(L_d_limite, 1),
        "verification_simplifiee_ok": verification_simplifiee,
        "verification_ok": verification_ok,
        "message": "Vérification flèche OK" if verification_ok else f"Flèche excessive: {f_total:.1f}mm > {f_limite_aspect:.1f}mm"
    }
