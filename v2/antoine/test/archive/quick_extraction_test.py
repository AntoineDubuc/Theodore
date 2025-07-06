#!/usr/bin/env python3
"""
Quick Content Extraction Test for CloudGeometry
Compare Trafilatura vs BeautifulSoup vs Selenium for immediate testing
"""

import requests
import time
from bs4 import BeautifulSoup
import trafilatura
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_trafilatura_extraction():
    """Test Trafilatura with all options"""
    url = "https://www.cloudgeometry.com/services"
    
    print("🔍 Testing Trafilatura extraction...")
    
    # Basic extraction
    basic_content = trafilatura.extract(url)
    print(f"Basic extraction: {len(basic_content or '')} characters")
    
    # Advanced extraction
    downloaded = trafilatura.fetch_url(url)
    if downloaded:
        advanced_content = trafilatura.extract(
            downloaded,
            include_comments=True,
            include_tables=True,
            include_links=True,
            include_images=True,
            no_fallback=False,
            favor_precision=False,
            favor_recall=True,
            with_metadata=True
        )
        print(f"Advanced extraction: {len(advanced_content or '')} characters")
        
        # Try different extraction strategies
        strategies = [
            {'favor_precision': True, 'favor_recall': False},
            {'favor_precision': False, 'favor_recall': True},
            {'no_fallback': True},
            {'no_fallback': False, 'include_formatting': True}
        ]
        
        for i, strategy in enumerate(strategies):
            content = trafilatura.extract(downloaded, **strategy)
            print(f"Strategy {i+1}: {len(content or '')} characters")
    
    return basic_content, advanced_content

def test_beautifulsoup_advanced():
    """Test advanced BeautifulSoup extraction"""
    url = "https://www.cloudgeometry.com/services"
    
    print("\n🍲 Testing Advanced BeautifulSoup extraction...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Remove unwanted elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript']):
        element.decompose()
    
    # Strategy 1: Look for main content containers
    main_containers = soup.find_all(['main', 'article', 'section'])
    main_content = []
    for container in main_containers:
        text = container.get_text(separator=' ', strip=True)
        if len(text) > 100:  # Only substantial content
            main_content.append(text)
    
    # Strategy 2: Look for service-specific content
    service_selectors = [
        '[class*="service"]',
        '[class*="offering"]',
        '[class*="solution"]',
        '[id*="service"]',
        '.content',
        '.main-content'
    ]
    
    service_content = []
    for selector in service_selectors:
        elements = soup.select(selector)
        for element in elements:
            text = element.get_text(separator=' ', strip=True)
            if len(text) > 50:
                service_content.append(text)
    
    # Strategy 3: Extract all meaningful paragraphs and lists
    content_elements = soup.find_all(['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    paragraph_content = []
    for element in content_elements:
        text = element.get_text(strip=True)
        if len(text) > 20:  # Filter out short snippets
            paragraph_content.append(text)
    
    # Strategy 4: Look for specific keywords
    keyword_content = []
    keywords = ['aws', 'kubernetes', 'cloud', 'platform', 'engineering', 'modernization', 'mlops', 'ai', 'partnership']
    all_text = soup.get_text()
    
    for keyword in keywords:
        if keyword.lower() in all_text.lower():
            # Find sentences containing the keyword
            sentences = all_text.split('.')
            for sentence in sentences:
                if keyword.lower() in sentence.lower() and len(sentence.strip()) > 30:
                    keyword_content.append(sentence.strip())
    
    results = {
        'main_content': main_content,
        'service_content': service_content,
        'paragraph_content': paragraph_content[:20],  # Limit for readability
        'keyword_content': keyword_content[:10],
        'total_main_chars': len(' '.join(main_content)),
        'total_service_chars': len(' '.join(service_content)),
        'total_paragraph_chars': len(' '.join(paragraph_content)),
        'total_keyword_chars': len(' '.join(keyword_content))
    }
    
    print(f"Main content: {results['total_main_chars']} characters")
    print(f"Service content: {results['total_service_chars']} characters")
    print(f"Paragraph content: {results['total_paragraph_chars']} characters")
    print(f"Keyword content: {results['total_keyword_chars']} characters")
    
    return results

def test_selenium_extraction():
    """Test Selenium extraction with JavaScript execution"""
    url = "https://www.cloudgeometry.com/services"
    
    print("\n🤖 Testing Selenium extraction...")
    
    try:
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            driver.get(url)
            
            # Wait for content to load
            time.sleep(5)
            
            # Get page title
            title = driver.title
            print(f"Page title: {title}")
            
            # Get all visible text
            body = driver.find_element(By.TAG_NAME, "body")
            all_text = body.text
            
            # Look for specific service elements
            service_selectors = [
                "main",
                "[class*='service']",
                "[class*='offering']",
                "[class*='solution']",
                ".content"
            ]
            
            service_texts = []
            for selector in service_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 30:
                            service_texts.append(text)
                except:
                    continue
            
            # Look for partnership/technology mentions
            partnership_keywords = ['aws', 'kubernetes', 'cloud native', 'partnership', 'certified']
            partnership_texts = []
            
            for keyword in partnership_keywords:
                try:
                    elements = driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]")
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 10:
                            partnership_texts.append(text)
                except:
                    continue
            
            results = {
                'title': title,
                'all_text': all_text,
                'service_texts': service_texts[:10],  # Limit for readability
                'partnership_texts': partnership_texts[:10],
                'total_chars': len(all_text),
                'service_chars': len(' '.join(service_texts)),
                'partnership_chars': len(' '.join(partnership_texts))
            }
            
            print(f"Total content: {results['total_chars']} characters")
            print(f"Service content: {results['service_chars']} characters")
            print(f"Partnership content: {results['partnership_chars']} characters")
            
            return results
            
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"Selenium error: {e}")
        return None

def analyze_and_compare(trafilatura_results, beautifulsoup_results, selenium_results):
    """Analyze and compare all extraction methods"""
    print("\n📊 Comparison Analysis:")
    print("=" * 50)
    
    # Extract character counts
    trafilatura_chars = len(trafilatura_results[1] or trafilatura_results[0] or '')
    beautifulsoup_chars = max(
        beautifulsoup_results['total_main_chars'],
        beautifulsoup_results['total_service_chars'],
        beautifulsoup_results['total_paragraph_chars']
    )
    selenium_chars = selenium_results['total_chars'] if selenium_results else 0
    
    methods = [
        ('Trafilatura', trafilatura_chars),
        ('BeautifulSoup', beautifulsoup_chars),
        ('Selenium', selenium_chars)
    ]
    
    methods.sort(key=lambda x: x[1], reverse=True)
    
    print("Content extraction results (by character count):")
    for method, chars in methods:
        print(f"  {method}: {chars:,} characters")
    
    # Calculate improvements
    baseline = trafilatura_chars
    print(f"\nComparison to Trafilatura baseline ({baseline} chars):")
    
    for method, chars in methods:
        if method != 'Trafilatura' and baseline > 0:
            improvement = ((chars - baseline) / baseline) * 100
            print(f"  {method}: {improvement:+.1f}% improvement")
    
    # Recommendations
    print("\n🔧 Recommendations:")
    print("=" * 50)
    
    if methods[0][0] != 'Trafilatura':
        print(f"Switch to {methods[0][0]} for better content extraction")
        print(f"Expected improvement: {((methods[0][1] - baseline) / baseline) * 100:.1f}%")
    
    if selenium_chars > trafilatura_chars * 2:
        print("JavaScript rendering significantly improves extraction")
        print("Consider using Selenium or Crawl4AI for JavaScript-heavy sites")
    
    print("\nNext steps:")
    print("1. Test the recommended method in your production pipeline")
    print("2. Consider implementing a fallback chain")
    print("3. Monitor extraction quality on similar service pages")
    
    return methods

def main():
    """Main execution function"""
    print("🧪 Quick Content Extraction Test")
    print("Testing: https://www.cloudgeometry.com/services")
    print("=" * 60)
    
    # Test all methods
    trafilatura_results = test_trafilatura_extraction()
    beautifulsoup_results = test_beautifulsoup_advanced()
    selenium_results = test_selenium_extraction()
    
    # Analyze results
    comparison = analyze_and_compare(trafilatura_results, beautifulsoup_results, selenium_results)
    
    # Save results
    results = {
        'url': 'https://www.cloudgeometry.com/services',
        'timestamp': time.time(),
        'trafilatura': {
            'basic_chars': len(trafilatura_results[0] or ''),
            'advanced_chars': len(trafilatura_results[1] or ''),
            'content': trafilatura_results[1] or trafilatura_results[0]
        },
        'beautifulsoup': beautifulsoup_results,
        'selenium': selenium_results,
        'comparison': comparison
    }
    
    with open('quick_extraction_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: quick_extraction_results.json")

if __name__ == "__main__":
    main()