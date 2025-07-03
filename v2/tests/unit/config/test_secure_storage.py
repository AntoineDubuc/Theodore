"""
Unit tests for Theodore secure storage system.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.infrastructure.config.secure_storage import (
    SecureStorage,
    get_secure_credential,
    ensure_keyring_setup
)


class TestSecureStorage:
    """Test SecureStorage class functionality"""
    
    def test_secure_keys_mapping(self):
        """Test the secure keys mapping"""
        expected_keys = {
            'aws_access_key_id': 'aws-access-key-id',
            'aws_secret_access_key': 'aws-secret-access-key',
            'gemini_api_key': 'gemini-api-key',
            'openai_api_key': 'openai-api-key',
            'pinecone_api_key': 'pinecone-api-key',
            'perplexity_api_key': 'perplexity-api-key',
            'tavily_api_key': 'tavily-api-key',
        }
        
        assert SecureStorage.SECURE_KEYS == expected_keys
    
    def test_service_name(self):
        """Test the service name constant"""
        assert SecureStorage.SERVICE_NAME == "theodore-ai"
    
    @patch('src.infrastructure.config.secure_storage.keyring')
    def test_store_credential_success(self, mock_keyring):
        """Test successful credential storage"""
        mock_keyring.set_password.return_value = None
        
        result = SecureStorage.store_credential('gemini_api_key', 'test-api-key')
        
        assert result is True
        mock_keyring.set_password.assert_called_once_with(
            'theodore-ai', 
            'gemini-api-key', 
            'test-api-key'
        )
    
    @patch('src.infrastructure.config.secure_storage.keyring')
    def test_store_credential_failure(self, mock_keyring):
        """Test credential storage failure"""
        mock_keyring.set_password.side_effect = Exception("Keyring error")
        
        result = SecureStorage.store_credential('gemini_api_key', 'test-api-key')
        
        assert result is False
    
    @patch('src.infrastructure.config.secure_storage.keyring')
    def test_get_credential_success(self, mock_keyring):
        """Test successful credential retrieval"""
        mock_keyring.get_password.return_value = 'test-api-key'
        
        result = SecureStorage.get_credential('gemini_api_key')
        
        assert result == 'test-api-key'
        mock_keyring.get_password.assert_called_once_with(
            'theodore-ai',
            'gemini-api-key'
        )
    
    @patch('src.infrastructure.config.secure_storage.keyring')
    def test_get_credential_not_found(self, mock_keyring):
        """Test credential retrieval when not found"""
        mock_keyring.get_password.return_value = None
        
        result = SecureStorage.get_credential('gemini_api_key')
        
        assert result is None
    
    @patch('src.infrastructure.config.secure_storage.keyring')
    def test_get_credential_failure(self, mock_keyring):
        """Test credential retrieval failure"""
        mock_keyring.get_password.side_effect = Exception("Keyring error")
        
        result = SecureStorage.get_credential('gemini_api_key')
        
        assert result is None
    
    @patch('src.infrastructure.config.secure_storage.keyring')
    def test_delete_credential_success(self, mock_keyring):
        """Test successful credential deletion"""
        mock_keyring.delete_password.return_value = None
        
        result = SecureStorage.delete_credential('gemini_api_key')
        
        assert result is True
        mock_keyring.delete_password.assert_called_once_with(
            'theodore-ai',
            'gemini-api-key'
        )
    
    @patch('src.infrastructure.config.secure_storage.keyring')
    def test_delete_credential_failure(self, mock_keyring):
        """Test credential deletion failure"""
        mock_keyring.delete_password.side_effect = Exception("Keyring error")
        
        result = SecureStorage.delete_credential('gemini_api_key')
        
        assert result is False
    
    @patch.object(SecureStorage, 'get_credential')
    def test_list_stored_credentials(self, mock_get_credential):
        """Test listing stored credentials"""
        # Mock some credentials as stored, others as not
        def mock_get_side_effect(key):
            stored_keys = ['gemini_api_key', 'pinecone_api_key']
            return 'test-value' if key in stored_keys else None
        
        mock_get_credential.side_effect = mock_get_side_effect
        
        result = SecureStorage.list_stored_credentials()
        
        assert 'gemini_api_key' in result
        assert 'pinecone_api_key' in result
        assert 'aws_access_key_id' not in result
        assert len(result) == 2
    
    @patch.object(SecureStorage, 'get_credential')
    @patch.object(SecureStorage, 'delete_credential')
    def test_clear_all_credentials_success(self, mock_delete, mock_get):
        """Test successful clearing of all credentials"""
        # Mock some credentials as existing
        def mock_get_side_effect(key):
            stored_keys = ['gemini_api_key', 'pinecone_api_key']
            return 'test-value' if key in stored_keys else None
        
        mock_get.side_effect = mock_get_side_effect
        mock_delete.return_value = True
        
        result = SecureStorage.clear_all_credentials()
        
        assert result is True
        # Should only try to delete existing credentials
        assert mock_delete.call_count == 2
    
    @patch.object(SecureStorage, 'get_credential')
    @patch.object(SecureStorage, 'delete_credential')
    def test_clear_all_credentials_partial_failure(self, mock_delete, mock_get):
        """Test partial failure when clearing credentials"""
        # Mock some credentials as existing
        def mock_get_side_effect(key):
            stored_keys = ['gemini_api_key', 'pinecone_api_key']
            return 'test-value' if key in stored_keys else None
        
        mock_get.side_effect = mock_get_side_effect
        
        # Mock one deletion failure
        def mock_delete_side_effect(key):
            return key != 'pinecone_api_key'  # Fail for pinecone_api_key
        
        mock_delete.side_effect = mock_delete_side_effect
        
        result = SecureStorage.clear_all_credentials()
        
        assert result is False
    
    @patch.object(SecureStorage, 'store_credential')
    @patch.object(SecureStorage, 'get_credential')
    @patch.object(SecureStorage, 'delete_credential')
    def test_validate_keyring_access_success(self, mock_delete, mock_get, mock_store):
        """Test successful keyring access validation"""
        mock_store.return_value = True
        mock_get.return_value = "test-value-12345"
        mock_delete.return_value = True
        
        result = SecureStorage.validate_keyring_access()
        
        assert result is True
        mock_store.assert_called_once_with("test-access", "test-value-12345")
        mock_get.assert_called_once_with("test-access")
        mock_delete.assert_called_once_with("test-access")
    
    @patch.object(SecureStorage, 'store_credential')
    def test_validate_keyring_access_store_failure(self, mock_store):
        """Test keyring validation with store failure"""
        mock_store.return_value = False
        
        result = SecureStorage.validate_keyring_access()
        
        assert result is False
    
    @patch.object(SecureStorage, 'store_credential')
    @patch.object(SecureStorage, 'get_credential')
    def test_validate_keyring_access_get_failure(self, mock_get, mock_store):
        """Test keyring validation with get failure"""
        mock_store.return_value = True
        mock_get.return_value = "wrong-value"  # Different from stored value
        
        result = SecureStorage.validate_keyring_access()
        
        assert result is False
    
    @patch.object(SecureStorage, 'store_credential')
    @patch.object(SecureStorage, 'get_credential')
    @patch.object(SecureStorage, 'delete_credential')
    def test_validate_keyring_access_delete_failure(self, mock_delete, mock_get, mock_store):
        """Test keyring validation with delete failure"""
        mock_store.return_value = True
        mock_get.return_value = "test-value-12345"
        mock_delete.return_value = False
        
        result = SecureStorage.validate_keyring_access()
        
        assert result is False
    
    @patch('src.infrastructure.config.secure_storage.keyring')
    def test_get_keyring_backend_info_success(self, mock_keyring):
        """Test successful keyring backend info retrieval"""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "MacOSKeychain"
        mock_backend.__class__.__module__ = "keyring.backends.macOS"
        mock_backend.priority = 10
        mock_backend.viable = True
        
        mock_keyring.get_keyring.return_value = mock_backend
        
        result = SecureStorage.get_keyring_backend_info()
        
        expected = {
            "backend_name": "MacOSKeychain",
            "backend_module": "keyring.backends.macOS",
            "priority": "10",
            "viable": "True"
        }
        
        assert result == expected
    
    @patch('src.infrastructure.config.secure_storage.keyring')
    def test_get_keyring_backend_info_failure(self, mock_keyring):
        """Test keyring backend info retrieval failure"""
        mock_keyring.get_keyring.side_effect = Exception("Backend error")
        
        result = SecureStorage.get_keyring_backend_info()
        
        assert result["backend_name"] == "unknown"
        assert "error" in result
        assert "Backend error" in result["error"]
    
    @patch.object(SecureStorage, 'store_credential')
    def test_import_credentials_from_env(self, mock_store):
        """Test importing credentials from environment variables"""
        env_vars = {
            'gemini_api_key': 'test-gemini-key',
            'pinecone_api_key': 'test-pinecone-key',
            'non_secure_key': 'test-value',  # Not in SECURE_KEYS
            'empty_key': None
        }
        
        mock_store.return_value = True
        
        result = SecureStorage.import_credentials_from_env(env_vars)
        
        assert result['gemini_api_key'] is True
        assert result['pinecone_api_key'] is True
        assert result['non_secure_key'] is False  # Not in SECURE_KEYS
        assert result['empty_key'] is False  # Empty value
        
        # Should only call store for valid credentials
        assert mock_store.call_count == 2
    
    @patch.object(SecureStorage, 'get_credential')
    def test_export_credentials_to_dict_masked(self, mock_get):
        """Test exporting credentials with masking"""
        def mock_get_side_effect(key):
            credentials = {
                'gemini_api_key': 'AIzaSyDVeryLongAPIKeyForTesting123456789',
                'pinecone_api_key': '12345678-1234-1234-1234-123456789012'
            }
            return credentials.get(key)
        
        mock_get.side_effect = mock_get_side_effect
        
        result = SecureStorage.export_credentials_to_dict(mask_values=True)
        
        assert result['gemini_api_key'] == 'AIzaSyDV***'
        assert result['pinecone_api_key'] == '12345678***'
    
    @patch.object(SecureStorage, 'get_credential')
    def test_export_credentials_to_dict_unmasked(self, mock_get):
        """Test exporting credentials without masking"""
        def mock_get_side_effect(key):
            credentials = {
                'gemini_api_key': 'test-api-key'
            }
            return credentials.get(key)
        
        mock_get.side_effect = mock_get_side_effect
        
        result = SecureStorage.export_credentials_to_dict(mask_values=False)
        
        assert result['gemini_api_key'] == 'test-api-key'


class TestHelperFunctions:
    """Test helper functions for secure storage"""
    
    @patch.object(SecureStorage, 'get_credential')
    def test_get_secure_credential_found(self, mock_get):
        """Test get_secure_credential when credential is found"""
        mock_get.return_value = 'test-api-key'
        
        result = get_secure_credential('gemini_api_key', 'fallback-value')
        
        assert result == 'test-api-key'
        mock_get.assert_called_once_with('gemini_api_key')
    
    @patch.object(SecureStorage, 'get_credential')
    def test_get_secure_credential_not_found(self, mock_get):
        """Test get_secure_credential when credential is not found"""
        mock_get.return_value = None
        
        result = get_secure_credential('gemini_api_key', 'fallback-value')
        
        assert result == 'fallback-value'
        mock_get.assert_called_once_with('gemini_api_key')
    
    @patch.object(SecureStorage, 'get_credential')
    def test_get_secure_credential_no_fallback(self, mock_get):
        """Test get_secure_credential with no fallback"""
        mock_get.return_value = None
        
        result = get_secure_credential('gemini_api_key')
        
        assert result is None
    
    @patch.object(SecureStorage, 'validate_keyring_access')
    def test_ensure_keyring_setup_success(self, mock_validate):
        """Test successful keyring setup validation"""
        mock_validate.return_value = True
        
        result = ensure_keyring_setup()
        
        assert result is True
        mock_validate.assert_called_once()
    
    @patch.object(SecureStorage, 'validate_keyring_access')
    def test_ensure_keyring_setup_failure(self, mock_validate):
        """Test keyring setup validation failure"""
        mock_validate.return_value = False
        
        result = ensure_keyring_setup()
        
        assert result is False
        mock_validate.assert_called_once()
    
    @patch.object(SecureStorage, 'validate_keyring_access')
    def test_ensure_keyring_setup_exception(self, mock_validate):
        """Test keyring setup with exception"""
        mock_validate.side_effect = Exception("Keyring error")
        
        result = ensure_keyring_setup()
        
        assert result is False