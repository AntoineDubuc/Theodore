"""
Configuration validation utilities for Theodore.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import yaml
import json
from urllib.parse import urlparse


class ConfigValidator:
    """Configuration validation utilities"""
    
    @staticmethod
    def validate_api_key_format(key: str, provider: str) -> Tuple[bool, str]:
        """
        Validate API key format for different providers.
        
        Args:
            key: The API key to validate
            provider: The provider name (aws, gemini, openai, etc.)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not key or not key.strip():
            return False, f"{provider} API key cannot be empty"
        
        key = key.strip()
        
        # Provider-specific validation
        if provider.lower() == "openai":
            if not key.startswith("sk-"):
                return False, "OpenAI API keys must start with 'sk-'"
            if len(key) < 20:
                return False, "OpenAI API key is too short"
                
        elif provider.lower() == "gemini":
            if not key.startswith("AIza"):
                return False, "Gemini API keys typically start with 'AIza'"
            if len(key) < 20:
                return False, "Gemini API key is too short"
                
        elif provider.lower() == "aws":
            # AWS access keys are typically 20 characters, all uppercase
            if len(key) != 20:
                return False, "AWS access key ID should be 20 characters"
            if not key.isupper():
                return False, "AWS access key ID should be uppercase"
                
        elif provider.lower() == "pinecone":
            # Pinecone keys are UUIDs or similar
            if len(key) < 32:
                return False, "Pinecone API key appears too short"
        
        # General validation
        if len(key) > 200:
            return False, f"{provider} API key is suspiciously long"
            
        # Check for obvious test/placeholder values
        placeholder_patterns = [
            "your_api_key", "replace_me", "test_key", "example",
            "placeholder", "dummy", "fake", "mock"
        ]
        
        for pattern in placeholder_patterns:
            if pattern.lower() in key.lower():
                return False, f"{provider} API key appears to be a placeholder"
        
        return True, ""
    
    @staticmethod
    def validate_aws_region(region: str) -> Tuple[bool, str]:
        """
        Validate AWS region format.
        
        Args:
            region: AWS region string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not region:
            return False, "AWS region cannot be empty"
        
        # AWS region pattern: us-west-2, eu-central-1, etc.
        region_pattern = r'^[a-z0-9]+-[a-z0-9]+-[0-9]+$'
        
        if not re.match(region_pattern, region):
            return False, f"Invalid AWS region format: {region} (expected format: us-west-2)"
        
        # Known AWS regions (partial list for validation)
        known_regions = [
            "us-east-1", "us-east-2", "us-west-1", "us-west-2",
            "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1",
            "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
            "ca-central-1", "sa-east-1", "af-south-1",
            "ap-south-1", "eu-north-1", "me-south-1"
        ]
        
        if region not in known_regions:
            return True, f"Warning: {region} is not a commonly known AWS region"
        
        return True, ""
    
    @staticmethod
    def validate_model_name(model: str, provider: str) -> Tuple[bool, str]:
        """
        Validate AI model name for provider.
        
        Args:
            model: Model name
            provider: Provider name
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not model:
            return False, f"{provider} model name cannot be empty"
        
        # Provider-specific model validation
        if provider.lower() == "gemini":
            valid_models = [
                "gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash",
                "gemini-pro", "gemini-pro-vision"
            ]
            if model not in valid_models:
                return False, f"Unknown Gemini model: {model}"
                
        elif provider.lower() == "openai":
            valid_models = [
                "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini",
                "gpt-3.5-turbo", "text-embedding-3-large", "text-embedding-3-small"
            ]
            if model not in valid_models:
                return False, f"Unknown OpenAI model: {model}"
                
        elif provider.lower() == "bedrock":
            if not (model.startswith("amazon.") or model.startswith("anthropic.") or 
                   model.startswith("meta.") or model.startswith("ai21.")):
                return False, f"Bedrock model should start with provider prefix: {model}"
        
        return True, ""
    
    @staticmethod
    def validate_config_file(file_path: Path) -> Tuple[bool, str, Optional[Dict]]:
        """
        Validate configuration file format and content.
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            Tuple of (is_valid, error_message, parsed_config)
        """
        if not file_path.exists():
            return False, f"Configuration file not found: {file_path}", None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                return False, "Configuration file is empty", None
            
            # Try to parse as YAML first, then JSON
            try:
                config = yaml.safe_load(content)
            except yaml.YAMLError:
                try:
                    config = json.loads(content)
                except json.JSONDecodeError as e:
                    return False, f"Invalid YAML/JSON format: {e}", None
            
            if not isinstance(config, dict):
                return False, "Configuration must be a dictionary/object", None
            
            return True, "", config
            
        except Exception as e:
            return False, f"Error reading configuration file: {e}", None
    
    @staticmethod
    def validate_environment_setup(config: Dict[str, Any]) -> List[str]:
        """
        Validate overall environment setup and return warnings/issues.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            List of validation messages (warnings and errors)
        """
        issues = []
        
        # Check for required credentials
        ai_providers = [
            config.get('gemini_api_key'),
            config.get('aws_access_key_id') and config.get('aws_secret_access_key'),
            config.get('openai_api_key')
        ]
        
        if not any(ai_providers):
            issues.append("ERROR: No AI provider credentials found. Configure Gemini, AWS, or OpenAI.")
        
        if not config.get('pinecone_api_key'):
            issues.append("ERROR: Pinecone API key is required for vector storage.")
        
        # Check for development vs production settings
        environment = config.get('environment', 'development')
        debug = config.get('debug', False)
        
        if environment == 'production' and debug:
            issues.append("WARNING: Debug mode is enabled in production environment.")
        
        if environment == 'development' and not debug:
            issues.append("INFO: Debug mode is disabled in development environment.")
        
        # Check MCP tools configuration
        mcp_tools = config.get('mcp_tools_enabled', [])
        for tool in mcp_tools:
            if tool == 'perplexity' and not config.get('perplexity_api_key'):
                issues.append(f"WARNING: {tool} MCP tool is enabled but API key is missing.")
            elif tool == 'tavily' and not config.get('tavily_api_key'):
                issues.append(f"WARNING: {tool} MCP tool is enabled but API key is missing.")
        
        # Check research settings
        research_config = config.get('research', {})
        max_pages = research_config.get('max_pages_per_company', 50)
        if max_pages > 100:
            issues.append("WARNING: max_pages_per_company is very high, may impact performance.")
        
        parallel_requests = research_config.get('parallel_requests', 5)
        if parallel_requests > 20:
            issues.append("WARNING: parallel_requests is very high, may hit rate limits.")
        
        return issues
    
    @staticmethod
    def generate_config_template() -> str:
        """
        Generate a configuration file template with comments.
        
        Returns:
            YAML configuration template as string
        """
        template = """# Theodore AI Company Intelligence Configuration
# Copy this file to ~/.theodore/config.yml and customize

# Application Environment
environment: development  # development, staging, production
debug: false
log_level: INFO
verbose: false

# AI Provider Configuration
# Configure at least one AI provider

# Google Gemini (Recommended)
gemini_api_key: null  # Get from https://aistudio.google.com/
gemini_model: "gemini-2.0-flash-exp"

# AWS Bedrock (Cost-optimized)
aws_region: "us-west-2"
aws_access_key_id: null
aws_secret_access_key: null
bedrock_analysis_model: "amazon.nova-pro-v1:0"

# OpenAI (Fallback)
openai_api_key: null  # Get from https://platform.openai.com/
openai_model: "gpt-4o-mini"

# Vector Database (Required)
pinecone_api_key: null  # Get from https://pinecone.io/
pinecone_index_name: "theodore-companies"
pinecone_environment: "us-west1-gcp-free"

# MCP Search Tools (Optional)
mcp_tools_enabled:
  - perplexity
  - tavily
perplexity_api_key: null
tavily_api_key: null

# Research Configuration
research:
  max_pages_per_company: 50
  timeout_seconds: 30
  parallel_requests: 5
  enable_javascript: true
  respect_robots_txt: true
  primary_analysis_model: "gemini-2.0-flash-exp"
  cost_optimization_enabled: true
  max_cost_per_company: 5.0

# Search and Discovery
search:
  default_similarity_limit: 10
  min_confidence_threshold: 0.5
  enable_mcp_search: true
  enable_google_fallback: true

# Storage and Caching
storage:
  cache_enabled: true
  cache_ttl_hours: 24
  backup_enabled: true
  max_backup_files: 10

# Output Configuration
default_output_format: table  # table, json, csv
colored_output: true
progress_bars: true

# Security
enable_secure_storage: true  # Use system keyring for credentials
"""
        return template
    
    @staticmethod
    def validate_complete_config(config_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Perform comprehensive validation of configuration.
        
        Args:
            config_dict: Complete configuration dictionary
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # API key validation
        api_keys = {
            'gemini_api_key': 'gemini',
            'openai_api_key': 'openai',
            'pinecone_api_key': 'pinecone',
            'perplexity_api_key': 'perplexity',
            'tavily_api_key': 'tavily'
        }
        
        for key_name, provider in api_keys.items():
            key_value = config_dict.get(key_name)
            if key_value:
                is_valid, error = ConfigValidator.validate_api_key_format(key_value, provider)
                if not is_valid:
                    issues.append(f"ERROR: {error}")
        
        # AWS specific validation
        aws_key = config_dict.get('aws_access_key_id')
        if aws_key:
            is_valid, error = ConfigValidator.validate_api_key_format(aws_key, 'aws')
            if not is_valid:
                issues.append(f"ERROR: {error}")
        
        # Region validation
        aws_region = config_dict.get('aws_region')
        if aws_region:
            is_valid, error = ConfigValidator.validate_aws_region(aws_region)
            if not is_valid:
                issues.append(f"ERROR: {error}")
            elif error:  # Warning
                issues.append(f"WARNING: {error}")
        
        # Environment-specific validation
        env_issues = ConfigValidator.validate_environment_setup(config_dict)
        issues.extend(env_issues)
        
        # Determine if config is valid (no ERROR-level issues)
        has_errors = any(issue.startswith("ERROR:") for issue in issues)
        
        return not has_errors, issues