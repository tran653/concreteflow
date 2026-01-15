"""
Calcul de l'effort tranchant selon Eurocode 2.
NF EN 1992-1-1 §6.2

Vérification de la résistance au cisaillement et dimensionnement
des armatures transversales.
"""
import math
from typing import Dict, Any


def calcul_effort_tranchant(
    portee: float,  # m
    largeur: float,  # m (largeur âme bw)
    hauteur: float,  # m
    q_elu: float,  # kN/m
    fck: float,  # MPa
    fyk: float,  # MPa
    as_longitudinal: float,  # mm² (armatures longitudinales tendues)
    enrobage: float = 0.03,  # m
    gamma_c: float = 1.5,
    gamma_s: float = 1.15
) -> Dict[str, Any]:
    """
    Calcul de l'effort tranchant pour une poutre/dalle isostatique.

    Args:
        portee: Portée (m)
        largeur: Largeur de l'âme bw (m)
        hauteur: Hauteur totale (m)
        q_elu: Charge ELU (kN/m)
        fck: Résistance caractéristique béton (MPa)
        fyk: Limite élastique acier (MPa)
        as_longitudinal: Section armatures tendues (mm²)
        enrobage: Enrobage (m)
        gamma_c: Coefficient partiel béton
        gamma_s: Coefficient partiel acier

    Returns:
        Dictionnaire avec résultats détaillés
    """
    # Conversion
    L = portee * 1000  # mm
    bw = largeur * 1000  # mm
    h = hauteur * 1000  # mm
    c = enrobage * 1000  # mm
    d = h - c - 10  # mm

    # === Effort tranchant sollicitant ===
    # Poutre isostatique: V = qL/2 (à l'appui)
    V_ed = (q_elu * portee) / 2  # kN
    V_ed_N = V_ed * 1000  # N

    # Effort tranchant réduit à d de l'appui (EC2 §6.2.1(8))
    V_ed_red = V_ed - q_elu * (d / 1000)  # kN

    # === Résistance sans armatures d'effort tranchant (EC2 §6.2.2) ===
    # VRd,c = [CRd,c * k * (100 * ρl * fck)^(1/3) + k1 * σcp] * bw * d

    # Coefficient CRd,c
    C_Rd_c = 0.18 / gamma_c

    # Facteur de taille
    k = min(1 + math.sqrt(200 / d), 2.0)

    # Taux d'armatures longitudinales
    rho_l = min(as_longitudinal / (bw * d), 0.02)

    # Contrainte de compression (σcp = 0 sans précontrainte)
    sigma_cp = 0

    # Résistance VRd,c
    V_Rd_c = C_Rd_c * k * (100 * rho_l * fck)**(1/3) * bw * d  # N

    # Valeur minimale
    v_min = 0.035 * k**1.5 * math.sqrt(fck)
    V_Rd_c_min = v_min * bw * d  # N

    V_Rd_c = max(V_Rd_c, V_Rd_c_min)  # N
    V_Rd_c_kN = V_Rd_c / 1000  # kN

    # === Vérification besoin d'armatures transversales ===
    besoin_armatures = V_ed_N > V_Rd_c

    # === Si armatures nécessaires: calcul selon EC2 §6.2.3 ===
    if besoin_armatures:
        # Résistance de calcul de l'acier
        fywd = fyk / gamma_s  # MPa

        # Angle des bielles (θ entre 21.8° et 45°)
        # On prend cot(θ) = 2.5 (θ ≈ 21.8°) pour minimiser les armatures
        cot_theta = 2.5
        theta = math.degrees(math.atan(1 / cot_theta))

        # Bras de levier interne
        z = 0.9 * d  # mm (approximation EC2)

        # === Résistance maximale des bielles (VRd,max) ===
        # VRd,max = αcw * bw * z * ν1 * fcd / (cot(θ) + tan(θ))
        alpha_cw = 1.0  # Sans précontrainte
        nu_1 = 0.6 * (1 - fck / 250)  # Facteur de réduction
        fcd = fck / gamma_c

        V_Rd_max = (alpha_cw * bw * z * nu_1 * fcd /
                   (cot_theta + 1/cot_theta))  # N
        V_Rd_max_kN = V_Rd_max / 1000  # kN

        # Vérification bielles
        bielles_ok = V_ed_N <= V_Rd_max

        if not bielles_ok:
            # Réduire cot(θ) si nécessaire
            # On itère pour trouver θ permettant de vérifier
            cot_theta = 1.0  # θ = 45°
            theta = 45
            V_Rd_max = (alpha_cw * bw * z * nu_1 * fcd /
                       (cot_theta + 1/cot_theta))
            V_Rd_max_kN = V_Rd_max / 1000
            bielles_ok = V_ed_N <= V_Rd_max

        # === Section d'armatures transversales ===
        # VRd,s = (Asw/s) * z * fywd * cot(θ)
        # => Asw/s = VEd / (z * fywd * cot(θ))

        Asw_s = V_ed_N / (z * fywd * cot_theta)  # mm²/mm

        # Conversion en cm²/m
        Asw_s_cm2_m = Asw_s * 10  # cm²/m

        # === Armatures minimales (EC2 §9.2.2) ===
        rho_w_min = 0.08 * math.sqrt(fck) / fyk
        Asw_s_min = rho_w_min * bw  # mm²/mm
        Asw_s_min_cm2_m = Asw_s_min * 10  # cm²/m

        # Section finale
        Asw_s_final = max(Asw_s, Asw_s_min)
        Asw_s_final_cm2_m = Asw_s_final * 10

        # Espacement maximal (EC2 §9.2.2)
        s_max = min(0.75 * d, 600)  # mm

        verification_ok = bielles_ok

    else:
        # Pas besoin d'armatures calculées, mais minimum constructif
        rho_w_min = 0.08 * math.sqrt(fck) / fyk
        Asw_s_min = rho_w_min * bw
        Asw_s_min_cm2_m = Asw_s_min * 10

        Asw_s_final_cm2_m = Asw_s_min_cm2_m
        V_Rd_max_kN = 0
        theta = 0
        cot_theta = 0
        s_max = min(0.75 * d, 600)
        bielles_ok = True
        verification_ok = True

    return {
        "effort_tranchant_kN": round(V_ed, 2),
        "effort_tranchant_reduit_kN": round(V_ed_red, 2),
        "resistance_sans_armatures_kN": round(V_Rd_c_kN, 2),
        "besoin_armatures_transversales": besoin_armatures,
        "resistance_max_bielles_kN": round(V_Rd_max_kN, 2) if besoin_armatures else None,
        "angle_bielles_deg": round(theta, 1) if besoin_armatures else None,
        "as_transversal_cm2_m": round(Asw_s_final_cm2_m, 2),
        "as_transversal_min_cm2_m": round(Asw_s_min_cm2_m, 2),
        "espacement_max_mm": round(s_max, 0),
        "facteur_k": round(k, 2),
        "taux_armatures_longitudinales": round(rho_l * 100, 3),
        "verification_ok": verification_ok,
        "message": "Vérification effort tranchant OK" if verification_ok else "Résistance insuffisante - augmenter section ou béton"
    }
