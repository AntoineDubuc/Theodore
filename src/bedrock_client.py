"""
AWS Bedrock integration for company intelligence analysis
"""

import json
import logging
from typing import List, Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError
from src.models import CompanyData, CompanyIntelligenceConfig

logger = logging.getLogger(__name__)


class BedrockClient:
    """AWS Bedrock client for AI analysis and embeddings"""
    
    def __init__(self, config: CompanyIntelligenceConfig):
        self.config = config
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=config.bedrock_region
        )
        self.embedding_model = config.bedrock_embedding_model
        self.analysis_model = config.bedrock_analysis_model
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding vector for text using Titan"""
        try:
            # Clean and truncate text
            cleaned_text = self._clean_text_for_embedding(text)
            
            body = json.dumps({
                "inputText": cleaned_text
            })
            
            response = self.bedrock_runtime.invoke_model(
                body=body,
                modelId=self.embedding_model,
                accept="application/json",
                contentType="application/json"
            )
            
            response_body = json.loads(response.get('body').read())
            return response_body.get('embedding')
            
        except ClientError as e:
            logger.error(f"Bedrock embedding error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected embedding error: {e}")
            return None
    
    def analyze_company_content(self, company_data: CompanyData) -> Dict[str, Any]:
        """Analyze company content and extract structured intelligence"""
        
        prompt = self._build_analysis_prompt(company_data)
        
        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
            
            response = self.bedrock_runtime.invoke_model(
                body=body,
                modelId=self.analysis_model,
                accept="application/json",
                contentType="application/json"
            )
            
            response_body = json.loads(response.get('body').read())
            analysis_text = response_body['content'][0]['text']
            
            # Parse the structured response
            return self._parse_analysis_response(analysis_text)
            
        except ClientError as e:
            logger.error(f"Bedrock analysis error for {company_data.name}: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected analysis error for {company_data.name}: {e}")
            return {"error": str(e)}
    
    def generate_sector_summary(self, companies: List[CompanyData], sector_name: str) -> str:
        """Generate sector-level insights from multiple companies"""
        
        company_summaries = []
        for company in companies[:10]:  # Limit to first 10 to avoid token limits
            summary = f"- {company.name}: {company.ai_summary or 'No summary'}"
            company_summaries.append(summary)
        
        prompt = f"""
        Analyze this sector: {sector_name}
        
        Companies in this sector:
        {chr(10).join(company_summaries)}
        
        Provide sector-level insights in this JSON format:
        {{
            "sector_overview": "Brief description of this sector",
            "common_pain_points": ["pain1", "pain2", "pain3"],
            "common_technologies": ["tech1", "tech2", "tech3"],
            "market_opportunities": "Key opportunities for sales teams",
            "recommended_approach": "How to approach companies in this sector"
        }}
        
        Focus on actionable insights for sales teams.
        """
        
        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 800,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
            
            response = self.bedrock_runtime.invoke_model(
                body=body,
                modelId=self.analysis_model,
                accept="application/json",
                contentType="application/json"
            )
            
            response_body = json.loads(response.get('body').read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            logger.error(f"Sector summary error for {sector_name}: {e}")
            return f"Error generating sector summary: {str(e)}"
    
    def _build_analysis_prompt(self, company_data: CompanyData) -> str:
        """Build analysis prompt for company intelligence extraction"""
        
        content_preview = (company_data.raw_content or "")[:3000]  # First 3000 chars
        
        prompt = f"""
        Analyze this company's website content and extract structured intelligence:
        
        Company: {company_data.name}
        Website: {company_data.website}
        Content: {content_preview}
        
        Extract the following information in JSON format:
        {{
            "industry": "primary industry/sector (e.g., healthcare, fintech, saas)",
            "business_model": "B2B, B2C, marketplace, or other",
            "company_size": "startup, SMB, or enterprise (based on content tone)",
            "tech_stack": ["technology1", "technology2"],
            "key_services": ["service1", "service2", "service3"],
            "pain_points": ["inferred business challenge1", "challenge2"],
            "target_market": "who they serve",
            "ai_summary": "2-3 sentence summary focused on sales relevance"
        }}
        
        Guidelines:
        - Focus on information useful for sales teams
        - Infer pain points from their solutions/services
        - Detect technologies from mentions, integrations, or job postings
        - Keep summaries actionable and specific
        - If information isn't clear, use "unknown" rather than guessing
        
        Return only valid JSON.
        """
        
        return prompt
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's JSON response into structured data"""
        try:
            # Try to extract JSON from response
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                json_text = response_text[json_start:json_end].strip()
            elif '{' in response_text and '}' in response_text:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_text = response_text[json_start:json_end]
            else:
                # Fallback: return raw response
                return {"ai_summary": response_text, "error": "Could not parse JSON"}
            
            parsed = json.loads(json_text)
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return {"ai_summary": response_text, "error": f"JSON parse error: {str(e)}"}
        except Exception as e:
            logger.error(f"Response parsing error: {e}")
            return {"ai_summary": response_text, "error": f"Parse error: {str(e)}"}
    
    def _clean_text_for_embedding(self, text: str) -> str:
        """Clean and prepare text for embedding generation"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        cleaned = ' '.join(text.split())
        
        # Truncate to embedding model limits (Titan supports ~8000 tokens)
        max_chars = 25000  # Conservative limit
        if len(cleaned) > max_chars:
            cleaned = cleaned[:max_chars] + "..."
        
        return cleaned
    
    def batch_generate_embeddings(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            embedding = self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    def generate_text(self, prompt: str, max_tokens: int = 4000) -> str:
        """Generate text using the LLM for general purpose prompts"""
        try:
            # Check if using Nova (inference profile) or Anthropic model
            if "Nova" in self.analysis_model:
                # Nova API format
                request_body = {
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "inferenceConfig": {
                        "maxTokens": max_tokens,
                        "temperature": 0.7
                    }
                }
            else:
                # Anthropic Claude API format
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.config.bedrock_analysis_model,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            
            # Handle different response formats
            if "Nova" in self.analysis_model:
                # Nova response format
                if response_body.get('output') and response_body['output'].get('message'):
                    content = response_body['output']['message'].get('content', [])
                    if content and len(content) > 0:
                        return content[0].get('text', '')
            else:
                # Anthropic response format
                if response_body.get('content') and len(response_body['content']) > 0:
                    return response_body['content'][0].get('text', '')
            
            return ""
            
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return ""
    
    # Wrapper methods for backward compatibility with other components
    def get_embeddings(self, text: str) -> Optional[List[float]]:
        """
        Wrapper for generate_embedding() - used by similarity_validator.py
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of floats representing the embedding vector
        """
        return self.generate_embedding(text)
    
    def analyze_content(self, content: str) -> str:
        """
        Wrapper for generate_text() - used by similarity_validator.py
        
        Args:
            content: Content/prompt to analyze
            
        Returns:
            Generated analysis text
        """
        return self.generate_text(content)