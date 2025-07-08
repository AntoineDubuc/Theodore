#!/usr/bin/env python3
"""
Test Helpers for Complete Field Coverage
=======================================

Provides functions to ensure all CompanyData fields are properly saved
to both Google Sheets and Pinecone.
"""

import sys
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.models import CompanyData
from config.sheets_field_mapping import (
    COMPLETE_DATA_COLUMNS,
    convert_value_for_sheets,
    get_complete_data_headers
)


def get_all_company_headers() -> List[str]:
    """Get ALL headers for the complete data sheet (54 fields)"""
    # Sort columns by their letter (A, B, C, ..., AA, AB, ..., BB)
    sorted_cols = sorted(COMPLETE_DATA_COLUMNS.keys(), 
                        key=lambda x: (len(x), x))
    
    headers = []
    for col in sorted_cols:
        headers.append(COMPLETE_DATA_COLUMNS[col]['header'])
    
    return headers


def company_data_to_complete_row(company: CompanyData) -> List[str]:
    """Convert CompanyData to a complete row with all 54 fields"""
    # Sort columns by their letter
    sorted_cols = sorted(COMPLETE_DATA_COLUMNS.keys(), 
                        key=lambda x: (len(x), x))
    
    row = []
    for col in sorted_cols:
        field_info = COMPLETE_DATA_COLUMNS[col]
        field_name = field_info['field']
        field_type = field_info['type']
        
        # Get the value from company data
        if hasattr(company, field_name):
            value = getattr(company, field_name)
        else:
            value = None
        
        # Convert to sheets-compatible format
        converted_value = convert_value_for_sheets(value, field_type)
        row.append(converted_value)
    
    return row


def get_field_coverage_report(company: CompanyData) -> Dict[str, Any]:
    """Generate a detailed report of which fields have data"""
    report = {
        'total_fields': 0,
        'populated_fields': 0,
        'empty_fields': 0,
        'field_details': {},
        'coverage_by_category': {}
    }
    
    # Categories for grouping fields
    categories = {
        'Core Identity': ['id', 'name', 'website', 'industry', 'business_model', 'company_size'],
        'Technology': ['tech_stack', 'has_chat_widget', 'has_forms', 'tech_sophistication'],
        'Business Intelligence': ['pain_points', 'key_services', 'competitive_advantages', 
                                 'target_market', 'company_description', 'value_proposition'],
        'Company Details': ['founding_year', 'location', 'employee_count_range', 
                           'company_culture', 'funding_status', 'social_media', 
                           'contact_info', 'leadership_team'],
        'Extended Info': ['recent_news', 'certifications', 'partnerships', 'awards',
                         'recent_news_events', 'job_listings_details'],
        'Sales Intelligence': ['has_job_listings', 'job_listings_count', 'products_services_offered',
                              'key_decision_makers', 'funding_stage_detailed', 'sales_marketing_tools'],
        'Similarity Metrics': ['company_stage', 'geographic_scope', 'business_model_type',
                              'decision_maker_type', 'sales_complexity'],
        'AI Analysis': ['raw_content', 'ai_summary', 'embedding'],
        'Metadata': ['pages_crawled', 'crawl_duration', 'scrape_status', 'created_at', 'last_updated']
    }
    
    # Initialize category counts
    for category in categories:
        report['coverage_by_category'][category] = {
            'total': 0,
            'populated': 0,
            'percentage': 0.0
        }
    
    # Check each field
    for col, field_info in COMPLETE_DATA_COLUMNS.items():
        field_name = field_info['field']
        field_header = field_info['header']
        
        report['total_fields'] += 1
        
        # Get field value
        has_value = False
        value_preview = None
        
        if hasattr(company, field_name):
            value = getattr(company, field_name)
            
            # Check if field has meaningful data
            if value is not None:
                if isinstance(value, str) and value.strip():
                    has_value = True
                    value_preview = value[:100] + "..." if len(value) > 100 else value
                elif isinstance(value, (list, dict)) and value:
                    has_value = True
                    value_preview = f"{type(value).__name__} with {len(value)} items"
                elif isinstance(value, (int, float, bool)):
                    has_value = True
                    value_preview = str(value)
                elif hasattr(value, 'isoformat'):  # datetime
                    has_value = True
                    value_preview = value.isoformat()
        
        if has_value:
            report['populated_fields'] += 1
        else:
            report['empty_fields'] += 1
        
        # Store field details
        report['field_details'][field_name] = {
            'header': field_header,
            'column': col,
            'has_value': has_value,
            'value_preview': value_preview
        }
        
        # Update category counts
        for category, fields in categories.items():
            if field_name in fields:
                report['coverage_by_category'][category]['total'] += 1
                if has_value:
                    report['coverage_by_category'][category]['populated'] += 1
                break
    
    # Calculate percentages
    report['overall_coverage'] = (report['populated_fields'] / report['total_fields'] * 100) if report['total_fields'] > 0 else 0
    
    for category in report['coverage_by_category'].values():
        if category['total'] > 0:
            category['percentage'] = (category['populated'] / category['total'] * 100)
    
    return report


def verify_pinecone_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Verify that all expected fields are in Pinecone metadata"""
    expected_fields = [
        # Core fields
        'company_name', 'website', 'company_description', 'industry', 'business_model',
        
        # Rich data fields
        'ai_summary', 'value_proposition', 'key_services', 'competitive_advantages',
        'tech_stack', 'pain_points', 'raw_content',
        
        # Company details
        'founding_year', 'location', 'employee_count_range', 'leadership_team',
        'contact_info', 'social_media', 'products_services_offered',
        'funding_status', 'partnerships', 'awards', 'company_culture',
        
        # Job-related
        'job_listings_count', 'job_listings', 'job_listings_details',
        
        # Processing metadata
        'pages_crawled', 'crawl_duration', 'scrape_status', 'last_updated',
        
        # Similarity dimensions
        'company_stage', 'tech_sophistication', 'industry', 'business_model_type',
        'geographic_scope', 'decision_maker_type',
        
        # SaaS classification
        'saas_classification', 'is_saas', 'classification_confidence',
        
        # Token tracking
        'total_input_tokens', 'total_output_tokens', 'total_cost_usd'
    ]
    
    verification = {
        'total_expected': len(expected_fields),
        'found': 0,
        'missing': [],
        'field_status': {}
    }
    
    for field in expected_fields:
        if field in metadata and metadata[field]:
            verification['found'] += 1
            verification['field_status'][field] = 'present'
        else:
            verification['missing'].append(field)
            verification['field_status'][field] = 'missing'
    
    verification['coverage_percentage'] = (verification['found'] / verification['total_expected'] * 100)
    
    return verification


def create_field_coverage_sheet_data(company: CompanyData, report: Dict[str, Any]) -> List[List[str]]:
    """Create sheet data showing field coverage analysis"""
    rows = []
    
    # Header row
    rows.append(['Field Category', 'Field Name', 'Column', 'Has Value', 'Value Preview'])
    
    # Group fields by category
    categories = {
        'Core Identity': ['id', 'name', 'website', 'industry', 'business_model', 'company_size'],
        'Technology': ['tech_stack', 'has_chat_widget', 'has_forms', 'tech_sophistication'],
        'Business Intelligence': ['pain_points', 'key_services', 'competitive_advantages', 
                                 'target_market', 'company_description', 'value_proposition'],
        'Company Details': ['founding_year', 'location', 'employee_count_range', 
                           'company_culture', 'funding_status', 'social_media', 
                           'contact_info', 'leadership_team'],
        'Extended Info': ['recent_news', 'certifications', 'partnerships', 'awards',
                         'recent_news_events', 'job_listings_details'],
        'Sales Intelligence': ['has_job_listings', 'job_listings_count', 'products_services_offered',
                              'key_decision_makers', 'funding_stage_detailed', 'sales_marketing_tools'],
        'Similarity Metrics': ['company_stage', 'geographic_scope', 'business_model_type',
                              'decision_maker_type', 'sales_complexity'],
        'AI Analysis': ['raw_content', 'ai_summary', 'embedding'],
        'Metadata': ['pages_crawled', 'crawl_duration', 'scrape_status', 'created_at', 'last_updated']
    }
    
    # Add field details grouped by category
    for category, fields in categories.items():
        for field_name in fields:
            if field_name in report['field_details']:
                field_data = report['field_details'][field_name]
                rows.append([
                    category,
                    field_data['header'],
                    field_data['column'],
                    'YES' if field_data['has_value'] else 'NO',
                    field_data['value_preview'] or ''
                ])
    
    # Add summary section
    rows.append([])  # Empty row
    rows.append(['SUMMARY', '', '', '', ''])
    rows.append(['Total Fields', str(report['total_fields']), '', '', ''])
    rows.append(['Populated Fields', str(report['populated_fields']), '', '', ''])
    rows.append(['Empty Fields', str(report['empty_fields']), '', '', ''])
    rows.append(['Coverage %', f"{report['overall_coverage']:.1f}%", '', '', ''])
    
    return rows