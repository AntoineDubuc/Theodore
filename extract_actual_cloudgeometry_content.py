#!/usr/bin/env python3
"""
Extract Actual CloudGeometry Content
Finds and extracts the raw content from the original CloudGeometry research that successfully crawled 100 pages
"""

import os
import sys
import json
import glob
from datetime import datetime

def find_cloudgeometry_files():
    """Find all files that might contain CloudGeometry content"""
    print("🔍 Searching for CloudGeometry content files...")
    
    search_locations = [
        "/Users/antoinedubuc/Desktop/AI_Goodies/Theodore/data/",
        "/Users/antoinedubuc/Desktop/AI_Goodies/Theodore/logs/",
        "/Users/antoinedubuc/Desktop/AI_Goodies/Theodore/tests/",
        "/Users/antoinedubuc/Desktop/AI_Goodies/Theodore/",
        "/tmp/"
    ]
    
    found_files = []
    
    for location in search_locations:
        if os.path.exists(location):
            # Search for JSON files
            json_files = glob.glob(os.path.join(location, "**/*.json"), recursive=True)
            for file in json_files:
                try:
                    with open(file, 'r') as f:
                        content = f.read()
                        if 'cloudgeometry' in content.lower():
                            found_files.append(('JSON', file, len(content)))
                except:
                    pass
            
            # Search for log files
            log_files = glob.glob(os.path.join(location, "**/*.log"), recursive=True)
            for file in log_files:
                try:
                    with open(file, 'r') as f:
                        content = f.read()
                        if 'cloudgeometry' in content.lower():
                            found_files.append(('LOG', file, len(content)))
                except:
                    pass
            
            # Search for txt files
            txt_files = glob.glob(os.path.join(location, "**/*.txt"), recursive=True)
            for file in txt_files:
                try:
                    with open(file, 'r') as f:
                        content = f.read()
                        if 'cloudgeometry' in content.lower():
                            found_files.append(('TXT', file, len(content)))
                except:
                    pass
    
    return found_files

def search_app_log():
    """Search the app.log file for CloudGeometry processing details"""
    print("\n📋 Searching app.log for CloudGeometry processing...")
    
    app_log_path = "/Users/antoinedubuc/Desktop/AI_Goodies/Theodore/app.log"
    
    if not os.path.exists(app_log_path):
        print("❌ app.log not found")
        return None
    
    cloudgeometry_lines = []
    
    with open(app_log_path, 'r') as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        if 'cloudgeometry' in line.lower():
            # Include context around CloudGeometry mentions
            start = max(0, i-2)
            end = min(len(lines), i+3)
            context = lines[start:end]
            cloudgeometry_lines.extend(context)
    
    if cloudgeometry_lines:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"/Users/antoinedubuc/Desktop/AI_Goodies/Theodore/cloudgeometry_app_log_extract_{timestamp}.txt"
        
        with open(output_file, 'w') as f:
            f.write("CloudGeometry App Log Extract\n")
            f.write("=" * 40 + "\n\n")
            f.writelines(cloudgeometry_lines)
        
        print(f"✅ Found {len(cloudgeometry_lines)} lines mentioning CloudGeometry")
        print(f"📁 Saved to: {output_file}")
        return output_file
    else:
        print("❌ No CloudGeometry mentions found in app.log")
        return None

def check_response_json():
    """Check if there's a response JSON file with the actual API response"""
    print("\n🔍 Looking for API response files...")
    
    # Check if the /tmp/cloudgeometry_response.json file was recreated
    possible_response_files = [
        "/tmp/cloudgeometry_response.json",
        "/Users/antoinedubuc/Desktop/AI_Goodies/Theodore/data/test_responses/cloudgeometry_response.json",
        "/Users/antoinedubuc/Desktop/AI_Goodies/Theodore/cloudgeometry_response.json"
    ]
    
    for file_path in possible_response_files:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"✅ Found response file: {file_path} ({file_size:,} bytes)")
            
            # Check if it contains page content
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                if isinstance(data, dict) and 'company' in data:
                    company = data['company']
                    
                    # Check for raw content
                    if 'raw_content' in company and company['raw_content']:
                        print(f"   📄 Has raw_content: {len(company['raw_content']):,} characters")
                    
                    # Check for scraped content details
                    if 'scraped_content_details' in company and company['scraped_content_details']:
                        print(f"   📄 Has scraped_content_details")
                    
                    # Check pages crawled
                    if 'pages_crawled' in company:
                        print(f"   📊 Pages crawled: {company['pages_crawled']}")
                    
                    return file_path
                        
            except Exception as e:
                print(f"   ❌ Error reading {file_path}: {e}")
    
    print("❌ No API response files found")
    return None

def extract_content_from_file(file_path):
    """Extract and display content from a found file"""
    print(f"\n📄 Extracting content from: {file_path}")
    
    try:
        if file_path.endswith('.json'):
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Create output file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"/Users/antoinedubuc/Desktop/AI_Goodies/Theodore/cloudgeometry_extracted_content_{timestamp}.txt"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("CloudGeometry Extracted Content\n")
                f.write("=" * 50 + "\n")
                f.write(f"Source: {file_path}\n")
                f.write(f"Extracted: {datetime.now().isoformat()}\n\n")
                
                if isinstance(data, dict) and 'company' in data:
                    company = data['company']
                    
                    # Extract raw content
                    if 'raw_content' in company and company['raw_content']:
                        f.write("RAW CONTENT:\n")
                        f.write("-" * 30 + "\n")
                        f.write(company['raw_content'])
                        f.write("\n\n")
                    
                    # Extract scraped content details
                    if 'scraped_content_details' in company and company['scraped_content_details']:
                        f.write("SCRAPED CONTENT DETAILS:\n")
                        f.write("-" * 30 + "\n")
                        
                        details = company['scraped_content_details']
                        if isinstance(details, str):
                            try:
                                details = json.loads(details)
                            except:
                                pass
                        
                        if isinstance(details, dict):
                            for url, content in details.items():
                                f.write(f"\n=== {url} ===\n")
                                f.write(content)
                                f.write("\n")
                        elif isinstance(details, list):
                            for i, page in enumerate(details):
                                f.write(f"\n=== Page {i+1} ===\n")
                                if isinstance(page, dict):
                                    f.write(f"URL: {page.get('url', 'Unknown')}\n")
                                    f.write(f"Content: {page.get('content', 'No content')}\n")
                                else:
                                    f.write(str(page))
                                f.write("\n")
                        else:
                            f.write(str(details))
                        f.write("\n\n")
                    
                    # Extract other relevant fields
                    interesting_fields = ['pages_crawled', 'crawl_duration', 'scraped_urls', 'ai_summary']
                    f.write("OTHER FIELDS:\n")
                    f.write("-" * 30 + "\n")
                    for field in interesting_fields:
                        if field in company:
                            value = company[field]
                            if isinstance(value, list) and len(value) > 10:
                                f.write(f"{field}: {len(value)} items\n")
                                for i, item in enumerate(value[:10]):
                                    f.write(f"  {i+1}. {item}\n")
                                f.write(f"  ... and {len(value)-10} more\n")
                            else:
                                f.write(f"{field}: {value}\n")
                else:
                    f.write("Raw JSON data:\n")
                    f.write(json.dumps(data, indent=2))
            
            print(f"✅ Content extracted to: {output_file}")
            print(f"📁 File size: {os.path.getsize(output_file):,} bytes")
            return output_file
            
    except Exception as e:
        print(f"❌ Error extracting content: {e}")
        return None

def main():
    """Main execution"""
    print("🚀 CloudGeometry Content Extractor")
    print("=" * 50)
    
    # Search for files
    found_files = find_cloudgeometry_files()
    
    if found_files:
        print(f"\n📁 Found {len(found_files)} files containing CloudGeometry:")
        for file_type, file_path, size in found_files:
            print(f"   {file_type}: {file_path} ({size:,} bytes)")
        
        # Process the largest file (likely contains most content)
        largest_file = max(found_files, key=lambda x: x[2])
        print(f"\n🎯 Processing largest file: {largest_file[1]}")
        
        extracted_file = extract_content_from_file(largest_file[1])
        if extracted_file:
            print(f"\n✅ SUCCESS: CloudGeometry content extracted to {extracted_file}")
        else:
            print(f"\n❌ FAILED: Could not extract content")
    else:
        print("\n❌ No CloudGeometry files found")
    
    # Also search app.log
    log_extract = search_app_log()
    
    # Check for response files
    response_file = check_response_json()
    if response_file:
        extract_content_from_file(response_file)

if __name__ == "__main__":
    main()