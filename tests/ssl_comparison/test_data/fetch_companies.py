#!/usr/bin/env python3
"""
Fetch companies from Google Sheets for SSL comparison testing
Uses the 6000+ company dataset from the provided spreadsheet
"""

import pandas as pd
import json
import random
import sys
import os
from typing import List, Dict

# Google Sheets URL - convert to CSV export format
SHEETS_URL = "https://docs.google.com/spreadsheets/d/1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk/export?format=csv&gid=0"

def fetch_companies_from_sheets(url: str, sample_size: int = 10) -> List[Dict]:
    """
    Fetch companies from Google Sheets and return a sample for testing
    
    Args:
        url: Google Sheets CSV export URL
        sample_size: Number of companies to sample for testing
        
    Returns:
        List of company dictionaries with name, website, and metadata
    """
    try:
        print(f"📊 Fetching companies from Google Sheets...")
        
        # Read the CSV data from Google Sheets
        df = pd.read_csv(url)
        
        print(f"✅ Successfully loaded {len(df)} companies from spreadsheet")
        
        # Display available columns
        print(f"📋 Available columns: {list(df.columns)}")
        
        # Clean and prepare the data
        companies = []
        
        for idx, row in df.iterrows():
            # Try to identify company name and website columns
            # Common column names for company data
            name_columns = ['company', 'company_name', 'name', 'organization', 'Company', 'Company Name', 'Name']
            website_columns = ['website', 'url', 'domain', 'site', 'Website', 'URL', 'Domain', 'web_site']
            
            company_name = None
            website = None
            
            # Find company name
            for col in name_columns:
                if col in df.columns and pd.notna(row.get(col)):
                    company_name = str(row[col]).strip()
                    break
            
            # Find website URL
            for col in website_columns:
                if col in df.columns and pd.notna(row.get(col)):
                    website = str(row[col]).strip()
                    # Ensure website has protocol
                    if website and not website.startswith(('http://', 'https://')):
                        website = f"https://{website}"
                    break
            
            # Only include companies with both name and website
            if company_name and website and len(company_name) > 1:
                company = {
                    "name": company_name,
                    "website": website,
                    "domain": website.replace("https://", "").replace("http://", "").split("/")[0],
                    "source_row": idx + 2,  # +2 for 1-indexed + header row
                    "additional_data": {col: str(row[col]) for col in df.columns if pd.notna(row.get(col))}
                }
                companies.append(company)
        
        print(f"🔍 Found {len(companies)} companies with both name and website")
        
        if len(companies) < sample_size:
            print(f"⚠️  Warning: Only {len(companies)} valid companies found, using all of them")
            return companies
        
        # Randomly sample companies for testing
        sample = random.sample(companies, sample_size)
        
        print(f"🎯 Selected {len(sample)} companies for SSL comparison testing:")
        for i, company in enumerate(sample, 1):
            print(f"  {i:2d}. {company['name']} → {company['domain']}")
        
        return sample
        
    except Exception as e:
        print(f"❌ Error fetching companies from Google Sheets: {str(e)}")
        print(f"🔧 Falling back to manual company selection...")
        
        # Fallback: Return a few well-known companies for testing
        return [
            {
                "name": "Microsoft",
                "website": "https://microsoft.com",
                "domain": "microsoft.com",
                "source_row": "fallback",
                "additional_data": {"note": "Fallback company - reliable for testing"}
            },
            {
                "name": "Google",
                "website": "https://google.com", 
                "domain": "google.com",
                "source_row": "fallback",
                "additional_data": {"note": "Fallback company - reliable for testing"}
            },
            {
                "name": "Apple",
                "website": "https://apple.com",
                "domain": "apple.com", 
                "source_row": "fallback",
                "additional_data": {"note": "Fallback company - reliable for testing"}
            }
        ]

def save_test_companies(companies: List[Dict], output_file: str):
    """Save the fetched companies to a JSON file for testing"""
    
    test_data = {
        "test_companies": companies,
        "test_metadata": {
            "total_companies": len(companies),
            "source": "Google Sheets - 6000+ company dataset",
            "sheets_url": "https://docs.google.com/spreadsheets/d/1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk/edit?gid=0#gid=0",
            "selection_method": "Random sampling from valid companies with name and website",
            "test_purpose": "SSL comparison testing - demonstrate SSL fix impact on real company data",
            "generated_at": pd.Timestamp.now().isoformat()
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved {len(companies)} companies to {output_file}")

def main():
    """Main execution function"""
    
    # Configuration
    sample_size = 8  # Number of companies to test
    output_file = "company_list.json"
    
    if len(sys.argv) > 1:
        try:
            sample_size = int(sys.argv[1])
        except ValueError:
            print(f"⚠️  Invalid sample size '{sys.argv[1]}', using default: {sample_size}")
    
    print(f"🚀 SSL Comparison Test - Company Data Fetcher")
    print(f"📊 Fetching {sample_size} companies from Google Sheets dataset...")
    print(f"🔗 Source: https://docs.google.com/spreadsheets/d/1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk/edit")
    print("=" * 80)
    
    # Fetch companies
    companies = fetch_companies_from_sheets(SHEETS_URL, sample_size)
    
    if not companies:
        print("❌ No companies fetched, exiting...")
        sys.exit(1)
    
    # Save to JSON file
    save_test_companies(companies, output_file)
    
    print("\n" + "=" * 80)
    print(f"✅ Company data ready for SSL comparison testing!")
    print(f"📁 Data saved to: {output_file}")
    print(f"🧪 Ready to run control and treatment tests with {len(companies)} companies")

if __name__ == "__main__":
    main()