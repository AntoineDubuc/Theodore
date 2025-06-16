#!/usr/bin/env python3
"""
Debug what data is actually returned for a company
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from src.pinecone_client import PineconeClient
from src.models import CompanyIntelligenceConfig

def debug_company_data():
    """Check what data is stored for connatix.com"""
    print("🔍 Debugging Company Data for connatix.com")
    print("=" * 50)
    
    try:
        # Initialize Pinecone client
        config = CompanyIntelligenceConfig()
        pinecone_client = PineconeClient(
            config=config,
            api_key=os.getenv('PINECONE_API_KEY'),
            environment=os.getenv('PINECONE_ENVIRONMENT', 'us-east-1'),
            index_name=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        )
        
        # Find connatix in the database
        print("\n📊 Searching for connatix.com in Pinecone...")
        company_data = pinecone_client.find_company_by_name('connatix.com')
        
        if not company_data:
            print("❌ Company not found in database")
            return
        
        print("✅ Found company data!")
        
        # Print all fields
        print("\n📋 Company Data Fields:")
        print("-" * 50)
        
        # Convert to dict to see all fields
        data_dict = company_data.dict()
        
        # Count populated vs empty fields
        populated_fields = 0
        empty_fields = 0
        
        for field, value in data_dict.items():
            if value is not None and value != "" and value != [] and value != {}:
                populated_fields += 1
                # Show populated fields
                if isinstance(value, str) and len(value) > 100:
                    print(f"✅ {field}: {value[:100]}...")
                else:
                    print(f"✅ {field}: {value}")
            else:
                empty_fields += 1
                print(f"❌ {field}: <empty>")
        
        print("\n📊 Summary:")
        print(f"   Total fields: {len(data_dict)}")
        print(f"   Populated fields: {populated_fields}")
        print(f"   Empty fields: {empty_fields}")
        
        # Check specific important fields
        print("\n🔍 Key Fields Check:")
        key_fields = [
            'name', 'website', 'industry', 'business_model', 'company_size',
            'tech_stack', 'pain_points', 'key_services', 'target_market',
            'company_description', 'value_proposition', 'location',
            'employee_count_range', 'funding_status', 'ai_summary'
        ]
        
        for field in key_fields:
            value = getattr(company_data, field, None)
            if value:
                print(f"   {field}: {value}")
            else:
                print(f"   {field}: ❌ MISSING")
        
        # Save full data to file for inspection
        output_file = Path(__file__).parent / 'connatix_debug_data.json'
        with open(output_file, 'w') as f:
            json.dump(data_dict, f, indent=2, default=str)
        print(f"\n💾 Full data saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_company_data()