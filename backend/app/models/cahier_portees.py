"""Modèles pour les cahiers de portées limites."""
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, JSON, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.core.database import Base


class CahierPortees(Base):
    """Cahier de portées limites d'un fabricant."""
    __tablename__ = "cahiers_portees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fabricant_id = Column(UUID(as_uuid=True), ForeignKey("fabricants.id"), nullable=False)

    # Métadonnées du cahier
    nom = Column(String(255), nullable=False)  # Ex: "Gamme standard 2024"
    version = Column(String(50))  # Ex: "v2.1"
    date_validite = Column(DateTime)  # Date limite de validité
    notes = Column(Text)

    # Fichier source
    fichier_original = Column(String(500))  # Nom du fichier importé

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    imported_at = Column(DateTime)  # Date d'import effectif

    # Relations
    fabricant = relationship("Fabricant", back_populates="cahiers_portees")
    lignes = relationship(
        "LigneCahierPortees",
        back_populates="cahier",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<CahierPortees {self.nom}>"


class LigneCahierPortees(Base):
    """Ligne individuelle du cahier de portées limites."""
    __tablename__ = "lignes_cahier_portees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cahier_id = Column(UUID(as_uuid=True), ForeignKey("cahiers_portees.id"), nullable=False)

    # Identification poutrelle
    reference_poutrelle = Column(String(100), nullable=False)  # Ex: "BP 113", "SP 114"

    # Configuration plancher
    hauteur_hourdis_cm = Column(Integer, nullable=False)  # 12, 16, 20, 25
    entraxe_cm = Column(Integer, nullable=False)  # Ex: 60, 62, 65
    epaisseur_table_cm = Column(Float, default=5.0)  # Table de compression

    # Hauteur totale calculée
    hauteur_totale_cm = Column(Float)  # Poutrelle + hourdis + table

    # Portées limites par charge (JSON)
    # Structure: { "250": 5.20, "300": 4.95, "350": 4.70, ... }
    # Clé: charge G+Q en kg/m² ou daN/m²
    # Valeur: portée limite en mètres
    portees_limites = Column(JSON, nullable=False)

    # Métadonnées optionnelles
    poids_lineique_kg_m = Column(Float)  # Poids de la poutrelle
    inertie_cm4 = Column(Float)  # Moment d'inertie si disponible
    notes = Column(String(500))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    cahier = relationship("CahierPortees", back_populates="lignes")

    # Index pour recherche efficace
    __table_args__ = (
        Index('ix_ligne_recherche', 'cahier_id', 'hauteur_hourdis_cm', 'entraxe_cm'),
    )

    def __repr__(self):
        return f"<LigneCahierPortees {self.reference_poutrelle} H{self.hauteur_hourdis_cm}>"
