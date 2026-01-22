"""Schémas Pydantic pour les fabricants et cahiers de portées."""
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# ============== Fabricant ==============

class FabricantBase(BaseModel):
    nom: str
    code: str
    description: Optional[str] = None
    adresse: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[EmailStr] = None
    site_web: Optional[str] = None


class FabricantCreate(FabricantBase):
    pass


class FabricantUpdate(BaseModel):
    nom: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    adresse: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[EmailStr] = None
    site_web: Optional[str] = None
    is_active: Optional[bool] = None


class FabricantResponse(FabricantBase):
    id: UUID
    tenant_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FabricantListResponse(BaseModel):
    id: UUID
    nom: str
    code: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Cahier de Portées ==============

class CahierPorteesBase(BaseModel):
    nom: str
    version: Optional[str] = None
    notes: Optional[str] = None


class CahierPorteesCreate(CahierPorteesBase):
    date_validite: Optional[datetime] = None


class CahierPorteesUpdate(BaseModel):
    nom: Optional[str] = None
    version: Optional[str] = None
    notes: Optional[str] = None
    date_validite: Optional[datetime] = None


class CahierPorteesResponse(CahierPorteesBase):
    id: UUID
    fabricant_id: UUID
    type_poutrelle: str = "precontrainte"
    fichier_original: Optional[str] = None
    date_validite: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    imported_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CahierPorteesListResponse(BaseModel):
    id: UUID
    nom: str
    type_poutrelle: str = "precontrainte"
    version: Optional[str] = None
    fichier_original: Optional[str] = None
    created_at: datetime
    imported_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============== Ligne Cahier de Portées ==============

class LigneCahierPorteesBase(BaseModel):
    reference_poutrelle: str
    hauteur_hourdis_cm: int
    entraxe_cm: int
    epaisseur_table_cm: float = 5.0
    portees_limites: Dict[str, float]  # {"250": 6.20, "300": 5.95, ...}


class LigneCahierPorteesCreate(LigneCahierPorteesBase):
    hauteur_totale_cm: Optional[float] = None
    poids_lineique_kg_m: Optional[float] = None
    inertie_cm4: Optional[float] = None
    notes: Optional[str] = None


class LigneCahierPorteesResponse(LigneCahierPorteesBase):
    id: UUID
    cahier_id: UUID
    hauteur_totale_cm: Optional[float] = None
    poids_lineique_kg_m: Optional[float] = None
    inertie_cm4: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Import ==============

class ImportCahierRequest(BaseModel):
    nom: Optional[str] = None
    version: Optional[str] = None


class ImportCahierResponse(BaseModel):
    cahier_id: UUID
    lignes_importees: int
    lignes_ignorees: int
    avertissements: List[str] = []


# ============== Sélection Poutrelle (pour calcul) ==============

class SelectionPoutrelleParams(BaseModel):
    cahier_portees_id: UUID
    portee: float  # m
    permanentes: float  # kN/m²
    exploitation: float  # kN/m²
    entraxe_souhaite: Optional[int] = None  # cm
    hauteur_hourdis: Optional[int] = None  # cm
    optimisation: str = "economique"  # "economique", "minimal_hauteur", "maximal_reserve"


class PoutrelleSelectionnee(BaseModel):
    reference: str
    hauteur_hourdis_cm: int
    entraxe_cm: int
    epaisseur_table_cm: float
    hauteur_totale_cm: float


class VerificationPortee(BaseModel):
    portee_demandee_m: float
    portee_limite_m: float
    charge_utilisee_kg_m2: int
    ratio_utilisation_pct: float
    reserve_portee_m: float


class AlternativePoutrelle(BaseModel):
    reference: str
    hauteur_hourdis_cm: int
    entraxe_cm: int
    portee_limite_m: float
    ratio_utilisation_pct: float
    hauteur_totale_cm: float


class SelectionPoutrelleResponse(BaseModel):
    verification_ok: bool
    message: str
    poutrelle: Optional[PoutrelleSelectionnee] = None
    verification: Optional[VerificationPortee] = None
    alternatives: List[AlternativePoutrelle] = []
    nombre_candidates: int = 0
