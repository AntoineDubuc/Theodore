"""
Theodore Research Prompt Library

Predefined prompt templates for structured company research based on PRD requirements.
Supports cost estimation, structured output formats, and dynamic company context.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class OutputFormat(str, Enum):
    """Supported output formats for research prompts"""
    JSON = "json"
    TEXT = "text"
    STRUCTURED = "structured"

@dataclass
class ResearchPrompt:
    """Individual research prompt with metadata"""
    id: str
    name: str
    description: str
    prompt_template: str
    output_format: OutputFormat
    estimated_tokens: int
    category: str
    requires_website: bool = True
    requires_domain: bool = True

class ResearchPromptLibrary:
    """Centralized library of predefined research prompts"""
    
    def __init__(self):
        self.prompts = self._initialize_prompts()
    
    def _initialize_prompts(self) -> Dict[str, ResearchPrompt]:
        """Initialize all predefined research prompts"""
        
        prompts = {
            # Job Listings & Hiring
            "job_listings": ResearchPrompt(
                id="job_listings",
                name="Job Listings Analysis",
                description="Identify current open positions and hiring trends",
                prompt_template="""
Analyze {company_name} (website: {website}) for current job listings and hiring activity.

Please provide a structured analysis including:
1. Current open positions (if any)
2. Most frequently posted roles
3. Required skills and technologies
4. Growth indicators from hiring patterns
5. Remote work policies

Focus on roles in sales, marketing, engineering, and executive positions.
If no careers page is found, check LinkedIn or other job boards mentioned on their site.

Respond in JSON format with clear boolean indicators for active hiring.
""",
                output_format=OutputFormat.JSON,
                estimated_tokens=800,
                category="hiring"
            ),
            
            # Decision Makers
            "decision_makers": ResearchPrompt(
                id="decision_makers",
                name="Key Decision Makers",
                description="Identify leadership team and decision makers",
                prompt_template="""
Research {company_name} (website: {website}) to identify key decision makers and leadership.

Please identify:
1. CEO/Founder information
2. CMO/Head of Marketing
3. Head of Product/CTO
4. VP of Sales/Revenue
5. Other C-level executives

For each person found, include:
- Full name and title
- Professional background (if available)
- LinkedIn presence
- Key responsibilities

Focus on finding contact information or LinkedIn profiles where possible.
Respond in JSON format with structured leadership data.
""",
                output_format=OutputFormat.JSON,
                estimated_tokens=600,
                category="leadership"
            ),
            
            # Products & Services
            "products_services": ResearchPrompt(
                id="products_services",
                name="Products & Services Analysis",
                description="Comprehensive analysis of company offerings",
                prompt_template="""
Analyze {company_name} (website: {website}) to understand their products and services.

Please provide:
1. Core products/services offered
2. Target markets and customer segments
3. Pricing models (if available)
4. Unique value propositions
5. Competitive advantages
6. Recent product launches or updates

Include specific details about features, benefits, and positioning.
Look for case studies, customer testimonials, or success stories.

Respond in JSON format with detailed product information.
""",
                output_format=OutputFormat.JSON,
                estimated_tokens=900,
                category="products"
            ),
            
            # Funding & Investment
            "funding_stage": ResearchPrompt(
                id="funding_stage",
                name="Funding & Investment Analysis",
                description="Research funding history and investment stage",
                prompt_template="""
Research the funding stage and investment history of {company_name} (website: {website}).

Please determine:
1. Current funding stage (seed, Series A/B/C, IPO, etc.)
2. Total funding raised (if available)
3. Recent investment rounds
4. Key investors and venture capital firms
5. Valuation information (if public)
6. Financial health indicators

Look for press releases, investor pages, or news about funding.
If no funding information is found, indicate whether the company appears to be:
- Bootstrap/self-funded
- Revenue-generating
- Seeking investment

Respond in JSON format with funding details.
""",
                output_format=OutputFormat.JSON,
                estimated_tokens=700,
                category="finance"
            ),
            
            # Technology Stack
            "tech_stack": ResearchPrompt(
                id="tech_stack",
                name="Technology Stack Analysis",
                description="Identify technologies and tools used",
                prompt_template="""
Analyze {company_name} (website: {website}) to identify their technology stack and tools.

Please research:
1. Programming languages and frameworks
2. Cloud platforms and infrastructure
3. Marketing and sales tools
4. Analytics and tracking tools
5. Security certifications
6. Integration capabilities

Look for:
- Job postings mentioning technologies
- Stack overflow profiles
- GitHub presence
- Technology partner pages
- Security/compliance badges

Respond in JSON format categorizing technologies by type.
""",
                output_format=OutputFormat.JSON,
                estimated_tokens=750,
                category="technology"
            ),
            
            # Recent News & Events
            "recent_news": ResearchPrompt(
                id="recent_news",
                name="Recent News & Events",
                description="Latest company news, announcements, and milestones",
                prompt_template="""
Research recent news and events for {company_name} (website: {website}).

Please find:
1. Recent press releases or announcements
2. Product launches or major updates
3. Partnership announcements
4. Awards or recognition
5. Media coverage or interviews
6. Conference appearances or speaking events

Focus on news from the last 6 months that indicates:
- Company growth or expansion
- Strategic partnerships
- Market positioning changes
- Thought leadership activities

Include dates and sources where possible.
Respond in JSON format with chronological news items.
""",
                output_format=OutputFormat.JSON,
                estimated_tokens=650,
                category="news"
            ),
            
            # Competitive Analysis
            "competitive_landscape": ResearchPrompt(
                id="competitive_landscape",
                name="Competitive Landscape",
                description="Identify competitors and market positioning",
                prompt_template="""
Analyze the competitive landscape for {company_name} (website: {website}).

Please identify:
1. Direct competitors mentioned or implied
2. Market category/space they compete in
3. Competitive advantages claimed
4. Differentiation factors
5. Market positioning strategy
6. Partnership ecosystem

Look for:
- Comparison pages or competitive sections
- Customer testimonials mentioning alternatives
- Industry reports or analyst mentions
- G2/Capterra competitor listings

Respond in JSON format with competitive intelligence.
""",
                output_format=OutputFormat.JSON,
                estimated_tokens=800,
                category="competitive"
            ),
            
            # Customer Base
            "customer_analysis": ResearchPrompt(
                id="customer_analysis",
                name="Customer Base Analysis",
                description="Understand target customers and use cases",
                prompt_template="""
Research the customer base and target market for {company_name} (website: {website}).

Please analyze:
1. Primary customer segments
2. Company size of typical customers
3. Industries served
4. Geographic markets
5. Use cases and applications
6. Customer success stories

Look for:
- Customer logos and case studies
- Testimonials and reviews
- Pricing tiers indicating customer types
- Sales materials or demos

Respond in JSON format with customer insights.
""",
                output_format=OutputFormat.JSON,
                estimated_tokens=700,
                category="customers"
            )
        }
        
        return prompts
    
    def get_prompt(self, prompt_id: str) -> Optional[ResearchPrompt]:
        """Get a specific prompt by ID"""
        return self.prompts.get(prompt_id)
    
    def get_prompts_by_category(self, category: str) -> List[ResearchPrompt]:
        """Get all prompts in a specific category"""
        return [prompt for prompt in self.prompts.values() if prompt.category == category]
    
    def get_all_prompts(self) -> List[ResearchPrompt]:
        """Get all available prompts"""
        return list(self.prompts.values())
    
    def get_prompt_categories(self) -> List[str]:
        """Get all available categories"""
        return list(set(prompt.category for prompt in self.prompts.values()))
    
    def format_prompt(self, prompt_id: str, company_name: str, website: str, **kwargs) -> str:
        """Format a prompt with company-specific information"""
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            raise ValueError(f"Prompt '{prompt_id}' not found")
        
        # Basic template variables
        template_vars = {
            "company_name": company_name,
            "website": website,
            **kwargs
        }
        
        return prompt.prompt_template.format(**template_vars)
    
    def estimate_total_cost(self, selected_prompts: List[str], token_price_per_1k: float = 0.011) -> Dict[str, Any]:
        """Estimate total cost for selected prompts"""
        total_tokens = 0
        prompt_details = []
        
        for prompt_id in selected_prompts:
            prompt = self.get_prompt(prompt_id)
            if prompt:
                total_tokens += prompt.estimated_tokens
                prompt_details.append({
                    "prompt_id": prompt_id,
                    "name": prompt.name,
                    "estimated_tokens": prompt.estimated_tokens,
                    "estimated_cost": (prompt.estimated_tokens / 1000) * token_price_per_1k
                })
        
        total_cost = (total_tokens / 1000) * token_price_per_1k
        
        return {
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "cost_per_company": total_cost,
            "prompt_details": prompt_details,
            "token_price_per_1k": token_price_per_1k
        }
    
    def get_prompt_summary(self) -> Dict[str, Any]:
        """Get summary of all available prompts"""
        categories = {}
        total_prompts = len(self.prompts)
        
        for prompt in self.prompts.values():
            if prompt.category not in categories:
                categories[prompt.category] = {
                    "count": 0,
                    "prompts": [],
                    "total_tokens": 0
                }
            
            categories[prompt.category]["count"] += 1
            categories[prompt.category]["prompts"].append({
                "id": prompt.id,
                "name": prompt.name,
                "description": prompt.description,
                "tokens": prompt.estimated_tokens
            })
            categories[prompt.category]["total_tokens"] += prompt.estimated_tokens
        
        return {
            "total_prompts": total_prompts,
            "categories": categories,
            "total_estimated_tokens": sum(p.estimated_tokens for p in self.prompts.values())
        }

# Global instance for easy access
research_prompt_library = ResearchPromptLibrary()