"""
User Authentication Service for Theodore
Handles user storage, validation, and session management using Pinecone as backend
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pinecone import Pinecone
from src.auth_models import User, UserRegistration, UserLogin, UserSession, UserNotFoundError, InvalidCredentialsError, UserAlreadyExistsError

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service using Pinecone for user storage"""
    
    def __init__(self, pinecone_api_key: str, index_name: str = "theodore-users"):
        """Initialize auth service with Pinecone"""
        self.pc = Pinecone(api_key=pinecone_api_key)
        self.index_name = index_name
        self.index = None
        
        # Try to connect to existing index or create new one
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize or create Pinecone index for users"""
        try:
            # Check if index exists
            indexes = self.pc.list_indexes()
            index_names = [idx.name for idx in indexes]
            
            if self.index_name not in index_names:
                logger.info(f"Creating new Pinecone index for users: {self.index_name}")
                # Create index with minimal dimensions (we'll use dummy vectors)
                self.pc.create_index(
                    name=self.index_name,
                    dimension=8,  # Minimal dimension for user storage
                    metric='cosine',
                    spec={
                        'serverless': {
                            'cloud': 'aws',
                            'region': 'us-east-1'
                        }
                    }
                )
                # Wait for index to be ready
                import time
                time.sleep(10)
            
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Connected to Pinecone index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone index for users: {e}")
            raise
    
    def _generate_dummy_vector(self, user_id: str) -> List[float]:
        """Generate a dummy vector for user storage"""
        # Use user_id hash to generate consistent dummy vector
        import hashlib
        hash_obj = hashlib.md5(user_id.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        
        # Generate 8 float values between -1 and 1
        vector = []
        for i in range(8):
            # Extract bits and normalize to [-1, 1]
            bit_value = (hash_int >> (i * 4)) & 0xF
            normalized = (bit_value / 15.0) * 2 - 1
            vector.append(normalized)
        
        return vector
    
    def register_user(self, registration: UserRegistration) -> User:
        """Register a new user"""
        try:
            # Check if user already exists by email
            existing_user = self.get_user_by_email(registration.email)
            if existing_user:
                raise UserAlreadyExistsError(registration.email)
            
            # Check if username is taken
            existing_user = self.get_user_by_username(registration.username)
            if existing_user:
                raise UserAlreadyExistsError(registration.username)
            
            # Create new user
            user = User(
                email=registration.email,
                username=registration.username,
                password_hash=""  # Will be set by set_password
            )
            user.set_password(registration.password)
            
            # Store in Pinecone
            vector = self._generate_dummy_vector(user.id)
            
            
            self.index.upsert(
                vectors=[
                    {
                        'id': f"user_{user.id}",
                        'values': vector,
                        'metadata': {
                            'type': 'user',
                            'user_id': user.id,
                            'email': user.email,
                            'username': user.username,
                            'password_hash': user.password_hash,
                            'is_active': user.is_active,
                            'created_at': user.created_at.isoformat(),
                            'last_login': user.last_login.isoformat() if user.last_login else ""
                        }
                    }
                ]
            )
            
            logger.info(f"User registered successfully: {user.email}")
            return user
            
        except (UserAlreadyExistsError, Exception) as e:
            logger.error(f"User registration failed: {e}")
            raise
    
    def authenticate_user(self, login: UserLogin) -> User:
        """Authenticate user login"""
        try:
            # Get user by email
            user = self.get_user_by_email(login.email)
            if not user:
                raise InvalidCredentialsError()
            
            # Check password
            if not user.check_password(login.password):
                raise InvalidCredentialsError()
            
            # Update last login
            user.last_login = datetime.utcnow()
            self._update_user(user)
            
            logger.info(f"User authenticated successfully: {user.email}")
            return user
            
        except InvalidCredentialsError:
            logger.error(f"User authentication failed: Invalid email or password")
            raise
        except Exception as e:
            logger.error(f"User authentication failed with unexpected error: {e}")
            raise InvalidCredentialsError()
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            # Query Pinecone for user
            results = self.index.query(
                vector=self._generate_dummy_vector(user_id),
                filter={'user_id': user_id, 'type': 'user'},
                top_k=1,
                include_metadata=True
            )
            
            if not results.matches:
                return None
            
            metadata = results.matches[0].metadata
            return self._metadata_to_user(metadata)
            
        except Exception as e:
            logger.error(f"Failed to get user by ID {user_id}: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            # Query Pinecone for user by email
            results = self.index.query(
                vector=[0.0] * 8,  # Dummy vector for search
                filter={'email': email, 'type': 'user'},
                top_k=1,
                include_metadata=True
            )
            
            if not results.matches:
                return None
            
            metadata = results.matches[0].metadata
            return self._metadata_to_user(metadata)
            
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            # Query Pinecone for user by username
            results = self.index.query(
                vector=[0.0] * 8,  # Dummy vector for search
                filter={'username': username.lower(), 'type': 'user'},
                top_k=1,
                include_metadata=True
            )
            
            if not results.matches:
                return None
            
            metadata = results.matches[0].metadata
            return self._metadata_to_user(metadata)
            
        except Exception as e:
            logger.error(f"Failed to get user by username {username}: {e}")
            return None
    
    def _metadata_to_user(self, metadata: Dict[str, Any]) -> User:
        """Convert Pinecone metadata to User object"""
        return User(
            id=metadata['user_id'],
            email=metadata['email'],
            username=metadata['username'],
            password_hash=metadata['password_hash'],
            is_active=metadata.get('is_active', True),
            created_at=datetime.fromisoformat(metadata['created_at']),
            last_login=datetime.fromisoformat(metadata['last_login']) if metadata.get('last_login') and metadata['last_login'] else None
        )
    
    def _update_user(self, user: User) -> None:
        """Update user in Pinecone"""
        try:
            vector = self._generate_dummy_vector(user.id)
            
            self.index.upsert(
                vectors=[
                    {
                        'id': f"user_{user.id}",
                        'values': vector,
                        'metadata': {
                            'type': 'user',
                            'user_id': user.id,
                            'email': user.email,
                            'username': user.username,
                            'password_hash': user.password_hash,
                            'is_active': user.is_active,
                            'created_at': user.created_at.isoformat(),
                            'last_login': user.last_login.isoformat() if user.last_login else ""
                        }
                    }
                ]
            )
            
        except Exception as e:
            logger.error(f"Failed to update user {user.id}: {e}")
            raise
    
    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user account"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.is_active = False
            self._update_user(user)
            return True
            
        except Exception as e:
            logger.error(f"Failed to deactivate user {user_id}: {e}")
            return False
    
    def list_users(self, limit: int = 100) -> List[User]:
        """List all users (admin function)"""
        try:
            # Query all user records
            results = self.index.query(
                vector=[0.0] * 8,
                filter={'type': 'user'},
                top_k=limit,
                include_metadata=True
            )
            
            users = []
            for match in results.matches:
                try:
                    user = self._metadata_to_user(match.metadata)
                    users.append(user)
                except Exception as e:
                    logger.error(f"Failed to parse user metadata: {e}")
                    continue
            
            return users
            
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            return []