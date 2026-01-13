"""Phase E1.2: Authentication API Routes.

Provides FastAPI routes for user registration, login, token refresh.
Integrates with authentication service and database.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional

from infra.database import get_db
from infra.authentication import (
    AuthenticationService, PasswordManager, TokenManager, User,
    UserRole, RoleBasedAccessControl
)


# Request/Response Models
class UserRegisterRequest(BaseModel):
    """User registration request."""
    username: str
    email: EmailStr
    password: str
    password_confirm: str


class UserRegisterResponse(BaseModel):
    """User registration response."""
    id: str
    username: str
    email: str
    role: str
    created_at: str


class LoginRequest(BaseModel):
    """User login request."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    old_password: str
    new_password: str
    password_confirm: str


class UserProfileResponse(BaseModel):
    """User profile response."""
    id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: str
    last_login_at: Optional[str]


# Authentication service factory
def get_auth_service(pwd_manager: PasswordManager = None,
                     token_manager: TokenManager = None) -> AuthenticationService:
    """Get or create authentication service.
    
    Args:
        pwd_manager: PasswordManager instance (optional, creates default)
        token_manager: TokenManager instance (optional, creates default)
        
    Returns:
        AuthenticationService instance
    """
    if not pwd_manager:
        pwd_manager = PasswordManager()
    
    if not token_manager:
        # In production, SECRET_KEY should come from config
        token_manager = TokenManager(
            secret_key="your-secret-key-change-in-production",
            access_token_expire_minutes=30,
            refresh_token_expire_days=7
        )
    
    return AuthenticationService(pwd_manager, token_manager)


def extract_token_from_header(authorization: str) -> str:
    """Extract JWT token from Authorization header.
    
    Args:
        authorization: Authorization header value (format: "Bearer <token>")
        
    Returns:
        Token string
        
    Raises:
        HTTPException: If header format invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )
    
    return parts[1]


async def get_current_user(
    authorization: Optional[str] = None,
    db: Session = Depends(get_db),
    auth_service: AuthenticationService = Depends(get_auth_service)
) -> User:
    """Dependency for getting current authenticated user.
    
    Usage:
        @app.get("/profile")
        async def get_profile(current_user: User = Depends(get_current_user)):
            return current_user.to_dict()
    
    Args:
        authorization: Authorization header
        db: Database session
        auth_service: Authentication service
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If not authenticated
    """
    token = extract_token_from_header(authorization)
    user = auth_service.get_current_user(db, token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return user


# Create router
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserRegisterResponse)
async def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db),
    auth_service: AuthenticationService = Depends(get_auth_service)
) -> dict:
    """Register new user.
    
    Args:
        request: Registration request with username, email, password
        db: Database session
        auth_service: Authentication service
        
    Returns:
        Created user details
        
    Raises:
        HTTPException: If validation fails or user exists
    """
    # Validate passwords match
    if request.password != request.password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    # Validate password strength
    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )
    
    try:
        user = auth_service.register_user(
            db, request.username, request.email, request.password
        )
        db.commit()
        
        return UserRegisterResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role.value,
            created_at=user.created_at.isoformat()
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
    auth_service: AuthenticationService = Depends(get_auth_service)
) -> dict:
    """Authenticate user and return tokens.
    
    Args:
        request: Login request with username and password
        db: Database session
        auth_service: Authentication service
        
    Returns:
        Access and refresh tokens
        
    Raises:
        HTTPException: If authentication fails
    """
    user = auth_service.authenticate_user(db, request.username, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    db.commit()
    tokens = auth_service.create_token_pair(user)
    
    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
    auth_service: AuthenticationService = Depends(get_auth_service)
) -> dict:
    """Refresh access token using refresh token.
    
    Args:
        request: Refresh token request
        db: Database session
        auth_service: Authentication service
        
    Returns:
        New access token with original refresh token
        
    Raises:
        HTTPException: If refresh token invalid
    """
    access_token = auth_service.refresh_access_token(db, request.refresh_token)
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=request.refresh_token
    )


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user)
) -> dict:
    """Get current user profile.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User profile details
    """
    return UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
        last_login_at=current_user.last_login_at.isoformat() if current_user.last_login_at else None
    )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    auth_service: AuthenticationService = Depends(get_auth_service)
) -> dict:
    """Change current user password.
    
    Args:
        request: Password change request
        current_user: Current authenticated user
        db: Database session
        auth_service: Authentication service
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If validation fails or old password incorrect
    """
    # Validate new passwords match
    if request.new_password != request.password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match"
        )
    
    # Validate password strength
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )
    
    # Change password
    if not auth_service.change_password(
        db, current_user, request.old_password, request.new_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
) -> dict:
    """Logout user (client-side token deletion).
    
    Note: JWT tokens cannot be revoked server-side without additional infrastructure
    (e.g., token blacklist). This endpoint is a placeholder for logging purposes.
    In production, implement token blacklist or use short expiration times.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    # In production, add token to blacklist or revocation list
    # For now, client should delete token locally
    
    return {"message": f"User {current_user.username} logged out successfully"}
