from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class TenantBase(BaseModel):
    name: str
    slug: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    siret: Optional[str] = None


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    siret: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class TenantResponse(TenantBase):
    id: UUID
    settings: Dict[str, Any] = {}
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
