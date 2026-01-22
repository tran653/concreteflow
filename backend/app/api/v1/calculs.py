from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import tempfile
import os

from app.core.database import get_db
from app.services.pdf_import import PdfPlanExtractor, ExtractedPlanData
from app.models.user import User, UserRole
from app.models.projet import Projet
from app.models.calcul import Calcul, CalculStatus, TypeProduit
from app.models.fabricant import Fabricant
from app.models.cahier_portees import CahierPortees, LigneCahierPortees
from app.schemas import (
    CalculCreate,
    CalculUpdate,
    CalculResponse,
    CalculListResponse,
    CalculRunRequest,
    NormeInfo,
    NormeListResponse
)
from app.api.deps import get_current_active_user, require_engineer
from app.services.calculs.engine import run_calculation
from app.services.calculs.normes import NormeType, NormeFactory

router = APIRouter(prefix="/calculs", tags=["Calculs"])


@router.get("/normes", response_model=NormeListResponse)
async def list_normes():
    """
    List available calculation norms.

    Returns information about all supported norms including:
    - Code and display name
    - Region of application
    - Available concrete and steel classes
    - Safety coefficients
    """
    normes_data = NormeFactory.list_normes()
    normes = [NormeInfo(**n) for n in normes_data]
    return NormeListResponse(normes=normes)


@router.get("/normes/{norme_code}")
async def get_norme_details(norme_code: str):
    """
    Get detailed information about a specific norm.

    Args:
        norme_code: Norm code (EC2, ACI318, BAEL91, etc.)
    """
    try:
        norme = NormeFactory.get_norme_from_code(norme_code)
        return {
            "code": norme.code,
            "nom_complet": norme.nom_complet,
            "region": norme.region,
            "coefficients": {
                "gamma_c": norme.gamma_c,
                "gamma_s": norme.gamma_s,
                "gamma_g": norme.gamma_g,
                "gamma_q": norme.gamma_q,
            },
            "classes_beton": norme.get_classes_beton(),
            "classes_acier": norme.get_classes_acier(),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("", response_model=List[CalculListResponse])
async def list_calculs(
    projet_id: UUID = None,
    status: CalculStatus = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List calculations."""
    query = select(Calcul).join(Projet).where(
        Projet.tenant_id == current_user.tenant_id
    )

    if projet_id:
        query = query.where(Calcul.projet_id == projet_id)

    if status:
        query = query.where(Calcul.status == status)

    query = query.order_by(Calcul.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    calculs = result.scalars().all()

    return [CalculListResponse.model_validate(c) for c in calculs]


@router.post("", response_model=CalculResponse, status_code=status.HTTP_201_CREATED)
async def create_calcul(
    data: CalculCreate,
    current_user: User = Depends(require_engineer),
    db: AsyncSession = Depends(get_db)
):
    """Create a new calculation."""
    # Verify project belongs to tenant
    result = await db.execute(
        select(Projet).where(
            Projet.id == data.projet_id,
            Projet.tenant_id == current_user.tenant_id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    calcul = Calcul(
        projet_id=data.projet_id,
        plan_id=data.plan_id,
        name=data.name,
        type_produit=data.type_produit,
        norme=data.norme,
        parametres=data.parametres.model_dump(),
        status=CalculStatus.DRAFT
    )
    db.add(calcul)
    await db.flush()

    return CalculResponse.model_validate(calcul)


@router.get("/{calcul_id}", response_model=CalculResponse)
async def get_calcul(
    calcul_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get calculation by ID."""
    result = await db.execute(
        select(Calcul).join(Projet).where(
            Calcul.id == calcul_id,
            Projet.tenant_id == current_user.tenant_id
        )
    )
    calcul = result.scalar_one_or_none()

    if not calcul:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calculation not found"
        )

    return CalculResponse.model_validate(calcul)


@router.put("/{calcul_id}", response_model=CalculResponse)
async def update_calcul(
    calcul_id: UUID,
    data: CalculUpdate,
    current_user: User = Depends(require_engineer),
    db: AsyncSession = Depends(get_db)
):
    """Update calculation parameters."""
    result = await db.execute(
        select(Calcul).join(Projet).where(
            Calcul.id == calcul_id,
            Projet.tenant_id == current_user.tenant_id
        )
    )
    calcul = result.scalar_one_or_none()

    if not calcul:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calculation not found"
        )

    if data.name is not None:
        calcul.name = data.name

    if data.parametres is not None:
        calcul.parametres = data.parametres.model_dump()
        calcul.status = CalculStatus.DRAFT  # Reset status when params change
        calcul.resultats = {}

    await db.flush()
    return CalculResponse.model_validate(calcul)


@router.delete("/{calcul_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calcul(
    calcul_id: UUID,
    current_user: User = Depends(require_engineer),
    db: AsyncSession = Depends(get_db)
):
    """Delete calculation."""
    result = await db.execute(
        select(Calcul).join(Projet).where(
            Calcul.id == calcul_id,
            Projet.tenant_id == current_user.tenant_id
        )
    )
    calcul = result.scalar_one_or_none()

    if not calcul:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calculation not found"
        )

    await db.delete(calcul)


@router.post("/{calcul_id}/run", response_model=CalculResponse)
async def run_calcul(
    calcul_id: UUID,
    data: CalculRunRequest = CalculRunRequest(),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(require_engineer),
    db: AsyncSession = Depends(get_db)
):
    """Execute structural calculation."""
    result = await db.execute(
        select(Calcul).join(Projet).where(
            Calcul.id == calcul_id,
            Projet.tenant_id == current_user.tenant_id
        )
    )
    calcul = result.scalar_one_or_none()

    if not calcul:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calculation not found"
        )

    # Check if already computed
    if calcul.status == CalculStatus.COMPLETED and not data.force:
        return CalculResponse.model_validate(calcul)

    # Run calculation (synchronous for now, can be made async with Celery)
    try:
        calcul.status = CalculStatus.COMPUTING
        await db.flush()

        # For plancher poutrelles-hourdis, get cahier de portées data
        cahier_data = None
        if calcul.type_produit == TypeProduit.PLANCHER_POUTRELLES_HOURDIS:
            cahier_id = calcul.parametres.get('cahier_portees_id')
            if not cahier_id:
                raise ValueError("cahier_portees_id est requis pour le calcul plancher poutrelles-hourdis")

            # Verify access and get lines
            cahier_result = await db.execute(
                select(CahierPortees)
                .join(Fabricant)
                .where(
                    CahierPortees.id == UUID(cahier_id),
                    Fabricant.tenant_id == current_user.tenant_id
                )
            )
            cahier = cahier_result.scalar_one_or_none()
            if not cahier:
                raise ValueError("Cahier de portées non trouvé ou accès non autorisé")

            # Get all lines from cahier
            lignes_result = await db.execute(
                select(LigneCahierPortees)
                .where(LigneCahierPortees.cahier_id == cahier.id)
            )
            lignes = lignes_result.scalars().all()

            if not lignes:
                raise ValueError("Le cahier de portées est vide")

            cahier_data = [
                {
                    'reference_poutrelle': l.reference_poutrelle,
                    'hauteur_hourdis_cm': l.hauteur_hourdis_cm,
                    'entraxe_cm': l.entraxe_cm,
                    'epaisseur_table_cm': l.epaisseur_table_cm or 5.0,
                    'portees_limites': l.portees_limites
                }
                for l in lignes
            ]

        # Execute calculation
        resultats = run_calculation(
            type_produit=calcul.type_produit,
            parametres=calcul.parametres,
            norme=calcul.norme,
            cahier_portees_data=cahier_data
        )

        calcul.resultats = resultats
        calcul.status = CalculStatus.COMPLETED
        calcul.computed_at = datetime.utcnow()
        calcul.error_message = None

    except Exception as e:
        calcul.status = CalculStatus.ERROR
        calcul.error_message = str(e)

    await db.flush()
    return CalculResponse.model_validate(calcul)


@router.get("/{calcul_id}/results")
async def get_calcul_results(
    calcul_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed calculation results."""
    result = await db.execute(
        select(Calcul).join(Projet).where(
            Calcul.id == calcul_id,
            Projet.tenant_id == current_user.tenant_id
        )
    )
    calcul = result.scalar_one_or_none()

    if not calcul:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calculation not found"
        )

    if calcul.status != CalculStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Calculation not completed (status: {calcul.status.value})"
        )

    return {
        "calcul_id": str(calcul.id),
        "name": calcul.name,
        "type_produit": calcul.type_produit.value,
        "norme": calcul.norme,
        "parametres": calcul.parametres,
        "resultats": calcul.resultats,
        "computed_at": calcul.computed_at.isoformat() if calcul.computed_at else None
    }


@router.post("/import-pdf")
async def import_pdf_plan(
    file: UploadFile = File(...),
    use_ocr: bool = Query(False, description="Utiliser OCR pour les PDF scannés"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Import a PDF plan and extract structural parameters.

    Extracts:
    - Portées (spans)
    - Poutrelles (joists)
    - Charges (loads)
    - Entre-axes (spacing)
    - Dalle thickness
    - Hourdis type

    Returns extracted data for user validation before creating calculation.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier doit être au format PDF"
        )

    # Save uploaded file temporarily
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)

    try:
        content = await file.read()
        with open(temp_path, 'wb') as f:
            f.write(content)

        # Extract data from PDF
        extractor = PdfPlanExtractor(use_ocr=use_ocr)
        extracted = extractor.extract(temp_path)

        # Convert to response format
        def format_value(v):
            if v is None:
                return None
            return {
                "value": v.value,
                "confidence": v.confidence,
                "source": v.source
            }

        return {
            "success": True,
            "filename": file.filename,
            "extraction_confidence": extracted.confidence_globale,
            "data": {
                "portees": [format_value(p) for p in extracted.portees],
                "poutrelles": [format_value(p) for p in extracted.poutrelles],
                "charges_permanentes": [format_value(c) for c in extracted.charges_permanentes],
                "charges_exploitation": [format_value(c) for c in extracted.charges_exploitation],
                "entre_axes": [format_value(e) for e in extracted.entre_axes],
                "epaisseur_dalle": format_value(extracted.epaisseur_dalle),
                "type_hourdis": format_value(extracted.type_hourdis),
            },
            "raw_text_preview": extracted.texte_brut[:500] if extracted.texte_brut else None,
            "tables_found": len(extracted.tables_extraites),
            "message": "Données extraites. Veuillez vérifier et ajuster avant de créer le calcul."
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'extraction du PDF: {str(e)}"
        )
    finally:
        # Cleanup temp files
        try:
            os.remove(temp_path)
            os.rmdir(temp_dir)
        except:
            pass
