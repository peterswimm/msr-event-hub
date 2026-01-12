"""Integration tests for Phase E1.2: Authentication Layer.

Tests cover:
- User registration and validation
- Password hashing and verification
- JWT token generation and validation
- User authentication
- Token refresh
- Role-based access control
- Protected routes
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from infra.models import Base
from infra.authentication import (
    PasswordManager, TokenManager, AuthenticationService, User,
    UserRole, RoleBasedAccessControl
)


# Test database configuration (in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def test_db():
    """Create test database and initialize schema."""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def pwd_manager():
    """Create PasswordManager instance."""
    return PasswordManager()


@pytest.fixture
def token_manager():
    """Create TokenManager instance."""
    return TokenManager(
        secret_key="test-secret-key",
        access_token_expire_minutes=30,
        refresh_token_expire_days=7
    )


@pytest.fixture
def auth_service(pwd_manager, token_manager):
    """Create AuthenticationService instance."""
    return AuthenticationService(pwd_manager, token_manager)


class TestPasswordManager:
    """Tests for PasswordManager."""
    
    def test_hash_password(self, pwd_manager):
        """Test password hashing."""
        password = "my-secure-password"
        hashed = pwd_manager.hash_password(password)
        
        # Hash should be different from password
        assert hashed != password
        # Hash should be bcrypt format
        assert hashed.startswith("$2b$")
    
    def test_verify_correct_password(self, pwd_manager):
        """Test verifying correct password."""
        password = "my-secure-password"
        hashed = pwd_manager.hash_password(password)
        
        assert pwd_manager.verify_password(password, hashed) is True
    
    def test_verify_incorrect_password(self, pwd_manager):
        """Test verifying incorrect password."""
        password = "my-secure-password"
        hashed = pwd_manager.hash_password(password)
        
        assert pwd_manager.verify_password("wrong-password", hashed) is False
    
    def test_different_hashes_for_same_password(self, pwd_manager):
        """Test that same password produces different hashes (salt)."""
        password = "my-secure-password"
        hash1 = pwd_manager.hash_password(password)
        hash2 = pwd_manager.hash_password(password)
        
        # Hashes should be different due to random salt
        assert hash1 != hash2
        # But both should verify correctly
        assert pwd_manager.verify_password(password, hash1) is True
        assert pwd_manager.verify_password(password, hash2) is True


class TestTokenManager:
    """Tests for TokenManager."""
    
    def test_create_access_token(self, token_manager):
        """Test access token creation."""
        data = {"sub": "user-123", "username": "testuser"}
        token = token_manager.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        # JWT tokens have 3 parts separated by dots
        assert token.count(".") == 2
    
    def test_verify_valid_token(self, token_manager):
        """Test verifying valid token."""
        data = {"sub": "user-123", "username": "testuser"}
        token = token_manager.create_access_token(data)
        
        payload = token_manager.verify_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["username"] == "testuser"
    
    def test_verify_invalid_token(self, token_manager):
        """Test verifying invalid token."""
        invalid_token = "invalid.token.here"
        payload = token_manager.verify_token(invalid_token)
        
        assert payload is None
    
    def test_verify_expired_token(self, token_manager):
        """Test verifying expired token."""
        data = {"sub": "user-123"}
        # Create token with past expiration
        to_encode = data.copy()
        to_encode["exp"] = datetime.utcnow() - timedelta(hours=1)
        
        from jose import jwt
        expired_token = jwt.encode(
            to_encode, token_manager.secret_key, algorithm=token_manager.algorithm
        )
        
        payload = token_manager.verify_token(expired_token)
        assert payload is None
    
    def test_create_refresh_token(self, token_manager):
        """Test refresh token creation."""
        user_id = "user-123"
        token = token_manager.create_refresh_token(user_id)
        
        payload = token_manager.verify_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"


class TestAuthenticationService:
    """Tests for AuthenticationService."""
    
    def test_register_user(self, auth_service, test_db):
        """Test user registration."""
        user = auth_service.register_user(
            test_db,
            username="testuser",
            email="test@example.com",
            password="secure-password"
        )
        test_db.commit()
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.VIEWER
        assert user.is_active is True
        # Password should be hashed, not plain text
        assert user.hashed_password != "secure-password"
    
    def test_register_duplicate_username(self, auth_service, test_db):
        """Test registering with duplicate username."""
        auth_service.register_user(
            test_db,
            username="testuser",
            email="test@example.com",
            password="secure-password"
        )
        test_db.commit()
        
        with pytest.raises(ValueError):
            auth_service.register_user(
                test_db,
                username="testuser",
                email="another@example.com",
                password="secure-password"
            )
    
    def test_register_duplicate_email(self, auth_service, test_db):
        """Test registering with duplicate email."""
        auth_service.register_user(
            test_db,
            username="testuser",
            email="test@example.com",
            password="secure-password"
        )
        test_db.commit()
        
        with pytest.raises(ValueError):
            auth_service.register_user(
                test_db,
                username="anotheruser",
                email="test@example.com",
                password="secure-password"
            )
    
    def test_authenticate_success(self, auth_service, test_db):
        """Test successful authentication."""
        auth_service.register_user(
            test_db,
            username="testuser",
            email="test@example.com",
            password="secure-password"
        )
        test_db.commit()
        
        user = auth_service.authenticate_user(
            test_db, "testuser", "secure-password"
        )
        
        assert user is not None
        assert user.username == "testuser"
        assert user.last_login_at is not None
    
    def test_authenticate_wrong_password(self, auth_service, test_db):
        """Test authentication with wrong password."""
        auth_service.register_user(
            test_db,
            username="testuser",
            email="test@example.com",
            password="secure-password"
        )
        test_db.commit()
        
        user = auth_service.authenticate_user(
            test_db, "testuser", "wrong-password"
        )
        
        assert user is None
    
    def test_authenticate_nonexistent_user(self, auth_service, test_db):
        """Test authentication for nonexistent user."""
        user = auth_service.authenticate_user(
            test_db, "nonexistent", "password"
        )
        
        assert user is None
    
    def test_authenticate_inactive_user(self, auth_service, test_db):
        """Test authentication for inactive user."""
        user = auth_service.register_user(
            test_db,
            username="testuser",
            email="test@example.com",
            password="secure-password"
        )
        user.is_active = False
        test_db.commit()
        
        authenticated = auth_service.authenticate_user(
            test_db, "testuser", "secure-password"
        )
        
        assert authenticated is None
    
    def test_create_token_pair(self, auth_service, test_db):
        """Test creating access and refresh tokens."""
        user = auth_service.register_user(
            test_db,
            username="testuser",
            email="test@example.com",
            password="secure-password",
            role=UserRole.ADMIN
        )
        test_db.commit()
        
        tokens = auth_service.create_token_pair(user)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        
        # Verify token contents
        access_payload = auth_service.token_manager.verify_token(tokens["access_token"])
        assert access_payload["sub"] == user.id
        assert access_payload["username"] == "testuser"
        assert access_payload["role"] == "admin"
    
    def test_get_current_user(self, auth_service, test_db):
        """Test getting current user from token."""
        user = auth_service.register_user(
            test_db,
            username="testuser",
            email="test@example.com",
            password="secure-password"
        )
        test_db.commit()
        
        token = auth_service.token_manager.create_access_token(
            {"sub": user.id, "username": "testuser"}
        )
        
        current = auth_service.get_current_user(test_db, token)
        assert current is not None
        assert current.id == user.id
        assert current.username == "testuser"
    
    def test_get_current_user_invalid_token(self, auth_service, test_db):
        """Test getting current user with invalid token."""
        current = auth_service.get_current_user(test_db, "invalid.token.here")
        assert current is None
    
    def test_refresh_access_token(self, auth_service, test_db):
        """Test refreshing access token."""
        user = auth_service.register_user(
            test_db,
            username="testuser",
            email="test@example.com",
            password="secure-password"
        )
        test_db.commit()
        
        refresh_token = auth_service.token_manager.create_refresh_token(user.id)
        new_access_token = auth_service.refresh_access_token(test_db, refresh_token)
        
        assert new_access_token is not None
        
        # Verify new token is valid
        payload = auth_service.token_manager.verify_token(new_access_token)
        assert payload["sub"] == user.id
    
    def test_refresh_with_invalid_token(self, auth_service, test_db):
        """Test refreshing with invalid token."""
        new_token = auth_service.refresh_access_token(
            test_db, "invalid.refresh.token"
        )
        assert new_token is None
    
    def test_change_password(self, auth_service, test_db):
        """Test changing password."""
        user = auth_service.register_user(
            test_db,
            username="testuser",
            email="test@example.com",
            password="old-password"
        )
        test_db.commit()
        
        success = auth_service.change_password(
            test_db, user, "old-password", "new-password"
        )
        test_db.commit()
        
        assert success is True
        
        # Verify old password no longer works
        authenticated = auth_service.authenticate_user(
            test_db, "testuser", "old-password"
        )
        assert authenticated is None
        
        # Verify new password works
        authenticated = auth_service.authenticate_user(
            test_db, "testuser", "new-password"
        )
        assert authenticated is not None
    
    def test_change_password_wrong_old(self, auth_service, test_db):
        """Test changing password with wrong old password."""
        user = auth_service.register_user(
            test_db,
            username="testuser",
            email="test@example.com",
            password="correct-password"
        )
        test_db.commit()
        
        success = auth_service.change_password(
            test_db, user, "wrong-password", "new-password"
        )
        
        assert success is False
        
        # Verify old password still works
        authenticated = auth_service.authenticate_user(
            test_db, "testuser", "correct-password"
        )
        assert authenticated is not None


class TestRoleBasedAccessControl:
    """Tests for role-based access control."""
    
    def test_admin_permissions(self):
        """Test admin has all permissions."""
        rbac = RoleBasedAccessControl()
        user = User(
            username="admin",
            email="admin@example.com",
            hashed_password="hashed",
            role=UserRole.ADMIN
        )
        
        assert rbac.has_permission(user, "evaluate_projects") is True
        assert rbac.has_permission(user, "approve_knowledge") is True
        assert rbac.has_permission(user, "manage_users") is True
        assert rbac.is_admin(user) is True
    
    def test_evaluator_permissions(self):
        """Test evaluator has limited permissions."""
        rbac = RoleBasedAccessControl()
        user = User(
            username="evaluator",
            email="eval@example.com",
            hashed_password="hashed",
            role=UserRole.EVALUATOR
        )
        
        assert rbac.has_permission(user, "evaluate_projects") is True
        assert rbac.has_permission(user, "view_projects") is True
        assert rbac.has_permission(user, "manage_users") is False
        assert rbac.is_evaluator(user) is True
    
    def test_viewer_permissions(self):
        """Test viewer has minimal permissions."""
        rbac = RoleBasedAccessControl()
        user = User(
            username="viewer",
            email="view@example.com",
            hashed_password="hashed",
            role=UserRole.VIEWER
        )
        
        assert rbac.has_permission(user, "view_projects") is True
        assert rbac.has_permission(user, "evaluate_projects") is False
        assert rbac.has_permission(user, "manage_users") is False
        assert rbac.is_evaluator(user) is False


class TestAuthenticationIntegration:
    """Integration tests for complete authentication flow."""
    
    def test_registration_login_token_flow(self, auth_service, test_db):
        """Test complete registration → login → token flow."""
        # Register user
        user = auth_service.register_user(
            test_db,
            username="johndoe",
            email="john@example.com",
            password="secure-password123",
            role=UserRole.EVALUATOR
        )
        test_db.commit()
        
        # Login
        authenticated = auth_service.authenticate_user(
            test_db, "johndoe", "secure-password123"
        )
        assert authenticated is not None
        
        # Create tokens
        tokens = auth_service.create_token_pair(authenticated)
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        
        # Use token to get current user
        current = auth_service.get_current_user(test_db, tokens["access_token"])
        assert current.username == "johndoe"
        
        # Refresh token
        new_token = auth_service.refresh_access_token(test_db, tokens["refresh_token"])
        assert new_token is not None
        
        # Use new token
        current_again = auth_service.get_current_user(test_db, new_token)
        assert current_again.username == "johndoe"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
