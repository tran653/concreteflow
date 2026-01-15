"""Modèle Fabricant de poutrelles précontraintes."""
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.core.database import Base


class Fabricant(Base):
    """Fabricant de poutrelles précontraintes."""
    __tablename__ = "fabricants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Informations fabricant
    nom = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)  # Code court unique par tenant
    description = Column(Text)

    # Contact
    adresse = Column(String(500))
    telephone = Column(String(50))
    email = Column(String(255))
    site_web = Column(String(255))

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    tenant = relationship("Tenant", back_populates="fabricants")
    cahiers_portees = relationship(
        "CahierPortees",
        back_populates="fabricant",
        cascade="all, delete-orphan"
    )

    # Contrainte unicité code par tenant
    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_fabricant_tenant_code'),
    )

    def __repr__(self):
        return f"<Fabricant {self.nom} ({self.code})>"
