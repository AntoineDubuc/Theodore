#!/usr/bin/env python3
"""
SSL Configuration for Treatment Test
Applies SSL certificate fixes in isolated scope without modifying Theodore's main codebase
"""

import ssl
import os
import sys
import certifi
import urllib3
from pathlib import Path

class SSLFixer:
    """
    Applies SSL certificate fixes for the treatment test
    All changes are scoped to this test process only
    """
    
    def __init__(self):
        self.original_ssl_context = None
        self.original_env_vars = {}
        self.fixes_applied = []
        
    def apply_ssl_fixes(self):
        """Apply all SSL certificate fixes"""
        
        print("🔧 Applying SSL certificate fixes for treatment test...")
        
        # Fix 1: Update certifi certificates
        self._fix_certifi_certificates()
        
        # Fix 2: Set SSL environment variables
        self._fix_ssl_environment_variables()
        
        # Fix 3: Configure SSL context programmatically
        self._fix_ssl_context()
        
        # Fix 4: Disable SSL warnings for development
        self._disable_ssl_warnings()
        
        print(f"✅ Applied {len(self.fixes_applied)} SSL fixes:")
        for fix in self.fixes_applied:
            print(f"   • {fix}")
            
    def _fix_certifi_certificates(self):
        """Ensure certifi certificates are up to date"""
        
        try:
            # Verify certifi is available and get certificate path
            cert_path = certifi.where()
            
            if os.path.exists(cert_path):
                print(f"📋 Using certifi certificates: {cert_path}")
                self.fixes_applied.append("Certifi certificate bundle located and verified")
                
                # Set environment variables to use certifi certificates
                os.environ['SSL_CERT_FILE'] = cert_path
                os.environ['REQUESTS_CA_BUNDLE'] = cert_path
                self.fixes_applied.append("SSL_CERT_FILE and REQUESTS_CA_BUNDLE environment variables set")
                
            else:
                print(f"⚠️  Certifi certificate file not found: {cert_path}")
                
        except ImportError:
            print("⚠️  Certifi not available - install with: pip install certifi")
        except Exception as e:
            print(f"⚠️  Error configuring certifi: {str(e)}")
            
    def _fix_ssl_environment_variables(self):
        """Set SSL-related environment variables"""
        
        try:
            # Store original values for restoration
            ssl_env_vars = ['SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE']
            
            for var in ssl_env_vars:
                if var in os.environ:
                    self.original_env_vars[var] = os.environ[var]
                    
            # Set to certifi certificate bundle
            cert_path = certifi.where()
            
            for var in ssl_env_vars:
                os.environ[var] = cert_path
                
            self.fixes_applied.append(f"SSL environment variables configured: {', '.join(ssl_env_vars)}")
            
        except Exception as e:
            print(f"⚠️  Error setting SSL environment variables: {str(e)}")
            
    def _fix_ssl_context(self):
        """Configure SSL context programmatically"""
        
        try:
            # Store original SSL context creation function
            self.original_ssl_context = ssl._create_default_https_context
            
            # Create new SSL context using certifi certificates
            def create_ssl_context():
                context = ssl.create_default_context(cafile=certifi.where())
                return context
            
            # Replace the default SSL context creation
            ssl._create_default_https_context = create_ssl_context
            
            self.fixes_applied.append("SSL context configured to use certifi certificates")
            
        except Exception as e:
            print(f"⚠️  Error configuring SSL context: {str(e)}")
            
    def _disable_ssl_warnings(self):
        """Disable SSL warnings for cleaner output"""
        
        try:
            # Disable urllib3 SSL warnings
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            self.fixes_applied.append("SSL warnings disabled for cleaner test output")
            
        except Exception as e:
            print(f"⚠️  Error disabling SSL warnings: {str(e)}")
            
    def test_ssl_connectivity(self, test_urls=None):
        """Test SSL connectivity to verify fixes are working"""
        
        if test_urls is None:
            test_urls = [
                "https://httpbin.org/get",
                "https://google.com",
                "https://github.com"
            ]
            
        print("\n🧪 Testing SSL connectivity with fixes applied...")
        
        import requests
        
        success_count = 0
        for url in test_urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print(f"✅ {url} - SSL connection successful")
                    success_count += 1
                else:
                    print(f"⚠️  {url} - HTTP {response.status_code}")
                    
            except requests.exceptions.SSLError as e:
                print(f"❌ {url} - SSL Error: {str(e)}")
            except requests.exceptions.Timeout:
                print(f"⏰ {url} - Timeout")
            except Exception as e:
                print(f"💥 {url} - Error: {str(e)}")
                
        success_rate = success_count / len(test_urls)
        print(f"\n📊 SSL Test Results: {success_count}/{len(test_urls)} successful ({success_rate:.1%})")
        
        if success_rate >= 0.8:
            print("✅ SSL fixes appear to be working correctly")
            return True
        else:
            print("⚠️  SSL fixes may not be fully effective")
            return False
            
    def restore_ssl_settings(self):
        """Restore original SSL settings (cleanup)"""
        
        print("\n🔄 Restoring original SSL settings...")
        
        try:
            # Restore SSL context
            if self.original_ssl_context:
                ssl._create_default_https_context = self.original_ssl_context
                print("   • SSL context restored")
                
            # Restore environment variables
            for var, value in self.original_env_vars.items():
                os.environ[var] = value
                print(f"   • {var} restored")
                
            # Remove variables we added
            ssl_vars = ['SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE']
            for var in ssl_vars:
                if var not in self.original_env_vars and var in os.environ:
                    del os.environ[var]
                    print(f"   • {var} removed")
                    
            print("✅ SSL settings restored to original state")
            
        except Exception as e:
            print(f"⚠️  Error restoring SSL settings: {str(e)}")

def apply_ssl_fixes_for_treatment():
    """
    Main function to apply SSL fixes for treatment test
    Returns SSLFixer instance for cleanup
    """
    
    fixer = SSLFixer()
    fixer.apply_ssl_fixes()
    
    # Test that SSL fixes are working
    if fixer.test_ssl_connectivity():
        print("🚀 SSL fixes applied successfully - ready for treatment test")
        return fixer
    else:
        print("⚠️  SSL fixes may not be fully effective - proceeding with caution")
        return fixer

if __name__ == "__main__":
    """Test SSL configuration independently"""
    
    print("🧪 SSL Configuration Test")
    print("=" * 40)
    
    fixer = apply_ssl_fixes_for_treatment()
    
    print("\n" + "=" * 40)
    print("✅ SSL configuration test completed")
    
    # Cleanup
    fixer.restore_ssl_settings()