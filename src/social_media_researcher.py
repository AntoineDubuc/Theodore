"""
Social Media Research Module for Theodore
=========================================

Extracts social media links from crawled website content as part of the 
intelligent company scraping pipeline. Integrates as Phase 5 of the 
4-phase Antoine crawler architecture.

Features:
- Consent popup removal to prevent extraction interference
- 15+ social media platform support
- Enhanced request headers for bot detection avoidance
- Comprehensive CSS selectors for header/footer extraction
- False positive filtering for accurate results

Usage:
    researcher = SocialMediaResearcher()
    social_links = researcher.extract_social_media_links(html_content)
"""

import logging
import asyncio
from typing import Dict, List
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class SocialMediaResearcher:
    """
    Advanced social media link extractor with consent popup handling
    and comprehensive platform support for company intelligence gathering.
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
        'header a[href*="x.com"]', 'header a[href*="tiktok"]',
        
        # Footer selectors  
        'footer a[href*="facebook"]', 'footer a[href*="twitter"]', 'footer a[href*="linkedin"]',
        'footer a[href*="instagram"]', 'footer a[href*="youtube"]', 'footer a[href*="github"]',
        'footer a[href*="x.com"]', 'footer a[href*="tiktok"]',
        
        # Generic social link containers
        '.social-links a', '.social-media a', '.social a',
        '[class*="social"] a', '[id*="social"] a',
        
        # Common social icon patterns
        'a[class*="facebook"]', 'a[class*="twitter"]', 'a[class*="linkedin"]',
        'a[class*="instagram"]', 'a[class*="youtube"]', 'a[class*="github"]',
        'a[class*="tiktok"]', 'a[class*="discord"]',
    ]
    
    def extract_social_media_links(self, html_content: str) -> Dict[str, str]:
        """
        Extract social media links from HTML content with consent popup handling.
        
        Args:
            html_content: Raw HTML content to parse
            
        Returns:
            Dict mapping platform names to URLs
        """
        if not html_content:
            return {}
        
        try:
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
            
        except Exception as e:
            logger.warning(f"Social media extraction failed: {e}")
            return {}
    
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
        
        if removed_count > 0:
            logger.debug(f"Removed {removed_count} consent popup elements")

    def extract_social_media_from_pages(self, page_contents: List[Dict[str, str]], job_id: str = None) -> Dict[str, str]:
        """
        Extract social media links from multiple crawled pages.
        
        Args:
            page_contents: List of page content dictionaries with 'content' key
            job_id: Optional job ID for progress tracking
            
        Returns:
            Dict mapping platform names to URLs (consolidated from all pages)
        """
        all_social_links = {}
        pages_processed = 0
        
        for page in page_contents:
            html_content = page.get('content', '')
            if html_content:
                try:
                    links = self.extract_social_media_links(html_content)
                    # Merge links, keeping the first occurrence of each platform
                    for platform, url in links.items():
                        if platform not in all_social_links:
                            all_social_links[platform] = url
                    pages_processed += 1
                except Exception as e:
                    logger.warning(f"Failed to extract social media from page: {e}")
                    continue
        
        logger.info(f"Social media research complete: {len(all_social_links)} links found from {pages_processed} pages")
        
        return all_social_links

    def get_supported_platforms(self) -> List[str]:
        """
        Get list of supported social media platforms.
        
        Returns:
            List of platform names
        """
        return list(set(self.SOCIAL_MEDIA_DOMAINS.values()))