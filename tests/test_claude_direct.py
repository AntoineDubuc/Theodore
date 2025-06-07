#!/usr/bin/env python3
"""
Direct test of Claude Sonnet 4 access
"""

import boto3
import json
import os
from dotenv import load_dotenv

def test_claude_direct():
    # Load environment
    load_dotenv(override=True)
    
    print('🧪 DIRECT CLAUDE SONNET 4 TEST')
    print('=' * 40)
    
    model_id = 'us.anthropic.claude-sonnet-4-20250514-v1:0'
    print(f'Model: {model_id}')
    print()
    
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-west-2')
        
        prompt = """You are helping find biotech companies similar to Visterra Inc. 

Visterra Inc is a biotechnology company focused on developing therapeutic antibodies for cancer treatment and autoimmune diseases.

Please suggest 3 real biotech companies that are similar to Visterra Inc. For each company, provide:
1. Company name
2. Website URL (if known)
3. Brief reason why they're similar

Respond in JSON format:
{
  "similar_companies": [
    {
      "company_name": "Company Name",
      "website_url": "https://example.com",
      "reason": "Brief explanation"
    }
  ]
}"""

        request_body = {
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 500,
            'temperature': 0.7,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }
        
        print('🚀 Calling Claude Sonnet 4...')
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body),
            contentType='application/json',
            accept='application/json'
        )
        
        response_body = json.loads(response['body'].read())
        
        if response_body.get('content'):
            result = response_body['content'][0].get('text', '')
            print('✅ CLAUDE SONNET 4 IS WORKING!')
            print()
            print('🤖 AI Response:')
            print(result)
            print()
            print('🎉 SUCCESS! Real AI company discovery is possible!')
            
        else:
            print('❌ No content in response')
            print('Response:', response_body)
            
    except Exception as e:
        print(f'❌ Error: {e}')
        
        if 'AccessDeniedException' in str(e):
            print()
            print('💡 Access denied - model agreement may still be pending')
            print('💡 Check AWS Bedrock console for model access status')
        elif 'does not have an agreement' in str(e):
            print()
            print('💡 Need to accept model agreement in AWS Bedrock console')
        elif 'ValidationException' in str(e):
            print()
            print('💡 Model ID validation error - check if profile is available')

if __name__ == '__main__':
    test_claude_direct()