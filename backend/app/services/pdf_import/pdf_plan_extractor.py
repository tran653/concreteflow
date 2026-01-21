"""
Service d'extraction de données depuis les plans PDF de béton armé.

Extrait automatiquement:
- Portées des travées
- Types de poutrelles
- Épaisseur de dalle de compression
- Charges (permanentes, exploitation)
- Entre-axes des poutrelles
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


class ConfidenceLevel(str, Enum):
    """Niveau de confiance de l'extraction."""
    HIGH = "high"      # > 90% - Extraction directe du texte
    MEDIUM = "medium"  # 60-90% - Pattern matching
    LOW = "low"        # < 60% - OCR ou estimation


@dataclass
class ExtractedValue:
    """Valeur extraite avec son niveau de confiance."""
    value: Any
    confidence: ConfidenceLevel
    source: str  # "text", "table", "ocr", "pattern"
    raw_text: Optional[str] = None


@dataclass
class ExtractedPlanData:
    """Données extraites d'un plan PDF de béton armé."""
    # Identifiant du fichier
    filename: str
    num_pages: int

    # Données de portées (en mètres)
    portees: List[ExtractedValue] = field(default_factory=list)

    # Types de poutrelles détectés
    poutrelles: List[ExtractedValue] = field(default_factory=list)

    # Épaisseur dalle de compression (cm)
    epaisseur_dalle: Optional[ExtractedValue] = None

    # Charges (kN/m²)
    charge_permanente: Optional[ExtractedValue] = None
    charge_exploitation: Optional[ExtractedValue] = None

    # Entre-axes (cm)
    entraxes: List[ExtractedValue] = field(default_factory=list)

    # Hauteur hourdis (cm)
    hauteur_hourdis: Optional[ExtractedValue] = None

    # Texte brut extrait (pour debug)
    raw_text: str = ""

    # Tableaux détectés
    tables: List[Dict] = field(default_factory=list)

    # Avertissements
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convertit en dictionnaire pour l'API."""
        def value_to_dict(v: Optional[ExtractedValue]) -> Optional[Dict]:
            if v is None:
                return None
            return {
                "value": v.value,
                "confidence": v.confidence.value,
                "source": v.source,
            }

        return {
            "filename": self.filename,
            "num_pages": self.num_pages,
            "portees": [value_to_dict(p) for p in self.portees],
            "poutrelles": [value_to_dict(p) for p in self.poutrelles],
            "epaisseur_dalle": value_to_dict(self.epaisseur_dalle),
            "charge_permanente": value_to_dict(self.charge_permanente),
            "charge_exploitation": value_to_dict(self.charge_exploitation),
            "entraxes": [value_to_dict(e) for e in self.entraxes],
            "hauteur_hourdis": value_to_dict(self.hauteur_hourdis),
            "tables": self.tables,
            "warnings": self.warnings,
            "has_data": self._has_meaningful_data(),
        }

    def _has_meaningful_data(self) -> bool:
        """Vérifie si des données significatives ont été extraites."""
        return bool(
            self.portees or
            self.poutrelles or
            self.epaisseur_dalle or
            self.charge_permanente or
            self.entraxes
        )

    def to_calcul_parametres(self) -> Dict:
        """Convertit en paramètres de calcul pour pré-remplir le formulaire."""
        params = {
            "geometrie": {},
            "charges": {},
            "materiaux": {},
            "conditions": {},
        }

        # Portée (prendre la première ou la plus grande)
        if self.portees:
            portees_values = [p.value for p in self.portees if isinstance(p.value, (int, float))]
            if portees_values:
                params["geometrie"]["portee"] = max(portees_values)

        # Épaisseur dalle
        if self.epaisseur_dalle and self.epaisseur_dalle.value:
            # Convertir cm en m pour la hauteur si nécessaire
            params["geometrie"]["epaisseur_dalle_cm"] = self.epaisseur_dalle.value

        # Hauteur hourdis
        if self.hauteur_hourdis and self.hauteur_hourdis.value:
            params["geometrie"]["hauteur_hourdis"] = self.hauteur_hourdis.value

        # Entre-axe
        if self.entraxes:
            entraxes_values = [e.value for e in self.entraxes if isinstance(e.value, (int, float))]
            if entraxes_values:
                params["geometrie"]["entraxe_souhaite"] = entraxes_values[0]

        # Charges
        if self.charge_permanente and self.charge_permanente.value:
            params["charges"]["permanentes"] = self.charge_permanente.value

        if self.charge_exploitation and self.charge_exploitation.value:
            params["charges"]["exploitation"] = self.charge_exploitation.value

        return params


class PdfPlanExtractor:
    """
    Extracteur de données depuis les plans PDF de béton armé.

    Supporte:
    - Extraction de texte directe (pdfplumber)
    - Extraction de tableaux
    - OCR pour les plans scannés (pytesseract)
    """

    # Patterns pour détecter les portées (en mètres)
    PORTEE_PATTERNS = [
        r"port[ée]e[s]?\s*[=:]\s*(\d+[.,]?\d*)\s*m",
        r"(\d+[.,]?\d*)\s*m\s*(?:de\s+)?port[ée]e",
        r"L\s*[=:]\s*(\d+[.,]?\d*)\s*m",
        r"travée[s]?\s*[=:]\s*(\d+[.,]?\d*)\s*m",
        r"(\d+[.,]\d+)\s*m",  # Capture générique de mesures en mètres
    ]

    # Patterns pour les poutrelles
    POUTRELLE_PATTERNS = [
        r"poutrelle[s]?\s*[=:]\s*([A-Z0-9\-\.]+)",
        r"type\s*[=:]\s*([A-Z0-9\-\.]+)",
        r"réf[érence]*\s*[=:]\s*([A-Z0-9\-\.]+)",
        r"(\d{2,3}[+\-]?\d*)",  # Références numériques comme "112", "113+1"
    ]

    # Patterns pour les charges
    CHARGE_PATTERNS = {
        "permanente": [
            r"G\s*[=:]\s*(\d+[.,]?\d*)\s*(?:kN/m[²2]?|kg/m[²2]?)",
            r"charge[s]?\s+permanente[s]?\s*[=:]\s*(\d+[.,]?\d*)",
            r"poids\s+propre\s*[=:]\s*(\d+[.,]?\d*)",
        ],
        "exploitation": [
            r"Q\s*[=:]\s*(\d+[.,]?\d*)\s*(?:kN/m[²2]?|kg/m[²2]?)",
            r"charge[s]?\s+(?:d')?exploitation\s*[=:]\s*(\d+[.,]?\d*)",
            r"surcharge[s]?\s*[=:]\s*(\d+[.,]?\d*)",
        ],
    }

    # Patterns pour entre-axes
    ENTRAXE_PATTERNS = [
        r"entre[- ]?axe[s]?\s*[=:]\s*(\d+)\s*(?:cm|mm)?",
        r"e[- ]?a\s*[=:]\s*(\d+)\s*(?:cm)?",
        r"espacement\s*[=:]\s*(\d+)\s*(?:cm)?",
    ]

    # Patterns pour épaisseur dalle
    DALLE_PATTERNS = [
        r"dalle\s+(?:de\s+)?compression\s*[=:]\s*(\d+)\s*(?:cm)?",
        r"table\s+(?:de\s+)?compression\s*[=:]\s*(\d+)\s*(?:cm)?",
        r"épaisseur\s+dalle\s*[=:]\s*(\d+)\s*(?:cm)?",
        r"(\d+)\s*\+\s*(\d+)",  # Format "16+4" pour hourdis+dalle
    ]

    # Patterns pour hauteur hourdis
    HOURDIS_PATTERNS = [
        r"hourdis\s*[=:]\s*(\d+)\s*(?:cm)?",
        r"hauteur\s+hourdis\s*[=:]\s*(\d+)",
        r"h\s*[=:]\s*(\d+)\s*(?:cm)?",
    ]

    def __init__(self, use_ocr: bool = True):
        """
        Initialise l'extracteur.

        Args:
            use_ocr: Utiliser l'OCR pour les PDF scannés
        """
        self.use_ocr = use_ocr and OCR_AVAILABLE

        if not PDF_AVAILABLE:
            raise ImportError(
                "pdfplumber n'est pas installé. "
                "Installez-le avec: pip install pdfplumber"
            )

    def extract(self, pdf_path: str) -> ExtractedPlanData:
        """
        Extrait les données d'un plan PDF.

        Args:
            pdf_path: Chemin vers le fichier PDF

        Returns:
            ExtractedPlanData avec les données extraites
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"Fichier non trouvé: {pdf_path}")

        result = ExtractedPlanData(
            filename=path.name,
            num_pages=0,
        )

        try:
            with pdfplumber.open(pdf_path) as pdf:
                result.num_pages = len(pdf.pages)

                all_text = []
                all_tables = []

                for page_num, page in enumerate(pdf.pages):
                    # Extraire le texte
                    text = page.extract_text() or ""
                    all_text.append(text)

                    # Extraire les tableaux
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            all_tables.append({
                                "page": page_num + 1,
                                "data": table,
                            })

                result.raw_text = "\n".join(all_text)
                result.tables = all_tables

                # Si peu de texte, essayer l'OCR
                if len(result.raw_text.strip()) < 100 and self.use_ocr:
                    result.warnings.append(
                        "Peu de texte détecté, tentative d'OCR..."
                    )
                    ocr_text = self._extract_with_ocr(pdf_path)
                    if ocr_text:
                        result.raw_text += "\n" + ocr_text

                # Analyser le texte extrait
                self._analyze_text(result)

                # Analyser les tableaux
                self._analyze_tables(result)

        except Exception as e:
            result.warnings.append(f"Erreur lors de l'extraction: {str(e)}")

        return result

    def _extract_with_ocr(self, pdf_path: str) -> str:
        """Extrait le texte via OCR."""
        if not OCR_AVAILABLE:
            return ""

        try:
            from pdf2image import convert_from_path

            # Convertir PDF en images
            images = convert_from_path(pdf_path, dpi=150)

            ocr_text = []
            for img in images:
                text = pytesseract.image_to_string(img, lang='fra')
                ocr_text.append(text)

            return "\n".join(ocr_text)

        except Exception as e:
            return ""

    def _analyze_text(self, result: ExtractedPlanData) -> None:
        """Analyse le texte extrait pour trouver les données."""
        text = result.raw_text.lower()

        # Extraire les portées
        for pattern in self.PORTEE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    value = float(match.replace(",", "."))
                    # Filtrer les valeurs aberrantes (portées entre 1 et 20m généralement)
                    if 1.0 <= value <= 20.0:
                        result.portees.append(ExtractedValue(
                            value=value,
                            confidence=ConfidenceLevel.MEDIUM,
                            source="pattern",
                            raw_text=match,
                        ))
                except ValueError:
                    continue

        # Dédupliquer les portées
        seen_portees = set()
        unique_portees = []
        for p in result.portees:
            if p.value not in seen_portees:
                seen_portees.add(p.value)
                unique_portees.append(p)
        result.portees = unique_portees

        # Extraire les poutrelles
        for pattern in self.POUTRELLE_PATTERNS:
            matches = re.findall(pattern, result.raw_text, re.IGNORECASE)
            for match in matches:
                if len(match) >= 2:  # Filtrer les matches trop courts
                    result.poutrelles.append(ExtractedValue(
                        value=match.upper(),
                        confidence=ConfidenceLevel.MEDIUM,
                        source="pattern",
                        raw_text=match,
                    ))

        # Extraire les charges
        for charge_type, patterns in self.CHARGE_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        value = float(match.group(1).replace(",", "."))
                        extracted = ExtractedValue(
                            value=value,
                            confidence=ConfidenceLevel.MEDIUM,
                            source="pattern",
                            raw_text=match.group(0),
                        )
                        if charge_type == "permanente":
                            result.charge_permanente = extracted
                        else:
                            result.charge_exploitation = extracted
                        break
                    except ValueError:
                        continue

        # Extraire les entre-axes
        for pattern in self.ENTRAXE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    value = int(match)
                    # Entre-axes typiques: 40-80 cm
                    if 30 <= value <= 100:
                        result.entraxes.append(ExtractedValue(
                            value=value,
                            confidence=ConfidenceLevel.MEDIUM,
                            source="pattern",
                            raw_text=match,
                        ))
                except ValueError:
                    continue

        # Extraire l'épaisseur de dalle
        for pattern in self.DALLE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    # Gérer le format "16+4"
                    if "+" in pattern:
                        hourdis = int(match.group(1))
                        dalle = int(match.group(2))
                        result.hauteur_hourdis = ExtractedValue(
                            value=hourdis,
                            confidence=ConfidenceLevel.MEDIUM,
                            source="pattern",
                        )
                        result.epaisseur_dalle = ExtractedValue(
                            value=dalle,
                            confidence=ConfidenceLevel.MEDIUM,
                            source="pattern",
                        )
                    else:
                        value = int(match.group(1))
                        if 3 <= value <= 10:  # Épaisseur dalle typique
                            result.epaisseur_dalle = ExtractedValue(
                                value=value,
                                confidence=ConfidenceLevel.MEDIUM,
                                source="pattern",
                                raw_text=match.group(0),
                            )
                    break
                except (ValueError, IndexError):
                    continue

        # Extraire la hauteur de hourdis
        if not result.hauteur_hourdis:
            for pattern in self.HOURDIS_PATTERNS:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        value = int(match.group(1))
                        if 10 <= value <= 30:  # Hauteurs hourdis typiques
                            result.hauteur_hourdis = ExtractedValue(
                                value=value,
                                confidence=ConfidenceLevel.MEDIUM,
                                source="pattern",
                                raw_text=match.group(0),
                            )
                        break
                    except ValueError:
                        continue

    def _analyze_tables(self, result: ExtractedPlanData) -> None:
        """Analyse les tableaux extraits."""
        for table_info in result.tables:
            table = table_info["data"]
            if not table or len(table) < 2:
                continue

            # Chercher des en-têtes reconnaissables
            header = table[0] if table else []
            header_lower = [str(h).lower() if h else "" for h in header]

            # Détecter un tableau de charges
            if any("charge" in h or "g" == h or "q" == h for h in header_lower):
                self._parse_charge_table(result, table)

            # Détecter un tableau de portées
            if any("portée" in h or "travée" in h or "l" == h for h in header_lower):
                self._parse_portee_table(result, table)

    def _parse_charge_table(self, result: ExtractedPlanData, table: List) -> None:
        """Parse un tableau de charges."""
        for row in table[1:]:  # Skip header
            for i, cell in enumerate(row):
                if cell:
                    try:
                        value = float(str(cell).replace(",", "."))
                        # Heuristique simple basée sur les valeurs typiques
                        if 1 <= value <= 10:
                            if not result.charge_permanente:
                                result.charge_permanente = ExtractedValue(
                                    value=value,
                                    confidence=ConfidenceLevel.HIGH,
                                    source="table",
                                )
                            elif not result.charge_exploitation:
                                result.charge_exploitation = ExtractedValue(
                                    value=value,
                                    confidence=ConfidenceLevel.HIGH,
                                    source="table",
                                )
                    except ValueError:
                        continue

    def _parse_portee_table(self, result: ExtractedPlanData, table: List) -> None:
        """Parse un tableau de portées."""
        for row in table[1:]:  # Skip header
            for cell in row:
                if cell:
                    try:
                        value = float(str(cell).replace(",", "."))
                        if 1.0 <= value <= 15.0:
                            result.portees.append(ExtractedValue(
                                value=value,
                                confidence=ConfidenceLevel.HIGH,
                                source="table",
                            ))
                    except ValueError:
                        continue
