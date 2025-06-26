"""
SSL Configuration for Theodore
Centralizes SSL handling across the application
"""

import ssl
import certifi
import aiohttp
import logging
import requests
from typing import Optional

# Disable SSL warnings globally
requests.packages.urllib3.disable_warnings()

logger = logging.getLogger(__name__)


def get_ssl_context(verify: bool = False) -> ssl.SSLContext:
    """
    Create SSL context for aiohttp connections
    
    Args:
        verify: Whether to verify SSL certificates
        
    Returns:
        Configured SSL context
    """
    if verify:
        return ssl.create_default_context(cafile=certifi.where())
    else:
        # Create permissive SSL context
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        logger.info("SSL verification disabled for compatibility with self-signed certificates")
        return ssl_context


def get_aiohttp_connector(verify: bool = False) -> aiohttp.TCPConnector:
    """
    Create aiohttp connector with SSL configuration
    
    Args:
        verify: Whether to verify SSL certificates
        
    Returns:
        Configured TCPConnector
    """
    ssl_context = get_ssl_context(verify)
    return aiohttp.TCPConnector(ssl=ssl_context)


def get_browser_args(ignore_ssl: bool = True) -> list:
    """
    Get browser arguments for Crawl4AI
    
    Args:
        ignore_ssl: Whether to ignore SSL errors
        
    Returns:
        List of browser arguments
    """
    if ignore_ssl:
        return [
            "--ignore-certificate-errors",
            "--ignore-certificate-errors-spki-list", 
            "--disable-web-security",
            "--ignore-ssl-errors"
        ]
    return []


# Convenience functions for requests
def requests_get(url: str, verify: bool = False, **kwargs):
    """Wrapper for requests.get with SSL handling"""
    return requests.get(url, verify=verify, **kwargs)


def requests_head(url: str, verify: bool = False, **kwargs):
    """Wrapper for requests.head with SSL handling"""
    return requests.head(url, verify=verify, **kwargs)


def requests_post(url: str, verify: bool = False, **kwargs):
    """Wrapper for requests.post with SSL handling"""
    return requests.post(url, verify=verify, **kwargs)


# Environment-based configuration
def should_verify_ssl() -> bool:
    """Check if SSL verification should be enabled based on environment"""
    import os
    return os.getenv('SSL_VERIFY', 'false').lower() == 'true'


def configure_ssl_for_production():
    """Configure SSL settings appropriate for production environment"""
    import os
    
    # Set SSL certificate file if not already set
    if not os.getenv('SSL_CERT_FILE'):
        os.environ['SSL_CERT_FILE'] = certifi.where()
    
    if not os.getenv('REQUESTS_CA_BUNDLE'):
        os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
    
    logger.info(f"SSL configuration initialized - Verify: {should_verify_ssl()}")
    logger.info(f"Certificate bundle: {certifi.where()}")


# Initialize SSL configuration on import
configure_ssl_for_production()