"""
Enhanced Crawl4AI scraper with specialized sales intelligence extraction
Uses different prompts for different page types to maximize intelligence gathering
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
from src.enhanced_extraction_prompts import (
    SALES_INTELLIGENCE_PROMPT,
    LEADERSHIP_INTELLIGENCE_PROMPT, 
    PRODUCT_INTELLIGENCE_PROMPT,
    NEWS_INTELLIGENCE_PROMPT
)
import openai

logger = logging.getLogger(__name__)


class EnhancedCrawl4AICompanyScraper:
    """Enhanced company scraper with specialized sales intelligence extraction"""
    
    def __init__(self, config: CompanyIntelligenceConfig):
        self.config = config
        
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Enhanced target pages with specialized extraction
        self.page_configs = [
            {"path": "", "type": "general", "priority": "high"},  # Homepage
            {"path": "/about", "type": "general", "priority": "high"},
            {"path": "/about-us", "type": "general", "priority": "high"},
            {"path": "/team", "type": "leadership", "priority": "high"},
            {"path": "/leadership", "type": "leadership", "priority": "high"},
            {"path": "/management", "type": "leadership", "priority": "medium"},
            {"path": "/executives", "type": "leadership", "priority": "medium"},
            {"path": "/services", "type": "product", "priority": "high"},
            {"path": "/products", "type": "product", "priority": "high"},
            {"path": "/solutions", "type": "product", "priority": "high"},
            {"path": "/platform", "type": "product", "priority": "medium"},
            {"path": "/news", "type": "news", "priority": "medium"},
            {"path": "/press", "type": "news", "priority": "medium"},
            {"path": "/blog", "type": "news", "priority": "low"},
            {"path": "/contact", "type": "general", "priority": "low"},
            {"path": "/careers", "type": "general", "priority": "low"},
            {"path": "/investors", "type": "general", "priority": "medium"},
            {"path": "/partners", "type": "product", "priority": "medium"}
        ]
    
    def _get_prompt_for_page_type(self, page_type: str) -> str:
        """Get specialized prompt based on page type"""
        prompt_map = {
            "general": SALES_INTELLIGENCE_PROMPT,
            "leadership": LEADERSHIP_INTELLIGENCE_PROMPT,
            "product": PRODUCT_INTELLIGENCE_PROMPT,
            "news": NEWS_INTELLIGENCE_PROMPT
        }
        return prompt_map.get(page_type, SALES_INTELLIGENCE_PROMPT)
    
    async def extract_with_specialized_prompt(self, content: str, url: str, page_type: str) -> Dict:
        """Extract intelligence using specialized prompts for different page types"""
        
        try:
            prompt = self._get_prompt_for_page_type(page_type)
            
            # Truncate content to fit within token limits
            max_content_length = 8000
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            
            # Call OpenAI API with specialized prompt
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt + content}
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            extracted_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                data = json.loads(extracted_text)
                # Add metadata about extraction
                data["_extraction_metadata"] = {
                    "page_type": page_type,
                    "url": url,
                    "extraction_timestamp": time.time()
                }
                return data
            except json.JSONDecodeError:
                # If not valid JSON, try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', extracted_text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    data["_extraction_metadata"] = {
                        "page_type": page_type,
                        "url": url,
                        "extraction_timestamp": time.time()
                    }
                    return data
                else:
                    logger.warning(f"Could not parse JSON from specialized extraction for {url}")
                    return {
                        "raw_extracted": extracted_text,
                        "_extraction_metadata": {
                            "page_type": page_type,
                            "url": url,
                            "extraction_timestamp": time.time(),
                            "parse_error": True
                        }
                    }
                    
        except Exception as e:
            logger.error(f"Specialized extraction failed for {url}: {e}")
            return {}
    
    async def scrape_company_comprehensive(self, company_data: CompanyData) -> CompanyData:
        """Enhanced comprehensive scraping with specialized intelligence extraction"""
        
        start_time = time.time()
        base_url = self._normalize_url(company_data.website)
        
        logger.info(f"Starting enhanced intelligence extraction for {company_data.name}")
        
        try:
            async with AsyncWebCrawler(
                headless=True,
                browser_type="chromium",
                verbose=False
            ) as crawler:
                
                # Track all extractions by type
                extractions_by_type = {
                    "general": [],
                    "leadership": [],
                    "product": [],
                    "news": []
                }
                
                crawled_pages = []
                
                # Process pages by priority
                high_priority_pages = [p for p in self.page_configs if p["priority"] == "high"]
                medium_priority_pages = [p for p in self.page_configs if p["priority"] == "medium"]
                low_priority_pages = [p for p in self.page_configs if p["priority"] == "low"]
                
                for page_group in [high_priority_pages, medium_priority_pages, low_priority_pages]:
                    for page_config in page_group:
                        try:
                            page_url = urljoin(base_url, page_config["path"])
                            
                            # Skip if same as base URL
                            if page_url == base_url and page_config["path"] != "":
                                continue
                            
                            logger.info(f"Extracting {page_config['type']} intelligence from {page_url}")
                            
                            # Crawl with Crawl4AI
                            result = await crawler.arun(
                                url=page_url,
                                timeout=30,
                                wait_for="networkidle"
                            )
                            
                            if result.success and result.markdown:
                                crawled_pages.append(page_url)
                                
                                # Store homepage content
                                if not company_data.raw_content and page_config["path"] == "":
                                    company_data.raw_content = result.cleaned_html[:self.config.max_content_length]
                                
                                # Extract intelligence with specialized prompt
                                intelligence_data = await self.extract_with_specialized_prompt(
                                    result.markdown, 
                                    page_url, 
                                    page_config["type"]
                                )
                                
                                if intelligence_data:
                                    extractions_by_type[page_config["type"]].append({
                                        'page_url': page_url,
                                        'page_path': page_config["path"],
                                        'intelligence': intelligence_data
                                    })
                                    
                                    logger.info(f"Successfully extracted {page_config['type']} intelligence from {page_url}")
                            
                            # Rate limiting
                            await asyncio.sleep(2)
                            
                        except Exception as e:
                            logger.warning(f"Failed to process {page_url}: {e}")
                            continue
                
                # Merge and apply specialized intelligence
                comprehensive_intelligence = self._merge_specialized_intelligence(extractions_by_type)
                self._apply_comprehensive_intelligence(company_data, comprehensive_intelligence)
                
                # Update metadata
                company_data.pages_crawled = crawled_pages
                company_data.crawl_depth = len(crawled_pages)
                company_data.crawl_duration = time.time() - start_time
                company_data.scrape_status = "success"
                
                logger.info(f"Enhanced extraction completed: {len(crawled_pages)} pages, {sum(len(extractions) for extractions in extractions_by_type.values())} specialized extractions")
                
        except Exception as e:
            logger.error(f"Enhanced extraction failed for {company_data.name}: {e}")
            company_data.scrape_status = "failed"
            company_data.scrape_error = str(e)
        
        return company_data
    
    def _merge_specialized_intelligence(self, extractions_by_type: Dict[str, List[Dict]]) -> Dict:
        """Merge specialized intelligence from different page types"""
        
        merged = {
            "company_profile": {},
            "business_metrics": {},
            "sales_intelligence": {},
            "sales_triggers": {},
            "contact_intelligence": {},
            "competitive_landscape": {},
            "leadership_analysis": {},
            "product_analysis": {},
            "recent_developments": []
        }
        
        # Merge general intelligence (homepage, about pages)
        for extraction in extractions_by_type["general"]:
            data = extraction["intelligence"]
            
            for section in ["company_profile", "business_metrics", "sales_intelligence", 
                           "sales_triggers", "contact_intelligence", "competitive_landscape"]:
                if section in data:
                    self._merge_section(merged[section], data[section])
        
        # Merge leadership intelligence
        leadership_data = {"executives": [], "organizational_insights": {}, "sales_targeting": {}}
        for extraction in extractions_by_type["leadership"]:
            data = extraction["intelligence"]
            if "leadership_team" in data:
                leadership_data["executives"].extend(data["leadership_team"])
            if "organizational_insights" in data:
                self._merge_section(leadership_data["organizational_insights"], data["organizational_insights"])
            if "sales_targeting" in data:
                self._merge_section(leadership_data["sales_targeting"], data["sales_targeting"])
        merged["leadership_analysis"] = leadership_data
        
        # Merge product intelligence
        product_data = {"offerings": {}, "market_intelligence": {}, "competitive_positioning": {}, "sales_opportunities": {}}
        for extraction in extractions_by_type["product"]:
            data = extraction["intelligence"]
            for section in ["product_portfolio", "market_intelligence", "competitive_positioning", "sales_opportunities"]:
                if section in data:
                    target_key = section.replace("product_portfolio", "offerings")
                    self._merge_section(product_data[target_key], data[section])
        merged["product_analysis"] = product_data
        
        # Merge news/developments
        for extraction in extractions_by_type["news"]:
            data = extraction["intelligence"]
            if "recent_developments" in data:
                merged["recent_developments"].extend(data["recent_developments"])
        
        return merged
    
    def _merge_section(self, target: Dict, source: Dict):
        """Helper to merge dictionary sections"""
        for key, value in source.items():
            if isinstance(value, list):
                if key not in target:
                    target[key] = []
                target[key].extend(value)
                # Deduplicate
                target[key] = list(dict.fromkeys(target[key]))[:15]
            elif isinstance(value, dict):
                if key not in target:
                    target[key] = {}
                target[key].update(value)
            elif value and value != "unknown":
                target[key] = value
    
    def _apply_comprehensive_intelligence(self, company_data: CompanyData, intelligence: Dict):
        """Apply comprehensive intelligence to company data"""
        
        try:
            # Company profile
            profile = intelligence.get("company_profile", {})
            if profile.get("company_name"):
                company_data.name = profile["company_name"]
            if profile.get("industry"):
                company_data.industry = profile["industry"]
            if profile.get("business_model"):
                company_data.business_model = profile["business_model"]
            if profile.get("company_description"):
                company_data.company_description = profile["company_description"]
            if profile.get("target_market"):
                company_data.target_market = profile["target_market"]
            
            # Business metrics
            metrics = intelligence.get("business_metrics", {})
            if metrics.get("employee_count"):
                company_data.employee_count_range = metrics["employee_count"]
            
            # Sales intelligence
            sales_intel = intelligence.get("sales_intelligence", {})
            if sales_intel.get("key_decision_makers"):
                company_data.leadership_team = sales_intel["key_decision_makers"][:8]
            if sales_intel.get("technology_stack"):
                company_data.tech_stack = sales_intel["technology_stack"][:10]
            
            # Product analysis
            product_analysis = intelligence.get("product_analysis", {})
            if product_analysis.get("offerings", {}).get("primary_offerings"):
                company_data.key_services = product_analysis["offerings"]["primary_offerings"][:5]
            
            # Contact intelligence
            contact = intelligence.get("contact_intelligence", {})
            if contact.get("headquarters"):
                company_data.location = contact["headquarters"]
            if contact.get("contact_methods"):
                company_data.contact_info = contact["contact_methods"]
            
            # Leadership analysis
            leadership = intelligence.get("leadership_analysis", {})
            if leadership.get("executives"):
                # Enhance leadership team with structured data
                enhanced_leadership = []
                for exec_data in leadership["executives"][:8]:
                    if isinstance(exec_data, dict):
                        name = exec_data.get("name", "")
                        title = exec_data.get("title", "")
                        enhanced_leadership.append(f"{name} - {title}")
                    else:
                        enhanced_leadership.append(str(exec_data))
                company_data.leadership_team = enhanced_leadership
            
        except Exception as e:
            logger.warning(f"Error applying comprehensive intelligence: {e}")
    
    def _normalize_url(self, url: str) -> str:
        """Normalize website URL"""
        if not url:
            raise ValueError("No website URL provided")
        
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        
        return url.rstrip('/')


# Synchronous wrapper
class EnhancedCompanyWebScraper:
    """Enhanced wrapper with comprehensive sales intelligence"""
    
    def __init__(self, config: CompanyIntelligenceConfig):
        self.config = config
        self.enhanced_scraper = EnhancedCrawl4AICompanyScraper(config)
    
    def scrape_company(self, company_data: CompanyData) -> CompanyData:
        """Enhanced company scraping with sales intelligence"""
        
        try:
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OPENAI_API_KEY is required for enhanced extraction")
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.enhanced_scraper.scrape_company_comprehensive(company_data)
            )
            
            loop.close()
            return result
            
        except Exception as e:
            logger.error(f"Enhanced scraper error for {company_data.name}: {e}")
            company_data.scrape_status = "failed"
            company_data.scrape_error = str(e)
            return company_data