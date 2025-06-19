"""
Specialized page scraper for targeted business intelligence extraction
Focuses on specific page types for leadership, partnerships, awards, etc.
"""

import asyncio
from typing import Dict, List, Optional, Any
import re
from urllib.parse import urljoin, urlparse

class SpecializedPageScraper:
    """Scraper that targets specific page types for enhanced data extraction"""
    
    def __init__(self):
        # Page type patterns for targeted scraping
        self.page_patterns = {
            'leadership': [
                r'/team', r'/leadership', r'/about.*team', r'/management',
                r'/executives', r'/founders', r'/board', r'/advisors'
            ],
            'partnerships': [
                r'/partners', r'/partnerships', r'/alliances', r'/integrations',
                r'/ecosystem', r'/marketplace', r'/certified.*partners'
            ],
            'awards': [
                r'/awards', r'/recognition', r'/achievements', r'/press',
                r'/news', r'/media', r'/accolades'
            ],
            'funding': [
                r'/investors', r'/funding', r'/investment', r'/series.*',
                r'/venture', r'/capital', r'/finance'
            ],
            'contact': [
                r'/contact', r'/get.*touch', r'/reach.*us', r'/support',
                r'/sales', r'/demo', r'/talk.*to.*us'
            ]
        }
        
        # Content extraction patterns for each page type
        self.extraction_patterns = {
            'leadership': {
                'executives': [
                    r'ceo[:\s-]*([^,\n\.]{5,50})',
                    r'chief executive officer[:\s-]*([^,\n\.]{5,50})',
                    r'founder[:\s-]*([^,\n\.]{5,50})',
                    r'president[:\s-]*([^,\n\.]{5,50})',
                    r'cto[:\s-]*([^,\n\.]{5,50})',
                    r'cfo[:\s-]*([^,\n\.]{5,50})',
                    r'cmo[:\s-]*([^,\n\.]{5,50})',
                    r'vp[:\s-]*([^,\n\.]{5,50})',
                    r'vice president[:\s-]*([^,\n\.]{5,50})',
                    r'head of[:\s-]*([^,\n\.]{5,50})',
                    r'director[:\s-]*([^,\n\.]{5,50})'
                ]
            },
            'partnerships': {
                'partners': [
                    r'partner(?:s|ship)?[:\s-]*([^,\n\.]{5,100})',
                    r'alliance[:\s-]*([^,\n\.]{5,100})',
                    r'integration[:\s-]*([^,\n\.]{5,100})',
                    r'certified[:\s-]*([^,\n\.]{5,100})',
                    r'ecosystem[:\s-]*([^,\n\.]{5,100})'
                ]
            },
            'awards': {
                'recognition': [
                    r'award[:\s-]*([^,\n\.]{5,100})',
                    r'winner[:\s-]*([^,\n\.]{5,100})',
                    r'recognized[:\s-]*([^,\n\.]{5,100})',
                    r'best[:\s-]*([^,\n\.]{5,100})',
                    r'top[:\s-]*([^,\n\.]{5,100})',
                    r'leader[:\s-]*([^,\n\.]{5,100})',
                    r'excellence[:\s-]*([^,\n\.]{5,100})'
                ]
            }
        }
    
    def identify_specialized_pages(self, all_discovered_urls: List[str], base_domain: str) -> Dict[str, List[str]]:
        """Identify URLs that match specialized page patterns"""
        specialized_pages = {page_type: [] for page_type in self.page_patterns.keys()}
        
        for url in all_discovered_urls:
            url_lower = url.lower()
            
            for page_type, patterns in self.page_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, url_lower):
                        specialized_pages[page_type].append(url)
                        break  # Avoid duplicate categorization
        
        return specialized_pages
    
    def prioritize_scraping_targets(self, specialized_pages: Dict[str, List[str]], 
                                  missing_fields: List[str]) -> List[str]:
        """Prioritize which pages to scrape based on missing fields"""
        priority_urls = []
        
        # Map missing fields to page types
        field_to_page_mapping = {
            'leadership_team': 'leadership',
            'partnerships': 'partnerships', 
            'awards': 'awards',
            'funding_status': 'funding',
            'contact_info': 'contact',
            'founding_year': 'leadership',  # Often found on team/about pages
            'location': 'contact'
        }
        
        # Add high-priority pages based on missing fields
        for field in missing_fields:
            page_type = field_to_page_mapping.get(field)
            if page_type and specialized_pages.get(page_type):
                priority_urls.extend(specialized_pages[page_type][:2])  # Top 2 per type
        
        # Remove duplicates while preserving order
        seen = set()
        return [url for url in priority_urls if not (url in seen or seen.add(url))]
    
    def extract_structured_data(self, page_content: str, page_type: str) -> Dict[str, Any]:
        """Extract structured data from specialized page content"""
        extracted_data = {}
        
        if page_type not in self.extraction_patterns:
            return extracted_data
        
        page_patterns = self.extraction_patterns[page_type]
        page_content_lower = page_content.lower()
        
        for data_type, patterns in page_patterns.items():
            matches = []
            
            for pattern in patterns:
                found_matches = re.findall(pattern, page_content_lower, re.IGNORECASE | re.MULTILINE)
                for match in found_matches:
                    # Clean up the match
                    cleaned_match = re.sub(r'\s+', ' ', match.strip())
                    if len(cleaned_match) > 3 and cleaned_match not in matches:
                        matches.append(cleaned_match.title())
            
            if matches:
                extracted_data[data_type] = matches[:10]  # Limit to top 10 matches
        
        return extracted_data
    
    def generate_specialized_prompt(self, company_name: str, page_type: str, 
                                  page_content: str, missing_fields: List[str]) -> str:
        """Generate specialized AI prompt for specific page types"""
        
        prompts = {
            'leadership': f"""
            Analyze this leadership/team page for {company_name} and extract:
            - CEO name and background
            - Founders and their roles  
            - C-level executives (CTO, CFO, CMO, etc.)
            - Board members or advisors
            - Any mention of company founding year or history
            
            Content: {page_content[:2000]}
            
            Format as:
            CEO: [Name - Background]
            Founders: [Name - Role, Name - Role]
            Executives: [Title - Name, Title - Name]
            Founded: [Year if mentioned]
            """,
            
            'partnerships': f"""
            Analyze this partnerships page for {company_name} and extract:
            - Technology partners and integrations
            - Strategic alliances
            - Certified partnerships
            - Channel partners
            - Ecosystem members
            
            Content: {page_content[:2000]}
            
            Format as:
            Technology Partners: [Company1, Company2, Company3]
            Strategic Partners: [Company1, Company2]
            Integrations: [Platform1, Platform2]
            """,
            
            'awards': f"""
            Analyze this awards/recognition page for {company_name} and extract:
            - Industry awards received
            - Recognition and accolades
            - "Best of" or "Top" designations
            - Year of awards when mentioned
            
            Content: {page_content[:2000]}
            
            Format as:
            Awards: [Award Name - Year, Award Name - Year]
            Recognition: [Recognition Type - Source]
            """
        }
        
        return prompts.get(page_type, f"Analyze this {page_type} page and extract relevant business information.")
    
    async def enhanced_field_scraping(self, company_data: Dict[str, Any], 
                                    discovered_urls: List[str]) -> Dict[str, Any]:
        """Perform enhanced scraping focused on missing fields"""
        
        # Identify missing fields
        missing_fields = []
        if not company_data.get('leadership_team'):
            missing_fields.append('leadership_team')
        if not company_data.get('partnerships'):
            missing_fields.append('partnerships')
        if not company_data.get('awards'):
            missing_fields.append('awards')
        if not company_data.get('funding_status'):
            missing_fields.append('funding_status')
        if not company_data.get('contact_info'):
            missing_fields.append('contact_info')
        
        if not missing_fields:
            return company_data
        
        # Get base domain for URL filtering
        website = company_data.get('website', '')
        if website:
            base_domain = urlparse(website).netloc
        else:
            return company_data
        
        # Identify specialized pages
        specialized_pages = self.identify_specialized_pages(discovered_urls, base_domain)
        
        # Prioritize scraping targets
        priority_urls = self.prioritize_scraping_targets(specialized_pages, missing_fields)
        
        if not priority_urls:
            return company_data
        
        print(f"   🎯 Targeting {len(priority_urls)} specialized pages for {company_data.get('name', 'Unknown')}")
        
        # This would integrate with the existing Crawl4AI scraper
        # For now, return the enhanced structure
        enhanced_data = company_data.copy()
        enhanced_data['specialized_pages_identified'] = len(priority_urls)
        enhanced_data['priority_scraping_targets'] = priority_urls[:5]  # Top 5 for metadata
        
        return enhanced_data