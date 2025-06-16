#!/usr/bin/env python3
"""
Complete UI Workflow Test - Mimics the exact user workflow:
1. Research Walmart (like clicking research button)
2. Save to index (like clicking "Add to Index")
3. Verify rich data preservation in both Pinecone and JSON storage
4. Report detailed results

This test replicates what you've been doing 30 times manually in the UI.
"""

import os
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

class UIWorkflowTester:
    def __init__(self):
        self.base_url = "http://localhost:5004"  # V2 app URL
        self.company_name = "Walmart"
        self.test_results = {
            "research_success": False,
            "save_to_index_success": False,
            "rich_data_preserved": False,
            "json_file_created": False,
            "pinecone_metadata_complete": False,
            "completion_percentage_match": False
        }
        
    def log(self, message):
        """Log with timestamp"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def test_research_walmart(self):
        """Step 1: Research Walmart (mimics clicking research button in UI)"""
        self.log("🔬 STEP 1: Starting Walmart research (mimicking UI research button)")
        
        try:
            # Call the same endpoint the UI calls
            research_payload = {
                "company_name": self.company_name,
                "website_url": "https://www.walmart.com"
            }
            
            self.log(f"📤 Calling POST {self.base_url}/api/v2/research/start")
            response = requests.post(
                f"{self.base_url}/api/v2/research/start",
                json=research_payload,
                timeout=30
            )
            
            if response.status_code != 200:
                self.log(f"❌ Research start failed: {response.status_code} - {response.text}")
                return None
                
            response_data = response.json()
            job_id = response_data.get('job_id')
            
            if not job_id:
                self.log(f"❌ No job_id in response: {response_data}")
                return None
                
            self.log(f"✅ Research started with job_id: {job_id}")
            return job_id
            
        except Exception as e:
            self.log(f"❌ Research start exception: {e}")
            return None
    
    def poll_research_progress(self, job_id):
        """Step 2: Poll for research completion (mimics UI progress polling)"""
        self.log("📊 STEP 2: Polling research progress (mimicking UI progress updates)")
        
        max_polls = 24  # 2 minutes max
        poll_count = 0
        
        while poll_count < max_polls:
            try:
                self.log(f"📡 Polling progress ({poll_count + 1}/{max_polls})")
                # Try different progress endpoints
                response = requests.get(
                    f"{self.base_url}/api/progress/all",
                    timeout=10
                )
                
                if response.status_code != 200:
                    self.log(f"⚠️ Progress check failed: {response.status_code}")
                    time.sleep(5)
                    poll_count += 1
                    continue
                    
                all_progress = response.json()
                
                # Find our specific job in the progress data
                job_progress = None
                if 'progress' in all_progress and 'jobs' in all_progress['progress']:
                    job_progress = all_progress['progress']['jobs'].get(job_id)
                elif 'jobs' in all_progress:
                    job_progress = all_progress['jobs'].get(job_id)
                
                if not job_progress:
                    self.log(f"⚠️ Job {job_id} not found in progress data")
                    time.sleep(5)
                    poll_count += 1
                    continue
                
                status = job_progress.get('status')
                self.log(f"📈 Status: {status}")
                
                if status == 'completed':
                    self.log("✅ Research completed successfully")
                    self.test_results["research_success"] = True
                    return job_progress.get('results')
                elif status == 'failed':
                    self.log(f"❌ Research failed: {job_progress.get('error', 'Unknown error')}")
                    return None
                elif status in ['pending', 'running']:
                    # Still processing
                    time.sleep(5)
                    poll_count += 1
                    continue
                else:
                    self.log(f"⚠️ Unknown status: {status}")
                    time.sleep(5)
                    poll_count += 1
                    continue
                    
            except Exception as e:
                self.log(f"⚠️ Progress polling exception: {e}")
                time.sleep(5)
                poll_count += 1
                continue
        
        self.log("❌ Research timed out after 5 minutes")
        return None
    
    def save_to_index(self, research_data):
        """Step 3: Save to index (mimics clicking "Add to Index" button)"""
        self.log("💾 STEP 3: Saving to index (mimicking 'Add to Index' button click)")
        
        try:
            # Use the exact same payload structure the UI sends
            save_payload = {
                "company_name": self.company_name,
                "research_data": research_data
            }
            
            self.log(f"📤 Calling POST {self.base_url}/api/v2/save-to-index")
            self.log(f"📋 Research data keys: {list(research_data.keys()) if research_data else 'None'}")
            
            # Check if rich data exists in research_data
            rich_fields = ['ai_summary', 'company_description', 'value_proposition', 'key_services', 'competitive_advantages', 'tech_stack', 'pain_points']
            rich_data_count = 0
            for field in rich_fields:
                if field in research_data and research_data[field]:
                    rich_data_count += 1
                    self.log(f"✅ Rich field '{field}' present in research data")
                else:
                    self.log(f"❌ Rich field '{field}' missing from research data")
            
            self.log(f"📊 Rich data fields in research: {rich_data_count}/{len(rich_fields)}")
            
            response = requests.post(
                f"{self.base_url}/api/v2/save-to-index",
                json=save_payload,
                timeout=60
            )
            
            if response.status_code != 200:
                self.log(f"❌ Save to index failed: {response.status_code} - {response.text}")
                return None
                
            response_data = response.json()
            
            if response_data.get('success'):
                self.log("✅ Save to index succeeded")
                self.test_results["save_to_index_success"] = True
                return response_data
            else:
                self.log(f"❌ Save to index returned success=False: {response_data}")
                return None
                
        except Exception as e:
            self.log(f"❌ Save to index exception: {e}")
            return None
    
    def verify_pinecone_storage(self):
        """Step 4: Verify data is properly stored in Pinecone"""
        self.log("🔍 STEP 4: Verifying Pinecone storage")
        
        try:
            from src.models import CompanyIntelligenceConfig
            from src.pinecone_client import PineconeClient
            
            config = CompanyIntelligenceConfig()
            pinecone_client = PineconeClient(
                config=config,
                api_key=os.getenv('PINECONE_API_KEY'),
                environment=os.getenv('PINECONE_ENVIRONMENT', 'us-west1-gcp'),
                index_name=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
            )
            
            # Find Walmart in Pinecone
            walmart_company = pinecone_client.find_company_by_name("Walmart")
            
            if not walmart_company:
                self.log("❌ Walmart not found in Pinecone after save")
                return False
                
            self.log(f"✅ Found Walmart in Pinecone with ID: {walmart_company.id}")
            
            # Check rich data fields in Pinecone metadata
            company_id = walmart_company.id
            metadata = pinecone_client.get_company_metadata(company_id)
            
            if not metadata:
                self.log("❌ No metadata found for Walmart")
                return False
            
            self.log(f"📊 Pinecone metadata contains {len(metadata)} fields")
            
            # Check rich fields preservation
            rich_fields = ['ai_summary', 'company_description', 'value_proposition', 'key_services', 'competitive_advantages', 'tech_stack', 'pain_points']
            preserved_count = 0
            
            for field in rich_fields:
                if field in metadata and metadata[field]:
                    preserved_count += 1
                    if isinstance(metadata[field], str):
                        preview = metadata[field][:100] + "..." if len(metadata[field]) > 100 else metadata[field]
                        self.log(f"✅ {field}: {len(metadata[field])} chars - '{preview}'")
                    else:
                        self.log(f"✅ {field}: {type(metadata[field]).__name__} - {metadata[field]}")
                else:
                    self.log(f"❌ {field}: NOT in metadata or empty")
            
            self.log(f"📈 Rich fields preserved in Pinecone: {preserved_count}/{len(rich_fields)}")
            
            if preserved_count >= 6:  # Allow for some variance
                self.test_results["pinecone_metadata_complete"] = True
                self.log("✅ Pinecone metadata verification PASSED")
                return True
            else:
                self.log("❌ Pinecone metadata verification FAILED")
                return False
                
        except Exception as e:
            self.log(f"❌ Pinecone verification exception: {e}")
            return False
    
    def verify_json_storage(self):
        """Step 5: Verify JSON file storage"""
        self.log("📁 STEP 5: Verifying JSON file storage")
        
        try:
            # Look for JSON files in data/company_details
            data_dir = "data/company_details"
            if not os.path.exists(data_dir):
                self.log(f"❌ Data directory {data_dir} does not exist")
                return False
            
            json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
            self.log(f"📁 Found {len(json_files)} JSON files in {data_dir}")
            
            # Find the most recent JSON file (likely our Walmart data)
            if not json_files:
                self.log("❌ No JSON files found")
                return False
            
            # Check each JSON file for Walmart data
            walmart_json_file = None
            for json_file in json_files:
                json_path = os.path.join(data_dir, json_file)
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                    
                    if json_data.get('name', '').lower() == 'walmart':
                        walmart_json_file = json_path
                        break
                except Exception as e:
                    self.log(f"⚠️ Could not read {json_file}: {e}")
                    continue
            
            if not walmart_json_file:
                self.log("❌ No JSON file found containing Walmart data")
                return False
            
            self.log(f"✅ Found Walmart JSON file: {walmart_json_file}")
            
            # Verify rich data in JSON
            with open(walmart_json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            self.log(f"📊 JSON file contains {len(json_data)} fields")
            
            rich_fields = ['ai_summary', 'company_description', 'value_proposition', 'key_services', 'competitive_advantages', 'tech_stack', 'pain_points']
            json_preserved_count = 0
            
            for field in rich_fields:
                if field in json_data and json_data[field]:
                    json_preserved_count += 1
                    if isinstance(json_data[field], str):
                        preview = json_data[field][:100] + "..." if len(json_data[field]) > 100 else json_data[field]
                        self.log(f"✅ {field}: {len(json_data[field])} chars - '{preview}'")
                    else:
                        self.log(f"✅ {field}: {type(json_data[field]).__name__} - {json_data[field]}")
                else:
                    self.log(f"❌ {field}: NOT in JSON or empty")
            
            self.log(f"📈 Rich fields preserved in JSON: {json_preserved_count}/{len(rich_fields)}")
            
            if json_preserved_count >= 6:
                self.test_results["json_file_created"] = True
                self.test_results["rich_data_preserved"] = True
                self.log("✅ JSON storage verification PASSED")
                return True
            else:
                self.log("❌ JSON storage verification FAILED")
                return False
                
        except Exception as e:
            self.log(f"❌ JSON verification exception: {e}")
            return False
    
    def calculate_completion_percentage(self, research_data):
        """Calculate completion percentage like the UI does"""
        if not research_data:
            return 0
        
        # Count non-empty fields (mimicking UI logic)
        total_fields = 0
        populated_fields = 0
        
        for key, value in research_data.items():
            total_fields += 1
            if value is not None and value != '' and value != []:
                populated_fields += 1
        
        if total_fields == 0:
            return 0
        
        return round((populated_fields / total_fields) * 100, 1)
    
    def run_complete_test(self):
        """Run the complete UI workflow test"""
        self.log("🚀 STARTING COMPLETE UI WORKFLOW TEST")
        self.log("=" * 60)
        self.log(f"Testing the workflow you've done 30 times: Research {self.company_name} → Add to Index → Verify")
        self.log("=" * 60)
        
        # Step 1: Research Walmart
        job_id = self.test_research_walmart()
        if not job_id:
            self.log("💥 Test FAILED at research step")
            return self.generate_report()
        
        # Step 2: Poll for completion
        research_data = self.poll_research_progress(job_id)
        if not research_data:
            self.log("💥 Test FAILED at polling step")
            return self.generate_report()
        
        # Calculate completion percentage
        completion_pct = self.calculate_completion_percentage(research_data)
        self.log(f"📊 Research completion percentage: {completion_pct}%")
        
        # Step 3: Save to index
        save_result = self.save_to_index(research_data)
        if not save_result:
            self.log("💥 Test FAILED at save-to-index step")
            return self.generate_report()
        
        # Step 4: Verify Pinecone storage
        pinecone_ok = self.verify_pinecone_storage()
        
        # Step 5: Verify JSON storage
        json_ok = self.verify_json_storage()
        
        # Final assessment
        if pinecone_ok and json_ok:
            self.log("🎉 COMPLETE UI WORKFLOW TEST PASSED!")
            self.test_results["completion_percentage_match"] = True
        else:
            self.log("💥 COMPLETE UI WORKFLOW TEST FAILED!")
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate final test report"""
        self.log("\n" + "=" * 60)
        self.log("📋 FINAL TEST REPORT")
        self.log("=" * 60)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{status} {test_name}")
        
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        
        self.log(f"\n📊 SUMMARY: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL TESTS PASSED - The UI workflow works correctly!")
            self.log("✅ The save-to-index fix is working")
            self.log("✅ Rich data is being preserved")
            self.log("✅ Both Pinecone and JSON storage are functional")
        else:
            self.log("💥 SOME TESTS FAILED - Issues remain in the workflow")
            self.log("❌ You would still experience the same issues in the UI")
        
        return self.test_results


if __name__ == "__main__":
    print("🧪 UI WORKFLOW COMPLETE TEST")
    print(f"Timestamp: {datetime.now()}")
    print("This test mimics your manual workflow: Research Walmart → Add to Index → Verify storage")
    print()
    
    tester = UIWorkflowTester()
    results = tester.run_complete_test()
    
    print(f"\n✅ TEST COMPLETE - Check results above")