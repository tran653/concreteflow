"""
Optimisation et sélection du ferraillage.
Choix des barres et disposition des armatures.
"""
import math
from typing import Dict, Any, List, Tuple

from app.models.calcul import TypeProduit


# Sections d'acier standard (mm²)
SECTIONS_BARRES = {
    6: 28.3,
    8: 50.3,
    10: 78.5,
    12: 113.1,
    14: 153.9,
    16: 201.1,
    20: 314.2,
    25: 490.9,
    32: 804.2,
}

# Sections de fils lisses (mm²)
SECTIONS_FILS = {
    4: 12.6,
    5: 19.6,
    6: 28.3,
    7: 38.5,
    8: 50.3,
}

# Torons de précontrainte
TORONS = {
    "T13": {"section": 100, "fpk": 1860, "fp01k": 1600},
    "T15.2": {"section": 140, "fpk": 1860, "fp01k": 1600},
    "T15.7": {"section": 150, "fpk": 1860, "fp01k": 1600},
}


def choisir_barres(
    as_requis_cm2: float,
    largeur_mm: float,
    diametre_min: int = 8,
    diametre_max: int = 25,
    espacement_min: float = 50  # mm entre barres
) -> Dict[str, Any]:
    """
    Sélectionne la combinaison optimale de barres pour atteindre la section requise.

    Args:
        as_requis_cm2: Section d'acier requise (cm²)
        largeur_mm: Largeur disponible (mm)
        diametre_min: Diamètre minimum (mm)
        diametre_max: Diamètre maximum (mm)
        espacement_min: Espacement minimum entre barres (mm)

    Returns:
        Dictionnaire avec choix de barres
    """
    as_requis_mm2 = as_requis_cm2 * 100

    # Essayer différentes combinaisons
    meilleures_options = []

    for diam in sorted(SECTIONS_BARRES.keys()):
        if diam < diametre_min or diam > diametre_max:
            continue

        section_barre = SECTIONS_BARRES[diam]
        nombre = math.ceil(as_requis_mm2 / section_barre)

        # Vérifier si ça rentre dans la largeur
        largeur_necessaire = nombre * diam + (nombre - 1) * espacement_min + 2 * 30  # enrobage
        if largeur_necessaire > largeur_mm:
            continue

        section_totale = nombre * section_barre
        surplus = (section_totale - as_requis_mm2) / as_requis_mm2 * 100

        meilleures_options.append({
            "diametre": diam,
            "nombre": nombre,
            "designation": f"{nombre}HA{diam}",
            "section_mm2": round(section_totale, 1),
            "section_cm2": round(section_totale / 100, 2),
            "surplus_pct": round(surplus, 1)
        })

    if not meilleures_options:
        # Fallback: prendre le plus gros diamètre avec le nombre nécessaire
        diam = diametre_max
        section_barre = SECTIONS_BARRES.get(diam, SECTIONS_BARRES[25])
        nombre = math.ceil(as_requis_mm2 / section_barre)

        return {
            "diametre": diam,
            "nombre": nombre,
            "designation": f"{nombre}HA{diam}",
            "section_mm2": round(nombre * section_barre, 1),
            "section_cm2": round(nombre * section_barre / 100, 2),
            "surplus_pct": round((nombre * section_barre - as_requis_mm2) / as_requis_mm2 * 100, 1),
            "warning": "Disposition serrée - vérifier l'espacement"
        }

    # Choisir l'option avec le moins de surplus (optimale)
    meilleure = min(meilleures_options, key=lambda x: x["surplus_pct"])
    return meilleure


def choisir_cadres(
    as_transversal_cm2_m: float,
    largeur_mm: float,
    hauteur_mm: float,
    diametre_cadre: int = 8
) -> Dict[str, Any]:
    """
    Sélectionne l'espacement des cadres.

    Args:
        as_transversal_cm2_m: Section d'armatures transversales requise (cm²/m)
        largeur_mm: Largeur de la section (mm)
        hauteur_mm: Hauteur de la section (mm)
        diametre_cadre: Diamètre du cadre (mm)

    Returns:
        Dictionnaire avec disposition des cadres
    """
    as_requis_mm2_m = as_transversal_cm2_m * 100  # mm²/m

    # Section d'un cadre (2 brins)
    section_cadre = 2 * SECTIONS_BARRES.get(diametre_cadre, 50.3)

    # Espacement
    espacement = section_cadre / as_requis_mm2_m * 1000  # mm

    # Arrondir à un espacement standard (multiples de 50)
    espacements_standards = [100, 150, 200, 250, 300]
    espacement_choisi = max([s for s in espacements_standards if s <= espacement], default=100)

    # Section réelle
    section_reelle = section_cadre / espacement_choisi * 1000  # mm²/m

    return {
        "diametre_cadre": diametre_cadre,
        "espacement_mm": espacement_choisi,
        "designation": f"HA{diametre_cadre}@{espacement_choisi}",
        "section_mm2_m": round(section_reelle, 1),
        "section_cm2_m": round(section_reelle / 100, 2)
    }


def calcul_ferraillage(
    as_flexion: float,  # cm²
    as_tranchant: float,  # cm²/m
    largeur: float,  # mm
    hauteur: float,  # mm
    type_produit: TypeProduit
) -> Dict[str, Any]:
    """
    Calcul complet du ferraillage.

    Args:
        as_flexion: Section armatures de flexion (cm²)
        as_tranchant: Section armatures transversales (cm²/m)
        largeur: Largeur section (mm)
        hauteur: Hauteur section (mm)
        type_produit: Type de produit

    Returns:
        Dictionnaire avec tout le ferraillage
    """
    result = {
        "type_produit": type_produit.value,
        "armatures_inferieures": {},
        "armatures_superieures": {},
        "armatures_transversales": {},
        "resume": ""
    }

    # === Armatures inférieures (flexion) ===
    if as_flexion > 0:
        result["armatures_inferieures"] = choisir_barres(
            as_requis_cm2=as_flexion,
            largeur_mm=largeur,
            diametre_min=10 if type_produit == TypeProduit.POUTRE else 8
        )

    # === Armatures supérieures (constructif ou compression) ===
    # Minimum constructif: 20% des armatures inférieures
    as_sup_min = max(0.2 * as_flexion, 1.0)  # cm²
    result["armatures_superieures"] = choisir_barres(
        as_requis_cm2=as_sup_min,
        largeur_mm=largeur,
        diametre_min=8,
        diametre_max=16
    )

    # === Armatures transversales ===
    if as_tranchant > 0:
        result["armatures_transversales"] = choisir_cadres(
            as_transversal_cm2_m=as_tranchant,
            largeur_mm=largeur,
            hauteur_mm=hauteur
        )

    # === Résumé ===
    inf = result["armatures_inferieures"].get("designation", "")
    sup = result["armatures_superieures"].get("designation", "")
    trans = result["armatures_transversales"].get("designation", "")

    result["resume"] = f"Inf: {inf} | Sup: {sup} | Cadres: {trans}"

    # === Poids estimé ===
    # Densité acier: 7850 kg/m³
    volume_acier = 0
    if "section_mm2" in result["armatures_inferieures"]:
        # Estimation longueur = portée + 2*ancrage
        volume_acier += result["armatures_inferieures"]["section_mm2"]

    result["poids_acier_estime_kg_m"] = round(volume_acier * 7850 / 1e9, 2)

    return result
