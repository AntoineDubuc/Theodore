"""
Advanced web scraper for company intelligence extraction using Crawl4AI
Multi-page crawling with AI-powered content extraction
"""

import logging
import time
import re
import asyncio
from typing import Dict, Optional, List, Tuple
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup, Comment
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from src.models import CompanyData, CompanyIntelligenceConfig

logger = logging.getLogger(__name__)


class CompanyWebScraper:
    """Lambda-compatible web scraper for company websites"""
    
    def __init__(self, config: CompanyIntelligenceConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Technology detection patterns
        self.tech_patterns = {
            'react': [r'react', r'_react', r'react-dom'],
            'vue': [r'vue\.js', r'vuejs', r'@vue/'],
            'angular': [r'angular', r'@angular/', r'ng-'],
            'javascript': [r'javascript', r'\.js', r'jquery'],
            'python': [r'python', r'django', r'flask', r'fastapi'],
            'node': [r'node\.js', r'nodejs', r'express'],
            'wordpress': [r'wp-content', r'wordpress', r'/wp/'],
            'shopify': [r'shopify', r'myshopify\.com'],
            'salesforce': [r'salesforce', r'force\.com', r'lightning'],
            'hubspot': [r'hubspot', r'hs-analytics', r'_hsq'],
            'aws': [r'amazonaws\.com', r'aws', r'cloudfront'],
            'stripe': [r'stripe', r'js\.stripe\.com'],
            'intercom': [r'intercom', r'widget\.intercom'],
            'zendesk': [r'zendesk', r'zdassets'],
            'google_analytics': [r'google-analytics', r'gtag', r'ga\('],
        }
        
        # Industry keyword patterns
        self.industry_patterns = {
            'healthcare': [r'health', r'medical', r'patient', r'clinical', r'hospital', r'doctor'],
            'fintech': [r'financial', r'banking', r'payment', r'investment', r'trading', r'crypto'],
            'ecommerce': [r'shop', r'store', r'commerce', r'retail', r'marketplace', r'buy'],
            'saas': [r'software', r'platform', r'cloud', r'api', r'service', r'solution'],
            'education': [r'education', r'learning', r'school', r'university', r'course'],
            'manufacturing': [r'manufacturing', r'production', r'factory', r'industrial'],
            'real_estate': [r'real estate', r'property', r'housing', r'rental'],
            'logistics': [r'logistics', r'shipping', r'delivery', r'transport', r'supply chain'],
            'marketing': [r'marketing', r'advertising', r'digital agency', r'seo', r'campaign'],
        }
    
    def scrape_company(self, company_data: CompanyData) -> CompanyData:
        """Scrape and analyze a company website"""
        try:
            # Normalize website URL
            url = self._normalize_url(company_data.website)
            
            # Fetch website content
            content, status_code = self._fetch_website_content(url)
            
            if content is None:
                company_data.scrape_status = "failed"
                company_data.scrape_error = f"Failed to fetch content (status: {status_code})"
                return company_data
            
            # Store raw content
            company_data.raw_content = content[:self.config.max_content_length]
            
            # Extract structured data
            self._extract_company_intelligence(company_data, content)
            
            company_data.scrape_status = "success"
            logger.info(f"Successfully scraped {company_data.name}")
            
        except Exception as e:
            logger.error(f"Error scraping {company_data.name}: {str(e)}")
            company_data.scrape_status = "failed"
            company_data.scrape_error = str(e)
        
        return company_data
    
    def _normalize_url(self, url: str) -> str:
        """Normalize website URL"""
        if not url:
            raise ValueError("No website URL provided")
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        
        # Remove trailing slash
        url = url.rstrip('/')
        
        return url
    
    def _fetch_website_content(self, url: str) -> Tuple[Optional[str], Optional[int]]:
        """Fetch website content with error handling"""
        try:
            response = self.session.get(
                url,
                timeout=self.config.request_timeout,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                return response.text, response.status_code
            else:
                logger.warning(f"HTTP {response.status_code} for {url}")
                return None, response.status_code
                
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout for {url}")
            return None, None
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error for {url}")
            return None, None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error for {url}: {str(e)}")
            return None, None
    
    def _extract_company_intelligence(self, company_data: CompanyData, html_content: str):
        """Extract structured intelligence from website content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()
        
        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Extract text content
        text_content = soup.get_text(separator=' ', strip=True)
        clean_text = re.sub(r'\s+', ' ', text_content).strip()
        
        # Detect technologies
        company_data.tech_stack = self._detect_technologies(html_content, clean_text)
        
        # Detect industry
        detected_industry = self._detect_industry(clean_text)
        if detected_industry and not company_data.industry:
            company_data.industry = detected_industry
        
        # Detect UI elements
        company_data.has_chat_widget = self._has_chat_widget(html_content)
        company_data.has_forms = self._has_forms(soup)
        
        # Extract key information
        company_data.key_services = self._extract_services(clean_text)
        company_data.pain_points = self._infer_pain_points(clean_text)
        
        # Determine company size hints
        if not company_data.company_size:
            company_data.company_size = self._estimate_company_size(clean_text)
    
    def _detect_technologies(self, html_content: str, text_content: str) -> List[str]:
        """Detect technologies used by the company"""
        detected_techs = []
        
        # Combine HTML and text for comprehensive detection
        combined_content = (html_content + " " + text_content).lower()
        
        for tech, patterns in self.tech_patterns.items():
            for pattern in patterns:
                if re.search(pattern, combined_content, re.IGNORECASE):
                    detected_techs.append(tech)
                    break  # Found this tech, move to next
        
        return list(set(detected_techs))  # Remove duplicates
    
    def _detect_industry(self, text_content: str) -> Optional[str]:
        """Detect company industry from content"""
        text_lower = text_content.lower()
        industry_scores = {}
        
        for industry, keywords in self.industry_patterns.items():
            score = 0
            for keyword in keywords:
                matches = len(re.findall(keyword, text_lower, re.IGNORECASE))
                score += matches
            
            if score > 0:
                industry_scores[industry] = score
        
        if industry_scores:
            # Return industry with highest score
            return max(industry_scores, key=industry_scores.get)
        
        return None
    
    def _has_chat_widget(self, html_content: str) -> bool:
        """Detect if website has chat widget"""
        chat_indicators = [
            r'intercom', r'zendesk', r'drift', r'hubspot.*chat',
            r'livechat', r'tawk\.to', r'crisp', r'freshchat'
        ]
        
        html_lower = html_content.lower()
        return any(re.search(pattern, html_lower) for pattern in chat_indicators)
    
    def _has_forms(self, soup: BeautifulSoup) -> bool:
        """Detect if website has forms (lead capture)"""
        forms = soup.find_all('form')
        
        # Look for contact/lead forms (not just search)
        lead_form_indicators = ['email', 'contact', 'demo', 'trial', 'signup']
        
        for form in forms:
            form_text = form.get_text().lower()
            if any(indicator in form_text for indicator in lead_form_indicators):
                return True
        
        return False
    
    def _extract_services(self, text_content: str) -> List[str]:
        """Extract key services/offerings mentioned"""
        # Look for service-related sections
        service_patterns = [
            r'we offer ([^.]+)',
            r'our services include ([^.]+)',
            r'solutions[:\s]+([^.]+)',
            r'services[:\s]+([^.]+)',
        ]
        
        services = []
        for pattern in service_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            services.extend(matches)
        
        # Clean and limit results
        cleaned_services = []
        for service in services[:5]:  # Limit to 5 services
            cleaned = re.sub(r'[^\w\s]', '', service).strip()
            if cleaned and len(cleaned) > 5:
                cleaned_services.append(cleaned)
        
        return cleaned_services
    
    def _infer_pain_points(self, text_content: str) -> List[str]:
        """Infer pain points from solution descriptions"""
        # Common pain point indicators
        pain_indicators = [
            r'struggling with ([^.]+)',
            r'challenges.*?include ([^.]+)',
            r'problems.*?with ([^.]+)',
            r'difficult.*?to ([^.]+)',
            r'hard to ([^.]+)',
            r'eliminate ([^.]+)',
            r'reduce ([^.]+)',
            r'solve ([^.]+)',
        ]
        
        pain_points = []
        for pattern in pain_indicators:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            pain_points.extend(matches)
        
        # Clean and deduplicate
        cleaned_pains = []
        for pain in pain_points[:3]:  # Limit to 3 pain points
            cleaned = re.sub(r'[^\w\s]', '', pain).strip()
            if cleaned and len(cleaned) > 5:
                cleaned_pains.append(cleaned)
        
        return list(set(cleaned_pains))
    
    def _estimate_company_size(self, text_content: str) -> str:
        """Estimate company size from content tone and mentions"""
        text_lower = text_content.lower()
        
        # Enterprise indicators
        enterprise_indicators = [
            'enterprise', 'fortune 500', 'global', 'worldwide',
            'thousands of employees', 'offices in', 'headquarters'
        ]
        
        # Startup indicators
        startup_indicators = [
            'startup', 'founded in 202', 'seed funding', 'series a',
            'small team', 'agile', 'innovative'
        ]
        
        enterprise_score = sum(1 for indicator in enterprise_indicators if indicator in text_lower)
        startup_score = sum(1 for indicator in startup_indicators if indicator in text_lower)
        
        if enterprise_score > startup_score:
            return 'enterprise'
        elif startup_score > 0:
            return 'startup'
        else:
            return 'SMB'  # Default to small-medium business
    
    def batch_scrape_companies(self, companies: List[CompanyData]) -> List[CompanyData]:
        """Batch scrape multiple companies with rate limiting"""
        scraped_companies = []
        
        for i, company in enumerate(companies):
            logger.info(f"Scraping {i+1}/{len(companies)}: {company.name}")
            
            scraped_company = self.scrape_company(company)
            scraped_companies.append(scraped_company)
            
            # Rate limiting
            if i < len(companies) - 1:  # Don't sleep after the last company
                sleep_time = 1.0 / self.config.requests_per_second
                time.sleep(sleep_time)
        
        return scraped_companies