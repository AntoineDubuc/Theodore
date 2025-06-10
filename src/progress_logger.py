"""
Real-time progress logging system for web UI
Provides live updates during company processing
"""

import json
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


class ProgressLogger:
    """
    Thread-safe progress logger for real-time UI updates
    """
    
    def __init__(self, log_file: str = "logs/processing_progress.json"):
        self.log_file = log_file
        self.progress_data = {
            "current_job": None,
            "jobs": {},
            "last_updated": None
        }
        self.lock = threading.Lock()
        
        # Ensure logs directory exists
        Path(self.log_file).parent.mkdir(exist_ok=True)
        
        # Initialize empty log file
        self._save_progress()
    
    def start_job(self, job_id: str, company_name: str, total_phases: int = 4) -> None:
        """Start tracking a new processing job"""
        print(f"🔧 PROGRESS_LOGGER: Starting job {job_id} for {company_name}")
        with self.lock:
            job_data = {
                "job_id": job_id,
                "company_name": company_name,
                "status": "running",
                "current_phase": 0,
                "total_phases": total_phases,
                "phases": [],
                "start_time": datetime.now().isoformat(),
                "end_time": None,
                "error": None,
                "result_summary": None
            }
            
            print(f"🔧 PROGRESS_LOGGER: Created job data: {job_data}")
            print(f"🔧 PROGRESS_LOGGER: Setting current_job to: {job_id}")
            
            self.progress_data["current_job"] = job_id
            self.progress_data["jobs"][job_id] = job_data
            self.progress_data["last_updated"] = datetime.now().isoformat()
            
            print(f"🔧 PROGRESS_LOGGER: Jobs in memory after adding: {len(self.progress_data['jobs'])}")
            print(f"🔧 PROGRESS_LOGGER: Current job set to: {self.progress_data['current_job']}")
            
            self._save_progress()
            
            print(f"🔧 PROGRESS_LOGGER: Job {job_id} saved successfully")
            logger.info(f"Started processing job {job_id} for {company_name}")
    
    def update_phase(self, job_id: str, phase_name: str, status: str = "running", 
                    details: Optional[Dict] = None) -> None:
        """Update current phase progress"""
        print(f"🔧 DEBUG: update_phase called - job_id: {job_id}, phase: {phase_name}, status: {status}")
        with self.lock:
            if job_id not in self.progress_data["jobs"]:
                print(f"❌ DEBUG: Job {job_id} not found in jobs: {list(self.progress_data['jobs'].keys())}")
                logger.warning(f"Job {job_id} not found for phase update")
                return
            
            job = self.progress_data["jobs"][job_id]
            
            # Extract new details from parameters
            current_url = details.get("current_url") if details else None
            progress_step = details.get("progress_step") if details else None
            status_message = details.get("status_message") if details else None
            
            phase_data = {
                "name": phase_name,
                "status": status,
                "start_time": datetime.now().isoformat(),
                "end_time": None if status == "running" else datetime.now().isoformat(),
                "details": details or {},
                "duration": None,
                "current_url": current_url,
                "progress_step": progress_step,
                "status_message": status_message,
                "current_page": details.get("current_page") if details else None,
                "pages_completed": details.get("pages_completed", 0) if details else 0,
                "total_pages": details.get("total_pages", 0) if details else 0,
                "scraped_content_preview": details.get("content_preview") if details else None
            }
            
            # Update or add phase
            phase_found = False
            for i, existing_phase in enumerate(job["phases"]):
                if existing_phase["name"] == phase_name:
                    # Keep start_time from existing phase if updating
                    if status == "running" and existing_phase.get("start_time"):
                        phase_data["start_time"] = existing_phase["start_time"]
                    
                    # Calculate duration if completing
                    if status != "running" and existing_phase.get("start_time"):
                        start = datetime.fromisoformat(existing_phase["start_time"])
                        end = datetime.now()
                        phase_data["duration"] = (end - start).total_seconds()
                    
                    job["phases"][i] = phase_data
                    phase_found = True
                    break
            
            if not phase_found:
                job["phases"].append(phase_data)
                job["current_phase"] = len(job["phases"])
                print(f"✅ DEBUG: Added new phase '{phase_name}' to job {job_id}. Total phases: {len(job['phases'])}")
            else:
                print(f"🔄 DEBUG: Updated existing phase '{phase_name}' for job {job_id}")
            
            self.progress_data["last_updated"] = datetime.now().isoformat()
            self._save_progress()
            
            print(f"💾 DEBUG: Saved progress data for job {job_id}. Current phases: {[p['name'] for p in job['phases']]}")
            logger.info(f"Job {job_id}: {phase_name} - {status}")
    
    def complete_job(self, job_id: str, success: bool = True, 
                    error: Optional[str] = None, result_summary: Optional[str] = None,
                    results: Optional[Dict] = None) -> None:
        """Mark job as completed"""
        with self.lock:
            if job_id not in self.progress_data["jobs"]:
                logger.warning(f"Job {job_id} not found for completion")
                return
            
            job = self.progress_data["jobs"][job_id]
            job["status"] = "completed" if success else "failed"
            job["end_time"] = datetime.now().isoformat()
            job["error"] = error
            job["result_summary"] = result_summary
            job["results"] = results  # Store full research results
            
            # Calculate total duration
            if job.get("start_time"):
                start = datetime.fromisoformat(job["start_time"])
                end = datetime.now()
                job["total_duration"] = (end - start).total_seconds()
            
            # Clear current job if this was it
            if self.progress_data["current_job"] == job_id:
                self.progress_data["current_job"] = None
            
            self.progress_data["last_updated"] = datetime.now().isoformat()
            self._save_progress()
            
            status_msg = "completed successfully" if success else f"failed: {error}"
            logger.info(f"Job {job_id} {status_msg}")
    
    def get_progress(self, job_id: Optional[str] = None) -> Dict:
        """Get current progress data"""
        with self.lock:
            if job_id:
                job_data = self.progress_data["jobs"].get(job_id, {})
                if job_data:
                    return self._build_phase_structure(job_data)
                return {}
            return self.progress_data.copy()
    
    def get_current_job_progress(self) -> Optional[Dict]:
        """Get progress for currently running job"""
        with self.lock:
            print(f"🔧 PROGRESS_LOGGER: Getting current job progress...")
            current_job_id = self.progress_data.get("current_job")
            print(f"🔧 PROGRESS_LOGGER: Current job ID: {current_job_id}")
            
            all_jobs = self.progress_data.get("jobs", {})
            print(f"🔧 PROGRESS_LOGGER: Total jobs in memory: {len(all_jobs)}")
            print(f"🔧 PROGRESS_LOGGER: All job IDs: {list(all_jobs.keys())}")
            
            if current_job_id:
                print(f"🔧 PROGRESS_LOGGER: Looking for job {current_job_id} in jobs...")
                if current_job_id in all_jobs:
                    job_data = all_jobs[current_job_id]
                    print(f"🔧 PROGRESS_LOGGER: Found current job: {job_data.get('company_name')}")
                    print(f"🔧 PROGRESS_LOGGER: Job status: {job_data.get('status')}")
                    print(f"🔧 PROGRESS_LOGGER: Job phases: {len(job_data.get('phases', []))}")
                    return self._build_phase_structure(job_data)
                else:
                    print(f"🔧 PROGRESS_LOGGER: ❌ Current job {current_job_id} not found in jobs!")
            else:
                print(f"🔧 PROGRESS_LOGGER: No current job set")
                
            # If no current job, look for any running jobs
            running_jobs = []
            for job_id, job_data in all_jobs.items():
                if job_data.get("status") == "running":
                    running_jobs.append((job_id, job_data))
                    
            print(f"🔧 PROGRESS_LOGGER: Found {len(running_jobs)} running jobs")
            if running_jobs:
                # Return the most recent running job
                most_recent = max(running_jobs, key=lambda x: x[1].get("start_time", ""))
                print(f"🔧 PROGRESS_LOGGER: Returning most recent running job: {most_recent[1].get('company_name')}")
                return self._build_phase_structure(most_recent[1])
                
            print(f"🔧 PROGRESS_LOGGER: No active jobs found")
            return None
    
    def _build_phase_structure(self, job_data: Dict) -> Dict:
        """Build phase structure for frontend consumption"""
        phases = {}
        for phase in job_data.get("phases", []):
            phases[phase["name"]] = phase
        
        result = job_data.copy()
        result["phases"] = phases
        return result
    
    def log_page_scraping(self, job_id: str, page_url: str, content_preview: str, 
                         page_number: int, total_pages: int) -> None:
        """Log individual page scraping progress"""
        print(f"🔧 DEBUG: log_page_scraping called - job_id: {job_id}, page: {page_url}, page_num: {page_number}/{total_pages}")
        with self.lock:
            if job_id not in self.progress_data["jobs"]:
                print(f"❌ DEBUG: Job {job_id} not found for page scraping update")
                return
            
            # Update the current Content Extraction phase with page details
            job = self.progress_data["jobs"][job_id]
            phase_updated = False
            for phase in job["phases"]:
                if phase["name"] == "Content Extraction" and phase["status"] == "running":
                    phase["current_page"] = page_url
                    phase["pages_completed"] = page_number
                    phase["total_pages"] = total_pages
                    phase["scraped_content_preview"] = content_preview[:500] + "..." if len(content_preview) > 500 else content_preview
                    phase_updated = True
                    print(f"✅ DEBUG: Updated Content Extraction phase with page {page_url}")
                    break
            
            if not phase_updated:
                print(f"⚠️ DEBUG: No running Content Extraction phase found to update")
            
            self.progress_data["last_updated"] = datetime.now().isoformat()
            self._save_progress()
            
            # Console logging for immediate feedback
            print(f"🔍 [{page_number}/{total_pages}] Scraping: {page_url}")
            if content_preview:
                preview = content_preview[:200] + "..." if len(content_preview) > 200 else content_preview
                print(f"📄 Content preview: {preview}")
            
            logger.info(f"Job {job_id}: Scraped page {page_number}/{total_pages} - {page_url}")
    
    def _save_progress(self) -> None:
        """Save progress data to file (thread-safe)"""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.progress_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save progress data: {e}")
    
    def cleanup_old_jobs(self, max_jobs: int = 50) -> None:
        """Clean up old completed jobs to prevent file growth"""
        with self.lock:
            jobs = self.progress_data["jobs"]
            
            if len(jobs) <= max_jobs:
                return
            
            # Sort jobs by completion time, keep most recent
            completed_jobs = [
                (job_id, job_data) for job_id, job_data in jobs.items()
                if job_data.get("status") in ["completed", "failed"] and job_data.get("end_time")
            ]
            
            if len(completed_jobs) > max_jobs // 2:
                # Sort by end_time and remove oldest
                completed_jobs.sort(key=lambda x: x[1]["end_time"])
                jobs_to_remove = completed_jobs[:-max_jobs//2]
                
                for job_id, _ in jobs_to_remove:
                    del jobs[job_id]
                
                self._save_progress()
                logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")


# Global progress logger instance
progress_logger = ProgressLogger()


def log_processing_phase(job_id: str, phase_name: str, status: str = "running", **details):
    """Convenience function for logging processing phases"""
    print(f"🔧 DEBUG: log_processing_phase called - job_id: {job_id}, phase: {phase_name}, status: {status}, details: {details}")
    progress_logger.update_phase(job_id, phase_name, status, details)


def start_company_processing(company_name: str) -> str:
    """Start tracking company processing, returns job_id"""
    job_id = f"company_{int(time.time() * 1000)}"
    progress_logger.start_job(job_id, company_name, total_phases=4)
    return job_id


def complete_company_processing(job_id: str, success: bool, error: str = None, summary: str = None, results: dict = None):
    """Complete company processing tracking"""
    progress_logger.complete_job(job_id, success, error, summary, results)