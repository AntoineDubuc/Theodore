#!/usr/bin/env python3
"""
Theodore v2 API Authentication

JWT token management and authentication utilities.
"""

import os
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ...infrastructure.observability.logging import get_logger
from ..models.auth import UserProfile

logger = get_logger(__name__)

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Token payload data
        expires_delta: Token expiration time
    
    Returns:
        Encoded JWT token
    """
    
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Failed to create access token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token creation failed"
        )


def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT token
    
    Args:
        token: JWT token to verify
    
    Returns:
        Decoded token payload
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserProfile:
    """
    Get current authenticated user from JWT token
    
    Args:
        credentials: HTTP Bearer credentials
    
    Returns:
        User profile information
    
    Raises:
        HTTPException: If authentication fails
    """
    
    token = credentials.credentials
    
    # Verify token
    payload = verify_token(token)
    
    # Extract user information from token
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # In production, this would fetch user from database
    # For now, return mock user data based on token
    user_data = _get_user_from_token(payload)
    
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return UserProfile(**user_data)


def verify_api_key(api_key: str) -> Optional[UserProfile]:
    """
    Verify API key and return associated user
    
    Args:
        api_key: API key to verify
    
    Returns:
        User profile if valid, None otherwise
    """
    
    # Mock API key validation
    # In production, this would check against database
    if api_key.startswith("theo_sk_live_"):
        # Extract username from key for demo
        if "admin" in api_key:
            return UserProfile(
                user_id="usr_admin",
                username="admin",
                email="admin@theodore.ai",
                role="admin",
                is_active=True,
                is_verified=True,
                created_at=datetime.now(timezone.utc)
            )
        else:
            return UserProfile(
                user_id="usr_api",
                username="api_user",
                email="api@theodore.ai", 
                role="user",
                is_active=True,
                is_verified=True,
                created_at=datetime.now(timezone.utc)
            )
    
    return None


def _get_user_from_token(payload: dict) -> Optional[dict]:
    """
    Get user data from token payload
    
    In production, this would query the database.
    For demo, return mock data.
    """
    
    username = payload.get("sub")
    
    # Mock user data
    mock_users = {
        "admin": {
            "user_id": "usr_admin",
            "username": "admin",
            "email": "admin@theodore.ai",
            "role": "admin",
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.now(timezone.utc),
            "last_login": datetime.now(timezone.utc)
        },
        "demo": {
            "user_id": "usr_demo", 
            "username": "demo",
            "email": "demo@theodore.ai",
            "role": "user",
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.now(timezone.utc),
            "last_login": datetime.now(timezone.utc)
        }
    }
    
    return mock_users.get(username)


def create_refresh_token(user_id: str) -> str:
    """
    Create a refresh token for token renewal
    
    Args:
        user_id: User identifier
    
    Returns:
        Refresh token
    """
    
    data = {
        "sub": user_id,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=30)  # 30 day expiry
    }
    
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def verify_refresh_token(token: str) -> str:
    """
    Verify refresh token and return user ID
    
    Args:
        token: Refresh token to verify
    
    Returns:
        User ID from token
    
    Raises:
        HTTPException: If token is invalid
    """
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        return user_id
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


# Optional dependency for endpoints that support both auth and anonymous access
def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[UserProfile]:
    """
    Get current user if authenticated, None if anonymous
    
    Used for endpoints that work for both authenticated and anonymous users
    but provide different functionality based on authentication status.
    """
    
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials)
    except HTTPException:
        return None


# Role-based access control decorators
def require_admin(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
    """
    Require admin role for endpoint access
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        User profile if admin
    
    Raises:
        HTTPException: If user is not admin
    """
    
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


def require_active_user(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
    """
    Require active user account
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        User profile if active
    
    Raises:
        HTTPException: If user account is inactive
    """
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return current_user