#!/usr/bin/env python3
"""
Debug script to identify why the Theodore web scraping system is failing.
This will test the scraping pipeline step by step.
"""

import sys
import logging
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append('src')

# Set up logging to see detailed output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_scraping.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

def test_scraping_pipeline():
    """Test the scraping pipeline to identify failure points"""
    
    print("🔍 Starting Theodore scraping debug analysis...")
    
    try:
        # Step 1: Test configuration loading
        print("\n📋 Step 1: Testing configuration loading...")
        from config.settings import settings
        print(f"✅ Configuration loaded successfully")
        print(f"   - Bedrock region: {settings.aws_region}")
        print(f"   - Pinecone API key present: {bool(settings.pinecone_api_key)}")
        print(f"   - Gemini API key present: {bool(settings.gemini_api_key)}")
        
        # Step 2: Test AI clients initialization
        print("\n🤖 Step 2: Testing AI clients...")
        from src.bedrock_client import BedrockClient
        from src.gemini_client import GeminiClient
        from src.models import CompanyIntelligenceConfig
        
        config = CompanyIntelligenceConfig()
        
        # Test Bedrock client
        try:
            bedrock_client = BedrockClient(config)
            print("✅ Bedrock client initialized")
        except Exception as e:
            print(f"❌ Bedrock client failed: {e}")
            bedrock_client = None
            
        # Test Gemini client
        try:
            gemini_client = GeminiClient(config)
            print("✅ Gemini client initialized")
        except Exception as e:
            print(f"❌ Gemini client failed: {e}")
            gemini_client = None
        
        # Step 3: Test Pinecone client
        print("\n📊 Step 3: Testing Pinecone client...")
        try:
            from src.pinecone_client import PineconeClient
            pinecone_client = PineconeClient(
                config,
                settings.pinecone_api_key,
                settings.pinecone_environment,
                settings.pinecone_index_name
            )
            print("✅ Pinecone client initialized")
        except Exception as e:
            print(f"❌ Pinecone client failed: {e}")
            pinecone_client = None
        
        # Step 4: Test intelligent scraper initialization
        print("\n🕷️ Step 4: Testing intelligent scraper...")
        try:
            from src.intelligent_company_scraper import IntelligentCompanyScraperSync
            scraper = IntelligentCompanyScraperSync(config, bedrock_client)
            print("✅ Intelligent scraper initialized")
        except Exception as e:
            print(f"❌ Intelligent scraper failed: {e}")
            scraper = None
        
        # Step 5: Test simple enhanced discovery
        print("\n🔍 Step 5: Testing simple enhanced discovery...")
        try:
            from src.simple_enhanced_discovery import SimpleEnhancedDiscovery
            enhanced_discovery = SimpleEnhancedDiscovery(
                ai_client=bedrock_client or gemini_client,
                pinecone_client=pinecone_client,
                scraper=scraper
            )
            print("✅ Enhanced discovery initialized")
        except Exception as e:
            print(f"❌ Enhanced discovery failed: {e}")
            enhanced_discovery = None
        
        # Step 6: Test a simple company scraping operation
        print("\n🏢 Step 6: Testing company scraping operation...")
        if scraper and enhanced_discovery:
            try:
                from src.models import CompanyData
                
                # Test with AbGenomics (the company mentioned in the issue)
                test_company = CompanyData(
                    name="AbGenomics",
                    website="https://abgenomics.com"
                )
                
                print(f"   Testing scraping for: {test_company.name}")
                print(f"   Website: {test_company.website}")
                
                # Test the scraping process
                result = scraper.scrape_company(test_company)
                
                print(f"   Scrape status: {result.scrape_status}")
                if result.scrape_status == "success":
                    print(f"   Content length: {len(result.company_description or '')}")
                    print(f"   Pages crawled: {len(result.pages_crawled or [])}")
                    print(f"   Content preview: {(result.company_description or '')[:200]}...")
                else:
                    print(f"   Scrape error: {result.scrape_error}")
                
            except Exception as e:
                print(f"❌ Company scraping test failed: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("❌ Cannot test scraping - scraper or enhanced discovery not available")
        
        # Step 7: Test async scraping directly
        print("\n⚡ Step 7: Testing async scraping directly...")
        if bedrock_client or gemini_client:
            try:
                from src.intelligent_company_scraper import IntelligentCompanyScraper
                from src.models import CompanyData
                
                async_scraper = IntelligentCompanyScraper(config, bedrock_client or gemini_client)
                
                test_company = CompanyData(
                    name="AbGenomics",
                    website="https://abgenomics.com"
                )
                
                print("   Running async scraping test...")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                result = loop.run_until_complete(
                    async_scraper.scrape_company_intelligent(test_company)
                )
                
                loop.close()
                
                print(f"   Async scrape status: {result.scrape_status}")
                if result.scrape_status == "success":
                    print(f"   Content length: {len(result.company_description or '')}")
                    print(f"   Pages crawled: {len(result.pages_crawled or [])}")
                else:
                    print(f"   Async scrape error: {result.scrape_error}")
                    
            except Exception as e:
                print(f"❌ Async scraping test failed: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n✅ Debug analysis complete. Check debug_scraping.log for detailed logs.")
        
    except Exception as e:
        print(f"❌ Debug analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scraping_pipeline()