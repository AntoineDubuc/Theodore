"""
Validation utilities for Theodore CLI.

Provides input validation and normalization functions.
"""

import re
from typing import Optional


def validate_company_name(company_name: str) -> Optional[str]:
    """
    Validate and normalize company name input.
    
    Args:
        company_name: Raw company name input
        
    Returns:
        Normalized company name or None if invalid
    """
    
    if not company_name or not isinstance(company_name, str):
        return None
    
    # Basic cleanup
    normalized = company_name.strip()
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Check minimum length
    if len(normalized) < 2:
        return None
    
    # Check maximum length
    if len(normalized) > 100:
        return None
    
    # Check for valid characters (allow letters, numbers, spaces, and common punctuation)
    if not re.match(r'^[a-zA-Z0-9\s\-\.\,\&\(\)]+$', normalized):
        return None
    
    return normalized


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid URL format
    """
    
    if not url:
        return False
    
    # Basic URL pattern
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(url) is not None


def validate_similarity_threshold(threshold: float) -> bool:
    """
    Validate similarity threshold value.
    
    Args:
        threshold: Threshold value to validate
        
    Returns:
        True if valid threshold (0.0 to 1.0)
    """
    
    return isinstance(threshold, (int, float)) and 0.0 <= threshold <= 1.0


def normalize_industry(industry: str) -> Optional[str]:
    """
    Normalize industry name.
    
    Args:
        industry: Raw industry input
        
    Returns:
        Normalized industry name or None if invalid
    """
    
    if not industry or not isinstance(industry, str):
        return None
    
    # Basic cleanup
    normalized = industry.strip().lower()
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Check length
    if len(normalized) < 2 or len(normalized) > 50:
        return None
    
    return normalized


def validate_file_path(file_path: str) -> bool:
    """
    Validate file path for saving results.
    
    Args:
        file_path: File path to validate
        
    Returns:
        True if valid file path
    """
    
    if not file_path or not isinstance(file_path, str):
        return False
    
    # Check for valid file path characters
    if not re.match(r'^[a-zA-Z0-9\s\-\._/\\:]+$', file_path):
        return False
    
    # Check for valid extension
    valid_extensions = ['.json', '.yaml', '.yml', '.csv', '.txt', '.md']
    if not any(file_path.lower().endswith(ext) for ext in valid_extensions):
        return False
    
    return True