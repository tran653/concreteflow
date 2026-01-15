"""
Service d'import et parsing de fichiers DXF.
Utilise ezdxf pour extraire la géométrie des plans.
"""
import ezdxf
from ezdxf.entities import Line, LWPolyline, Polyline, Circle, Arc, Text, MText
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import math


@dataclass
class Point2D:
    x: float
    y: float

    def to_dict(self) -> Dict[str, float]:
        return {"x": round(self.x, 2), "y": round(self.y, 2)}


@dataclass
class LineGeometry:
    start: Point2D
    end: Point2D
    layer: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "line",
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
            "layer": self.layer
        }


@dataclass
class PolylineGeometry:
    points: List[Point2D]
    closed: bool
    layer: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "polyline",
            "points": [p.to_dict() for p in self.points],
            "closed": self.closed,
            "layer": self.layer
        }


@dataclass
class CircleGeometry:
    center: Point2D
    radius: float
    layer: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "circle",
            "center": self.center.to_dict(),
            "radius": round(self.radius, 2),
            "layer": self.layer
        }


@dataclass
class ArcGeometry:
    center: Point2D
    radius: float
    start_angle: float
    end_angle: float
    layer: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "arc",
            "center": self.center.to_dict(),
            "radius": round(self.radius, 2),
            "start_angle": round(self.start_angle, 2),
            "end_angle": round(self.end_angle, 2),
            "layer": self.layer
        }


@dataclass
class TextGeometry:
    position: Point2D
    text: str
    height: float
    rotation: float
    layer: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "text",
            "position": self.position.to_dict(),
            "text": self.text,
            "height": round(self.height, 2),
            "rotation": round(self.rotation, 2),
            "layer": self.layer
        }


@dataclass
class DXFParseResult:
    """Résultat du parsing d'un fichier DXF."""
    success: bool
    filename: str
    units: str = "mm"
    scale: float = 1.0
    bounds: Dict[str, float] = field(default_factory=dict)
    layers: List[str] = field(default_factory=list)
    entities: List[Dict[str, Any]] = field(default_factory=list)
    contours: List[Dict[str, Any]] = field(default_factory=list)
    openings: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "filename": self.filename,
            "units": self.units,
            "scale": self.scale,
            "bounds": self.bounds,
            "layers": self.layers,
            "entity_count": len(self.entities),
            "contour_count": len(self.contours),
            "opening_count": len(self.openings),
            "error": self.error
        }


class DXFParser:
    """Parser de fichiers DXF pour extraction de géométrie."""

    # Layers typiques pour les contours de plancher
    CONTOUR_LAYERS = ["CONTOUR", "PLANCHER", "FLOOR", "OUTLINE", "PERIMETRE", "0"]

    # Layers typiques pour les ouvertures/trémies
    OPENING_LAYERS = ["TREMIE", "OUVERTURE", "OPENING", "RESERVATION", "VOID"]

    def __init__(self):
        self.doc = None
        self.msp = None

    def parse_file(self, file_path: str) -> DXFParseResult:
        """Parse un fichier DXF et extrait la géométrie."""
        try:
            path = Path(file_path)
            if not path.exists():
                return DXFParseResult(
                    success=False,
                    filename=path.name,
                    error=f"Fichier non trouvé: {file_path}"
                )

            # Charger le fichier DXF
            self.doc = ezdxf.readfile(file_path)
            self.msp = self.doc.modelspace()

            # Extraire les métadonnées
            units = self._get_units()
            layers = self._get_layers()

            # Extraire toutes les entités
            entities = self._extract_entities()

            # Calculer les limites
            bounds = self._calculate_bounds(entities)

            # Identifier les contours et ouvertures
            contours = self._identify_contours(entities)
            openings = self._identify_openings(entities)

            return DXFParseResult(
                success=True,
                filename=path.name,
                units=units,
                scale=1.0,
                bounds=bounds,
                layers=layers,
                entities=entities,
                contours=contours,
                openings=openings
            )

        except Exception as e:
            return DXFParseResult(
                success=False,
                filename=Path(file_path).name if file_path else "unknown",
                error=str(e)
            )

    def parse_bytes(self, content: bytes, filename: str) -> DXFParseResult:
        """Parse un contenu DXF depuis des bytes."""
        try:
            from io import BytesIO
            stream = BytesIO(content)

            self.doc = ezdxf.read(stream)
            self.msp = self.doc.modelspace()

            units = self._get_units()
            layers = self._get_layers()
            entities = self._extract_entities()
            bounds = self._calculate_bounds(entities)
            contours = self._identify_contours(entities)
            openings = self._identify_openings(entities)

            return DXFParseResult(
                success=True,
                filename=filename,
                units=units,
                scale=1.0,
                bounds=bounds,
                layers=layers,
                entities=entities,
                contours=contours,
                openings=openings
            )

        except Exception as e:
            return DXFParseResult(
                success=False,
                filename=filename,
                error=str(e)
            )

    def _get_units(self) -> str:
        """Récupère l'unité du dessin."""
        try:
            units = self.doc.header.get("$INSUNITS", 0)
            units_map = {
                0: "unitless",
                1: "inches",
                2: "feet",
                4: "mm",
                5: "cm",
                6: "m",
            }
            return units_map.get(units, "mm")
        except:
            return "mm"

    def _get_layers(self) -> List[str]:
        """Récupère la liste des calques."""
        try:
            return [layer.dxf.name for layer in self.doc.layers]
        except:
            return []

    def _extract_entities(self) -> List[Dict[str, Any]]:
        """Extrait toutes les entités géométriques."""
        entities = []

        for entity in self.msp:
            geom = self._parse_entity(entity)
            if geom:
                entities.append(geom.to_dict() if hasattr(geom, 'to_dict') else geom)

        return entities

    def _parse_entity(self, entity) -> Optional[Any]:
        """Parse une entité DXF individuelle."""
        try:
            layer = entity.dxf.layer if hasattr(entity.dxf, 'layer') else "0"

            if isinstance(entity, Line):
                return LineGeometry(
                    start=Point2D(entity.dxf.start.x, entity.dxf.start.y),
                    end=Point2D(entity.dxf.end.x, entity.dxf.end.y),
                    layer=layer
                )

            elif isinstance(entity, LWPolyline):
                points = [Point2D(p[0], p[1]) for p in entity.get_points()]
                return PolylineGeometry(
                    points=points,
                    closed=entity.closed,
                    layer=layer
                )

            elif isinstance(entity, Circle):
                return CircleGeometry(
                    center=Point2D(entity.dxf.center.x, entity.dxf.center.y),
                    radius=entity.dxf.radius,
                    layer=layer
                )

            elif isinstance(entity, Arc):
                return ArcGeometry(
                    center=Point2D(entity.dxf.center.x, entity.dxf.center.y),
                    radius=entity.dxf.radius,
                    start_angle=entity.dxf.start_angle,
                    end_angle=entity.dxf.end_angle,
                    layer=layer
                )

            elif isinstance(entity, (Text, MText)):
                text = entity.dxf.text if isinstance(entity, Text) else entity.text
                pos = entity.dxf.insert if hasattr(entity.dxf, 'insert') else (0, 0, 0)
                height = entity.dxf.height if hasattr(entity.dxf, 'height') else 2.5
                rotation = entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0

                return TextGeometry(
                    position=Point2D(pos[0], pos[1]),
                    text=text,
                    height=height,
                    rotation=rotation,
                    layer=layer
                )

        except Exception:
            pass

        return None

    def _calculate_bounds(self, entities: List[Dict]) -> Dict[str, float]:
        """Calcule les limites du dessin."""
        if not entities:
            return {"min_x": 0, "min_y": 0, "max_x": 1000, "max_y": 1000}

        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')

        for entity in entities:
            etype = entity.get("type")

            if etype == "line":
                for point_key in ["start", "end"]:
                    p = entity.get(point_key, {})
                    min_x = min(min_x, p.get("x", 0))
                    min_y = min(min_y, p.get("y", 0))
                    max_x = max(max_x, p.get("x", 0))
                    max_y = max(max_y, p.get("y", 0))

            elif etype == "polyline":
                for p in entity.get("points", []):
                    min_x = min(min_x, p.get("x", 0))
                    min_y = min(min_y, p.get("y", 0))
                    max_x = max(max_x, p.get("x", 0))
                    max_y = max(max_y, p.get("y", 0))

            elif etype == "circle":
                c = entity.get("center", {})
                r = entity.get("radius", 0)
                min_x = min(min_x, c.get("x", 0) - r)
                min_y = min(min_y, c.get("y", 0) - r)
                max_x = max(max_x, c.get("x", 0) + r)
                max_y = max(max_y, c.get("y", 0) + r)

        if min_x == float('inf'):
            return {"min_x": 0, "min_y": 0, "max_x": 1000, "max_y": 1000}

        return {
            "min_x": round(min_x, 2),
            "min_y": round(min_y, 2),
            "max_x": round(max_x, 2),
            "max_y": round(max_y, 2),
            "width": round(max_x - min_x, 2),
            "height": round(max_y - min_y, 2)
        }

    def _identify_contours(self, entities: List[Dict]) -> List[Dict]:
        """Identifie les contours de plancher."""
        contours = []

        for entity in entities:
            layer = entity.get("layer", "").upper()

            # Vérifier si c'est un layer de contour
            is_contour_layer = any(cl in layer for cl in self.CONTOUR_LAYERS)

            # Les polylignes fermées sur les layers de contour sont des contours
            if entity.get("type") == "polyline" and entity.get("closed") and is_contour_layer:
                contours.append(entity)

        return contours

    def _identify_openings(self, entities: List[Dict]) -> List[Dict]:
        """Identifie les ouvertures/trémies."""
        openings = []

        for entity in entities:
            layer = entity.get("layer", "").upper()

            # Vérifier si c'est un layer d'ouverture
            is_opening_layer = any(ol in layer for ol in self.OPENING_LAYERS)

            if is_opening_layer:
                if entity.get("type") in ["polyline", "circle"]:
                    openings.append(entity)

        return openings
