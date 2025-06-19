"""
Enhanced field extractor for specific business intelligence fields
Focuses on improving extraction of founding_year, location, contact_info, leadership_team
"""

import re
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

class EnhancedFieldExtractor:
    """Extract specific business fields using targeted patterns and AI analysis"""
    
    def __init__(self):
        # Patterns for founding year extraction
        self.founding_year_patterns = [
            r'founded in (\d{4})',
            r'established in (\d{4})',
            r'since (\d{4})',
            r'started in (\d{4})',
            r'began in (\d{4})',
            r'inception in (\d{4})',
            r'launched in (\d{4})',
            r'incorporated in (\d{4})',
            r'formed in (\d{4})',
            r'created in (\d{4})',
            r'®\s*(\d{4})',  # Copyright years
            r'©\s*(\d{4})',  # Copyright years
        ]
        
        # Patterns for location extraction
        self.location_patterns = [
            r'headquarters in ([^,.]+(?:, [^,.]+)*)',
            r'based in ([^,.]+(?:, [^,.]+)*)',
            r'located in ([^,.]+(?:, [^,.]+)*)',
            r'offices in ([^,.]+(?:, [^,.]+)*)',
            r'hq in ([^,.]+(?:, [^,.]+)*)',
            r'headquartered in ([^,.]+(?:, [^,.]+)*)',
        ]
        
        # Common CEO/leadership title patterns
        self.leadership_patterns = [
            r'ceo[:\s]+([^,\n]+)',
            r'chief executive officer[:\s]+([^,\n]+)',
            r'founder[:\s]+([^,\n]+)',
            r'president[:\s]+([^,\n]+)',
            r'cto[:\s]+([^,\n]+)',
            r'chief technology officer[:\s]+([^,\n]+)',
            r'cfo[:\s]+([^,\n]+)',
            r'chief financial officer[:\s]+([^,\n]+)',
            r'cmo[:\s]+([^,\n]+)',
            r'chief marketing officer[:\s]+([^,\n]+)',
        ]
    
    def extract_founding_year(self, content: str) -> Optional[int]:
        """Extract founding year from text content"""
        if not content:
            return None
        
        content_lower = content.lower()
        
        for pattern in self.founding_year_patterns:
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            for match in matches:
                try:
                    year = int(match)
                    # Validate reasonable year range
                    if 1800 <= year <= datetime.now().year:
                        return year
                except ValueError:
                    continue
        
        return None
    
    def extract_location(self, content: str) -> Optional[str]:
        """Extract company location from text content"""
        if not content:
            return None
        
        content_lower = content.lower()
        
        for pattern in self.location_patterns:
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            for match in matches:
                # Clean up the location string
                location = match.strip().replace('\n', ' ').replace('\r', '')
                # Remove common prefixes/suffixes
                location = re.sub(r'^(in|at|from)\s+', '', location, flags=re.IGNORECASE)
                location = re.sub(r'\s+(and|with|including).*$', '', location, flags=re.IGNORECASE)
                
                if len(location) > 3:  # Minimum reasonable location length
                    return location.title()
        
        return None
    
    def extract_leadership_team(self, content: str) -> List[str]:
        """Extract leadership team members from text content"""
        if not content:
            return []
        
        content_lower = content.lower()
        leadership = []
        
        for pattern in self.leadership_patterns:
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            for match in matches:
                # Clean up the name
                name = match.strip().replace('\n', ' ').replace('\r', '')
                name = re.sub(r'\s+', ' ', name)  # Normalize whitespace
                
                if len(name) > 2 and len(name) < 100:  # Reasonable name length
                    leadership.append(name.title())
        
        return list(set(leadership))  # Remove duplicates
    
    def extract_contact_info(self, content: str) -> Dict[str, str]:
        """Extract contact information from text content"""
        if not content:
            return {}
        
        contact_info = {}
        
        # Email patterns
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, content)
        if emails:
            # Prefer general contact emails over personal ones
            general_emails = [e for e in emails if any(word in e.lower() for word in ['contact', 'info', 'hello', 'support', 'sales'])]
            contact_info['email'] = general_emails[0] if general_emails else emails[0]
        
        # Phone patterns
        phone_patterns = [
            r'\+?1?[-.\s]?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})',  # US format
            r'\+(\d{1,3})[-.\s]?(\d{1,4})[-.\s]?(\d{1,4})[-.\s]?(\d{1,4})',  # International
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, content)
            if matches:
                # Format the first match nicely
                if len(matches[0]) == 3:  # US format
                    contact_info['phone'] = f"+1-{matches[0][0]}-{matches[0][1]}-{matches[0][2]}"
                break
        
        # Address patterns (basic)
        address_patterns = [
            r'(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln)[^,\n]*(?:,[^,\n]*){0,2})',
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                contact_info['address'] = matches[0].strip()
                break
        
        return contact_info
    
    def generate_enhancement_prompt(self, company_name: str, existing_data: Dict[str, Any]) -> str:
        """Generate AI prompt to extract missing business intelligence fields"""
        
        missing_fields = []
        if not existing_data.get('founding_year'):
            missing_fields.append('founding year')
        if not existing_data.get('location'):
            missing_fields.append('headquarters location')
        if not existing_data.get('leadership_team'):
            missing_fields.append('leadership team (CEO, CTO, founders)')
        if not existing_data.get('employee_count_range'):
            missing_fields.append('company size/employee count')
        if not existing_data.get('funding_status'):
            missing_fields.append('funding status')
        
        if not missing_fields:
            return None
        
        prompt = f"""Analyze the following company and extract specific missing business intelligence:

Company: {company_name}
Website: {existing_data.get('website', 'Unknown')}
Current Description: {existing_data.get('company_description', 'No description available')}

Please extract ONLY the following missing information:
{', '.join(missing_fields)}

Focus on factual, verifiable information. If information is not available or unclear, respond with "Not found".

Format your response as:
- Founding Year: [YYYY or Not found]
- Location: [City, State/Country or Not found]  
- Leadership: [CEO Name - Title, CTO Name - Title, etc. or Not found]
- Company Size: [Employee range like "51-200" or Not found]
- Funding: [Series A/B/C, Amount, or Not found]

Be concise and factual."""

        return prompt

    def enhance_company_data(self, company_data: Dict[str, Any], scraped_content: str = None) -> Dict[str, Any]:
        """Enhance company data with extracted fields"""
        enhanced_data = company_data.copy()
        
        if scraped_content:
            # Extract fields using pattern matching
            if not enhanced_data.get('founding_year'):
                founding_year = self.extract_founding_year(scraped_content)
                if founding_year:
                    enhanced_data['founding_year'] = founding_year
            
            if not enhanced_data.get('location'):
                location = self.extract_location(scraped_content)
                if location:
                    enhanced_data['location'] = location
            
            if not enhanced_data.get('leadership_team'):
                leadership = self.extract_leadership_team(scraped_content)
                if leadership:
                    enhanced_data['leadership_team'] = leadership
            
            if not enhanced_data.get('contact_info'):
                contact_info = self.extract_contact_info(scraped_content)
                if contact_info:
                    enhanced_data['contact_info'] = contact_info
        
        return enhanced_data