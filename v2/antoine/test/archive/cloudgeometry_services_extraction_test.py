#!/usr/bin/env python3
"""
CloudGeometry Services Page Content Extraction Test
==================================================

Tests different content extraction methods on the specific CloudGeometry services page
that Trafilatura failed to extract properly (only 318 chars vs much more content available).
"""

import requests
import time
from bs4 import BeautifulSoup

def test_trafilatura_extraction():
    """Test current Trafilatura approach"""
    print("🧪 Testing Trafilatura Extraction")
    print("-" * 40)
    
    try:
        import trafilatura
        url = "https://www.cloudgeometry.com/services"
        
        start_time = time.time()
        downloaded = trafilatura.fetch_url(url)
        content = trafilatura.extract(downloaded) if downloaded else ""
        extraction_time = time.time() - start_time
        
        content_length = len(content) if content else 0
        
        print(f"📊 Results:")
        print(f"   Content Length: {content_length:,} characters")
        print(f"   Extraction Time: {extraction_time:.2f}s")
        print(f"   Success: {'✅' if content_length > 0 else '❌'}")
        
        if content:
            preview = content[:200] + "..." if len(content) > 200 else content
            print(f"   Preview: {preview}")
        else:
            print("   Preview: [NO CONTENT EXTRACTED]")
            
        return content, content_length, extraction_time
        
    except Exception as e:
        print(f"❌ Trafilatura extraction failed: {e}")
        return "", 0, 0


def test_advanced_trafilatura_extraction():
    """Test Trafilatura with advanced settings"""
    print("\n🔬 Testing Advanced Trafilatura Extraction")
    print("-" * 40)
    
    try:
        import trafilatura
        url = "https://www.cloudgeometry.com/services"
        
        start_time = time.time()
        downloaded = trafilatura.fetch_url(url)
        
        if downloaded:
            # Try with different settings
            content = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=True,
                include_links=False,
                include_images=False,
                favor_precision=False,  # Favor recall over precision
                favor_recall=True
            )
        else:
            content = ""
            
        extraction_time = time.time() - start_time
        content_length = len(content) if content else 0
        
        print(f"📊 Results:")
        print(f"   Content Length: {content_length:,} characters")
        print(f"   Extraction Time: {extraction_time:.2f}s")
        print(f"   Success: {'✅' if content_length > 0 else '❌'}")
        
        if content:
            preview = content[:200] + "..." if len(content) > 200 else content
            print(f"   Preview: {preview}")
        else:
            print("   Preview: [NO CONTENT EXTRACTED]")
            
        return content, content_length, extraction_time
        
    except Exception as e:
        print(f"❌ Advanced Trafilatura extraction failed: {e}")
        return "", 0, 0


def test_beautifulsoup_basic_extraction():
    """Test basic BeautifulSoup extraction"""
    print("\n🔍 Testing BeautifulSoup Basic Extraction")
    print("-" * 40)
    
    try:
        url = "https://www.cloudgeometry.com/services"
        
        start_time = time.time()
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script, style, and navigation elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()
        
        # Extract text from body
        content = soup.get_text(separator=' ', strip=True)
        
        # Clean up extra whitespace
        import re
        content = re.sub(r'\\s+', ' ', content).strip()
        
        extraction_time = time.time() - start_time
        content_length = len(content)
        
        print(f"📊 Results:")
        print(f"   Content Length: {content_length:,} characters")
        print(f"   Extraction Time: {extraction_time:.2f}s")
        print(f"   Success: {'✅' if content_length > 0 else '❌'}")
        
        if content:
            preview = content[:200] + "..." if len(content) > 200 else content
            print(f"   Preview: {preview}")
        else:
            print("   Preview: [NO CONTENT EXTRACTED]")
            
        return content, content_length, extraction_time
        
    except Exception as e:
        print(f"❌ BeautifulSoup basic extraction failed: {e}")
        return "", 0, 0


def test_beautifulsoup_advanced_extraction():
    """Test advanced BeautifulSoup extraction targeting service content"""
    print("\n🎯 Testing BeautifulSoup Advanced Extraction")
    print("-" * 40)
    
    try:
        url = "https://www.cloudgeometry.com/services"
        
        start_time = time.time()
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Try different strategies to find main content
        content_strategies = []
        
        # Strategy 1: Look for main content containers
        main_selectors = [
            'main',
            '[role="main"]',
            '.main-content',
            '.content',
            '.page-content',
            '.services-content',
            '.container'
        ]
        
        for selector in main_selectors:
            elements = soup.select(selector)
            if elements:
                for element in elements:
                    text = element.get_text(separator=' ', strip=True)
                    if len(text) > 500:  # Only consider substantial content
                        content_strategies.append(text)
        
        # Strategy 2: Look for service-specific sections
        service_selectors = [
            '[class*="service"]',
            '[class*="offering"]', 
            '[class*="solution"]',
            '[class*="product"]',
            'section',
            '.section'
        ]
        
        for selector in service_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(separator=' ', strip=True)
                if len(text) > 100:  # Include smaller service descriptions
                    content_strategies.append(text)
        
        # Strategy 3: Find sections with service keywords
        service_keywords = [
            'application modernization', 'platform engineering', 'kubernetes',
            'data engineering', 'mlops', 'cloudops', 'aws', 'azure', 'gcp',
            'cloud migration', 'saas', 'ai', 'generative ai'
        ]
        
        all_sections = soup.find_all(['div', 'section', 'article'])
        for section in all_sections:
            text = section.get_text().lower()
            if any(keyword in text for keyword in service_keywords):
                section_text = section.get_text(separator=' ', strip=True)
                if len(section_text) > 50:
                    content_strategies.append(section_text)
        
        # Combine and deduplicate content
        if content_strategies:
            # Take the longest content block as primary
            content = max(content_strategies, key=len)
            
            # Add any additional unique content
            unique_content = []
            for strategy_content in content_strategies:
                # Check if this content adds significant new information
                if len(strategy_content) > 200 and strategy_content not in content:
                    # Check for significant overlap to avoid duplication
                    words_in_main = set(content.lower().split())
                    words_in_strategy = set(strategy_content.lower().split())
                    overlap = len(words_in_main & words_in_strategy)
                    overlap_ratio = overlap / len(words_in_strategy) if words_in_strategy else 0
                    
                    if overlap_ratio < 0.7:  # Less than 70% overlap means unique content
                        unique_content.append(strategy_content)
            
            # Combine main content with unique additional content
            if unique_content:
                content = content + "\\n\\n" + "\\n\\n".join(unique_content)
        else:
            # Fallback: get all text from body
            content = soup.get_text(separator=' ', strip=True)
        
        # Clean up extra whitespace
        import re
        content = re.sub(r'\\s+', ' ', content).strip()
        
        extraction_time = time.time() - start_time
        content_length = len(content)
        
        print(f"📊 Results:")
        print(f"   Content Length: {content_length:,} characters")
        print(f"   Extraction Time: {extraction_time:.2f}s")
        print(f"   Success: {'✅' if content_length > 0 else '❌'}")
        print(f"   Strategies used: {len(content_strategies)} content blocks found")
        
        if content:
            preview = content[:300] + "..." if len(content) > 300 else content
            print(f"   Preview: {preview}")
        else:
            print("   Preview: [NO CONTENT EXTRACTED]")
            
        return content, content_length, extraction_time
        
    except Exception as e:
        print(f"❌ BeautifulSoup advanced extraction failed: {e}")
        return "", 0, 0


def test_content_keywords():
    """Test if the extracted content contains the expected service keywords"""
    print("\n🔍 Testing Content Keyword Coverage")
    print("-" * 40)
    
    expected_keywords = [
        'AWS', 'Azure', 'GCP', 'Cloud Native Computing Foundation',
        'Application Modernization', 'Platform Engineering',
        'Multi-Platform App Design', 'Multi-Tenancy SaaS',
        'CI/CD', 'Kubernetes Adoption', 'Managed Data Engineering',
        'AI, Data & MLOps', 'Generative AI', 'Managed CloudOps',
        'Professional Services', 'Customer Success Engineering'
    ]
    
    return expected_keywords


def main():
    """Run all extraction tests and compare results"""
    print("🧪 CLOUDGEOMETRY SERVICES PAGE EXTRACTION COMPARISON")
    print("=" * 60)
    print("Testing: https://www.cloudgeometry.com/services")
    print()
    
    # Run all tests
    results = {}
    
    # Test 1: Current Trafilatura
    traf_content, traf_length, traf_time = test_trafilatura_extraction()
    results['trafilatura'] = {'content': traf_content, 'length': traf_length, 'time': traf_time}
    
    # Test 2: Advanced Trafilatura  
    adv_traf_content, adv_traf_length, adv_traf_time = test_advanced_trafilatura_extraction()
    results['trafilatura_advanced'] = {'content': adv_traf_content, 'length': adv_traf_length, 'time': adv_traf_time}
    
    # Test 3: Basic BeautifulSoup
    bs_content, bs_length, bs_time = test_beautifulsoup_basic_extraction()
    results['beautifulsoup_basic'] = {'content': bs_content, 'length': bs_length, 'time': bs_time}
    
    # Test 4: Advanced BeautifulSoup
    adv_bs_content, adv_bs_length, adv_bs_time = test_beautifulsoup_advanced_extraction()
    results['beautifulsoup_advanced'] = {'content': adv_bs_content, 'length': adv_bs_length, 'time': adv_bs_time}
    
    # Summary comparison
    print("\\n📊 EXTRACTION COMPARISON SUMMARY")
    print("=" * 60)
    print(f"{'Method':<25} {'Characters':<12} {'Time':<8} {'Improvement':<12}")
    print("-" * 60)
    
    baseline = traf_length if traf_length > 0 else 1  # Avoid division by zero
    
    for method, data in results.items():
        improvement = f"+{((data['length'] / baseline) - 1) * 100:.0f}%" if data['length'] > baseline else "Baseline"
        print(f"{method:<25} {data['length']:<12,} {data['time']:<8.2f}s {improvement}")
    
    # Find best method
    best_method = max(results.keys(), key=lambda k: results[k]['length'])
    best_length = results[best_method]['length']
    
    print(f"\\n🏆 BEST METHOD: {best_method}")
    print(f"   Content Length: {best_length:,} characters")
    print(f"   Improvement: {((best_length / baseline) - 1) * 100:.0f}% over baseline")
    
    # Test keyword coverage with best method
    if best_length > 0:
        best_content = results[best_method]['content']
        expected_keywords = test_content_keywords()
        
        found_keywords = []
        missing_keywords = []
        
        for keyword in expected_keywords:
            if keyword.lower() in best_content.lower():
                found_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)
        
        print(f"\\n🎯 KEYWORD COVERAGE ({best_method}):")
        print(f"   Found: {len(found_keywords)}/{len(expected_keywords)} keywords")
        print(f"   Coverage: {(len(found_keywords)/len(expected_keywords))*100:.1f}%")
        
        if found_keywords:
            print(f"   ✅ Found: {', '.join(found_keywords[:5])}{'...' if len(found_keywords) > 5 else ''}")
        if missing_keywords:
            print(f"   ❌ Missing: {', '.join(missing_keywords[:3])}{'...' if len(missing_keywords) > 3 else ''}")
    
    # Save best result to file
    if best_length > 0:
        filename = f'cloudgeometry_services_best_extraction.txt'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"CLOUDGEOMETRY SERVICES PAGE - BEST EXTRACTION\\n")
            f.write(f"Method: {best_method}\\n")
            f.write(f"Content Length: {best_length:,} characters\\n")
            f.write(f"Extraction Time: {results[best_method]['time']:.2f}s\\n")
            f.write("=" * 60 + "\\n\\n")
            f.write(results[best_method]['content'])
        
        print(f"\\n💾 Best extraction saved to: {filename}")
    
    print(f"\\n✅ Test completed! Best method: {best_method} with {best_length:,} characters")


if __name__ == "__main__":
    main()