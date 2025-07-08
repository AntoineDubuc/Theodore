#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antoine Selection Module for Theodore - LLM-Powered Valuable Links Filter
==========================================================================

Pure Amazon Nova Pro LLM-based path filtering via OpenRouter API.
NO HEURISTICS. NO FALLBACKS. Pure LLM intelligence only.

Adapted from antoine/get_valuable_links_from_llm.py for Theodore integration.
"""

import asyncio
import json
import logging
import os
import time
import requests
from typing import List, Dict, Optional
from urllib.parse import urlparse
from dataclasses import dataclass

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print("⚠️ No .env file found, using system environment variables")
except ImportError:
    print("⚠️ python-dotenv not available, using system environment variables")

logger = logging.getLogger(__name__)


@dataclass
class OpenRouterResponse:
    """Response from OpenRouter API"""
    success: bool
    content: str
    model_used: str
    tokens_used: int
    cost_usd: float
    processing_time: float
    error: Optional[str] = None


@dataclass
class LinkSelectionResult:
    """Result of Nova Pro link filtering"""
    success: bool
    selected_paths: List[str]
    path_priorities: Dict[str, float]
    path_reasoning: Dict[str, str]
    rejected_paths: List[str]
    
    # LLM metadata
    model_used: str
    tokens_used: int
    cost_usd: float
    processing_time: float
    llm_prompt: str  # The complete prompt sent to Nova Pro
    
    # Input metadata
    total_input_paths: int
    confidence_threshold: float
    
    # Error info
    error: str = ""


class OpenRouterClient:
    """OpenRouter client for Nova Pro LLM"""
    
    def __init__(self, api_key: str, model: str = "amazon/nova-pro-v1"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        
    def analyze_paths(self, prompt: str, timeout: int = 45) -> OpenRouterResponse:
        """
        Send prompt to Nova Pro via OpenRouter.
        No fallbacks, no heuristics - if this fails, the whole thing fails.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://theodore-ai.com",
            "X-Title": "Theodore AI Company Intelligence"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": 0.1,  # Low temperature for consistent analysis
            "max_tokens": 4000
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=timeout
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code != 200:
                return OpenRouterResponse(
                    success=False,
                    content="",
                    model_used="",
                    tokens_used=0,
                    cost_usd=0.0,
                    processing_time=processing_time,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
            
            data = response.json()
            
            # Extract response data
            content = data["choices"][0]["message"]["content"]
            model_used = data.get("model", self.model)
            
            # Extract usage stats
            usage = data.get("usage", {})
            tokens_used = usage.get("total_tokens", 0)
            
            # Calculate cost (rough estimate - Nova Pro is ~$0.0008/1K tokens)
            cost_usd = (tokens_used / 1000) * 0.0008
            
            return OpenRouterResponse(
                success=True,
                content=content,
                model_used=model_used,
                tokens_used=tokens_used,
                cost_usd=cost_usd,
                processing_time=processing_time
            )
            
        except requests.exceptions.Timeout:
            return OpenRouterResponse(
                success=False,
                content="",
                model_used="",
                tokens_used=0,
                cost_usd=0.0,
                processing_time=time.time() - start_time,
                error=f"Request timed out after {timeout} seconds"
            )
            
        except Exception as e:
            return OpenRouterResponse(
                success=False,
                content="",
                model_used="",
                tokens_used=0,
                cost_usd=0.0,
                processing_time=time.time() - start_time,
                error=str(e)
            )


def create_openrouter_client() -> OpenRouterClient:
    """Create OpenRouter client with environment variables"""
    # Try both possible environment variable names
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPEN_ROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable is required")
    
    return OpenRouterClient(api_key, "amazon/nova-pro-v1")


def create_path_selection_prompt(paths: List[str], domain: str, min_confidence: float) -> str:
    """Create the refined prompt for Nova Pro path selection using Target Information Profile"""
    
    # Get the prompt template from storage
    try:
        from src.prompt_storage import get_prompt_storage
        storage = get_prompt_storage()
        prompt_template = storage.get_prompt('page_selection')
    except Exception as e:
        # Fallback to default if storage not available
        print(f"❌ Failed to load page selection prompt from storage: {e}")
        from src.theodore_prompts import get_page_selection_prompt
        prompt_template = get_page_selection_prompt()
    
    # Format paths for JSON array
    paths_json = json.dumps(paths, indent=2)
    
    # Default max pages if not specified
    max_pages = 50
    
    # Fill in the placeholders
    prompt = prompt_template.format(
        paths_json=paths_json,
        min_confidence=min_confidence,
        max_pages=max_pages
    )
    
    return prompt


async def filter_valuable_links(
    all_paths: List[str], 
    base_url: str,
    min_confidence: float = 0.6,
    timeout_seconds: int = 60,
    _is_retry: bool = False  # Internal parameter to track retry state
) -> LinkSelectionResult:
    """
    Filter paths using Nova Pro LLM via OpenRouter.
    Automatically retries with lower confidence if fewer than 8 paths selected.
    """
    
    # Filter to first-level paths if too many paths
    if len(all_paths) > 500:
        print(f"⚠️  Found {len(all_paths)} paths - filtering to first-level paths only")
        
        # Keep only paths with a single forward slash (first-level paths)
        first_level_paths = []
        for path in all_paths:
            # Count slashes in the path
            slash_count = path.count('/')
            # Keep paths with only one slash (e.g., /about, /contact)
            # Also keep the root path "/"
            if path == "/" or (slash_count == 1 and path.startswith('/')):
                first_level_paths.append(path)
        
        print(f"✅ Filtered from {len(all_paths)} to {len(first_level_paths)} first-level paths")
        all_paths = first_level_paths
    
    print(f"🤖 Filtering {len(all_paths)} paths using Nova Pro LLM via OpenRouter")
    print(f"🎯 Confidence threshold: {min_confidence}")
    print(f"⚡ Timeout: {timeout_seconds}s")
    if _is_retry:
        print(f"🔄 RETRY with lowered confidence threshold")
    
    start_time = time.time()
    
    # Parse domain for context
    parsed_url = urlparse(base_url)
    domain = parsed_url.netloc
    
    try:
        # Create OpenRouter client
        client = create_openrouter_client()
        
        # Create prompt
        prompt = create_path_selection_prompt(all_paths, domain, min_confidence)
        
        print(f"📝 Prompt length: {len(prompt):,} characters")
        print(f"🔄 Sending to Nova Pro via OpenRouter...")
        
        # Call Nova Pro
        response = client.analyze_paths(prompt, timeout_seconds)
        
        if not response.success:
            return LinkSelectionResult(
                success=False,
                selected_paths=[],
                path_priorities={},
                path_reasoning={},
                rejected_paths=all_paths,
                model_used="",
                tokens_used=0,
                cost_usd=0.0,
                processing_time=time.time() - start_time,
                total_input_paths=len(all_paths),
                confidence_threshold=min_confidence,
                llm_prompt=prompt,
                error=f"Nova Pro failed: {response.error}"
            )
        
        print(f"✅ Nova Pro response received")
        print(f"🏷️  Model: {response.model_used}")
        print(f"🔢 Tokens: {response.tokens_used:,}")
        print(f"💰 Cost: ${response.cost_usd:.4f}")
        
        # Parse Nova Pro response
        try:
            # Extract JSON from response
            content = response.content.strip()
            
            # Find JSON object in response (try object first, then array fallback)
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                # Fallback to array format
                json_start = content.find('[')
                json_end = content.rfind(']') + 1
                
                if json_start == -1 or json_end == 0:
                    raise ValueError("No JSON found in Nova Pro response")
                
                # Old format - just array of paths
                json_content = content[json_start:json_end]
                parsed_response = json.loads(json_content)
                
                if not isinstance(parsed_response, list):
                    raise ValueError("Nova Pro response is not a valid array")
                
                selected_paths = parsed_response
                path_explanations = {}
            else:
                # New format - object with paths and explanations
                json_content = content[json_start:json_end]
                parsed_response = json.loads(json_content)
                
                if not isinstance(parsed_response, dict):
                    raise ValueError("Nova Pro response is not a valid object")
                
                selected_paths = parsed_response.get("selected_paths", [])
                path_explanations = parsed_response.get("path_explanations", {})
            
            # Clean and validate paths
            cleaned_paths = []
            for path in selected_paths:
                if isinstance(path, str) and path.strip():
                    cleaned_path = path.strip()
                    if cleaned_path in all_paths:  # Verify path was in original list
                        cleaned_paths.append(cleaned_path)
            
            selected_paths = cleaned_paths
            
            # Check if we need to retry with lower confidence
            if len(selected_paths) < 8 and not _is_retry and min_confidence > 0.3:
                print(f"⚠️  Only {len(selected_paths)} paths selected (minimum: 8)")
                print(f"🔄 Retrying with lowered confidence threshold: 0.3")
                
                # Retry with lower confidence
                return await filter_valuable_links(
                    all_paths, 
                    base_url,
                    min_confidence=0.3,  # Lower threshold
                    timeout_seconds=timeout_seconds,
                    _is_retry=True  # Mark as retry
                )
            
            # Create path metadata using explanations or defaults
            path_priorities = {path: 0.8 for path in selected_paths}  # Default high confidence
            path_reasoning = {}
            for path in selected_paths:
                if path in path_explanations:
                    path_reasoning[path] = f"Fields expected: {path_explanations[path]}"
                else:
                    path_reasoning[path] = "Selected by Nova Pro using Target Information Profile"
            
            # Determine rejected paths
            selected_set = set(selected_paths)
            rejected_paths = [path for path in all_paths if path not in selected_set]
            
            print(f"🎯 Nova Pro selected {len(selected_paths)} paths")
            print(f"🚫 Rejected {len(rejected_paths)} paths")
            
            return LinkSelectionResult(
                success=True,
                selected_paths=selected_paths,
                path_priorities=path_priorities,
                path_reasoning=path_reasoning,
                rejected_paths=rejected_paths,
                model_used=response.model_used,
                tokens_used=response.tokens_used,
                cost_usd=response.cost_usd,
                processing_time=time.time() - start_time,
                total_input_paths=len(all_paths),
                confidence_threshold=min_confidence,
                llm_prompt=prompt
            )
            
        except json.JSONDecodeError as e:
            return LinkSelectionResult(
                success=False,
                selected_paths=[],
                path_priorities={},
                path_reasoning={},
                rejected_paths=all_paths,
                model_used=response.model_used,
                tokens_used=response.tokens_used,
                cost_usd=response.cost_usd,
                processing_time=time.time() - start_time,
                total_input_paths=len(all_paths),
                confidence_threshold=min_confidence,
                llm_prompt=prompt,
                error=f"Failed to parse Nova Pro JSON response: {e}"
            )
            
        except Exception as e:
            return LinkSelectionResult(
                success=False,
                selected_paths=[],
                path_priorities={},
                path_reasoning={},
                rejected_paths=all_paths,
                model_used=response.model_used,
                tokens_used=response.tokens_used,
                cost_usd=response.cost_usd,
                processing_time=time.time() - start_time,
                total_input_paths=len(all_paths),
                confidence_threshold=min_confidence,
                llm_prompt=prompt,
                error=f"Failed to process Nova Pro response: {e}"
            )
            
    except Exception as e:
        return LinkSelectionResult(
            success=False,
            selected_paths=[],
            path_priorities={},
            path_reasoning={},
            rejected_paths=all_paths,
            model_used="",
            tokens_used=0,
            cost_usd=0.0,
            processing_time=time.time() - start_time,
            total_input_paths=len(all_paths),
            confidence_threshold=min_confidence,
            llm_prompt="",  # Prompt may not be available in outer exception
            error=f"Nova Pro filtering failed: {e}"
        )


def filter_valuable_links_sync(
    all_paths: List[str], 
    base_url: str,
    min_confidence: float = 0.6,
    timeout_seconds: int = 60
) -> LinkSelectionResult:
    """
    Synchronous wrapper for filter_valuable_links().
    NO HEURISTICS. If Nova Pro fails, the entire operation fails.
    """
    try:
        return asyncio.run(filter_valuable_links(all_paths, base_url, min_confidence, timeout_seconds))
    except Exception as e:
        logger.error(f"Error in Nova Pro filtering for {base_url}: {e}")
        return LinkSelectionResult(
            success=False,
            selected_paths=[],
            path_priorities={},
            path_reasoning={},
            rejected_paths=all_paths,
            model_used="",
            tokens_used=0,
            cost_usd=0.0,
            processing_time=0.0,
            total_input_paths=len(all_paths),
            confidence_threshold=min_confidence,
            error=f"Nova Pro sync wrapper error: {e}"
        )