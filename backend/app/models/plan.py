from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.core.database import Base


class Plan(Base):
    """Floor plan model - represents a level/floor in a project."""
    __tablename__ = "plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    projet_id = Column(UUID(as_uuid=True), ForeignKey("projets.id"), nullable=False)

    # Plan info
    name = Column(String(255), nullable=False)  # e.g., "RDC", "Niveau 1", "Toiture"
    level = Column(Float, default=0.0)  # Floor level in meters

    # File references
    file_url = Column(String(500))  # Original DXF file URL
    thumbnail_url = Column(String(500))  # Preview image

    # Geometric data (stored as JSON for flexibility)
    contour = Column(JSON)  # Plan boundary polygon
    openings = Column(JSON)  # Trémies, réservations
    elements_data = Column(JSON)  # Cached element positions

    # DXF import metadata
    dxf_metadata = Column(JSON)  # Layers, units, scale, etc.

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    projet = relationship("Projet", back_populates="plans")
    calculs = relationship("Calcul", back_populates="plan", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Plan {self.name}>"
