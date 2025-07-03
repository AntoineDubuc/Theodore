"""
Configuration Provider for Theodore v2 Container.

Simplified configuration provider that works with dependency-injector library.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dependency_injector import containers, providers
import logging


class ConfigProvider(containers.DeclarativeContainer):
    """
    Configuration provider with hierarchical loading and validation.
    
    Uses dependency-injector Configuration providers properly.
    """
    
    # Main configuration
    config = providers.Configuration()
    
    def __init__(self, config_path: str = "config/", environment: str = "development"):
        """
        Initialize configuration provider.
        
        Args:
            config_path: Base path for configuration files
            environment: Target environment (development, testing, production, cli)
        """
        super().__init__()
        self.config_path = Path(config_path)
        self.environment = environment
        self.logger = logging.getLogger(__name__)
        
        # Set default configuration
        self._set_defaults()
        
        # Load configuration files
        self._load_configuration()
        
        # Inject environment variables
        self._inject_environment_variables()
    
    def _set_defaults(self) -> None:
        """Set default configuration values."""
        defaults = {
            "app": {
                "name": "theodore-v2",
                "version": "1.0.0",
                "debug": False,
                "log_level": "INFO"
            },
            "storage": {
                "vector_storage": {
                    "provider": "pinecone",
                    "index_name": "theodore-companies",
                    "environment": "gcp-starter",
                    "dimension": 1536,
                    "api_key": "",
                    "timeout_seconds": 30.0
                },
                "cache": {
                    "provider": "memory",
                    "ttl_seconds": 3600,
                    "max_size": 1000
                }
            },
            "ai_services": {
                "llm_provider": {
                    "primary": "bedrock",
                    "fallback": "openai",
                    "timeout_seconds": 30.0,
                    "max_retries": 3
                },
                "embedding_provider": {
                    "provider": "openai",
                    "model": "text-embedding-3-small",
                    "dimension": 1536
                },
                "bedrock": {
                    "region": "us-east-1",
                    "model": "amazon.nova-pro-v1:0",
                    "max_tokens": 4096,
                    "aws_access_key_id": "",
                    "aws_secret_access_key": ""
                },
                "openai": {
                    "api_key": "",
                    "model": "gpt-4o-mini",
                    "max_tokens": 4096,
                    "temperature": 0.1
                },
                "gemini": {
                    "api_key": "",
                    "model": "gemini-2.0-flash-exp",
                    "max_tokens": 1000000,
                    "temperature": 0.1
                }
            },
            "mcp_search": {
                "enabled_tools": ["tavily", "perplexity"],
                "default_tool": "tavily",
                "max_results_per_tool": 10,
                "timeout_seconds": 30.0,
                "enable_caching": True,
                "cache_ttl_seconds": 1800,
                "tavily": {
                    "api_key": "",
                    "search_depth": "basic",
                    "include_raw_content": True,
                    "max_results": 10
                },
                "perplexity": {
                    "api_key": "",
                    "model": "llama-3.1-sonar-small-128k-online",
                    "max_tokens": 4096,
                    "return_citations": True
                }
            },
            "infrastructure": {
                "http_client": {
                    "timeout_seconds": 30.0,
                    "max_connections": 100,
                    "max_keepalive_connections": 20
                },
                "rate_limiting": {
                    "enabled": True,
                    "requests_per_minute": 60,
                    "burst_size": 10
                }
            },
            "lifecycle": {
                "startup_timeout_seconds": 60.0,
                "shutdown_timeout_seconds": 30.0,
                "health_check_interval_seconds": 30.0
            },
            "health": {
                "enabled": True,
                "endpoint": "/health",
                "detailed_checks": True,
                "timeout_seconds": 10.0
            },
            "api_server": {
                "enabled": True,
                "host": "localhost",
                "port": 8000,
                "reload": False,
                "workers": 1
            },
            "cli": {
                "output_format": "json",
                "verbose": False,
                "progress_bars": True
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "handlers": ["console"],
                "file_path": "logs/theodore.log"
            },
            "monitoring": {
                "enabled": False,
                "metrics_endpoint": "/metrics",
                "tracing_enabled": False
            }
        }
        
        # Set configuration
        self.config.override(defaults)
    
    def _load_configuration(self) -> None:
        """Load configuration from files in hierarchical order."""
        try:
            # Load base configuration if exists
            base_config_path = self.config_path / "base.yml"
            if base_config_path.exists():
                self._load_config_file(base_config_path)
            
            # Load environment-specific configuration
            env_config_path = self.config_path / "environments" / f"{self.environment}.yml"
            if env_config_path.exists():
                self._load_config_file(env_config_path)
            
            # Load local overrides
            local_config_path = self.config_path / "local.yml"
            if local_config_path.exists():
                self._load_config_file(local_config_path)
                
        except Exception as e:
            self.logger.warning(f"Failed to load configuration files: {e}")
    
    def _load_config_file(self, config_file: Path) -> None:
        """Load configuration from a file."""
        try:
            with open(config_file, 'r') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    # Merge with existing config
                    current_config = self.config.get_config()
                    merged_config = self._deep_merge(current_config, file_config)
                    self.config.override(merged_config)
                    self.logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            self.logger.error(f"Failed to load config file {config_file}: {e}")
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def _inject_environment_variables(self) -> None:
        """Inject sensitive configuration from environment variables."""
        env_mappings = {
            # API Keys
            "OPENAI_API_KEY": ["ai_services", "openai", "api_key"],
            "GEMINI_API_KEY": ["ai_services", "gemini", "api_key"],
            "AWS_ACCESS_KEY_ID": ["ai_services", "bedrock", "aws_access_key_id"],
            "AWS_SECRET_ACCESS_KEY": ["ai_services", "bedrock", "aws_secret_access_key"],
            "BEDROCK_ANALYSIS_MODEL": ["ai_services", "bedrock", "model"],
            
            # Vector Storage
            "PINECONE_API_KEY": ["storage", "vector_storage", "api_key"],
            "PINECONE_INDEX_NAME": ["storage", "vector_storage", "index_name"],
            "PINECONE_ENVIRONMENT": ["storage", "vector_storage", "environment"],
            
            # MCP Search Tools
            "TAVILY_API_KEY": ["mcp_search", "tavily", "api_key"],
            "PERPLEXITY_API_KEY": ["mcp_search", "perplexity", "api_key"],
            
            # Application
            "LOG_LEVEL": ["logging", "level"],
            "DEBUG": ["app", "debug"],
            "API_PORT": ["api_server", "port"],
            "API_HOST": ["api_server", "host"],
        }
        
        current_config = self.config.get_config()
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Apply environment variable to config
                self._set_nested_value(current_config, config_path, value)
        
        # Update configuration
        self.config.override(current_config)
    
    def _set_nested_value(self, config: Dict[str, Any], path: list, value: Any) -> None:
        """Set nested configuration value."""
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def validate(self) -> Dict[str, Any]:
        """Validate configuration."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            config_data = self.config.get_config()
            
            # Check required fields
            required_fields = [
                ["storage", "vector_storage", "api_key"],
                ["ai_services", "llm_provider", "primary"]
            ]
            
            for field_path in required_fields:
                if not self._get_nested_value(config_data, field_path):
                    validation_result["warnings"].append(
                        f"Missing configuration: {'.'.join(field_path)}"
                    )
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Configuration validation failed: {e}")
        
        return validation_result
    
    def _get_nested_value(self, config: Dict[str, Any], path: list) -> Any:
        """Get nested configuration value."""
        current = config
        for key in path:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        return current
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration."""
        try:
            config_data = self.config.get_config()
            return {
                "environment": self.environment,
                "config_path": str(self.config_path),
                "app": config_data.get("app", {}),
                "providers": {
                    "vector_storage": config_data.get("storage", {}).get("vector_storage", {}).get("provider"),
                    "llm_primary": config_data.get("ai_services", {}).get("llm_provider", {}).get("primary"),
                    "mcp_tools": config_data.get("mcp_search", {}).get("enabled_tools", [])
                }
            }
        except Exception as e:
            return {"error": str(e)}


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass