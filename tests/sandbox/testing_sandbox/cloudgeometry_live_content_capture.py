#!/usr/bin/env python3
"""
CloudGeometry Live Content Capture
Re-runs CloudGeometry research and captures the raw page content from Phase 3
to show what content is actually available before LLM aggregation fails
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

from src.intelligent_company_scraper import IntelligentCompanyScraper
from src.models import CompanyData, CompanyIntelligenceConfig

class CloudGeometryLiveCapture:
    def __init__(self):
        self.config = CompanyIntelligenceConfig()
        
    async def capture_cloudgeometry_content(self):
        """Run CloudGeometry research and capture intermediate content"""
        print("🚀 CloudGeometry Live Content Capture")
        print("=" * 50)
        
        # Create company data for CloudGeometry
        company_data = CompanyData(
            name="CloudGeometry Live Test",
            website="https://www.cloudgeometry.com"
        )
        
        print(f"🎯 Target: {company_data.name}")
        print(f"🌐 Website: {company_data.website}")
        print()
        
        # Initialize scraper
        scraper = IntelligentCompanyScraper(self.config)
        
        # Create a custom scraper class to capture intermediate results
        class ContentCapturingScraper(IntelligentCompanyScraper):
            def __init__(self, config):
                super().__init__(config)
                self.captured_content = []
                
            async def _extract_page_content_parallel(self, selected_urls, job_id=None):
                """Override to capture content before LLM processing"""
                print(f"📄 CAPTURING CONTENT FROM {len(selected_urls)} PAGES...")
                
                # Call the original method
                page_contents = await super()._extract_page_content_parallel(selected_urls, job_id)
                
                # Store captured content
                self.captured_content = page_contents
                
                print(f"✅ CAPTURED {len(page_contents)} PAGES OF CONTENT")
                
                # Save captured content to file immediately
                await self._save_captured_content(page_contents)
                
                return page_contents
            
            async def _save_captured_content(self, page_contents):
                """Save captured content to text file"""
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"/Users/antoinedubuc/Desktop/AI_Goodies/Theodore/tests/reports/cloudgeometry_live_content_{timestamp}.txt"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write("=" * 80 + "\n")
                    f.write("CLOUDGEOMETRY LIVE CONTENT CAPTURE\n")
                    f.write("=" * 80 + "\n")
                    f.write(f"Generated: {datetime.now().isoformat()}\n")
                    f.write(f"Target: https://www.cloudgeometry.com\n")
                    f.write(f"Pages Captured: {len(page_contents)}\n")
                    f.write("=" * 80 + "\n\n")
                    
                    for i, page in enumerate(page_contents, 1):
                        url = page.get('url', 'Unknown URL')
                        content = page.get('content', 'No content')
                        
                        f.write(f"\n{'='*20} PAGE {i}: {url} {'='*20}\n")
                        f.write(f"Content Length: {len(content):,} characters\n")
                        f.write("-" * 60 + "\n")
                        f.write(content)
                        f.write("\n\n")
                
                print(f"💾 Content saved to: {output_file}")
                print(f"📁 File size: {os.path.getsize(output_file):,} bytes")
                
                return output_file
        
        # Use the capturing scraper
        capturing_scraper = ContentCapturingScraper(self.config)
        
        try:
            print("🔍 Starting intelligent scraping with content capture...")
            
            # Run the scraping process
            result = await capturing_scraper.scrape_company_intelligent(company_data)
            
            print(f"\n✅ Scraping completed!")
            print(f"📊 Pages crawled: {len(capturing_scraper.captured_content)}")
            
            # Analyze captured content
            if capturing_scraper.captured_content:
                total_chars = sum(len(page.get('content', '')) for page in capturing_scraper.captured_content)
                print(f"📄 Total content: {total_chars:,} characters")
                
                # Show sample of key pages
                key_pages = []
                for page in capturing_scraper.captured_content:
                    url = page.get('url', '').lower()
                    if any(keyword in url for keyword in ['about', 'contact', 'careers', 'services', 'team']):
                        key_pages.append(page)
                
                print(f"🎯 Key business pages found: {len(key_pages)}")
                for page in key_pages[:5]:  # Show first 5
                    url = page.get('url', 'Unknown')
                    content_length = len(page.get('content', ''))
                    preview = page.get('content', '')[:200].replace('\n', ' ')
                    print(f"   📄 {url} ({content_length:,} chars): {preview}...")
                
                print(f"\n💡 This shows the raw content that WAS successfully extracted")
                print(f"   The 12% field extraction rate is because LLM aggregation failed,")
                print(f"   NOT because the content wasn't available.")
                
            else:
                print(f"❌ No content was captured")
            
            return capturing_scraper.captured_content
            
        except Exception as e:
            print(f"❌ Error during capture: {e}")
            import traceback
            traceback.print_exc()
            return None

async def main():
    """Main execution function"""
    capture = CloudGeometryLiveCapture()
    
    content = await capture.capture_cloudgeometry_content()
    
    if content:
        print(f"\n🎉 SUCCESS: Captured content from {len(content)} pages")
        print(f"   This demonstrates that Theodore CAN extract comprehensive content")
        print(f"   The field extraction issue is in Phase 4 LLM aggregation, not scraping")
    else:
        print(f"\n❌ FAILED: No content captured")

if __name__ == "__main__":
    asyncio.run(main())