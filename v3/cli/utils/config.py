#!/usr/bin/env python3
"""
Theodore v3 Configuration Management
===================================

Simple configuration management using environment variables.
No complex dependency injection - just load what we need.
"""

import os
from typing import Dict, List, Optional
from pathlib import Path

def load_environment():
    """Load environment variables from .env file if it exists"""
    try:
        from dotenv import load_dotenv
        
        # Look for .env file in current directory and parent directories
        env_paths = [
            Path.cwd() / '.env',
            Path.cwd().parent / '.env',
            Path.cwd().parent.parent / '.env',
            Path(__file__).parent.parent.parent / '.env'
        ]
        
        for env_path in env_paths:
            if env_path.exists():
                load_dotenv(env_path)
                return str(env_path)
                
        return None
        
    except ImportError:
        return None

def get_required_env_vars() -> List[str]:
    """Get list of required environment variables"""
    return [
        'OPEN_ROUTER_API_KEY',  # For Nova Pro via OpenRouter
        'GEMINI_API_KEY',       # For Gemini analysis
        'PINECONE_API_KEY',     # For vector storage
        'PINECONE_INDEX_NAME'   # Pinecone index name
    ]

def get_optional_env_vars() -> List[str]:
    """Get list of optional environment variables"""
    return [
        'OPENAI_API_KEY',       # Fallback AI client
        'AWS_ACCESS_KEY_ID',    # For Bedrock if available
        'AWS_SECRET_ACCESS_KEY' # For Bedrock if available
    ]

def check_configuration() -> Dict:
    """Check configuration status and return report"""
    
    # Load environment
    env_file = load_environment()
    
    required_vars = get_required_env_vars()
    optional_vars = get_optional_env_vars()
    
    issues = []
    configured_count = 0
    
    # Check required variables
    for var in required_vars:
        if os.getenv(var):
            configured_count += 1
        else:
            issues.append(f"Missing required environment variable: {var}")
    
    # Check optional variables
    for var in optional_vars:
        if os.getenv(var):
            configured_count += 1
    
    # Determine if configuration is valid
    valid = len(issues) == 0
    
    return {
        'valid': valid,
        'issues': issues,
        'api_keys_count': configured_count,
        'total_possible': len(required_vars) + len(optional_vars),
        'env_file': env_file,
        'working_dir': str(Path.cwd())
    }

def get_openrouter_config() -> Dict:
    """Get OpenRouter configuration for Nova Pro"""
    return {
        'api_key': os.getenv('OPEN_ROUTER_API_KEY'),
        'base_url': 'https://openrouter.ai/api/v1',
        'model': 'amazon/nova-pro-v1'
    }

def get_gemini_config() -> Dict:
    """Get Gemini configuration"""
    return {
        'api_key': os.getenv('GEMINI_API_KEY'),
        'model': 'gemini-2.5-pro'
    }

def get_pinecone_config() -> Dict:
    """Get Pinecone configuration"""
    return {
        'api_key': os.getenv('PINECONE_API_KEY'),
        'index_name': os.getenv('PINECONE_INDEX_NAME', 'theodore-companies'),
        'dimension': 1536
    }

def get_openai_config() -> Dict:
    """Get OpenAI configuration (fallback)"""
    return {
        'api_key': os.getenv('OPENAI_API_KEY'),
        'model': 'gpt-4o-mini'
    }

def validate_api_keys() -> Dict[str, bool]:
    """Validate that API keys are present and non-empty"""
    
    configs = {
        'openrouter': get_openrouter_config(),
        'gemini': get_gemini_config(), 
        'pinecone': get_pinecone_config(),
        'openai': get_openai_config()
    }
    
    validation = {}
    
    for service, config in configs.items():
        api_key = config.get('api_key')
        validation[service] = bool(api_key and api_key.strip())
    
    return validation

def get_crawling_config() -> Dict:
    """Get crawling configuration with proven optimal settings"""
    return {
        'max_concurrent': 10,           # Proven optimal from antoine
        'timeout_seconds': 30,
        'max_content_per_page': 15000,
        'max_pages_to_select': 20,
        'min_confidence': 0.6
    }

def get_output_config() -> Dict:
    """Get output configuration"""
    return {
        'default_format': 'console',
        'progress_enabled': True,
        'verbose_enabled': False,
        'color_enabled': True
    }