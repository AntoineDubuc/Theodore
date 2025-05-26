"""
Working Crawl4AI scraper using hybrid approach:
- Crawl4AI for robust web content extraction  
- Direct OpenAI API for AI-powered data extraction
This bypasses the LLMExtractionStrategy bug while maintaining full functionality
"""

import logging
import time
import asyncio
import json
import os
from typing import Dict, Optional, List, Any
from urllib.parse import urljoin, urlparse

from crawl4ai import AsyncWebCrawler
from src.models import CompanyData, CompanyIntelligenceConfig
import openai

logger = logging.getLogger(__name__)


class WorkingCrawl4AICompanyScraper:
    """Working company scraper using Crawl4AI + direct OpenAI API"""
    
    def __init__(self, config: CompanyIntelligenceConfig):
        self.config = config
        
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Define target pages to crawl per company
        self.target_pages = [
            "",  # Homepage
            "/about",
            "/about-us", 
            "/team",
            "/leadership",
            "/services",
            "/products",
            "/contact"
        ]
        
        # Company intelligence extraction prompt
        self.extraction_prompt = """You are an expert business intelligence analyst. Extract key company information from the webpage content below.

Extract and return the following information as valid JSON:
{
    "company_name": "Company name",
    "industry": "Primary industry or sector", 
    "business_model": "Business model (B2B, B2C, SaaS, etc.)",
    "company_description": "Brief company description",
    "target_market": "Target market or customer segment",
    "key_services": ["Service 1", "Service 2", "Service 3"],
    "location": "Company location/headquarters",
    "founding_year": "Year founded (if mentioned)",
    "tech_stack": ["Technology 1", "Technology 2"],
    "leadership_team": ["Leader Name - Title", "Leader Name - Title"],
    "value_proposition": "Main value proposition",
    "employee_count": "Number of employees (if mentioned)",
    "contact_info": {
        "email": "contact email",
        "phone": "phone number",
        "address": "address"
    }
}

Only include information that is clearly stated in the content. Use "unknown" for missing information.
Return only valid JSON, no other text.

Webpage content:
"""
    
    async def extract_with_openai(self, content: str, url: str) -> Dict:
        """Extract company intelligence using direct OpenAI API"""
        
        try:
            # Truncate content to fit within token limits
            max_content_length = 8000  # Conservative limit for gpt-4o-mini
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            
            # Call OpenAI API directly
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": self.extraction_prompt + content}
                ],
                max_tokens=1500,
                temperature=0.1
            )
            
            extracted_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                return json.loads(extracted_text)
            except json.JSONDecodeError:
                # If not valid JSON, try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', extracted_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    logger.warning(f"Could not parse JSON from OpenAI response for {url}")
                    return {"raw_extracted": extracted_text}
                    
        except Exception as e:
            logger.error(f"OpenAI extraction failed for {url}: {e}")
            return {}
    
    async def scrape_company_comprehensive(self, company_data: CompanyData) -> CompanyData:
        """Comprehensive multi-page scraping with AI-powered extraction"""
        
        start_time = time.time()
        base_url = self._normalize_url(company_data.website)
        
        logger.info(f"Starting comprehensive crawl of {company_data.name} using working hybrid approach")
        
        try:
            async with AsyncWebCrawler(
                headless=True,
                browser_type="chromium",
                verbose=False
            ) as crawler:
                
                # Crawl multiple pages and extract intelligence
                crawled_pages = []
                all_intelligence = []
                
                for page_path in self.target_pages:
                    try:
                        page_url = urljoin(base_url, page_path)
                        
                        # Skip if same as base URL
                        if page_url == base_url and page_path != "":
                            continue
                        
                        logger.info(f"Crawling and extracting from {page_url}")
                        
                        # Crawl with Crawl4AI (content extraction only)
                        result = await crawler.arun(
                            url=page_url,
                            timeout=30,
                            wait_for="networkidle"
                        )
                        
                        if result.success and result.markdown:
                            crawled_pages.append(page_url)
                            
                            # Store homepage content for reference
                            if not company_data.raw_content and page_path == "":
                                company_data.raw_content = result.cleaned_html[:self.config.max_content_length]
                            
                            # Extract intelligence using direct OpenAI API
                            intelligence_data = await self.extract_with_openai(result.markdown, page_url)
                            
                            if intelligence_data:
                                all_intelligence.append({
                                    'page_url': page_url,
                                    'page_path': page_path,
                                    'intelligence': intelligence_data
                                })
                                
                                logger.info(f"Successfully extracted intelligence from {page_url}")
                            else:
                                logger.warning(f"No intelligence extracted from {page_url}")
                        
                        # Rate limiting between pages
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        logger.warning(f"Failed to process {page_url}: {e}")
                        continue
                
                # Merge and apply all extracted intelligence
                merged_intelligence = self._merge_intelligence(all_intelligence)
                self._apply_intelligence_to_company(company_data, merged_intelligence)
                
                # Update crawling metadata
                company_data.pages_crawled = crawled_pages
                company_data.crawl_depth = len(crawled_pages)
                company_data.crawl_duration = time.time() - start_time
                company_data.scrape_status = "success"
                
                logger.info(f"Successfully extracted intelligence from {len(crawled_pages)} pages for {company_data.name}")
                
        except Exception as e:
            logger.error(f"Comprehensive crawl failed for {company_data.name}: {e}")
            company_data.scrape_status = "failed"
            company_data.scrape_error = str(e)
        
        return company_data
    
    def _merge_intelligence(self, all_intelligence: List[Dict]) -> Dict:
        """Intelligently merge extracted data from multiple pages"""
        
        if not all_intelligence:
            return {}
        
        # Initialize merged structure
        merged = {}
        
        # Process each page's intelligence
        for page_data in all_intelligence:
            intelligence = page_data.get('intelligence', {})
            page_path = page_data.get('page_path', '')
            
            # Merge intelligence data
            for key, value in intelligence.items():
                if value and value != "unknown" and value != "null":
                    # For lists, merge and deduplicate
                    if isinstance(value, list) and value:
                        existing = merged.get(key, [])
                        if isinstance(existing, list):
                            combined = existing + value
                            # Deduplicate while preserving order
                            seen = set()
                            deduped = []
                            for item in combined:
                                if item not in seen:
                                    seen.add(item)
                                    deduped.append(item)
                            merged[key] = deduped[:10]  # Limit to 10 items
                        else:
                            merged[key] = value[:10]
                    
                    # For objects, merge deeply
                    elif isinstance(value, dict) and value:
                        existing = merged.get(key, {})
                        if isinstance(existing, dict):
                            merged[key] = {**existing, **value}
                        else:
                            merged[key] = value
                    
                    # For strings, prioritize homepage and about pages
                    elif isinstance(value, str):
                        if not merged.get(key) or page_path in ["", "/about", "/about-us"]:
                            merged[key] = value
        
        return merged
    
    def _apply_intelligence_to_company(self, company_data: CompanyData, intelligence: Dict):
        """Apply merged intelligence to company data object"""
        
        try:
            # Direct mapping from extracted data
            if intelligence.get('company_name') and not company_data.name:
                company_data.name = intelligence['company_name']
            
            if intelligence.get('company_description'):
                company_data.company_description = intelligence['company_description']
            
            if intelligence.get('industry'):
                company_data.industry = intelligence['industry']
            
            if intelligence.get('business_model'):
                company_data.business_model = intelligence['business_model']
            
            if intelligence.get('target_market'):
                company_data.target_market = intelligence['target_market']
            
            if intelligence.get('key_services'):
                company_data.key_services = intelligence['key_services'][:5]
            
            if intelligence.get('location'):
                company_data.location = intelligence['location']
            
            if intelligence.get('founding_year'):
                company_data.founding_year = intelligence['founding_year']
            
            if intelligence.get('tech_stack'):
                company_data.tech_stack = intelligence['tech_stack'][:10]
            
            if intelligence.get('leadership_team'):
                company_data.leadership_team = intelligence['leadership_team'][:8]
            
            if intelligence.get('value_proposition'):
                company_data.value_proposition = intelligence['value_proposition']
            
            if intelligence.get('employee_count'):
                company_data.employee_count_range = intelligence['employee_count']
            
            if intelligence.get('contact_info'):
                company_data.contact_info = intelligence['contact_info']
            
        except Exception as e:
            logger.warning(f"Error applying intelligence to company data: {e}")
    
    def _normalize_url(self, url: str) -> str:
        """Normalize website URL"""
        if not url:
            raise ValueError("No website URL provided")
        
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        
        return url.rstrip('/')
    
    async def batch_scrape_companies(self, companies: List[CompanyData]) -> List[CompanyData]:
        """Batch scrape multiple companies with rate limiting"""
        
        processed_companies = []
        
        for i, company in enumerate(companies):
            logger.info(f"Processing company {i+1}/{len(companies)}: {company.name}")
            
            try:
                processed_company = await self.scrape_company_comprehensive(company)
                processed_companies.append(processed_company)
                
                # Rate limiting between companies
                if i < len(companies) - 1:
                    await asyncio.sleep(5)  # Longer delay for API rate limiting
                    
            except Exception as e:
                logger.error(f"Failed to process {company.name}: {e}")
                company.scrape_status = "failed"
                company.scrape_error = str(e)
                processed_companies.append(company)
        
        return processed_companies


# Synchronous wrapper for the main pipeline
class CompanyWebScraper:
    """Working wrapper that uses the hybrid Crawl4AI + OpenAI approach"""
    
    def __init__(self, config: CompanyIntelligenceConfig):
        self.config = config
        self.working_scraper = WorkingCrawl4AICompanyScraper(config)
    
    def scrape_company(self, company_data: CompanyData) -> CompanyData:
        """Synchronous wrapper for working company scraping"""
        
        try:
            # Check for OpenAI API key
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OPENAI_API_KEY is required for AI-powered extraction")
            
            # Run the async working scraper
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.working_scraper.scrape_company_comprehensive(company_data)
            )
            
            loop.close()
            return result
            
        except Exception as e:
            logger.error(f"Working scraper error for {company_data.name}: {e}")
            company_data.scrape_status = "failed"
            company_data.scrape_error = str(e)
            return company_data
    
    def batch_scrape_companies(self, companies: List[CompanyData]) -> List[CompanyData]:
        """Synchronous wrapper for batch working scraping"""
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.working_scraper.batch_scrape_companies(companies)
            )
            
            loop.close()
            return result
            
        except Exception as e:
            logger.error(f"Batch working scraping error: {e}")
            return companies