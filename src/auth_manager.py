"""
Flask-Login Integration for Theodore Authentication
Handles user session management and login integration
"""

import os
from flask_login import LoginManager, UserMixin
from auth_service import AuthService
from auth_models import User, UserSession

class TheodoreUser(UserMixin):
    """Flask-Login compatible user class"""
    
    def __init__(self, user: User):
        self.user = user
    
    def get_id(self):
        """Required by Flask-Login"""
        return self.user.id
    
    @property
    def is_authenticated(self):
        """Required by Flask-Login"""
        return True
    
    @property
    def is_active(self):
        """Required by Flask-Login"""
        return self.user.is_active
    
    @property
    def is_anonymous(self):
        """Required by Flask-Login"""
        return False
    
    @property
    def email(self):
        return self.user.email
    
    @property
    def username(self):
        return self.user.username
    
    @property
    def id(self):
        """Expose user ID directly for easy access"""
        return self.user.id

class AuthManager:
    """Authentication manager for Theodore"""
    
    def __init__(self, app=None, pinecone_api_key: str = None):
        self.app = app
        self.auth_service = None
        self.login_manager = LoginManager()
        
        if app and pinecone_api_key:
            self.init_app(app, pinecone_api_key)
    
    def init_app(self, app, pinecone_api_key: str):
        """Initialize Flask app with authentication"""
        self.app = app
        
        # Initialize auth service
        self.auth_service = AuthService(pinecone_api_key)
        
        # Configure Flask-Login
        self.login_manager.init_app(app)
        self.login_manager.login_view = 'auth.login'
        self.login_manager.login_message = 'Please log in to access this page.'
        self.login_manager.login_message_category = 'info'
        
        # Set user loader
        self.login_manager.user_loader(self.load_user)
        
        # Store auth manager in app context
        app.auth_manager = self
    
    def load_user(self, user_id: str):
        """Load user for Flask-Login"""
        try:
            user = self.auth_service.get_user_by_id(user_id)
            if user and user.is_active:
                return TheodoreUser(user)
            return None
        except Exception as e:
            print(f"Error loading user {user_id}: {e}")
            return None
    
    def register_user(self, email: str, username: str, password: str, confirm_password: str):
        """Register a new user"""
        from auth_models import UserRegistration
        
        registration = UserRegistration(
            email=email,
            username=username,
            password=password,
            confirm_password=confirm_password
        )
        
        user = self.auth_service.register_user(registration)
        return TheodoreUser(user)
    
    def authenticate_user(self, email: str, password: str, remember_me: bool = False):
        """Authenticate user login"""
        from auth_models import UserLogin
        
        login = UserLogin(
            email=email,
            password=password,
            remember_me=remember_me
        )
        
        user = self.auth_service.authenticate_user(login)
        return TheodoreUser(user)
    
    def get_user_by_email(self, email: str):
        """Get user by email"""
        user = self.auth_service.get_user_by_email(email)
        if user:
            return TheodoreUser(user)
        return None
    
    def get_user_by_username(self, username: str):
        """Get user by username"""
        user = self.auth_service.get_user_by_username(username)
        if user:
            return TheodoreUser(user)
        return None