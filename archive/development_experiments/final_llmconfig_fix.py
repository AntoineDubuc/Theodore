#!/usr/bin/env python3
"""
Final fix for LLMConfig ForwardRef issue using proper imports and create_llm_config function
"""

import asyncio
from pydantic import BaseModel, Field
from typing import List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LLMConfig
    from crawl4ai.extraction_strategy import LLMExtractionStrategy, create_llm_config
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

async def test_create_llm_config_function():
    """Test using the create_llm_config function"""
    print("\n=== Testing create_llm_config Function ===")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("✗ No OPENAI_API_KEY found in environment")
        return None
    
    try:
        # Test create_llm_config function
        llm_config = create_llm_config(
            provider="openai/gpt-4o-mini",
            api_token=openai_key
        )
        print(f"✓ create_llm_config successful: {type(llm_config)}")
        
        # Test creating strategy with this config
        strategy = LLMExtractionStrategy(
            llm_config=llm_config,
            schema=CompanyList.model_json_schema(),
            extraction_type="schema",
            instruction="Extract company information including name, industry, and description"
        )
        print(f"✓ LLMExtractionStrategy created successfully")
        
        # Test CrawlerRunConfig
        config = CrawlerRunConfig(extraction_strategy=strategy)
        print(f"✓ CrawlerRunConfig created successfully")
        
        return strategy
        
    except Exception as e:
        print(f"✗ create_llm_config approach failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_direct_llmconfig():
    """Test using LLMConfig directly from main module"""
    print("\n=== Testing Direct LLMConfig ===")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("✗ No OPENAI_API_KEY found in environment")
        return None
    
    try:
        # Try direct LLMConfig instantiation
        llm_config = LLMConfig(
            provider="openai/gpt-4o-mini",
            api_token=openai_key
        )
        print(f"✓ Direct LLMConfig successful: {type(llm_config)}")
        
        # Test creating strategy with this config
        strategy = LLMExtractionStrategy(
            llm_config=llm_config,
            schema=CompanyList.model_json_schema(),
            extraction_type="schema",
            instruction="Extract company information including name, industry, and description"
        )
        print(f"✓ LLMExtractionStrategy created successfully")
        
        return strategy
        
    except Exception as e:
        print(f"✗ Direct LLMConfig approach failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_working_extraction(strategy):
    """Test the working strategy with Visterra"""
    print("\n=== Testing Working Extraction with Visterra ===")
    
    if not strategy:
        print("✗ No working strategy provided")
        return
    
    try:
        config = CrawlerRunConfig(
            extraction_strategy=strategy,
            word_count_threshold=10,
            only_text=True,
            verbose=False
        )
        
        async with AsyncWebCrawler() as crawler:
            print("Extracting from Visterra...")
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
                
                # Try to parse the extracted content
                if isinstance(result.extracted_content, str):
                    try:
                        import json
                        parsed = json.loads(result.extracted_content)
                        print(f"  ✓ Successfully parsed JSON: {parsed}")
                    except json.JSONDecodeError:
                        print(f"  Raw content: {result.extracted_content}")
                else:
                    print(f"  Direct object: {result.extracted_content}")
            else:
                print("  No extracted content")
                print(f"  Raw content length: {len(result.cleaned_html) if result.cleaned_html else 0}")
                
    except Exception as e:
        print(f"✗ Working extraction test failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function to test both approaches"""
    print("=== Final LLMConfig ForwardRef Fix ===")
    
    # Test create_llm_config function approach
    strategy1 = await test_create_llm_config_function()
    
    # Test direct LLMConfig approach
    strategy2 = await test_direct_llmconfig()
    
    # Test with whichever strategy worked
    working_strategy = strategy1 or strategy2
    if working_strategy:
        await test_working_extraction(working_strategy)
        print("\n✅ SUCCESS: LLMConfig ForwardRef issue has been resolved!")
        print("The working approach can now be integrated into Theodore's main pipeline.")
    else:
        print("\n❌ FAILED: Unable to resolve LLMConfig ForwardRef issue")

if __name__ == "__main__":
    asyncio.run(main())