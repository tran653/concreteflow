from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import re

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    verify_password,
    get_password_hash
)
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.schemas import (
    LoginRequest,
    LoginResponse,
    UserRegister,
    UserResponse,
    PasswordChange
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


def create_slug(name: str) -> str:
    """Create URL-safe slug from company name."""
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug


@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return JWT token."""
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    # Update last login
    user.last_login = datetime.utcnow()

    # Create token
    access_token = create_access_token(
        subject=str(user.id),
        tenant_id=str(user.tenant_id)
    )

    return LoginResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """Register new user with new tenant (company)."""
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create tenant
    slug = create_slug(data.company_name)

    # Check if slug exists, append number if needed
    base_slug = slug
    counter = 1
    while True:
        result = await db.execute(
            select(Tenant).where(Tenant.slug == slug)
        )
        if not result.scalar_one_or_none():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    tenant = Tenant(
        name=data.company_name,
        slug=slug
    )
    db.add(tenant)
    await db.flush()  # Get tenant.id

    # Create user as admin of new tenant
    user = User(
        tenant_id=tenant.id,
        email=data.email,
        password_hash=get_password_hash(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(user)
    await db.flush()

    # Create token
    access_token = create_access_token(
        subject=str(user.id),
        tenant_id=str(tenant.id)
    )

    return LoginResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile."""
    return UserResponse.model_validate(current_user)


@router.post("/change-password")
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change current user password."""
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )

    current_user.password_hash = get_password_hash(data.new_password)
    return {"message": "Password updated successfully"}
