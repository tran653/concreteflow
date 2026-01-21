"""
Factory pour l'instanciation des normes de calcul.

Utilise le pattern Factory pour créer la bonne implémentation
de norme selon le type demandé.
"""

from typing import Dict, List, Type, Optional

from . import NormeType
from .base import NormeBase
from .eurocode import EurocodeNorme
from .aci318 import ACI318Norme
from .bael import BAELNorme


class NormeFactory:
    """
    Factory pour créer les instances de normes de calcul.

    Usage:
        norme = NormeFactory.get_norme(NormeType.EC2)
        norme.set_beton("C30/37")
        norme.set_acier("S500")
        result = norme.calcul_flexion(moment, largeur, hauteur)
    """

    # Registre des normes disponibles
    _registry: Dict[NormeType, Type[NormeBase]] = {
        NormeType.EC2: EurocodeNorme,
        NormeType.ACI318: ACI318Norme,
        NormeType.BAEL91: BAELNorme,
        # NormeType.BS8110: BS8110Norme,  # À implémenter
        # NormeType.CSA_A23: CSAA23Norme,  # À implémenter
    }

    @classmethod
    def get_norme(
        cls,
        norme_type: NormeType,
        classe_beton: Optional[str] = None,
        classe_acier: Optional[str] = None
    ) -> NormeBase:
        """
        Crée et retourne une instance de la norme demandée.

        Args:
            norme_type: Type de norme (NormeType enum)
            classe_beton: Classe de béton optionnelle à définir
            classe_acier: Classe d'acier optionnelle à définir

        Returns:
            Instance de la norme

        Raises:
            ValueError: Si la norme n'est pas supportée
        """
        if norme_type not in cls._registry:
            supported = ", ".join(n.value for n in cls._registry.keys())
            raise ValueError(
                f"Norme '{norme_type.value}' non supportée. "
                f"Normes disponibles: {supported}"
            )

        norme_class = cls._registry[norme_type]
        norme = norme_class()

        # Définir les matériaux si spécifiés
        if classe_beton:
            norme.set_beton(classe_beton)
        if classe_acier:
            norme.set_acier(classe_acier)

        return norme

    @classmethod
    def get_norme_from_code(
        cls,
        code: str,
        classe_beton: Optional[str] = None,
        classe_acier: Optional[str] = None
    ) -> NormeBase:
        """
        Crée une norme à partir de son code string.

        Args:
            code: Code de la norme (ex: "EC2", "ACI318", "BAEL91")
            classe_beton: Classe de béton optionnelle
            classe_acier: Classe d'acier optionnelle

        Returns:
            Instance de la norme

        Raises:
            ValueError: Si le code n'est pas reconnu
        """
        # Normaliser le code
        code_upper = code.upper().replace(" ", "").replace("-", "").replace("_", "")

        # Mapping des codes alternatifs
        code_mapping = {
            "EC2": NormeType.EC2,
            "EUROCODE2": NormeType.EC2,
            "EUROCODE": NormeType.EC2,
            "EN199211": NormeType.EC2,
            "ACI318": NormeType.ACI318,
            "ACI": NormeType.ACI318,
            "BAEL91": NormeType.BAEL91,
            "BAEL": NormeType.BAEL91,
            "BAEL99": NormeType.BAEL91,
            "BS8110": NormeType.BS8110,
            "BS": NormeType.BS8110,
            "CSAA23": NormeType.CSA_A23,
            "CSA": NormeType.CSA_A23,
        }

        norme_type = code_mapping.get(code_upper)

        if norme_type is None:
            raise ValueError(
                f"Code de norme '{code}' non reconnu. "
                f"Codes acceptés: EC2, ACI318, BAEL91, BS8110, CSA_A23"
            )

        return cls.get_norme(norme_type, classe_beton, classe_acier)

    @classmethod
    def list_normes(cls) -> List[Dict]:
        """
        Retourne la liste des normes disponibles avec leurs informations.

        Returns:
            Liste de dictionnaires avec code, nom, région, et statut
        """
        result = []

        for norme_type in NormeType:
            is_implemented = norme_type in cls._registry

            info = {
                "code": norme_type.value,
                "display_name": norme_type.display_name,
                "region": norme_type.region,
                "implemented": is_implemented,
            }

            if is_implemented:
                # Ajouter les classes de matériaux disponibles
                norme = cls._registry[norme_type]()
                info["classes_beton"] = norme.get_classes_beton()
                info["classes_acier"] = norme.get_classes_acier()
                info["coefficients"] = {
                    "gamma_c": norme.gamma_c,
                    "gamma_s": norme.gamma_s,
                    "gamma_g": norme.gamma_g,
                    "gamma_q": norme.gamma_q,
                }

            result.append(info)

        return result

    @classmethod
    def get_default_materials(cls, norme_type: NormeType) -> Dict[str, str]:
        """
        Retourne les matériaux par défaut pour une norme.

        Args:
            norme_type: Type de norme

        Returns:
            Dict avec classe_beton et classe_acier par défaut
        """
        defaults = {
            NormeType.EC2: {
                "classe_beton": "C30/37",
                "classe_acier": "S500",
            },
            NormeType.ACI318: {
                "classe_beton": "C28",
                "classe_acier": "Grade60",
            },
            NormeType.BAEL91: {
                "classe_beton": "B30",
                "classe_acier": "HA500",
            },
            NormeType.BS8110: {
                "classe_beton": "C30",
                "classe_acier": "Grade500",
            },
            NormeType.CSA_A23: {
                "classe_beton": "C30",
                "classe_acier": "400W",
            },
        }

        return defaults.get(norme_type, {
            "classe_beton": "C30/37",
            "classe_acier": "S500",
        })

    @classmethod
    def compare_normes(
        cls,
        moment: float,
        largeur: float,
        hauteur: float,
        enrobage: float = 0.03
    ) -> Dict[str, Dict]:
        """
        Compare les résultats de calcul de flexion entre les normes.

        Utile pour la documentation et les études comparatives.

        Args:
            moment: Moment ELU (kN.m)
            largeur: Largeur de section (m)
            hauteur: Hauteur de section (m)
            enrobage: Enrobage (m)

        Returns:
            Dict avec les résultats par norme
        """
        results = {}

        for norme_type in cls._registry.keys():
            defaults = cls.get_default_materials(norme_type)
            norme = cls.get_norme(
                norme_type,
                defaults["classe_beton"],
                defaults["classe_acier"]
            )

            try:
                result = norme.calcul_flexion(moment, largeur, hauteur, enrobage)
                results[norme_type.value] = {
                    "section_acier": round(result.section_acier, 2),
                    "moment_resistant": round(result.moment_resistant, 2),
                    "verification_ok": result.verification_ok,
                    "message": result.message,
                    "coefficients": {
                        "gamma_c": norme.gamma_c,
                        "gamma_s": norme.gamma_s,
                    },
                }
            except Exception as e:
                results[norme_type.value] = {
                    "error": str(e),
                }

        return results
