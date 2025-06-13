#!/usr/bin/env python3
"""
Remove duplicate companies from Pinecone index based on company names and websites.
This script identifies and removes duplicate entries while preserving the most complete record.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline
from typing import List, Dict, Any, Tuple
import logging
from collections import defaultdict
from difflib import SequenceMatcher

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PineconeDuplicateRemover:
    """Remove duplicate companies from Pinecone index"""
    
    def __init__(self, dry_run: bool = True):
        """
        Initialize the duplicate remover
        
        Args:
            dry_run: If True, only identify duplicates without removing them
        """
        self.dry_run = dry_run
        load_dotenv()
        
        config = CompanyIntelligenceConfig()
        self.pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME')
        )
        
    def get_all_companies(self) -> List[Dict[str, Any]]:
        """Get all companies from Pinecone"""
        try:
            # Get a large number to capture all companies
            all_companies = self.pipeline.pinecone_client.find_companies_by_filters({}, top_k=1000)
            logger.info(f"Retrieved {len(all_companies)} companies from Pinecone")
            return all_companies
        except Exception as e:
            logger.error(f"Failed to retrieve companies: {e}")
            return []
    
    def normalize_company_name(self, name: str) -> str:
        """Normalize company name for comparison"""
        if not name:
            return ""
        
        # Convert to lowercase and strip whitespace
        normalized = name.lower().strip()
        
        # Remove common suffixes and prefixes
        suffixes_to_remove = [
            'inc.', 'inc', 'llc', 'ltd.', 'ltd', 'corp.', 'corp', 'co.', 'co',
            'company', 'corporation', 'incorporated', 'limited', 'technologies',
            'tech', 'software', 'solutions', 'systems', 'services'
        ]
        
        for suffix in suffixes_to_remove:
            if normalized.endswith(f' {suffix}'):
                normalized = normalized[:-len(suffix)-1].strip()
            elif normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
        
        # Remove extra spaces and special characters
        normalized = ' '.join(normalized.split())
        normalized = ''.join(char for char in normalized if char.isalnum() or char.isspace())
        
        return normalized
    
    def normalize_website(self, website: str) -> str:
        """Normalize website URL for comparison"""
        if not website:
            return ""
        
        # Remove protocol and www
        normalized = website.lower().strip()
        for prefix in ['https://', 'http://', 'www.']:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
        
        # Remove trailing slash
        if normalized.endswith('/'):
            normalized = normalized[:-1]
        
        return normalized
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings using SequenceMatcher"""
        if not str1 or not str2:
            return 0.0
        return SequenceMatcher(None, str1, str2).ratio()
    
    def find_duplicates(self, companies: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find duplicate companies based on name and website similarity
        
        Returns:
            Dict mapping normalized identifier to list of duplicate companies
        """
        duplicates = defaultdict(list)
        processed_companies = []
        
        for company in companies:
            metadata = company.get('metadata', {})
            company_name = metadata.get('company_name', '')
            website = metadata.get('website', '')
            
            # Skip companies without names
            if not company_name or company_name.lower() in ['unknown', 'test company', '']:
                continue
            
            # Normalize identifiers
            normalized_name = self.normalize_company_name(company_name)
            normalized_website = self.normalize_website(website)
            
            # Check against existing companies for duplicates
            found_duplicate = False
            for existing_group_key, existing_companies in duplicates.items():
                if existing_companies:
                    existing_metadata = existing_companies[0].get('metadata', {})
                    existing_name = self.normalize_company_name(existing_metadata.get('company_name', ''))
                    existing_website = self.normalize_website(existing_metadata.get('website', ''))
                    
                    # Check name similarity
                    name_similarity = self.calculate_similarity(normalized_name, existing_name)
                    website_match = normalized_website and existing_website and normalized_website == existing_website
                    
                    # Consider as duplicate if:
                    # 1. Names are very similar (>= 0.9 similarity)
                    # 2. Websites match exactly
                    # 3. Names are somewhat similar (>= 0.8) AND one has no website
                    if (name_similarity >= 0.9 or 
                        website_match or 
                        (name_similarity >= 0.8 and (not normalized_website or not existing_website))):
                        
                        duplicates[existing_group_key].append(company)
                        found_duplicate = True
                        break
            
            if not found_duplicate:
                # Create new group with normalized name as key
                group_key = f"{normalized_name}_{normalized_website}" if normalized_website else normalized_name
                duplicates[group_key].append(company)
        
        # Filter to only return groups with actual duplicates (>1 company)
        actual_duplicates = {k: v for k, v in duplicates.items() if len(v) > 1}
        
        return actual_duplicates
    
    def select_best_record(self, duplicate_group: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Select the best record from a group of duplicates and return records to delete
        
        Selection criteria (in order of priority):
        1. Most complete metadata (most non-empty fields)
        2. Has website URL
        3. Longest description/summary
        4. Most recent (if timestamp available)
        """
        
        def score_record(company: Dict[str, Any]) -> int:
            """Score a record based on completeness"""
            metadata = company.get('metadata', {})
            score = 0
            
            # Count non-empty metadata fields
            for key, value in metadata.items():
                if value and str(value).strip() and str(value).lower() not in ['unknown', 'n/a', 'none']:
                    score += 1
            
            # Bonus for having website
            if metadata.get('website') and metadata['website'].strip():
                score += 5
            
            # Bonus for having description/summary
            description_fields = ['company_description', 'ai_summary', 'value_proposition']
            for field in description_fields:
                if metadata.get(field) and len(str(metadata[field]).strip()) > 50:
                    score += 3
            
            # Bonus for having rich data
            rich_fields = ['key_services', 'tech_stack', 'competitive_advantages']
            for field in rich_fields:
                if metadata.get(field) and str(metadata[field]).strip():
                    score += 2
            
            return score
        
        # Score all records
        scored_records = [(company, score_record(company)) for company in duplicate_group]
        scored_records.sort(key=lambda x: x[1], reverse=True)  # Sort by score descending
        
        best_record = scored_records[0][0]
        records_to_delete = [record[0] for record in scored_records[1:]]
        
        return best_record, records_to_delete
    
    def remove_duplicates(self) -> Dict[str, Any]:
        """
        Main function to identify and remove duplicates
        
        Returns:
            Dict with results summary
        """
        logger.info(f"🔍 Starting duplicate removal process (dry_run={self.dry_run})")
        
        # Get all companies
        all_companies = self.get_all_companies()
        if not all_companies:
            return {"error": "No companies found in database"}
        
        logger.info(f"📊 Found {len(all_companies)} total companies")
        
        # Find duplicates
        duplicate_groups = self.find_duplicates(all_companies)
        
        if not duplicate_groups:
            logger.info("✅ No duplicates found!")
            return {
                "total_companies": len(all_companies),
                "duplicate_groups": 0,
                "duplicates_found": 0,
                "records_would_delete": 0,
                "message": "No duplicates found"
            }
        
        logger.info(f"🔍 Found {len(duplicate_groups)} duplicate groups")
        
        # Process each duplicate group
        total_duplicates = 0
        total_to_delete = 0
        deletion_summary = []
        
        for group_key, duplicate_group in duplicate_groups.items():
            total_duplicates += len(duplicate_group)
            
            logger.info(f"\n📂 Duplicate Group: {group_key}")
            logger.info(f"   Companies in group: {len(duplicate_group)}")
            
            # Show all companies in the group
            for i, company in enumerate(duplicate_group):
                metadata = company.get('metadata', {})
                company_id = company.get('company_id', 'Unknown')
                name = metadata.get('company_name', 'Unknown')
                website = metadata.get('website', 'No website')
                description = metadata.get('company_description', 'No description')
                
                logger.info(f"     {i+1}. {name} (ID: {company_id[:8]}...)")
                logger.info(f"        Website: {website}")
                logger.info(f"        Description: {description[:100]}{'...' if len(description) > 100 else ''}")
            
            # Select best record and records to delete
            best_record, records_to_delete = self.select_best_record(duplicate_group)
            
            best_metadata = best_record.get('metadata', {})
            best_name = best_metadata.get('company_name', 'Unknown')
            best_id = best_record.get('company_id', 'Unknown')
            
            logger.info(f"   🏆 Selected as best: {best_name} (ID: {best_id[:8]}...)")
            logger.info(f"   🗑️  Will delete {len(records_to_delete)} duplicates")
            
            # Track for summary
            total_to_delete += len(records_to_delete)
            deletion_summary.append({
                "group": group_key,
                "keep": {
                    "id": best_id,
                    "name": best_name
                },
                "delete": [
                    {
                        "id": record.get('company_id', 'Unknown'),
                        "name": record.get('metadata', {}).get('company_name', 'Unknown')
                    }
                    for record in records_to_delete
                ]
            })
            
            # Perform actual deletions if not dry run
            if not self.dry_run:
                deleted_count = 0
                for record_to_delete in records_to_delete:
                    company_id = record_to_delete.get('company_id')
                    if company_id:
                        try:
                            success = self.pipeline.pinecone_client.delete_company(company_id)
                            if success:
                                deleted_count += 1
                                logger.info(f"   ✅ Deleted: {company_id[:8]}...")
                            else:
                                logger.error(f"   ❌ Failed to delete: {company_id[:8]}...")
                        except Exception as e:
                            logger.error(f"   ❌ Error deleting {company_id[:8]}...: {e}")
                
                logger.info(f"   📊 Successfully deleted {deleted_count}/{len(records_to_delete)} duplicates")
        
        # Summary
        result = {
            "total_companies": len(all_companies),
            "duplicate_groups": len(duplicate_groups),
            "duplicates_found": total_duplicates,
            "records_would_delete" if self.dry_run else "records_deleted": total_to_delete,
            "deletion_summary": deletion_summary,
            "dry_run": self.dry_run
        }
        
        logger.info(f"\n🎯 SUMMARY:")
        logger.info(f"   Total companies: {len(all_companies)}")
        logger.info(f"   Duplicate groups found: {len(duplicate_groups)}")
        logger.info(f"   Total duplicates: {total_duplicates}")
        if self.dry_run:
            logger.info(f"   Records that would be deleted: {total_to_delete}")
            logger.info(f"   💡 Run with --execute to actually delete duplicates")
        else:
            logger.info(f"   Records deleted: {total_to_delete}")
            logger.info(f"   Database cleanup completed!")
        
        return result

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Remove duplicate companies from Pinecone index")
    parser.add_argument(
        "--execute", 
        action="store_true", 
        help="Actually delete duplicates (default is dry-run mode)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Warning for actual execution
    if args.execute:
        print("⚠️  WARNING: This will permanently delete duplicate records from Pinecone!")
        print("⚠️  Make sure you have a backup or are confident in the duplicate detection logic.")
        response = input("Are you sure you want to proceed? (type 'DELETE' to confirm): ")
        if response != 'DELETE':
            print("❌ Operation cancelled.")
            return
    
    # Initialize remover
    remover = PineconeDuplicateRemover(dry_run=not args.execute)
    
    try:
        result = remover.remove_duplicates()
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            sys.exit(1)
        
        print(f"\n✅ Operation completed successfully!")
        
        if result.get("dry_run", True):
            print(f"💡 This was a dry run. Use --execute to actually delete duplicates.")
        
    except Exception as e:
        logger.error(f"❌ Duplicate removal failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()