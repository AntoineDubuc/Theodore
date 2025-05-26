#!/usr/bin/env python3
"""
Discover CrawlerRunConfig parameters and test direct LLMExtractionStrategy application
to bypass the problematic LLMConfig wrapper causing ForwardRef errors.
"""

import asyncio
import inspect
from pydantic import BaseModel, Field
from typing import List, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
    from crawl4ai.extraction_strategy import LLMExtractionStrategy
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

def inspect_crawler_config():
    """Inspect CrawlerRunConfig to understand available parameters"""
    print("\n=== CrawlerRunConfig Inspection ===")
    
    # Get the signature of CrawlerRunConfig
    sig = inspect.signature(CrawlerRunConfig)
    print(f"CrawlerRunConfig parameters:")
    for param_name, param in sig.parameters.items():
        print(f"  {param_name}: {param.annotation} = {param.default}")
    
    # Check if it has extraction_strategy field
    try:
        config_fields = CrawlerRunConfig.__fields__ if hasattr(CrawlerRunConfig, '__fields__') else {}
        print(f"\nCrawlerRunConfig fields: {list(config_fields.keys())}")
    except Exception as e:
        print(f"Could not inspect fields: {e}")

def inspect_llm_extraction_strategy():
    """Inspect LLMExtractionStrategy to understand initialization"""
    print("\n=== LLMExtractionStrategy Inspection ===")
    
    sig = inspect.signature(LLMExtractionStrategy)
    print(f"LLMExtractionStrategy parameters:")
    for param_name, param in sig.parameters.items():
        print(f"  {param_name}: {param.annotation} = {param.default}")

async def test_direct_strategy_application():
    """Test applying LLMExtractionStrategy directly without LLMConfig"""
    print("\n=== Testing Direct Strategy Application ===")
    
    # Try different approaches to create the strategy
    test_cases = [
        {
            "name": "Direct provider string",
            "strategy_kwargs": {
                "provider": "openai/gpt-4o-mini",
                "api_token": os.getenv("OPENAI_API_KEY"),
                "schema": CompanyList.model_json_schema(),
                "extraction_type": "schema",
                "instruction": "Extract company information"
            }
        },
        {
            "name": "Legacy provider format", 
            "strategy_kwargs": {
                "provider": "openai",
                "api_token": os.getenv("OPENAI_API_KEY"),
                "schema": CompanyList.model_json_schema(),
                "extraction_type": "schema", 
                "instruction": "Extract company information"
            }
        },
        {
            "name": "With model parameter",
            "strategy_kwargs": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "api_token": os.getenv("OPENAI_API_KEY"),
                "schema": CompanyList.model_json_schema(),
                "extraction_type": "schema",
                "instruction": "Extract company information"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        try:
            strategy = LLMExtractionStrategy(**test_case['strategy_kwargs'])
            print(f"  ✓ Strategy created successfully: {type(strategy)}")
            
            # Try to use it in CrawlerRunConfig
            try:
                config = CrawlerRunConfig(extraction_strategy=strategy)
                print(f"  ✓ CrawlerRunConfig created successfully")
            except Exception as e:
                print(f"  ✗ CrawlerRunConfig failed: {e}")
                
        except Exception as e:
            print(f"  ✗ Strategy creation failed: {e}")

async def test_minimal_crawl():
    """Test minimal crawl with working strategy"""
    print("\n=== Testing Minimal Crawl ===")
    
    try:
        # Create strategy without problematic LLMConfig
        strategy = LLMExtractionStrategy(
            provider="openai",
            api_token=os.getenv("OPENAI_API_KEY"),
            schema=CompanyList.model_json_schema(),
            extraction_type="schema",
            instruction="Extract any company names and their industries from this content"
        )
        
        config = CrawlerRunConfig(
            extraction_strategy=strategy,
            word_count_threshold=10,
            only_text=True
        )
        
        async with AsyncWebCrawler() as crawler:
            print("Testing with simple company page...")
            result = await crawler.arun(
                url="https://www.apple.com",
                config=config
            )
            
            print(f"✓ Crawl completed")
            print(f"  Success: {result.success}")
            print(f"  Status: {result.status_code}")
            if result.extracted_content:
                print(f"  Extracted content length: {len(str(result.extracted_content))}")
                print(f"  Extracted content preview: {str(result.extracted_content)[:200]}...")
            else:
                print("  No extracted content")
                
    except Exception as e:
        print(f"✗ Minimal crawl failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main discovery function"""
    print("=== Crawl4AI LLMExtractionStrategy Discovery ===")
    
    # Step 1: Inspect available parameters
    inspect_crawler_config()
    inspect_llm_extraction_strategy()
    
    # Step 2: Test direct strategy creation
    await test_direct_strategy_application()
    
    # Step 3: Test minimal crawl
    await test_minimal_crawl()

if __name__ == "__main__":
    asyncio.run(main())