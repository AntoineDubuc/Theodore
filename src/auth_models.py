"""
User Authentication Models for Theodore
Handles user registration, login, and session management
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import hashlib

class User(BaseModel):
    """User model for authentication"""
    id: str = Field(default_factory=lambda: secrets.token_urlsafe(16))
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password_hash: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v.lower()
    
    def set_password(self, password: str) -> None:
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_id(self) -> str:
        """Required by Flask-Login"""
        return self.id
    
    @property
    def is_authenticated(self) -> bool:
        """Required by Flask-Login"""
        return True
    
    @property
    def is_anonymous(self) -> bool:
        """Required by Flask-Login"""
        return False

class UserRegistration(BaseModel):
    """User registration request model"""
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('Password must contain uppercase, lowercase, and numbers')
        
        return v

class UserLogin(BaseModel):
    """User login request model"""
    email: EmailStr
    password: str
    remember_me: bool = False

class UserSession(BaseModel):
    """User session information"""
    user_id: str
    email: str
    username: str
    created_at: datetime
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for session storage"""
        return {
            'user_id': self.user_id,
            'email': self.email,
            'username': self.username,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserSession':
        """Create from dictionary"""
        return cls(
            user_id=data['user_id'],
            email=data['email'],
            username=data['username'],
            created_at=datetime.fromisoformat(data['created_at']),
            last_activity=datetime.fromisoformat(data['last_activity'])
        )

class AuthError(Exception):
    """Custom authentication error"""
    def __init__(self, message: str, code: str = 'AUTH_ERROR'):
        self.message = message
        self.code = code
        super().__init__(self.message)

class UserNotFoundError(AuthError):
    """User not found error"""
    def __init__(self, identifier: str):
        super().__init__(f"User not found: {identifier}", 'USER_NOT_FOUND')

class InvalidCredentialsError(AuthError):
    """Invalid credentials error"""
    def __init__(self):
        super().__init__("Invalid email or password", 'INVALID_CREDENTIALS')

class UserAlreadyExistsError(AuthError):
    """User already exists error"""
    def __init__(self, identifier: str):
        super().__init__(f"User already exists: {identifier}", 'USER_EXISTS')