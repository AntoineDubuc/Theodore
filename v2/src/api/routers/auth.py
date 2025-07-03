#!/usr/bin/env python3
"""
Theodore v2 Authentication API Router

FastAPI router for authentication and user management endpoints.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ...infrastructure.observability.logging import get_logger
from ...infrastructure.observability.metrics import get_metrics_collector
from ..models.auth import (
    LoginRequest, LoginResponse, TokenResponse, RefreshTokenRequest,
    UserProfile, CreateUserRequest, UpdateUserRequest, ChangePasswordRequest,
    APIKeyRequest, APIKeyResponse, APIKey
)

logger = get_logger(__name__)
metrics = get_metrics_collector()

router = APIRouter()
security = HTTPBearer()

# Mock user database for demonstration
# In production, this would be replaced with proper database integration
_mock_users = {
    "admin": {
        "user_id": "usr_admin",
        "username": "admin",
        "email": "admin@theodore.ai",
        "password_hash": "hashed_admin_password",  # In real implementation, properly hashed
        "role": "admin",
        "is_active": True,
        "is_verified": True,
        "created_at": datetime.now(timezone.utc),
        "last_login": None
    },
    "demo": {
        "user_id": "usr_demo",
        "username": "demo",
        "email": "demo@theodore.ai", 
        "password_hash": "hashed_demo_password",
        "role": "user",
        "is_active": True,
        "is_verified": True,
        "created_at": datetime.now(timezone.utc),
        "last_login": None
    }
}


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserProfile:
    """
    Get current authenticated user from JWT token
    
    This is a simplified implementation for demonstration.
    In production, this would validate JWT tokens and extract user information.
    """
    
    # Mock JWT validation - in production, use proper JWT library
    token = credentials.credentials
    
    # For demo purposes, accept "demo_token" and "admin_token"
    if token == "demo_token":
        user_data = _mock_users["demo"]
    elif token == "admin_token":
        user_data = _mock_users["admin"]
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return UserProfile(
        user_id=user_data["user_id"],
        username=user_data["username"],
        email=user_data["email"],
        role=user_data["role"],
        is_active=user_data["is_active"],
        is_verified=user_data["is_verified"],
        created_at=user_data["created_at"],
        last_login=user_data["last_login"]
    )


@router.post("/login", response_model=LoginResponse, summary="User Login")
async def login(request: LoginRequest) -> LoginResponse:
    """
    Authenticate user and return access token
    
    Validates user credentials and returns JWT access and refresh tokens.
    The access token should be included in the Authorization header
    for subsequent API requests.
    """
    
    try:
        # Find user by username or email
        user_data = None
        for user in _mock_users.values():
            if user["username"] == request.username or user["email"] == request.username:
                user_data = user
                break
        
        if not user_data:
            metrics.increment_counter("auth_login_failed", tags={"reason": "user_not_found"})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Validate password (in production, use proper password hashing)
        if not _verify_password(request.password, user_data["password_hash"]):
            metrics.increment_counter("auth_login_failed", tags={"reason": "invalid_password"})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Check if user is active
        if not user_data["is_active"]:
            metrics.increment_counter("auth_login_failed", tags={"reason": "user_inactive"})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )
        
        # Generate tokens (mock implementation)
        access_token = f"{user_data['username']}_token"
        refresh_token = f"{user_data['username']}_refresh_token"
        
        # Update last login
        user_data["last_login"] = datetime.now(timezone.utc)
        
        # Create user profile
        user_profile = UserProfile(
            user_id=user_data["user_id"],
            username=user_data["username"],
            email=user_data["email"],
            role=user_data["role"],
            is_active=user_data["is_active"],
            is_verified=user_data["is_verified"],
            created_at=user_data["created_at"],
            last_login=user_data["last_login"]
        )
        
        logger.info(f"User logged in: {user_data['username']}")
        metrics.increment_counter("auth_login_success")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=3600,  # 1 hour
            user=user_profile
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}", exc_info=True)
        metrics.increment_counter("auth_login_error")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


@router.post("/logout", summary="User Logout")
async def logout(current_user: UserProfile = Depends(get_current_user)):
    """
    Logout user and invalidate tokens
    
    Invalidates the current access token and refresh token.
    The client should discard the tokens after calling this endpoint.
    """
    
    try:
        # In production, add tokens to blacklist or invalidate in token store
        logger.info(f"User logged out: {current_user.username}")
        metrics.increment_counter("auth_logout_success")
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout failed: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/refresh", response_model=TokenResponse, summary="Refresh Access Token")
async def refresh_token(request: RefreshTokenRequest) -> TokenResponse:
    """
    Refresh access token using refresh token
    
    Generates a new access token using a valid refresh token.
    The old access token is invalidated.
    """
    
    try:
        # Validate refresh token (mock implementation)
        username = None
        for user in _mock_users.values():
            if request.refresh_token == f"{user['username']}_refresh_token":
                username = user["username"]
                break
        
        if not username:
            metrics.increment_counter("auth_refresh_failed", tags={"reason": "invalid_token"})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Generate new access token
        new_access_token = f"{username}_token"
        
        logger.info(f"Token refreshed for user: {username}")
        metrics.increment_counter("auth_refresh_success")
        
        return TokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=3600
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}", exc_info=True)
        metrics.increment_counter("auth_refresh_error")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.get("/profile", response_model=UserProfile, summary="Get User Profile")
async def get_profile(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
    """
    Get current user profile information
    
    Returns detailed information about the currently authenticated user.
    """
    
    return current_user


@router.put("/profile", response_model=UserProfile, summary="Update User Profile")
async def update_profile(
    updates: UpdateUserRequest,
    current_user: UserProfile = Depends(get_current_user)
) -> UserProfile:
    """
    Update user profile information
    
    Allows users to update their profile information such as
    name, email, and preferences.
    """
    
    try:
        # Find user data
        user_data = _mock_users.get(current_user.username)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields
        if updates.first_name is not None:
            # In production, store in database
            pass
        if updates.last_name is not None:
            # In production, store in database
            pass
        if updates.email is not None:
            user_data["email"] = updates.email
        if updates.preferences is not None:
            # In production, store preferences
            pass
        
        logger.info(f"Profile updated for user: {current_user.username}")
        metrics.increment_counter("auth_profile_updated")
        
        # Return updated profile
        return UserProfile(
            user_id=user_data["user_id"],
            username=user_data["username"],
            email=user_data["email"],
            role=user_data["role"],
            is_active=user_data["is_active"],
            is_verified=user_data["is_verified"],
            created_at=user_data["created_at"],
            last_login=user_data["last_login"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update failed: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.post("/change-password", summary="Change Password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Change user password
    
    Allows users to change their password by providing
    their current password and a new password.
    """
    
    try:
        # Find user data
        user_data = _mock_users.get(current_user.username)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not _verify_password(request.current_password, user_data["password_hash"]):
            metrics.increment_counter("auth_password_change_failed", tags={"reason": "invalid_current"})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid current password"
            )
        
        # Update password (in production, properly hash the new password)
        user_data["password_hash"] = f"hashed_{request.new_password}"
        
        logger.info(f"Password changed for user: {current_user.username}")
        metrics.increment_counter("auth_password_changed")
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change failed: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post("/api-keys", response_model=APIKeyResponse, summary="Create API Key")
async def create_api_key(
    request: APIKeyRequest,
    current_user: UserProfile = Depends(get_current_user)
) -> APIKeyResponse:
    """
    Create a new API key
    
    Generates a new API key for programmatic access.
    The key is only shown once and cannot be retrieved later.
    """
    
    try:
        # Generate API key (in production, use cryptographically secure generation)
        key_id = f"key_{current_user.username}_{int(datetime.now().timestamp())}"
        api_key = f"theo_sk_live_{key_id}"
        
        # Store API key (in production, store in database with proper hashing)
        
        logger.info(f"API key created for user: {current_user.username}")
        metrics.increment_counter("auth_api_key_created")
        
        return APIKeyResponse(
            key_id=key_id,
            name=request.name,
            key=api_key,
            created_at=datetime.now(timezone.utc),
            expires_at=request.expires_at,
            scopes=request.scopes or ["research", "discovery"],
            last_used=None
        )
        
    except Exception as e:
        logger.error(f"API key creation failed: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key creation failed"
        )


def _verify_password(password: str, password_hash: str) -> bool:
    """
    Verify password against hash
    
    Mock implementation - in production, use proper password hashing
    like bcrypt, scrypt, or argon2.
    """
    
    # Mock verification - in production, use proper password verification
    return password_hash == f"hashed_{password}"