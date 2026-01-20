from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, JSON, Float, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base
from app.core.types import GUID


class ElementStatus(str, enum.Enum):
    DESIGNED = "designed"  # Dimensionné
    TO_PRODUCE = "to_produce"  # À fabriquer
    IN_PRODUCTION = "in_production"  # En fabrication
    PRODUCED = "produced"  # Fabriqué
    DELIVERED = "delivered"  # Livré
    INSTALLED = "installed"  # Posé


class Element(Base):
    """Precast element model (poutrelle, prédalle, etc.)."""
    __tablename__ = "elements"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    calcul_id = Column(GUID(), ForeignKey("calculs.id"), nullable=False)

    # Identification
    reference = Column(String(50), nullable=False)  # e.g., "PP-001", "DA-A1"
    designation = Column(String(255))

    # Geometry
    longueur = Column(Float)  # Length in mm
    largeur = Column(Float)  # Width in mm
    hauteur = Column(Float)  # Height in mm
    poids = Column(Float)  # Weight in kg

    # Position in plan
    position = Column(JSON)  # { "x": 0, "y": 0, "rotation": 0 }

    # Reinforcement
    ferraillage = Column(JSON)
    # Structure:
    # {
    #   "fils": [{"diameter": 5, "count": 4, "position": "inf"}],
    #   "torons": [{"type": "T15.7", "count": 2, "tension": 1395}],
    #   "barres": [{"diameter": 12, "count": 2, "longueur": 4500}],
    #   "cadres": {"diameter": 8, "espacement": 200}
    # }

    # Concrete
    classe_beton = Column(String(20))  # e.g., "C40/50"
    volume_beton = Column(Float)  # m³

    # Production tracking
    status = Column(Enum(ElementStatus), default=ElementStatus.DESIGNED)
    numero_fabrication = Column(String(50))  # Production batch number
    date_fabrication = Column(DateTime)
    date_livraison = Column(DateTime)

    # Quality
    numero_lot = Column(Integer)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    calcul = relationship("Calcul", back_populates="elements")

    def __repr__(self):
        return f"<Element {self.reference}>"
