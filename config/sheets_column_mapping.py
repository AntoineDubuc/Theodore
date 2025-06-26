"""
Google Sheets column mapping for Theodore company data
Maps CompanyData fields to specific sheet columns
"""

from typing import Dict, Any, List
import json
from datetime import datetime

# Column mapping: CompanyData field -> Sheet column letter
COLUMN_MAPPING = {
    # Basic identification (A-E, fixed structure)
    'id': 'A',                          # ID
    'awards': 'B',                      # Awards  
    'pages_crawled': 'C',               # Pages Crawled
    'crawl_depth': 'D',                 # Crawl Depth
    'crawl_duration': 'E',              # Crawl Duration (seconds)
    
    # Similarity metrics (F-N)
    'company_stage': 'F',               # Company Stage
    'tech_sophistication': 'G',         # Tech Sophistication  
    'geographic_scope': 'H',            # Geographic Scope
    'business_model_type': 'I',         # Business Model Type
    'decision_maker_type': 'J',         # Decision Maker Type
    'sales_complexity': 'K',            # Sales Complexity
    'stage_confidence': 'L',            # Stage Confidence
    'tech_confidence': 'M',             # Tech Confidence
    'industry_confidence': 'N',         # Industry Confidence
    
    # Job listings (O-Q)
    'has_job_listings': 'O',            # Has Job Listings
    'job_listings_count': 'P',          # Job Listings Count
    'job_listings_details': 'Q',        # Job Listings Details
    
    # Business intelligence (R-V)
    'products_services_offered': 'R',   # Products/Services Offered
    'key_decision_makers': 'S',         # Key Decision Makers
    'funding_stage_detailed': 'T',      # Detailed Funding Stage
    'sales_marketing_tools': 'U',       # Sales/Marketing Tools
    'recent_news_events': 'V',          # Recent News/Events
    
    # AI analysis (W-Y)
    'raw_content': 'W',                 # Raw Content
    'ai_summary': 'X',                  # AI Summary
    'embedding': 'Y',                   # Vector Embedding
    
    # Metadata (Z-^)
    'created_at': 'Z',                  # Created At
    'last_updated': 'AA',               # Last Updated
    'name': 'AB',                       # Company Name
    'scrape_status': 'AC',              # Scrape Status
    'scrape_error': 'AD',               # Scrape Error
    'website': 'AE',                    # Website
    
    # Basic company info (`-j)
    'industry': 'AF',                   # Industry
    'business_model': 'AG',             # Business Model
    'company_size': 'AH',               # Company Size
    'tech_stack': 'AI',                 # Tech Stack
    'has_chat_widget': 'AJ',            # Has Chat Widget
    'has_forms': 'AK',                  # Has Forms
    'pain_points': 'AL',                # Pain Points
    'key_services': 'AM',               # Key Services
    'competitive_advantages': 'AN',     # Competitive Advantages
    'target_market': 'AO',              # Target Market
    'company_description': 'AP',        # Company Description
    'value_proposition': 'AQ',          # Value Proposition
    'founding_year': 'AR',              # Founding Year
    'location': 'AS',                   # Location
    'employee_count_range': 'AT',       # Employee Count Range
    'company_culture': 'AU',            # Company Culture
    'funding_status': 'AV',             # Funding Status
    'social_media': 'AW',               # Social Media
    'contact_info': 'AX',               # Contact Info
    'leadership_team': 'AY',            # Leadership Team
    'recent_news': 'AZ',                # Recent News
    'certifications': 'BA',             # Certifications
    'partnerships': 'BB',               # Partnerships
    
    # NEW: SaaS Classification fields (BC-BG)
    'saas_classification': 'BC',        # SaaS Classification
    'classification_confidence': 'BD',  # Classification Confidence
    'classification_justification': 'BE', # Classification Justification
    'classification_timestamp': 'BF',   # Classification Timestamp
    'is_saas': 'BG',                    # Is SaaS
    
    # NEW: Token tracking fields (BH-BK)
    'total_input_tokens': 'BH',         # Total Input Tokens
    'total_output_tokens': 'BI',        # Total Output Tokens
    'total_cost_usd': 'BJ',             # Total Cost USD
    'llm_calls_breakdown': 'BK',        # LLM Calls Breakdown
    
    # NEW: Additional crawling fields (BL-BP)
    'scraped_urls': 'BL',               # Scraped URLs
    'llm_prompts_sent': 'BM',           # LLM Prompts Sent
    'page_selection_prompt': 'BN',      # Page Selection Prompt
    'content_analysis_prompt': 'BO',    # Content Analysis Prompt
    'business_model_framework': 'BP',   # David's Business Model Framework
}

def format_value_for_sheet(value: Any) -> str:
    """Convert a Python value to a string suitable for Google Sheets"""
    if value is None:
        return ""
    elif isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    elif isinstance(value, (list, dict)):
        return json.dumps(value, default=str)
    elif isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, float):
        return f"{value:.6f}"  # 6 decimal places for confidence scores
    else:
        return str(value)

def company_data_to_sheet_row(company_data: Any) -> Dict[str, str]:
    """Convert CompanyData object to a row for Google Sheets"""
    row_data = {}
    
    # Handle CompanyData object
    if hasattr(company_data, '__dict__'):
        data_dict = company_data.__dict__
    elif hasattr(company_data, 'dict'):
        data_dict = company_data.dict()
    elif hasattr(company_data, 'model_dump'):
        data_dict = company_data.model_dump()
    else:
        data_dict = company_data
    
    # Map each field to its column
    for field_name, column_letter in COLUMN_MAPPING.items():
        value = data_dict.get(field_name)
        formatted_value = format_value_for_sheet(value)
        row_data[column_letter] = formatted_value
    
    return row_data

def create_batch_update_values(companies_data: List[Any], start_row: int = 2) -> List[Dict]:
    """Create batch update values for multiple companies"""
    batch_data = []
    
    for i, company_data in enumerate(companies_data):
        row_number = start_row + i
        row_data = company_data_to_sheet_row(company_data)
        
        # Create individual cell updates
        for column_letter, value in row_data.items():
            if value:  # Only update non-empty values
                batch_data.append({
                    'range': f'Details!{column_letter}{row_number}',
                    'values': [[value]]
                })
    
    return batch_data

def get_column_letter(field_name: str) -> str:
    """Get the column letter for a specific field"""
    return COLUMN_MAPPING.get(field_name, '')

def get_all_columns() -> List[str]:
    """Get all column letters in order"""
    return list(COLUMN_MAPPING.values())

# Cost calculation for different LLM providers
LLM_COSTS = {
    'gemini-2.5-flash': {
        'input_cost_per_token': 0.075 / 1000000,   # $0.075 per 1M input tokens
        'output_cost_per_token': 0.30 / 1000000,   # $0.30 per 1M output tokens
    },
    'gemini-2.5-pro': {
        'input_cost_per_token': 3.50 / 1000000,    # $3.50 per 1M input tokens
        'output_cost_per_token': 10.50 / 1000000,  # $10.50 per 1M output tokens
    },
    'amazon.nova-pro-v1:0': {
        'input_cost_per_token': 0.80 / 1000000,    # $0.80 per 1M input tokens
        'output_cost_per_token': 3.20 / 1000000,   # $3.20 per 1M output tokens
    },
    'gpt-4o-mini': {
        'input_cost_per_token': 0.15 / 1000000,    # $0.15 per 1M input tokens
        'output_cost_per_token': 0.60 / 1000000,   # $0.60 per 1M output tokens
    }
}

def calculate_llm_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost for LLM usage"""
    if model_name not in LLM_COSTS:
        return 0.0
    
    costs = LLM_COSTS[model_name]
    input_cost = input_tokens * costs['input_cost_per_token']
    output_cost = output_tokens * costs['output_cost_per_token']
    
    return input_cost + output_cost

def format_llm_calls_breakdown(llm_calls: List[Dict]) -> str:
    """Format LLM calls breakdown for the sheet"""
    breakdown = []
    
    for call in llm_calls:
        model = call.get('model', 'unknown')
        input_tokens = call.get('input_tokens', 0)
        output_tokens = call.get('output_tokens', 0)
        cost = calculate_llm_cost(model, input_tokens, output_tokens)
        
        breakdown.append({
            'model': model,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost_usd': round(cost, 6),
            'purpose': call.get('purpose', 'analysis')
        })
    
    return json.dumps(breakdown, default=str)