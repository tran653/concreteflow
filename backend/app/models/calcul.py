from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class TypeProduit(str, enum.Enum):
    POUTRELLE = "poutrelle"  # Prestressed beam
    PREDALLE = "predalle"  # Precast slab
    DALLE_ALVEOLAIRE = "dalle_alveolaire"  # Hollow core slab
    POUTRE = "poutre"  # Beam
    DALLE_PLEINE = "dalle_pleine"  # Solid slab (cast in place)
    PLANCHER_POUTRELLES_HOURDIS = "plancher_poutrelles_hourdis"  # Floor with beams and blocks


class CalculStatus(str, enum.Enum):
    DRAFT = "draft"  # Input not complete
    PENDING = "pending"  # Ready to compute
    COMPUTING = "computing"  # In progress
    COMPLETED = "completed"  # Done successfully
    ERROR = "error"  # Computation failed
    VALIDATED = "validated"  # Reviewed and approved


class Calcul(Base):
    """Structural calculation model."""
    __tablename__ = "calculs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    projet_id = Column(UUID(as_uuid=True), ForeignKey("projets.id"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=True)

    # Calculation info
    name = Column(String(255), nullable=False)
    type_produit = Column(Enum(TypeProduit), nullable=False)

    # Normative reference
    norme = Column(String(50), default="EC2")  # EC2, BPEL, DTU

    # Input parameters (JSON for flexibility)
    parametres = Column(JSON, nullable=False, default=dict)
    # Structure of parametres:
    # {
    #   "geometrie": { "portee": 5.0, "largeur": 0.6, "hauteur": 0.2 },
    #   "charges": { "permanentes": 5.0, "exploitation": 2.5 },
    #   "materiaux": { "classe_beton": "C30/37", "classe_acier": "S500" },
    #   "conditions": { "classe_exposition": "XC1", "duree_vie": 50 }
    # }

    # Results (JSON)
    resultats = Column(JSON, default=dict)
    # Structure of resultats:
    # {
    #   "flexion": { "moment_elu": 45.2, "moment_els": 32.1, "ok": true },
    #   "fleche": { "instantanee": 8.2, "differee": 12.4, "limite": 20.0, "ok": true },
    #   "effort_tranchant": { "ved": 25.3, "vrd": 45.0, "ok": true },
    #   "ferraillage": { "as_inf": 4.52, "as_sup": 2.26, "cadres": "HA8@200" }
    # }

    # Status
    status = Column(Enum(CalculStatus), default=CalculStatus.DRAFT, nullable=False)
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    computed_at = Column(DateTime)

    # Relationships
    projet = relationship("Projet", back_populates="calculs")
    plan = relationship("Plan", back_populates="calculs")
    elements = relationship("Element", back_populates="calcul", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Calcul {self.name} ({self.type_produit.value})>"
