"""
Real Job Listings Crawler for Theodore
Implements your exact instructions:
1. Crawl main page, give all links to LLM asking it to select career page
2. Crawl that career page and if no obvious listings, ask LLM to find job listing link
3. If no listing can be found, Google it
"""

import logging
import json
import re
import os
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class JobListingsCrawler:
    """Job listings crawler following exact user instructions"""
    
    def __init__(self, bedrock_client=None, openai_client=None):
        self.bedrock_client = bedrock_client
        self.openai_client = openai_client
        
        # Use OpenAI as primary if available, Bedrock as fallback
        if openai_client:
            self.llm_client = openai_client
            logger.info("🧠 Using OpenAI for LLM analysis")
        elif bedrock_client:
            self.llm_client = bedrock_client
            logger.info("🧠 Using Bedrock for LLM analysis")
        else:
            raise ValueError("Either OpenAI or Bedrock client must be provided")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def crawl_job_listings(self, company_name: str, website: str) -> Dict[str, Any]:
        """
        Main method following your exact instructions:
        1. Crawl main page, get all links
        2. Give links to LLM to select most likely career page
        3. Crawl career page for job listings  
        4. If no listings, ask LLM to find job listing link
        5. If still no listings, Google it
        """
        logger.info(f"🚀 Starting job listings crawl for {company_name} at {website}")
        
        try:
            # STEP 1: Crawl main page and get all links
            logger.info(f"📄 STEP 1: Crawling main page {website}")
            main_links = self._crawl_main_page_links(website)
            
            if not main_links:
                logger.warning(f"⚠️ STEP 1 FAILED: No links found on main page")
                logger.info(f"🌐 FALLBACK TO STEP 6: Using Google search since main page crawling failed")
                google_result = self._google_search_fallback(company_name)
                logger.info(f"✅ STEP 6 COMPLETE: Google search fallback completed")
                return {
                    **google_result,
                    'source': 'google_search_crawl_failed',
                    'career_page_found': False,
                    'steps_completed': 6,
                    'reason': 'Could not extract links from main page'
                }
            
            logger.info(f"✅ STEP 1 SUCCESS: Found {len(main_links)} links on main page")
            logger.debug(f"🔍 Sample links: {main_links[:5]}")
            
            # Check if any links obviously contain career keywords first
            obvious_career_links = []
            career_keywords = ['career', 'job', 'work', 'hiring', 'join', 'team', 'employment', 'openings', 'opportunities']
            for link in main_links:
                if any(keyword in link.lower() for keyword in career_keywords):
                    obvious_career_links.append(link)
            
            if not obvious_career_links:
                logger.warning(f"⚠️ No obvious career links found in {len(main_links)} main page links")
                logger.info(f"🌐 SKIP TO STEP 6: Using Google search since no career links found on homepage")
                google_result = self._google_search_fallback(company_name)
                logger.info(f"✅ STEP 6 COMPLETE: Google search fallback completed")
                return {
                    **google_result,
                    'source': 'google_search_direct',
                    'career_page_found': False,
                    'steps_completed': 6,
                    'reason': 'No career links found on homepage'
                }
            
            # STEP 2: Give all links to LLM asking it to select the one most likely to lead to career page
            logger.info(f"🧠 STEP 2: Found {len(obvious_career_links)} potential career links, asking LLM to select best one")
            career_link = self._ask_llm_for_career_page(main_links, company_name, website)
            
            if not career_link:
                logger.error(f"❌ STEP 2 FAILED: LLM could not identify career page link")
                logger.info(f"🌐 FALLBACK TO STEP 6: Using Google search")
                google_result = self._google_search_fallback(company_name)
                return {
                    **google_result,
                    'source': 'google_search_llm_fallback',
                    'career_page_found': False,
                    'steps_completed': 6,
                    'reason': 'LLM could not identify career page link'
                }
            
            logger.info(f"✅ STEP 2 SUCCESS: LLM selected career page: {career_link}")
            
            # STEP 3: Crawl that career page
            logger.info(f"📄 STEP 3: Crawling career page {career_link}")
            career_content, career_links = self._crawl_career_page(career_link)
            
            if not career_content:
                logger.warning(f"⚠️ STEP 3 FAILED: Could not crawl career page")
                logger.info(f"🌐 FALLBACK TO STEP 6: Using Google search since career page inaccessible")
                google_result = self._google_search_fallback(company_name)
                logger.info(f"✅ STEP 6 COMPLETE: Google search fallback completed")
                return {
                    **google_result,
                    'source': 'google_search_career_failed',
                    'career_page_found': True,
                    'career_page_url': career_link,
                    'steps_completed': 6,
                    'reason': 'Could not access career page'
                }
            
            logger.info(f"✅ STEP 3 SUCCESS: Crawled career page, got {len(career_content)} chars content, {len(career_links)} links")
            
            # STEP 4: Check for obvious job listings on career page
            logger.info(f"🔍 STEP 4: Checking career page for obvious job listings")
            job_listings = self._check_for_job_listings(career_content, company_name)
            
            if job_listings['found_jobs']:
                logger.info(f"✅ STEP 4 SUCCESS: Found job listings on career page!")
                return job_listings
            
            logger.info(f"⚠️ STEP 4: No obvious job listings found on career page")
            
            # STEP 5: Ask LLM to find link most likely to lead to list of jobs
            if career_links:
                logger.info(f"🧠 STEP 5: Asking LLM to find job listing link from {len(career_links)} career page links")
                job_link = self._ask_llm_for_job_listing_link(career_links, company_name, career_link)
                
                if job_link:
                    logger.info(f"✅ STEP 5 SUCCESS: LLM found job listing link: {job_link}")
                    
                    # Crawl the job listing page
                    logger.info(f"📄 STEP 5b: Crawling job listing page {job_link}")
                    job_content, _ = self._crawl_career_page(job_link)
                    
                    if job_content:
                        job_listings = self._check_for_job_listings(job_content, company_name)
                        if job_listings['found_jobs']:
                            logger.info(f"✅ STEP 5b SUCCESS: Found job listings on job listing page!")
                            return job_listings
                        else:
                            logger.info(f"⚠️ STEP 5b: No job listings found on job listing page")
                    else:
                        logger.error(f"❌ STEP 5b FAILED: Could not crawl job listing page")
                else:
                    logger.info(f"⚠️ STEP 5: LLM could not find job listing link")
            else:
                logger.info(f"⚠️ STEP 5 SKIPPED: No links found on career page")
            
            # STEP 6: Google it
            logger.info(f"🌐 STEP 6: Falling back to Google search")
            google_result = self._google_search_fallback(company_name)
            
            logger.info(f"✅ STEP 6 COMPLETE: Google search fallback completed")
            
            return {
                **google_result,
                'source': 'google_search',
                'career_page_found': True,
                'career_page_url': career_link,
                'steps_completed': 6
            }
            
        except Exception as e:
            logger.error(f"💥 CRITICAL ERROR in job listings crawl for {company_name}: {e}")
            logger.info(f"🌐 EMERGENCY FALLBACK TO STEP 6: Using Google search due to critical error")
            try:
                google_result = self._google_search_fallback(company_name)
                logger.info(f"✅ STEP 6 COMPLETE: Emergency Google search fallback completed")
                return {
                    **google_result,
                    'source': 'google_search_emergency',
                    'career_page_found': False,
                    'steps_completed': 6,
                    'reason': f'Critical crawling error: {str(e)}'
                }
            except Exception as fallback_error:
                logger.error(f"💥 Even Google fallback failed: {fallback_error}")
                return self._create_error_result(f"Critical crawling error: {str(e)}")
        
    
    def _crawl_main_page_links(self, url: str) -> List[str]:
        """Crawl main page and extract all links"""
        logger.info(f"🌐 Requesting main page: {url}")
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            logger.info(f"✅ Main page response: {response.status_code}, {len(response.content)} bytes")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            logger.info(f"🔍 Parsing HTML with BeautifulSoup")
            
            links = []
            base_domain = urlparse(url).netloc
            logger.info(f"🏠 Base domain: {base_domain}")
            
            # Find all links
            all_links = soup.find_all('a', href=True)
            logger.info(f"🔗 Found {len(all_links)} total anchor tags")
            
            for i, link in enumerate(all_links):
                href = link['href']
                link_text = link.get_text(strip=True)
                
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    full_url = urljoin(url, href)
                elif href.startswith('http'):
                    full_url = href
                else:
                    full_url = urljoin(url, href)
                
                # Only include links from the same domain
                if urlparse(full_url).netloc == base_domain:
                    links.append(full_url)
                    logger.debug(f"  Link {i+1}: {full_url} (text: '{link_text[:30]}...')")
            
            # Remove duplicates
            unique_links = list(set(links))
            logger.info(f"📋 Extracted {len(unique_links)} unique same-domain links")
            
            return unique_links[:50]  # Limit for LLM processing
            
        except Exception as e:
            logger.error(f"💥 Failed to crawl main page {url}: {e}")
            return []
    
    def _ask_llm_for_career_page(self, links: List[str], company_name: str, website: str) -> Optional[str]:
        """Give all links to LLM asking it to select the one most likely to lead to career page"""
        logger.info(f"🧠 Preparing LLM prompt with {len(links)} links for {company_name}")
        
        try:
            # Prepare links for LLM
            links_text = "\n".join([f"{i+1}. {link}" for i, link in enumerate(links)])
            logger.debug(f"📝 Links text length: {len(links_text)} characters")
            
            prompt = f"""I need you to analyze these links from {company_name}'s website ({website}) and select the ONE link most likely to lead to a careers/jobs page.

Here are all the links I found:
{links_text}

Instructions:
- Look for URLs containing words like: careers, jobs, work, employment, join, team, hiring, opportunities
- Choose the MOST LIKELY link that would lead to their careers/jobs page
- Return ONLY the complete URL, nothing else
- If no career-related link exists, return exactly: NONE

Most likely career page URL:"""

            logger.info(f"🚀 Sending prompt to LLM ({len(prompt)} chars)")
            response = self.llm_client.analyze_content(prompt)
            logger.info(f"📥 LLM response: '{response[:100]}...'")
            
            if response and response.strip() != "NONE":
                career_url = response.strip()
                
                # Validate the URL is in our list
                if career_url in links:
                    logger.info(f"✅ LLM selected valid career URL: {career_url}")
                    return career_url
                else:
                    logger.warning(f"⚠️ LLM returned URL not in original list: {career_url}")
                    # Try to find a partial match
                    for link in links:
                        if career_url in link or link in career_url:
                            logger.info(f"✅ Found partial match: {link}")
                            return link
                    
                    logger.error(f"❌ LLM returned invalid URL")
                    return None
            else:
                logger.info(f"ℹ️ LLM returned NONE - no career page found")
                return None
                
        except Exception as e:
            logger.error(f"💥 LLM career page selection failed: {e}")
            return None
    
    def _crawl_career_page(self, url: str) -> Tuple[Optional[str], List[str]]:
        """Crawl career page and return content + links"""
        logger.info(f"🌐 Requesting career page: {url}")
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            logger.info(f"✅ Career page response: {response.status_code}, {len(response.content)} bytes")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract text content
            content = soup.get_text(separator=' ', strip=True)
            logger.info(f"📄 Extracted {len(content)} characters of text content")
            
            # Extract links from career page
            links = []
            base_domain = urlparse(url).netloc
            
            all_links = soup.find_all('a', href=True)
            logger.info(f"🔗 Found {len(all_links)} links on career page")
            
            for link in all_links:
                href = link['href']
                if href.startswith('/'):
                    full_url = urljoin(url, href)
                elif href.startswith('http'):
                    full_url = href
                else:
                    full_url = urljoin(url, href)
                
                if urlparse(full_url).netloc == base_domain:
                    links.append(full_url)
            
            unique_links = list(set(links))
            logger.info(f"📋 Extracted {len(unique_links)} unique links from career page")
            
            return content, unique_links
            
        except Exception as e:
            logger.error(f"💥 Failed to crawl career page {url}: {e}")
            return None, []
    
    def _check_for_job_listings(self, content: str, company_name: str) -> Dict[str, Any]:
        """Check career page content for obvious job listings using LLM"""
        logger.info(f"🔍 Analyzing {len(content)} chars of content for job listings")
        
        try:
            # Limit content for LLM processing
            content_sample = content[:6000] if len(content) > 6000 else content
            logger.info(f"📝 Using {len(content_sample)} chars for LLM analysis")
            
            prompt = f"""Analyze this content from {company_name}'s career page and tell me if there are obvious job listings.

Content:
{content_sample}

Look for:
- Specific job titles/positions listed
- "Apply now" buttons or links
- Job departments or categories
- Any indication of current openings

Respond in JSON format:
{{
    "found_jobs": true/false,
    "job_count": <number>,
    "positions": ["Job Title 1", "Job Title 2"],
    "evidence": ["text that shows jobs", "apply button found"],
    "reason": "explanation of what you found"
}}

Response:"""

            logger.info(f"🚀 Sending job listing analysis to LLM")
            response = self.llm_client.analyze_content(prompt)
            logger.info(f"📥 LLM job analysis response: '{response[:200]}...'")
            
            if response:
                try:
                    # Extract JSON
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_text = response[json_start:json_end]
                        data = json.loads(json_text)
                        logger.info(f"✅ Parsed LLM response: {data}")
                        
                        if data.get('found_jobs'):
                            job_count = data.get('job_count', len(data.get('positions', [])))
                            logger.info(f"🎉 FOUND JOBS! Count: {job_count}")
                            return {
                                'job_listings': f"Yes - {job_count} open positions",
                                'details': {
                                    'positions': data.get('positions', [])[:10],
                                    'evidence': data.get('evidence', []),
                                    'source_analysis': data.get('reason', '')
                                },
                                'found_jobs': True,
                                'source': 'career_page_content'
                            }
                        else:
                            logger.info(f"❌ No jobs found. Reason: {data.get('reason', 'Unknown')}")
                            return {
                                'job_listings': 'No current job listings found on career page',
                                'details': {'reason': data.get('reason', 'No specific jobs listed')},
                                'found_jobs': False,
                                'source': 'career_page_content'
                            }
                            
                except json.JSONDecodeError as je:
                    logger.error(f"💥 Failed to parse LLM JSON: {je}")
                    logger.error(f"Raw response: {response}")
            
            logger.warning(f"⚠️ Could not analyze job listings from content")
            return {
                'job_listings': 'Could not analyze career page content',
                'details': {},
                'found_jobs': False,
                'source': 'analysis_failed'
            }
            
        except Exception as e:
            logger.error(f"💥 Job listing analysis failed: {e}")
            return {
                'job_listings': f'Analysis error: {str(e)}',
                'details': {},
                'found_jobs': False,
                'source': 'error'
            }
    
    def _ask_llm_for_job_listing_link(self, links: List[str], company_name: str, career_page_url: str) -> Optional[str]:
        """Ask LLM to find the link most likely to lead to list of jobs"""
        logger.info(f"🧠 Asking LLM to find job listing link from {len(links)} career page links")
        
        try:
            links_text = "\n".join([f"{i+1}. {link}" for i, link in enumerate(links[:30])])
            
            prompt = f"""I'm on {company_name}'s career page ({career_page_url}) but I don't see obvious job listings. 

Look at these links from the career page and find the one most likely to lead to actual job listings:
{links_text}

Look for:
- "View all jobs", "Open positions", "Current openings"
- Links with "openings", "positions", "apply", "jobs"
- Department-specific job pages

Return ONLY the complete URL most likely to show job listings, or "NONE" if no good link found.

Job listings URL:"""

            logger.info(f"🚀 Sending job link prompt to LLM")
            response = self.llm_client.analyze_content(prompt)
            logger.info(f"📥 LLM job link response: '{response[:100]}...'")
            
            if response and response.strip() != "NONE":
                job_url = response.strip()
                if job_url in links:
                    logger.info(f"✅ LLM found valid job listing URL: {job_url}")
                    return job_url
                else:
                    # Try partial match
                    for link in links:
                        if job_url in link or link in job_url:
                            logger.info(f"✅ Found partial match for job URL: {link}")
                            return link
                    logger.warning(f"⚠️ LLM returned invalid job URL: {job_url}")
                    return None
            else:
                logger.info(f"ℹ️ LLM found no job listing links")
                return None
                
        except Exception as e:
            logger.error(f"💥 LLM job link selection failed: {e}")
            return None
    
    def _google_search_fallback(self, company_name: str) -> Dict[str, Any]:
        """Try common career URL patterns, then fallback to LLM knowledge"""
        logger.info(f"🌐 Running enhanced search fallback for {company_name}")
        
        # First, try to find career pages using common URL patterns
        career_url = self._try_common_career_urls(company_name)
        if career_url:
            logger.info(f"✅ Found career page using URL patterns: {career_url}")
            # Try to crawl this career page
            try:
                career_content, career_links = self._crawl_career_page(career_url)
                if career_content:
                    # Check for job listings on this discovered page
                    job_listings = self._check_for_job_listings(career_content, company_name)
                    if job_listings['found_jobs']:
                        logger.info(f"🎉 SUCCESS: Found job listings on discovered career page!")
                        return {
                            **job_listings,
                            'source': 'discovered_career_page',
                            'career_page_found': True,
                            'career_page_url': career_url,
                            'steps_completed': 6
                        }
                    else:
                        logger.info(f"📄 Found career page but no active job listings")
                        # Still provide the career page as useful info
                        return {
                            'job_listings': f"Found career page but no current openings | Direct link: {career_url}",
                            'details': {
                                'career_page_url': career_url,
                                'best_job_sites': ['LinkedIn', 'company careers page', 'Indeed'],
                                'search_tips': f"Check {career_url} regularly for new postings",
                                'hiring_status': 'No current openings',
                                'company_info': f'Career page found at {career_url}'
                            },
                            'source': 'discovered_career_page_no_jobs',
                            'career_page_found': True,
                            'career_page_url': career_url,
                            'steps_completed': 6
                        }
            except Exception as e:
                logger.warning(f"⚠️ Found career URL {career_url} but couldn't crawl it: {e}")
        
        # If no career page found via URL patterns, ACTUALLY GOOGLE IT FOR REAL
        logger.info(f"🔍 REAL GOOGLE SEARCH for {company_name} careers")
        google_results = self._perform_real_google_search(company_name)
        if google_results:
            return google_results
        
        # Final fallback to LLM knowledge if Google search fails
        logger.info(f"🤖 Final LLM knowledge fallback for {company_name}")
        try:
            return {
                'job_listings': 'Could not determine hiring status',
                'details': {'note': 'Google search analysis failed'}
            }
            
        except Exception as e:
            logger.error(f"💥 Google search fallback error: {e}")
            return {
                'job_listings': f'Search fallback failed: {str(e)}',
                'details': {}
            }
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error result"""
        logger.error(f"💥 Creating error result: {error_message}")
        return {
            'job_listings': f'Error: {error_message}',
            'details': {'error': error_message},
            'found_jobs': False,
            'source': 'error'
        }
    
    def _try_common_career_urls(self, company_name: str) -> Optional[str]:
        """Try common career URL patterns to discover career pages"""
        logger.info(f"🔍 Trying common career URL patterns for {company_name}")
        
        # Add timeout for entire career URL discovery (max 30 seconds)
        import time
        start_time = time.time()
        max_duration = 30  # seconds
        
        # Get base domain from company name (simple heuristic)
        base_domains = self._generate_possible_domains(company_name)
        
        # Limit to first 5 most likely domains to prevent excessive requests
        base_domains = base_domains[:5]
        logger.info(f"🔍 Testing {len(base_domains)} domain variations (limited for performance)")
        
        # Common career URL patterns
        career_patterns = [
            "/careers",
            "/about/careers", 
            "/careers/jobs",
            "/jobs",
            "/work-with-us",
            "/join-us",
            "/career",
            "/employment",
            "/opportunities",
            "/company/careers"
        ]
        
        # Try each domain + pattern combination
        for domain in base_domains:
            # Check timeout for entire process
            if time.time() - start_time > max_duration:
                logger.warning(f"⏰ Career URL discovery timeout ({max_duration}s) reached for {company_name}")
                break
                
            for pattern in career_patterns:
                career_url = f"{domain}{pattern}"
                logger.debug(f"🌐 Trying: {career_url}")
                
                try:
                    # Reduced timeout per request to 5 seconds
                    response = self.session.head(career_url, timeout=5, allow_redirects=True)
                    if response.status_code == 200:
                        logger.info(f"✅ Found accessible career page: {career_url}")
                        return career_url
                    elif response.status_code in [301, 302, 303, 307, 308]:
                        # Follow redirect
                        final_url = response.url
                        logger.info(f"✅ Found redirected career page: {career_url} → {final_url}")
                        return final_url
                except Exception as e:
                    logger.debug(f"❌ {career_url} failed: {e}")
                    continue
                    
                # Check timeout again within inner loop
                if time.time() - start_time > max_duration:
                    logger.warning(f"⏰ Career URL discovery timeout ({max_duration}s) reached during pattern testing")
                    break
        
        logger.info(f"❌ No common career URLs found for {company_name}")
        return None
    
    def _generate_possible_domains(self, company_name: str) -> List[str]:
        """Generate possible domain names for a company using Google Search"""
        logger.info(f"🔍 Using Google Search to discover official domain for {company_name}")
        
        # Try Google Search first to find the official website
        google_domains = self._google_search_for_domain(company_name)
        if google_domains:
            logger.info(f"✅ Google Search found {len(google_domains)} domains for {company_name}")
            return google_domains
        
        # Fallback to heuristic domain generation if Google Search fails
        logger.warning(f"⚠️ Google Search failed, falling back to heuristic domain generation for {company_name}")
        return self._generate_heuristic_domains(company_name)
    
    def _google_search_for_domain(self, company_name: str) -> List[str]:
        """Use Google Search to find the official company domain"""
        try:
            # Search for the company's official website
            search_query = f"{company_name} official website"
            search_results = self._google_search_api(search_query)
            
            if not search_results:
                logger.warning(f"⚠️ Google Search returned no results for '{search_query}'")
                return []
            
            # Extract domains from search results
            domains = []
            for url in search_results:
                try:
                    parsed = urlparse(url)
                    if parsed.scheme and parsed.netloc:
                        # Get the base domain
                        base_domain = f"{parsed.scheme}://{parsed.netloc}"
                        if base_domain not in domains:
                            domains.append(base_domain)
                            logger.info(f"🎯 Found domain from Google Search: {base_domain}")
                except Exception as e:
                    logger.debug(f"❌ Failed to parse URL {url}: {e}")
                    continue
            
            return domains[:3]  # Limit to top 3 most relevant domains
            
        except Exception as e:
            logger.error(f"💥 Google Search for domain failed: {e}")
            return []
    
    def _generate_heuristic_domains(self, company_name: str) -> List[str]:
        """Fallback: Generate domain names using heuristics (no hardcoding)"""
        domains = []
        
        # Common domain patterns for unknown companies
        name_clean = company_name.lower().replace(" ", "").replace(",", "").replace(".", "").replace("-", "")
        name_hyphen = company_name.lower().replace(" ", "-").replace(",", "").replace(".", "")
        
        # Try different TLDs and variations
        base_patterns = [
            name_clean,
            name_hyphen,
            f"{name_clean}corp",
            f"{name_clean}inc"
        ]
        
        tlds = [".com", ".ca", ".net", ".org"]
        
        for pattern in base_patterns:
            for tld in tlds:
                domains.append(f"https://www.{pattern}{tld}")
                domains.append(f"https://{pattern}{tld}")
        
        
        return domains
    
    def _perform_real_google_search(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Perform ACTUAL Google search for company careers"""
        logger.info(f"🌐 REAL Google search: '{company_name} careers' OR '{company_name} jobs'")
        
        search_queries = [
            f"{company_name} careers",
            f"{company_name} jobs", 
            f"{company_name} hiring",
            f"site:{company_name.lower()}.com careers"
        ]
        
        for query in search_queries:
            try:
                career_urls = self._google_search_api(query)
                if career_urls:
                    # Try to crawl each discovered URL
                    for url in career_urls[:3]:  # Try top 3 results
                        logger.info(f"🔍 Testing Google result: {url}")
                        try:
                            # Check if this looks like a career page
                            if self._is_likely_career_url(url):
                                # Try to crawl it
                                career_content, career_links = self._crawl_career_page(url)
                                if career_content:
                                    # Check for job listings
                                    job_listings = self._check_for_job_listings(career_content, company_name)
                                    if job_listings['found_jobs']:
                                        logger.info(f"🎉 GOOGLE SUCCESS: Found job listings at {url}")
                                        return {
                                            **job_listings,
                                            'source': 'google_search_success',
                                            'career_page_found': True,
                                            'career_page_url': url,
                                            'steps_completed': 6,
                                            'search_query': query
                                        }
                                    else:
                                        # Career page but no jobs
                                        logger.info(f"📄 GOOGLE: Found career page but no current jobs at {url}")
                                        return {
                                            'job_listings': f"Found career page via Google but no current openings | Direct link: {url}",
                                            'details': {
                                                'career_page_url': url,
                                                'best_job_sites': ['LinkedIn', 'Indeed', 'company careers page'],
                                                'search_tips': f"Monitor {url} for new job postings",
                                                'hiring_status': 'No current openings',
                                                'company_info': f'Career page discovered via Google search',
                                                'search_query': query
                                            },
                                            'source': 'google_search_career_found',
                                            'career_page_found': True,
                                            'career_page_url': url,
                                            'steps_completed': 6
                                        }
                        except Exception as e:
                            logger.debug(f"❌ Failed to crawl Google result {url}: {e}")
                            continue
                            
            except Exception as e:
                logger.warning(f"⚠️ Google search failed for query '{query}': {e}")
                continue
        
        logger.info(f"❌ Google search found no accessible career pages for {company_name}")
        return None
    
    def _google_search_api(self, query: str) -> List[str]:
        """Perform actual Google search using multiple methods"""
        logger.info(f"🔍 Searching Google for: '{query}'")
        
        try:
            # Method 1: Try Google Custom Search API if available
            google_api_key = os.getenv('GOOGLE_API_KEY')
            google_cx = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
            
            if google_api_key and google_cx:
                return self._google_custom_search_api(query, google_api_key, google_cx)
            
            # Method 2: Try SerpAPI if available
            serpapi_key = os.getenv('SERPAPI_KEY')
            if serpapi_key:
                return self._serpapi_search(query, serpapi_key)
            
            # Method 3: Direct Google search (basic scraping - may be blocked)
            logger.warning("⚠️ No Google API keys found, skipping Google search to avoid hanging")
            logger.info("💡 Add GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID to .env for real Google search")
            return []
            
        except Exception as e:
            logger.error(f"💥 Google search API failed: {e}")
            return []
    
    def _google_custom_search_api(self, query: str, api_key: str, cx: str) -> List[str]:
        """Use Google Custom Search API"""
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': cx,
                'q': query,
                'num': 5  # Get top 5 results
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            urls = []
            
            if 'items' in data:
                for item in data['items']:
                    urls.append(item['link'])
                    
            logger.info(f"✅ Google Custom Search found {len(urls)} results")
            return urls
            
        except Exception as e:
            logger.error(f"💥 Google Custom Search API failed: {e}")
            return []
    
    def _serpapi_search(self, query: str, api_key: str) -> List[str]:
        """Use SerpAPI for Google search"""
        try:
            url = "https://serpapi.com/search"
            params = {
                'api_key': api_key,
                'engine': 'google',
                'q': query,
                'num': 5
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            urls = []
            
            if 'organic_results' in data:
                for result in data['organic_results']:
                    urls.append(result['link'])
                    
            logger.info(f"✅ SerpAPI found {len(urls)} results")
            return urls
            
        except Exception as e:
            logger.error(f"💥 SerpAPI failed: {e}")
            return []
    
    def _direct_google_search(self, query: str) -> List[str]:
        """Direct Google search (may be blocked, use as last resort)"""
        try:
            search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            urls = []
            
            # Extract URLs from search results
            for result in soup.find_all('a', href=True):
                href = result['href']
                if href.startswith('/url?q='):
                    # Extract actual URL from Google redirect
                    actual_url = href.split('/url?q=')[1].split('&')[0]
                    actual_url = requests.utils.unquote(actual_url)
                    if actual_url.startswith('http'):
                        urls.append(actual_url)
                        
            logger.info(f"✅ Direct Google search found {len(urls)} results")
            return urls[:5]  # Return top 5
            
        except Exception as e:
            logger.error(f"💥 Direct Google search failed: {e}")
            return []
    
    def _is_likely_career_url(self, url: str) -> bool:
        """Check if URL looks like a career page"""
        url_lower = url.lower()
        career_indicators = [
            'career', 'job', 'hiring', 'work', 'employment', 
            'join', 'team', 'opportunities', 'openings'
        ]
        
        return any(indicator in url_lower for indicator in career_indicators)