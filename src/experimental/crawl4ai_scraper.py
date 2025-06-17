"""
Advanced company intelligence scraper using Crawl4AI with LLMExtractionStrategy
Proper AI-powered extraction using Pydantic schemas and custom prompts
"""

import logging
import time
import asyncio
import json
import os
import hashlib
from typing import Dict, Optional, List, Any
from urllib.parse import urljoin, urlparse
from pydantic import BaseModel, Field
from enum import Enum

from crawl4ai import AsyncWebCrawler, LLMConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.async_configs import CacheMode
from src.models import CompanyData, CompanyIntelligenceConfig

logger = logging.getLogger(__name__)


# Define Pydantic schema for structured extraction
class CompanyIntelligence(BaseModel):
    company_name: str = Field(description="Company name")
    industry: str = Field(description="Primary industry or sector")
    business_model: str = Field(description="Business model (B2B, B2C, SaaS, etc.)")
    company_description: str = Field(description="Brief company description")
    target_market: str = Field(description="Target market or customer segment")
    key_services: List[str] = Field(description="List of key services or products")
    location: str = Field(description="Company location")
    founding_year: str = Field(description="Year founded (if mentioned)")
    tech_stack: List[str] = Field(description="Technologies used")
    leadership_team: List[str] = Field(description="Leadership team members with titles")
    value_proposition: str = Field(description="Main value proposition")

# Rebuild model to resolve any ForwardRef issues
CompanyIntelligence.model_rebuild()


class PageType(Enum):
    """Enum for different page types and their importance"""
    HOMEPAGE = ("homepage", 1.0, "")
    ABOUT = ("about", 0.9, "/about")
    ABOUT_US = ("about_us", 0.9, "/about-us")
    COMPANY = ("company", 0.8, "/company")
    SERVICES = ("services", 0.7, "/services")
    PRODUCTS = ("products", 0.7, "/products")
    SOLUTIONS = ("solutions", 0.6, "/solutions")
    TEAM = ("team", 0.5, "/team")
    LEADERSHIP = ("leadership", 0.5, "/leadership")
    PRICING = ("pricing", 0.9, "/pricing")
    CUSTOMERS = ("customers", 0.8, "/customers")
    CASE_STUDIES = ("case-studies", 0.8, "/case-studies")
    CAREERS = ("careers", 0.3, "/careers")
    CONTACT = ("contact", 0.2, "/contact")
    
    def __init__(self, name: str, priority: float, path: str):
        self.page_name = name
        self.priority = priority
        self.path = path


class Crawl4AICompanyScraper:
    """Advanced company scraper using Crawl4AI with intelligent URL discovery"""
    
    def __init__(self, config: CompanyIntelligenceConfig, bedrock_client=None):
        self.config = config
        self.bedrock_client = bedrock_client
        
        # Initialize intelligent URL discovery if bedrock client available
        if self.bedrock_client:
            from src.intelligent_url_discovery import IntelligentURLDiscovery
            self.url_discovery = IntelligentURLDiscovery(self.bedrock_client)
        else:
            self.url_discovery = None
        
        # Define target pages with priorities (fallback)
        self.target_pages = [page_type for page_type in PageType]
        
        # Enhanced extraction instruction for better results
        self.extraction_instruction = """
Extract comprehensive company information with focus on:
1. Business model and revenue streams
2. Target market and customer segments  
3. Key products/services and differentiators
4. Leadership team and company culture
5. Technology stack and innovation indicators
6. Market position and competitive advantages

Be specific about industry classification and company size indicators.
Use 'unknown' only when information is genuinely not available.
Prioritize factual information over marketing language.
"""
    
    def _create_extraction_strategy(self, page_type: PageType = None) -> LLMExtractionStrategy:
        """Create optimized LLM extraction strategy based on page type"""
        
        # Check for OpenAI API key
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if openai_api_key and openai_api_key != "your-openai-api-key-here":
            logger.info(f"Creating LLM extraction strategy for {page_type.page_name if page_type else 'general'} page")
            
            # Use the working LLMConfig format (fixed ForwardRef issue)
            try:
                # Optimize model selection based on page importance
                if page_type and page_type.priority >= 0.7:
                    # High-value pages: Use more capable model
                    provider = "openai/gpt-4o-mini"
                    max_tokens = 2500
                    temperature = 0.05  # More deterministic for important pages
                else:
                    # Standard pages: Use cost-effective model
                    provider = "openai/gpt-4o-mini" 
                    max_tokens = 2000
                    temperature = 0.1
                
                llm_config = LLMConfig(
                    provider=provider,
                    api_token=openai_api_key
                )
                
                # Optimize chunking based on typical page content
                chunk_threshold = self._get_optimal_chunk_size(page_type)
                
                return LLMExtractionStrategy(
                    llm_config=llm_config,
                    schema=CompanyIntelligence.model_json_schema(),
                    extraction_type="schema",
                    instruction=self.extraction_instruction,
                    chunk_token_threshold=chunk_threshold,
                    overlap_rate=0.05,  # Minimal overlap for company pages
                    apply_chunking=chunk_threshold < 3000,  # Disable for small content
                    extra_args={
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "top_p": 0.9
                    }
                )
            except Exception as e:
                logger.error(f"Failed to create LLMConfig: {e}")
                raise ValueError(
                    f"Failed to initialize LLM extraction strategy: {e}. "
                    "Please ensure OPENAI_API_KEY is properly set."
                )
        else:
            # Try to use Bedrock (requires custom implementation)
            logger.info("OpenAI API key not found, attempting Bedrock integration")
            
            # For now, raise an error since Bedrock integration for Crawl4AI needs more setup
            raise ValueError(
                "OpenAI API key required for LLM extraction. "
                "Please set OPENAI_API_KEY in your .env file. "
                "Bedrock integration for Crawl4AI is not yet implemented."
            )
    
    def _get_optimal_chunk_size(self, page_type: PageType = None) -> int:
        """Get optimal chunk size based on page type and expected content"""
        
        if not page_type:
            return 2000
        
        # Optimize chunking based on page type
        chunk_sizes = {
            PageType.HOMEPAGE: 2500,    # May have more content
            PageType.ABOUT: 2000,       # Moderate content
            PageType.ABOUT_US: 2000,    # Moderate content
            PageType.COMPANY: 2000,     # Moderate content
            PageType.SERVICES: 1800,    # Often list-based
            PageType.PRODUCTS: 1800,    # Often list-based
            PageType.SOLUTIONS: 1500,   # Usually brief
            PageType.TEAM: 1500,        # Usually brief
            PageType.LEADERSHIP: 1500,  # Usually brief
            PageType.CAREERS: 1000,     # Minimal extraction needed
            PageType.CONTACT: 800       # Minimal extraction needed
        }
        
        return chunk_sizes.get(page_type, 2000)
    
    def _create_crawler_config(self, page_type: PageType, company_id: str, extraction_strategy: LLMExtractionStrategy) -> CrawlerRunConfig:
        """Create optimized crawler configuration with caching and filtering"""
        
        # Create company-specific session for caching
        session_id = f"theodore_{hashlib.md5(company_id.encode()).hexdigest()[:8]}"
        
        # Build CSS selector string
        css_selector = ", ".join([
            "main", "article", ".content", ".main-content", ".about-section", 
            ".company-info", "[role='main']", ".page-content"
        ])
        
        # Tags to exclude for cleaner extraction
        excluded_tags = [
            "nav", "footer", "aside", "script", "style", 
            "noscript", "iframe", "form", "input", "button"
        ]
        
        config = CrawlerRunConfig(
            # Extraction strategy
            extraction_strategy=extraction_strategy,
            
            # Content filtering (Low-risk improvements)
            word_count_threshold=50,  # Higher threshold to filter noise
            css_selector=css_selector,  # Target main content areas
            excluded_tags=excluded_tags,  # Remove navigation/ads
            only_text=True,  # Strip HTML formatting
            remove_forms=True,  # Remove form elements
            exclude_external_links=True,  # Remove external links
            exclude_social_media_links=True,  # Remove social media links
            
            # Caching (Performance improvement)
            cache_mode=CacheMode.ENABLED,  # Enable intelligent caching
            session_id=session_id,  # Company-specific caching
            
            # Page interaction
            wait_until="domcontentloaded",  # Faster than networkidle
            page_timeout=25000,  # Slightly longer timeout
            delay_before_return_html=1.0,  # Reduced delay
            
            # Logging
            verbose=False  # Keep minimal logging
        )
        
        return config
    
    async def scrape_company_comprehensive(self, company_data: CompanyData) -> CompanyData:
        """Comprehensive multi-page scraping with AI-powered extraction"""
        
        start_time = time.time()
        base_url = self._normalize_url(company_data.website)
        
        logger.info(f"Starting AI-powered crawl of {company_data.name}")
        
        try:
            # Note: Extraction strategies now created per-page for optimization
            logger.info("Starting optimized multi-page AI extraction with caching and filtering...")
            
            async with AsyncWebCrawler(
                headless=True,
                browser_type="chromium",
                verbose=False
            ) as crawler:
                
                # Discover URLs intelligently or fall back to patterns
                if self.url_discovery:
                    logger.info("Using intelligent URL discovery...")
                    try:
                        target_urls = await self.url_discovery.get_crawl_priority_list(
                            base_url, company_data.name
                        )
                        logger.info(f"Discovered {len(target_urls)} priority URLs to crawl")
                    except Exception as e:
                        logger.warning(f"Intelligent URL discovery failed: {e}, falling back to patterns")
                        target_urls = [(urljoin(base_url, page_type.path), page_type.page_name, page_type.priority) 
                                     for page_type in self.target_pages]
                else:
                    logger.info("Using fallback URL patterns...")
                    target_urls = [(urljoin(base_url, page_type.path), page_type.page_name, page_type.priority) 
                                 for page_type in self.target_pages]
                
                # Crawl discovered pages and extract intelligence
                crawled_pages = []
                all_intelligence = []
                
                for page_url, page_type_name, priority in target_urls:
                    try:
                        # Skip if same as base URL (except homepage)
                        if page_url == base_url and not page_url.endswith('/'):
                            continue
                        
                        logger.info(f"AI-extracting from {page_url} ({page_type_name})")
                        
                        # Find corresponding PageType for extraction strategy, or use default
                        page_type = None
                        for pt in self.target_pages:
                            if pt.page_name == page_type_name:
                                page_type = pt
                                break
                        
                        if not page_type:
                            # Create a default PageType for unknown types
                            page_type = PageType.HOMEPAGE if page_type_name == 'homepage' else PageType.ABOUT
                        
                        # Create optimized extraction strategy for this page type
                        page_extraction_strategy = self._create_extraction_strategy(page_type)
                        
                        # Create optimized crawler configuration
                        config = self._create_crawler_config(
                            page_type=page_type,
                            company_id=f"{company_data.name}_{company_data.website}",
                            extraction_strategy=page_extraction_strategy
                        )
                        
                        # Crawl with optimized configuration
                        result = await crawler.arun(
                            url=page_url,
                            config=config,
                            timeout=30  # Increased timeout for better reliability
                        )
                        
                        if result.success:
                            crawled_pages.append(page_url)
                            
                            # Store homepage content for reference
                            if not company_data.raw_content and page_type.path == "":
                                company_data.raw_content = result.cleaned_html[:self.config.max_content_length]
                            
                            # Process extracted intelligence
                            if result.extracted_content:
                                try:
                                    # Schema extraction returns structured JSON
                                    logger.info(f"Extracted content from {page_url}: {result.extracted_content[:200]}...")
                                    
                                    # Parse the structured extraction result
                                    try:
                                        extracted_list = json.loads(result.extracted_content)
                                        
                                        # Extract the first valid result from the list
                                        if isinstance(extracted_list, list) and len(extracted_list) > 0:
                                            intelligence_data = extracted_list[0]  # Take the first extraction result
                                        elif isinstance(extracted_list, list) and len(extracted_list) == 0:
                                            # Empty list - no data extracted
                                            intelligence_data = {"raw_extracted": "no_content_extracted"}
                                        else:
                                            intelligence_data = extracted_list
                                            
                                        # Ensure intelligence_data is a dict
                                        if not isinstance(intelligence_data, dict):
                                            intelligence_data = {"raw_extracted": str(intelligence_data)}
                                            
                                    except json.JSONDecodeError:
                                        # Store as raw text if not valid JSON
                                        intelligence_data = {"raw_extracted": result.extracted_content}
                                    
                                    all_intelligence.append({
                                        'page_url': page_url,
                                        'page_path': page_type.path if page_type else '',
                                        'page_type': page_type_name,
                                        'priority': priority,
                                        'intelligence': intelligence_data
                                    })
                                    
                                    logger.info(f"Successfully extracted intelligence from {page_url}")
                                    
                                except Exception as e:
                                    logger.warning(f"Error processing extracted content from {page_url}: {e}")
                        
                        # Rate limiting between pages
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.warning(f"Failed to crawl {page_url}: {e}")
                        continue
                
                # Merge and apply all extracted intelligence
                merged_intelligence = self._merge_intelligence(all_intelligence)
                self._apply_intelligence_to_company(company_data, merged_intelligence)
                
                # Update crawling metadata
                company_data.pages_crawled = crawled_pages
                company_data.crawl_depth = len(crawled_pages)
                company_data.crawl_duration = time.time() - start_time
                company_data.scrape_status = "success"
                
                logger.info(f"Successfully AI-extracted from {len(crawled_pages)} pages for {company_data.name}")
                
        except Exception as e:
            logger.error(f"AI-powered crawl failed for {company_data.name}: {e}")
            company_data.scrape_status = "failed"
            company_data.scrape_error = str(e)
        
        return company_data
    
    def _merge_intelligence(self, all_intelligence: List[Dict]) -> Dict:
        """Intelligently merge extracted data from multiple pages with priority weighting"""
        
        if not all_intelligence:
            return {}
        
        # Initialize merged structure with best values from all pages
        merged = {
            'company_name': '',
            'industry': '',
            'business_model': '',
            'company_description': '',
            'target_market': '',
            'key_services': [],
            'location': '',
            'founding_year': '',
            'tech_stack': [],
            'leadership_team': [],
            'value_proposition': ''
        }
        
        # Collect all values for each field with priority weighting
        field_values = {key: [] for key in merged.keys()}
        
        # Sort pages by priority (higher priority first)
        sorted_pages = sorted(
            all_intelligence, 
            key=lambda x: x.get('priority', 0.0), 
            reverse=True
        )
        
        # Process each page's intelligence with priority consideration
        for page_data in sorted_pages:
            intelligence = page_data.get('intelligence', {})
            page_path = page_data.get('page_path', '')
            page_priority = page_data.get('priority', 0.0)
            
            # Ensure intelligence is a dict
            if not isinstance(intelligence, dict):
                logger.warning(f"Intelligence data is not a dict: {type(intelligence)}, skipping")
                continue
            
            # Skip if raw extracted content or no content
            if 'raw_extracted' in intelligence:
                continue
                
            # Collect values for each field with priority weighting
            for field in merged.keys():
                value = intelligence.get(field)
                if value and value != 'unknown':
                    if isinstance(value, list):
                        # Extend lists with priority weighting
                        weighted_values = [(v, page_priority) for v in value if v and v != 'unknown']
                        field_values[field].extend(weighted_values)
                    else:
                        # Add individual values with priority weighting
                        field_values[field].append((value, page_priority))
        
        # Select best values for each field using priority weighting
        for field, weighted_values in field_values.items():
            if not weighted_values:
                continue
                
            if isinstance(merged[field], list):
                # For lists, deduplicate and sort by priority, then by frequency
                all_values = [v[0] for v in weighted_values]
                value_scores = {}
                
                for value, priority in weighted_values:
                    if value not in value_scores:
                        value_scores[value] = []
                    value_scores[value].append(priority)
                
                # Score by average priority and frequency
                scored_values = [
                    (value, sum(priorities) / len(priorities) * len(priorities))
                    for value, priorities in value_scores.items()
                ]
                
                # Sort by score and take top values
                sorted_values = sorted(scored_values, key=lambda x: x[1], reverse=True)
                unique_values = [v[0] for v in sorted_values]
                merged[field] = unique_values[:10 if field == 'tech_stack' else 5]
            else:
                # For strings, prefer high priority and longer descriptions
                best_value = max(
                    weighted_values, 
                    key=lambda x: (x[1], len(str(x[0])) if x[0] else 0)
                )
                merged[field] = best_value[0]
        
        return merged
    
    def _apply_intelligence_to_company(self, company_data: CompanyData, intelligence: Dict):
        """Apply merged intelligence to company data object"""
        
        try:
            # Apply structured extraction data directly
            if intelligence.get('company_name') and intelligence['company_name'] != 'unknown':
                # Don't override the original name unless it's significantly different
                pass
            
            if intelligence.get('company_description') and intelligence['company_description'] != 'unknown':
                company_data.company_description = intelligence['company_description']
                
            if intelligence.get('industry') and intelligence['industry'] != 'unknown':
                company_data.industry = intelligence['industry']
                
            if intelligence.get('business_model') and intelligence['business_model'] != 'unknown':
                company_data.business_model = intelligence['business_model']
                
            if intelligence.get('target_market') and intelligence['target_market'] != 'unknown':
                company_data.target_market = intelligence['target_market']
                
            if intelligence.get('key_services') and intelligence['key_services']:
                # Filter out 'unknown' values
                services = [s for s in intelligence['key_services'] if s and s != 'unknown']
                if services:
                    company_data.key_services = services[:5]
                    
            if intelligence.get('location') and intelligence['location'] != 'unknown':
                company_data.location = intelligence['location']
                
            if intelligence.get('founding_year') and intelligence['founding_year'] != 'unknown':
                company_data.founding_year = intelligence['founding_year']
                
            if intelligence.get('tech_stack') and intelligence['tech_stack']:
                # Filter out 'unknown' values
                tech = [t for t in intelligence['tech_stack'] if t and t != 'unknown']
                if tech:
                    company_data.tech_stack = tech[:10]
                    
            if intelligence.get('leadership_team') and intelligence['leadership_team']:
                # Filter out 'unknown' values
                leaders = [l for l in intelligence['leadership_team'] if l and l != 'unknown']
                if leaders:
                    company_data.leadership_team = leaders[:5]
                    
            if intelligence.get('value_proposition') and intelligence['value_proposition'] != 'unknown':
                company_data.value_proposition = intelligence['value_proposition']
            
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
            logger.info(f"AI-processing company {i+1}/{len(companies)}: {company.name}")
            
            try:
                processed_company = await self.scrape_company_comprehensive(company)
                processed_companies.append(processed_company)
                
                # Rate limiting between companies
                if i < len(companies) - 1:
                    await asyncio.sleep(3)  # Longer delay for AI processing
                    
            except Exception as e:
                logger.error(f"Failed to AI-process {company.name}: {e}")
                company.scrape_status = "failed"
                company.scrape_error = str(e)
                processed_companies.append(company)
        
        return processed_companies


# Synchronous wrapper for the main pipeline
class CompanyWebScraper:
    """Wrapper to maintain compatibility with existing pipeline"""
    
    def __init__(self, config: CompanyIntelligenceConfig, bedrock_client=None):
        self.config = config
        self.crawl4ai_scraper = Crawl4AICompanyScraper(config, bedrock_client)
    
    def scrape_company(self, company_data: CompanyData) -> CompanyData:
        """Synchronous wrapper for AI-powered company scraping"""
        
        try:
            # Run the async AI scraper
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.crawl4ai_scraper.scrape_company_comprehensive(company_data)
            )
            
            loop.close()
            return result
            
        except Exception as e:
            logger.error(f"Sync wrapper error for {company_data.name}: {e}")
            company_data.scrape_status = "failed"
            company_data.scrape_error = str(e)
            return company_data
    
    def batch_scrape_companies(self, companies: List[CompanyData]) -> List[CompanyData]:
        """Synchronous wrapper for batch AI scraping"""
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.crawl4ai_scraper.batch_scrape_companies(companies)
            )
            
            loop.close()
            return result
            
        except Exception as e:
            logger.error(f"Batch AI scraping error: {e}")
            return companies
    
    def extract_similarity_metrics(self, company: CompanyData) -> CompanyData:
        """Extract similarity metrics from scraped content"""
        try:
            from src.similarity_prompts import extract_similarity_metrics
            
            # Combine relevant content for analysis
            similarity_content = self._prepare_similarity_content(company)
            
            # Extract metrics using LLM
            bedrock_client = self._get_bedrock_client()
            metrics = extract_similarity_metrics(similarity_content, bedrock_client)
            
            # Apply metrics to company object
            company = self._apply_similarity_metrics(company, metrics)
            
            logger.info(f"Extracted similarity metrics for {company.name}")
            return company
            
        except Exception as e:
            logger.error(f"Failed to extract similarity metrics for {company.name}: {e}")
            return company
    
    def _prepare_similarity_content(self, company: CompanyData) -> str:
        """Prepare content focused on similarity indicators"""
        content_parts = []
        
        # Prioritize content that indicates company stage, tech level, business model
        if company.raw_content:
            # Extract key sections
            content = company.raw_content
            
            # Look for specific similarity indicators
            indicators = [
                "about us", "our team", "careers", "jobs",
                "pricing", "customers", "case studies",
                "api", "documentation", "developers",
                "contact", "offices", "locations"
            ]
            
            # Extract relevant sections (simplified approach)
            for indicator in indicators:
                if indicator in content.lower():
                    # Find context around indicator
                    start = max(0, content.lower().find(indicator) - 200)
                    end = min(len(content), content.lower().find(indicator) + 500)
                    section = content[start:end]
                    content_parts.append(f"{indicator.title()}: {section}")
        
        return "\n\n".join(content_parts)[:5000]  # Limit to 5000 chars
    
    def _apply_similarity_metrics(self, company: CompanyData, metrics: dict) -> CompanyData:
        """Apply extracted metrics to company object"""
        
        for metric_name, metric_data in metrics.items():
            if isinstance(metric_data, dict) and 'value' in metric_data:
                # Set the metric value
                setattr(company, metric_name, metric_data['value'])
                
                # Set confidence score
                confidence_field = f"{metric_name.replace('_type', '')}_confidence"
                if hasattr(company, confidence_field):
                    setattr(company, confidence_field, metric_data.get('confidence', 0.5))
        
        return company
    
    def _get_bedrock_client(self):
        """Get Bedrock client for LLM analysis"""
        # Import here to avoid circular imports
        from src.bedrock_client import BedrockClient
        from src.models import CompanyIntelligenceConfig
        
        config = CompanyIntelligenceConfig()
        return BedrockClient(config)