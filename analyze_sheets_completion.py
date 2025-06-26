#!/usr/bin/env python3
"""
Analyze Google Sheets data completion rates for all fields
"""

import sys
from pathlib import Path
import os

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def analyze_sheets_data():
    """Analyze completion rates for all fields in the Google Sheets"""
    
    print("📊 GOOGLE SHEETS DATA COMPLETION ANALYSIS")
    print("=" * 70)
    
    try:
        # Import the sheets integration
        from src.sheets_integration.google_sheets_service_client import GoogleSheetsServiceClient
        
        # Initialize sheets client
        service_account_file = project_root / 'config' / 'credentials' / 'theodore-service-account.json'
        
        if not service_account_file.exists():
            print(f"❌ Service account key not found at: {service_account_file}")
            print("Please ensure Google Sheets credentials are properly configured")
            return None
        
        sheets_client = GoogleSheetsServiceClient(service_account_file)
        spreadsheet_id = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'
        
        print(f"🔗 Analyzing spreadsheet: {spreadsheet_id}")
        print(f"📋 Sheet: Company Data")
        
        # Read all data from the sheet
        try:
            # First, get the sheet metadata to find the correct sheet name
            spreadsheet_metadata = sheets_client.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            sheets_info = spreadsheet_metadata.get('sheets', [])
            print(f"📋 Available sheets:")
            for sheet in sheets_info:
                sheet_props = sheet.get('properties', {})
                sheet_id = sheet_props.get('sheetId')
                sheet_name = sheet_props.get('title')
                print(f"   - {sheet_name} (ID: {sheet_id})")
            
            # Find the sheet with gid 81910028 (from the URL)
            target_gid = 81910028
            target_sheet_name = None
            
            for sheet in sheets_info:
                sheet_props = sheet.get('properties', {})
                if sheet_props.get('sheetId') == target_gid:
                    target_sheet_name = sheet_props.get('title')
                    break
            
            if not target_sheet_name:
                # Fallback to first sheet
                target_sheet_name = sheets_info[0]['properties']['title'] if sheets_info else 'Sheet1'
                print(f"⚠️ Target sheet with gid {target_gid} not found, using: {target_sheet_name}")
            else:
                print(f"🎯 Using target sheet: {target_sheet_name}")
            
            sheet_name = target_sheet_name
            
            # Read header row first to understand structure
            header_range = f"'{sheet_name}'!A1:ZZ1"
            header_result = sheets_client.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=header_range
            ).execute()
            
            headers = header_result.get('values', [[]])[0] if header_result.get('values') else []
            
            if not headers:
                print("❌ No headers found in the sheet")
                return None
            
            print(f"📈 Found {len(headers)} columns in the sheet")
            print(f"📊 Column headers: {', '.join(headers[:10])}{'...' if len(headers) > 10 else ''}")
            
            # Read all data
            data_range = f"'{sheet_name}'!A2:ZZ1000"  # Assuming max 1000 rows
            data_result = sheets_client.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=data_range
            ).execute()
            
            rows = data_result.get('values', [])
            
            if not rows:
                print("❌ No data rows found in the sheet")
                return None
            
            print(f"📊 Found {len(rows)} data rows")
            
            # Analyze completion rates
            field_stats = {}
            total_rows_with_data = 0
            
            # Count rows that have any data (not completely empty)
            for row_idx, row in enumerate(rows):
                has_any_data = any(cell.strip() if cell else '' for cell in row)
                if has_any_data:
                    total_rows_with_data += 1
            
            print(f"📈 Rows with data: {total_rows_with_data} out of {len(rows)} total rows")
            
            if total_rows_with_data == 0:
                print("❌ No rows contain any data")
                return None
            
            # Analyze each field
            for col_idx, header in enumerate(headers):
                if not header.strip():
                    continue
                    
                filled_count = 0
                
                # Count filled cells for this column in rows with data
                for row_idx, row in enumerate(rows):
                    # Only count rows that have any data
                    has_any_data = any(cell.strip() if cell else '' for cell in row)
                    if not has_any_data:
                        continue
                        
                    # Check if this specific cell is filled
                    if col_idx < len(row) and row[col_idx] and row[col_idx].strip():
                        # Check for meaningful data (not just "unknown", "N/A", etc.)
                        cell_value = row[col_idx].strip().lower()
                        if cell_value and cell_value not in ['unknown', 'n/a', 'na', '', 'none', 'null', 'undefined']:
                            filled_count += 1
                
                completion_rate = (filled_count / total_rows_with_data) * 100 if total_rows_with_data > 0 else 0
                field_stats[header] = {
                    'filled_count': filled_count,
                    'total_rows': total_rows_with_data,
                    'completion_rate': completion_rate
                }
            
            # Generate report
            print(f"\n📊 FIELD COMPLETION REPORT")
            print("=" * 70)
            print(f"Based on {total_rows_with_data} rows containing data\n")
            
            # Sort by completion rate (descending)
            sorted_fields = sorted(field_stats.items(), key=lambda x: x[1]['completion_rate'], reverse=True)
            
            print("🏆 HIGHEST COMPLETION RATES:")
            print("-" * 50)
            for field, stats in sorted_fields[:10]:
                rate = stats['completion_rate']
                count = stats['filled_count']
                print(f"{field:<30} | {rate:5.1f}% ({count:3d}/{total_rows_with_data:3d})")
            
            print(f"\n📉 LOWEST COMPLETION RATES:")
            print("-" * 50)
            for field, stats in sorted_fields[-10:]:
                rate = stats['completion_rate']
                count = stats['filled_count']
                print(f"{field:<30} | {rate:5.1f}% ({count:3d}/{total_rows_with_data:3d})")
            
            # Summary statistics
            completion_rates = [stats['completion_rate'] for stats in field_stats.values()]
            if completion_rates:
                avg_completion = sum(completion_rates) / len(completion_rates)
                max_completion = max(completion_rates)
                min_completion = min(completion_rates)
                
                print(f"\n📈 SUMMARY STATISTICS:")
                print("-" * 50)
                print(f"Total fields analyzed:     {len(field_stats)}")
                print(f"Average completion rate:   {avg_completion:.1f}%")
                print(f"Highest completion rate:   {max_completion:.1f}%")
                print(f"Lowest completion rate:    {min_completion:.1f}%")
                
                # Fields by completion tier
                excellent = sum(1 for rate in completion_rates if rate >= 80)
                good = sum(1 for rate in completion_rates if 50 <= rate < 80)
                poor = sum(1 for rate in completion_rates if 20 <= rate < 50)
                very_poor = sum(1 for rate in completion_rates if rate < 20)
                
                print(f"\n🎯 COMPLETION TIERS:")
                print("-" * 50)
                print(f"Excellent (≥80%):          {excellent} fields")
                print(f"Good (50-79%):             {good} fields")
                print(f"Poor (20-49%):             {poor} fields")
                print(f"Very Poor (<20%):          {very_poor} fields")
            
            # Export detailed report
            print(f"\n📋 DETAILED FIELD ANALYSIS:")
            print("=" * 70)
            for field, stats in sorted_fields:
                rate = stats['completion_rate']
                count = stats['filled_count']
                tier = "🏆" if rate >= 80 else "✅" if rate >= 50 else "⚠️" if rate >= 20 else "❌"
                print(f"{tier} {field:<35} | {rate:5.1f}% ({count:3d}/{total_rows_with_data:3d})")
            
            return field_stats
            
        except Exception as e:
            print(f"❌ Error reading sheet data: {e}")
            return None
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure Google Sheets integration is properly set up")
        return None
    except Exception as e:
        print(f"❌ Error initializing sheets client: {e}")
        return None

if __name__ == "__main__":
    print("🚀 GOOGLE SHEETS COMPLETION ANALYSIS")
    print("=" * 70)
    
    result = analyze_sheets_data()
    
    if result:
        print(f"\n✅ ANALYSIS COMPLETE")
        print(f"Analyzed {len(result)} fields across company data")
    else:
        print(f"\n❌ ANALYSIS FAILED") 
        print("Please check Google Sheets access and data availability")