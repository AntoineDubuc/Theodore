#!/usr/bin/env python3
"""
Social Media Link Extraction Test Suite
=======================================

Tests for extracting social media links from website headers and footers.
This test validates the approach before implementing it in the main crawler.

Test Cases:
1. Header social media links
2. Footer social media links  
3. Mixed header + footer links
4. No social media links (edge case)
5. Invalid/non-social links (validation)
6. Link deduplication
7. Platform detection accuracy

Usage:
    python test_social_media_extraction.py
"""

import unittest
import sys
import os
from typing import Dict, List, Tuple

# Add parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import BeautifulSoup for HTML parsing
try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    print("❌ BeautifulSoup not available - installing...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'beautifulsoup4'])
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True


class SocialMediaExtractor:
    """
    Social media link extractor for testing.
    This will be integrated into the main crawler after validation.
    """
    
    # Known social media domains for validation
    SOCIAL_MEDIA_DOMAINS = {
        'facebook.com': 'facebook',
        'fb.com': 'facebook',
        'twitter.com': 'twitter',
        'x.com': 'twitter', 
        'linkedin.com': 'linkedin',
        'instagram.com': 'instagram',
        'youtube.com': 'youtube',
        'tiktok.com': 'tiktok',
        'pinterest.com': 'pinterest',
        'snapchat.com': 'snapchat',
        'reddit.com': 'reddit',
        'github.com': 'github',
        'discord.com': 'discord',
        'telegram.org': 'telegram',
        'whatsapp.com': 'whatsapp'
    }
    
    # CSS selectors for finding social media links
    SOCIAL_MEDIA_SELECTORS = [
        # Header selectors
        'header a[href*="facebook"]', 'header a[href*="twitter"]', 'header a[href*="linkedin"]',
        'header a[href*="instagram"]', 'header a[href*="youtube"]', 'header a[href*="github"]',
        
        # Footer selectors  
        'footer a[href*="facebook"]', 'footer a[href*="twitter"]', 'footer a[href*="linkedin"]',
        'footer a[href*="instagram"]', 'footer a[href*="youtube"]', 'footer a[href*="github"]',
        
        # Generic social link containers
        '.social-links a', '.social-media a', '.social a',
        '[class*="social"] a', '[id*="social"] a',
        
        # Common social icon patterns
        'a[class*="facebook"]', 'a[class*="twitter"]', 'a[class*="linkedin"]',
        'a[class*="instagram"]', 'a[class*="youtube"]', 'a[class*="github"]',
    ]
    
    def extract_social_media_links(self, html_content: str) -> Dict[str, str]:
        """
        Extract social media links from HTML content.
        
        Args:
            html_content: Raw HTML content to parse
            
        Returns:
            Dict mapping platform names to URLs
        """
        if not html_content:
            return {}
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove consent popup elements that can interfere with extraction
        self._remove_consent_popups(soup)
        
        social_links = {}
        
        # Method 1: Use CSS selectors for targeted extraction
        for selector in self.SOCIAL_MEDIA_SELECTORS:
            try:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href', '')
                    if href:
                        platform = self._identify_platform(href)
                        if platform:
                            social_links[platform] = href
            except Exception:
                continue  # Skip invalid selectors
        
        # Method 2: Scan all links in header/footer for social media domains
        for section in ['header', 'footer']:
            section_element = soup.find(section)
            if section_element:
                links = section_element.find_all('a', href=True)
                for link in links:
                    href = link['href']
                    platform = self._identify_platform(href)
                    if platform:
                        social_links[platform] = href
        
        # Method 3: Look for links with social media domain patterns anywhere
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link['href']
            platform = self._identify_platform(href)
            if platform and platform not in social_links:
                # Only add if not already found (avoid duplicates)
                social_links[platform] = href
        
        return social_links
    
    def _identify_platform(self, url: str) -> str:
        """
        Identify social media platform from URL.
        
        Args:
            url: URL to analyze
            
        Returns:
            Platform name if identified, empty string otherwise
        """
        if not url:
            return ""
        
        url_lower = url.lower()
        
        # Check each known domain
        for domain, platform in self.SOCIAL_MEDIA_DOMAINS.items():
            if domain in url_lower:
                # Additional validation - ensure it's not a false positive
                if self._is_valid_social_url(url_lower, domain):
                    return platform
        
        return ""
    
    def _is_valid_social_url(self, url: str, domain: str) -> bool:
        """
        Additional validation to avoid false positives.
        
        Args:
            url: URL to validate
            domain: Expected domain
            
        Returns:
            True if URL appears to be a valid social media link
        """
        # Must contain the domain
        if domain not in url:
            return False
        
        # Exclude obvious false positives
        false_positive_patterns = [
            'share', 'button', 'widget', 'embed', 'api', 'developer',
            'help', 'support', 'docs', 'blog.facebook', 'developers.facebook'
        ]
        
        for pattern in false_positive_patterns:
            if pattern in url:
                return False
        
        # Must look like a profile/page URL
        valid_patterns = [
            f'{domain}/', f'{domain}/company/', f'{domain}/pages/',
            f'{domain}/in/', f'{domain}/channel/', f'{domain}/user/'
        ]
        
        return any(pattern in url for pattern in valid_patterns) or url.count('/') <= 4
    
    def _remove_consent_popups(self, soup: BeautifulSoup) -> None:
        """
        Remove consent popup elements that can interfere with social media extraction.
        
        Args:
            soup: BeautifulSoup object to modify in-place
        """
        # CSS selectors for consent popup elements
        consent_selectors = [
            # Class-based selectors
            '[class*="consent"]', '[class*="cookie"]', '[class*="privacy"]', 
            '[class*="gdpr"]', '[class*="popup"]', '[class*="overlay"]',
            '[class*="modal"]', '[class*="banner"]', '[class*="notice"]',
            
            # ID-based selectors
            '[id*="consent"]', '[id*="cookie"]', '[id*="privacy"]',
            '[id*="gdpr"]', '[id*="popup"]', '[id*="overlay"]',
            '[id*="modal"]', '[id*="banner"]', '[id*="notice"]',
            
            # Common consent management platform selectors
            '[class*="cmplz"]',  # Complianz
            '[class*="cookiebot"]',  # Cookiebot
            '[class*="onetrust"]',  # OneTrust
            '[class*="trustarc"]',  # TrustArc
            '[class*="iubenda"]',  # Iubenda
            '[class*="cookiehub"]',  # CookieHub
            '[class*="termly"]',  # Termly
            '[class*="usercentrics"]',  # Usercentrics
            
            # Generic overlay/modal patterns
            '.overlay', '.modal', '.popup', '.banner', '.notice',
            '.cookie-notice', '.cookie-banner', '.privacy-notice',
            '.gdpr-notice', '.consent-banner', '.consent-modal'
        ]
        
        removed_count = 0
        for selector in consent_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    element.decompose()
                    removed_count += 1
            except Exception:
                # Skip invalid selectors
                continue
        
        # Also remove elements with consent-related data attributes
        consent_data_attrs = [
            'data-consent', 'data-cookie', 'data-privacy', 'data-gdpr',
            'data-popup', 'data-modal', 'data-banner', 'data-notice'
        ]
        
        for attr in consent_data_attrs:
            try:
                elements = soup.find_all(attrs={attr: True})
                for element in elements:
                    element.decompose()
                    removed_count += 1
            except Exception:
                continue


class TestSocialMediaExtraction(unittest.TestCase):
    """Test suite for social media link extraction"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor = SocialMediaExtractor()
    
    def test_extract_header_social_links(self):
        """Test extraction of social media links from header"""
        html = """
        <html>
            <head><title>Test Company</title></head>
            <body>
                <header>
                    <nav>
                        <a href="https://facebook.com/testcompany">Facebook</a>
                        <a href="https://twitter.com/testcompany">Twitter</a>
                        <a href="https://linkedin.com/company/testcompany">LinkedIn</a>
                    </nav>
                </header>
                <main>
                    <h1>Welcome to Test Company</h1>
                </main>
            </body>
        </html>
        """
        
        result = self.extractor.extract_social_media_links(html)
        
        self.assertIn('facebook', result)
        self.assertIn('twitter', result) 
        self.assertIn('linkedin', result)
        self.assertEqual(result['facebook'], 'https://facebook.com/testcompany')
        self.assertEqual(result['twitter'], 'https://twitter.com/testcompany')
        self.assertEqual(result['linkedin'], 'https://linkedin.com/company/testcompany')
    
    def test_extract_footer_social_links(self):
        """Test extraction of social media links from footer"""
        html = """
        <html>
            <body>
                <main>
                    <h1>Company Content</h1>
                </main>
                <footer>
                    <div class="social-links">
                        <a href="https://instagram.com/testcompany">Instagram</a>
                        <a href="https://youtube.com/channel/testcompany">YouTube</a>
                        <a href="https://github.com/testcompany">GitHub</a>
                    </div>
                    <p>&copy; 2025 Test Company</p>
                </footer>
            </body>
        </html>
        """
        
        result = self.extractor.extract_social_media_links(html)
        
        self.assertIn('instagram', result)
        self.assertIn('youtube', result)
        self.assertIn('github', result)
        self.assertEqual(result['instagram'], 'https://instagram.com/testcompany')
        self.assertEqual(result['youtube'], 'https://youtube.com/channel/testcompany')
        self.assertEqual(result['github'], 'https://github.com/testcompany')
    
    def test_extract_mixed_header_footer_links(self):
        """Test extraction from both header and footer"""
        html = """
        <html>
            <body>
                <header>
                    <a href="https://facebook.com/company">Facebook</a>
                    <a href="https://twitter.com/company">Follow Us</a>
                </header>
                <main>
                    <h1>Content</h1>
                </main>
                <footer>
                    <div class="social-media">
                        <a href="https://linkedin.com/company/testco">LinkedIn</a>
                        <a href="https://instagram.com/testco">Instagram</a>
                    </div>
                </footer>
            </body>
        </html>
        """
        
        result = self.extractor.extract_social_media_links(html)
        
        # Should find all 4 platforms
        self.assertEqual(len(result), 4)
        self.assertIn('facebook', result)
        self.assertIn('twitter', result)
        self.assertIn('linkedin', result)  
        self.assertIn('instagram', result)
    
    def test_no_social_links(self):
        """Test handling of pages with no social media links"""
        html = """
        <html>
            <body>
                <header>
                    <nav>
                        <a href="/about">About</a>
                        <a href="/contact">Contact</a>
                    </nav>
                </header>
                <main>
                    <h1>No Social Media Here</h1>
                    <a href="https://example.com">External Link</a>
                </main>
                <footer>
                    <p>Contact: info@company.com</p>
                </footer>
            </body>
        </html>
        """
        
        result = self.extractor.extract_social_media_links(html)
        
        self.assertEqual(len(result), 0)
        self.assertEqual(result, {})
    
    def test_social_link_validation(self):
        """Test validation of social media links vs false positives"""
        html = """
        <html>
            <body>
                <main>
                    <!-- Valid social links -->
                    <a href="https://facebook.com/realcompany">Real Facebook</a>
                    <a href="https://twitter.com/realcompany">Real Twitter</a>
                    
                    <!-- False positives to exclude -->
                    <a href="https://developers.facebook.com/docs">Facebook Docs</a>
                    <a href="https://help.twitter.com/support">Twitter Support</a>
                    <a href="https://business.facebook.com/share/widget">Share Widget</a>
                    
                    <!-- Edge cases -->
                    <a href="https://facebook.com/">Facebook Home</a>
                    <a href="https://linkedin.com/in/person">LinkedIn Profile</a>
                </main>
            </body>
        </html>
        """
        
        result = self.extractor.extract_social_media_links(html)
        
        # Should find valid links but exclude false positives
        self.assertIn('facebook', result)
        self.assertIn('twitter', result) 
        self.assertIn('linkedin', result)
        
        # Verify correct URLs are extracted (not the false positives)
        self.assertEqual(result['facebook'], 'https://facebook.com/realcompany')
        self.assertEqual(result['twitter'], 'https://twitter.com/realcompany')
        self.assertEqual(result['linkedin'], 'https://linkedin.com/in/person')
    
    def test_link_deduplication(self):
        """Test that duplicate links are handled correctly"""
        html = """
        <html>
            <body>
                <header>
                    <a href="https://facebook.com/company">Facebook</a>
                </header>
                <main>
                    <a href="https://facebook.com/company">Like us on Facebook</a>
                </main>
                <footer>
                    <div class="social">
                        <a href="https://facebook.com/company">Facebook</a>
                        <a href="https://twitter.com/company">Twitter</a>
                    </div>
                </footer>
            </body>
        </html>
        """
        
        result = self.extractor.extract_social_media_links(html)
        
        # Should only have one entry per platform despite duplicates
        self.assertEqual(len(result), 2)
        self.assertIn('facebook', result)
        self.assertIn('twitter', result)
        self.assertEqual(result['facebook'], 'https://facebook.com/company')
    
    def test_platform_detection_accuracy(self):
        """Test accuracy of platform detection for various URL formats"""
        test_cases = [
            ('https://facebook.com/company', 'facebook'),
            ('https://www.facebook.com/pages/company/123', 'facebook'),
            ('https://fb.com/company', 'facebook'),
            ('https://twitter.com/company', 'twitter'),
            ('https://x.com/company', 'twitter'),
            ('https://linkedin.com/company/company-name', 'linkedin'),
            ('https://www.linkedin.com/in/person', 'linkedin'),
            ('https://instagram.com/company', 'instagram'),
            ('https://youtube.com/channel/company', 'youtube'),
            ('https://github.com/company', 'github'),
            ('https://example.com/notasocial', ''),  # Should not match
        ]
        
        for url, expected_platform in test_cases:
            with self.subTest(url=url):
                detected_platform = self.extractor._identify_platform(url)
                self.assertEqual(detected_platform, expected_platform, 
                               f"Failed for URL: {url}")
    
    def test_empty_and_invalid_input(self):
        """Test handling of empty or invalid HTML input"""
        test_cases = [
            "",  # Empty string
            None,  # None input
            "<html></html>",  # Minimal HTML
            "Not HTML at all",  # Invalid HTML
            "<html><body><p>No links here</p></body></html>",  # No links
        ]
        
        for html_input in test_cases:
            with self.subTest(html=html_input):
                try:
                    result = self.extractor.extract_social_media_links(html_input) 
                    self.assertIsInstance(result, dict)
                    # Should return empty dict for no social links
                    if html_input in ["", None]:
                        self.assertEqual(len(result), 0)
                except Exception as e:
                    self.fail(f"Should handle invalid input gracefully, got: {e}")
    
    def test_consent_popup_removal(self):
        """Test that consent popups are properly removed before extraction"""
        html = """
        <html>
            <body>
                <header>
                    <a href="https://facebook.com/company">Facebook</a>
                    <a href="https://twitter.com/company">Twitter</a>
                </header>
                
                <!-- Consent popup that could interfere -->
                <div class="cmplz-consent-overlay cmplz-modal" id="cmplz-consent-modal">
                    <div class="cmplz-consent-content">
                        <div class="cmplz-consent-banner">
                            <p>This website uses cookies</p>
                            <button class="cmplz-btn cmplz-accept">Accept</button>
                            <button class="cmplz-btn cmplz-deny">Deny</button>
                        </div>
                    </div>
                </div>
                
                <div class="cookie-notice privacy-notice" data-consent="true">
                    <p>We use cookies to improve your experience</p>
                    <button class="accept-cookies">Accept All</button>
                </div>
                
                <footer>
                    <div class="social-links">
                        <a href="https://linkedin.com/company/testco">LinkedIn</a>
                        <a href="https://instagram.com/testco">Instagram</a>
                    </div>
                </footer>
            </body>
        </html>
        """
        
        result = self.extractor.extract_social_media_links(html)
        
        # Should find all social media links despite consent popups
        self.assertEqual(len(result), 4)
        self.assertIn('facebook', result)
        self.assertIn('twitter', result)
        self.assertIn('linkedin', result)
        self.assertIn('instagram', result)
        
        # Verify correct URLs are extracted
        self.assertEqual(result['facebook'], 'https://facebook.com/company')
        self.assertEqual(result['twitter'], 'https://twitter.com/company')
        self.assertEqual(result['linkedin'], 'https://linkedin.com/company/testco')
        self.assertEqual(result['instagram'], 'https://instagram.com/testco')


def run_comprehensive_test():
    """Run comprehensive test with detailed output"""
    print("🧪 Social Media Link Extraction Test Suite")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSocialMediaExtraction)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback}")
    
    if result.errors:
        print(f"\n❌ Errors:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback}")
    
    if result.wasSuccessful():
        print(f"\n✅ All tests passed! Social media extraction is ready for implementation.")
    else:
        print(f"\n❌ Some tests failed. Review and fix before implementation.")
    
    return result.wasSuccessful()


def demo_extraction():
    """Demonstrate extraction on sample HTML"""
    print("\n🔬 Social Media Extraction Demo")
    print("-" * 30)
    
    sample_html = """
    <html>
        <head><title>Demo Company</title></head>
        <body>
            <header>
                <nav>
                    <a href="/home">Home</a>
                    <a href="https://facebook.com/democompany">Facebook</a>
                    <a href="https://twitter.com/democompany">Twitter</a>
                </nav>
            </header>
            <main>
                <h1>Welcome to Demo Company</h1>
                <p>Connect with us!</p>
            </main>
            <footer>
                <div class="social-links">
                    <a href="https://linkedin.com/company/democompany">LinkedIn</a>
                    <a href="https://instagram.com/democompany">Instagram</a>
                    <a href="https://github.com/democompany">GitHub</a>
                </div>
                <p>&copy; 2025 Demo Company</p>
            </footer>
        </body>
    </html>
    """
    
    extractor = SocialMediaExtractor()
    result = extractor.extract_social_media_links(sample_html)
    
    print(f"📄 Sample HTML processed")
    print(f"🔗 Social media links found: {len(result)}")
    
    for platform, url in result.items():
        print(f"   {platform}: {url}")
    
    return result


if __name__ == "__main__":
    print("🚀 Starting Social Media Extraction Tests")
    
    # Run comprehensive tests
    success = run_comprehensive_test()
    
    # Run demo
    demo_result = demo_extraction()
    
    # Final status
    print(f"\n🎯 Test Suite Status: {'✅ PASSED' if success else '❌ FAILED'}")
    print(f"📊 Demo extracted {len(demo_result)} social media links")
    
    if success:
        print("\n✅ Ready to integrate social media extraction into the main crawler!")
    else:
        print("\n❌ Fix failing tests before integration")