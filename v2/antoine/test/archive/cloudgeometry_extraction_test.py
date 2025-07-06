#!/usr/bin/env python3
"""
CloudGeometry Content Extraction Testing Suite
Testing multiple extraction methods for https://www.cloudgeometry.com/services
"""

import requests
import time
from bs4 import BeautifulSoup
import trafilatura
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json
import os
from typing import Dict, List, Optional

# Optional imports - install if needed
try:
    from newspaper import Article
    HAS_NEWSPAPER = True
except ImportError:
    HAS_NEWSPAPER = False
    print("newspaper3k not available - install with: pip install newspaper3k")

try:
    from readability import Document
    HAS_READABILITY = True
except ImportError:
    HAS_READABILITY = False
    print("python-readability not available - install with: pip install readability-lxml")

try:
    from goose3 import Goose
    HAS_GOOSE = True
except ImportError:
    HAS_GOOSE = False
    print("goose3 not available - install with: pip install goose3")

try:
    from crawl4ai import AsyncWebCrawler
    HAS_CRAWL4AI = True
except ImportError:
    HAS_CRAWL4AI = False
    print("crawl4ai not available - install with: pip install crawl4ai")

try:
    from boilerpy3 import extractors
    HAS_BOILERPY = True
except ImportError:
    HAS_BOILERPY = False
    print("boilerpy3 not available - install with: pip install boilerpy3")

class CloudGeometryExtractor:
    """Testing suite for different content extraction methods"""
    
    def __init__(self):
        self.url = "https://www.cloudgeometry.com/services"
        self.results = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def get_page_html(self) -> str:
        """Get raw HTML content"""
        try:
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching HTML: {e}")
            return ""
    
    def test_trafilatura(self) -> Dict:
        """Test Trafilatura extraction"""
        print("\n🔍 Testing Trafilatura...")
        try:
            # Basic extraction
            content = trafilatura.extract(self.url)
            
            # Advanced extraction with metadata
            metadata = trafilatura.extract_metadata(self.url)
            
            # Extract with all options
            downloaded = trafilatura.fetch_url(self.url)
            detailed_content = trafilatura.extract(
                downloaded,
                include_comments=True,
                include_tables=True,
                include_links=True,
                include_images=True,
                no_fallback=False,
                favor_precision=False,
                favor_recall=True
            )
            
            return {
                'method': 'trafilatura',
                'basic_content': content,
                'detailed_content': detailed_content,
                'metadata': metadata,
                'char_count': len(content or ''),
                'detailed_char_count': len(detailed_content or ''),
                'success': bool(content)
            }
        except Exception as e:
            return {
                'method': 'trafilatura',
                'error': str(e),
                'success': False
            }
    
    def test_newspaper3k(self) -> Dict:
        """Test Newspaper3k extraction"""
        print("\n📰 Testing Newspaper3k...")
        if not HAS_NEWSPAPER:
            return {'method': 'newspaper3k', 'error': 'Library not available', 'success': False}
        
        try:
            article = Article(self.url)
            article.download()
            article.parse()
            
            return {
                'method': 'newspaper3k',
                'title': article.title,
                'text': article.text,
                'summary': article.summary if hasattr(article, 'summary') else '',
                'authors': article.authors,
                'publish_date': str(article.publish_date) if article.publish_date else '',
                'char_count': len(article.text or ''),
                'success': bool(article.text)
            }
        except Exception as e:
            return {
                'method': 'newspaper3k',
                'error': str(e),
                'success': False
            }
    
    def test_readability(self) -> Dict:
        """Test python-readability extraction"""
        print("\n📖 Testing python-readability...")
        if not HAS_READABILITY:
            return {'method': 'readability', 'error': 'Library not available', 'success': False}
        
        try:
            html = self.get_page_html()
            if not html:
                return {'method': 'readability', 'error': 'Failed to fetch HTML', 'success': False}
            
            doc = Document(html)
            
            return {
                'method': 'readability',
                'title': doc.title(),
                'content': doc.summary(),
                'char_count': len(doc.summary() or ''),
                'success': bool(doc.summary())
            }
        except Exception as e:
            return {
                'method': 'readability',
                'error': str(e),
                'success': False
            }
    
    def test_goose3(self) -> Dict:
        """Test Goose3 extraction"""
        print("\n🦢 Testing Goose3...")
        if not HAS_GOOSE:
            return {'method': 'goose3', 'error': 'Library not available', 'success': False}
        
        try:
            g = Goose()
            article = g.extract(url=self.url)
            
            return {
                'method': 'goose3',
                'title': article.title,
                'content': article.cleaned_text,
                'meta_description': article.meta_description,
                'meta_keywords': article.meta_keywords,
                'char_count': len(article.cleaned_text or ''),
                'success': bool(article.cleaned_text)
            }
        except Exception as e:
            return {
                'method': 'goose3',
                'error': str(e),
                'success': False
            }
    
    def test_boilerpy3(self) -> Dict:
        """Test BoilerPy3 extraction"""
        print("\n🔥 Testing BoilerPy3...")
        if not HAS_BOILERPY:
            return {'method': 'boilerpy3', 'error': 'Library not available', 'success': False}
        
        try:
            html = self.get_page_html()
            if not html:
                return {'method': 'boilerpy3', 'error': 'Failed to fetch HTML', 'success': False}
            
            # Try different extractors
            extractors_to_test = [
                ('ArticleExtractor', extractors.ArticleExtractor()),
                ('DefaultExtractor', extractors.DefaultExtractor()),
                ('CanolaExtractor', extractors.CanolaExtractor()),
                ('KeepEverythingExtractor', extractors.KeepEverythingExtractor())
            ]
            
            results = {}
            for name, extractor in extractors_to_test:
                try:
                    content = extractor.get_content(html)
                    results[name] = {
                        'content': content,
                        'char_count': len(content or '')
                    }
                except Exception as e:
                    results[name] = {'error': str(e)}
            
            # Use the best result
            best_result = max(results.items(), key=lambda x: x[1].get('char_count', 0))
            
            return {
                'method': 'boilerpy3',
                'extractor_used': best_result[0],
                'content': best_result[1].get('content', ''),
                'char_count': best_result[1].get('char_count', 0),
                'all_results': results,
                'success': bool(best_result[1].get('content'))
            }
        except Exception as e:
            return {
                'method': 'boilerpy3',
                'error': str(e),
                'success': False
            }
    
    def test_beautifulsoup_advanced(self) -> Dict:
        """Test advanced BeautifulSoup extraction strategies"""
        print("\n🍲 Testing Advanced BeautifulSoup...")
        try:
            html = self.get_page_html()
            if not html:
                return {'method': 'beautifulsoup', 'error': 'Failed to fetch HTML', 'success': False}
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Strategy 1: Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Strategy 2: Look for main content areas
            main_content = ""
            content_selectors = [
                'main',
                '[role="main"]',
                '.main-content',
                '.content',
                '#content',
                '.page-content',
                '.services-content',
                '.services-section',
                '.service-item',
                '.service-card'
            ]
            
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    main_content += "\n".join([elem.get_text(strip=True) for elem in elements])
                    break
            
            # Strategy 3: Extract specific service-related content
            service_keywords = [
                'aws', 'kubernetes', 'cloud', 'application', 'platform',
                'engineering', 'modernization', 'mlops', 'data', 'ai'
            ]
            
            service_content = []
            for text in soup.find_all(text=True):
                text_lower = text.lower()
                if any(keyword in text_lower for keyword in service_keywords):
                    if len(text.strip()) > 10:  # Avoid short snippets
                        service_content.append(text.strip())
            
            # Strategy 4: Extract structured data
            structured_data = []
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    structured_data.append(json.loads(script.string))
                except:
                    pass
            
            # Strategy 5: Extract all headings and their content
            headings_content = []
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                headings_content.append(heading.get_text(strip=True))
                # Get following paragraphs
                for sibling in heading.find_next_siblings(['p', 'div', 'ul', 'li']):
                    if sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        break
                    headings_content.append(sibling.get_text(strip=True))
            
            return {
                'method': 'beautifulsoup_advanced',
                'main_content': main_content,
                'service_content': service_content[:10],  # Limit for readability
                'structured_data': structured_data,
                'headings_content': headings_content[:20],  # Limit for readability
                'main_char_count': len(main_content),
                'service_char_count': len(' '.join(service_content)),
                'headings_char_count': len(' '.join(headings_content)),
                'success': bool(main_content or service_content or headings_content)
            }
        except Exception as e:
            return {
                'method': 'beautifulsoup_advanced',
                'error': str(e),
                'success': False
            }
    
    def test_selenium_extraction(self) -> Dict:
        """Test Selenium with headless browser"""
        print("\n🤖 Testing Selenium...")
        try:
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                driver.get(self.url)
                
                # Wait for page to load
                time.sleep(3)
                
                # Wait for specific elements that indicate content is loaded
                wait = WebDriverWait(driver, 10)
                try:
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
                except TimeoutException:
                    pass  # Continue even if main element not found
                
                # Extract content using various strategies
                page_source = driver.page_source
                
                # Get all text content
                body = driver.find_element(By.TAG_NAME, "body")
                all_text = body.text
                
                # Try to find specific service content
                service_elements = []
                service_selectors = [
                    "[class*='service']",
                    "[class*='offering']",
                    "[class*='solution']",
                    "[id*='service']",
                    "main",
                    ".content"
                ]
                
                for selector in service_selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            text = element.text.strip()
                            if text and len(text) > 20:
                                service_elements.append(text)
                    except:
                        continue
                
                # Look for AWS and partnership mentions
                partnership_content = []
                try:
                    elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'AWS') or contains(text(), 'Cloud Native') or contains(text(), 'Kubernetes') or contains(text(), 'partnership')]")
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 10:
                            partnership_content.append(text)
                except:
                    pass
                
                return {
                    'method': 'selenium',
                    'page_title': driver.title,
                    'all_text': all_text,
                    'service_elements': service_elements[:10],  # Limit for readability
                    'partnership_content': partnership_content[:10],
                    'page_source_length': len(page_source),
                    'all_text_char_count': len(all_text),
                    'service_char_count': len(' '.join(service_elements)),
                    'partnership_char_count': len(' '.join(partnership_content)),
                    'success': bool(all_text)
                }
            finally:
                driver.quit()
                
        except Exception as e:
            return {
                'method': 'selenium',
                'error': str(e),
                'success': False
            }
    
    async def test_crawl4ai(self) -> Dict:
        """Test Crawl4AI extraction"""
        print("\n🚀 Testing Crawl4AI...")
        if not HAS_CRAWL4AI:
            return {'method': 'crawl4ai', 'error': 'Library not available', 'success': False}
        
        try:
            async with AsyncWebCrawler(verbose=True) as crawler:
                result = await crawler.arun(
                    url=self.url,
                    word_count_threshold=10,
                    extraction_strategy="CosineStrategy",
                    chunking_strategy="RegexChunking",
                    css_selector="main, .content, .services, [class*='service']",
                    wait_for="body",
                    delay_before_return_html=3
                )
                
                return {
                    'method': 'crawl4ai',
                    'markdown': result.markdown,
                    'cleaned_html': result.cleaned_html,
                    'extracted_content': result.extracted_content,
                    'media': result.media,
                    'links': result.links,
                    'metadata': result.metadata,
                    'markdown_char_count': len(result.markdown or ''),
                    'cleaned_html_char_count': len(result.cleaned_html or ''),
                    'success': bool(result.markdown or result.cleaned_html)
                }
        except Exception as e:
            return {
                'method': 'crawl4ai',
                'error': str(e),
                'success': False
            }
    
    def run_all_tests(self) -> Dict:
        """Run all extraction tests"""
        print(f"\n🔬 Testing content extraction for: {self.url}")
        print("=" * 60)
        
        # Run synchronous tests
        tests = [
            self.test_trafilatura,
            self.test_newspaper3k,
            self.test_readability,
            self.test_goose3,
            self.test_boilerpy3,
            self.test_beautifulsoup_advanced,
            self.test_selenium_extraction
        ]
        
        results = {}
        for test in tests:
            try:
                result = test()
                results[result['method']] = result
                
                # Print summary
                if result['success']:
                    char_count = result.get('char_count', 0) or result.get('all_text_char_count', 0) or result.get('main_char_count', 0)
                    print(f"✅ {result['method']}: {char_count} characters extracted")
                else:
                    print(f"❌ {result['method']}: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ {test.__name__}: {str(e)}")
                results[test.__name__] = {'error': str(e), 'success': False}
        
        # Run async test
        try:
            crawl4ai_result = asyncio.run(self.test_crawl4ai())
            results['crawl4ai'] = crawl4ai_result
            
            if crawl4ai_result['success']:
                char_count = crawl4ai_result.get('markdown_char_count', 0)
                print(f"✅ crawl4ai: {char_count} characters extracted")
            else:
                print(f"❌ crawl4ai: {crawl4ai_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ crawl4ai: {str(e)}")
            results['crawl4ai'] = {'error': str(e), 'success': False}
        
        return results
    
    def analyze_results(self, results: Dict) -> Dict:
        """Analyze and compare results"""
        print("\n📊 Analysis Results:")
        print("=" * 60)
        
        successful_methods = []
        char_counts = {}
        
        for method, result in results.items():
            if result.get('success'):
                successful_methods.append(method)
                
                # Get character count
                char_count = (
                    result.get('char_count', 0) or 
                    result.get('all_text_char_count', 0) or 
                    result.get('main_char_count', 0) or 
                    result.get('markdown_char_count', 0)
                )
                char_counts[method] = char_count
        
        # Sort by character count
        sorted_methods = sorted(char_counts.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\nSuccessful methods: {len(successful_methods)}")
        print("\nRanked by content extracted:")
        for method, count in sorted_methods:
            print(f"  {method}: {count:,} characters")
        
        # Find methods that extracted significantly more content than Trafilatura
        trafilatura_count = char_counts.get('trafilatura', 0)
        better_methods = [(m, c) for m, c in sorted_methods if c > trafilatura_count * 1.5]
        
        analysis = {
            'successful_methods': successful_methods,
            'char_counts': char_counts,
            'ranked_methods': sorted_methods,
            'trafilatura_baseline': trafilatura_count,
            'better_than_trafilatura': better_methods,
            'recommended_method': sorted_methods[0][0] if sorted_methods else None
        }
        
        if better_methods:
            print(f"\n🎯 Methods significantly better than Trafilatura ({trafilatura_count} chars):")
            for method, count in better_methods:
                improvement = (count - trafilatura_count) / trafilatura_count * 100
                print(f"  {method}: {count:,} chars (+{improvement:.1f}%)")
        
        return analysis

def main():
    """Main execution function"""
    extractor = CloudGeometryExtractor()
    results = extractor.run_all_tests()
    analysis = extractor.analyze_results(results)
    
    # Save results to file
    output_file = 'cloudgeometry_extraction_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'url': extractor.url,
            'timestamp': time.time(),
            'results': results,
            'analysis': analysis
        }, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Print recommendations
    print("\n🔧 Recommendations:")
    print("=" * 60)
    
    if analysis['recommended_method']:
        print(f"Best performing method: {analysis['recommended_method']}")
        
        if analysis['better_than_trafilatura']:
            print("\nFor CloudGeometry services page, consider switching to:")
            for method, count in analysis['better_than_trafilatura'][:3]:
                print(f"  • {method} (extracts {count:,} characters)")
        
        print("\nNext steps:")
        print("1. Install missing libraries for better extraction:")
        print("   pip install newspaper3k readability-lxml goose3 crawl4ai boilerpy3")
        print("2. Test the recommended method in your production pipeline")
        print("3. Consider using Selenium or Crawl4AI for JavaScript-heavy sites")
        print("4. Implement fallback chain: Crawl4AI → Selenium → BeautifulSoup → Trafilatura")

if __name__ == "__main__":
    main()