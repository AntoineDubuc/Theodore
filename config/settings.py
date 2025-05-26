"""
Theodore Configuration Settings
Centralized configuration management
"""

import os
from typing import Optional
from pydantic import BaseSettings, Field


class TheodoreSettings(BaseSettings):
    """Main configuration settings for Theodore"""
    
    # Project Info
    project_name: str = "Theodore"
    version: str = "1.0.0"
    description: str = "AI-powered company intelligence platform"
    
    # AWS Configuration
    aws_access_key_id: str = Field(..., env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(..., env="AWS_SECRET_ACCESS_KEY") 
    aws_region: str = Field(default="us-west-2", env="AWS_REGION")
    
    # Pinecone Configuration
    pinecone_api_key: str = Field(..., env="PINECONE_API_KEY")
    pinecone_environment: str = Field(..., env="PINECONE_ENVIRONMENT")
    pinecone_index_name: str = Field(..., env="PINECONE_INDEX_NAME")
    
    # Bedrock Configuration
    bedrock_embedding_model: str = Field(
        default="amazon.titan-embed-text-v1", 
        env="BEDROCK_EMBEDDING_MODEL"
    )
    bedrock_analysis_model: str = Field(
        default="anthropic.claude-3-sonnet-20240229-v1:0",
        env="BEDROCK_ANALYSIS_MODEL"
    )
    bedrock_region: str = Field(default="us-west-2", env="BEDROCK_REGION")
    
    # OpenAI Configuration (for Crawl4AI)
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    
    # Processing Configuration
    max_content_length: int = 10000
    rate_limit_delay: float = 1.0
    max_pages_per_company: int = 11
    embedding_dimensions: int = 1536
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = TheodoreSettings()