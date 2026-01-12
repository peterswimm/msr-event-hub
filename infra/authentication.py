"""Phase E1.2: Authentication Layer.

Provides JWT-based authentication with bcrypt password hashing.
Includes user/admin models, token generation/validation, protected routes.

Technologies:
- python-jose: JWT token handling
- bcrypt: Password hashing
- passlib: Password utilities
"""

from datetime import datetime, timedelta
from typing import Optional, Dict
from enum import Enum
import uuid
from functools import wraps

from sqlalchemy import Column, String, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext

from infra.models import Base


# Security configuration
class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    EVALUATOR = "evaluator"
    VIEWER = "viewer"


class User(Base):
    """User model for authentication.
    
    Attributes:
        id: Unique user ID (UUID)
        username: Unique username
        email: User email address
        hashed_password: Bcrypt hashed password
        role: User role (admin, evaluator, viewer)
        is_active: Whether user account is active
        created_at: Account creation timestamp
        updated_at: Last account update timestamp
        last_login_at: Last successful login timestamp
    """
    __tablename__ = "users"
    
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.VIEWER)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None
        }


class PasswordManager:
    """Manages password hashing and verification using bcrypt."""
    
    def __init__(self):
        """Initialize password manager with bcrypt context."""
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def hash_password(self, password: str) -> str:
        """Hash a plain text password.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Bcrypt hashed password
        """
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain text password against a hash.
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Bcrypt hash to verify against
            
        Returns:
            True if password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)


class TokenManager:
    """Manages JWT token generation and validation."""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256", 
                 access_token_expire_minutes: int = 30,
                 refresh_token_expire_days: int = 7):
        """Initialize token manager.
        
        Args:
            secret_key: Secret key for signing tokens (from config)
            algorithm: JWT algorithm (default: HS256)
            access_token_expire_minutes: Access token TTL (default: 30 min)
            refresh_token_expire_days: Refresh token TTL (default: 7 days)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
    
    def create_access_token(self, data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token.
        
        Args:
            data: Payload to encode (e.g., {"sub": user_id, "role": "admin"})
            expires_delta: Custom expiration delta (overrides default)
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create a JWT refresh token.
        
        Args:
            user_id: User ID for token
            
        Returns:
            JWT refresh token string
        """
        data = {"sub": user_id, "type": "refresh"}
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        data.update({"exp": expire})
        return jwt.encode(data, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify a JWT token and extract payload.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Token payload if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None


class AuthenticationService:
    """Service for user authentication and authorization."""
    
    def __init__(self, pwd_manager: PasswordManager, token_manager: TokenManager):
        """Initialize authentication service.
        
        Args:
            pwd_manager: PasswordManager instance
            token_manager: TokenManager instance
        """
        self.pwd_manager = pwd_manager
        self.token_manager = token_manager
    
    def register_user(self, session: Session, username: str, email: str, 
                     password: str, role: UserRole = UserRole.VIEWER) -> User:
        """Register a new user.
        
        Args:
            session: Database session
            username: Username (must be unique)
            email: Email address (must be unique)
            password: Plain text password
            role: User role (default: viewer)
            
        Returns:
            Created user
            
        Raises:
            ValueError: If username or email already exists
        """
        # Check for existing user
        existing = session.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing:
            raise ValueError(f"User {username} already exists")
        
        # Create new user
        user = User(
            username=username,
            email=email,
            hashed_password=self.pwd_manager.hash_password(password),
            role=role,
            is_active=True
        )
        
        session.add(user)
        session.flush()
        return user
    
    def authenticate_user(self, session: Session, username: str, 
                         password: str) -> Optional[User]:
        """Authenticate user with username and password.
        
        Args:
            session: Database session
            username: User's username
            password: User's plain text password
            
        Returns:
            User if authentication successful, None otherwise
        """
        user = session.query(User).filter(User.username == username).first()
        
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if not self.pwd_manager.verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        session.flush()
        
        return user
    
    def create_token_pair(self, user: User) -> Dict[str, str]:
        """Create access and refresh token pair for user.
        
        Args:
            user: Authenticated user
            
        Returns:
            Dictionary with access_token and refresh_token
        """
        access_token = self.token_manager.create_access_token(
            data={"sub": user.id, "username": user.username, "role": user.role.value}
        )
        refresh_token = self.token_manager.create_refresh_token(user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    def get_current_user(self, session: Session, token: str) -> Optional[User]:
        """Get current user from token.
        
        Args:
            session: Database session
            token: JWT access token
            
        Returns:
            User if token valid, None otherwise
        """
        payload = self.token_manager.verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = session.query(User).filter(User.id == user_id).first()
        return user if user and user.is_active else None
    
    def refresh_access_token(self, session: Session, refresh_token: str) -> Optional[str]:
        """Generate new access token from refresh token.
        
        Args:
            session: Database session
            refresh_token: JWT refresh token
            
        Returns:
            New access token if refresh token valid, None otherwise
        """
        payload = self.token_manager.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
        
        user_id = payload.get("sub")
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            return None
        
        return self.token_manager.create_access_token(
            data={"sub": user.id, "username": user.username, "role": user.role.value}
        )
    
    def change_password(self, session: Session, user: User, 
                       old_password: str, new_password: str) -> bool:
        """Change user password.
        
        Args:
            session: Database session
            user: User object
            old_password: Current password (verified)
            new_password: New password to set
            
        Returns:
            True if password changed successfully, False if old password incorrect
        """
        if not self.pwd_manager.verify_password(old_password, user.hashed_password):
            return False
        
        user.hashed_password = self.pwd_manager.hash_password(new_password)
        user.updated_at = datetime.utcnow()
        session.flush()
        return True


class RoleBasedAccessControl:
    """Provides role-based access control (RBAC).
    
    Usage:
        rbac = RoleBasedAccessControl()
        
        # Check if user is admin
        if rbac.is_admin(user):
            ...
        
        # Check if user has permission
        if rbac.has_permission(user, "evaluate_projects"):
            ...
    """
    
    # Define permissions by role
    ROLE_PERMISSIONS = {
        UserRole.ADMIN: {
            "view_events",
            "create_events",
            "delete_events",
            "view_projects",
            "create_projects",
            "delete_projects",
            "evaluate_projects",
            "publish_knowledge",
            "approve_knowledge",
            "manage_users",
            "view_metrics",
            "modify_settings"
        },
        UserRole.EVALUATOR: {
            "view_events",
            "view_projects",
            "create_projects",
            "evaluate_projects",
            "publish_knowledge",
            "view_metrics"
        },
        UserRole.VIEWER: {
            "view_events",
            "view_projects",
            "view_metrics"
        }
    }
    
    def has_permission(self, user: User, permission: str) -> bool:
        """Check if user has specific permission.
        
        Args:
            user: User object
            permission: Permission string (e.g., "evaluate_projects")
            
        Returns:
            True if user has permission, False otherwise
        """
        permissions = self.ROLE_PERMISSIONS.get(user.role, set())
        return permission in permissions
    
    def is_admin(self, user: User) -> bool:
        """Check if user is admin.
        
        Args:
            user: User object
            
        Returns:
            True if user is admin, False otherwise
        """
        return user.role == UserRole.ADMIN
    
    def is_evaluator(self, user: User) -> bool:
        """Check if user is evaluator or admin.
        
        Args:
            user: User object
            
        Returns:
            True if user is evaluator or admin, False otherwise
        """
        return user.role in [UserRole.EVALUATOR, UserRole.ADMIN]
    
    def require_permission(self, permission: str):
        """Decorator for route-level permission checking.
        
        Usage:
            @app.get("/evaluate")
            @rbac.require_permission("evaluate_projects")
            async def evaluate(user: User = Depends(get_current_user)):
                ...
        
        Args:
            permission: Required permission string
            
        Returns:
            Decorator function
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                user = kwargs.get("current_user")
                if not user:
                    raise PermissionError("User not authenticated")
                
                rbac = RoleBasedAccessControl()
                if not rbac.has_permission(user, permission):
                    raise PermissionError(f"User lacks permission: {permission}")
                
                return func(*args, **kwargs)
            return wrapper
        return decorator
