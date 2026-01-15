"""
Calcul de plancher poutrelles-hourdis.
Sélection automatique de la poutrelle optimale depuis le cahier de portées.
"""
from typing import Dict, Any, List, Optional


def calcul_plancher_poutrelles_hourdis(
    parametres: Dict[str, Any],
    lignes_cahier: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calcul de sélection de poutrelle optimale.

    Args:
        parametres: Paramètres du calcul
            - geometrie.portee: float (m)
            - geometrie.entraxe_souhaite: int (cm, optionnel)
            - geometrie.hauteur_hourdis: int (cm, optionnel)
            - charges.permanentes: float (kN/m²)
            - charges.exploitation: float (kN/m²)
            - conditions.optimisation: str ('economique', 'minimal_hauteur', 'maximal_reserve')
        lignes_cahier: Données du cahier de portées (liste de dict)

    Returns:
        Résultats du calcul avec poutrelle sélectionnée
    """
    # Extraction paramètres
    geometrie = parametres.get('geometrie', {})
    charges = parametres.get('charges', {})
    conditions = parametres.get('conditions', {})

    portee = geometrie.get('portee', 5.0)
    entraxe_souhaite = geometrie.get('entraxe_souhaite')
    hauteur_hourdis = geometrie.get('hauteur_hourdis')

    g = charges.get('permanentes', 3.0)  # kN/m²
    q = charges.get('exploitation', 2.5)  # kN/m²

    optimisation = conditions.get('optimisation', 'economique')

    # Validation portée
    if portee <= 0 or portee > 12:
        return {
            'verification_ok': False,
            'message': f"Portée invalide: {portee}m (doit être entre 0 et 12m)",
        }

    # Conversion charges en kg/m² (format cahier)
    # 1 kN/m² = 100 kg/m² (approximation: 1 kN = 100 daN = 100 kg)
    charge_totale_kg = int((g + q) * 100)

    # Arrondi à la charge supérieure standard
    charges_standard = [250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750]
    charge_calcul = next((c for c in charges_standard if c >= charge_totale_kg), 750)

    # Vérification qu'il y a des données dans le cahier
    if not lignes_cahier:
        return {
            'verification_ok': False,
            'message': "Cahier de portées vide ou non fourni",
        }

    # Filtrage des poutrelles candidates
    candidates = []

    for ligne in lignes_cahier:
        # Filtres optionnels
        if entraxe_souhaite and ligne.get('entraxe_cm') != entraxe_souhaite:
            continue
        if hauteur_hourdis and ligne.get('hauteur_hourdis_cm') != hauteur_hourdis:
            continue

        # Recherche portée limite pour la charge
        portees = ligne.get('portees_limites', {})
        portee_limite = portees.get(str(charge_calcul))

        if portee_limite is None:
            # Interpolation si charge exacte non disponible
            portee_limite = _interpoler_portee(portees, charge_calcul)

        if portee_limite and portee_limite >= portee:
            candidates.append({
                'ligne': ligne,
                'portee_limite': portee_limite,
                'ratio': portee / portee_limite,
                'reserve': portee_limite - portee,
                'hauteur_totale': _calculer_hauteur_totale(ligne)
            })

    if not candidates:
        return {
            'verification_ok': False,
            'message': (
                f"Aucune poutrelle ne convient pour portée={portee}m "
                f"avec charge={charge_calcul}kg/m²"
            ),
            'charges': {
                'permanentes_kN_m2': g,
                'exploitation_kN_m2': q,
                'totale_kg_m2': charge_totale_kg,
                'calcul_kg_m2': charge_calcul
            },
            'portee_demandee_m': portee,
            'filtres': {
                'entraxe_souhaite': entraxe_souhaite,
                'hauteur_hourdis': hauteur_hourdis
            }
        }

    # Tri selon critère d'optimisation
    if optimisation == 'economique':
        # Maximiser le ratio (utiliser au mieux la poutrelle)
        candidates.sort(key=lambda x: (-x['ratio'], x['hauteur_totale']))
    elif optimisation == 'minimal_hauteur':
        # Minimiser la hauteur totale
        candidates.sort(key=lambda x: (x['hauteur_totale'], -x['ratio']))
    elif optimisation == 'maximal_reserve':
        # Maximiser la réserve de portée
        candidates.sort(key=lambda x: (-x['reserve'], x['hauteur_totale']))

    # Sélection meilleure candidate
    best = candidates[0]
    ligne = best['ligne']

    # Préparation alternatives (3 suivantes max)
    alternatives = []
    for cand in candidates[1:4]:
        alt_ligne = cand['ligne']
        alternatives.append({
            'reference': alt_ligne['reference_poutrelle'],
            'hauteur_hourdis_cm': alt_ligne['hauteur_hourdis_cm'],
            'entraxe_cm': alt_ligne['entraxe_cm'],
            'portee_limite_m': round(cand['portee_limite'], 2),
            'ratio_utilisation_pct': round(cand['ratio'] * 100, 1),
            'hauteur_totale_cm': round(cand['hauteur_totale'], 1)
        })

    return {
        'verification_ok': True,
        'message': f"Poutrelle {ligne['reference_poutrelle']} sélectionnée",

        # Poutrelle sélectionnée
        'poutrelle': {
            'reference': ligne['reference_poutrelle'],
            'hauteur_hourdis_cm': ligne['hauteur_hourdis_cm'],
            'entraxe_cm': ligne['entraxe_cm'],
            'epaisseur_table_cm': ligne.get('epaisseur_table_cm', 5.0),
            'hauteur_totale_cm': round(best['hauteur_totale'], 1),
        },

        # Vérification
        'verification': {
            'portee_demandee_m': portee,
            'portee_limite_m': round(best['portee_limite'], 2),
            'charge_utilisee_kg_m2': charge_calcul,
            'ratio_utilisation_pct': round(best['ratio'] * 100, 1),
            'reserve_portee_m': round(best['reserve'], 2),
        },

        # Charges
        'charges': {
            'permanentes_kN_m2': g,
            'exploitation_kN_m2': q,
            'totale_kg_m2': charge_totale_kg,
            'calcul_kg_m2': charge_calcul
        },

        # Alternatives
        'alternatives': alternatives,
        'nombre_candidates': len(candidates),

        # Résumé pour affichage
        'summary': {
            'verification_globale': 'OK',
            'message': (
                f"Plancher {ligne['reference_poutrelle']} + hourdis {ligne['hauteur_hourdis_cm']}cm "
                f"(entraxe {ligne['entraxe_cm']}cm) - Utilisation {best['ratio']*100:.0f}%"
            )
        }
    }


def _interpoler_portee(portees: Dict[str, float], charge: int) -> Optional[float]:
    """Interpole la portée limite pour une charge intermédiaire."""
    if not portees:
        return None

    charges_dispo = sorted([int(c) for c in portees.keys()])

    if not charges_dispo:
        return None

    # Bornes
    if charge <= charges_dispo[0]:
        return portees.get(str(charges_dispo[0]))
    if charge >= charges_dispo[-1]:
        return portees.get(str(charges_dispo[-1]))

    # Interpolation linéaire
    for i in range(len(charges_dispo) - 1):
        c1, c2 = charges_dispo[i], charges_dispo[i + 1]
        if c1 <= charge <= c2:
            p1 = portees.get(str(c1), 0)
            p2 = portees.get(str(c2), 0)
            if p1 and p2:
                # Interpolation linéaire
                ratio = (charge - c1) / (c2 - c1)
                return p1 + ratio * (p2 - p1)

    return None


def _calculer_hauteur_totale(ligne: Dict[str, Any]) -> float:
    """Calcule la hauteur totale du plancher."""
    # Hauteur typique poutrelle selon hauteur hourdis
    # (la poutrelle dépasse généralement du hourdis de quelques cm)
    hauteurs_poutrelles = {
        12: 11,
        16: 13,
        20: 15,
        25: 18
    }

    h_hourdis = ligne.get('hauteur_hourdis_cm', 16)
    h_poutrelle = hauteurs_poutrelles.get(h_hourdis, 13)
    h_table = ligne.get('epaisseur_table_cm', 5.0)

    # Hauteur totale = max(poutrelle, hourdis) + table de compression
    return max(h_poutrelle, h_hourdis) + h_table
