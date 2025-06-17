"""
Enhanced extraction strategies to improve field population rates
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ExtractionPattern:
    """Pattern for extracting specific information"""
    field: str
    patterns: List[str]
    context_keywords: List[str]
    priority: int = 0


class EnhancedFieldExtractor:
    """Enhanced extraction methods for commonly missing fields"""
    
    # Common patterns for field extraction
    EXTRACTION_PATTERNS = {
        'founding_year': ExtractionPattern(
            field='founding_year',
            patterns=[
                r'(?:founded|established|started|began|launched)\s+(?:in\s+)?(\d{4})',
                r'since\s+(\d{4})',
                r'(\d{4})\s*[-–]\s*(?:present|today)',
                r'©\s*(\d{4})\s*[-–]\s*\d{4}',  # Copyright years
            ],
            context_keywords=['founded', 'established', 'since', 'history', 'about'],
            priority=1
        ),
        
        'employee_count_range': ExtractionPattern(
            field='employee_count_range',
            patterns=[
                r'(\d+\+?)\s*(?:employees|people|team\s*members)',
                r'team\s*of\s*(\d+)',
                r'(\d+)\s*(?:-|to)\s*(\d+)\s*employees',
                r'(?:small|medium|large)\s*team',
                r'(?:over|more\s*than)\s*(\d+)\s*(?:employees|people)',
            ],
            context_keywords=['team', 'employees', 'people', 'staff', 'workforce'],
            priority=1
        ),
        
        'location': ExtractionPattern(
            field='location',
            patterns=[
                r'(?:headquartered|based|located)\s+(?:in|at)\s+([A-Z][a-zA-Z\s,]+)',
                r'(?:offices?\s+in|presence\s+in)\s+([A-Z][a-zA-Z\s,]+)',
                r'([A-Z][a-zA-Z]+,\s*[A-Z]{2})\s*\d{5}',  # City, State ZIP
                r'(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)[^,]*,\s*[A-Za-z\s,]+)',
            ],
            context_keywords=['headquarters', 'office', 'location', 'based', 'address'],
            priority=2
        ),
        
        'social_media': ExtractionPattern(
            field='social_media',
            patterns=[
                r'(?:twitter|x)\.com/([a-zA-Z0-9_]+)',
                r'linkedin\.com/company/([a-zA-Z0-9-]+)',
                r'facebook\.com/([a-zA-Z0-9.]+)',
                r'instagram\.com/([a-zA-Z0-9_.]+)',
                r'youtube\.com/(?:c|channel|user)/([a-zA-Z0-9_-]+)',
                r'github\.com/([a-zA-Z0-9-]+)',
            ],
            context_keywords=['follow', 'connect', 'social', 'twitter', 'linkedin'],
            priority=3
        ),
        
        'contact_info': ExtractionPattern(
            field='contact_info',
            patterns=[
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',  # Email
                r'(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',  # Phone
                r'(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd)[^,]*,\s*[A-Za-z\s,]+\s*\d{5})',  # Address
            ],
            context_keywords=['contact', 'email', 'phone', 'call', 'reach'],
            priority=2
        )
    }
    
    @staticmethod
    def extract_founding_year(content: str) -> Optional[int]:
        """Extract founding year from content"""
        for pattern in EnhancedFieldExtractor.EXTRACTION_PATTERNS['founding_year'].patterns:
            matches = re.findall(pattern, content.lower(), re.IGNORECASE)
            for match in matches:
                try:
                    year = int(match)
                    if 1800 < year <= 2024:  # Reasonable year range
                        return year
                except:
                    continue
        return None
    
    @staticmethod
    def extract_employee_count(content: str) -> Optional[str]:
        """Extract employee count range from content"""
        content_lower = content.lower()
        
        # Check for specific patterns
        patterns = [
            (r'(\d+)\s*(?:-|to)\s*(\d+)\s*employees', lambda m: f"{m[1]}-{m[2]}"),
            (r'(\d+)\+?\s*employees', lambda m: f"{m[1]}+"),
            (r'team\s*of\s*(\d+)', lambda m: f"{m[1]}"),
            (r'over\s*(\d+)\s*(?:employees|people)', lambda m: f"{m[1]}+"),
        ]
        
        for pattern, formatter in patterns:
            match = re.search(pattern, content_lower)
            if match:
                return formatter(match.groups())
        
        # Check for size indicators
        if 'small team' in content_lower or 'startup' in content_lower:
            return "1-50"
        elif 'medium' in content_lower or 'mid-size' in content_lower:
            return "50-500"
        elif 'large' in content_lower or 'enterprise' in content_lower:
            return "500+"
        
        return None
    
    @staticmethod
    def extract_location(content: str) -> Optional[str]:
        """Extract headquarters location from content"""
        # Look for headquarters patterns
        hq_patterns = [
            r'(?:headquartered|based|located)\s+(?:in|at)\s+([A-Z][a-zA-Z\s,]+?)(?:\.|,|\s+and|\s+with)',
            r'([A-Z][a-zA-Z]+(?:,\s*[A-Z]{2})?)\s*\d{5}',  # City, State ZIP
        ]
        
        for pattern in hq_patterns:
            match = re.search(pattern, content)
            if match:
                location = match.group(1).strip()
                # Clean up location
                location = re.sub(r'\s+', ' ', location)
                if len(location) > 3 and location != 'United States':
                    return location
        
        return None
    
    @staticmethod
    def extract_social_media(content: str) -> Dict[str, str]:
        """Extract social media links from content"""
        social_media = {}
        
        patterns = {
            'twitter': r'(?:twitter|x)\.com/([a-zA-Z0-9_]+)',
            'linkedin': r'linkedin\.com/company/([a-zA-Z0-9-]+)',
            'facebook': r'facebook\.com/([a-zA-Z0-9.]+)',
            'instagram': r'instagram\.com/([a-zA-Z0-9_.]+)',
            'youtube': r'youtube\.com/(?:c|channel|user)/([a-zA-Z0-9_-]+)',
            'github': r'github\.com/([a-zA-Z0-9-]+)',
        }
        
        for platform, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                social_media[platform] = match.group(1)
        
        return social_media
    
    @staticmethod
    def extract_contact_info(content: str) -> Dict[str, str]:
        """Extract contact information from content"""
        contact_info = {}
        
        # Email pattern
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        email_match = re.search(email_pattern, content)
        if email_match:
            email = email_match.group(1)
            # Filter out common non-contact emails
            if not any(x in email.lower() for x in ['example', 'test', 'noreply', 'demo']):
                contact_info['email'] = email
        
        # Phone pattern (US format)
        phone_pattern = r'(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        phone_match = re.search(phone_pattern, content)
        if phone_match:
            contact_info['phone'] = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"
        
        # Address pattern
        address_pattern = r'(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)[^,]*,\s*[A-Za-z\s,]+\s*\d{5})'
        address_match = re.search(address_pattern, content)
        if address_match:
            contact_info['address'] = address_match.group(1).strip()
        
        return contact_info
    
    @staticmethod
    def extract_certifications(content: str) -> List[str]:
        """Extract certifications and compliance standards"""
        certifications = []
        
        # Common certification patterns
        cert_patterns = [
            r'(ISO\s*\d{4,5}(?::\d{4})?)',
            r'(SOC\s*[12]\s*Type\s*[III]+)',
            r'(GDPR\s*compliant)',
            r'(HIPAA\s*compliant)',
            r'(PCI[\s-]DSS)',
            r'(CCPA\s*compliant)',
        ]
        
        for pattern in cert_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            certifications.extend(matches)
        
        # Look for certification sections
        if 'certif' in content.lower() or 'complian' in content.lower():
            # Extract bullet points or lists near these keywords
            cert_section = re.search(r'(?:certif|complian)[^.]*?(?:\n|$)((?:[•\-*]\s*[^\n]+\n?){1,5})', content, re.IGNORECASE)
            if cert_section:
                items = re.findall(r'[•\-*]\s*([^\n]+)', cert_section.group(1))
                certifications.extend([item.strip() for item in items if len(item.strip()) < 50])
        
        return list(set(certifications))  # Remove duplicates
    
    @staticmethod
    def extract_partnerships(content: str) -> List[str]:
        """Extract key partnerships"""
        partnerships = []
        
        # Look for partnership keywords
        partnership_section = re.search(
            r'(?:partners|partnerships|integrat(?:es|ions)|works?\s+with)[^.]*?(?:\n|$)((?:[^.]+\.){1,3})',
            content, re.IGNORECASE
        )
        
        if partnership_section:
            # Look for company names (capitalized words)
            potential_partners = re.findall(r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\b', partnership_section.group(0))
            
            # Filter out common words
            exclude_words = {'The', 'Our', 'We', 'Partner', 'Partners', 'Integration', 'With', 'Works'}
            partnerships = [p for p in potential_partners if p not in exclude_words and len(p) > 3]
        
        return list(set(partnerships[:10]))  # Limit to 10 unique partnerships


def enhance_company_extraction(company_data: 'CompanyData', raw_content: str) -> 'CompanyData':
    """
    Enhance company data by extracting commonly missing fields
    
    Args:
        company_data: Existing company data object
        raw_content: Raw scraped content to extract from
        
    Returns:
        Enhanced company data with additional fields populated
    """
    extractor = EnhancedFieldExtractor()
    
    # Extract founding year if missing
    if not company_data.founding_year and raw_content:
        founding_year = extractor.extract_founding_year(raw_content)
        if founding_year:
            company_data.founding_year = founding_year
    
    # Extract employee count if missing
    if not company_data.employee_count_range and raw_content:
        employee_range = extractor.extract_employee_count(raw_content)
        if employee_range:
            company_data.employee_count_range = employee_range
    
    # Extract location if missing
    if not company_data.location and raw_content:
        location = extractor.extract_location(raw_content)
        if location:
            company_data.location = location
    
    # Extract social media if missing or empty
    if (not company_data.social_media or company_data.social_media == {}) and raw_content:
        social_media = extractor.extract_social_media(raw_content)
        if social_media:
            company_data.social_media = social_media
    
    # Extract contact info if missing or empty
    if (not company_data.contact_info or company_data.contact_info == {}) and raw_content:
        contact_info = extractor.extract_contact_info(raw_content)
        if contact_info:
            company_data.contact_info = contact_info
    
    # Extract certifications if missing
    if not company_data.certifications and raw_content:
        certifications = extractor.extract_certifications(raw_content)
        if certifications:
            company_data.certifications = certifications
    
    # Extract partnerships if missing
    if not company_data.partnerships and raw_content:
        partnerships = extractor.extract_partnerships(raw_content)
        if partnerships:
            company_data.partnerships = partnerships
    
    return company_data


# Enhanced prompts for better AI extraction
ENHANCED_EXTRACTION_PROMPTS = {
    'detailed_extraction': """
Extract the following specific information from the company content:

1. **Founding Year**: Look for phrases like "founded in", "established", "since", or copyright years
2. **Employee Count**: Look for team size, number of employees, or size indicators (small/medium/large)
3. **Headquarters Location**: City and state/country where the company is based
4. **Social Media**: Extract handles/usernames for Twitter/X, LinkedIn, Facebook, Instagram, YouTube
5. **Contact Information**: Email addresses, phone numbers, physical addresses
6. **Certifications**: ISO, SOC, GDPR, HIPAA, or other compliance certifications
7. **Key Partnerships**: Companies they partner with or integrate with
8. **Awards & Recognition**: Industry awards, rankings, or recognition
9. **Leadership Team**: Names and titles of executives (CEO, CTO, etc.)
10. **Products/Services**: Specific products or services offered (not general categories)

Return in JSON format with these exact keys:
founding_year (integer), employee_count_range (string like "50-100"), location (string),
social_media (object with platform names as keys), contact_info (object with email/phone/address),
certifications (array), partnerships (array), awards (array), leadership_team (array of {name, title}),
products_services_offered (array)

If information is not found, use null for that field.
""",
    
    'page_specific_extraction': {
        'about': """Focus on: founding year, company mission, employee count, headquarters location, company values""",
        'contact': """Focus on: email addresses, phone numbers, physical addresses, social media links""",
        'team': """Focus on: leadership names and titles, team size, department structure""",
        'careers': """Focus on: employee count, company culture, benefits, office locations""",
        'footer': """Focus on: social media links, certifications, legal information, contact details"""
    }
}