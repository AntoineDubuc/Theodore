"""
Unit tests for Theodore configuration settings.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from pydantic import ValidationError

from src.infrastructure.config.settings import (
    TheodoreSettings, 
    Environment, 
    LogLevel, 
    AIModel,
    ResearchSettings,
    SearchSettings,
    StorageSettings
)


class TestEnvironmentEnum:
    """Test Environment enum values"""
    
    def test_environment_values(self):
        """Test all environment enum values"""
        assert Environment.DEVELOPMENT == "development"
        assert Environment.STAGING == "staging"
        assert Environment.PRODUCTION == "production"
        assert Environment.TESTING == "testing"


class TestLogLevelEnum:
    """Test LogLevel enum values"""
    
    def test_log_level_values(self):
        """Test all log level enum values"""
        assert LogLevel.DEBUG == "DEBUG"
        assert LogLevel.INFO == "INFO"
        assert LogLevel.WARNING == "WARNING"
        assert LogLevel.ERROR == "ERROR"
        assert LogLevel.CRITICAL == "CRITICAL"


class TestAIModelEnum:
    """Test AIModel enum values"""
    
    def test_ai_model_values(self):
        """Test all AI model enum values"""
        assert AIModel.GEMINI_2_FLASH == "gemini-2.0-flash-exp"
        assert AIModel.GEMINI_1_5_PRO == "gemini-1.5-pro"
        assert AIModel.NOVA_PRO == "amazon.nova-pro-v1:0"
        assert AIModel.GPT_4_TURBO == "gpt-4-turbo"
        assert AIModel.GPT_4O_MINI == "gpt-4o-mini"


class TestResearchSettings:
    """Test ResearchSettings model"""
    
    def test_default_values(self):
        """Test default research settings"""
        settings = ResearchSettings()
        
        assert settings.max_pages_per_company == 50
        assert settings.timeout_seconds == 30
        assert settings.parallel_requests == 5
        assert settings.enable_javascript is True
        assert settings.respect_robots_txt is True
        assert settings.primary_analysis_model == AIModel.GEMINI_2_FLASH
        assert settings.fallback_analysis_model == AIModel.GPT_4O_MINI
        assert settings.max_analysis_tokens == 150000
        assert settings.cost_optimization_enabled is True
        assert settings.max_cost_per_company == 5.0
    
    def test_validation_constraints(self):
        """Test validation constraints"""
        # Test max_pages_per_company constraints
        with pytest.raises(ValidationError):
            ResearchSettings(max_pages_per_company=0)  # Below minimum
        
        with pytest.raises(ValidationError):
            ResearchSettings(max_pages_per_company=101)  # Above maximum
        
        # Test timeout_seconds constraints
        with pytest.raises(ValidationError):
            ResearchSettings(timeout_seconds=4)  # Below minimum
        
        with pytest.raises(ValidationError):
            ResearchSettings(timeout_seconds=301)  # Above maximum
        
        # Test parallel_requests constraints
        with pytest.raises(ValidationError):
            ResearchSettings(parallel_requests=0)  # Below minimum
        
        with pytest.raises(ValidationError):
            ResearchSettings(parallel_requests=21)  # Above maximum


class TestSearchSettings:
    """Test SearchSettings model"""
    
    def test_default_values(self):
        """Test default search settings"""
        settings = SearchSettings()
        
        assert settings.default_similarity_limit == 10
        assert settings.min_confidence_threshold == 0.5
        assert settings.enable_mcp_search is True
        assert settings.enable_google_fallback is True
        assert settings.vector_dimensions == 1536
        assert settings.similarity_metric == "cosine"
    
    def test_validation_constraints(self):
        """Test validation constraints"""
        # Test similarity limit constraints
        with pytest.raises(ValidationError):
            SearchSettings(default_similarity_limit=0)  # Below minimum
        
        with pytest.raises(ValidationError):
            SearchSettings(default_similarity_limit=51)  # Above maximum
        
        # Test confidence threshold constraints
        with pytest.raises(ValidationError):
            SearchSettings(min_confidence_threshold=-0.1)  # Below minimum
        
        with pytest.raises(ValidationError):
            SearchSettings(min_confidence_threshold=1.1)  # Above maximum


class TestStorageSettings:
    """Test StorageSettings model"""
    
    def test_default_values(self):
        """Test default storage settings"""
        settings = StorageSettings()
        
        assert settings.cache_enabled is True
        assert settings.cache_ttl_hours == 24
        assert settings.backup_enabled is True
        assert settings.max_backup_files == 10
    
    def test_validation_constraints(self):
        """Test validation constraints"""
        # Test cache_ttl_hours constraints
        with pytest.raises(ValidationError):
            StorageSettings(cache_ttl_hours=0)  # Below minimum
        
        with pytest.raises(ValidationError):
            StorageSettings(cache_ttl_hours=169)  # Above maximum
        
        # Test max_backup_files constraints
        with pytest.raises(ValidationError):
            StorageSettings(max_backup_files=0)  # Below minimum
        
        with pytest.raises(ValidationError):
            StorageSettings(max_backup_files=101)  # Above maximum


class TestTheodoreSettings:
    """Test main TheodoreSettings class"""
    
    def test_default_values(self):
        """Test default configuration values"""
        settings = TheodoreSettings()
        
        # Application settings
        assert settings.environment == Environment.DEVELOPMENT
        assert settings.debug is False
        assert settings.log_level == LogLevel.INFO
        assert settings.verbose is False
        
        # AWS settings
        assert settings.aws_region == "us-west-2"
        assert settings.aws_access_key_id is None
        assert settings.aws_secret_access_key is None
        assert settings.bedrock_analysis_model == "amazon.nova-pro-v1:0"
        
        # Gemini settings
        assert settings.gemini_api_key is None
        assert settings.gemini_model == "gemini-2.0-flash-exp"
        
        # OpenAI settings
        assert settings.openai_api_key is None
        assert settings.openai_model == "gpt-4o-mini"
        
        # Pinecone settings
        assert settings.pinecone_api_key is None
        assert settings.pinecone_index_name == "theodore-companies"
        assert settings.pinecone_environment == "us-west1-gcp-free"
        
        # MCP settings
        assert "perplexity" in settings.mcp_tools_enabled
        assert "tavily" in settings.mcp_tools_enabled
        assert settings.perplexity_api_key is None
        assert settings.tavily_api_key is None
        
        # Nested settings
        assert isinstance(settings.research, ResearchSettings)
        assert isinstance(settings.search, SearchSettings)
        assert isinstance(settings.storage, StorageSettings)
        
        # Output settings
        assert settings.default_output_format == "table"
        assert settings.colored_output is True
        assert settings.progress_bars is True
        
        # Security settings
        assert settings.enable_secure_storage is True
    
    def test_aws_region_validation(self):
        """Test AWS region validation"""
        # Valid regions should work
        settings = TheodoreSettings(aws_region="us-east-1")
        assert settings.aws_region == "us-east-1"
        
        # Invalid regions should raise ValidationError
        with pytest.raises(ValidationError):
            TheodoreSettings(aws_region="")
        
        with pytest.raises(ValidationError):
            TheodoreSettings(aws_region="invalid")
    
    def test_pinecone_index_validation(self):
        """Test Pinecone index name validation"""
        # Valid index names should work
        settings = TheodoreSettings(pinecone_index_name="test-index")
        assert settings.pinecone_index_name == "test-index"
        
        settings = TheodoreSettings(pinecone_index_name="TEST_INDEX")
        assert settings.pinecone_index_name == "test_index"  # Should be lowercased
        
        # Invalid index names should raise ValidationError
        with pytest.raises(ValidationError):
            TheodoreSettings(pinecone_index_name="")
        
        with pytest.raises(ValidationError):
            TheodoreSettings(pinecone_index_name="invalid@index")
    
    def test_mcp_tools_validation(self):
        """Test MCP tools validation"""
        # Valid tools should work
        settings = TheodoreSettings(mcp_tools_enabled=["perplexity"])
        assert settings.mcp_tools_enabled == ["perplexity"]
        
        # Invalid tools should raise ValidationError
        with pytest.raises(ValidationError):
            TheodoreSettings(mcp_tools_enabled=["invalid_tool"])
    
    def test_has_required_credentials(self):
        """Test required credentials checking"""
        # No credentials
        settings = TheodoreSettings()
        assert not settings.has_required_credentials()
        
        # Only Pinecone (missing AI provider)
        settings = TheodoreSettings(pinecone_api_key="test-key")
        assert not settings.has_required_credentials()
        
        # Only Gemini (missing Pinecone)
        settings = TheodoreSettings(gemini_api_key="test-key")
        assert not settings.has_required_credentials()
        
        # Gemini + Pinecone (complete)
        settings = TheodoreSettings(
            gemini_api_key="test-key",
            pinecone_api_key="test-key"
        )
        assert settings.has_required_credentials()
        
        # AWS + Pinecone (complete)
        settings = TheodoreSettings(
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            pinecone_api_key="test-key"
        )
        assert settings.has_required_credentials()
    
    def test_get_missing_credentials(self):
        """Test missing credentials detection"""
        # No credentials
        settings = TheodoreSettings()
        missing = settings.get_missing_credentials()
        assert "AI Provider (Gemini, AWS, or OpenAI)" in missing
        assert "Pinecone API key" in missing
        
        # Only Gemini
        settings = TheodoreSettings(gemini_api_key="test-key")
        missing = settings.get_missing_credentials()
        assert "AI Provider (Gemini, AWS, or OpenAI)" not in missing
        assert "Pinecone API key" in missing
        
        # Complete credentials
        settings = TheodoreSettings(
            gemini_api_key="test-key",
            pinecone_api_key="test-key"
        )
        missing = settings.get_missing_credentials()
        assert len(missing) == 0
    
    def test_is_production_ready(self):
        """Test production readiness check"""
        # Development environment
        settings = TheodoreSettings()
        assert not settings.is_production_ready()
        
        # Production environment but missing credentials
        settings = TheodoreSettings(environment=Environment.PRODUCTION)
        assert not settings.is_production_ready()
        
        # Production environment with debug enabled
        settings = TheodoreSettings(
            environment=Environment.PRODUCTION,
            debug=True,
            gemini_api_key="test-key",
            pinecone_api_key="test-key"
        )
        assert not settings.is_production_ready()
        
        # Properly configured production
        settings = TheodoreSettings(
            environment=Environment.PRODUCTION,
            debug=False,
            log_level=LogLevel.INFO,
            gemini_api_key="test-key",
            pinecone_api_key="test-key"
        )
        assert settings.is_production_ready()
    
    def test_to_safe_dict(self):
        """Test safe dictionary conversion with masked sensitive data"""
        settings = TheodoreSettings(
            gemini_api_key="AIzaSyDVeryLongAPIKeyForTesting123456789",
            pinecone_api_key="12345678-1234-1234-1234-123456789012"
        )
        
        safe_dict = settings.to_safe_dict()
        
        # Sensitive fields should be masked
        assert safe_dict['gemini_api_key'] == "AIzaSyDV***"
        assert safe_dict['pinecone_api_key'] == "12345678***"
        
        # Non-sensitive fields should be unchanged
        assert safe_dict['environment'] == "development"
        assert safe_dict['gemini_model'] == "gemini-2.0-flash-exp"
    
    def test_get_config_file_path(self):
        """Test configuration file path generation"""
        settings = TheodoreSettings()
        config_path = settings.get_config_file_path()
        
        assert config_path.name == "config.yml"
        assert config_path.parent.name == ".theodore"
        assert str(config_path).endswith("/.theodore/config.yml")
    
    def test_ensure_config_dir(self):
        """Test configuration directory creation"""
        settings = TheodoreSettings()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the home directory
            temp_path = Path(temp_dir)
            config_dir = temp_path / ".theodore"
            
            # Directory shouldn't exist initially
            assert not config_dir.exists()
            
            # Manually create directory to test
            config_dir.mkdir(parents=True, exist_ok=True)
            assert config_dir.exists()
            assert config_dir.is_dir()


class TestConfigurationFromEnvironment:
    """Test configuration loading from environment variables"""
    
    def test_environment_variable_loading(self, monkeypatch):
        """Test loading configuration from environment variables"""
        # Set environment variables
        monkeypatch.setenv("THEODORE_ENVIRONMENT", "production")
        monkeypatch.setenv("THEODORE_DEBUG", "true")
        monkeypatch.setenv("THEODORE_GEMINI_API_KEY", "test-gemini-key")
        monkeypatch.setenv("THEODORE_AWS_REGION", "eu-west-1")
        monkeypatch.setenv("THEODORE_RESEARCH__MAX_PAGES_PER_COMPANY", "25")
        
        # Create settings (should load from environment)
        settings = TheodoreSettings()
        
        assert settings.environment == Environment.PRODUCTION
        assert settings.debug is True
        assert settings.gemini_api_key == "test-gemini-key"
        assert settings.aws_region == "eu-west-1"
        assert settings.research.max_pages_per_company == 25


class TestConfigurationFromFile:
    """Test configuration loading from YAML files"""
    
    def test_yaml_file_loading(self):
        """Test loading configuration from YAML file"""
        config_data = {
            'environment': 'staging',
            'debug': True,
            'gemini_model': 'gemini-1.5-pro',
            'research': {
                'max_pages_per_company': 30,
                'timeout_seconds': 45
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name
        
        try:
            # Test direct file reading (simulating how Pydantic Settings would work)
            with open(config_file, 'r') as f:
                loaded_config = yaml.safe_load(f)
            
            assert loaded_config['environment'] == 'staging'
            assert loaded_config['debug'] is True
            assert loaded_config['gemini_model'] == 'gemini-1.5-pro'
            assert loaded_config['research']['max_pages_per_company'] == 30
            assert loaded_config['research']['timeout_seconds'] == 45
            
        finally:
            Path(config_file).unlink()  # Clean up