"""
API endpoints pour la gestion des plans et import DXF.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.projet import Projet
from app.models.plan import Plan
from app.api.deps import get_current_active_user
from app.services.dxf import DXFParser, extract_plan_geometry

router = APIRouter(prefix="/plans", tags=["Plans"])


@router.post("/upload-dxf/{projet_id}")
async def upload_dxf(
    projet_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload et parse un fichier DXF pour un projet.
    """
    # Vérifier le projet
    result = await db.execute(
        select(Projet).where(
            Projet.id == projet_id,
            Projet.tenant_id == current_user.tenant_id
        )
    )
    projet = result.scalar_one_or_none()
    if not projet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projet non trouvé"
        )

    # Vérifier le type de fichier
    if not file.filename.lower().endswith('.dxf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier doit être au format DXF"
        )

    # Lire le contenu
    content = await file.read()

    # Parser le DXF
    parser = DXFParser()
    parse_result = parser.parse_bytes(content, file.filename)

    if not parse_result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur de parsing DXF: {parse_result.error}"
        )

    # Sauvegarder le fichier
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(projet_id))
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)

    with open(file_path, 'wb') as f:
        f.write(content)

    # Extraire la géométrie pour les calculs
    geometry = extract_plan_geometry(parse_result.__dict__)

    # Créer le plan en base
    plan = Plan(
        projet_id=projet_id,
        name=file.filename.replace('.dxf', '').replace('.DXF', ''),
        file_url=file_path,
        contour=parse_result.contours,
        openings=parse_result.openings,
        elements_data=geometry,
        dxf_metadata={
            "units": parse_result.units,
            "layers": parse_result.layers,
            "bounds": parse_result.bounds,
            "entity_count": len(parse_result.entities)
        }
    )
    db.add(plan)
    await db.flush()

    return {
        "id": str(plan.id),
        "name": plan.name,
        "parse_result": parse_result.to_dict(),
        "geometry": geometry
    }


@router.get("/{plan_id}")
async def get_plan(
    plan_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Récupère les détails d'un plan."""
    result = await db.execute(
        select(Plan).join(Projet).where(
            Plan.id == plan_id,
            Projet.tenant_id == current_user.tenant_id
        )
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan non trouvé"
        )

    return {
        "id": str(plan.id),
        "projet_id": str(plan.projet_id),
        "name": plan.name,
        "level": plan.level,
        "contour": plan.contour,
        "openings": plan.openings,
        "elements_data": plan.elements_data,
        "dxf_metadata": plan.dxf_metadata,
        "created_at": plan.created_at.isoformat()
    }


@router.get("/projet/{projet_id}")
async def list_projet_plans(
    projet_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Liste les plans d'un projet."""
    # Vérifier l'accès au projet
    result = await db.execute(
        select(Projet).where(
            Projet.id == projet_id,
            Projet.tenant_id == current_user.tenant_id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projet non trouvé"
        )

    # Récupérer les plans
    result = await db.execute(
        select(Plan).where(Plan.projet_id == projet_id).order_by(Plan.level)
    )
    plans = result.scalars().all()

    return [
        {
            "id": str(plan.id),
            "name": plan.name,
            "level": plan.level,
            "has_contour": bool(plan.contour),
            "opening_count": len(plan.openings) if plan.openings else 0,
            "created_at": plan.created_at.isoformat()
        }
        for plan in plans
    ]


@router.delete("/{plan_id}")
async def delete_plan(
    plan_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Supprime un plan."""
    result = await db.execute(
        select(Plan).join(Projet).where(
            Plan.id == plan_id,
            Projet.tenant_id == current_user.tenant_id
        )
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan non trouvé"
        )

    # Supprimer le fichier
    if plan.file_url and os.path.exists(plan.file_url):
        os.remove(plan.file_url)

    await db.delete(plan)
    return {"message": "Plan supprimé"}


@router.get("/{plan_id}/geometry")
async def get_plan_geometry(
    plan_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Récupère la géométrie détaillée d'un plan pour affichage."""
    result = await db.execute(
        select(Plan).join(Projet).where(
            Plan.id == plan_id,
            Projet.tenant_id == current_user.tenant_id
        )
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan non trouvé"
        )

    return {
        "bounds": plan.dxf_metadata.get("bounds", {}) if plan.dxf_metadata else {},
        "contours": plan.contour or [],
        "openings": plan.openings or [],
        "elements": plan.elements_data or {}
    }
