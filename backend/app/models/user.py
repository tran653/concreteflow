from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base
from app.core.types import GUID


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ENGINEER = "engineer"  # Ingénieur - full access to calculations
    TECHNICIAN = "technician"  # Technicien - limited access
    VIEWER = "viewer"  # Lecteur - read only


class User(Base):
    """User model with role-based access control."""
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(GUID(), ForeignKey("tenants.id"), nullable=False)

    # Auth
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Profile
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(50))

    # Role & Status
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")

    @property
    def full_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email

    def __repr__(self):
        return f"<User {self.email}>"
