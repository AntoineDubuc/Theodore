# TICKET-003: Configuration Management System

## Overview
Create a robust configuration system that handles environment variables, config files, and CLI overrides.

## Acceptance Criteria
- [ ] Load configuration from multiple sources (env, .theodore.yml, CLI args)
- [ ] Implement configuration precedence: CLI > env > file > defaults
- [ ] Secure storage for API keys using keyring library
- [ ] Configuration validation with helpful error messages
- [ ] `theodore config` commands to get/set values
- [ ] Auto-generate .theodore.yml template on first run

## Technical Details
- Use Pydantic Settings for configuration management
- Store user config in `~/.theodore/config.yml`
- Use python-keyring for secure credential storage
- Support both JSON and YAML config formats

## Testing
- Test configuration loading from all sources
- Test precedence order works correctly
- Test with real API keys (in secure storage)
- Test validation with invalid configurations
- Manual test:
  ```bash
  theodore config set aws.region us-west-2
  theodore config get aws.region
  theodore config list
  ```

## Estimated Time: 3-4 hours

## Dependencies
- TICKET-002 (for CLI commands)

## Files to Create
- `v2/src/infrastructure/config/__init__.py`
- `v2/src/infrastructure/config/settings.py`
- `v2/src/infrastructure/config/secure_storage.py`
- `v2/src/infrastructure/config/validators.py`
- `v2/src/cli/commands/config.py` (update from stub)
- `v2/tests/unit/config/test_settings.py`
- `v2/tests/unit/config/test_secure_storage.py`
- `v2/config/theodore.yml.example`

---

# Udemy Tutorial Script: Building Production-Ready Configuration Management

## Introduction (3 minutes)

**[SLIDE 1: Title - "Configuration Management for Production Applications"]**

"Welcome to this essential tutorial on building robust configuration management systems! Today we'll create a production-ready configuration system that handles multiple sources, secure credentials, and validation - all the things you need for real-world applications.

By the end of this tutorial, you'll know how to build configuration systems that are secure, flexible, and maintainable. We'll use Pydantic Settings, environment variables, config files, and secure credential storage to create something enterprise-ready.

This is the foundation that makes your application deployable anywhere!"

## Section 1: Understanding Configuration Complexity (5 minutes)

**[SLIDE 2: The Configuration Challenge]**

"Let's start by understanding why configuration is complex in modern applications:

```python
# ❌ The NAIVE way - hardcoded values
API_KEY = "sk-1234567890abcdef"  # Security nightmare!
DATABASE_URL = "localhost:5432"   # Won't work in production!
DEBUG = True                      # Oops, left debug on in prod!

# This doesn't scale and it's not secure!
```

**[SLIDE 3: Real-World Configuration Needs]**

Modern applications need:
- **Multiple Environments**: Dev, staging, production
- **Multiple Sources**: Files, environment variables, CLI args
- **Security**: API keys shouldn't be in code
- **Validation**: Catch config errors early
- **Precedence**: CLI overrides env vars, env vars override files
- **Defaults**: Sensible fallbacks for everything

**[SLIDE 4: Configuration Sources Hierarchy]**

```
CLI Arguments        (Highest Priority)
    ↓
Environment Variables
    ↓  
Config Files (.theodore.yml)
    ↓
Default Values       (Lowest Priority)
```

**[THE GOAL]** Build a system where this works seamlessly:
```bash
# Set in config file
theodore config set aws.region us-west-2

# Override with environment variable
export THEODORE_AWS_REGION=us-east-1

# Override with CLI flag
theodore research --aws-region eu-west-1 "Stripe"
```"

## Section 2: Project Architecture and Setup (6 minutes)

**[SLIDE 5: Configuration Architecture]**

"Let's design our configuration system architecture:

```
v2/src/infrastructure/config/
├── __init__.py              # Configuration exports
├── settings.py              # Pydantic Settings classes
├── secure_storage.py        # Keyring integration for secrets
├── validators.py            # Custom validation logic
└── loaders.py              # Configuration loading logic

v2/config/
├── theodore.yml.example     # Example configuration
└── schemas/                 # JSON schemas for validation
```

**[TERMINAL DEMO]**
```bash
# Create the structure
mkdir -p v2/src/infrastructure/config
mkdir -p v2/config/schemas

# Install dependencies
pip install "pydantic[settings]>=2.0" "pyyaml>=6.0" "keyring>=24.0"

# Verify installations
python -c "import pydantic_settings; print('Pydantic Settings ready!')"
python -c "import keyring; print('Keyring ready!')"
```

**[SLIDE 6: Configuration Design Principles]**

Our system follows these principles:
1. **Security First**: Secrets never in plain text
2. **Environment Aware**: Different configs for different environments  
3. **Validation Early**: Fail fast with clear error messages
4. **Developer Friendly**: Easy to set up and modify
5. **Production Ready**: Works in containers, CI/CD, etc.
6. **Precedence Clear**: CLI > Env > File > Defaults"

## Section 3: Building the Core Settings (12 minutes)

**[SLIDE 7: Pydantic Settings Foundation]**

"Let's start with our main configuration class:

```python
# v2/src/infrastructure/config/settings.py

from pydantic import BaseSettings, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List, Dict, Any
from pathlib import Path
import os
from enum import Enum

class Environment(str, Enum):
    \"\"\"Application environments\"\"\"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

class LogLevel(str, Enum):
    \"\"\"Logging levels\"\"\"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class TheodoreSettings(BaseSettings):
    \"\"\"
    Theodore application configuration with multiple source support.
    
    Configuration sources (in order of precedence):
    1. CLI arguments (handled by Click)
    2. Environment variables (THEODORE_*)
    3. Configuration files (.theodore.yml)
    4. Default values
    \"\"\"
    
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
        case_sensitive=False
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
    
    # API Configuration
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
        description="AWS secret access key (use secure storage)"
    )
    
    # Google AI
    gemini_api_key: Optional[str] = Field(
        default=None,
        description="Google Gemini API key"
    )
    
    # Vector Database
    pinecone_api_key: Optional[str] = Field(
        default=None,
        description="Pinecone API key"
    )
    
    pinecone_index_name: str = Field(
        default="theodore-companies",
        description="Pinecone index name"
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
```

**[EXPLANATION]** "Key features here:
- `env_prefix='THEODORE_'` means `aws_region` becomes `THEODORE_AWS_REGION`
- Multiple file locations are checked automatically
- Enums provide type safety for known values
- Field descriptions become documentation"

**[SLIDE 8: Advanced Configuration Fields]**

"Let's add more sophisticated configuration options:

```python
    # Research Configuration
    max_pages_to_scrape: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum pages to scrape per company"
    )
    
    research_timeout_seconds: int = Field(
        default=300,
        ge=30,
        le=3600,
        description="Research timeout in seconds"
    )
    
    concurrent_research_limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum concurrent research jobs"
    )
    
    # Cache Configuration
    cache_enabled: bool = Field(
        default=True,
        description="Enable result caching"
    )
    
    cache_ttl_seconds: int = Field(
        default=3600,
        ge=60,
        description="Cache time-to-live in seconds"
    )
    
    # Output Configuration
    default_output_format: str = Field(
        default="table",
        regex=r"^(table|json|csv|yaml)$",
        description="Default output format for CLI"
    )
    
    export_directory: Path = Field(
        default=Path("./exports"),
        description="Default directory for exports"
    )
    
    # Security Configuration  
    use_secure_storage: bool = Field(
        default=True,
        description="Store API keys in system keyring"
    )
    
    allowed_domains: List[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed domains for web scraping"
    )
    
    # Plugin Configuration
    plugin_directory: Path = Field(
        default=Path("~/.theodore/plugins").expanduser(),
        description="Directory for user plugins"
    )
    
    custom_mcp_tools: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Custom MCP tool configurations"
    )
```

**[VALIDATION POWER]** "Notice the validation:
- `ge=1, le=200` means 'greater than 1, less than 200'  
- `regex` patterns validate string formats
- `Path` objects handle file paths correctly
- Lists and Dicts support complex nested config"

**[SLIDE 9: Custom Validators]**

"Let's add custom validation logic:

```python
    @validator('environment')
    def validate_environment(cls, v):
        \"\"\"Ensure environment is properly configured\"\"\"
        if v == Environment.PRODUCTION:
            # In production, certain security checks are required
            pass  # We'll implement security validators later
        return v
    
    @validator('export_directory')
    def validate_export_directory(cls, v):
        \"\"\"Ensure export directory exists or can be created\"\"\"
        path = Path(v).expanduser().resolve()
        
        # Try to create directory if it doesn't exist
        try:
            path.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise ValueError(f"Cannot create export directory: {path}")
        
        return path
    
    @validator('mcp_tools_enabled')
    def validate_mcp_tools(cls, v):
        \"\"\"Validate MCP tools are known\"\"\"
        known_tools = ["perplexity", "tavily", "google_search", "custom"]
        
        for tool in v:
            if tool not in known_tools:
                raise ValueError(f"Unknown MCP tool: {tool}. Known tools: {known_tools}")
        
        return v
    
    @validator('aws_region')
    def validate_aws_region(cls, v):
        \"\"\"Validate AWS region format\"\"\"
        import re
        if not re.match(r'^[a-z]+-[a-z]+-\d+$', v):
            raise ValueError(f"Invalid AWS region format: {v}")
        return v
    
    def validate_api_keys(self) -> 'TheodoreSettings':
        \"\"\"Validate that required API keys are present\"\"\"
        required_keys = []
        
        if 'perplexity' in self.mcp_tools_enabled and not self.perplexity_api_key:
            required_keys.append('perplexity_api_key')
        
        if 'tavily' in self.mcp_tools_enabled and not self.tavily_api_key:
            required_keys.append('tavily_api_key')
        
        if not self.pinecone_api_key:
            required_keys.append('pinecone_api_key')
        
        if required_keys:
            raise ValueError(f"Missing required API keys: {required_keys}")
        
        return self
    
    @property
    def is_production(self) -> bool:
        \"\"\"Check if running in production\"\"\"
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        \"\"\"Check if running in development\"\"\"
        return self.environment == Environment.DEVELOPMENT
```

**[PAUSE POINT]** "Take a moment to implement these validators. Notice how they provide clear, actionable error messages!"

## Section 4: Secure Credential Storage (10 minutes)

**[SLIDE 10: The Security Problem]**

"Storing API keys in plain text is a security nightmare:

```yaml
# ❌ NEVER do this - keys in plain text!
aws:
  access_key: AKIA1234567890ABCDEF
  secret_key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# ✅ DO this - reference to secure storage
aws:
  access_key: ${keyring:aws:access_key}
  secret_key: ${keyring:aws:secret_key}
```

**[SLIDE 11: Keyring Integration]**

"Let's build secure credential storage:

```python
# v2/src/infrastructure/config/secure_storage.py

import keyring
import keyring.backends
from keyring.backends import SecretService, macOS, Windows
from typing import Optional, Dict, Any
import json
import os
import warnings

class SecureCredentialStore:
    \"\"\"
    Secure credential storage using system keyring.
    
    Supports:
    - macOS Keychain
    - Windows Credential Manager  
    - Linux Secret Service (GNOME Keyring, KWallet)
    - Fallback to encrypted file storage
    \"\"\"
    
    def __init__(self, service_name: str = "theodore-ai"):
        self.service_name = service_name
        self._ensure_keyring_available()
    
    def _ensure_keyring_available(self):
        \"\"\"Ensure keyring backend is available\"\"\"
        backend = keyring.get_keyring()
        
        # Check if we have a secure backend
        if isinstance(backend, keyring.backends.fail.Keyring):
            warnings.warn(
                "No secure keyring backend available. "
                "Credentials will be stored in plain text. "
                "Consider installing: pip install keyring[completion]"
            )
    
    def store_credential(self, key: str, value: str) -> None:
        \"\"\"Store a credential securely\"\"\"
        try:
            keyring.set_password(self.service_name, key, value)
            print(f"✅ Stored credential: {key}")
        except Exception as e:
            raise RuntimeError(f"Failed to store credential {key}: {e}")
    
    def get_credential(self, key: str) -> Optional[str]:
        \"\"\"Retrieve a credential securely\"\"\"
        try:
            return keyring.get_password(self.service_name, key)
        except Exception as e:
            warnings.warn(f"Failed to retrieve credential {key}: {e}")
            return None
    
    def delete_credential(self, key: str) -> bool:
        \"\"\"Delete a credential\"\"\"
        try:
            keyring.delete_password(self.service_name, key)
            return True
        except Exception:
            return False
    
    def list_credentials(self) -> List[str]:
        \"\"\"List stored credential keys (not values!)\"\"\"
        # This is backend-dependent and not always supported
        try:
            # Try to get credentials list if backend supports it
            backend = keyring.get_keyring()
            if hasattr(backend, 'list_credentials'):
                return backend.list_credentials(self.service_name)
        except Exception:
            pass
        
        # Fallback: return known credential keys
        return self._get_known_credential_keys()
    
    def _get_known_credential_keys(self) -> List[str]:
        \"\"\"Get list of known credential keys\"\"\"
        return [
            'aws_access_key_id',
            'aws_secret_access_key', 
            'gemini_api_key',
            'pinecone_api_key',
            'perplexity_api_key',
            'tavily_api_key'
        ]
    
    def store_multiple_credentials(self, credentials: Dict[str, str]) -> None:
        \"\"\"Store multiple credentials at once\"\"\"
        for key, value in credentials.items():
            if value:  # Only store non-empty values
                self.store_credential(key, value)
    
    def get_all_credentials(self) -> Dict[str, Optional[str]]:
        \"\"\"Get all known credentials\"\"\"
        credentials = {}
        for key in self._get_known_credential_keys():
            credentials[key] = self.get_credential(key)
        return credentials
    
    def export_credentials_safely(self) -> Dict[str, str]:
        \"\"\"Export credentials with masked values for display\"\"\"
        credentials = {}
        for key in self._get_known_credential_keys():
            value = self.get_credential(key)
            if value:
                # Mask the value for safe display
                if len(value) > 8:
                    masked = value[:4] + '*' * (len(value) - 8) + value[-4:]
                else:
                    masked = '*' * len(value)
                credentials[key] = masked
            else:
                credentials[key] = "Not set"
        return credentials

# Singleton instance
credential_store = SecureCredentialStore()
```

**[SLIDE 12: Integrating Secure Storage with Settings]**

"Now let's integrate secure storage with our settings:

```python
# Add to settings.py

from .secure_storage import credential_store

class TheodoreSettings(BaseSettings):
    # ... existing fields ...
    
    def __init__(self, **kwargs):
        # Load credentials from secure storage if not provided
        self._load_secure_credentials(kwargs)
        super().__init__(**kwargs)
    
    def _load_secure_credentials(self, kwargs: Dict[str, Any]):
        \"\"\"Load credentials from secure storage\"\"\"
        if not self.use_secure_storage:
            return
        
        credential_mappings = {
            'aws_access_key_id': 'aws_access_key_id',
            'aws_secret_access_key': 'aws_secret_access_key',
            'gemini_api_key': 'gemini_api_key',
            'pinecone_api_key': 'pinecone_api_key',
            'perplexity_api_key': 'perplexity_api_key',
            'tavily_api_key': 'tavily_api_key'
        }
        
        for field_name, credential_key in credential_mappings.items():
            # Only load from keyring if not provided via env/file/kwargs
            if field_name not in kwargs:
                stored_value = credential_store.get_credential(credential_key)
                if stored_value:
                    kwargs[field_name] = stored_value
    
    def store_credentials_securely(self):
        \"\"\"Store current credentials in secure storage\"\"\"
        if not self.use_secure_storage:
            return
        
        credentials = {
            'aws_access_key_id': self.aws_access_key_id,
            'aws_secret_access_key': self.aws_secret_access_key,
            'gemini_api_key': self.gemini_api_key,
            'pinecone_api_key': self.pinecone_api_key,
            'perplexity_api_key': self.perplexity_api_key,
            'tavily_api_key': self.tavily_api_key
        }
        
        # Only store non-None values
        filtered_credentials = {k: v for k, v in credentials.items() if v}
        credential_store.store_multiple_credentials(filtered_credentials)
    
    def get_credential_status(self) -> Dict[str, str]:
        \"\"\"Get status of all credentials\"\"\"
        return credential_store.export_credentials_safely()
```

**[SECURITY NOTE]** "This system automatically loads API keys from secure storage, but you can override with environment variables or CLI args when needed!"

## Section 5: Configuration File Handling (8 minutes)

**[SLIDE 13: Configuration File Formats]**

"Let's create a beautiful configuration file template:

```yaml
# v2/config/theodore.yml.example

# Theodore AI Company Intelligence Configuration
# Copy this file to ~/.theodore/config.yml and customize

# Application Settings
environment: development
debug: false
log_level: INFO

# AWS Configuration for Bedrock
aws:
  region: us-west-2
  # Credentials stored securely in keyring
  # Use: theodore config set-secure aws_access_key_id YOUR_KEY

# Google AI Configuration  
google:
  # Gemini API key stored securely
  # Use: theodore config set-secure gemini_api_key YOUR_KEY

# Vector Database Configuration
pinecone:
  index_name: theodore-companies
  # API key stored securely
  # Use: theodore config set-secure pinecone_api_key YOUR_KEY

# MCP Tools Configuration
mcp_tools:
  enabled:
    - perplexity
    - tavily
  
  # Individual tool settings
  perplexity:
    model: sonar-medium-online
    search_recency: month
    
  tavily:
    search_depth: advanced
    include_domains:
      - techcrunch.com
      - bloomberg.com
      - reuters.com

# Research Configuration
research:
  max_pages_to_scrape: 50
  timeout_seconds: 300
  concurrent_limit: 5

# Cache Configuration
cache:
  enabled: true
  ttl_seconds: 3600

# Output Configuration
output:
  default_format: table
  export_directory: ./exports

# Security Configuration
security:
  use_secure_storage: true
  allowed_domains:
    - "*"  # Allow all domains (use with caution)

# Plugin Configuration
plugins:
  directory: ~/.theodore/plugins
  custom_mcp_tools: {}
```

**[SLIDE 14: Configuration Loaders]**

"Let's build smart configuration loaders:

```python
# v2/src/infrastructure/config/loaders.py

import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import os

class ConfigurationLoader:
    \"\"\"Load configuration from multiple sources with proper precedence\"\"\"
    
    def __init__(self):
        self.config_paths = [
            Path('.theodore.yml'),
            Path('.theodore.yaml'),
            Path('~/.theodore/config.yml').expanduser(),
            Path('/etc/theodore/config.yml')
        ]
    
    def load_configuration(self) -> Dict[str, Any]:
        \"\"\"Load configuration with proper precedence\"\"\"
        config = {}
        
        # Start with defaults
        config.update(self._get_default_config())
        
        # Load from configuration files (in order)
        for config_path in self.config_paths:
            if config_path.exists():
                file_config = self._load_config_file(config_path)
                config = self._deep_merge(config, file_config)
                print(f"📄 Loaded config from: {config_path}")
        
        # Environment variables are handled by Pydantic Settings
        # CLI arguments are handled by Click
        
        return config
    
    def _load_config_file(self, path: Path) -> Dict[str, Any]:
        \"\"\"Load a single configuration file\"\"\"
        try:
            content = path.read_text(encoding='utf-8')
            
            if path.suffix in ['.yml', '.yaml']:
                return yaml.safe_load(content) or {}
            elif path.suffix == '.json':
                return json.loads(content)
            else:
                raise ValueError(f"Unsupported config file format: {path.suffix}")
                
        except Exception as e:
            raise RuntimeError(f"Failed to load config from {path}: {e}")
    
    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Deep merge two dictionaries\"\"\"
        result = base.copy()
        
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _get_default_config(self) -> Dict[str, Any]:
        \"\"\"Get default configuration values\"\"\"
        return {
            'environment': 'development',
            'debug': False,
            'log_level': 'INFO',
            'aws': {
                'region': 'us-west-2'
            },
            'research': {
                'max_pages_to_scrape': 50,
                'timeout_seconds': 300,
                'concurrent_limit': 5
            },
            'cache': {
                'enabled': True,
                'ttl_seconds': 3600
            },
            'output': {
                'default_format': 'table',
                'export_directory': './exports'
            },
            'mcp_tools': {
                'enabled': ['perplexity', 'tavily']
            }
        }
    
    def create_example_config(self, path: Path) -> None:
        \"\"\"Create an example configuration file\"\"\"
        example_path = Path(__file__).parent.parent.parent.parent / 'config' / 'theodore.yml.example'
        
        if example_path.exists():
            # Copy example file
            import shutil
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(example_path, path)
            print(f"📄 Created config file: {path}")
        else:
            # Generate basic config
            self._generate_basic_config(path)
    
    def _generate_basic_config(self, path: Path) -> None:
        \"\"\"Generate a basic configuration file\"\"\"
        config = {
            'environment': 'development',
            'aws': {'region': 'us-west-2'},
            'research': {
                'max_pages_to_scrape': 50,
                'timeout_seconds': 300
            },
            'mcp_tools': {
                'enabled': ['perplexity', 'tavily']
            }
        }
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        print(f"📄 Generated basic config: {path}")

# Singleton loader
config_loader = ConfigurationLoader()
```

**[PRACTICAL TIP]** "The deep merge function is crucial - it lets you override just part of nested configurations!"

## Section 6: CLI Configuration Commands (10 minutes)

**[SLIDE 15: Enhanced Configuration CLI]**

"Let's build powerful CLI commands for configuration:

```python
# v2/src/cli/commands/config.py (Enhanced version)

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from pathlib import Path
import yaml
import json

from ...infrastructure.config.settings import TheodoreSettings
from ...infrastructure.config.secure_storage import credential_store
from ...infrastructure.config.loaders import config_loader

console = Console()

@click.group(name='config')
def config_group():
    \"\"\"Manage Theodore configuration and credentials\"\"\"
    pass

@config_group.command()
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']), default='table')
@click.option('--show-secure', is_flag=True, help='Show secure credential status')
def show(format: str, show_secure: bool):
    \"\"\"Show current configuration\"\"\"
    try:
        settings = TheodoreSettings()
        
        if format == 'table':
            _display_config_table(settings, show_secure)
        elif format == 'json':
            _display_config_json(settings, show_secure)
        elif format == 'yaml':
            _display_config_yaml(settings, show_secure)
            
    except Exception as e:
        console.print(f"[red]Error loading configuration: {e}[/red]")

def _display_config_table(settings: TheodoreSettings, show_secure: bool):
    \"\"\"Display configuration as a table\"\"\"
    table = Table(title="Theodore Configuration")
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")
    table.add_column("Source", style="dim")
    
    # Core settings
    table.add_row("Environment", settings.environment, "config/env")
    table.add_row("Debug Mode", str(settings.debug), "config/env")
    table.add_row("Log Level", settings.log_level, "config/env")
    
    # AWS settings
    table.add_row("AWS Region", settings.aws_region, "config/env")
    
    # Research settings
    table.add_row("Max Pages", str(settings.max_pages_to_scrape), "config")
    table.add_row("Timeout", f"{settings.research_timeout_seconds}s", "config")
    table.add_row("Concurrent Limit", str(settings.concurrent_research_limit), "config")
    
    # MCP Tools
    table.add_row("MCP Tools", ", ".join(settings.mcp_tools_enabled), "config")
    
    console.print(table)
    
    # Show secure credentials if requested
    if show_secure:
        _display_credential_status()

def _display_credential_status():
    \"\"\"Display secure credential status\"\"\"
    credentials = credential_store.export_credentials_safely()
    
    cred_table = Table(title="Secure Credentials Status")
    cred_table.add_column("Credential", style="cyan")
    cred_table.add_column("Status", style="magenta")
    
    for key, value in credentials.items():
        status_color = "green" if value != "Not set" else "red"
        cred_table.add_row(
            key.replace('_', ' ').title(),
            f"[{status_color}]{value}[/{status_color}]"
        )
    
    console.print("\\n")
    console.print(cred_table)

@config_group.command()
@click.argument('key')
@click.argument('value')
@click.option('--global', 'is_global', is_flag=True, help='Set in global config')
@click.option('--secure', is_flag=True, help='Store securely in keyring')
def set(key: str, value: str, is_global: bool, secure: bool):
    \"\"\"Set a configuration value\"\"\"
    if secure:
        # Store in secure storage
        try:
            credential_store.store_credential(key, value)
            console.print(f"[green]✅ Securely stored: {key}[/green]")
        except Exception as e:
            console.print(f"[red]❌ Failed to store securely: {e}[/red]")
        return
    
    # Store in configuration file
    config_path = _get_config_path(is_global)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing config
    config = {}
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
    
    # Set nested key
    _set_nested_value(config, key, value)
    
    # Save config
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)
    
    console.print(f"[green]✅ Set {key} = {value}[/green]")
    console.print(f"[dim]Config file: {config_path}[/dim]")

@config_group.command()
@click.argument('key')
def get(key: str):
    \"\"\"Get a configuration value\"\"\"
    try:
        settings = TheodoreSettings()
        
        # Try to get the value using dot notation
        value = _get_nested_value(settings.dict(), key)
        
        if value is not None:
            console.print(f"[cyan]{key}[/cyan]: [magenta]{value}[/magenta]")
        else:
            console.print(f"[yellow]Configuration key '{key}' not found[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

@config_group.command()
def validate():
    \"\"\"Validate current configuration\"\"\"
    try:
        settings = TheodoreSettings()
        console.print("[green]✅ Configuration is valid[/green]")
        
        # Additional validation checks
        validation_results = []
        
        # Check API key presence
        if settings.use_secure_storage:
            credentials = credential_store.get_all_credentials()
            missing_keys = [k for k, v in credentials.items() if not v]
            if missing_keys:
                validation_results.append(
                    f"⚠️  Missing secure credentials: {', '.join(missing_keys)}"
                )
        
        # Check file permissions
        export_dir = settings.export_directory
        if not export_dir.exists():
            validation_results.append(f"⚠️  Export directory will be created: {export_dir}")
        elif not os.access(export_dir, os.W_OK):
            validation_results.append(f"❌ No write permission to export directory: {export_dir}")
        
        # Display validation results
        if validation_results:
            console.print("\\n[bold]Validation Notes:[/bold]")
            for result in validation_results:
                console.print(result)
        
    except Exception as e:
        console.print(f"[red]❌ Configuration validation failed: {e}[/red]")

@config_group.command()
def init():
    \"\"\"Initialize configuration with interactive setup\"\"\"
    console.print("[bold blue]🚀 Theodore Configuration Setup[/bold blue]\\n")
    
    # Get configuration path
    config_path = Path.home() / '.theodore' / 'config.yml'
    
    if config_path.exists():
        if not Confirm.ask(f"Configuration exists at {config_path}. Overwrite?"):
            console.print("Setup cancelled.")
            return
    
    # Interactive configuration
    config = {}
    
    # Environment
    environment = Prompt.ask(
        "Environment", 
        choices=["development", "staging", "production"],
        default="development"
    )
    config['environment'] = environment
    
    # AWS Region
    aws_region = Prompt.ask("AWS Region", default="us-west-2")
    config['aws'] = {'region': aws_region}
    
    # MCP Tools
    console.print("\\n[bold]MCP Tools Configuration:[/bold]")
    mcp_tools = []
    
    if Confirm.ask("Enable Perplexity search?", default=True):
        mcp_tools.append("perplexity")
    
    if Confirm.ask("Enable Tavily search?", default=True):
        mcp_tools.append("tavily")
    
    config['mcp_tools'] = {'enabled': mcp_tools}
    
    # Research settings
    max_pages = Prompt.ask("Max pages to scrape per company", default="50")
    config['research'] = {
        'max_pages_to_scrape': int(max_pages),
        'timeout_seconds': 300,
        'concurrent_limit': 5
    }
    
    # Save configuration
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)
    
    console.print(f"\\n[green]✅ Configuration saved to {config_path}[/green]")
    
    # Offer to set up credentials
    if Confirm.ask("\\nSet up API credentials securely?", default=True):
        _setup_credentials_interactively()

def _setup_credentials_interactively():
    \"\"\"Interactive credential setup\"\"\"
    console.print("\\n[bold]API Credentials Setup:[/bold]")
    console.print("[dim]Credentials will be stored securely in your system keyring[/dim]\\n")
    
    credentials = [
        ('aws_access_key_id', 'AWS Access Key ID'),
        ('aws_secret_access_key', 'AWS Secret Access Key'),
        ('gemini_api_key', 'Google Gemini API Key'),
        ('pinecone_api_key', 'Pinecone API Key'),
        ('perplexity_api_key', 'Perplexity API Key'),
        ('tavily_api_key', 'Tavily API Key')
    ]
    
    for key, description in credentials:
        if Confirm.ask(f"Set {description}?", default=False):
            value = Prompt.ask(f"{description}", password=True)
            if value:
                credential_store.store_credential(key, value)
                console.print(f"[green]✅ Stored {description}[/green]")

def _get_config_path(is_global: bool) -> Path:
    \"\"\"Get configuration file path\"\"\"
    if is_global:
        return Path.home() / '.theodore' / 'config.yml'
    else:
        return Path.cwd() / '.theodore.yml'

def _set_nested_value(config: dict, key: str, value: str):
    \"\"\"Set a nested configuration value\"\"\"
    keys = key.split('.')
    current = config
    
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    
    # Try to parse value
    if value.lower() == 'true':
        current[keys[-1]] = True
    elif value.lower() == 'false':
        current[keys[-1]] = False
    elif value.isdigit():
        current[keys[-1]] = int(value)
    else:
        current[keys[-1]] = value

def _get_nested_value(config: dict, key: str):
    \"\"\"Get a nested configuration value\"\"\"
    keys = key.split('.')
    current = config
    
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return None
    
    return current
```

**[LIVE DEMO]** "Let's test our configuration system:
```bash
theodore config init
theodore config set aws.region us-east-1
theodore config set-secure aws_access_key_id YOUR_KEY
theodore config validate
theodore config show --show-secure
```"

## Section 7: Testing Configuration Systems (8 minutes)

**[SLIDE 16: Configuration Testing Strategy]**

"Testing configuration systems requires special techniques:

```python
# v2/tests/unit/config/test_settings.py

import pytest
import tempfile
import os
from pathlib import Path
import yaml

from infrastructure.config.settings import TheodoreSettings, Environment
from infrastructure.config.secure_storage import SecureCredentialStore

class TestTheodoreSettings:
    
    def test_default_settings(self):
        \"\"\"Test default configuration values\"\"\"
        settings = TheodoreSettings()
        
        assert settings.environment == Environment.DEVELOPMENT
        assert settings.aws_region == "us-west-2"
        assert settings.debug is False
        assert settings.max_pages_to_scrape == 50
        assert "perplexity" in settings.mcp_tools_enabled
    
    def test_environment_variable_override(self):
        \"\"\"Test environment variable precedence\"\"\"
        # Set environment variable
        os.environ['THEODORE_AWS_REGION'] = 'eu-west-1'
        os.environ['THEODORE_DEBUG'] = 'true'
        
        try:
            settings = TheodoreSettings()
            assert settings.aws_region == 'eu-west-1'
            assert settings.debug is True
        finally:
            # Clean up
            del os.environ['THEODORE_AWS_REGION']
            del os.environ['THEODORE_DEBUG']
    
    def test_config_file_loading(self):
        \"\"\"Test configuration file loading\"\"\"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            config = {
                'environment': 'production',
                'aws': {'region': 'ap-southeast-1'},
                'research': {'max_pages_to_scrape': 100}
            }
            yaml.dump(config, f)
            config_file = f.name
        
        try:
            # Test with explicit config file
            settings = TheodoreSettings(_env_file=config_file)
            assert settings.environment == Environment.PRODUCTION
            assert settings.aws_region == 'ap-southeast-1'
            assert settings.max_pages_to_scrape == 100
        finally:
            os.unlink(config_file)
    
    def test_validation_errors(self):
        \"\"\"Test configuration validation\"\"\"
        # Test invalid AWS region
        with pytest.raises(ValueError, match="Invalid AWS region"):
            TheodoreSettings(aws_region="invalid-region")
        
        # Test invalid page limit
        with pytest.raises(ValueError):
            TheodoreSettings(max_pages_to_scrape=0)
        
        # Test invalid MCP tool
        with pytest.raises(ValueError, match="Unknown MCP tool"):
            TheodoreSettings(mcp_tools_enabled=["unknown_tool"])
    
    def test_precedence_order(self):
        \"\"\"Test configuration precedence order\"\"\"
        # Create config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump({'aws': {'region': 'file-region'}}, f)
            config_file = f.name
        
        try:
            # Set environment variable (should override file)
            os.environ['THEODORE_AWS_REGION'] = 'env-region'
            
            settings = TheodoreSettings(_env_file=config_file)
            
            # Environment should override file
            assert settings.aws_region == 'env-region'
            
        finally:
            del os.environ['THEODORE_AWS_REGION']
            os.unlink(config_file)
    
    def test_secure_storage_integration(self):
        \"\"\"Test secure storage integration\"\"\"
        # Create test credential store
        test_store = SecureCredentialStore("test-theodore")
        
        # Store test credential
        test_store.store_credential("test_key", "test_value")
        
        try:
            # Retrieve credential
            value = test_store.get_credential("test_key")
            assert value == "test_value"
            
            # Test credential listing
            credentials = test_store.export_credentials_safely()
            assert "test_key" in credentials
            
        finally:
            # Clean up
            test_store.delete_credential("test_key")

class TestConfigurationValidation:
    
    def test_production_validation(self):
        \"\"\"Test additional validation in production\"\"\"
        settings = TheodoreSettings(environment="production")
        
        # Production should require certain security measures
        assert settings.is_production
        assert not settings.is_development
    
    def test_export_directory_creation(self):
        \"\"\"Test export directory validation and creation\"\"\"
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = Path(temp_dir) / "exports" / "nested"
            
            settings = TheodoreSettings(export_directory=str(export_path))
            
            # Directory should be created
            assert export_path.exists()
            assert export_path.is_dir()
    
    def test_api_key_validation(self):
        \"\"\"Test API key presence validation\"\"\"
        settings = TheodoreSettings(
            mcp_tools_enabled=["perplexity"],
            perplexity_api_key=None
        )
        
        # Should raise error about missing API key
        with pytest.raises(ValueError, match="Missing required API keys"):
            settings.validate_api_keys()

class TestConfigurationLoading:
    
    def test_multiple_config_file_formats(self):
        \"\"\"Test loading from different file formats\"\"\"
        # Test YAML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump({'environment': 'staging'}, f)
            yaml_file = f.name
        
        # Test JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump({'environment': 'production'}, f)
            json_file = f.name
        
        try:
            # Test YAML loading
            settings_yaml = TheodoreSettings(_env_file=yaml_file)
            assert settings_yaml.environment == Environment.STAGING
            
            # Test JSON loading
            settings_json = TheodoreSettings(_env_file=json_file)
            assert settings_json.environment == Environment.PRODUCTION
            
        finally:
            os.unlink(yaml_file)
            os.unlink(json_file)
    
    def test_configuration_merging(self):
        \"\"\"Test deep configuration merging\"\"\"
        from infrastructure.config.loaders import ConfigurationLoader
        
        loader = ConfigurationLoader()
        
        base_config = {
            'aws': {'region': 'us-west-2', 'timeout': 30},
            'research': {'max_pages': 50}
        }
        
        update_config = {
            'aws': {'region': 'eu-west-1'},  # Override region
            'cache': {'enabled': True}        # Add new section
        }
        
        merged = loader._deep_merge(base_config, update_config)
        
        # Should override region but keep timeout
        assert merged['aws']['region'] == 'eu-west-1'
        assert merged['aws']['timeout'] == 30
        
        # Should add new section
        assert merged['cache']['enabled'] is True
        
        # Should keep existing section
        assert merged['research']['max_pages'] == 50
```

**[TESTING TIPS]** "Key testing principles:
1. Test all configuration sources and precedence
2. Use temporary files for file-based tests
3. Clean up environment variables after tests
4. Test validation with both valid and invalid data
5. Mock external dependencies like keyring when needed"

## Section 8: Best Practices and Production Considerations (5 minutes)

**[SLIDE 17: Configuration Security Best Practices]**

"Essential security practices for configuration:

### 1. **Never Store Secrets in Code**
```python
# ❌ NEVER do this
API_KEY = "sk-1234567890abcdef"

# ✅ DO this - environment variable
API_KEY = os.getenv('API_KEY')

# ✅ BETTER - secure storage with validation
@validator('api_key')
def validate_api_key(cls, v):
    if not v:
        raise ValueError("API key is required")
    return v
```

### 2. **Environment-Specific Validation**
```python
@validator('environment')
def validate_production_security(cls, v, values):
    if v == Environment.PRODUCTION:
        # Require HTTPS in production
        if values.get('allow_http', False):
            raise ValueError("HTTP not allowed in production")
        
        # Require secure storage
        if not values.get('use_secure_storage', True):
            raise ValueError("Secure storage required in production")
    
    return v
```

### 3. **Configuration Drift Detection**
```python
def detect_configuration_drift(expected_config: dict, actual_config: dict):
    \"\"\"Detect when runtime config differs from expected\"\"\"
    drift_items = []
    
    for key, expected_value in expected_config.items():
        actual_value = actual_config.get(key)
        if actual_value != expected_value:
            drift_items.append({
                'key': key,
                'expected': expected_value,
                'actual': actual_value
            })
    
    return drift_items
```"

**[SLIDE 18: Production Deployment Patterns]**

"Configuration patterns for different deployment scenarios:

### 1. **Container Deployment**
```dockerfile
# Dockerfile
ENV THEODORE_ENVIRONMENT=production
ENV THEODORE_AWS_REGION=us-west-2

# Mount secrets as files
COPY secrets/api-keys.yml /etc/theodore/secrets.yml
```

### 2. **CI/CD Pipeline**
```yaml
# .github/workflows/deploy.yml
env:
  THEODORE_ENVIRONMENT: ${{ secrets.ENVIRONMENT }}
  THEODORE_AWS_REGION: ${{ vars.AWS_REGION }}
  THEODORE_PINECONE_API_KEY: ${{ secrets.PINECONE_API_KEY }}
```

### 3. **Kubernetes ConfigMaps**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: theodore-config
data:
  config.yml: |
    environment: production
    aws:
      region: us-west-2
    research:
      max_pages_to_scrape: 100
```

### 4. **Health Checks**
```python
@config_group.command()
def health():
    \"\"\"Check configuration health\"\"\"
    try:
        settings = TheodoreSettings()
        
        # Check API connectivity
        health_checks = [
            ('AWS Bedrock', check_aws_connectivity),
            ('Pinecone', check_pinecone_connectivity),
            ('Perplexity', check_perplexity_connectivity)
        ]
        
        for service, check_func in health_checks:
            status = check_func(settings)
            color = "green" if status else "red"
            console.print(f"[{color}]{service}: {'✅' if status else '❌'}[/{color}]")
            
    except Exception as e:
        console.print(f"[red]Health check failed: {e}[/red]")
```"

## Conclusion (3 minutes)

**[SLIDE 19: What We Built]**

"Congratulations! You've built an enterprise-grade configuration management system with:

✅ **Multiple Sources**: Files, environment variables, CLI arguments
✅ **Security**: Secure credential storage with keyring
✅ **Validation**: Early error detection with helpful messages
✅ **Precedence**: Clear hierarchy for configuration overrides
✅ **CLI Integration**: Beautiful commands for config management
✅ **Testing**: Comprehensive test coverage for all scenarios

**[SLIDE 20: Configuration Mastery]**

"You now have patterns for:
- Secure credential management
- Environment-specific configuration
- Configuration validation and drift detection
- CLI configuration management
- Production deployment strategies

**[FINAL THOUGHT]**
"Configuration is the foundation of reliable software. When done right, it makes your application deployable anywhere, secure by default, and maintainable over time. The patterns you've learned here will serve you in any production application.

Remember: Make it secure, make it validated, and make it easy to use!

Thank you for joining me. Now go build bulletproof configuration systems!"

---

## Instructor Notes:
- Total runtime: ~65 minutes
- Include working examples with real keyring integration
- Demonstrate CLI commands with actual config files
- Show security best practices throughout
- Cover production deployment scenarios
- Emphasize validation and error handling