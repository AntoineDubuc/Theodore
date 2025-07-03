"""
Secure credential storage using system keyring.
"""

import keyring
from typing import Optional, Dict, List
import json
import logging

logger = logging.getLogger(__name__)

class SecureStorage:
    """Secure storage for sensitive configuration using system keyring"""
    
    SERVICE_NAME = "theodore-ai"
    
    # Mapping of setting names to secure storage keys
    SECURE_KEYS = {
        'aws_access_key_id': 'aws-access-key-id',
        'aws_secret_access_key': 'aws-secret-access-key',
        'gemini_api_key': 'gemini-api-key',
        'openai_api_key': 'openai-api-key',
        'pinecone_api_key': 'pinecone-api-key',
        'perplexity_api_key': 'perplexity-api-key',
        'tavily_api_key': 'tavily-api-key',
    }
    
    @classmethod
    def store_credential(cls, key: str, value: str) -> bool:
        """
        Store a credential securely in the system keyring.
        
        Args:
            key: The credential key (e.g., 'gemini_api_key')
            value: The credential value
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            secure_key = cls.SECURE_KEYS.get(key, key)
            keyring.set_password(cls.SERVICE_NAME, secure_key, value)
            logger.debug(f"Stored credential: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store credential {key}: {e}")
            return False
    
    @classmethod
    def get_credential(cls, key: str) -> Optional[str]:
        """
        Retrieve a credential from the system keyring.
        
        Args:
            key: The credential key (e.g., 'gemini_api_key')
            
        Returns:
            The credential value or None if not found
        """
        try:
            secure_key = cls.SECURE_KEYS.get(key, key)
            credential = keyring.get_password(cls.SERVICE_NAME, secure_key)
            
            if credential:
                logger.debug(f"Retrieved credential: {key}")
            else:
                logger.debug(f"Credential not found: {key}")
                
            return credential
            
        except Exception as e:
            logger.error(f"Failed to retrieve credential {key}: {e}")
            return None
    
    @classmethod
    def delete_credential(cls, key: str) -> bool:
        """
        Delete a credential from the system keyring.
        
        Args:
            key: The credential key to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            secure_key = cls.SECURE_KEYS.get(key, key)
            keyring.delete_password(cls.SERVICE_NAME, secure_key)
            logger.debug(f"Deleted credential: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete credential {key}: {e}")
            return False
    
    @classmethod
    def list_stored_credentials(cls) -> List[str]:
        """
        List all credential keys that are stored in the keyring.
        
        Returns:
            List of credential keys that have values in the keyring
        """
        stored = []
        
        for key in cls.SECURE_KEYS.keys():
            if cls.get_credential(key):
                stored.append(key)
        
        return stored
    
    @classmethod
    def clear_all_credentials(cls) -> bool:
        """
        Clear all Theodore credentials from the keyring.
        
        Returns:
            True if all credentials were cleared successfully
        """
        success = True
        
        for key in cls.SECURE_KEYS.keys():
            if cls.get_credential(key):  # Only try to delete if it exists
                if not cls.delete_credential(key):
                    success = False
        
        return success
    
    @classmethod
    def validate_keyring_access(cls) -> bool:
        """
        Test if keyring is accessible by storing and retrieving a test value.
        
        Returns:
            True if keyring is working, False otherwise
        """
        test_key = "test-access"
        test_value = "test-value-12345"
        
        try:
            # Test store
            if not cls.store_credential(test_key, test_value):
                return False
            
            # Test retrieve
            retrieved = cls.get_credential(test_key)
            if retrieved != test_value:
                return False
            
            # Test delete
            if not cls.delete_credential(test_key):
                return False
            
            logger.debug("Keyring access validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Keyring access validation failed: {e}")
            return False
    
    @classmethod
    def get_keyring_backend_info(cls) -> Dict[str, str]:
        """
        Get information about the current keyring backend.
        
        Returns:
            Dictionary with keyring backend information
        """
        try:
            backend = keyring.get_keyring()
            return {
                "backend_name": backend.__class__.__name__,
                "backend_module": backend.__class__.__module__,
                "priority": str(getattr(backend, 'priority', 'unknown')),
                "viable": str(getattr(backend, 'viable', 'unknown'))
            }
        except Exception as e:
            logger.error(f"Failed to get keyring info: {e}")
            return {
                "backend_name": "unknown",
                "error": str(e)
            }
    
    @classmethod
    def import_credentials_from_env(cls, env_vars: Dict[str, Optional[str]]) -> Dict[str, bool]:
        """
        Import credentials from environment variables into secure storage.
        
        Args:
            env_vars: Dictionary of environment variable values
            
        Returns:
            Dictionary showing which credentials were imported successfully
        """
        results = {}
        
        for key, value in env_vars.items():
            if value and key in cls.SECURE_KEYS:
                results[key] = cls.store_credential(key, value)
            else:
                results[key] = False
        
        return results
    
    @classmethod
    def export_credentials_to_dict(cls, mask_values: bool = True) -> Dict[str, str]:
        """
        Export stored credentials to a dictionary.
        
        Args:
            mask_values: If True, mask credential values for display
            
        Returns:
            Dictionary of stored credentials
        """
        credentials = {}
        
        for key in cls.SECURE_KEYS.keys():
            value = cls.get_credential(key)
            if value:
                if mask_values:
                    credentials[key] = f"{value[:8]}***" if len(value) > 8 else "***"
                else:
                    credentials[key] = value
        
        return credentials


def get_secure_credential(key: str, fallback_value: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to get a credential with fallback.
    
    Args:
        key: Credential key to retrieve
        fallback_value: Value to return if not found in secure storage
        
    Returns:
        Credential value from secure storage or fallback value
    """
    secure_value = SecureStorage.get_credential(key)
    return secure_value if secure_value else fallback_value


def ensure_keyring_setup() -> bool:
    """
    Ensure keyring is properly set up and accessible.
    
    Returns:
        True if keyring is ready to use, False otherwise
    """
    try:
        # Test basic keyring functionality
        if SecureStorage.validate_keyring_access():
            logger.info("Keyring is properly configured and accessible")
            return True
        else:
            logger.warning("Keyring validation failed - secure storage may not work")
            return False
            
    except Exception as e:
        logger.error(f"Keyring setup check failed: {e}")
        return False