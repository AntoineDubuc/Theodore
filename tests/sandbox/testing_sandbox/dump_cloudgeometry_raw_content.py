#!/usr/bin/env python3
"""
CloudGeometry Raw Content Dumper
Extracts and dumps the raw scraped content from CloudGeometry research to analyze what was actually captured
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
sys.path.insert(0, project_root)

# Load environment variables
load_dotenv(os.path.join(project_root, '.env'))

from src.pinecone_client import PineconeClient
from src.models import CompanyIntelligenceConfig

class CloudGeometryContentDumper:
    def __init__(self):
        self.config = CompanyIntelligenceConfig()
        # Initialize Pinecone client with environment variables
        import os
        api_key = os.getenv('PINECONE_API_KEY')
        index_name = os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable not set")
        
        self.pinecone_client = PineconeClient(
            config=self.config,
            api_key=api_key,
            environment="gcp-starter",  # Default environment
            index_name=index_name
        )
        # Multiple possible names for CloudGeometry entries
        self.possible_names = [
            "CloudGeometry Success Test",
            "CloudGeometry", 
            "Cloud Geometry",
            "cloudgeometry"
        ]
        self.possible_websites = [
            "https://www.cloudgeometry.com",
            "https://cloudgeometry.com", 
            "https://cloudgeometry.io"
        ]
        
    async def find_cloudgeometry_data(self):
        """Find CloudGeometry company data in Pinecone"""
        print(f"🔍 Searching for CloudGeometry data...")
        
        try:
            stats = self.pinecone_client.get_index_stats()
            print(f"📊 Database contains {stats.get('total_vector_count', 0)} companies")
            
            # Search through all possible name variations
            found_companies = []
            
            for name in self.possible_names:
                company = self.pinecone_client.find_company_by_name(name)
                if company:
                    found_companies.append(company)
                    print(f"✅ Found by name '{name}': {company.name}")
                    print(f"   Website: {company.website}")
                    print(f"   Pages crawled: {getattr(company, 'pages_crawled', 'Unknown')}")
                    print(f"   Crawl duration: {getattr(company, 'crawl_duration', 'Unknown')}s")
                    print(f"   Created: {getattr(company, 'created_at', 'Unknown')}")
                    print(f"   Has raw content: {'✅' if getattr(company, 'raw_content', None) and getattr(company, 'raw_content') != 'unknown' else '❌'}")
                    print()
            
            if not found_companies:
                print(f"❌ No CloudGeometry companies found")
                return None
            
            # If multiple found, prefer the one with the most data
            best_company = None
            best_score = 0
            
            for company in found_companies:
                score = 0
                
                # Score based on data availability
                if getattr(company, 'pages_crawled', None):
                    if isinstance(company.pages_crawled, list):
                        score += len(company.pages_crawled)
                    elif isinstance(company.pages_crawled, int):
                        score += company.pages_crawled
                
                if getattr(company, 'raw_content', None) and company.raw_content != 'unknown':
                    score += 100  # High value for having raw content
                
                if getattr(company, 'crawl_duration', None):
                    score += 10  # Has processing time
                
                # Prefer .com website over .io
                if company.website and '.com' in company.website:
                    score += 5
                
                print(f"📊 Company '{company.name}' score: {score}")
                
                if score > best_score:
                    best_score = score
                    best_company = company
            
            if best_company:
                print(f"🎯 Selected best match: {best_company.name} (score: {best_score})")
                return best_company
            else:
                print(f"⚠️  Found companies but none have significant data")
                return found_companies[0]  # Return first found if none are clearly better
            
            print(f"❌ No CloudGeometry data found in database")
            return None
            
        except Exception as e:
            print(f"❌ Error searching database: {e}")
            return None
    
    def dump_raw_content(self, company_data, output_file):
        """Dump all raw content to text file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("CLOUDGEOMETRY RAW CONTENT DUMP\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Company: {company_data.name}\n")
            f.write(f"Website: {company_data.website}\n")
            f.write(f"Pages Crawled: {company_data.pages_crawled}\n")
            f.write(f"Crawl Duration: {company_data.crawl_duration}s\n")
            f.write("=" * 80 + "\n\n")
            
            # Dump raw content
            if company_data.raw_content and company_data.raw_content != "unknown":
                f.write("RAW CONTENT (Phase 4 LLM Analysis Output):\n")
                f.write("-" * 60 + "\n")
                f.write(company_data.raw_content)
                f.write("\n\n")
            else:
                f.write("❌ NO RAW CONTENT AVAILABLE (Phase 4 failed)\n\n")
            
            # Dump scraped content details if available
            if hasattr(company_data, 'scraped_content_details') and company_data.scraped_content_details:
                f.write("SCRAPED CONTENT DETAILS (Individual Pages):\n")
                f.write("-" * 60 + "\n")
                
                if isinstance(company_data.scraped_content_details, str):
                    try:
                        content_details = json.loads(company_data.scraped_content_details)
                    except:
                        content_details = company_data.scraped_content_details
                else:
                    content_details = company_data.scraped_content_details
                
                if isinstance(content_details, dict):
                    for url, content in content_details.items():
                        f.write(f"\n{'='*20} PAGE: {url} {'='*20}\n")
                        f.write(f"{content}\n")
                elif isinstance(content_details, list):
                    for i, page in enumerate(content_details, 1):
                        if isinstance(page, dict) and 'url' in page and 'content' in page:
                            f.write(f"\n{'='*10} PAGE {i}: {page['url']} {'='*10}\n")
                            f.write(f"{page['content']}\n")
                        else:
                            f.write(f"\n{'='*10} PAGE {i} {'='*10}\n")
                            f.write(f"{page}\n")
                else:
                    f.write(str(content_details))
            else:
                f.write("❌ NO INDIVIDUAL PAGE CONTENT AVAILABLE\n")
            
            # Dump scraped URLs if available
            if company_data.scraped_urls:
                f.write(f"\n\nSCRAPED URLS ({len(company_data.scraped_urls)} pages):\n")
                f.write("-" * 60 + "\n")
                for i, url in enumerate(company_data.scraped_urls, 1):
                    f.write(f"{i:3d}. {url}\n")
            
            # Dump all available field data
            f.write("\n\nALL COMPANY DATA FIELDS:\n")
            f.write("-" * 60 + "\n")
            company_dict = company_data.__dict__
            for field, value in sorted(company_dict.items()):
                if field in ['embedding']:  # Skip large fields
                    f.write(f"{field}: [EMBEDDING VECTOR - {len(value) if value else 0} dimensions]\n")
                elif isinstance(value, str) and len(str(value)) > 200:
                    f.write(f"{field}: {str(value)[:200]}... (truncated, {len(str(value))} total chars)\n")
                else:
                    f.write(f"{field}: {value}\n")
    
    def analyze_content_structure(self, company_data):
        """Analyze what content is actually available"""
        print(f"\n📊 CONTENT ANALYSIS:")
        print(f"   Company Name: {company_data.name}")
        print(f"   Website: {company_data.website}")
        print(f"   Pages Crawled: {company_data.pages_crawled}")
        print(f"   Crawl Duration: {company_data.crawl_duration}s")
        
        # Check raw content
        if company_data.raw_content and company_data.raw_content != "unknown":
            print(f"   Raw Content: ✅ {len(company_data.raw_content):,} characters")
        else:
            print(f"   Raw Content: ❌ Not available")
        
        # Check scraped content details
        if hasattr(company_data, 'scraped_content_details') and company_data.scraped_content_details:
            print(f"   Individual Pages: ✅ Available")
        else:
            print(f"   Individual Pages: ❌ Not available")
        
        # Check scraped URLs
        if company_data.scraped_urls:
            print(f"   Scraped URLs: ✅ {len(company_data.scraped_urls)} URLs")
        else:
            print(f"   Scraped URLs: ❌ Not available")
        
        # Check key business fields
        key_fields = ['company_description', 'industry', 'business_model', 'target_market', 
                     'founding_year', 'location', 'employee_count_range']
        extracted_fields = 0
        for field in key_fields:
            value = getattr(company_data, field, "unknown")
            if value and value != "unknown" and value != "":
                extracted_fields += 1
        
        print(f"   Key Business Fields: {extracted_fields}/{len(key_fields)} extracted")
        
        return {
            'has_raw_content': bool(company_data.raw_content and company_data.raw_content != "unknown"),
            'has_individual_pages': bool(hasattr(company_data, 'scraped_content_details') and company_data.scraped_content_details),
            'has_scraped_urls': bool(company_data.scraped_urls),
            'key_fields_extracted': extracted_fields,
            'total_key_fields': len(key_fields)
        }

async def main():
    """Main execution function"""
    dumper = CloudGeometryContentDumper()
    
    print("🚀 CloudGeometry Raw Content Dumper")
    print("=" * 50)
    
    # Find CloudGeometry data
    company_data = await dumper.find_cloudgeometry_data()
    if not company_data:
        print("❌ Cannot proceed - CloudGeometry data not found")
        return
    
    # Analyze content structure
    analysis = dumper.analyze_content_structure(company_data)
    
    # Determine output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/Users/antoinedubuc/Desktop/AI_Goodies/Theodore/tests/reports/cloudgeometry_raw_content_{timestamp}.txt"
    
    # Dump content
    print(f"\n📝 Dumping raw content to: {output_file}")
    dumper.dump_raw_content(company_data, output_file)
    
    # Report results
    print(f"\n✅ Content dump complete!")
    print(f"   Output file: {output_file}")
    print(f"   File size: {os.path.getsize(output_file):,} bytes")
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"   Raw Content Available: {'✅' if analysis['has_raw_content'] else '❌'}")
    print(f"   Individual Pages Available: {'✅' if analysis['has_individual_pages'] else '❌'}")
    print(f"   Scraped URLs Available: {'✅' if analysis['has_scraped_urls'] else '❌'}")
    print(f"   Key Fields Extracted: {analysis['key_fields_extracted']}/{analysis['total_key_fields']}")
    
    if analysis['has_raw_content']:
        print(f"\n💡 The raw content shows what the LLM analysis produced from the 100 pages.")
        print(f"   You can analyze this to see what information was actually available.")
    else:
        print(f"\n⚠️  No processed content available - Phase 4 LLM aggregation likely failed.")
        print(f"   The individual page content may still be in the database.")

if __name__ == "__main__":
    asyncio.run(main())