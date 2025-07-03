#!/usr/bin/env python3
"""
Core Bedrock Client
==================

Enterprise-grade AWS Bedrock client with comprehensive authentication, retry logic,
cost tracking, and production monitoring capabilities.
"""

import boto3
import json
import time
import asyncio
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, BotoCoreError
from botocore.config import Config
import logging
from .config import BedrockConfig, calculate_bedrock_cost


class BedrockClient:
    """Core Bedrock client with authentication, retry logic, and cost tracking."""
    
    def __init__(self, config: BedrockConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._client = None
        self._session_created_at = None
        self._total_cost_today = 0.0
        self._last_cost_reset = time.strftime('%Y-%m-%d')
        
        # Performance optimizations
        self._boto_config = Config(
            region_name=config.region_name,
            retries={'max_attempts': 0},  # We handle retries ourselves
            max_pool_connections=config.connection_pool_size,
            read_timeout=config.timeout_seconds,
            connect_timeout=30
        )
    
    @property
    def client(self):
        """Get or create the Bedrock client with session management."""
        current_time = time.time()
        
        # Refresh session every hour for security
        if (self._client is None or 
            self._session_created_at is None or 
            current_time - self._session_created_at > 3600):
            
            self._create_client()
            
        return self._client
    
    @client.setter
    def client(self, value):
        """Allow setting client for testing purposes."""
        self._client = value
        self._session_created_at = time.time()
    
    @client.deleter  
    def client(self):
        """Allow deleting client for testing purposes."""
        self._client = None
        self._session_created_at = None
    
    def _create_client(self):
        """Create new Bedrock client with proper authentication."""
        try:
            # Create session with explicit credentials if provided
            if (self.config.aws_access_key_id and 
                self.config.aws_secret_access_key):
                
                session = boto3.Session(
                    aws_access_key_id=self.config.aws_access_key_id,
                    aws_secret_access_key=self.config.aws_secret_access_key,
                    aws_session_token=self.config.aws_session_token,
                    region_name=self.config.region_name
                )
            else:
                # Use default credential chain (IAM roles, env vars, etc.)
                session = boto3.Session(region_name=self.config.region_name)
            
            self._client = session.client('bedrock-runtime', config=self._boto_config)
            self._session_created_at = time.time()
            
            self.logger.info(f"Created Bedrock client for region {self.config.region_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to create Bedrock client: {e}")
            raise
    
    async def invoke_model(
        self, 
        model_id: str, 
        body: Dict[str, Any],
        max_retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """Invoke Bedrock model with retry logic and cost tracking."""
        
        max_retries = max_retries or self.config.max_retries
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                
                # Check daily cost limit
                self._check_cost_limits()
                
                # Prepare request
                request_body = json.dumps(body)
                
                # Make the API call
                response = self.client.invoke_model(
                    modelId=model_id,
                    body=request_body,
                    contentType='application/json',
                    accept='application/json'
                )
                
                # Parse response
                response_body = json.loads(response['body'].read())
                processing_time = time.time() - start_time
                
                # Track usage and costs
                usage_info = self._extract_usage_info(body, response_body, model_id)
                cost = self._track_usage(usage_info, model_id)
                
                self.logger.info(
                    f"Bedrock request successful: model={model_id}, "
                    f"tokens={usage_info.get('total_tokens', 0)}, "
                    f"cost=${cost:.4f}, time={processing_time:.2f}s"
                )
                
                # Add metadata to response
                response_body['_metadata'] = {
                    'model_id': model_id,
                    'processing_time': processing_time,
                    'usage': usage_info,
                    'cost': cost,
                    'attempt': attempt + 1
                }
                
                return response_body
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                last_exception = e
                
                # Don't retry on certain errors
                if error_code in ['ValidationException', 'AccessDeniedException']:
                    self.logger.error(f"Non-retryable Bedrock error: {error_code}")
                    raise
                
                # Calculate retry delay with exponential backoff and jitter
                if attempt < max_retries:
                    delay = min(2 ** attempt + (time.time() % 1), 60)  # Jitter + cap at 60s
                    self.logger.warning(
                        f"Bedrock request failed (attempt {attempt + 1}/{max_retries + 1}): "
                        f"{error_code}. Retrying in {delay:.2f}s"
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(f"Bedrock request failed after {max_retries + 1} attempts")
                    
            except BotoCoreError as e:
                last_exception = e
                if attempt < max_retries:
                    delay = min(2 ** attempt + (time.time() % 1), 60)
                    self.logger.warning(f"Bedrock connection error: {e}. Retrying in {delay:.2f}s")
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(f"Bedrock connection failed after {max_retries + 1} attempts")
        
        # If we get here, all retries failed
        raise last_exception
    
    def _check_cost_limits(self):
        """Check if we're within cost limits."""
        current_date = time.strftime('%Y-%m-%d')
        
        # Reset daily counter if it's a new day
        if current_date != self._last_cost_reset:
            self._total_cost_today = 0.0
            self._last_cost_reset = current_date
        
        if self._total_cost_today >= self.config.daily_cost_limit:
            raise Exception(
                f"Daily cost limit of ${self.config.daily_cost_limit} exceeded. "
                f"Current: ${self._total_cost_today:.2f}"
            )
    
    def _extract_usage_info(self, request_body: Dict, response_body: Dict, model_id: str) -> Dict[str, Any]:
        """Extract token usage information from request/response."""
        
        usage_info = {}
        
        # Try to extract tokens from response (varies by model)
        if 'usage' in response_body:
            # Nova models provide usage info
            usage = response_body['usage']
            usage_info = {
                'input_tokens': usage.get('inputTokens', 0),
                'output_tokens': usage.get('outputTokens', 0),
                'total_tokens': usage.get('totalTokens', 0)
            }
        elif '$metadata' in response_body and 'usage' in response_body['$metadata']:
            # Some models put usage in metadata
            usage = response_body['$metadata']['usage']
            usage_info = {
                'input_tokens': usage.get('prompt_tokens', usage.get('inputTokens', 0)),
                'output_tokens': usage.get('completion_tokens', usage.get('outputTokens', 0)),
                'total_tokens': usage.get('total_tokens', usage.get('totalTokens', 0))
            }
        else:
            # Fallback: estimate tokens for older models
            input_text = str(request_body.get('messages', request_body.get('prompt', request_body.get('inputText', ''))))
            output_text = str(response_body.get('content', response_body.get('completion', response_body.get('results', ''))))
            
            # Rough estimation: 1 token ≈ 4 characters
            usage_info = {
                'input_tokens': len(input_text) // 4,
                'output_tokens': len(output_text) // 4,
                'total_tokens': (len(input_text) + len(output_text)) // 4,
                'estimated': True
            }
        
        return usage_info
    
    def _track_usage(self, usage_info: Dict[str, Any], model_id: str) -> float:
        """Track usage and calculate costs."""
        
        if not self.config.enable_cost_tracking:
            return 0.0
        
        input_tokens = usage_info.get('input_tokens', 0)
        output_tokens = usage_info.get('output_tokens', 0)
        
        try:
            cost = calculate_bedrock_cost(input_tokens, output_tokens, model_id)
        except ValueError:
            # Unknown model, estimate based on Nova Pro costs
            self.logger.warning(f"Unknown model {model_id}, using Nova Pro costs for estimation")
            cost = calculate_bedrock_cost(input_tokens, output_tokens, 'amazon.nova-pro-v1:0')
        
        # Check per-request cost limit
        if cost > self.config.max_cost_per_request:
            self.logger.warning(
                f"Request cost ${cost:.4f} exceeds limit ${self.config.max_cost_per_request}"
            )
        
        # Track daily costs
        self._total_cost_today += cost
        
        return cost
    
    async def health_check(self) -> bool:
        """Check if Bedrock is accessible."""
        try:
            # Simple test with Nova Lite (cheapest model)
            test_body = {
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 10,
                "temperature": 0.1
            }
            
            await self.invoke_model('amazon.nova-lite-v1:0', test_body)
            return True
            
        except Exception as e:
            self.logger.warning(f"Bedrock health check failed: {e}")
            return False
    
    def get_daily_cost(self) -> float:
        """Get today's accumulated costs."""
        current_date = time.strftime('%Y-%m-%d')
        if current_date != self._last_cost_reset:
            return 0.0
        return self._total_cost_today
    
    def reset_daily_cost(self) -> None:
        """Reset daily cost tracking (for testing purposes)."""
        self._total_cost_today = 0.0
        self._last_cost_reset = time.strftime('%Y-%m-%d')
    
    async def close(self) -> None:
        """Clean up client resources."""
        if self._client:
            # Boto3 clients don't need explicit closing, but we can clear the reference
            self._client = None
            self._session_created_at = None
            self.logger.debug("Bedrock client resources cleaned up")