from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.projets import router as projets_router
from app.api.v1.calculs import router as calculs_router
from app.api.v1.plans import router as plans_router
from app.api.v1.exports import router as exports_router
from app.api.v1.fabricants import router as fabricants_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(projets_router)
api_router.include_router(calculs_router)
api_router.include_router(plans_router)
api_router.include_router(exports_router)
api_router.include_router(fabricants_router)
