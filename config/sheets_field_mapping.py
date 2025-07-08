"""
Google Sheets field mapping for CompanyData model
Maps all CompanyData fields to Google Sheets columns for Option 1 implementation
"""

from typing import Dict, List, Any
from enum import Enum

class SheetType(Enum):
    PROGRESS_TRACKING = "Progress Tracking"
    COMPLETE_DATA = "Complete Research Data"

# Main progress tracking sheet columns (user-friendly)
PROGRESS_SHEET_COLUMNS = {
    'A': {'field': 'name', 'header': 'Company Name', 'type': 'input'},
    'B': {'field': 'website', 'header': 'Website', 'type': 'input'},  
    'C': {'field': 'status', 'header': 'Status', 'type': 'auto'},
    'D': {'field': 'progress', 'header': 'Progress', 'type': 'auto'},
    'E': {'field': 'research_date', 'header': 'Research Date', 'type': 'auto'},
    'F': {'field': 'industry', 'header': 'Industry', 'type': 'auto'},
    'G': {'field': 'company_stage', 'header': 'Stage', 'type': 'auto'},
    'H': {'field': 'tech_sophistication', 'header': 'Tech Level', 'type': 'auto'},
    'I': {'field': 'ai_summary', 'header': 'AI Summary', 'type': 'auto'},
    'J': {'field': 'full_data_link', 'header': 'View Details', 'type': 'link'},
    'K': {'field': 'id', 'header': 'Pinecone ID', 'type': 'auto'},
    'L': {'field': 'scrape_error', 'header': 'Error Notes', 'type': 'auto'}
}

# Complete data sheet - all CompanyData fields
COMPLETE_DATA_COLUMNS = {
    # Core Identity (A-F)
    'A': {'field': 'id', 'header': 'ID', 'type': 'string'},
    'B': {'field': 'name', 'header': 'Company Name', 'type': 'string'},
    'C': {'field': 'website', 'header': 'Website', 'type': 'string'},
    'D': {'field': 'industry', 'header': 'Industry', 'type': 'string'},
    'E': {'field': 'business_model', 'header': 'Business Model', 'type': 'string'},
    'F': {'field': 'company_size', 'header': 'Company Size', 'type': 'string'},
    
    # Technology Stack (G-I)
    'G': {'field': 'tech_stack', 'header': 'Tech Stack', 'type': 'list'},
    'H': {'field': 'has_chat_widget', 'header': 'Has Chat Widget', 'type': 'boolean'},
    'I': {'field': 'has_forms', 'header': 'Has Forms', 'type': 'boolean'},
    
    # Business Intelligence (J-P)
    'J': {'field': 'pain_points', 'header': 'Pain Points', 'type': 'list'},
    'K': {'field': 'key_services', 'header': 'Key Services', 'type': 'list'},
    'L': {'field': 'competitive_advantages', 'header': 'Competitive Advantages', 'type': 'list'},
    'M': {'field': 'target_market', 'header': 'Target Market', 'type': 'string'},
    'N': {'field': 'company_description', 'header': 'Company Description', 'type': 'string'},
    'O': {'field': 'value_proposition', 'header': 'Value Proposition', 'type': 'string'},
    'P': {'field': 'founding_year', 'header': 'Founding Year', 'type': 'integer'},
    
    # Company Details (Q-Z)
    'Q': {'field': 'location', 'header': 'Location', 'type': 'string'},
    'R': {'field': 'employee_count_range', 'header': 'Employee Count Range', 'type': 'string'},
    'S': {'field': 'company_culture', 'header': 'Company Culture', 'type': 'string'},
    'T': {'field': 'funding_status', 'header': 'Funding Status', 'type': 'string'},
    'U': {'field': 'social_media', 'header': 'Social Media', 'type': 'dict'},
    'V': {'field': 'contact_info', 'header': 'Contact Info', 'type': 'dict'},
    'W': {'field': 'leadership_team', 'header': 'Leadership Team', 'type': 'list'},
    'X': {'field': 'recent_news', 'header': 'Recent News', 'type': 'list'},
    'Y': {'field': 'certifications', 'header': 'Certifications', 'type': 'list'},
    'Z': {'field': 'partnerships', 'header': 'Partnerships', 'type': 'list'},
    
    # Extended Company Details (AA-AC)
    'AA': {'field': 'awards', 'header': 'Awards', 'type': 'list'},
    'AB': {'field': 'pages_crawled', 'header': 'Pages Crawled', 'type': 'list'},
    'AC': {'field': 'crawl_depth', 'header': 'Crawl Depth', 'type': 'integer'},
    'AD': {'field': 'crawl_duration', 'header': 'Crawl Duration (seconds)', 'type': 'float'},
    
    # Similarity Metrics (AE-AM)
    'AE': {'field': 'company_stage', 'header': 'Company Stage', 'type': 'string'},
    'AF': {'field': 'tech_sophistication', 'header': 'Tech Sophistication', 'type': 'string'},
    'AG': {'field': 'geographic_scope', 'header': 'Geographic Scope', 'type': 'string'},
    'AH': {'field': 'business_model_type', 'header': 'Business Model Type', 'type': 'string'},
    'AI': {'field': 'decision_maker_type', 'header': 'Decision Maker Type', 'type': 'string'},
    'AJ': {'field': 'sales_complexity', 'header': 'Sales Complexity', 'type': 'string'},
    'AK': {'field': 'stage_confidence', 'header': 'Stage Confidence', 'type': 'float'},
    'AL': {'field': 'tech_confidence', 'header': 'Tech Confidence', 'type': 'float'},
    'AM': {'field': 'industry_confidence', 'header': 'Industry Confidence', 'type': 'float'},
    
    # Batch Research Intelligence (AN-AT)
    'AN': {'field': 'has_job_listings', 'header': 'Has Job Listings', 'type': 'boolean'},
    'AO': {'field': 'job_listings_count', 'header': 'Job Listings Count', 'type': 'integer'},
    'AP': {'field': 'job_listings_details', 'header': 'Job Listings Details', 'type': 'list_dict'},
    'AQ': {'field': 'products_services_offered', 'header': 'Products/Services Offered', 'type': 'list'},
    'AR': {'field': 'key_decision_makers', 'header': 'Key Decision Makers', 'type': 'dict'},
    'AS': {'field': 'funding_stage_detailed', 'header': 'Detailed Funding Stage', 'type': 'string'},
    'AT': {'field': 'sales_marketing_tools', 'header': 'Sales/Marketing Tools', 'type': 'list'},
    'AU': {'field': 'recent_news_events', 'header': 'Recent News/Events', 'type': 'list_dict'},
    
    # AI Analysis (AV-AX)
    'AV': {'field': 'raw_content', 'header': 'Raw Content', 'type': 'string'},
    'AW': {'field': 'ai_summary', 'header': 'AI Summary', 'type': 'string'},
    'AX': {'field': 'embedding', 'header': 'Vector Embedding', 'type': 'list_float'},
    
    # System Metadata (AY-BB)
    'AY': {'field': 'created_at', 'header': 'Created At', 'type': 'datetime'},
    'AZ': {'field': 'last_updated', 'header': 'Last Updated', 'type': 'datetime'},
    'BA': {'field': 'scrape_status', 'header': 'Scrape Status', 'type': 'string'},
    'BB': {'field': 'scrape_error', 'header': 'Scrape Error', 'type': 'string'},
    
    # SaaS Classification fields (BC-BH)
    'BC': {'field': 'saas_classification', 'header': 'SaaS Classification', 'type': 'string'},
    'BD': {'field': 'classification_confidence', 'header': 'Classification Confidence', 'type': 'float'},
    'BE': {'field': 'classification_justification', 'header': 'Classification Justification', 'type': 'string'},
    'BF': {'field': 'classification_timestamp', 'header': 'Classification Timestamp', 'type': 'datetime'},
    'BG': {'field': 'classification_model_version', 'header': 'Classification Model Version', 'type': 'string'},
    'BH': {'field': 'is_saas', 'header': 'Is SaaS', 'type': 'boolean'},
    
    # Additional missing fields (BI-BS)
    'BI': {'field': 'business_model_framework', 'header': 'Business Model Framework', 'type': 'string'},
    'BJ': {'field': 'job_listings', 'header': 'Job Listings Summary', 'type': 'string'},
    'BK': {'field': 'scraped_urls', 'header': 'Scraped URLs', 'type': 'list'},
    'BL': {'field': 'scraped_content_details', 'header': 'Scraped Content Details', 'type': 'dict'},
    'BM': {'field': 'llm_prompts_sent', 'header': 'LLM Prompts Sent', 'type': 'list_dict'},
    'BN': {'field': 'page_selection_prompt', 'header': 'Page Selection Prompt', 'type': 'string'},
    'BO': {'field': 'content_analysis_prompt', 'header': 'Content Analysis Prompt', 'type': 'string'},
    'BP': {'field': 'llm_calls_breakdown', 'header': 'LLM Calls Breakdown', 'type': 'list_dict'},
    
    # Token usage and cost tracking (BQ-BS)
    'BQ': {'field': 'total_input_tokens', 'header': 'Total Input Tokens', 'type': 'integer'},
    'BR': {'field': 'total_output_tokens', 'header': 'Total Output Tokens', 'type': 'integer'},
    'BS': {'field': 'total_cost_usd', 'header': 'Total Cost USD', 'type': 'float'}
}

# Field type conversion functions
def convert_value_for_sheets(value: Any, field_type: str) -> str:
    """Convert Python values to Google Sheets compatible strings"""
    if value is None:
        return ""
    
    if field_type == 'string':
        return str(value)
    elif field_type == 'integer':
        return str(value) if isinstance(value, int) else ""
    elif field_type == 'float':
        return str(value) if isinstance(value, (int, float)) else ""
    elif field_type == 'boolean':
        return "TRUE" if value else "FALSE"
    elif field_type == 'datetime':
        return value.isoformat() if hasattr(value, 'isoformat') else str(value)
    elif field_type == 'list':
        if isinstance(value, list):
            if not value:  # Empty list
                return ""
            return "; ".join(str(item) for item in value)
        return str(value)
    elif field_type == 'dict':
        if isinstance(value, dict):
            if not value:  # Empty dict
                return ""
            return "; ".join(f"{k}: {v}" for k, v in value.items())
        return str(value)
    elif field_type == 'list_dict':
        if isinstance(value, list):
            if not value:  # Empty list
                return ""
            if value and isinstance(value[0], dict):
                return "; ".join(f"{item}" for item in value)
        return str(value)
    elif field_type == 'list_float':
        if isinstance(value, list):
            return f"[{len(value)} dimensions]"  # Don't export full embedding
        return ""
    else:
        return str(value)

def get_progress_sheet_headers() -> List[str]:
    """Get headers for the progress tracking sheet"""
    return [PROGRESS_SHEET_COLUMNS[col]['header'] for col in sorted(PROGRESS_SHEET_COLUMNS.keys())]

def get_complete_data_headers() -> List[str]:
    """Get headers for the complete data sheet"""
    return [COMPLETE_DATA_COLUMNS[col]['header'] for col in sorted(COMPLETE_DATA_COLUMNS.keys())]

def get_field_mapping(sheet_type: SheetType) -> Dict[str, Dict[str, Any]]:
    """Get the appropriate field mapping for the sheet type"""
    if sheet_type == SheetType.PROGRESS_TRACKING:
        return PROGRESS_SHEET_COLUMNS
    elif sheet_type == SheetType.COMPLETE_DATA:
        return COMPLETE_DATA_COLUMNS
    else:
        raise ValueError(f"Unknown sheet type: {sheet_type}")

def company_data_to_progress_row(company_data, row_number: int) -> List[str]:
    """Convert CompanyData to progress tracking sheet row"""
    row = []
    
    for col in sorted(PROGRESS_SHEET_COLUMNS.keys()):
        field_info = PROGRESS_SHEET_COLUMNS[col]
        field_name = field_info['field']
        
        if field_name == 'full_data_link':
            # Create hyperlink to Details sheet
            link_formula = f'=HYPERLINK("Details!A{row_number}", "View Details")'
            row.append(link_formula)
        elif field_name == 'progress':
            # Calculate progress percentage based on populated fields
            progress = calculate_completion_percentage(company_data)
            row.append(f"{progress}%")
        elif field_name == 'research_date':
            # Use last_updated timestamp
            value = getattr(company_data, 'last_updated', None)
            row.append(convert_value_for_sheets(value, 'datetime'))
        else:
            # Standard field mapping
            value = getattr(company_data, field_name, None)
            row.append(convert_value_for_sheets(value, 'string'))
    
    return row

def company_data_to_complete_row(company_data) -> List[str]:
    """Convert CompanyData to complete data sheet row"""
    row = []
    
    for col in sorted(COMPLETE_DATA_COLUMNS.keys()):
        field_info = COMPLETE_DATA_COLUMNS[col]
        field_name = field_info['field']
        field_type = field_info['type']
        
        value = getattr(company_data, field_name, None)
        row.append(convert_value_for_sheets(value, field_type))
    
    return row

def calculate_completion_percentage(company_data) -> int:
    """Calculate what percentage of fields are populated"""
    total_fields = len(COMPLETE_DATA_COLUMNS)
    populated_fields = 0
    
    for field_info in COMPLETE_DATA_COLUMNS.values():
        field_name = field_info['field']
        value = getattr(company_data, field_name, None)
        
        if value is not None and value != "" and value != []:
            if isinstance(value, dict) and value:
                populated_fields += 1
            elif not isinstance(value, dict):
                populated_fields += 1
    
    return int((populated_fields / total_fields) * 100)

# Sheet configuration
SHEET_CONFIG = {
    'progress_sheet_name': 'Companies',  # Changed to match existing sheet
    'complete_data_sheet_name': 'Details',  # Changed to match existing sheet
    'header_row': 1,
    'data_start_row': 2,
    'freeze_rows': 1,  # Freeze header row
    'freeze_columns': 2,  # Freeze company name and website columns
}

# Google Sheets formatting
SHEET_FORMATTING = {
    'header_format': {
        'background_color': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
        'text_color': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
        'bold': True
    },
    'status_colors': {
        'pending': {'red': 1.0, 'green': 0.8, 'blue': 0.0},      # Yellow
        'processing': {'red': 0.0, 'green': 0.8, 'blue': 1.0},   # Blue  
        'completed': {'red': 0.0, 'green': 0.8, 'blue': 0.0},    # Green
        'failed': {'red': 1.0, 'green': 0.0, 'blue': 0.0}        # Red
    }
}