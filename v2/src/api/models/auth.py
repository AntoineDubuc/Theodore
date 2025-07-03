#!/usr/bin/env python3
"""
Theodore v2 API Authentication Models

Pydantic models for authentication and authorization.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration"""
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"
    API_CLIENT = "api_client"


class TokenType(str, Enum):
    """Token type enumeration"""
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"


class LoginRequest(BaseModel):
    """Login request model"""
    
    username: str = Field(..., min_length=1, max_length=100, description="Username or email")
    password: str = Field(..., min_length=1, description="User password")
    remember_me: Optional[bool] = Field(False, description="Extended session duration")
    
    class Config:
        schema_extra = {
            "example": {
                "username": "john.doe@example.com",
                "password": "secure_password123",
                "remember_me": True
            }
        }


class LoginResponse(BaseModel):
    """Login response model"""
    
    access_token: str = Field(..., description="Access token for API authentication")
    refresh_token: str = Field(..., description="Refresh token for token renewal")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")
    user: "UserProfile" = Field(..., description="User profile information")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "user_id": "usr_123456",
                    "username": "john.doe",
                    "email": "john.doe@example.com",
                    "role": "user"
                }
            }
        }


class TokenResponse(BaseModel):
    """Token response model"""
    
    access_token: str = Field(..., description="New access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    
    refresh_token: str = Field(..., description="Valid refresh token")
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            }
        }


class UserProfile(BaseModel):
    """User profile model"""
    
    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username")
    email: Optional[EmailStr] = Field(None, description="User email address")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(True, description="Whether user account is active")
    is_verified: bool = Field(False, description="Whether user email is verified")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    # Preferences and settings
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    api_quota: Optional[Dict[str, int]] = Field(None, description="API usage quotas")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "usr_123456",
                "username": "john.doe",
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "role": "user",
                "is_active": True,
                "is_verified": True,
                "created_at": "2025-01-01T00:00:00Z",
                "last_login": "2025-01-02T10:30:00Z",
                "preferences": {
                    "theme": "dark",
                    "notifications": True,
                    "default_output_format": "json"
                },
                "api_quota": {
                    "daily_requests": 1000,
                    "concurrent_jobs": 5
                }
            }
        }


class CreateUserRequest(BaseModel):
    """Create user request model"""
    
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password")
    first_name: Optional[str] = Field(None, max_length=50, description="First name")
    last_name: Optional[str] = Field(None, max_length=50, description="Last name")
    role: Optional[UserRole] = Field(UserRole.USER, description="User role")
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        if not v.replace('_', '').replace('-', '').replace('.', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, underscores, and periods')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one uppercase, lowercase, and number
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('Password must contain uppercase, lowercase, and numeric characters')
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "username": "john.doe",
                "email": "john.doe@example.com",
                "password": "SecurePass123",
                "first_name": "John",
                "last_name": "Doe",
                "role": "user"
            }
        }


class UpdateUserRequest(BaseModel):
    """Update user request model"""
    
    first_name: Optional[str] = Field(None, max_length=50, description="First name")
    last_name: Optional[str] = Field(None, max_length=50, description="Last name")
    email: Optional[EmailStr] = Field(None, description="Email address")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    
    class Config:
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Smith",
                "email": "john.smith@example.com",
                "preferences": {
                    "theme": "light",
                    "notifications": False
                }
            }
        }


class ChangePasswordRequest(BaseModel):
    """Change password request model"""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('Password must contain uppercase, lowercase, and numeric characters')
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "current_password": "OldPassword123",
                "new_password": "NewSecurePass456"
            }
        }


class APIKeyRequest(BaseModel):
    """API key creation request model"""
    
    name: str = Field(..., min_length=1, max_length=100, description="API key name")
    description: Optional[str] = Field(None, max_length=500, description="API key description")
    expires_at: Optional[datetime] = Field(None, description="Expiration date (null for no expiration)")
    scopes: Optional[List[str]] = Field(None, description="API key scopes/permissions")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Production API Key",
                "description": "API key for production integrations",
                "expires_at": "2026-01-01T00:00:00Z",
                "scopes": ["research", "discovery"]
            }
        }


class APIKeyResponse(BaseModel):
    """API key response model"""
    
    key_id: str = Field(..., description="API key identifier")
    name: str = Field(..., description="API key name")
    key: str = Field(..., description="API key value (only shown once)")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    scopes: List[str] = Field(..., description="API key scopes")
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "key_id": "key_789012",
                "name": "Production API Key",
                "key": "theo_sk_live_1234567890abcdef",
                "created_at": "2025-01-02T10:30:00Z",
                "expires_at": "2026-01-01T00:00:00Z",
                "scopes": ["research", "discovery"],
                "last_used": None
            }
        }


class APIKey(BaseModel):
    """API key information model (without the key value)"""
    
    key_id: str = Field(..., description="API key identifier")
    name: str = Field(..., description="API key name")
    description: Optional[str] = Field(None, description="API key description")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    scopes: List[str] = Field(..., description="API key scopes")
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")
    is_active: bool = Field(True, description="Whether key is active")
    usage_count: int = Field(0, description="Total usage count")
    
    class Config:
        schema_extra = {
            "example": {
                "key_id": "key_789012",
                "name": "Production API Key",
                "description": "API key for production integrations",
                "created_at": "2025-01-02T10:30:00Z",
                "expires_at": "2026-01-01T00:00:00Z",
                "scopes": ["research", "discovery"],
                "last_used": "2025-01-02T10:45:00Z",
                "is_active": True,
                "usage_count": 127
            }
        }


# Forward reference resolution for UserProfile in LoginResponse
LoginResponse.model_rebuild()