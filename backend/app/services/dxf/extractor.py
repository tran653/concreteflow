"""
Extraction de données géométriques pour les calculs de plancher.
"""
from typing import Dict, Any, List, Tuple, Optional
import math


def extract_plan_geometry(dxf_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrait les données géométriques pertinentes pour le calcul de plancher.

    Args:
        dxf_result: Résultat du parsing DXF

    Returns:
        Dictionnaire avec géométrie simplifiée pour les calculs
    """
    bounds = dxf_result.get("bounds", {})
    contours = dxf_result.get("contours", [])
    openings = dxf_result.get("openings", [])
    entities = dxf_result.get("entities", [])

    # Calculer la surface totale du plancher
    total_area = calculate_contour_area(contours)

    # Calculer la surface des ouvertures
    opening_area = calculate_openings_area(openings)

    # Surface nette
    net_area = total_area - opening_area

    # Identifier les travées potentielles
    spans = identify_spans(contours, bounds)

    # Identifier les points d'appui (murs, poteaux)
    supports = identify_supports(entities)

    return {
        "bounds": bounds,
        "total_area_m2": round(total_area / 1e6, 2),  # mm² -> m²
        "opening_area_m2": round(opening_area / 1e6, 2),
        "net_area_m2": round(net_area / 1e6, 2),
        "contour_count": len(contours),
        "opening_count": len(openings),
        "spans": spans,
        "supports": supports,
        "main_dimensions": {
            "length_m": round(bounds.get("width", 0) / 1000, 2),
            "width_m": round(bounds.get("height", 0) / 1000, 2)
        }
    }


def calculate_contour_area(contours: List[Dict]) -> float:
    """Calcule la surface totale des contours (formule de Shoelace)."""
    total_area = 0

    for contour in contours:
        if contour.get("type") == "polyline":
            points = contour.get("points", [])
            if len(points) >= 3:
                area = polygon_area(points)
                total_area += abs(area)

    return total_area


def polygon_area(points: List[Dict]) -> float:
    """Calcule l'aire d'un polygone avec la formule de Shoelace."""
    n = len(points)
    if n < 3:
        return 0

    area = 0
    for i in range(n):
        j = (i + 1) % n
        x_i = points[i].get("x", 0)
        y_i = points[i].get("y", 0)
        x_j = points[j].get("x", 0)
        y_j = points[j].get("y", 0)
        area += x_i * y_j
        area -= x_j * y_i

    return abs(area) / 2


def calculate_openings_area(openings: List[Dict]) -> float:
    """Calcule la surface totale des ouvertures."""
    total_area = 0

    for opening in openings:
        if opening.get("type") == "polyline":
            points = opening.get("points", [])
            area = polygon_area(points)
            total_area += abs(area)

        elif opening.get("type") == "circle":
            radius = opening.get("radius", 0)
            total_area += math.pi * radius ** 2

    return total_area


def identify_spans(contours: List[Dict], bounds: Dict) -> List[Dict]:
    """
    Identifie les travées potentielles du plancher.
    Retourne une liste de travées avec leurs dimensions.
    """
    spans = []

    # Analyse simplifiée basée sur les dimensions globales
    width = bounds.get("width", 0)
    height = bounds.get("height", 0)

    # Déterminer la direction principale (poutrelles parallèles au côté court)
    if width > height:
        main_span = height / 1000  # m
        direction = "X"
    else:
        main_span = width / 1000  # m
        direction = "Y"

    # Créer une travée par défaut
    spans.append({
        "id": 1,
        "direction": direction,
        "length_m": round(main_span, 2),
        "width_m": round(max(width, height) / 1000, 2),
        "type": "isostatique"  # Hypothèse par défaut
    })

    return spans


def identify_supports(entities: List[Dict]) -> List[Dict]:
    """
    Identifie les éléments porteurs (murs, poteaux) dans le dessin.
    """
    supports = []

    # Rechercher les lignes épaisses ou sur certains layers
    support_layers = ["MUR", "WALL", "POTEAU", "COLUMN", "SUPPORT", "STRUCTURE"]

    for entity in entities:
        layer = entity.get("layer", "").upper()
        is_support_layer = any(sl in layer for sl in support_layers)

        if is_support_layer:
            if entity.get("type") == "line":
                start = entity.get("start", {})
                end = entity.get("end", {})
                length = math.sqrt(
                    (end.get("x", 0) - start.get("x", 0)) ** 2 +
                    (end.get("y", 0) - start.get("y", 0)) ** 2
                )
                supports.append({
                    "type": "wall",
                    "start": start,
                    "end": end,
                    "length_mm": round(length, 0)
                })

            elif entity.get("type") == "circle":
                center = entity.get("center", {})
                radius = entity.get("radius", 0)
                supports.append({
                    "type": "column",
                    "center": center,
                    "diameter_mm": round(radius * 2, 0)
                })

    return supports


def generate_element_layout(
    contours: List[Dict],
    openings: List[Dict],
    element_width: float = 600,  # mm
    element_type: str = "poutrelle"
) -> List[Dict]:
    """
    Génère un calepinage automatique des éléments.

    Args:
        contours: Contours du plancher
        openings: Ouvertures/trémies
        element_width: Largeur des éléments (mm)
        element_type: Type d'élément (poutrelle, predalle, etc.)

    Returns:
        Liste des éléments avec position et dimensions
    """
    elements = []

    if not contours:
        return elements

    # Prendre le premier contour comme référence
    main_contour = contours[0]
    points = main_contour.get("points", [])

    if len(points) < 3:
        return elements

    # Calculer la bounding box du contour
    xs = [p.get("x", 0) for p in points]
    ys = [p.get("y", 0) for p in points]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    width = max_x - min_x
    height = max_y - min_y

    # Déterminer l'orientation (éléments parallèles au côté court)
    if width > height:
        # Éléments dans la direction Y
        num_elements = int(width / element_width)
        for i in range(num_elements):
            x_pos = min_x + (i + 0.5) * element_width
            elements.append({
                "id": i + 1,
                "reference": f"{element_type[0].upper()}{i+1:03d}",
                "type": element_type,
                "position": {
                    "x": round(x_pos, 0),
                    "y": round(min_y + height / 2, 0),
                    "rotation": 90
                },
                "dimensions": {
                    "length_mm": round(height, 0),
                    "width_mm": element_width
                }
            })
    else:
        # Éléments dans la direction X
        num_elements = int(height / element_width)
        for i in range(num_elements):
            y_pos = min_y + (i + 0.5) * element_width
            elements.append({
                "id": i + 1,
                "reference": f"{element_type[0].upper()}{i+1:03d}",
                "type": element_type,
                "position": {
                    "x": round(min_x + width / 2, 0),
                    "y": round(y_pos, 0),
                    "rotation": 0
                },
                "dimensions": {
                    "length_mm": round(width, 0),
                    "width_mm": element_width
                }
            })

    return elements
