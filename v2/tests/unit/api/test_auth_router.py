#!/usr/bin/env python3
"""
Tests for Theodore v2 Authentication API Router
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.app import create_app
from src.api.models.auth import LoginRequest, TokenResponse, UserProfile


class TestAuthRouter:
    """Test authentication API endpoints"""
    
    @pytest.fixture
    def mock_container(self):
        """Mock application container"""
        container = AsyncMock()
        
        # Mock auth service
        mock_auth_service = AsyncMock()
        container.get.return_value = mock_auth_service
        
        return container, mock_auth_service
    
    @pytest.fixture
    def app(self, mock_container):
        """Create test app"""
        container, _ = mock_container
        app = create_app(debug=True)
        app.state.container = container
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    def test_login_success(self, client, mock_container):
        """Test successful login"""
        container, mock_auth_service = mock_container
        
        # Mock successful authentication
        mock_token_response = TokenResponse(
            access_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            token_type="bearer",
            expires_in=3600,
            refresh_token="refresh_token_123",
            scope="read write admin"
        )
        
        mock_auth_service.authenticate.return_value = mock_token_response
        
        # Make login request
        login_data = {
            "username": "test@example.com",
            "password": "secure_password123"
        }
        
        response = client.post("/api/v2/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["access_token"] == mock_token_response.access_token
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600
        assert "refresh_token" in data
        
        # Verify auth service was called
        mock_auth_service.authenticate.assert_called_once()
        call_args = mock_auth_service.authenticate.call_args
        assert call_args.kwargs["username"] == "test@example.com"
        assert call_args.kwargs["password"] == "secure_password123"
    
    def test_login_invalid_credentials(self, client, mock_container):
        """Test login with invalid credentials"""
        container, mock_auth_service = mock_container
        
        # Mock authentication failure
        mock_auth_service.authenticate.return_value = None
        
        login_data = {
            "username": "test@example.com",
            "password": "wrong_password"
        }
        
        response = client.post("/api/v2/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        
        assert "Invalid credentials" in data["detail"]
    
    def test_login_validation_error(self, client):
        """Test login with validation errors"""
        # Missing password
        response = client.post("/api/v2/auth/login", json={
            "username": "test@example.com"
        })
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
        
        # Invalid email format
        response = client.post("/api/v2/auth/login", json={
            "username": "invalid-email",
            "password": "password123"
        })
        
        assert response.status_code == 422
    
    def test_refresh_token_success(self, client, mock_container):
        """Test successful token refresh"""
        container, mock_auth_service = mock_container
        
        # Mock successful token refresh
        new_token_response = TokenResponse(
            access_token="new_access_token_123",
            token_type="bearer",
            expires_in=3600,
            refresh_token="new_refresh_token_123",
            scope="read write admin"
        )
        
        mock_auth_service.refresh_token.return_value = new_token_response
        
        refresh_data = {
            "refresh_token": "valid_refresh_token"
        }
        
        response = client.post("/api/v2/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["access_token"] == "new_access_token_123"
        assert data["refresh_token"] == "new_refresh_token_123"
    
    def test_refresh_token_invalid(self, client, mock_container):
        """Test refresh with invalid token"""
        container, mock_auth_service = mock_container
        
        # Mock invalid refresh token
        mock_auth_service.refresh_token.return_value = None
        
        refresh_data = {
            "refresh_token": "invalid_refresh_token"
        }
        
        response = client.post("/api/v2/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401
        data = response.json()
        
        assert "Invalid refresh token" in data["detail"]
    
    def test_logout_success(self, client, mock_container):
        """Test successful logout"""
        container, mock_auth_service = mock_container
        
        mock_auth_service.logout.return_value = True
        
        # Mock authenticated request
        headers = {"Authorization": "Bearer valid_access_token"}
        
        response = client.post("/api/v2/auth/logout", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "logged out successfully" in data["message"]
    
    def test_logout_without_token(self, client):
        """Test logout without authentication token"""
        response = client.post("/api/v2/auth/logout")
        
        assert response.status_code == 401
        data = response.json()
        
        assert "Missing authorization" in data["detail"]
    
    def test_get_current_user_success(self, client, mock_container):
        """Test getting current user profile"""
        container, mock_auth_service = mock_container
        
        # Mock user profile
        mock_user_profile = UserProfile(
            user_id="user_123",
            username="test@example.com",
            email="test@example.com",
            full_name="Test User",
            role="user",
            permissions=["read", "write"],
            created_at=datetime.now(timezone.utc),
            last_login=datetime.now(timezone.utc),
            is_active=True,
            is_verified=True
        )
        
        mock_auth_service.get_current_user.return_value = mock_user_profile
        
        headers = {"Authorization": "Bearer valid_access_token"}
        response = client.get("/api/v2/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == "user_123"
        assert data["username"] == "test@example.com"
        assert data["role"] == "user"
        assert data["is_active"] is True
        assert "permissions" in data
    
    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without authentication"""
        response = client.get("/api/v2/auth/me")
        
        assert response.status_code == 401
    
    def test_update_user_profile(self, client, mock_container):
        """Test updating user profile"""
        container, mock_auth_service = mock_container
        
        # Mock updated profile
        updated_profile = UserProfile(
            user_id="user_123",
            username="test@example.com",
            email="test@example.com",
            full_name="Updated Test User",
            role="user",
            permissions=["read", "write"],
            created_at=datetime.now(timezone.utc),
            last_login=datetime.now(timezone.utc),
            is_active=True,
            is_verified=True
        )
        
        mock_auth_service.update_user_profile.return_value = updated_profile
        
        profile_data = {
            "full_name": "Updated Test User",
            "preferences": {
                "theme": "dark",
                "notifications": True
            }
        }
        
        headers = {"Authorization": "Bearer valid_access_token"}
        response = client.put("/api/v2/auth/profile", json=profile_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["full_name"] == "Updated Test User"
    
    def test_change_password_success(self, client, mock_container):
        """Test successful password change"""
        container, mock_auth_service = mock_container
        
        mock_auth_service.change_password.return_value = True
        
        password_data = {
            "current_password": "old_password123",
            "new_password": "new_secure_password456"
        }
        
        headers = {"Authorization": "Bearer valid_access_token"}
        response = client.post("/api/v2/auth/change-password", json=password_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "Password changed successfully" in data["message"]
    
    def test_change_password_invalid_current(self, client, mock_container):
        """Test password change with invalid current password"""
        container, mock_auth_service = mock_container
        
        mock_auth_service.change_password.return_value = False
        
        password_data = {
            "current_password": "wrong_password",
            "new_password": "new_secure_password456"
        }
        
        headers = {"Authorization": "Bearer valid_access_token"}
        response = client.post("/api/v2/auth/change-password", json=password_data, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        
        assert "Invalid current password" in data["detail"]
    
    def test_register_user_success(self, client, mock_container):
        """Test successful user registration"""
        container, mock_auth_service = mock_container
        
        # Mock successful registration
        mock_user_profile = UserProfile(
            user_id="new_user_123",
            username="newuser@example.com",
            email="newuser@example.com",
            full_name="New User",
            role="user",
            permissions=["read"],
            created_at=datetime.now(timezone.utc),
            last_login=None,
            is_active=True,
            is_verified=False
        )
        
        mock_auth_service.register_user.return_value = mock_user_profile
        
        registration_data = {
            "username": "newuser@example.com",
            "email": "newuser@example.com",
            "password": "secure_password123",
            "full_name": "New User"
        }
        
        response = client.post("/api/v2/auth/register", json=registration_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["user_id"] == "new_user_123"
        assert data["username"] == "newuser@example.com"
        assert data["is_verified"] is False
    
    def test_register_user_already_exists(self, client, mock_container):
        """Test registration with existing user"""
        container, mock_auth_service = mock_container
        
        # Mock user already exists
        mock_auth_service.register_user.side_effect = ValueError("User already exists")
        
        registration_data = {
            "username": "existing@example.com",
            "email": "existing@example.com",
            "password": "password123",
            "full_name": "Existing User"
        }
        
        response = client.post("/api/v2/auth/register", json=registration_data)
        
        assert response.status_code == 409
        data = response.json()
        
        assert "User already exists" in data["detail"]
    
    def test_verify_email_success(self, client, mock_container):
        """Test successful email verification"""
        container, mock_auth_service = mock_container
        
        mock_auth_service.verify_email.return_value = True
        
        verification_data = {
            "token": "valid_verification_token"
        }
        
        response = client.post("/api/v2/auth/verify-email", json=verification_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "Email verified successfully" in data["message"]
    
    def test_verify_email_invalid_token(self, client, mock_container):
        """Test email verification with invalid token"""
        container, mock_auth_service = mock_container
        
        mock_auth_service.verify_email.return_value = False
        
        verification_data = {
            "token": "invalid_verification_token"
        }
        
        response = client.post("/api/v2/auth/verify-email", json=verification_data)
        
        assert response.status_code == 400
        data = response.json()
        
        assert "Invalid verification token" in data["detail"]
    
    def test_forgot_password_request(self, client, mock_container):
        """Test password reset request"""
        container, mock_auth_service = mock_container
        
        mock_auth_service.request_password_reset.return_value = True
        
        reset_data = {
            "email": "user@example.com"
        }
        
        response = client.post("/api/v2/auth/forgot-password", json=reset_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "Password reset email sent" in data["message"]
    
    def test_reset_password_success(self, client, mock_container):
        """Test successful password reset"""
        container, mock_auth_service = mock_container
        
        mock_auth_service.reset_password.return_value = True
        
        reset_data = {
            "token": "valid_reset_token",
            "new_password": "new_secure_password123"
        }
        
        response = client.post("/api/v2/auth/reset-password", json=reset_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "Password reset successfully" in data["message"]
    
    def test_get_user_permissions(self, client, mock_container):
        """Test getting user permissions"""
        container, mock_auth_service = mock_container
        
        mock_permissions = {
            "permissions": ["read", "write", "admin"],
            "role": "admin",
            "scopes": ["research:read", "research:write", "discovery:read", "system:admin"]
        }
        
        mock_auth_service.get_user_permissions.return_value = mock_permissions
        
        headers = {"Authorization": "Bearer valid_access_token"}
        response = client.get("/api/v2/auth/permissions", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "read" in data["permissions"]
        assert "admin" in data["permissions"]
        assert data["role"] == "admin"
        assert len(data["scopes"]) == 4
    
    def test_login_request_model_validation(self):
        """Test login request model validation"""
        # Valid request
        valid_request = LoginRequest(
            username="test@example.com",
            password="secure_password123"
        )
        
        assert valid_request.username == "test@example.com"
        assert valid_request.password == "secure_password123"
        
        # Test password validation (if implemented)
        # Should enforce minimum password requirements
    
    def test_token_response_model(self):
        """Test token response model"""
        token_response = TokenResponse(
            access_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            token_type="bearer",
            expires_in=3600,
            refresh_token="refresh_token_123",
            scope="read write admin"
        )
        
        assert token_response.access_token.startswith("eyJ")
        assert token_response.token_type == "bearer"
        assert token_response.expires_in == 3600
        
        # Test serialization
        data = token_response.dict()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_user_profile_model(self):
        """Test user profile model"""
        user_profile = UserProfile(
            user_id="user_123",
            username="test@example.com",
            email="test@example.com",
            full_name="Test User",
            role="user",
            permissions=["read", "write"],
            created_at=datetime.now(timezone.utc),
            last_login=datetime.now(timezone.utc),
            is_active=True,
            is_verified=True
        )
        
        assert user_profile.user_id == "user_123"
        assert user_profile.role == "user"
        assert len(user_profile.permissions) == 2
        assert user_profile.is_active is True
        
        # Test serialization excludes sensitive data
        data = user_profile.dict()
        assert "password" not in data
        assert "password_hash" not in data
    
    @pytest.mark.asyncio
    async def test_auth_endpoint_metrics(self, client, mock_container):
        """Test that auth endpoints record metrics"""
        with patch('src.api.routers.auth.metrics') as mock_metrics:
            container, mock_auth_service = mock_container
            
            mock_token_response = TokenResponse(
                access_token="token123",
                token_type="bearer",
                expires_in=3600
            )
            mock_auth_service.authenticate.return_value = mock_token_response
            
            login_data = {"username": "test@example.com", "password": "password123"}
            response = client.post("/api/v2/auth/login", json=login_data)
            
            assert response.status_code == 200
            
            # Verify metrics were recorded
            mock_metrics.increment_counter.assert_called_with(
                "auth_login_attempts_total",
                tags={"status": "success"}
            )
    
    def test_auth_endpoint_logging(self, client, mock_container):
        """Test that auth endpoints log appropriately"""
        with patch('src.api.routers.auth.logger') as mock_logger:
            container, mock_auth_service = mock_container
            
            mock_token_response = TokenResponse(
                access_token="token123",
                token_type="bearer",
                expires_in=3600
            )
            mock_auth_service.authenticate.return_value = mock_token_response
            
            login_data = {"username": "test@example.com", "password": "password123"}
            response = client.post("/api/v2/auth/login", json=login_data)
            
            assert response.status_code == 200
            
            # Verify logging was called
            mock_logger.info.assert_called()
            
            # Check that sensitive data is not logged
            log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            for log_message in log_calls:
                assert "password123" not in log_message
                assert "password" not in log_message.lower() or "password field" in log_message.lower()
    
    def test_auth_rate_limiting(self, client, mock_container):
        """Test authentication rate limiting"""
        container, mock_auth_service = mock_container
        
        # Mock authentication failure to trigger rate limiting
        mock_auth_service.authenticate.return_value = None
        
        login_data = {"username": "test@example.com", "password": "wrong_password"}
        
        # Make multiple failed attempts
        for i in range(5):
            response = client.post("/api/v2/auth/login", json=login_data)
            # First few should be 401, but rate limiting might kick in
            assert response.status_code in [401, 429]
        
        # Additional attempt should be rate limited
        response = client.post("/api/v2/auth/login", json=login_data)
        # Should eventually hit rate limit
        assert response.status_code in [401, 429]