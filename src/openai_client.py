"""
Simple OpenAI Client for Job Listings Analysis
"""

import os
import openai
import logging

logger = logging.getLogger(__name__)

class SimpleOpenAIClient:
    """Simple OpenAI client for LLM analysis"""
    
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        openai.api_key = api_key
        self.client = openai
        logger.info("✅ OpenAI client initialized")
    
    def analyze_content(self, prompt: str) -> str:
        """Analyze content using OpenAI GPT"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a helpful assistant that analyzes web content and URLs. Always follow instructions exactly."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            logger.info(f"📥 OpenAI response: '{result[:100]}...'")
            return result
            
        except Exception as e:
            logger.error(f"💥 OpenAI API call failed: {e}")
            return ""