"""
Theodore application configuration with multiple source support.

Configuration sources (in order of precedence):
1. CLI arguments (handled by Click)
2. Environment variables (THEODORE_*)
3. Configuration files (.theodore.yml)
4. Default values
"""

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List, Dict, Any
from pathlib import Path
import os
from enum import Enum


class Environment(str, Enum):
    """Application environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AIModel(str, Enum):
    """Supported AI models"""
    GEMINI_2_FLASH = "gemini-2.0-flash-exp"
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    NOVA_PRO = "amazon.nova-pro-v1:0"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O_MINI = "gpt-4o-mini"


class ResearchSettings(BaseModel):
    """Research-specific configuration"""
    max_pages_per_company: int = Field(default=50, ge=1, le=100)
    timeout_seconds: int = Field(default=30, ge=5, le=300)
    parallel_requests: int = Field(default=5, ge=1, le=20)
    enable_javascript: bool = Field(default=True)
    respect_robots_txt: bool = Field(default=True)
    
    # AI Analysis
    primary_analysis_model: AIModel = Field(default=AIModel.GEMINI_2_FLASH)
    fallback_analysis_model: AIModel = Field(default=AIModel.GPT_4O_MINI)
    max_analysis_tokens: int = Field(default=150000, ge=1000, le=1000000)
    
    # Cost optimization
    cost_optimization_enabled: bool = Field(default=True)
    max_cost_per_company: float = Field(default=5.0, ge=0.1, le=50.0)


class SearchSettings(BaseModel):
    """Search and discovery configuration"""
    default_similarity_limit: int = Field(default=10, ge=1, le=50)
    min_confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    enable_mcp_search: bool = Field(default=True)
    enable_google_fallback: bool = Field(default=True)
    
    # Vector search
    vector_dimensions: int = Field(default=1536)
    similarity_metric: str = Field(default="cosine")


class StorageSettings(BaseModel):
    """Data storage configuration"""
    cache_enabled: bool = Field(default=True)
    cache_ttl_hours: int = Field(default=24, ge=1, le=168)  # 1 hour to 1 week
    backup_enabled: bool = Field(default=True)
    max_backup_files: int = Field(default=10, ge=1, le=100)


class TheodoreSettings(BaseSettings):
    """
    Theodore application configuration with multiple source support.
    """
    
    model_config = SettingsConfigDict(
        # Environment variable prefix
        env_prefix='THEODORE_',
        
        # Configuration file locations to check
        env_file=[
            '.theodore.yml',
            '.theodore.yaml', 
            '~/.theodore/config.yml',
            '/etc/theodore/config.yml'
        ],
        
        # File encoding
        env_file_encoding='utf-8',
        
        # Allow extra fields for extensibility
        extra='allow',
        
        # Case sensitivity
        case_sensitive=False,
        
        # Nested environment variables
        env_nested_delimiter='__'
    )
    
    # Application Settings
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Application environment"
    )
    
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level"
    )
    
    verbose: bool = Field(
        default=False,
        description="Enable verbose output"
    )
    
    # AWS Bedrock Configuration
    aws_region: str = Field(
        default="us-west-2",
        description="AWS region for Bedrock"
    )
    
    aws_access_key_id: Optional[str] = Field(
        default=None,
        description="AWS access key ID"
    )
    
    aws_secret_access_key: Optional[str] = Field(
        default=None,
        description="AWS secret access key"
    )
    
    bedrock_analysis_model: str = Field(
        default="amazon.nova-pro-v1:0",
        description="Bedrock model for analysis"
    )
    
    # Google AI Configuration
    gemini_api_key: Optional[str] = Field(
        default=None,
        description="Google Gemini API key"
    )
    
    gemini_model: str = Field(
        default="gemini-2.0-flash-exp",
        description="Gemini model version"
    )
    
    # OpenAI Configuration (Fallback)
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key"
    )
    
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model version"
    )
    
    # Vector Database (Pinecone)
    pinecone_api_key: Optional[str] = Field(
        default=None,
        description="Pinecone API key"
    )
    
    pinecone_index_name: str = Field(
        default="theodore-companies",
        description="Pinecone index name"
    )
    
    pinecone_environment: str = Field(
        default="us-west1-gcp-free",
        description="Pinecone environment"
    )
    
    # MCP Tools Configuration
    mcp_tools_enabled: List[str] = Field(
        default_factory=lambda: ["perplexity", "tavily"],
        description="Enabled MCP tools"
    )
    
    perplexity_api_key: Optional[str] = Field(
        default=None,
        description="Perplexity API key"
    )
    
    tavily_api_key: Optional[str] = Field(
        default=None,
        description="Tavily API key"
    )
    
    # Nested configuration sections
    research: ResearchSettings = Field(default_factory=ResearchSettings)
    search: SearchSettings = Field(default_factory=SearchSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    
    # Output Configuration
    default_output_format: str = Field(
        default="table",
        description="Default CLI output format"
    )
    
    colored_output: bool = Field(
        default=True,
        description="Enable colored terminal output"
    )
    
    progress_bars: bool = Field(
        default=True,
        description="Show progress bars"
    )
    
    # Security Settings
    enable_secure_storage: bool = Field(
        default=True,
        description="Use keyring for secure credential storage"
    )
    
    @field_validator('aws_region')
    @classmethod
    def validate_aws_region(cls, v: str) -> str:
        """Validate AWS region format"""
        if not v:
            raise ValueError("AWS region cannot be empty")
        
        # Basic AWS region validation
        if not (len(v) >= 9 and '-' in v):
            raise ValueError(f"Invalid AWS region format: {v}")
        
        return v
    
    @field_validator('pinecone_index_name')
    @classmethod
    def validate_pinecone_index(cls, v: str) -> str:
        """Validate Pinecone index name"""
        if not v:
            raise ValueError("Pinecone index name cannot be empty")
        
        # Pinecone index naming rules
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError(f"Invalid Pinecone index name: {v}")
        
        return v.lower()
    
    @field_validator('mcp_tools_enabled')
    @classmethod
    def validate_mcp_tools(cls, v: List[str]) -> List[str]:
        """Validate MCP tools list"""
        valid_tools = ["perplexity", "tavily", "google"]
        
        for tool in v:
            if tool not in valid_tools:
                raise ValueError(f"Unknown MCP tool: {tool}. Valid tools: {valid_tools}")
        
        return v
    
    def get_config_file_path(self) -> Path:
        """Get the primary configuration file path"""
        return Path.home() / ".theodore" / "config.yml"
    
    def ensure_config_dir(self) -> Path:
        """Ensure configuration directory exists"""
        config_dir = Path.home() / ".theodore"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    def has_required_credentials(self) -> bool:
        """Check if required API credentials are available"""
        required_any = [
            self.gemini_api_key,
            self.aws_access_key_id and self.aws_secret_access_key,
            self.openai_api_key
        ]
        
        return any(required_any) and self.pinecone_api_key is not None
    
    def get_missing_credentials(self) -> List[str]:
        """Get list of missing required credentials"""
        missing = []
        
        # Need at least one AI provider
        has_ai_provider = any([
            self.gemini_api_key,
            self.aws_access_key_id and self.aws_secret_access_key,
            self.openai_api_key
        ])
        
        if not has_ai_provider:
            missing.append("AI Provider (Gemini, AWS, or OpenAI)")
        
        if not self.pinecone_api_key:
            missing.append("Pinecone API key")
        
        return missing
    
    def is_production_ready(self) -> bool:
        """Check if configuration is ready for production use"""
        return (
            self.environment == Environment.PRODUCTION and
            not self.debug and
            self.has_required_credentials() and
            self.log_level in [LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR]
        )
    
    def to_safe_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with sensitive data masked"""
        data = self.model_dump()
        
        # Mask sensitive fields
        sensitive_fields = [
            'aws_access_key_id', 'aws_secret_access_key',
            'gemini_api_key', 'openai_api_key', 'pinecone_api_key',
            'perplexity_api_key', 'tavily_api_key'
        ]
        
        for field in sensitive_fields:
            if field in data and data[field]:
                data[field] = f"{data[field][:8]}***"
        
        return data


# Global settings instance
settings = TheodoreSettings()