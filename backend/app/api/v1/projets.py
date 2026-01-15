from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from app.core.database import get_db
from app.models.user import User
from app.models.projet import Projet, ProjetStatus
from app.schemas import (
    ProjetCreate,
    ProjetUpdate,
    ProjetResponse,
    ProjetListResponse
)
from app.api.deps import get_current_active_user

router = APIRouter(prefix="/projets", tags=["Projets"])


@router.get("", response_model=List[ProjetListResponse])
async def list_projets(
    status: ProjetStatus = None,
    search: str = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List all projects for current tenant."""
    query = select(Projet).where(Projet.tenant_id == current_user.tenant_id)

    if status:
        query = query.where(Projet.status == status)

    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (Projet.name.ilike(search_filter)) |
            (Projet.reference.ilike(search_filter)) |
            (Projet.client_name.ilike(search_filter))
        )

    query = query.order_by(Projet.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    projets = result.scalars().all()

    return [ProjetListResponse.model_validate(p) for p in projets]


@router.post("", response_model=ProjetResponse, status_code=status.HTTP_201_CREATED)
async def create_projet(
    data: ProjetCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new project."""
    # Check reference uniqueness within tenant
    result = await db.execute(
        select(Projet).where(
            Projet.tenant_id == current_user.tenant_id,
            Projet.reference == data.reference
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project reference '{data.reference}' already exists"
        )

    projet = Projet(
        tenant_id=current_user.tenant_id,
        **data.model_dump()
    )
    db.add(projet)
    await db.flush()

    return ProjetResponse.model_validate(projet)


@router.get("/{projet_id}", response_model=ProjetResponse)
async def get_projet(
    projet_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get project by ID."""
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
            detail="Project not found"
        )

    return ProjetResponse.model_validate(projet)


@router.put("/{projet_id}", response_model=ProjetResponse)
async def update_projet(
    projet_id: UUID,
    data: ProjetUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update project."""
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
            detail="Project not found"
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(projet, field, value)

    await db.flush()
    return ProjetResponse.model_validate(projet)


@router.delete("/{projet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_projet(
    projet_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete project."""
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
            detail="Project not found"
        )

    await db.delete(projet)


@router.get("/{projet_id}/stats")
async def get_projet_stats(
    projet_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get project statistics."""
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
            detail="Project not found"
        )

    # Count plans and calculs
    from app.models.plan import Plan
    from app.models.calcul import Calcul, CalculStatus

    plans_count = await db.scalar(
        select(func.count(Plan.id)).where(Plan.projet_id == projet_id)
    )

    calculs_count = await db.scalar(
        select(func.count(Calcul.id)).where(Calcul.projet_id == projet_id)
    )

    calculs_completed = await db.scalar(
        select(func.count(Calcul.id)).where(
            Calcul.projet_id == projet_id,
            Calcul.status == CalculStatus.COMPLETED
        )
    )

    return {
        "plans_count": plans_count,
        "calculs_count": calculs_count,
        "calculs_completed": calculs_completed,
        "calculs_pending": calculs_count - calculs_completed
    }
