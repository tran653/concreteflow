from sqlalchemy import Column, String, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.core.database import Base


class Tenant(Base):
    """Multi-tenant organization model."""
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)

    # Company info
    address = Column(String(500))
    phone = Column(String(50))
    email = Column(String(255))
    siret = Column(String(20))  # French company ID

    # Settings
    settings = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    projets = relationship("Projet", back_populates="tenant", cascade="all, delete-orphan")
    fabricants = relationship("Fabricant", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant {self.name}>"
