"""
Moteur de calcul principal pour ConcreteFlow.
Dispatch les calculs vers les modules spécifiques selon le type de produit.
"""
from typing import Dict, Any, List, Optional

from app.models.calcul import TypeProduit
from app.services.calculs.eurocode import EurocodeCalculator
from app.services.calculs.flexion import calcul_flexion
from app.services.calculs.fleche import calcul_fleche
from app.services.calculs.effort_tranchant import calcul_effort_tranchant
from app.services.calculs.ferraillage import calcul_ferraillage
from app.services.calculs.plancher_poutrelles_hourdis import calcul_plancher_poutrelles_hourdis


def run_calculation(
    type_produit: TypeProduit,
    parametres: Dict[str, Any],
    norme: str = "EC2",
    cahier_portees_data: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Execute structural calculation based on product type and parameters.

    Args:
        type_produit: Type of precast element
        parametres: Input parameters (geometry, loads, materials, conditions)
        norme: Design code (EC2, BPEL, DTU)
        cahier_portees_data: Data from portees limit table (for PLANCHER_POUTRELLES_HOURDIS)

    Returns:
        Dictionary with all calculation results
    """
    # Special case: Plancher poutrelles-hourdis uses cahier de portées
    if type_produit == TypeProduit.PLANCHER_POUTRELLES_HOURDIS:
        if not cahier_portees_data:
            raise ValueError("Cahier de portées requis pour le calcul plancher poutrelles-hourdis")
        return calcul_plancher_poutrelles_hourdis(parametres, cahier_portees_data)

    # Initialize calculator with normative parameters
    calculator = EurocodeCalculator(norme=norme)

    # Extract parameters
    geometrie = parametres.get("geometrie", {})
    charges = parametres.get("charges", {})
    materiaux = parametres.get("materiaux", {})
    conditions = parametres.get("conditions", {})

    # Material properties
    calculator.set_materials(
        classe_beton=materiaux.get("classe_beton", "C30/37"),
        classe_acier=materiaux.get("classe_acier", "S500")
    )

    # Geometry
    portee = geometrie.get("portee", 5.0)  # m
    largeur = geometrie.get("largeur", 1.0)  # m (for slabs) or 0.2m for beams
    hauteur = geometrie.get("hauteur", 0.2)  # m

    # Loads (kN/m² or kN/m)
    g = charges.get("permanentes", 5.0)  # Permanent loads
    q = charges.get("exploitation", 2.5)  # Variable loads

    # Compute load combinations (EC0)
    # ELU: 1.35*G + 1.5*Q
    # ELS: G + Q
    q_elu = 1.35 * g + 1.5 * q
    q_els = g + q

    # Results container
    resultats = {
        "input_summary": {
            "type_produit": type_produit.value,
            "portee_m": portee,
            "largeur_m": largeur,
            "hauteur_m": hauteur,
            "charge_permanente_kN_m2": g,
            "charge_exploitation_kN_m2": q,
            "charge_elu_kN_m": q_elu * largeur,
            "charge_els_kN_m": q_els * largeur
        }
    }

    # 1. Flexion calculation
    flexion_result = calcul_flexion(
        portee=portee,
        largeur=largeur,
        hauteur=hauteur,
        q_elu=q_elu * largeur,  # kN/m
        q_els=q_els * largeur,
        fck=calculator.fck,
        fyk=calculator.fyk,
        gamma_c=calculator.gamma_c,
        gamma_s=calculator.gamma_s
    )
    resultats["flexion"] = flexion_result

    # 2. Shear calculation
    tranchant_result = calcul_effort_tranchant(
        portee=portee,
        largeur=largeur,
        hauteur=hauteur,
        q_elu=q_elu * largeur,
        fck=calculator.fck,
        fyk=calculator.fyk,
        as_longitudinal=flexion_result.get("as_requis_cm2", 0) * 100  # mm²
    )
    resultats["effort_tranchant"] = tranchant_result

    # 3. Deflection calculation
    fleche_result = calcul_fleche(
        portee=portee,
        largeur=largeur,
        hauteur=hauteur,
        q_els=q_els * largeur,
        fck=calculator.fck,
        as_tension=flexion_result.get("as_requis_cm2", 0) * 100  # mm²
    )
    resultats["fleche"] = fleche_result

    # 4. Reinforcement optimization
    ferraillage_result = calcul_ferraillage(
        as_flexion=flexion_result.get("as_requis_cm2", 0),
        as_tranchant=tranchant_result.get("as_transversal_cm2_m", 0),
        largeur=largeur * 1000,  # mm
        hauteur=hauteur * 1000,
        type_produit=type_produit
    )
    resultats["ferraillage"] = ferraillage_result

    # 5. Global verification summary
    all_ok = (
        flexion_result.get("verification_ok", False) and
        tranchant_result.get("verification_ok", False) and
        fleche_result.get("verification_ok", False)
    )

    resultats["summary"] = {
        "verification_globale": "OK" if all_ok else "NON CONFORME",
        "flexion_ok": flexion_result.get("verification_ok", False),
        "tranchant_ok": tranchant_result.get("verification_ok", False),
        "fleche_ok": fleche_result.get("verification_ok", False),
        "message": "Toutes les vérifications sont satisfaites." if all_ok else "Certaines vérifications ne sont pas satisfaites. Voir détails."
    }

    return resultats
