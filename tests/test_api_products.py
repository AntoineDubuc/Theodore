#!/usr/bin/env python3
import requests
import json

# Test the detailed companies API endpoint
response = requests.get("http://localhost:5002/api/companies/details")
data = response.json()

if data.get('success'):
    companies = data.get('companies', [])
    print(f'✅ Found {len(companies)} companies')
    print(f'📊 Companies with products: {data.get("stats", {}).get("companies_with_products", 0)}')
    print()
    print('📦 PRODUCTS/SERVICES DATA:')
    for company in companies[:10]:
        products = company.get('products_services_text', 'No data')
        name = company.get('name', 'Unknown')
        if products != 'No data' and len(products) > 5:
            print(f'  • {name:20}: {products[:80]}{"..." if len(products) > 80 else ""}')
        else:
            print(f'  • {name:20}: {products}')
else:
    print(f'❌ Error: {data.get("error", "Unknown error")}')