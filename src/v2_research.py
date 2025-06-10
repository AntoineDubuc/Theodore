"""
Theodore V2 Research Engine
Focused research with LLM-guided page discovery and content consolidation
"""

import logging
import json
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.async_configs import CacheMode

from src.models import CompanyData
from src.progress_logger import log_processing_phase, start_company_processing, complete_company_processing

logger = logging.getLogger(__name__)

class V2ResearchEngine:
    """V2 Research Engine - Focused research with LLM-guided page discovery"""
    
    def __init__(self, ai_client):
        self.ai_client = ai_client
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session_timeout = aiohttp.ClientTimeout(total=10)
    
    async def research_company(
        self, 
        company_name: str, 
        website_url: str, 
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main V2 research method
        
        Args:
            company_name: Company name to research
            website_url: Company website URL
            job_id: Optional job ID for progress tracking
            
        Returns:
            Dict with research results
        """
        # Only create job_id if not provided (for backward compatibility)
        if not job_id:
            job_id = start_company_processing(company_name)
            self.logger.info(f"📋 Created new job_id: {job_id}")
        else:
            self.logger.info(f"📋 Using provided job_id: {job_id}")
        
        self.logger.info(f"🔬 V2 Research starting for {company_name} at {website_url}")
        
        try:
            # Phase 1: Discover key pages using LLM
            log_processing_phase(job_id, "Page Discovery", "running", 
                               target_url=website_url,
                               status_message=f"🔍 Discovering key pages from {website_url}")
            
            key_pages = await self._discover_key_pages(website_url, company_name)
            
            log_processing_phase(job_id, "Page Discovery", "completed", 
                               pages_discovered=len(key_pages),
                               status_message=f"✅ Found {len(key_pages)} key pages to analyze")
            
            # Phase 2: Crawl discovered pages
            log_processing_phase(job_id, "Content Extraction", "running", 
                               pages_to_crawl=len(key_pages),
                               status_message=f"📥 Starting to crawl {len(key_pages)} selected pages")
            
            page_contents = await self._crawl_pages(key_pages, job_id)
            
            log_processing_phase(job_id, "Content Extraction", "completed",
                               successful_extractions=len(page_contents))
            
            # Phase 3: Consolidate and analyze content
            total_chars = sum(len(p['content']) for p in page_contents)
            log_processing_phase(job_id, "Content Analysis", "running",
                               total_content_chars=total_chars,
                               status_message=f"🧠 Analyzing {total_chars:,} characters of content with AI")
            
            research_result = await self._analyze_consolidated_content(
                page_contents, company_name, website_url
            )
            
            analysis_length = len(research_result.get('analysis', ''))
            log_processing_phase(job_id, "Content Analysis", "completed",
                               analysis_length=analysis_length,
                               status_message=f"✅ Generated {analysis_length:,} character business intelligence report")
            
            # Complete job tracking with results
            complete_company_processing(job_id, True, 
                                      summary=f"V2 Research completed for {company_name}",
                                      results=research_result)
            
            self.logger.info(f"✅ V2 Research completed for {company_name}")
            return research_result
            
        except Exception as e:
            error_msg = f"V2 Research failed: {str(e)}"
            self.logger.error(f"{error_msg} for {company_name}")
            
            complete_company_processing(job_id, False, error=error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "company_name": company_name,
                "website": website_url
            }
    
    async def _discover_key_pages(self, website_url: str, company_name: str) -> List[str]:
        """
        Phase 1: Use LLM to discover key pages from main page navigation
        """
        self.logger.info(f"🔍 Discovering key pages for {website_url}")
        
        try:
            # First crawl the main page to get navigation links
            main_page_links = await self._extract_navigation_links(website_url)
            
            if not main_page_links:
                self.logger.warning(f"No navigation links found on {website_url}")
                return [website_url]  # Fallback to just main page
            
            # Use LLM to select the most important pages
            selected_pages = await self._llm_select_key_pages(
                main_page_links, company_name, website_url
            )
            
            # Always include the main page
            if website_url not in selected_pages:
                selected_pages.insert(0, website_url)
            
            self.logger.info(f"✅ Discovered {len(selected_pages)} key pages")
            return selected_pages
            
        except Exception as e:
            self.logger.error(f"❌ Page discovery failed: {e}")
            return [website_url]  # Fallback to main page only
    
    async def _extract_navigation_links(self, website_url: str) -> List[str]:
        """Extract all navigation links from main page"""
        try:
            async with AsyncWebCrawler(
                headless=True,
                browser_type="chromium",
                verbose=False
            ) as crawler:
                
                config = CrawlerRunConfig(
                    only_text=False,  # We need HTML to extract links
                    cache_mode=CacheMode.ENABLED,
                    wait_until="domcontentloaded",
                    page_timeout=15000,
                    verbose=False
                )
                
                result = await crawler.arun(url=website_url, config=config)
                
                if result.success and result.html:
                    # Parse HTML to extract all links
                    soup = BeautifulSoup(result.html, 'html.parser')
                    links = []
                    
                    # Extract all internal links
                    domain = urlparse(website_url).netloc
                    
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(website_url, href)
                        parsed_url = urlparse(full_url)
                        
                        # Only include links on same domain
                        if parsed_url.netloc == domain:
                            # Clean URL (remove fragments and query params)
                            clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                            if clean_url not in links and clean_url != website_url:
                                links.append(clean_url)
                    
                    self.logger.info(f"📋 Extracted {len(links)} navigation links")
                    return links[:50]  # Limit to prevent overwhelming LLM
                else:
                    self.logger.warning(f"Failed to extract HTML from {website_url}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Link extraction failed: {e}")
            return []
    
    async def _llm_select_key_pages(
        self, 
        all_links: List[str], 
        company_name: str, 
        website_url: str
    ) -> List[str]:
        """Use LLM to select key pages for research"""
        
        self.logger.info(f"🧠 Using LLM to select key pages from {len(all_links)} links")
        
        # Prepare links for LLM
        links_text = "\\n".join([f"- {link}" for link in all_links])
        
        prompt = f"""Analyze the navigation links from {company_name}'s website and select the MOST IMPORTANT pages for comprehensive business research.

Website: {website_url}
Company: {company_name}

Available links:
{links_text}

Select pages that would contain information about:
1. **About/Company Info** - Company background, mission, values
2. **Products/Services** - What they offer, solutions, features  
3. **Careers/Jobs** - Current openings, company culture, growth indicators
4. **Contact/Location** - How to reach them, office locations
5. **News/Press** - Recent updates, announcements, media coverage
6. **Team/Leadership** - Key people, executives, founders

IMPORTANT: Only select pages that clearly match these categories. Ignore:
- Login/account pages
- Support/help pages  
- Legal/privacy pages
- Blog archives or old content
- Product-specific documentation

Return ONLY a JSON array of the selected URLs (maximum 6 pages):
["url1", "url2", "url3", ...]

Focus on the most valuable pages for understanding the business."""

        try:
            response = await self._call_llm_async(prompt)
            
            # Parse JSON response
            try:
                json_start = response.find('[')
                json_end = response.rfind(']') + 1
                if json_start >= 0 and json_end > json_start:
                    json_text = response[json_start:json_end]
                    selected_urls = json.loads(json_text)
                    
                    if isinstance(selected_urls, list):
                        # Validate URLs are in original list
                        valid_urls = [url for url in selected_urls if url in all_links]
                        self.logger.info(f"✅ LLM selected {len(valid_urls)} key pages")
                        return valid_urls[:6]  # Limit to 6 pages max
                    
            except json.JSONDecodeError:
                self.logger.warning("Failed to parse LLM JSON response")
                
            # Fallback: heuristic selection
            return self._heuristic_page_selection(all_links)
            
        except Exception as e:
            self.logger.error(f"LLM page selection failed: {e}")
            return self._heuristic_page_selection(all_links)
    
    def _heuristic_page_selection(self, all_links: List[str]) -> List[str]:
        """Fallback heuristic page selection"""
        priority_keywords = [
            'about', 'company', 'careers', 'jobs', 'team', 'leadership',
            'products', 'services', 'solutions', 'contact', 'news', 'press'
        ]
        
        scored_links = []
        for link in all_links:
            score = 0
            link_lower = link.lower()
            
            for keyword in priority_keywords:
                if keyword in link_lower:
                    score += 1
            
            if score > 0:
                scored_links.append((link, score))
        
        # Sort by score and return top 6
        scored_links.sort(key=lambda x: x[1], reverse=True)
        return [link for link, score in scored_links[:6]]
    
    async def _crawl_pages(self, page_urls: List[str], job_id: str) -> List[Dict[str, str]]:
        """
        Phase 2: Crawl selected pages and extract clean text content
        """
        self.logger.info(f"📥 Crawling {len(page_urls)} selected pages")
        
        page_contents = []
        
        for i, url in enumerate(page_urls, 1):
            try:
                # Log detailed progress for frontend
                log_processing_phase(job_id, "Content Extraction", "running", 
                                   current_url=url, 
                                   progress_step=f"{i}/{len(page_urls)}",
                                   status_message=f"Crawling: {url}")
                
                print(f"🔍 [{i}/{len(page_urls)}] Crawling: {url}")
                
                async with AsyncWebCrawler(
                    headless=True,
                    browser_type="chromium",
                    verbose=False
                ) as crawler:
                    
                    config = CrawlerRunConfig(
                        only_text=True,  # Extract clean text only
                        remove_forms=True,
                        word_count_threshold=50,
                        excluded_tags=['nav', 'footer', 'aside', 'script', 'style'],
                        css_selector='main, article, .content, .main-content, body',
                        cache_mode=CacheMode.ENABLED,
                        wait_until="domcontentloaded",
                        page_timeout=15000,
                        verbose=False
                    )
                    
                    result = await crawler.arun(url=url, config=config)
                    
                    if result.success and result.cleaned_html:
                        content = result.cleaned_html[:8000]  # Limit content length
                        
                        page_contents.append({
                            'url': url,
                            'content': content,
                            'page_type': self._classify_page_type(url)
                        })
                        
                        # Log successful extraction
                        log_processing_phase(job_id, "Content Extraction", "running", 
                                           current_url=url, 
                                           progress_step=f"{i}/{len(page_urls)}",
                                           status_message=f"✅ Extracted {len(content):,} chars from {self._get_page_name(url)}")
                        
                        print(f"✅ [{i}/{len(page_urls)}] Success: {len(content)} chars from {url}")
                    else:
                        print(f"❌ [{i}/{len(page_urls)}] Failed: {url}")
                        
            except Exception as e:
                print(f"❌ [{i}/{len(page_urls)}] Error: {url} - {str(e)}")
                self.logger.warning(f"Failed to crawl {url}: {e}")
        
        self.logger.info(f"✅ Successfully crawled {len(page_contents)} pages")
        return page_contents
    
    def _classify_page_type(self, url: str) -> str:
        """Classify page type based on URL for better consolidation"""
        url_lower = url.lower()
        
        if any(keyword in url_lower for keyword in ['about', 'company']):
            return 'about'
        elif any(keyword in url_lower for keyword in ['career', 'job']):
            return 'careers'
        elif any(keyword in url_lower for keyword in ['product', 'service', 'solution']):
            return 'products'
        elif any(keyword in url_lower for keyword in ['contact', 'location']):
            return 'contact'
        elif any(keyword in url_lower for keyword in ['news', 'press', 'media']):
            return 'news'
        elif any(keyword in url_lower for keyword in ['team', 'leadership', 'management']):
            return 'team'
        else:
            return 'main'
    
    def _get_page_name(self, url: str) -> str:
        """Get a friendly page name for progress display"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            path = parsed.path.strip('/')
            
            if not path:
                return "Home page"
            
            # Get the last part of the path and make it readable
            parts = path.split('/')
            last_part = parts[-1] if parts else ''
            
            # Convert common patterns to friendly names
            friendly_names = {
                'about': 'About page',
                'careers': 'Careers page', 
                'jobs': 'Jobs page',
                'team': 'Team page',
                'contact': 'Contact page',
                'products': 'Products page',
                'services': 'Services page',
                'news': 'News page',
                'press': 'Press page',
                'blog': 'Blog page'
            }
            
            return friendly_names.get(last_part.lower(), f"{last_part.title()} page")
            
        except Exception:
            return "page"
    
    async def _analyze_consolidated_content(
        self, 
        page_contents: List[Dict[str, str]], 
        company_name: str,
        website_url: str
    ) -> Dict[str, Any]:
        """
        Phase 3: Consolidate all page content and analyze with LLM
        """
        if not page_contents:
            return {
                "success": False,
                "error": "No content extracted",
                "company_name": company_name,
                "website": website_url
            }
        
        # Consolidate content by page type
        consolidated_text = self._consolidate_page_contents(page_contents)
        
        # Generate comprehensive structured analysis
        structured_analysis = await self._llm_analyze_company_content(
            consolidated_text, company_name, website_url
        )
        
        # Build comprehensive result with both structured data and research metadata
        result = {
            "success": True,
            "company_name": company_name,
            "website": website_url,
            "pages_analyzed": len(page_contents),
            "total_content_length": len(consolidated_text),
            "page_breakdown": [
                {
                    "url": page['url'],
                    "type": page['page_type'],
                    "content_length": len(page['content'])
                }
                for page in page_contents
            ]
        }
        
        # Merge structured analysis data
        if isinstance(structured_analysis, dict):
            result.update(structured_analysis)
        else:
            result["analysis"] = structured_analysis
            
        return result
    
    def _consolidate_page_contents(self, page_contents: List[Dict[str, str]]) -> str:
        """Consolidate page contents into readable text format"""
        
        # Group content by page type
        content_by_type = {}
        for page in page_contents:
            page_type = page['page_type']
            if page_type not in content_by_type:
                content_by_type[page_type] = []
            content_by_type[page_type].append(page['content'])
        
        # Build consolidated text in logical order
        sections = []
        
        # Main/About section first
        for page_type in ['main', 'about']:
            if page_type in content_by_type:
                section_content = "\\n\\n".join(content_by_type[page_type])
                sections.append(f"=== COMPANY OVERVIEW ===\\n{section_content}")
        
        # Products/Services
        if 'products' in content_by_type:
            section_content = "\\n\\n".join(content_by_type['products'])
            sections.append(f"=== PRODUCTS & SERVICES ===\\n{section_content}")
        
        # Team/Leadership
        if 'team' in content_by_type:
            section_content = "\\n\\n".join(content_by_type['team'])
            sections.append(f"=== TEAM & LEADERSHIP ===\\n{section_content}")
        
        # Careers
        if 'careers' in content_by_type:
            section_content = "\\n\\n".join(content_by_type['careers'])
            sections.append(f"=== CAREERS & CULTURE ===\\n{section_content}")
        
        # News/Press
        if 'news' in content_by_type:
            section_content = "\\n\\n".join(content_by_type['news'])
            sections.append(f"=== NEWS & UPDATES ===\\n{section_content}")
        
        # Contact
        if 'contact' in content_by_type:
            section_content = "\\n\\n".join(content_by_type['contact'])
            sections.append(f"=== CONTACT & LOCATION ===\\n{section_content}")
        
        return "\\n\\n".join(sections)
    
    async def _llm_analyze_company_content(
        self, 
        consolidated_content: str, 
        company_name: str,
        website_url: str
    ) -> Dict[str, Any]:
        """Use LLM to analyze consolidated content and extract structured business intelligence"""
        
        # Enhanced prompt for complete CompanyData model extraction
        prompt = f"""Analyze the following comprehensive content from {company_name}'s website and extract ALL possible business intelligence data.

Company: {company_name}
Website: {website_url}

Website Content:
{consolidated_content}

Extract the following information and return it as a complete JSON object. For missing information, use null for strings/numbers, [] for arrays, and {{}} for objects. Be thorough and extract as much as possible:

{{
  "company_name": "{company_name}",
  "website": "{website_url}",
  "company_description": "Brief description of what the company does",
  "industry": "Primary industry/sector (e.g., 'Food & Beverage', 'Technology', 'Healthcare')",
  "business_model": "B2B, B2C, marketplace, SaaS, franchise, etc.",
  "company_size": "startup, SMB, enterprise",
  "value_proposition": "Main value proposition or unique selling point",
  "target_market": "Who they serve (e.g., 'families', 'small businesses', 'enterprises')",
  "key_services": ["main service 1", "main service 2", "main service 3"],
  "competitive_advantages": ["advantage 1", "advantage 2"],
  "pain_points": ["pain point 1", "pain point 2"],
  "tech_stack": ["technology 1", "technology 2"],
  "location": "Company headquarters location (city, state/country)",
  "founding_year": year_as_number_or_null,
  "employee_count_range": "1-10, 11-50, 51-200, 201-1000, 1000+",
  "company_culture": "Description of company culture, values, and work environment",
  "funding_status": "bootstrap, seed, series_a, series_b, public, acquired, etc.",
  "leadership_team": ["CEO Name", "Founder Name", "CTO Name"],
  "recent_news": ["recent announcement 1", "recent update 2"],
  "contact_info": {{
    "email": "contact email address",
    "phone": "phone number", 
    "address": "physical address"
  }},
  "social_media": {{
    "linkedin": "linkedin company url",
    "twitter": "twitter url",
    "facebook": "facebook url",
    "instagram": "instagram url"
  }},
  "certifications": ["certification 1", "certification 2"],
  "partnerships": ["partner company 1", "partner company 2"],
  "awards": ["award 1", "award 2"],
  "company_stage": "startup, growth, mature, established",
  "tech_sophistication": "low, medium, high",
  "geographic_scope": "local, regional, national, global",
  "business_model_type": "saas, services, marketplace, ecommerce, manufacturing, restaurant, other",
  "decision_maker_type": "technical, business, hybrid",
  "sales_complexity": "simple, moderate, complex",
  "has_chat_widget": true_or_false,
  "has_forms": true_or_false,
  "ai_summary": "Comprehensive 2-3 paragraph business intelligence summary covering what the company does, who they serve, their market position, and key insights for business development"
}}

IMPORTANT: 
- Extract factual information only from the provided content
- Use null for missing string/number fields
- Use [] for missing array fields  
- Use {{}} for missing object fields
- Be specific and detailed where information is available
- The ai_summary should be comprehensive and business-focused
- Return ONLY the JSON object, no other text"""

        try:
            response = await self._call_llm_async(prompt)
            
            # Parse JSON response
            try:
                # Extract JSON from response
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_text = response[json_start:json_end]
                    structured_data = json.loads(json_text)
                    
                    # Add the original analysis as a fallback
                    if not structured_data.get('ai_summary'):
                        structured_data['ai_summary'] = f"Structured analysis completed for {company_name}"
                    
                    return structured_data
                else:
                    # Fallback to text analysis
                    return {"ai_summary": response.strip()}
                    
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse JSON from LLM response: {e}")
                return {"ai_summary": response.strip()}
                
        except Exception as e:
            self.logger.error(f"LLM content analysis failed: {e}")
            return {
                "ai_summary": f"Analysis failed for {company_name}. Content available but AI analysis encountered an error: {str(e)}"
            }
    
    async def _call_llm_async(self, prompt: str) -> str:
        """Call LLM asynchronously"""
        try:
            # Run LLM call in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                self.ai_client.analyze_content, 
                prompt
            )
            return response
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            raise


class V2ResearchEngineSync:
    """Synchronous wrapper for V2 Research Engine"""
    
    def __init__(self, ai_client):
        self.engine = V2ResearchEngine(ai_client)
    
    def research_company(
        self, 
        company_name: str, 
        website_url: str, 
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synchronous wrapper for company research"""
        return asyncio.run(
            self.engine.research_company(company_name, website_url, job_id)
        )