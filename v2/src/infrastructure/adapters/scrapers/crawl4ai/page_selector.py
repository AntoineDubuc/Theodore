#!/usr/bin/env python3
"""
LLM Page Selector - Phase 2 of Intelligent Scraping
===================================================

AI-powered page selection that uses LLM analysis to choose the most valuable pages
for business intelligence extraction from all discovered URLs.
"""

from typing import List, Dict, Any, Optional
from ...core.interfaces.ai_provider import AIProviderPort
import json
import logging
import re


class LLMPageSelector:
    """AI-powered service for intelligent page selection"""
    
    def __init__(self, ai_provider: AIProviderPort):
        self.ai_provider = ai_provider
        self.logger = logging.getLogger(__name__)
    
    async def select_valuable_pages(
        self, 
        urls: List[str], 
        max_pages: int = 50,
        base_url: str = ""
    ) -> List[str]:
        """Use LLM to intelligently select the most valuable pages."""
        
        if len(urls) <= max_pages:
            self.logger.info(f"All {len(urls)} URLs selected (within limit)")
            return urls
        
        # Create the selection prompt
        selection_prompt = self._create_selection_prompt(urls, max_pages, base_url)
        
        try:
            # Get LLM analysis
            response = await self.ai_provider.analyze_text(
                text=selection_prompt,
                config={
                    "max_tokens": 2000,
                    "temperature": 0.1  # Low temperature for consistent selection
                }
            )
            
            # Parse the LLM response
            selected_urls = self._parse_selection_response(response.content, urls)
            
            if selected_urls:
                self.logger.info(f"LLM selected {len(selected_urls)} pages from {len(urls)} candidates")
                return selected_urls[:max_pages]
            else:
                self.logger.warning("LLM selection failed, falling back to heuristics")
                return self._heuristic_selection(urls, max_pages)
        
        except Exception as e:
            self.logger.warning(f"LLM page selection failed: {e}")
            # Fallback to heuristic selection
            return self._heuristic_selection(urls, max_pages)
    
    def _create_selection_prompt(self, urls: List[str], max_pages: int, base_url: str) -> str:
        """Create a comprehensive prompt for intelligent page selection."""
        
        urls_text = "\n".join([f"{i+1}. {url}" for i, url in enumerate(urls)])
        
        return f"""You are an expert web scraper analyzing URLs to extract company intelligence. 
From the {len(urls)} discovered URLs below, select the {max_pages} MOST VALUABLE pages for extracting:

🎯 PRIMARY TARGETS (highest priority):
- Contact information & physical locations
- Company founding information & history  
- Employee count & company size indicators
- Leadership team & decision makers
- Business model & value proposition

🎯 SECONDARY TARGETS (good to have):
- Products/services descriptions
- Company culture & values  
- Press releases & company news
- Investor information
- Security & compliance info

❌ AVOID (low value for company intelligence):
- Blog posts & articles
- Product documentation
- Support & help pages
- Legal/privacy pages
- Marketing landing pages
- User-generated content

DISCOVERED URLS:
{urls_text}

Please analyze each URL and return ONLY a JSON array of the selected URLs in order of priority:

```json
[
  "url1",
  "url2", 
  "url3"
]
```

Focus on pages most likely to contain structured company information, contact details, team information, and business intelligence."""

    def _parse_selection_response(self, response: str, original_urls: List[str]) -> List[str]:
        """Parse the LLM response to extract selected URLs."""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'```json\s*(\[.*?\])\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Look for any JSON array in the response
                json_match = re.search(r'\[.*?\]', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON array found in response")
            
            selected_urls = json.loads(json_str)
            
            # Validate that selected URLs are from our original list
            valid_urls = []
            for url in selected_urls:
                if url in original_urls:
                    valid_urls.append(url)
                else:
                    # Try to find partial matches
                    for orig_url in original_urls:
                        if url in orig_url or orig_url in url:
                            valid_urls.append(orig_url)
                            break
            
            return valid_urls
        
        except Exception as e:
            self.logger.warning(f"Failed to parse LLM selection response: {e}")
            return []
    
    def _heuristic_selection(self, urls: List[str], max_pages: int) -> List[str]:
        """Fallback heuristic selection when LLM fails."""
        
        # Priority scoring based on URL patterns
        scored_urls = []
        
        for url in urls:
            score = self._calculate_url_score(url)
            scored_urls.append((score, url))
        
        # Sort by score (highest first) and return top URLs
        scored_urls.sort(reverse=True, key=lambda x: x[0])
        
        selected = [url for score, url in scored_urls[:max_pages]]
        self.logger.info(f"Heuristic selection: {len(selected)} pages selected")
        return selected
    
    def _calculate_url_score(self, url: str) -> float:
        """Calculate heuristic score for URL value."""
        score = 0.0
        path = url.lower()
        
        # High-value page patterns
        high_value = {
            '/contact': 10.0, '/about': 9.0, '/team': 8.0, '/careers': 7.0,
            '/company': 8.0, '/leadership': 7.0, '/management': 6.0, '/executive': 6.0,
            '/investors': 5.0, '/news': 4.0, '/press': 4.0
        }
        
        for pattern, points in high_value.items():
            if pattern in path:
                score += points
        
        # Secondary value patterns
        secondary_value = {
            '/products': 3.0, '/services': 3.0, '/solutions': 3.0,
            '/security': 2.0, '/compliance': 2.0, '/partners': 2.0
        }
        
        for pattern, points in secondary_value.items():
            if pattern in path:
                score += points
        
        # Bonus for root-level pages
        if path.count('/') <= 2:
            score += 2.0
        
        # Penalty for deep nesting
        depth_penalty = max(0, path.count('/') - 3) * 0.5
        score -= depth_penalty
        
        # Penalty for noise patterns
        noise_patterns = [
            '/blog/', '/wp-', '/admin/', '/login/', '/search',
            '.pdf', '.doc', '.jpg', '.png', '/tag/', '/category/'
        ]
        
        for pattern in noise_patterns:
            if pattern in path:
                score -= 5.0
        
        return max(0.0, score)