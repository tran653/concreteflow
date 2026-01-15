from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.projet import ProjetStatus


class ProjetBase(BaseModel):
    reference: str
    name: str
    description: Optional[str] = None
    client_name: Optional[str] = None
    client_contact: Optional[str] = None
    client_phone: Optional[str] = None
    client_email: Optional[EmailStr] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "France"


class ProjetCreate(ProjetBase):
    date_start: Optional[datetime] = None
    date_delivery: Optional[datetime] = None


class ProjetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    client_name: Optional[str] = None
    client_contact: Optional[str] = None
    client_phone: Optional[str] = None
    client_email: Optional[EmailStr] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    status: Optional[ProjetStatus] = None
    date_start: Optional[datetime] = None
    date_delivery: Optional[datetime] = None


class ProjetResponse(ProjetBase):
    id: UUID
    tenant_id: UUID
    status: ProjetStatus
    date_start: Optional[datetime] = None
    date_delivery: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjetListResponse(BaseModel):
    id: UUID
    reference: str
    name: str
    client_name: Optional[str] = None
    city: Optional[str] = None
    status: ProjetStatus
    date_delivery: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
