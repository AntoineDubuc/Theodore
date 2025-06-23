#!/usr/bin/env python3
"""
Minimal Business Model Framework Test
Tests David's framework with a single company to validate approach
"""

import os
import sys
sys.path.insert(0, 'src')

from dotenv import load_dotenv
load_dotenv()

from gemini_client import GeminiClient

def test_framework_prompt():
    """Test David's Business Model Framework with sample data"""
    
    # Sample company data (simulated)
    company_analysis = """
Company Name: Stripe
Website: https://stripe.com
Industry: Financial Technology
Business Model: B2B SaaS
Company Description: Stripe provides payment processing infrastructure for online businesses, enabling companies to accept payments, manage subscriptions, and handle complex payment flows.
Value Proposition: Simplified payment processing with developer-friendly APIs that reduce integration complexity and improve payment success rates.
Target Market: Online businesses, e-commerce platforms, subscription services, marketplaces
Products/Services: Payment processing API, subscription billing, marketplace payments, fraud prevention, financial reporting
AI Summary: Stripe is a B2B fintech company that provides payment infrastructure through APIs, targeting developers and businesses who need to process online payments.
"""
    
    # David's Business Model Framework Prompt
    framework_prompt = f"""
You are tasked with creating a concise, human-readable description of a company's business model that characterizes how it delivers value to customers. Follow this structured approach:

**Required Structure:**
[Primary Model Type] ([Brief Value Mechanism Description])

**Primary Model Type - Choose ONE:**
- SaaS - Software as a Service/subscription-based software
- Product Sales - One-time hardware/software product sales  
- Hardware-enabled SaaS - Hardware + recurring software/service fees
- Manufacturing - Mass production and supply contracts
- Enterprise Software - Licensed platforms for large organizations
- Technology Licensing - IP/patent licensing to other companies
- Consulting Services - Professional expertise and advisory services
- Managed Services - Ongoing operational support and management
- Project-based Services - Contract-based project delivery
- Transaction-based - Fees per transaction/usage
- Subscription-based - Recurring access fees
- Marketplace/Platform - Commission on transactions between parties

**Value Mechanism Description - Explain in parentheses HOW the company monetizes:**
Include these elements:
- WHO pays (customer type)
- WHAT they pay for (product/service)  
- HOW pricing works (per-user, per-transaction, fixed fee, etc.)
- WHY customers pay (value received)

**Requirements:**
- Concise: 1-2 sentences maximum
- Specific: Include concrete details about pricing and value
- Customer-centric: Focus on customer perspective and outcomes
- Business-viable: Explain how the model sustains the business

**Company Information:**
{company_analysis}

**Generate the business model description following the exact framework above.**
"""
    
    print("🧪 MINIMAL FRAMEWORK TEST")
    print("=" * 50)
    print("Testing David's Business Model Framework with Stripe")
    print()
    
    try:
        gemini_client = GeminiClient()
        
        print("📤 Sending prompt to Gemini...")
        response = gemini_client.generate_content(
            prompt=framework_prompt,
            model="gemini-2.0-flash-exp"
        )
        
        if response:
            print("✅ SUCCESS!")
            print(f"Framework Output: {response.strip()}")
            print()
            
            # Check if it follows the format
            if "(" in response and ")" in response:
                print("✅ Format Check: Contains parentheses structure")
            else:
                print("⚠️  Format Check: Missing parentheses structure")
            
            # Check length
            if len(response.split()) <= 50:  # Rough 1-2 sentence check
                print("✅ Length Check: Concise (1-2 sentences)")
            else:
                print("⚠️  Length Check: May be too long")
                
            return response
        else:
            print("❌ FAILED: No response from Gemini")
            return None
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None

if __name__ == "__main__":
    test_framework_prompt()