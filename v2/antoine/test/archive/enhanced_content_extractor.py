#!/usr/bin/env python3
"""
Enhanced Content Extractor for Service Pages
Production-ready implementation with fallback strategies for better content extraction
"""

import requests
import time
import logging
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from bs4 import BeautifulSoup
import trafilatura
import json
import asyncio
from urllib.parse import urljoin, urlparse
import re

# Optional imports with graceful fallbacks
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

try:
    from crawl4ai import AsyncWebCrawler
    HAS_CRAWL4AI = True
except ImportError:
    HAS_CRAWL4AI = False

try:
    from newspaper import Article
    HAS_NEWSPAPER = True
except ImportError:
    HAS_NEWSPAPER = False

try:
    from boilerpy3 import extractors
    HAS_BOILERPY = True
except ImportError:
    HAS_BOILERPY = False

@dataclass
class ExtractionResult:
    """Results from content extraction"""
    method: str
    content: str
    char_count: int
    success: bool
    extraction_time: float
    metadata: Dict = None
    error: str = None

class EnhancedContentExtractor:
    """
    Enhanced content extractor with multiple strategies and fallbacks
    Specifically optimized for service pages and JavaScript-heavy sites
    """
    
    def __init__(self, timeout: int = 30, user_agent: str = None):
        self.timeout = timeout
        self.user_agent = user_agent or (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
        
        # Service page specific selectors
        self.service_selectors = [
            'main',
            'article',
            '.main-content',
            '.content',
            '.services',
            '.service-section',
            '.services-section',
            '[class*="service"]',
            '[class*="offering"]',
            '[class*="solution"]',
            '[class*="capability"]',
            '[class*="expertise"]',
            '[id*="service"]',
            '.service-card',
            '.offering-card',
            '.solution-card'
        ]
        
        # Partnership/certification selectors
        self.partnership_selectors = [
            '[class*="partner"]',
            '[class*="certification"]',
            '[class*="badge"]',
            '[class*="credential"]',
            '.aws-partner',
            '.cncf-member',
            '.partner-logo',
            '.certification-badge'
        ]
        
        # Keywords for service content identification
        self.service_keywords = [
            'aws', 'kubernetes', 'cloud', 'platform', 'engineering', 'modernization',
            'mlops', 'ai', 'partnership', 'service', 'offering', 'solution',
            'consulting', 'development', 'devops', 'infrastructure', 'data'
        ]
    
    def extract_with_trafilatura_advanced(self, url: str) -> ExtractionResult:
        """Enhanced Trafilatura extraction with all options"""
        start_time = time.time()
        
        try:
            # Download content
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return ExtractionResult(
                    method="trafilatura_advanced",
                    content="",
                    char_count=0,
                    success=False,
                    extraction_time=time.time() - start_time,
                    error="Failed to download content"
                )
            
            # Try multiple extraction strategies
            strategies = [
                # Strategy 1: Favor recall over precision
                {
                    'include_comments': True,
                    'include_tables': True,
                    'include_links': True,
                    'include_images': True,
                    'no_fallback': False,
                    'favor_precision': False,
                    'favor_recall': True
                },
                # Strategy 2: Include formatting
                {
                    'include_formatting': True,
                    'include_links': True,
                    'include_tables': True,
                    'no_fallback': False
                },
                # Strategy 3: Basic with fallback
                {
                    'no_fallback': False,
                    'include_tables': True
                }
            ]
            
            best_content = ""
            best_metadata = None
            
            for strategy in strategies:
                try:
                    content = trafilatura.extract(downloaded, **strategy)
                    if content and len(content) > len(best_content):
                        best_content = content
                        best_metadata = trafilatura.extract_metadata(downloaded)
                except Exception as e:
                    self.logger.debug(f"Trafilatura strategy failed: {e}")
                    continue
            
            return ExtractionResult(
                method="trafilatura_advanced",
                content=best_content,
                char_count=len(best_content),
                success=bool(best_content),
                extraction_time=time.time() - start_time,
                metadata=best_metadata
            )
            
        except Exception as e:
            return ExtractionResult(
                method="trafilatura_advanced",
                content="",
                char_count=0,
                success=False,
                extraction_time=time.time() - start_time,
                error=str(e)
            )
    
    def extract_with_beautifulsoup_advanced(self, url: str) -> ExtractionResult:
        """Advanced BeautifulSoup extraction with service-specific strategies"""
        start_time = time.time()
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript']):
                element.decompose()
            
            content_parts = []
            
            # Strategy 1: Extract from main content containers
            for selector in self.service_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(separator=' ', strip=True)
                    if len(text) > 50:  # Filter out short snippets
                        content_parts.append(text)
            
            # Strategy 2: Extract partnership/certification content
            for selector in self.partnership_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(separator=' ', strip=True)
                    if len(text) > 10:
                        content_parts.append(text)
            
            # Strategy 3: Extract structured data
            structured_content = []
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        # Extract relevant fields
                        for key, value in data.items():
                            if isinstance(value, str) and len(value) > 20:
                                structured_content.append(f"{key}: {value}")
                except:
                    pass
            
            # Strategy 4: Keyword-based extraction
            all_text = soup.get_text()
            keyword_sentences = []
            sentences = re.split(r'[.!?]+', all_text)
            
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 30:
                    sentence_lower = sentence.lower()
                    if any(keyword in sentence_lower for keyword in self.service_keywords):
                        keyword_sentences.append(sentence)
            
            # Combine all content
            all_content = content_parts + structured_content + keyword_sentences
            
            # Remove duplicates while preserving order
            unique_content = []
            seen = set()
            for content in all_content:
                if content not in seen:
                    unique_content.append(content)
                    seen.add(content)
            
            final_content = '\n'.join(unique_content)
            
            return ExtractionResult(
                method="beautifulsoup_advanced",
                content=final_content,
                char_count=len(final_content),
                success=bool(final_content),
                extraction_time=time.time() - start_time,
                metadata={
                    'title': soup.title.string if soup.title else '',
                    'content_parts': len(content_parts),
                    'structured_parts': len(structured_content),
                    'keyword_parts': len(keyword_sentences)
                }
            )
            
        except Exception as e:
            return ExtractionResult(
                method="beautifulsoup_advanced",
                content="",
                char_count=0,
                success=False,
                extraction_time=time.time() - start_time,
                error=str(e)
            )
    
    def extract_with_selenium(self, url: str) -> ExtractionResult:
        """Selenium extraction with JavaScript execution"""
        start_time = time.time()
        
        if not HAS_SELENIUM:
            return ExtractionResult(
                method="selenium",
                content="",
                char_count=0,
                success=False,
                extraction_time=time.time() - start_time,
                error="Selenium not available"
            )
        
        try:
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument(f'--user-agent={self.user_agent}')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                driver.get(url)
                
                # Wait for page to load
                time.sleep(3)
                
                # Wait for specific elements
                wait = WebDriverWait(driver, 10)
                try:
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                except TimeoutException:
                    pass
                
                # Extract content using multiple strategies
                content_parts = []
                
                # Strategy 1: Get all visible text
                body = driver.find_element(By.TAG_NAME, "body")
                all_text = body.text
                if all_text:
                    content_parts.append(all_text)
                
                # Strategy 2: Extract from specific service elements
                for selector in self.service_selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            text = element.text.strip()
                            if text and len(text) > 30:
                                content_parts.append(text)
                    except:
                        continue
                
                # Strategy 3: Extract partnership content
                for selector in self.partnership_selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            text = element.text.strip()
                            if text and len(text) > 10:
                                content_parts.append(text)
                    except:
                        continue
                
                # Strategy 4: Keyword-based XPath extraction
                for keyword in self.service_keywords:
                    try:
                        xpath = f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]"
                        elements = driver.find_elements(By.XPATH, xpath)
                        for element in elements:
                            text = element.text.strip()
                            if text and len(text) > 20:
                                content_parts.append(text)
                    except:
                        continue
                
                # Remove duplicates and combine
                unique_content = list(dict.fromkeys(content_parts))  # Preserve order
                final_content = '\n'.join(unique_content)
                
                return ExtractionResult(
                    method="selenium",
                    content=final_content,
                    char_count=len(final_content),
                    success=bool(final_content),
                    extraction_time=time.time() - start_time,
                    metadata={
                        'title': driver.title,
                        'url': driver.current_url,
                        'content_parts': len(content_parts),
                        'unique_parts': len(unique_content)
                    }
                )
                
            finally:
                driver.quit()
                
        except Exception as e:
            return ExtractionResult(
                method="selenium",
                content="",
                char_count=0,
                success=False,
                extraction_time=time.time() - start_time,
                error=str(e)
            )
    
    async def extract_with_crawl4ai(self, url: str) -> ExtractionResult:
        """Crawl4AI extraction with AI-powered content extraction"""
        start_time = time.time()
        
        if not HAS_CRAWL4AI:
            return ExtractionResult(
                method="crawl4ai",
                content="",
                char_count=0,
                success=False,
                extraction_time=time.time() - start_time,
                error="Crawl4AI not available"
            )
        
        try:
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(
                    url=url,
                    word_count_threshold=10,
                    extraction_strategy="CosineStrategy",
                    css_selector=", ".join(self.service_selectors),
                    wait_for="body",
                    delay_before_return_html=3,
                    page_timeout=self.timeout * 1000  # Convert to milliseconds
                )
                
                # Combine markdown and cleaned HTML content
                content_parts = []
                
                if result.markdown:
                    content_parts.append(result.markdown)
                
                if result.cleaned_html:
                    soup = BeautifulSoup(result.cleaned_html, 'html.parser')
                    text = soup.get_text(separator=' ', strip=True)
                    if text:
                        content_parts.append(text)
                
                if result.extracted_content:
                    for item in result.extracted_content:
                        if isinstance(item, dict) and 'content' in item:
                            content_parts.append(item['content'])
                        elif isinstance(item, str):
                            content_parts.append(item)
                
                final_content = '\n'.join(content_parts)
                
                return ExtractionResult(
                    method="crawl4ai",
                    content=final_content,
                    char_count=len(final_content),
                    success=bool(final_content),
                    extraction_time=time.time() - start_time,
                    metadata={
                        'title': result.metadata.get('title', '') if result.metadata else '',
                        'links_count': len(result.links) if result.links else 0,
                        'media_count': len(result.media) if result.media else 0,
                        'content_parts': len(content_parts)
                    }
                )
                
        except Exception as e:
            return ExtractionResult(
                method="crawl4ai",
                content="",
                char_count=0,
                success=False,
                extraction_time=time.time() - start_time,
                error=str(e)
            )
    
    def extract_with_newspaper(self, url: str) -> ExtractionResult:
        """Newspaper3k extraction"""
        start_time = time.time()
        
        if not HAS_NEWSPAPER:
            return ExtractionResult(
                method="newspaper3k",
                content="",
                char_count=0,
                success=False,
                extraction_time=time.time() - start_time,
                error="Newspaper3k not available"
            )
        
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            return ExtractionResult(
                method="newspaper3k",
                content=article.text,
                char_count=len(article.text),
                success=bool(article.text),
                extraction_time=time.time() - start_time,
                metadata={
                    'title': article.title,
                    'authors': article.authors,
                    'publish_date': str(article.publish_date) if article.publish_date else '',
                    'top_image': article.top_image
                }
            )
            
        except Exception as e:
            return ExtractionResult(
                method="newspaper3k",
                content="",
                char_count=0,
                success=False,
                extraction_time=time.time() - start_time,
                error=str(e)
            )
    
    def extract_with_boilerpy(self, url: str) -> ExtractionResult:
        """BoilerPy3 extraction with multiple algorithms"""
        start_time = time.time()
        
        if not HAS_BOILERPY:
            return ExtractionResult(
                method="boilerpy3",
                content="",
                char_count=0,
                success=False,
                extraction_time=time.time() - start_time,
                error="BoilerPy3 not available"
            )
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            html = response.text
            
            # Try different extractors
            extractors_to_test = [
                ('ArticleExtractor', extractors.ArticleExtractor()),
                ('DefaultExtractor', extractors.DefaultExtractor()),
                ('CanolaExtractor', extractors.CanolaExtractor()),
                ('KeepEverythingExtractor', extractors.KeepEverythingExtractor())
            ]
            
            best_content = ""
            best_extractor = ""
            
            for name, extractor in extractors_to_test:
                try:
                    content = extractor.get_content(html)
                    if content and len(content) > len(best_content):
                        best_content = content
                        best_extractor = name
                except:
                    continue
            
            return ExtractionResult(
                method="boilerpy3",
                content=best_content,
                char_count=len(best_content),
                success=bool(best_content),
                extraction_time=time.time() - start_time,
                metadata={
                    'extractor_used': best_extractor,
                    'extractors_tested': len(extractors_to_test)
                }
            )
            
        except Exception as e:
            return ExtractionResult(
                method="boilerpy3",
                content="",
                char_count=0,
                success=False,
                extraction_time=time.time() - start_time,
                error=str(e)
            )
    
    def extract_with_fallback_chain(self, url: str, min_chars: int = 1000) -> ExtractionResult:
        """
        Extract content using fallback chain of methods
        
        Args:
            url: URL to extract content from
            min_chars: Minimum character count to consider successful
        
        Returns:
            ExtractionResult from the first successful method
        """
        self.logger.info(f"Starting fallback chain extraction for: {url}")
        
        # Define extraction methods in order of preference
        methods = []
        
        # Add async methods
        if HAS_CRAWL4AI:
            methods.append(('crawl4ai', self.extract_with_crawl4ai))
        
        # Add sync methods
        if HAS_SELENIUM:
            methods.append(('selenium', self.extract_with_selenium))
        
        methods.extend([
            ('beautifulsoup_advanced', self.extract_with_beautifulsoup_advanced),
            ('trafilatura_advanced', self.extract_with_trafilatura_advanced)
        ])
        
        if HAS_BOILERPY:
            methods.append(('boilerpy3', self.extract_with_boilerpy))
        
        if HAS_NEWSPAPER:
            methods.append(('newspaper3k', self.extract_with_newspaper))
        
        # Try each method
        for method_name, method_func in methods:
            try:
                self.logger.info(f"Trying {method_name}...")
                
                # Handle async methods
                if asyncio.iscoroutinefunction(method_func):
                    result = asyncio.run(method_func(url))
                else:
                    result = method_func(url)
                
                # Check if result meets minimum requirements
                if result.success and result.char_count >= min_chars:
                    self.logger.info(f"✅ Success with {method_name}: {result.char_count} characters")
                    return result
                else:
                    self.logger.info(f"❌ {method_name} failed: {result.char_count} characters, error: {result.error}")
                    
            except Exception as e:
                self.logger.error(f"❌ {method_name} exception: {e}")
                continue
        
        # If no method succeeded, return the best attempt
        self.logger.warning("All extraction methods failed or returned insufficient content")
        return ExtractionResult(
            method="fallback_chain",
            content="",
            char_count=0,
            success=False,
            extraction_time=0,
            error="All extraction methods failed"
        )
    
    def extract_best(self, url: str, min_chars: int = 500) -> ExtractionResult:
        """
        Extract content using the best available method
        
        Args:
            url: URL to extract content from
            min_chars: Minimum character count to consider successful
        
        Returns:
            ExtractionResult from the best method
        """
        return self.extract_with_fallback_chain(url, min_chars)

# Usage examples and testing
def test_cloudgeometry_extraction():
    """Test extraction on CloudGeometry services page"""
    url = "https://www.cloudgeometry.com/services"
    
    extractor = EnhancedContentExtractor()
    result = extractor.extract_best(url)
    
    print(f"Method: {result.method}")
    print(f"Success: {result.success}")
    print(f"Characters: {result.char_count:,}")
    print(f"Extraction time: {result.extraction_time:.2f}s")
    
    if result.success:
        print(f"Content preview: {result.content[:500]}...")
    else:
        print(f"Error: {result.error}")
    
    return result

if __name__ == "__main__":
    # Test the extraction
    result = test_cloudgeometry_extraction()
    
    # Save results
    with open('enhanced_extraction_result.json', 'w') as f:
        json.dump({
            'url': 'https://www.cloudgeometry.com/services',
            'method': result.method,
            'success': result.success,
            'char_count': result.char_count,
            'extraction_time': result.extraction_time,
            'content': result.content,
            'metadata': result.metadata,
            'error': result.error
        }, f, indent=2)
    
    print("\n💾 Results saved to enhanced_extraction_result.json")