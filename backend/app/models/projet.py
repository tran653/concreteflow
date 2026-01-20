from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base
from app.core.types import GUID


class ProjetStatus(str, enum.Enum):
    DRAFT = "draft"  # Brouillon
    IN_STUDY = "in_study"  # En étude
    VALIDATED = "validated"  # Validé
    IN_PRODUCTION = "in_production"  # En production
    DELIVERED = "delivered"  # Livré
    ARCHIVED = "archived"  # Archivé


class Projet(Base):
    """Construction project model."""
    __tablename__ = "projets"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(GUID(), ForeignKey("tenants.id"), nullable=False)

    # Project info
    reference = Column(String(50), nullable=False, index=True)  # Internal reference
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Client info
    client_name = Column(String(255))
    client_contact = Column(String(255))
    client_phone = Column(String(50))
    client_email = Column(String(255))

    # Location
    address = Column(String(500))
    city = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), default="France")

    # Status
    status = Column(Enum(ProjetStatus), default=ProjetStatus.DRAFT, nullable=False)

    # Dates
    date_start = Column(DateTime)
    date_delivery = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="projets")
    plans = relationship("Plan", back_populates="projet", cascade="all, delete-orphan")
    calculs = relationship("Calcul", back_populates="projet", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Projet {self.reference}: {self.name}>"
