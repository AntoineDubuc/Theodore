#!/usr/bin/env python3
"""
Test Trafilatura vs Current Crawler for Clean Content Extraction
================================================================

Compares Trafilatura (boilerplate remover) against our current BeautifulSoup approach
to see which gives cleaner, more unique content per page.
"""

import os
import time
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_trafilatura_extraction():
    """Test Trafilatura extraction on Digital Remedy pages"""
    
    print('🧪 TESTING TRAFILATURA VS CURRENT CRAWLER')
    print('=' * 60)
    
    # Test URLs - pages that should have very different content
    test_urls = [
        "https://www.digitalremedy.com/about",
        "https://www.digitalremedy.com/careers", 
        "https://www.digitalremedy.com/contact-us",
        "https://www.digitalremedy.com/capabilities"
    ]
    
    print(f'🔍 Testing {len(test_urls)} pages')
    print(f'   URLs: {[url.split("/")[-1] for url in test_urls]}')
    
    # Test 1: Trafilatura extraction
    print(f'\n📚 METHOD 1: TRAFILATURA EXTRACTION')
    print('-' * 50)
    
    try:
        import trafilatura
        trafilatura_available = True
        print('✅ Trafilatura imported successfully')
    except ImportError:
        print('❌ Trafilatura not available - installing...')
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'trafilatura'])
        import trafilatura
        trafilatura_available = True
        print('✅ Trafilatura installed and imported')
    
    trafilatura_results = []
    
    for i, url in enumerate(test_urls, 1):
        print(f'🔍 [{i}/{len(test_urls)}] Extracting: {url}')
        start_time = time.time()
        
        try:
            # Download and extract with Trafilatura
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                # Extract main content (removes boilerplate by default)
                content = trafilatura.extract(downloaded)
                if content:
                    content = content.strip()
                    extract_time = time.time() - start_time
                    trafilatura_results.append({
                        'url': url,
                        'content': content,
                        'length': len(content),
                        'time': extract_time,
                        'success': True,
                        'error': None
                    })
                    print(f'   ✅ Success: {len(content):,} chars in {extract_time:.2f}s')
                else:
                    extract_time = time.time() - start_time
                    trafilatura_results.append({
                        'url': url,
                        'content': '',
                        'length': 0,
                        'time': extract_time,
                        'success': False,
                        'error': 'No content extracted'
                    })
                    print(f'   ❌ Failed: No content extracted')
            else:
                extract_time = time.time() - start_time
                trafilatura_results.append({
                    'url': url,
                    'content': '',
                    'length': 0,
                    'time': extract_time,
                    'success': False,
                    'error': 'Failed to download'
                })
                print(f'   ❌ Failed: Download failed')
                
        except Exception as e:
            extract_time = time.time() - start_time
            trafilatura_results.append({
                'url': url,
                'content': '',
                'length': 0,
                'time': extract_time,
                'success': False,
                'error': str(e)
            })
            print(f'   ❌ Error: {e}')
    
    # Test 2: Current Crawler (for comparison)
    print(f'\\n🕷️  METHOD 2: CURRENT CRAWLER EXTRACTION')
    print('-' * 50)
    
    try:
        from crawler import crawl_selected_pages_sync
        crawler_available = True
        print('✅ Current crawler imported successfully')
        
        # Extract just the paths from URLs
        test_paths = [url.replace("https://www.digitalremedy.com", "") for url in test_urls]
        
        crawler_result = crawl_selected_pages_sync(
            base_url="https://www.digitalremedy.com",
            selected_paths=test_paths,
            timeout_seconds=30,
            max_content_per_page=5000,
            max_concurrent=2
        )
        
        print(f'✅ Crawler completed: {crawler_result.successful_pages}/{crawler_result.total_pages} pages')
        crawler_results = [r for r in crawler_result.page_results if r.success]
        
    except Exception as e:
        print(f'❌ Current crawler failed: {e}')
        crawler_available = False
        crawler_results = []
    
    # Analysis and Comparison
    print(f'\\n📊 COMPARISON ANALYSIS')
    print('=' * 60)
    
    # Content length comparison
    if trafilatura_results and crawler_results:
        print(f'\\n📏 CONTENT LENGTH COMPARISON:')
        print(f'{"Page":<20} {"Trafilatura":<12} {"Crawler":<12} {"Difference":<12}')
        print('-' * 60)
        
        for i, (traf_result, crawl_result) in enumerate(zip(trafilatura_results, crawler_results)):
            page_name = traf_result['url'].split('/')[-1] or 'home'
            traf_len = traf_result['length']
            crawl_len = crawl_result.content_length
            diff = abs(traf_len - crawl_len)
            print(f'{page_name:<20} {traf_len:<12,} {crawl_len:<12,} {diff:<12,}')
    
    # Content uniqueness analysis
    print(f'\\n🔬 CONTENT UNIQUENESS ANALYSIS:')
    
    if len(trafilatura_results) >= 2:
        print(f'\\nTrafilatura Results:')
        traf_successful = [r for r in trafilatura_results if r['success']]
        for i, result in enumerate(traf_successful, 1):
            page_name = result['url'].split('/')[-1] or 'home'
            preview = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']
            print(f'  {i}. {page_name}: {result["length"]:,} chars')
            print(f'     Preview: {preview}')
            print()
        
        # Check similarity between first two pages
        if len(traf_successful) >= 2:
            words1 = set(traf_successful[0]['content'].lower().split()[:50])
            words2 = set(traf_successful[1]['content'].lower().split()[:50])
            overlap = len(words1 & words2)
            similarity = overlap / min(len(words1), len(words2)) if words1 and words2 else 0
            print(f'     Similarity between pages 1&2: {similarity:.1%} overlap')
    
    if crawler_results:
        print(f'\\nCrawler Results:')
        for i, result in enumerate(crawler_results, 1):
            page_name = result.url.split('/')[-1] or 'home'
            preview = result.content[:100] + "..." if len(result.content) > 100 else result.content
            print(f'  {i}. {page_name}: {result.content_length:,} chars')
            print(f'     Preview: {preview}')
            print()
    
    # Save detailed results
    output_file = 'test/trafilatura_vs_crawler_comparison.txt'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('TRAFILATURA VS CRAWLER COMPARISON\\n')
        f.write('=' * 60 + '\\n\\n')
        
        # Trafilatura results
        f.write('📚 TRAFILATURA EXTRACTION RESULTS:\\n')
        f.write('-' * 50 + '\\n\\n')
        
        for i, result in enumerate(trafilatura_results, 1):
            page_name = result['url'].split('/')[-1] or 'home'
            f.write(f'PAGE {i}: {page_name.upper()}\\n')
            f.write(f'URL: {result["url"]}\\n')
            f.write(f'Success: {"✅" if result["success"] else "❌"}\\n')
            f.write(f'Content Length: {result["length"]:,} characters\\n')
            f.write(f'Extraction Time: {result["time"]:.2f} seconds\\n')
            if result['error']:
                f.write(f'Error: {result["error"]}\\n')
            f.write('\\nContent:\\n')
            f.write('-' * 40 + '\\n')
            f.write(result['content'] if result['content'] else '[NO CONTENT]')
            f.write('\\n\\n' + '=' * 60 + '\\n\\n')
        
        # Crawler results
        if crawler_results:
            f.write('🕷️  CURRENT CRAWLER EXTRACTION RESULTS:\\n')
            f.write('-' * 50 + '\\n\\n')
            
            for i, result in enumerate(crawler_results, 1):
                page_name = result.url.split('/')[-1] or 'home'
                f.write(f'PAGE {i}: {page_name.upper()}\\n')
                f.write(f'URL: {result.url}\\n')
                f.write(f'Success: {"✅" if result.success else "❌"}\\n')
                f.write(f'Content Length: {result.content_length:,} characters\\n')
                f.write(f'Extraction Time: {result.crawl_time:.2f} seconds\\n')
                if result.error:
                    f.write(f'Error: {result.error}\\n')
                f.write('\\nContent:\\n')
                f.write('-' * 40 + '\\n')
                f.write(result.content if result.content else '[NO CONTENT]')
                f.write('\\n\\n' + '=' * 60 + '\\n\\n')
        
        f.write('END OF COMPARISON REPORT\\n')
    
    print(f'\\n💾 Detailed comparison saved to: {output_file}')
    print(f'📁 File size: {os.path.getsize(output_file):,} bytes')
    
    # Summary and recommendation
    print(f'\\n🎯 SUMMARY & RECOMMENDATION:')
    print('-' * 40)
    
    successful_traf = len([r for r in trafilatura_results if r['success']])
    successful_crawl = len(crawler_results) if crawler_results else 0
    
    print(f'   Trafilatura: {successful_traf}/{len(test_urls)} pages successful')
    print(f'   Current Crawler: {successful_crawl}/{len(test_urls)} pages successful')
    
    if successful_traf > successful_crawl:
        print(f'   🏆 WINNER: Trafilatura (more successful extractions)')
    elif successful_crawl > successful_traf:
        print(f'   🏆 WINNER: Current Crawler (more successful extractions)')
    else:
        print(f'   🤝 TIE: Both methods equally successful')
        
        # Compare content quality if tied
        if trafilatura_results and crawler_results:
            avg_traf_len = sum(r['length'] for r in trafilatura_results) / len(trafilatura_results)
            avg_crawl_len = sum(r.content_length for r in crawler_results) / len(crawler_results)
            
            if avg_traf_len > avg_crawl_len * 1.2:
                print(f'   💡 QUALITY: Trafilatura extracts more content ({avg_traf_len:.0f} vs {avg_crawl_len:.0f} avg chars)')
            elif avg_crawl_len > avg_traf_len * 1.2:
                print(f'   💡 QUALITY: Current Crawler extracts more content ({avg_crawl_len:.0f} vs {avg_traf_len:.0f} avg chars)')
            else:
                print(f'   💡 QUALITY: Similar content extraction volume')
    
    return trafilatura_results, crawler_results


if __name__ == "__main__":
    test_trafilatura_extraction()