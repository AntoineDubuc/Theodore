"""
Enhanced page selection strategies for better data extraction
"""

from typing import List, Dict, Set, Tuple
import re
from urllib.parse import urlparse

class EnhancedPageSelector:
    """Improved page selection targeting missing data points"""
    
    # Page patterns for specific data extraction
    PAGE_DATA_MAPPING = {
        'contact': {
            'patterns': ['contact', 'get-in-touch', 'reach-us', 'connect'],
            'extracts': ['location', 'email', 'phone', 'address', 'social_media']
        },
        'about': {
            'patterns': ['about', 'company', 'who-we-are', 'our-story'],
            'extracts': ['founding_year', 'location', 'company_size', 'mission', 'values']
        },
        'team': {
            'patterns': ['team', 'leadership', 'people', 'management', 'board'],
            'extracts': ['leadership_team', 'employee_count', 'key_decision_makers']
        },
        'careers': {
            'patterns': ['careers', 'jobs', 'work-with-us', 'join', 'hiring'],
            'extracts': ['employee_count', 'company_culture', 'locations', 'tech_stack']
        },
        'products': {
            'patterns': ['products', 'services', 'solutions', 'offerings', 'what-we-do'],
            'extracts': ['products_services_offered', 'value_proposition', 'use_cases']
        },
        'pricing': {
            'patterns': ['pricing', 'plans', 'cost', 'packages', 'quote'],
            'extracts': ['pricing_model', 'target_market', 'company_size_targets']
        },
        'partners': {
            'patterns': ['partners', 'integrations', 'ecosystem', 'alliances'],
            'extracts': ['partnerships', 'integrations', 'tech_ecosystem']
        },
        'news': {
            'patterns': ['news', 'press', 'media', 'announcements', 'updates'],
            'extracts': ['recent_news', 'funding_status', 'awards', 'growth_indicators']
        },
        'security': {
            'patterns': ['security', 'compliance', 'trust', 'privacy', 'certifications'],
            'extracts': ['certifications', 'compliance_standards', 'security_features']
        },
        'customers': {
            'patterns': ['customers', 'clients', 'case-studies', 'testimonials', 'success-stories'],
            'extracts': ['target_market', 'customer_size', 'use_cases', 'testimonials']
        }
    }
    
    @staticmethod
    def generate_enhanced_llm_prompt(company_name: str, base_url: str, all_links: List[str]) -> str:
        """Generate an enhanced prompt targeting missing data points"""
        
        links_text = "\n".join([f"- {link}" for link in all_links[:200]])  # Increased to 200 for better coverage
        
        prompt = f"""You are a data extraction specialist analyzing {company_name}'s website structure.
Your goal is to select pages that contain specific missing data points we need.

Website: {base_url}
Available pages:
{links_text}

Select up to 50 pages that are most likely to contain these CRITICAL data points:

🔴 HIGHEST PRIORITY (Missing in our database):
1. **Location/Headquarters**: Look for /contact, /about, /company pages
2. **Founded Year**: Look for /about, /our-story, /history, /company
3. **Employee Count**: Look for /about, /team, /careers pages
4. **Contact Information**: Look for /contact, /get-in-touch, footer pages
5. **Social Media Links**: Often in /contact or footer pages
6. **Products/Services Details**: Look for /products, /services, /solutions
7. **Leadership Team**: Look for /team, /leadership, /about/team
8. **Partnerships**: Look for /partners, /integrations, /ecosystem
9. **Certifications**: Look for /security, /compliance, /trust, /about
10. **Company Stage/Funding**: Look for /about, /press, /news

🟡 SECONDARY PRIORITY:
- Decision maker titles (team pages)
- Company culture (careers pages)
- Recent news and updates
- Awards and recognition
- Geographic scope

Prioritize pages with these URL patterns:
- /about* (founding year, location, size)
- /contact* (all contact info, location)
- /team* or /leadership* (decision makers)
- /careers* or /jobs* (employee count, culture)
- /products* or /services* (offerings)
- /partners* (partnerships)
- /security* or /compliance* (certifications)

Return ONLY a JSON array of URLs prioritized by likelihood of containing missing data:
["url1", "url2", "url3", ...]

Focus on pages that typically have structured data we can extract."""
        
        return prompt
    
    @staticmethod
    def score_url_for_missing_data(url: str, missing_fields: Set[str]) -> int:
        """Score a URL based on likelihood of containing missing data"""
        score = 0
        url_lower = url.lower()
        
        # Check each page type
        for page_type, info in EnhancedPageSelector.PAGE_DATA_MAPPING.items():
            # Check if URL matches this page type
            if any(pattern in url_lower for pattern in info['patterns']):
                # Add score based on how many missing fields this page might have
                matching_fields = set(info['extracts']) & missing_fields
                score += len(matching_fields) * 20
        
        # Bonus for specific high-value pages
        if 'contact' in url_lower and 'location' in missing_fields:
            score += 50
        if 'about' in url_lower and 'founding_year' in missing_fields:
            score += 50
        if 'team' in url_lower and 'leadership_team' in missing_fields:
            score += 40
        
        # Penalize deep nested pages
        depth = url.count('/') - 2
        if depth > 3:
            score -= depth * 5
        
        return score
    
    @staticmethod
    def get_page_extraction_targets(url: str) -> List[str]:
        """Get list of data points likely to be found on a specific page"""
        url_lower = url.lower()
        targets = []
        
        for page_type, info in EnhancedPageSelector.PAGE_DATA_MAPPING.items():
            if any(pattern in url_lower for pattern in info['patterns']):
                targets.extend(info['extracts'])
        
        return list(set(targets))
    
    @staticmethod
    def create_page_specific_prompts(url: str, company_name: str) -> Dict[str, str]:
        """Create extraction prompts specific to page type"""
        url_lower = url.lower()
        prompts = {}
        
        if 'contact' in url_lower:
            prompts['contact'] = f"""Extract from this contact page for {company_name}:
            - Physical address/headquarters location
            - Email addresses (general, sales, support)
            - Phone numbers
            - Social media links
            - Office locations if multiple"""
        
        if 'about' in url_lower:
            prompts['about'] = f"""Extract from this about page for {company_name}:
            - Founded/established year
            - Company headquarters location
            - Number of employees or company size
            - Company mission and values
            - Key milestones or history"""
        
        if 'team' in url_lower or 'leadership' in url_lower:
            prompts['team'] = f"""Extract from this team page for {company_name}:
            - Leadership team names and titles
            - Board members if listed
            - Key decision makers (C-level, VPs)
            - Department heads
            - Total team size if mentioned"""
        
        if 'careers' in url_lower or 'jobs' in url_lower:
            prompts['careers'] = f"""Extract from this careers page for {company_name}:
            - Number of employees (team size)
            - Office locations
            - Company culture description
            - Tech stack from job descriptions
            - Growth indicators"""
        
        return prompts


def enhance_page_selection_in_scraper():
    """
    Suggested improvements to the intelligent scraper's page selection
    """
    improvements = {
        'llm_prompt': {
            'current_issue': 'Generic prompt not targeting missing fields',
            'improvement': 'Use enhanced prompt focusing on location, founding year, contacts, etc.',
            'implementation': 'Replace prompt in _llm_select_promising_pages method'
        },
        'heuristic_scoring': {
            'current_issue': 'Simple keyword matching',
            'improvement': 'Score based on missing data likelihood',
            'implementation': 'Use score_url_for_missing_data method'
        },
        'page_specific_extraction': {
            'current_issue': 'Same extraction for all pages',
            'improvement': 'Customize extraction based on page type',
            'implementation': 'Apply page-specific prompts after scraping'
        },
        'robots_txt_parsing': {
            'current_issue': 'Just collecting URLs',
            'improvement': 'Identify high-value paths like /api, /data, /team',
            'implementation': 'Enhanced parsing in _parse_robots_txt'
        },
        'link_discovery': {
            'current_issue': 'May miss footer/header links',
            'improvement': 'Specifically look for social media and contact in footers',
            'implementation': 'Add footer-specific extraction'
        }
    }
    
    return improvements


# Example integration with existing scraper
def integrate_enhanced_selection(scraper_instance):
    """Example of how to integrate enhanced selection into existing scraper"""
    
    # Store original method
    original_llm_select = scraper_instance._llm_select_promising_pages
    
    # Create enhanced version
    async def enhanced_llm_select(all_links, company_name, base_url):
        # Identify missing fields for this company
        missing_fields = {'location', 'founding_year', 'employee_count', 
                         'contact_email', 'social_media', 'products_services_offered'}
        
        # Sort URLs by likelihood of containing missing data
        scored_urls = [(url, EnhancedPageSelector.score_url_for_missing_data(url, missing_fields)) 
                       for url in all_links]
        scored_urls.sort(key=lambda x: x[1], reverse=True)
        
        # Take top URLs
        top_urls = [url for url, score in scored_urls[:100]]
        
        # Use enhanced prompt if LLM available
        if scraper_instance.bedrock_client:
            enhanced_prompt = EnhancedPageSelector.generate_enhanced_llm_prompt(
                company_name, base_url, top_urls
            )
            # Call LLM with enhanced prompt
            # ... (implementation)
        
        return top_urls[:50]  # Return top 50 pages
    
    # Replace method
    scraper_instance._llm_select_promising_pages = enhanced_llm_select
    
    return scraper_instance