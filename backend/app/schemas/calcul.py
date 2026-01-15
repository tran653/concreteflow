from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from app.models.calcul import TypeProduit, CalculStatus


class CalculParametres(BaseModel):
    """Input parameters for structural calculation."""
    geometrie: Dict[str, float] = {}
    # { "portee": 5.0, "largeur": 0.6, "hauteur": 0.2, "enrobage": 25 }

    charges: Dict[str, float] = {}
    # { "permanentes": 5.0, "exploitation": 2.5, "cloisons": 1.0 }

    materiaux: Dict[str, str] = {}
    # { "classe_beton": "C30/37", "classe_acier": "S500", "type_acier_precontrainte": "Y1860S7" }

    conditions: Dict[str, Any] = {}
    # { "classe_exposition": "XC1", "duree_vie": 50, "classe_feu": "R60" }


class CalculResultats(BaseModel):
    """Output results from structural calculation."""
    flexion: Optional[Dict[str, Any]] = None
    fleche: Optional[Dict[str, Any]] = None
    effort_tranchant: Optional[Dict[str, Any]] = None
    ferraillage: Optional[Dict[str, Any]] = None
    feu: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None


class CalculBase(BaseModel):
    name: str
    type_produit: TypeProduit
    norme: str = "EC2"


class CalculCreate(CalculBase):
    projet_id: UUID
    plan_id: Optional[UUID] = None
    parametres: CalculParametres = CalculParametres()


class CalculUpdate(BaseModel):
    name: Optional[str] = None
    parametres: Optional[CalculParametres] = None


class CalculResponse(CalculBase):
    id: UUID
    projet_id: UUID
    plan_id: Optional[UUID] = None
    parametres: Dict[str, Any]
    resultats: Dict[str, Any]
    status: CalculStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    computed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CalculListResponse(BaseModel):
    id: UUID
    name: str
    type_produit: TypeProduit
    status: CalculStatus
    created_at: datetime
    computed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CalculRunRequest(BaseModel):
    """Request to run a calculation."""
    force: bool = False  # Force recalculation even if already computed
