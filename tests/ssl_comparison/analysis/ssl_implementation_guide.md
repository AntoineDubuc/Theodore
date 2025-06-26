# SSL Fix Implementation Guide for Theodore

## Step-by-Step Implementation

### 1. Fix `/src/intelligent_company_scraper.py`

#### Location: Line 269 - aiohttp Session Creation

**Current Code:**
```python
async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
```

**Fixed Code:**
```python
# Add imports at the top of file
import ssl
import certifi

# In the _comprehensive_link_discovery method (around line 269):
# Create SSL context
ssl_context = ssl.create_default_context(cafile=certifi.where())
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Create connector with SSL context
connector = aiohttp.TCPConnector(ssl=ssl_context)

# Use connector in session
async with aiohttp.ClientSession(connector=connector, timeout=self.session_timeout) as session:
```

#### Location: Lines 866-870 - AsyncWebCrawler

**Current Code:**
```python
async with AsyncWebCrawler(
    headless=True,
    browser_type="chromium",
    verbose=False
) as crawler:
```

**Fixed Code:**
```python
# AsyncWebCrawler uses Chromium browser which handles SSL differently
# Add browser args to ignore certificate errors
async with AsyncWebCrawler(
    headless=True,
    browser_type="chromium",
    verbose=False,
    browser_args=[
        "--ignore-certificate-errors",
        "--ignore-certificate-errors-spki-list",
        "--disable-web-security"
    ]
) as crawler:
```

### 2. Fix `/src/concurrent_intelligent_scraper.py`

#### Similar fixes needed at:
- Line 573 (in _parse_sitemap method)
- Line 632 (in _recursive_crawl method)  
- Lines 844-845 (in _extract_content_with_logging method)

Apply the same AsyncWebCrawler browser_args configuration.

### 3. Fix `/app.py`

#### Location: Line 1214 (inside search_company_website function)

**Add after import:**
```python
import requests
# Disable SSL warnings
requests.packages.urllib3.disable_warnings()
```

#### Location: Lines 1226 and 1252

**Current Code:**
```python
response = requests.get(search_url, headers=headers, timeout=10)
test_response = requests.head(domain, timeout=5, allow_redirects=True)
```

**Fixed Code:**
```python
response = requests.get(search_url, headers=headers, timeout=10, verify=False)
test_response = requests.head(domain, timeout=5, allow_redirects=True, verify=False)
```

### 4. Fix `/src/simple_enhanced_discovery.py`

#### Location: Line 9 (after imports)

**Add:**
```python
import requests
# Disable SSL warnings
requests.packages.urllib3.disable_warnings()
```

#### Location: Lines 858, 886, 911

**Current Code:**
```python
response = requests.get(url, params=params, timeout=10)
```

**Fixed Code:**
```python
response = requests.get(url, params=params, timeout=10, verify=False)
```

### 5. Create SSL Configuration Module

Create `/src/ssl_config.py`:

```python
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
        logger.warning("SSL verification disabled - use only in development")
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
            "--disable-web-security"
        ]
    return []


# Convenience function for requests
def requests_get(url: str, verify: bool = False, **kwargs):
    """Wrapper for requests.get with SSL handling"""
    return requests.get(url, verify=verify, **kwargs)


def requests_head(url: str, verify: bool = False, **kwargs):
    """Wrapper for requests.head with SSL handling"""
    return requests.head(url, verify=verify, **kwargs)
```

### 6. Update Requirements

Add to `requirements.txt`:
```
certifi>=2023.0.0
```

### 7. Environment-based Configuration

Update `/config/settings.py`:

```python
# Add to TheodoreSettings class
ssl_verify: bool = Field(default=False, env="SSL_VERIFY")
ssl_warnings: bool = Field(default=False, env="SSL_WARNINGS")
```

## Testing the Implementation

1. **Test with problematic SSL sites:**
   ```python
   # Test sites with known SSL issues
   test_urls = [
       "https://expired.badssl.com/",
       "https://self-signed.badssl.com/",
       "https://untrusted-root.badssl.com/"
   ]
   ```

2. **Verify each component:**
   - Test aiohttp connections in link discovery
   - Test AsyncWebCrawler with SSL sites
   - Test requests in search functionality

3. **Monitor logs for SSL warnings**

## Rollback Plan

If SSL fixes cause issues:

1. Set environment variable: `SSL_VERIFY=true`
2. Remove browser args from AsyncWebCrawler
3. Change verify=False back to verify=True in requests calls

## Security Considerations

1. **Development vs Production:**
   - Use `SSL_VERIFY=false` only in development
   - Production should use proper certificates
   
2. **Logging:**
   - Log when SSL verification is disabled
   - Track which sites require SSL bypass

3. **Future Improvements:**
   - Implement certificate pinning for known sites
   - Add per-domain SSL configuration
   - Consider using a certificate bundle for internal CAs