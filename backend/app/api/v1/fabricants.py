"""API endpoints pour les fabricants et cahiers de portées."""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from app.core.database import get_db
from app.models.user import User
from app.models.fabricant import Fabricant
from app.models.cahier_portees import CahierPortees, LigneCahierPortees
from app.schemas.fabricant import (
    FabricantCreate,
    FabricantUpdate,
    FabricantResponse,
    FabricantListResponse,
    CahierPorteesResponse,
    CahierPorteesListResponse,
    LigneCahierPorteesResponse,
    ImportCahierResponse
)
from app.api.deps import get_current_active_user, require_admin, require_engineer
from app.services.importer.cahier_portees_importer import CahierPorteesImporter

router = APIRouter(prefix="/fabricants", tags=["Fabricants"])


# ==================== FABRICANTS ====================

@router.get("", response_model=List[FabricantListResponse])
async def list_fabricants(
    active_only: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Liste des fabricants du tenant."""
    query = select(Fabricant).where(Fabricant.tenant_id == current_user.tenant_id)

    if active_only:
        query = query.where(Fabricant.is_active == True)

    query = query.order_by(Fabricant.nom)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{fabricant_id}", response_model=FabricantResponse)
async def get_fabricant(
    fabricant_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Récupère un fabricant par son ID."""
    result = await db.execute(
        select(Fabricant).where(
            Fabricant.id == fabricant_id,
            Fabricant.tenant_id == current_user.tenant_id
        )
    )
    fabricant = result.scalar_one_or_none()

    if not fabricant:
        raise HTTPException(status_code=404, detail="Fabricant non trouvé")

    return fabricant


@router.post("", response_model=FabricantResponse, status_code=status.HTTP_201_CREATED)
async def create_fabricant(
    data: FabricantCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Crée un nouveau fabricant (admin uniquement)."""
    # Vérifier unicité du code
    existing = await db.execute(
        select(Fabricant).where(
            Fabricant.tenant_id == current_user.tenant_id,
            Fabricant.code == data.code
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Un fabricant avec le code '{data.code}' existe déjà"
        )

    fabricant = Fabricant(
        tenant_id=current_user.tenant_id,
        **data.model_dump()
    )
    db.add(fabricant)
    await db.flush()
    await db.refresh(fabricant)
    return fabricant


@router.put("/{fabricant_id}", response_model=FabricantResponse)
async def update_fabricant(
    fabricant_id: UUID,
    data: FabricantUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Met à jour un fabricant (admin uniquement)."""
    result = await db.execute(
        select(Fabricant).where(
            Fabricant.id == fabricant_id,
            Fabricant.tenant_id == current_user.tenant_id
        )
    )
    fabricant = result.scalar_one_or_none()

    if not fabricant:
        raise HTTPException(status_code=404, detail="Fabricant non trouvé")

    # Vérifier unicité du nouveau code si modifié
    if data.code and data.code != fabricant.code:
        existing = await db.execute(
            select(Fabricant).where(
                Fabricant.tenant_id == current_user.tenant_id,
                Fabricant.code == data.code,
                Fabricant.id != fabricant_id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"Un fabricant avec le code '{data.code}' existe déjà"
            )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(fabricant, field, value)

    await db.flush()
    await db.refresh(fabricant)
    return fabricant


@router.delete("/{fabricant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fabricant(
    fabricant_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Supprime (désactive) un fabricant (admin uniquement)."""
    result = await db.execute(
        select(Fabricant).where(
            Fabricant.id == fabricant_id,
            Fabricant.tenant_id == current_user.tenant_id
        )
    )
    fabricant = result.scalar_one_or_none()

    if not fabricant:
        raise HTTPException(status_code=404, detail="Fabricant non trouvé")

    fabricant.is_active = False
    await db.flush()


# ==================== CAHIERS DE PORTEES ====================

@router.get("/{fabricant_id}/cahiers", response_model=List[CahierPorteesListResponse])
async def list_cahiers_portees(
    fabricant_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Liste des cahiers de portées d'un fabricant."""
    # Vérifier accès au fabricant
    fab_result = await db.execute(
        select(Fabricant).where(
            Fabricant.id == fabricant_id,
            Fabricant.tenant_id == current_user.tenant_id
        )
    )
    if not fab_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Fabricant non trouvé")

    result = await db.execute(
        select(CahierPortees)
        .where(CahierPortees.fabricant_id == fabricant_id)
        .order_by(CahierPortees.created_at.desc())
    )
    return result.scalars().all()


@router.get("/cahiers/{cahier_id}", response_model=CahierPorteesResponse)
async def get_cahier_portees(
    cahier_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Récupère un cahier de portées par son ID."""
    result = await db.execute(
        select(CahierPortees)
        .join(Fabricant)
        .where(
            CahierPortees.id == cahier_id,
            Fabricant.tenant_id == current_user.tenant_id
        )
    )
    cahier = result.scalar_one_or_none()

    if not cahier:
        raise HTTPException(status_code=404, detail="Cahier de portées non trouvé")

    return cahier


@router.post("/{fabricant_id}/cahiers/import", response_model=ImportCahierResponse)
async def import_cahier_portees(
    fabricant_id: UUID,
    file: UploadFile = File(...),
    nom: Optional[str] = Query(None, description="Nom du cahier"),
    version: Optional[str] = Query(None, description="Version du cahier"),
    type_poutrelle: str = Query("precontrainte", description="Type de poutrelle: precontrainte ou treillis"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Importe un cahier de portées depuis un fichier Excel (admin uniquement)."""
    # Vérifier accès au fabricant
    fab_result = await db.execute(
        select(Fabricant).where(
            Fabricant.id == fabricant_id,
            Fabricant.tenant_id == current_user.tenant_id
        )
    )
    fabricant = fab_result.scalar_one_or_none()

    if not fabricant:
        raise HTTPException(status_code=404, detail="Fabricant non trouvé")

    # Vérifier type de fichier
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(
            status_code=400,
            detail="Format de fichier non supporté. Utilisez .xlsx, .xls ou .csv"
        )

    # Lecture fichier
    content = await file.read()

    # Import
    importer = CahierPorteesImporter()
    lignes_data, import_result = importer.import_from_excel(content)

    if not import_result.success:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Erreur d'import",
                "erreurs": import_result.erreurs,
                "avertissements": import_result.avertissements
            }
        )

    # Création cahier
    cahier = CahierPortees(
        fabricant_id=fabricant_id,
        type_poutrelle=type_poutrelle,
        nom=nom or file.filename,
        version=version,
        fichier_original=file.filename,
        imported_at=datetime.utcnow()
    )
    db.add(cahier)
    await db.flush()

    # Création lignes
    for ligne_data in lignes_data:
        ligne = LigneCahierPortees(
            cahier_id=cahier.id,
            **ligne_data
        )
        db.add(ligne)

    await db.flush()

    return ImportCahierResponse(
        cahier_id=cahier.id,
        lignes_importees=import_result.lignes_importees,
        lignes_ignorees=import_result.lignes_ignorees,
        avertissements=import_result.avertissements
    )


@router.delete("/cahiers/{cahier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cahier_portees(
    cahier_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Supprime un cahier de portées (admin uniquement)."""
    result = await db.execute(
        select(CahierPortees)
        .join(Fabricant)
        .where(
            CahierPortees.id == cahier_id,
            Fabricant.tenant_id == current_user.tenant_id
        )
    )
    cahier = result.scalar_one_or_none()

    if not cahier:
        raise HTTPException(status_code=404, detail="Cahier de portées non trouvé")

    await db.delete(cahier)
    await db.flush()


# ==================== LIGNES CAHIER ====================

@router.get("/cahiers/{cahier_id}/lignes", response_model=List[LigneCahierPorteesResponse])
async def list_lignes_cahier(
    cahier_id: UUID,
    hauteur_hourdis: Optional[int] = Query(None, description="Filtrer par hauteur hourdis (cm)"),
    entraxe: Optional[int] = Query(None, description="Filtrer par entraxe (cm)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Récupère les lignes d'un cahier de portées avec filtres optionnels."""
    # Vérifier accès
    cahier_result = await db.execute(
        select(CahierPortees)
        .join(Fabricant)
        .where(
            CahierPortees.id == cahier_id,
            Fabricant.tenant_id == current_user.tenant_id
        )
    )
    if not cahier_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Cahier de portées non trouvé")

    query = select(LigneCahierPortees).where(LigneCahierPortees.cahier_id == cahier_id)

    if hauteur_hourdis:
        query = query.where(LigneCahierPortees.hauteur_hourdis_cm == hauteur_hourdis)
    if entraxe:
        query = query.where(LigneCahierPortees.entraxe_cm == entraxe)

    query = query.order_by(
        LigneCahierPortees.hauteur_hourdis_cm,
        LigneCahierPortees.reference_poutrelle
    )

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/cahiers/{cahier_id}/stats")
async def get_cahier_stats(
    cahier_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Récupère les statistiques d'un cahier de portées."""
    # Vérifier accès
    cahier_result = await db.execute(
        select(CahierPortees)
        .join(Fabricant)
        .where(
            CahierPortees.id == cahier_id,
            Fabricant.tenant_id == current_user.tenant_id
        )
    )
    cahier = cahier_result.scalar_one_or_none()
    if not cahier:
        raise HTTPException(status_code=404, detail="Cahier de portées non trouvé")

    # Compter les lignes
    count_result = await db.execute(
        select(func.count(LigneCahierPortees.id))
        .where(LigneCahierPortees.cahier_id == cahier_id)
    )
    total_lignes = count_result.scalar()

    # Hauteurs hourdis disponibles
    hauteurs_result = await db.execute(
        select(LigneCahierPortees.hauteur_hourdis_cm)
        .where(LigneCahierPortees.cahier_id == cahier_id)
        .distinct()
        .order_by(LigneCahierPortees.hauteur_hourdis_cm)
    )
    hauteurs = [h for h in hauteurs_result.scalars().all()]

    # Entraxes disponibles
    entraxes_result = await db.execute(
        select(LigneCahierPortees.entraxe_cm)
        .where(LigneCahierPortees.cahier_id == cahier_id)
        .distinct()
        .order_by(LigneCahierPortees.entraxe_cm)
    )
    entraxes = [e for e in entraxes_result.scalars().all()]

    # Références poutrelles uniques
    refs_result = await db.execute(
        select(func.count(func.distinct(LigneCahierPortees.reference_poutrelle)))
        .where(LigneCahierPortees.cahier_id == cahier_id)
    )
    nb_poutrelles = refs_result.scalar()

    return {
        "cahier_id": str(cahier_id),
        "nom": cahier.nom,
        "total_lignes": total_lignes,
        "nb_poutrelles_uniques": nb_poutrelles,
        "hauteurs_hourdis_disponibles": hauteurs,
        "entraxes_disponibles": entraxes
    }
