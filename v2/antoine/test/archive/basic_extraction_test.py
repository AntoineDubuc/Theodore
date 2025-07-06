#!/usr/bin/env python3
"""
Basic Content Extraction Test for CloudGeometry
Using only built-in libraries: requests, BeautifulSoup, and trafilatura
"""

import requests
import time
from bs4 import BeautifulSoup
import trafilatura
import json
import re

def test_trafilatura_basic():
    """Test basic Trafilatura extraction"""
    url = "https://www.cloudgeometry.com/services"
    
    print("🔍 Testing Trafilatura (basic)...")
    
    # Basic extraction
    basic_content = trafilatura.extract(url)
    print(f"Basic extraction: {len(basic_content or '')} characters")
    
    return basic_content

def test_trafilatura_advanced():
    """Test advanced Trafilatura extraction with all options"""
    url = "https://www.cloudgeometry.com/services"
    
    print("\n🔍 Testing Trafilatura (advanced)...")
    
    # Download content first
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        print("Failed to download content")
        return ""
    
    # Try different strategies
    strategies = [
        {
            'name': 'Favor Recall',
            'params': {
                'include_comments': True,
                'include_tables': True,
                'include_links': True,
                'include_images': True,
                'no_fallback': False,
                'favor_precision': False,
                'favor_recall': True
            }
        },
        {
            'name': 'Include Formatting',
            'params': {
                'include_formatting': True,
                'include_links': True,
                'include_tables': True,
                'no_fallback': False
            }
        },
        {
            'name': 'No Fallback',
            'params': {
                'no_fallback': True,
                'include_tables': True
            }
        }
    ]
    
    best_content = ""
    best_strategy = ""
    
    for strategy in strategies:
        try:
            content = trafilatura.extract(downloaded, **strategy['params'])
            char_count = len(content or '')
            print(f"  {strategy['name']}: {char_count} characters")
            
            if char_count > len(best_content):
                best_content = content or ""
                best_strategy = strategy['name']
                
        except Exception as e:
            print(f"  {strategy['name']}: Error - {e}")
    
    print(f"Best strategy: {best_strategy} with {len(best_content)} characters")
    return best_content

def test_beautifulsoup_basic():
    """Test basic BeautifulSoup extraction"""
    url = "https://www.cloudgeometry.com/services"
    
    print("\n🍲 Testing BeautifulSoup (basic)...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Basic text extraction
    basic_text = soup.get_text()
    print(f"Basic text: {len(basic_text)} characters")
    
    return basic_text

def test_beautifulsoup_advanced():
    """Test advanced BeautifulSoup extraction with service-specific strategies"""
    url = "https://www.cloudgeometry.com/services"
    
    print("\n🍲 Testing BeautifulSoup (advanced)...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Remove unwanted elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript']):
        element.decompose()
    
    strategies = []
    
    # Strategy 1: Main content containers
    main_containers = soup.find_all(['main', 'article', 'section'])
    main_content = []
    for container in main_containers:
        text = container.get_text(separator=' ', strip=True)
        if len(text) > 100:
            main_content.append(text)
    
    strategies.append(('Main Containers', main_content))
    
    # Strategy 2: Service-specific selectors
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
    
    strategies.append(('Service Selectors', service_content))
    
    # Strategy 3: Meaningful paragraphs and headings
    content_elements = soup.find_all(['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    paragraph_content = []
    for element in content_elements:
        text = element.get_text(strip=True)
        if len(text) > 20:
            paragraph_content.append(text)
    
    strategies.append(('Paragraphs & Headings', paragraph_content))
    
    # Strategy 4: Keyword-based extraction
    keywords = ['aws', 'kubernetes', 'cloud', 'platform', 'engineering', 'modernization', 'mlops', 'ai', 'partnership']
    all_text = soup.get_text()
    
    keyword_content = []
    sentences = re.split(r'[.!?]+', all_text)
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 30:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in keywords):
                keyword_content.append(sentence)
    
    strategies.append(('Keyword Sentences', keyword_content))
    
    # Print results for each strategy
    for name, content_list in strategies:
        char_count = len(' '.join(content_list))
        print(f"  {name}: {char_count} characters ({len(content_list)} items)")
    
    # Combine all strategies
    all_content = []
    for _, content_list in strategies:
        all_content.extend(content_list)
    
    # Remove duplicates while preserving order
    unique_content = []
    seen = set()
    for content in all_content:
        if content not in seen:
            unique_content.append(content)
            seen.add(content)
    
    final_content = '\n'.join(unique_content)
    print(f"Combined unique content: {len(final_content)} characters")
    
    return final_content

def compare_methods():
    """Compare all extraction methods"""
    print("🧪 CloudGeometry Content Extraction Test")
    print("URL: https://www.cloudgeometry.com/services")
    print("=" * 60)
    
    # Test all methods
    results = {}
    
    # Trafilatura basic
    try:
        trafilatura_basic = test_trafilatura_basic()
        results['trafilatura_basic'] = len(trafilatura_basic or '')
    except Exception as e:
        print(f"Trafilatura basic failed: {e}")
        results['trafilatura_basic'] = 0
    
    # Trafilatura advanced
    try:
        trafilatura_advanced = test_trafilatura_advanced()
        results['trafilatura_advanced'] = len(trafilatura_advanced or '')
    except Exception as e:
        print(f"Trafilatura advanced failed: {e}")
        results['trafilatura_advanced'] = 0
    
    # BeautifulSoup basic
    try:
        bs_basic = test_beautifulsoup_basic()
        results['beautifulsoup_basic'] = len(bs_basic or '')
    except Exception as e:
        print(f"BeautifulSoup basic failed: {e}")
        results['beautifulsoup_basic'] = 0
    
    # BeautifulSoup advanced
    try:
        bs_advanced = test_beautifulsoup_advanced()
        results['beautifulsoup_advanced'] = len(bs_advanced or '')
    except Exception as e:
        print(f"BeautifulSoup advanced failed: {e}")
        results['beautifulsoup_advanced'] = 0
    
    # Analysis
    print("\n📊 Results Summary:")
    print("=" * 60)
    
    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    
    for method, char_count in sorted_results:
        print(f"{method}: {char_count:,} characters")
    
    # Calculate improvements
    baseline = results.get('trafilatura_basic', 0)
    if baseline > 0:
        print(f"\nComparison to Trafilatura baseline ({baseline} chars):")
        for method, char_count in sorted_results:
            if method != 'trafilatura_basic':
                improvement = ((char_count - baseline) / baseline) * 100
                print(f"  {method}: {improvement:+.1f}% improvement")
    
    # Recommendations
    print("\n🔧 Recommendations:")
    print("=" * 60)
    
    if sorted_results:
        best_method, best_count = sorted_results[0]
        print(f"Best method: {best_method} ({best_count:,} characters)")
        
        if best_count > baseline * 1.5:
            print(f"✅ Significant improvement over Trafilatura baseline")
            print(f"Recommendation: Switch to {best_method}")
        else:
            print(f"⚠️  Modest improvement over Trafilatura baseline")
            print(f"Consider testing JavaScript-enabled extraction (Selenium/Crawl4AI)")
    
    # Save results
    output = {
        'url': 'https://www.cloudgeometry.com/services',
        'timestamp': time.time(),
        'results': results,
        'ranking': sorted_results,
        'baseline': baseline
    }
    
    with open('basic_extraction_results.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Results saved to: basic_extraction_results.json")
    
    return results

if __name__ == "__main__":
    compare_methods()