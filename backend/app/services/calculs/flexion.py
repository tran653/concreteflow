"""
Calcul de flexion simple selon Eurocode 2.
NF EN 1992-1-1 §6.1

Hypothèses:
- Sections rectangulaires
- Béton fissuré en traction
- Diagramme rectangulaire simplifié pour le béton
"""
import math
from typing import Dict, Any


def calcul_flexion(
    portee: float,  # m
    largeur: float,  # m
    hauteur: float,  # m
    q_elu: float,  # kN/m (charge linéique ELU)
    q_els: float,  # kN/m (charge linéique ELS)
    fck: float,  # MPa
    fyk: float,  # MPa
    gamma_c: float = 1.5,
    gamma_s: float = 1.15,
    enrobage: float = 0.03  # m
) -> Dict[str, Any]:
    """
    Calcul de flexion pour une poutre/dalle isostatique.

    Args:
        portee: Portée de la travée (m)
        largeur: Largeur de la section (m)
        hauteur: Hauteur totale de la section (m)
        q_elu: Charge linéique à l'ELU (kN/m)
        q_els: Charge linéique à l'ELS (kN/m)
        fck: Résistance caractéristique béton (MPa)
        fyk: Limite élastique acier (MPa)
        gamma_c: Coefficient partiel béton
        gamma_s: Coefficient partiel acier
        enrobage: Enrobage des armatures (m)

    Returns:
        Dictionnaire avec résultats détaillés
    """
    # Conversion en mm pour les calculs
    L = portee * 1000  # mm
    b = largeur * 1000  # mm
    h = hauteur * 1000  # mm
    c = enrobage * 1000  # mm

    # Hauteur utile (approximation initiale)
    d = h - c - 10  # mm (10mm = demi-diamètre estimé)

    # Résistances de calcul
    fcd = fck / gamma_c  # MPa
    fyd = fyk / gamma_s  # MPa

    # === Moment fléchissant ELU ===
    # Poutre isostatique: M = qL²/8
    M_elu = (q_elu * portee**2) / 8  # kN.m
    M_elu_Nmm = M_elu * 1e6  # N.mm

    # === Moment fléchissant ELS ===
    M_els = (q_els * portee**2) / 8  # kN.m

    # === Moment réduit μ ===
    mu = M_elu_Nmm / (b * d**2 * fcd)

    # Moment réduit limite (pivot B, aciers S500)
    # Pour epsilon_s = fyd/Es et epsilon_cu = 3.5‰
    epsilon_yd = fyd / 200000  # déformation élastique acier
    epsilon_cu = 0.0035  # déformation ultime béton

    alpha_lim = epsilon_cu / (epsilon_cu + epsilon_yd)
    mu_lim = 0.8 * alpha_lim * (1 - 0.4 * alpha_lim)

    # Vérification section suffisante
    section_suffisante = mu <= mu_lim

    if not section_suffisante:
        return {
            "moment_elu_kNm": round(M_elu, 2),
            "moment_els_kNm": round(M_els, 2),
            "mu": round(mu, 4),
            "mu_limite": round(mu_lim, 4),
            "verification_ok": False,
            "message": f"Section insuffisante: μ={mu:.4f} > μ_lim={mu_lim:.4f}. Augmenter la hauteur."
        }

    # === Calcul section d'acier ===
    # Profondeur relative axe neutre
    alpha = 1.25 * (1 - math.sqrt(1 - 2 * mu))

    # Bras de levier
    z = d * (1 - 0.4 * alpha)  # mm

    # Section d'acier requise
    As_requis = M_elu_Nmm / (z * fyd)  # mm²
    As_requis_cm2 = As_requis / 100  # cm²

    # === Section minimale (EC2 §9.2.1.1) ===
    # As,min = max(0.26 * fctm/fyk * bt * d, 0.0013 * bt * d)
    fctm = 0.3 * fck**(2/3) if fck <= 50 else 2.12 * math.log(1 + fck/10)
    As_min_1 = 0.26 * (fctm / fyk) * b * d
    As_min_2 = 0.0013 * b * d
    As_min = max(As_min_1, As_min_2)  # mm²
    As_min_cm2 = As_min / 100  # cm²

    # === Section maximale (EC2 §9.2.1.1) ===
    As_max = 0.04 * b * h  # mm²
    As_max_cm2 = As_max / 100  # cm²

    # Section finale
    As_final = max(As_requis, As_min)  # mm²
    As_final_cm2 = As_final / 100  # cm²

    # Vérification
    verification_ok = As_final <= As_max

    # === Taux de travail ===
    taux_travail = (mu / mu_lim) * 100  # %

    return {
        "moment_elu_kNm": round(M_elu, 2),
        "moment_els_kNm": round(M_els, 2),
        "hauteur_utile_mm": round(d, 1),
        "mu": round(mu, 4),
        "mu_limite": round(mu_lim, 4),
        "alpha": round(alpha, 4),
        "bras_levier_mm": round(z, 1),
        "as_requis_cm2": round(As_requis_cm2, 2),
        "as_min_cm2": round(As_min_cm2, 2),
        "as_max_cm2": round(As_max_cm2, 2),
        "as_final_cm2": round(As_final_cm2, 2),
        "taux_travail_pct": round(taux_travail, 1),
        "verification_ok": verification_ok,
        "message": "Vérification flexion OK" if verification_ok else "Section d'acier excessive"
    }
