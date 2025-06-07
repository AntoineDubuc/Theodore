#!/usr/bin/env python3
"""
Test script for real AI company discovery with Claude Sonnet 4
"""

import sys
import os
sys.path.insert(0, 'src')

from dotenv import load_dotenv
load_dotenv(override=True)

from company_discovery import CompanyDiscoveryService
from models import CompanyData, CompanyIntelligenceConfig
from bedrock_client import BedrockClient

def main():
    print('🎉 TESTING REAL AI COMPANY DISCOVERY WITH CLAUDE SONNET 4!')
    print('=' * 70)
    
    # Force the model configuration
    os.environ['BEDROCK_ANALYSIS_MODEL'] = 'us.anthropic.claude-sonnet-4-20250514-v1:0'
    
    # Create fresh config
    config = CompanyIntelligenceConfig()
    print(f'🤖 Model: {config.bedrock_analysis_model}')
    
    test_company = CompanyData(
        name='Visterra Inc',
        website='https://visterrainc.com',
        industry='Biotechnology', 
        business_model='B2B',
        company_description='Biotechnology company focused on developing therapeutic antibodies for cancer treatment and autoimmune diseases'
    )
    
    print(f'🎯 Target: {test_company.name} ({test_company.industry})')
    print(f'📋 Description: {test_company.company_description}')
    print()
    
    try:
        # Test Bedrock client directly first
        print('🧪 Testing Claude access...')
        bedrock_client = BedrockClient(config)
        
        test_prompt = f"Find 3 real biotech companies similar to {test_company.name}, which develops therapeutic antibodies. Include company names and brief reasons why they're similar."
        
        response = bedrock_client.generate_text(test_prompt, max_tokens=300)
        
        if response and len(response) > 50:
            print('✅ Claude is responding!')
            print('AI Response:')
            print(response)
            print()
            
            # Now test full discovery service
            print('🚀 Running full AI discovery pipeline...')
            discovery_service = CompanyDiscoveryService(bedrock_client)
            result = discovery_service.discover_similar_companies(test_company, limit=5)
            
            if result.suggestions:
                print(f'🎉 REAL AI DISCOVERY SUCCESS!')
                print(f'Found {len(result.suggestions)} companies')
                print()
                
                for i, suggestion in enumerate(result.suggestions, 1):
                    print(f'{i}. {suggestion.company_name}')
                    print(f'   Reason: {suggestion.suggested_reason}')
                    print(f'   Website: {suggestion.website_url or "Not provided"}')
                    print(f'   Confidence: {suggestion.confidence_score:.1%}')
                    print()
                    
                print('🌟 These are REAL AI suggestions from Claude!')
                
            else:
                print('❌ No suggestions from discovery service')
        else:
            print(f'❌ Claude not responding properly. Response: "{response}"')
            
    except Exception as e:
        print(f'❌ Error: {e}')
        if 'AccessDeniedException' in str(e):
            print('💡 Model access may still be pending')
        elif 'does not have an agreement' in str(e):
            print('💡 Need to accept model agreement in AWS console')
        else:
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()