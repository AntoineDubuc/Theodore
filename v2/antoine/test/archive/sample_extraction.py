#!/usr/bin/env python3
"""
Sample extraction to show what content is actually captured
"""

import requests
from bs4 import BeautifulSoup
import trafilatura
import re

def show_extraction_sample():
    """Show actual extracted content samples"""
    url = "https://www.cloudgeometry.com/services"
    
    print("📄 Sample Content Extraction from CloudGeometry")
    print("=" * 60)
    
    # Advanced BeautifulSoup extraction
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Remove unwanted elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript']):
        element.decompose()
    
    # Extract service-specific content
    service_selectors = [
        '[class*="service"]',
        '[class*="offering"]',
        '[class*="solution"]',
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
    
    print("\n🎯 Service-Specific Content Found:")
    print("-" * 40)
    
    # Show first few service items
    for i, content in enumerate(service_content[:10]):
        print(f"\n{i+1}. {content[:200]}...")
    
    # Look for specific partnerships and technologies
    keywords = ['aws', 'kubernetes', 'cloud native', 'partnership', 'cncf', 'modernization', 'mlops', 'ai']
    all_text = soup.get_text()
    
    keyword_matches = []
    sentences = re.split(r'[.!?]+', all_text)
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 30:
            sentence_lower = sentence.lower()
            for keyword in keywords:
                if keyword in sentence_lower:
                    keyword_matches.append((keyword, sentence))
                    break
    
    print(f"\n🔍 Keyword Matches Found ({len(keyword_matches)} total):")
    print("-" * 40)
    
    # Group by keyword
    keyword_groups = {}
    for keyword, sentence in keyword_matches:
        if keyword not in keyword_groups:
            keyword_groups[keyword] = []
        keyword_groups[keyword].append(sentence)
    
    for keyword, sentences in keyword_groups.items():
        print(f"\n📌 {keyword.upper()} ({len(sentences)} mentions):")
        for sentence in sentences[:3]:  # Show first 3 matches
            print(f"  • {sentence}")
    
    # Compare with Trafilatura
    print(f"\n\n🔍 Trafilatura Advanced Extraction:")
    print("-" * 40)
    
    downloaded = trafilatura.fetch_url(url)
    if downloaded:
        trafilatura_content = trafilatura.extract(
            downloaded,
            include_comments=True,
            include_tables=True,
            include_links=True,
            include_images=True,
            no_fallback=False,
            favor_recall=True
        )
        
        if trafilatura_content:
            print(f"Length: {len(trafilatura_content)} characters")
            print(f"Content preview:\n{trafilatura_content[:500]}...")
        else:
            print("No content extracted")
    
    # Statistics
    print(f"\n\n📊 Extraction Statistics:")
    print("-" * 40)
    print(f"Total service content items: {len(service_content)}")
    print(f"Total keyword matches: {len(keyword_matches)}")
    print(f"BeautifulSoup total chars: {len(' '.join(service_content))}")
    print(f"Trafilatura chars: {len(trafilatura_content) if trafilatura_content else 0}")
    
    improvement = len(' '.join(service_content)) / max(len(trafilatura_content) if trafilatura_content else 1, 1)
    print(f"Improvement ratio: {improvement:.1f}x")

if __name__ == "__main__":
    show_extraction_sample()