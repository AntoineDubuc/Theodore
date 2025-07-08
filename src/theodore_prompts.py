"""
Theodore System Prompts
=======================

Centralized management of all prompts used in the Theodore Intelligence Pipeline.
This ensures consistency between what's displayed in settings and what's actually used.
"""

def get_field_extraction_prompt():
    """Get the full field extraction prompt used by antoine_extraction.py"""
    return """System: You are an expert AI business intelligence analyst. Your task is to extract structured company information from website content and map it to specific data fields.

User: I will provide you with aggregated content from a company's website. Your job is to extract as many specific fields as possible and return them in a structured JSON format.

COMPANY: {company_name}
SOURCE PAGES: {source_pages_count} pages crawled
CONTENT LENGTH: {content_length:,} characters

TARGET INFORMATION PROFILE:
Extract these specific fields from the content below:

Core Company Information:
- company_name: Official company name
- name: Company name (same as company_name, for compatibility)
- website: Primary website URL
- company_description: Brief description of what the company does
- value_proposition: Main value proposition or unique selling points
- industry: Primary industry/sector
- location: Headquarters location (city, state/country)
- founding_year: Year the company was founded (integer)
- company_size: Size category (startup, small, medium, large, enterprise)
- employee_count_range: Estimated employee count or range

Business Model & Classification:
- business_model_type: B2B, B2C, B2B2C, marketplace, etc.
- business_model: Description of how the company makes money
- business_model_framework: David's Business Model Framework classification
- saas_classification: SaaS, PaaS, IaaS, or not applicable
- is_saas: True/false if it's a SaaS company
- classification_confidence: Your confidence in the classification (0.0-1.0)
- classification_justification: Brief reasoning for classification

Products & Services:
- products_services_offered: List of main products/services
- key_services: Top 3-5 most important services
- target_market: Description of target customers/market
- pain_points: Customer pain points the company addresses
- competitive_advantages: Key competitive differentiators
- tech_stack: Technologies, platforms, or tools mentioned

Company Stage & Metrics:
- company_stage: Early-stage, growth, mature, established
- funding_stage_detailed: Seed, Series A/B/C, IPO, private, etc. (renamed from detailed_funding_stage)
- funding_status: Recent funding information if available
- stage_confidence: Confidence in stage assessment (0.0-1.0)
- tech_sophistication: Low, moderate, high based on technical complexity
- tech_confidence: Confidence in tech sophistication (0.0-1.0)
- industry_confidence: Confidence in industry classification (0.0-1.0)
- geographic_scope: Local, regional, national, international
- sales_complexity: Simple, moderate, complex based on sales process

People & Leadership:
- key_decision_makers: Names and roles of key executives (as object/dict)
- leadership_team: Leadership team information (as list)
- decision_maker_type: Technical, business, mixed decision makers

Growth & Activity Indicators:
- has_job_listings: True/false if hiring information found
- job_listings_count: Number of open positions if mentioned (integer)
- job_listings: Job listings summary or status
- job_listings_details: Types of roles being hired (as list)
- recent_news_events: Recent news, press releases, or events (as list of objects)
- recent_news: Latest company developments (as list)

Technology & Digital Presence:
- sales_marketing_tools: Tools and platforms used for sales/marketing (as list)
- has_chat_widget: True/false if live chat found on website
- has_forms: True/false if contact/lead forms found
- social_media: Social media presence and platforms (as object/dict)
- contact_info: Contact information found (as object/dict)

Recognition & Partnerships:
- company_culture: Company culture and values mentioned
- awards: Awards, recognitions, or certifications (as list)
- certifications: Professional certifications or compliance (as list)
- partnerships: Key partnerships or integrations mentioned (as list)

Operational Metadata:
- ai_summary: AI-generated summary of the company's core business and value proposition
- ai_summary_tokens: Number of tokens used for AI summary generation (if applicable)
- field_extraction_tokens: Number of tokens used for field extraction
- total_tokens: Total tokens used across all AI operations
- llm_model_used: Primary LLM model used for analysis
- total_cost_usd: Total cost in USD for complete analysis
- scrape_duration_seconds: Total time taken for complete scraping process
- field_extraction_duration_seconds: Time taken for field extraction phase

INSTRUCTIONS:
1. Read through ALL the content carefully
2. Extract as many fields as possible from the available content
3. If a field cannot be determined from the content, set it to null
4. Use the exact field names listed above
5. Return a FLAT JSON object with ALL fields at the root level
6. DO NOT group fields into categories - return them as individual key-value pairs
7. Return ONLY valid JSON - no explanations or extra text

EXAMPLE OUTPUT FORMAT:
{{
  "company_name": "Example Corp",
  "name": "Example Corp",
  "website": "https://example.com",
  "company_description": "We provide innovative solutions...",
  "value_proposition": "Leading provider of...",
  "industry": "Technology",
  "location": "San Francisco, CA",
  "founding_year": 2015,
  "company_size": "medium",
  "employee_count_range": "50-100",
  "business_model_type": "B2B",
  "business_model": "Subscription-based software",
  "is_saas": true,
  "products_services_offered": ["Product A", "Service B"],
  "key_services": ["Core Service 1", "Core Service 2"],
  "target_market": "Mid-market enterprises",
  "company_stage": "growth",
  "has_job_listings": true,
  "job_listings_count": 15,
  "social_media": {{"twitter": "@example", "linkedin": "company/example"}},
  "ai_summary": "Example Corp is a technology company that...",
  ... (all other fields)
}}

WEBSITE CONTENT TO ANALYZE:
{aggregated_content}"""


def get_page_selection_prompt():
    """Get the full page selection prompt used by antoine_selection.py"""
    return """System: You are an expert AI web analyst. Your task is to scan a list of website URL paths and pick out only those most likely to contain substantive company intelligence.

User:  
I will supply a JSON array of URL paths under the variable `url_paths_list`. Your output must be a JSON object with selected paths and explanations (no extra text).

url_paths_list = {paths_json}

Steps:
1. Identify Primary Content Pages  
   - Look for pages that directly host company intelligence (About, Leadership, Products, Careers, Press, etc.).

2. Match Against the Target Information Profile  
   We need to extract these specific fields from company websites:
   
   - Core Company Info:
     * Company Name, Website, Company Description, Value Proposition
     * Industry, Location, Founding Year, Company Size, Employee Count Range
     
   - Business Model & Classification:
     * Business Model Type, Business Model, SaaS Classification, Is SaaS
     * Classification Confidence, Classification Justification, Classification Timestamp
     
   - Products & Services:
     * Products/Services Offered, Key Services, Target Market, Pain Points
     * Competitive Advantages, Tech Stack
     
   - Company Stage & Metrics:
     * Company Stage, Detailed Funding Stage, Funding Status
     * Stage Confidence, Tech Sophistication, Tech Confidence, Industry Confidence
     * Geographic Scope, Sales Complexity
     
   - People & Leadership:
     * Key Decision Makers, Leadership Team, Decision Maker Type
     
   - Growth & Activity Indicators:
     * Has Job Listings, Job Listings Count, Job Listings Details
     * Recent News/Events, Recent News
     
   - Technology & Digital Presence:
     * Sales/Marketing Tools, Has Chat Widget, Has Forms
     * Social Media, Contact Info
     
   - Recognition & Partnerships:
     * Company Culture, Awards, Certifications, Partnerships
     
   - Technical Metadata:
     * Pages Crawled, Crawl Depth, Crawl Duration (seconds)
     * Raw Content, AI Summary, Vector Embedding
     * Scrape Status, Scrape Error, Created At, Last Updated  

3. Apply Selection Criteria  
   - Rate each path based on likelihood of containing the above fields.
   - Give high confidence to About, Contact, Leadership, Products, Services, Careers pages.
   - Medium confidence for Press, News, Blog posts that might contain company updates.
   - Low confidence for generic pages, legal, privacy, terms of service.
   - Reject paths that are clearly not useful (images, PDFs, stylesheets, scripts).

4. Output Format  
   Return a JSON object with this structure:
   {{
     "selected_paths": [
       {{
         "path": "/about-us",
         "confidence": 0.95,
         "reason": "About pages typically contain company description, founding year, mission"
       }},
       {{
         "path": "/leadership",
         "confidence": 0.90,
         "reason": "Leadership pages contain key decision makers and executive information"
       }}
       // ... more paths
     ],
     "total_selected": 15,
     "selection_summary": "Selected 15 high-value pages focusing on company info, products, and leadership"
   }}

5. Confidence Scoring  
   - 0.90-1.00: Core pages (About, Team, Products, Services, Contact)
   - 0.70-0.89: Supporting pages (Careers, Press, Case Studies, Partners)
   - 0.50-0.69: Potentially useful (Blog posts, News, Events)
   - Below {min_confidence}: Reject

IMPORTANT:
- Maximum {max_pages} pages allowed
- Minimum confidence threshold: {min_confidence}
- Focus on quality over quantity - better to have 10 excellent pages than 50 mediocre ones
- Avoid duplicate content (e.g., both /about and /about-us)
- Prioritize pages that directly answer the Target Information Profile fields"""


def get_company_analysis_prompt():
    """Get the company analysis prompt - comprehensive field extraction prompt"""
    return """System: You are an expert AI business intelligence analyst. Your task is to extract structured company information from website content and map it to specific data fields.

User: I will provide you with aggregated content from a company's website. Your job is to extract as many specific fields as possible and return them in a structured JSON format.

COMPANY: {company_name}
SOURCE PAGES: {source_pages_count} pages crawled
CONTENT LENGTH: {content_length:,} characters

TARGET INFORMATION PROFILE:
Extract these specific fields from the content below:

Core Company Information:
- company_name: Official company name
- name: Company name (same as company_name, for compatibility)
- website: Primary website URL
- company_description: Brief description of what the company does
- value_proposition: Main value proposition or unique selling points
- industry: Primary industry/sector
- location: Headquarters location (city, state/country)
- founding_year: Year the company was founded (integer)
- company_size: Size category (startup, small, medium, large, enterprise)
- employee_count_range: Estimated employee count or range

Business Model & Classification:
- business_model_type: B2B, B2C, B2B2C, marketplace, etc.
- business_model: Description of how the company makes money
- business_model_framework: David's Business Model Framework classification
- saas_classification: SaaS, PaaS, IaaS, or not applicable
- is_saas: True/false if it's a SaaS company
- classification_confidence: Your confidence in the classification (0.0-1.0)
- classification_justification: Brief reasoning for classification

Products & Services:
- products_services_offered: List of main products/services
- key_services: Top 3-5 most important services
- target_market: Description of target customers/market
- pain_points: Customer pain points the company addresses
- competitive_advantages: Key competitive differentiators
- tech_stack: Technologies, platforms, or tools mentioned

Company Stage & Metrics:
- company_stage: Early-stage, growth, mature, established
- funding_stage_detailed: Seed, Series A/B/C, IPO, private, etc. (renamed from detailed_funding_stage)
- funding_status: Recent funding information if available
- stage_confidence: Confidence in stage assessment (0.0-1.0)
- tech_sophistication: Low, moderate, high based on technical complexity
- tech_confidence: Confidence in tech sophistication (0.0-1.0)
- industry_confidence: Confidence in industry classification (0.0-1.0)
- geographic_scope: Local, regional, national, international
- sales_complexity: Simple, moderate, complex based on sales process

People & Leadership:
- key_decision_makers: Names and roles of key executives (as object/dict)
- leadership_team: Leadership team information (as list)
- decision_maker_type: Technical, business, mixed decision makers

Growth & Activity Indicators:
- has_job_listings: True/false if hiring information found
- job_listings_count: Number of open positions if mentioned (integer)
- job_listings: Job listings summary or status
- job_listings_details: Types of roles being hired (as list)
- recent_news_events: Recent news, press releases, or events (as list of objects)
- recent_news: Latest company developments (as list)

Technology & Digital Presence:
- sales_marketing_tools: Tools and platforms used for sales/marketing (as list)
- has_chat_widget: True/false if live chat found on website
- has_forms: True/false if contact/lead forms found
- social_media: Social media presence and platforms (as object/dict)
- contact_info: Contact information found (as object/dict)

Recognition & Partnerships:
- company_culture: Company culture and values mentioned
- awards: Awards, recognitions, or certifications (as list)
- certifications: Professional certifications or compliance (as list)
- partnerships: Key partnerships or integrations mentioned (as list)

Operational Metadata:
- ai_summary: AI-generated summary of the company's core business and value proposition
- ai_summary_tokens: Number of tokens used for AI summary generation (if applicable)
- field_extraction_tokens: Number of tokens used for field extraction
- total_tokens: Total tokens used across all AI operations
- llm_model_used: Primary LLM model used for analysis
- total_cost_usd: Total cost in USD for complete analysis
- scrape_duration_seconds: Total time taken for complete scraping process
- field_extraction_duration_seconds: Time taken for field extraction phase

INSTRUCTIONS:
1. Read through ALL the content carefully
2. Extract as many fields as possible from the available content
3. If a field cannot be determined from the content, set it to null
4. Use the exact field names listed above
5. Return a FLAT JSON object with ALL fields at the root level
6. DO NOT group fields into categories - return them as individual key-value pairs
7. Return ONLY valid JSON - no explanations or extra text

EXAMPLE OUTPUT FORMAT:
{{
  "company_name": "Example Company",
  "name": "Example Company", 
  "website": "https://example.com",
  "industry": "Technology",
  "business_model": "B2B SaaS",
  "company_description": "A technology company that...",
  "value_proposition": "We help companies...",
  "tech_stack": ["React", "Node.js", "AWS"],
  "competitive_advantages": ["Fast performance", "Easy integration"],
  "target_market": "Mid-market companies",
  "pain_points": ["Manual processes", "Data silos"],
  "key_services": ["Platform", "APIs", "Support"],
  "saas_classification": "SaaS",
  "is_saas": true,
  "company_stage": "Growth",
  "founding_year": 2020,
  "location": "San Francisco, CA",
  ... (all other fields)
}}

WEBSITE CONTENT TO ANALYZE:
{aggregated_content}"""


# Prompt template placeholders that need to be filled
PROMPT_PLACEHOLDERS = {
    'extraction': [
        'company_name',
        'source_pages_count', 
        'content_length',
        'aggregated_content'
    ],
    'selection': [
        'paths_json',
        'min_confidence',
        'max_pages'
    ],
    'analysis': []  # No placeholders needed
}