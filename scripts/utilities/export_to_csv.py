#!/usr/bin/env python3
"""
Export enhanced company data to CSV for Google Sheets import
"""

import requests
import csv
import os
from datetime import datetime

def export_companies_to_csv():
    print("📊 EXPORTING ENHANCED COMPANY DATA TO CSV")
    print("=" * 50)
    
    try:
        # Get detailed company data
        response = requests.get("http://localhost:5002/api/companies/details")
        data = response.json()
        
        if not data.get('success'):
            print(f"❌ Error: {data.get('error', 'Unknown error')}")
            return
        
        companies = data.get('companies', [])
        print(f"✅ Found {len(companies)} companies")
        
        # CSV filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"theodore_companies_enhanced_{timestamp}.csv"
        
        # CSV headers (matching what you'd expect in Google Sheets)
        headers = [
            'Company Name',
            'Website',
            'Industry', 
            'Products/Services',
            'Value Proposition',
            'Company Culture',
            'Location',
            'Leadership Team',
            'Job Listings Count',
            'Founding Year',
            'Funding Status',
            'Last Updated'
        ]
        
        # Write CSV file
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write headers
            writer.writerow(headers)
            
            # Write company data
            for company in companies:
                leadership = ', '.join(company.get('leadership_team', [])) if company.get('leadership_team') else 'No data'
                
                row = [
                    company.get('name', 'Unknown'),
                    company.get('website', ''),
                    company.get('industry', 'Unknown'),
                    company.get('products_services_text', 'No data'),
                    company.get('value_proposition', 'No data'),
                    company.get('company_culture', 'No data'),
                    company.get('location', 'Unknown'),
                    leadership,
                    company.get('job_listings_count', 0),
                    company.get('founding_year', 'Unknown'),
                    company.get('funding_status', 'Unknown'),
                    company.get('last_updated', 'Unknown')
                ]
                writer.writerow(row)
        
        print(f"✅ CSV exported: {csv_filename}")
        print(f"📂 Location: {os.path.abspath(csv_filename)}")
        
        # Show companies with products data
        companies_with_products = [c for c in companies if c.get('products_services_text', 'No data') != 'No data']
        print(f"\n📦 COMPANIES WITH PRODUCTS/SERVICES DATA ({len(companies_with_products)}):")
        
        for company in companies_with_products:
            products = company.get('products_services_text', 'No data')
            print(f"  • {company.get('name', 'Unknown'):20}: {products[:60]}{'...' if len(products) > 60 else ''}")
        
        print(f"\n💡 TO UPDATE YOUR GOOGLE SHEETS:")
        print(f"   1. Open your Google Sheets document")
        print(f"   2. Go to File → Import")
        print(f"   3. Upload: {csv_filename}")
        print(f"   4. Choose 'Replace spreadsheet' or 'Insert new sheet'")
        print(f"   5. Column R will now have Products/Services data!")
        
        return csv_filename
        
    except Exception as e:
        print(f"❌ Error exporting CSV: {e}")
        return None

if __name__ == "__main__":
    export_companies_to_csv()