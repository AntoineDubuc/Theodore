#!/usr/bin/env python3
"""
Fix LLMConfig ForwardRef issue by testing different initialization approaches
"""

import asyncio
from pydantic import BaseModel, Field
from typing import List, Optional, ForwardRef
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
    from crawl4ai.extraction_strategy import LLMExtractionStrategy
    from crawl4ai.config import LLMConfig
    print("✓ Crawl4AI imports successful")
except ImportError as e:
    print(f"✗ Crawl4AI import failed: {e}")
    exit(1)

class CompanyInfo(BaseModel):
    name: str = Field(description="Company name")
    industry: str = Field(description="Primary industry or sector")
    description: str = Field(description="Brief company description")
    
class CompanyList(BaseModel):
    companies: List[CompanyInfo] = Field(description="List of companies found")

# Rebuild models to resolve any ForwardRef issues
CompanyInfo.model_rebuild()
CompanyList.model_rebuild()

async def test_llmconfig_approaches():
    """Test different approaches to create LLMConfig without ForwardRef errors"""
    print("\n=== Testing LLMConfig Creation Approaches ===")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("✗ No OPENAI_API_KEY found in environment")
        return
    
    test_cases = [
        {
            "name": "Standard provider format",
            "config_kwargs": {
                "provider": "openai/gpt-4o-mini",
                "api_token": openai_key
            }
        },
        {
            "name": "Legacy provider format",
            "config_kwargs": {
                "provider": "openai",
                "api_token": openai_key
            }
        },
        {
            "name": "With model in provider string",
            "config_kwargs": {
                "provider": "openai/gpt-4o-mini",
                "api_token": openai_key,
                "model": "gpt-4o-mini"
            }
        },
        {
            "name": "With explicit model parameter",
            "config_kwargs": {
                "provider": "openai",
                "model": "gpt-4o-mini", 
                "api_token": openai_key
            }
        },
        {
            "name": "With api_base parameter",
            "config_kwargs": {
                "provider": "openai",
                "api_token": openai_key,
                "api_base": "https://api.openai.com/v1"
            }
        },
        {
            "name": "Using dict initialization",
            "config_kwargs": None,  # Will use dict approach
            "config_dict": {
                "provider": "openai/gpt-4o-mini",
                "api_token": openai_key
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        
        try:
            if test_case.get('config_dict'):
                # Try dict initialization
                llm_config = LLMConfig(**test_case['config_dict'])
            else:
                # Try keyword arguments
                llm_config = LLMConfig(**test_case['config_kwargs'])
            
            print(f"  ✓ LLMConfig created: {type(llm_config)}")
            
            # Test creating strategy with this config
            try:
                strategy = LLMExtractionStrategy(
                    llm_config=llm_config,
                    schema=CompanyList.model_json_schema(),
                    extraction_type="schema",
                    instruction="Extract company information"
                )
                print(f"  ✓ LLMExtractionStrategy created successfully")
                
                # Test CrawlerRunConfig
                try:
                    config = CrawlerRunConfig(extraction_strategy=strategy)
                    print(f"  ✓ CrawlerRunConfig created successfully")
                    return strategy  # Return the working strategy
                except Exception as e:
                    print(f"  ✗ CrawlerRunConfig failed: {e}")
                    
            except Exception as e:
                print(f"  ✗ LLMExtractionStrategy failed: {e}")
                
        except Exception as e:
            print(f"  ✗ LLMConfig creation failed: {e}")
            
    return None

async def test_working_extraction():
    """Test the working strategy with a real URL"""
    print("\n=== Testing Working Extraction ===")
    
    # Get working strategy
    strategy = await test_llmconfig_approaches()
    if not strategy:
        print("✗ No working strategy found")
        return
    
    try:
        config = CrawlerRunConfig(
            extraction_strategy=strategy,
            word_count_threshold=10,
            only_text=True,
            verbose=False
        )
        
        async with AsyncWebCrawler() as crawler:
            print("Testing extraction with Visterra...")
            result = await crawler.arun(
                url="https://visterra.com",
                config=config
            )
            
            print(f"✓ Extraction completed")
            print(f"  Success: {result.success}")
            print(f"  Status: {result.status_code}")
            
            if result.extracted_content:
                print(f"  Extracted content type: {type(result.extracted_content)}")
                print(f"  Extracted content: {result.extracted_content}")
            else:
                print("  No extracted content")
                print(f"  Raw content length: {len(result.cleaned_html) if result.cleaned_html else 0}")
                
    except Exception as e:
        print(f"✗ Working extraction test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_alternative_approaches():
    """Test alternative approaches to avoid LLMConfig entirely"""
    print("\n=== Testing Alternative Approaches ===")
    
    # Try to inspect LLMConfig to understand the ForwardRef issue
    try:
        import inspect
        from crawl4ai.config import LLMConfig
        
        print("LLMConfig signature:")
        sig = inspect.signature(LLMConfig)
        for param_name, param in sig.parameters.items():
            print(f"  {param_name}: {param.annotation} = {param.default}")
            
        # Check for ForwardRef in annotations
        annotations = LLMConfig.__annotations__ if hasattr(LLMConfig, '__annotations__') else {}
        print(f"\nLLMConfig annotations: {annotations}")
        
        # Try to find the source of ForwardRef
        for name, annotation in annotations.items():
            if isinstance(annotation, ForwardRef):
                print(f"  ForwardRef found in {name}: {annotation}")
        
    except Exception as e:
        print(f"Could not inspect LLMConfig: {e}")

async def main():
    """Main function to fix LLMConfig ForwardRef issue"""
    print("=== Fixing LLMConfig ForwardRef Issue ===")
    
    await test_alternative_approaches()
    await test_working_extraction()

if __name__ == "__main__":
    asyncio.run(main())