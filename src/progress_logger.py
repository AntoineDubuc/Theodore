"""
Real-time progress logging system for web UI
Provides live updates during company processing
"""

import json
import time
import logging
import os
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
        
        # Load existing progress data or initialize empty
        self._load_progress()
    
    def start_job(self, job_id: str, company_name: str, total_phases: int = 4) -> None:
        """Start tracking a new processing job"""
        # Starting job tracking
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
            
            
            self.progress_data["current_job"] = job_id
            self.progress_data["jobs"][job_id] = job_data
            self.progress_data["last_updated"] = datetime.now().isoformat()
            
            
            self._save_progress()
            
            logger.info(f"Started processing job {job_id} for {company_name}")
    
    def update_phase(self, job_id: str, phase_name: str, status: str = "running", 
                    details: Optional[Dict] = None) -> None:
        """Update current phase progress"""
        with self.lock:
            if job_id not in self.progress_data["jobs"]:
                # Try reloading progress data from file (subprocess case)
                self._load_progress()
                
                if job_id not in self.progress_data["jobs"]:
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
            else:
                # Update current phase number for running phases
                job["current_phase"] = len(job["phases"])
            
            self.progress_data["last_updated"] = datetime.now().isoformat()
            self._save_progress()
            
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
            current_job_id = self.progress_data.get("current_job")
            
            all_jobs = self.progress_data.get("jobs", {})
            
            if current_job_id:
                
                # CRITICAL FIX: Always reload from file to get latest subprocess updates
                self._load_progress()
                all_jobs = self.progress_data.get("jobs", {})  # Update with fresh data
                
                # If subprocess is writing, retry once after a short delay
                if current_job_id in all_jobs:
                    job_data = all_jobs[current_job_id]
                    if len(job_data.get('phases', [])) == 0 and job_data.get('status') == 'running':
                        import time
                        time.sleep(0.1)  # Brief delay for file sync
                        self._load_progress()
                        all_jobs = self.progress_data.get("jobs", {})
                
                if current_job_id in all_jobs:
                    job_data = all_jobs[current_job_id]
                    
                    # If current job is no longer running, clear it
                    if job_data.get('status') != 'running':
                        self.progress_data["current_job"] = None
                        self._save_progress()
                    else:
                        return self._build_phase_structure(job_data)
                else:
                    pass
            else:
                pass
                
            # If no current job, look for any running jobs (but clean up stale ones first)
            running_jobs = []
            stale_jobs_cleaned = False
            for job_id, job_data in all_jobs.items():
                if job_data.get("status") == "running":
                    # Check if job is stale (running for more than 15 minutes for concurrent implementation)
                    start_time_str = job_data.get("start_time")
                    if start_time_str:
                        try:
                            from datetime import datetime, timedelta
                            start_time = datetime.fromisoformat(start_time_str)
                            if datetime.now() - start_time > timedelta(minutes=15):
                                job_data["status"] = "failed"
                                job_data["error"] = "Job timed out after 15 minutes"
                                job_data["end_time"] = datetime.now().isoformat()
                                stale_jobs_cleaned = True
                                continue  # Skip this job
                        except:
                            pass  # If we can't parse the time, treat as valid
                    
                    running_jobs.append((job_id, job_data))
            
            # Save progress if we cleaned up stale jobs
            if stale_jobs_cleaned:
                self._save_progress()
                    
            if running_jobs:
                # Return the most recent running job
                most_recent = max(running_jobs, key=lambda x: x[1].get("start_time", ""))
                return self._build_phase_structure(most_recent[1])
                
            return None
    
    def _build_phase_structure(self, job_data: Dict) -> Dict:
        """Build phase structure for frontend consumption"""
        # Keep phases as an array for JavaScript compatibility
        result = job_data.copy()
        # JavaScript expects phases to be an array, not a dictionary
        result["phases"] = job_data.get("phases", [])
        return result
    
    def log_page_scraping(self, job_id: str, page_url: str, content_preview: str, 
                         page_number: int, total_pages: int) -> None:
        """Log individual page scraping progress"""
        print(f"🔍 [{page_number}/{total_pages}] Scraping: {page_url}")
        with self.lock:
            if job_id not in self.progress_data["jobs"]:
                return
            
            # Add to UI processing log
            self.add_to_progress_log(job_id, f"🔍 Scraped page {page_number}/{total_pages}: {page_url} ({len(content_preview):,} chars)")
            
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
                    break
            
            if not phase_updated:
                print(f"⚠️ DEBUG: No running Content Extraction phase found to update")
    
    def add_to_progress_log(self, job_id: str, message: str):
        """Add a message to the processing log for the UI"""
        with self.lock:
            if job_id in self.progress_data["jobs"]:
                if "processing_log" not in self.progress_data["jobs"][job_id]:
                    self.progress_data["jobs"][job_id]["processing_log"] = []
                
                # Check for duplicate messages to reduce spam
                existing_logs = self.progress_data["jobs"][job_id]["processing_log"]
                if existing_logs and existing_logs[-1]["message"] == message:
                    return  # Skip duplicate message
                
                timestamp = datetime.now().strftime("%I:%M:%S %p")
                self.progress_data["jobs"][job_id]["processing_log"].append({
                    "timestamp": timestamp,
                    "message": message
                })
                
                # Keep only the last 50 log entries to prevent memory issues
                if len(self.progress_data["jobs"][job_id]["processing_log"]) > 50:
                    self.progress_data["jobs"][job_id]["processing_log"] = self.progress_data["jobs"][job_id]["processing_log"][-50:]
                
                self._save_progress()
    
    def log_llm_call(self, job_id: str, call_number: int, model: str, prompt_length: int, response_length: int = None):
        """Log LLM call to UI processing log"""
        with self.lock:
            if job_id not in self.progress_data["jobs"]:
                return
            
            if response_length:
                self.add_to_progress_log(job_id, f"🧠 LLM Call #{call_number}: {model} - {prompt_length:,} chars in → {response_length:,} chars out")
            else:
                self.add_to_progress_log(job_id, f"🧠 LLM Call #{call_number}: {model} - sending {prompt_length:,} chars...")
            
            self.progress_data["last_updated"] = datetime.now().isoformat()
            
            # Console logging for immediate feedback  
            print(f"🧠 LLM Call #{call_number}: {model} - {prompt_length:,} chars")
            
            logger.info(f"Job {job_id}: LLM Call #{call_number} - {model}")
    
    def _load_progress(self) -> None:
        """Load progress data from JSON file"""
        try:
            if Path(self.log_file).exists():
                with open(self.log_file, 'r') as f:
                    self.progress_data = json.load(f)
                    logger.info(f"Loaded existing progress data with {len(self.progress_data.get('jobs', {}))} jobs")
            else:
                # File doesn't exist, save empty data
                self._save_progress()
                logger.info("Created new progress data file")
        except Exception as e:
            logger.warning(f"Failed to load progress data: {e}, using empty data")
            self._save_progress()
    
    def _save_progress(self) -> None:
        """Save progress data to file (thread-safe)"""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.progress_data, f, indent=2, default=str)
                f.flush()  # Force flush to disk
                os.fsync(f.fileno())  # Force sync to disk
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
    progress_logger.update_phase(job_id, phase_name, status, details=details)


def start_company_processing(company_name: str) -> str:
    """Start tracking company processing, returns job_id"""
    import uuid
    
    # Check if there's already a running job for this company
    with progress_logger.lock:
        for job_data in progress_logger.progress_data["jobs"].values():
            if (job_data.get("company_name") == company_name and 
                job_data.get("status") == "running"):
                logger.warning(f"Company {company_name} is already being processed in job {job_data.get('job_id')}")
                return job_data.get('job_id')
    
    # Generate unique job ID using UUID to prevent collisions
    job_id = f"company_{int(time.time() * 1000)}_{str(uuid.uuid4())[:8]}"
    progress_logger.start_job(job_id, company_name, total_phases=4)
    return job_id


def complete_company_processing(job_id: str, success: bool, error: str = None, summary: str = None, results: dict = None):
    """Complete company processing tracking"""
    progress_logger.complete_job(job_id, success, error, summary, results)


# ============================================================================ 
# BATCH PROCESSING PROGRESS TRACKING
# ============================================================================

class BatchProgressLogger:
    """Handles progress tracking for batch processing operations"""
    
    def __init__(self):
        self.batch_jobs = {}
        self.lock = threading.Lock()
    
    def start_batch_job(self, job_id: str, total_companies: int):
        """Start tracking a batch processing job"""
        with self.lock:
            self.batch_jobs[job_id] = {
                'job_id': job_id,
                'total_companies': total_companies,
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'status': 'running',
                'start_time': datetime.now().isoformat(),
                'current_message': f'Starting batch processing of {total_companies} companies...',
                'current_company': 'Initializing...',
                'companies': []
            }
    
    def update_batch_progress(self, job_id: str, processed_count: int, message: str, current_company: str = None):
        """Update progress for a batch job"""
        with self.lock:
            if job_id in self.batch_jobs:
                self.batch_jobs[job_id]['processed'] = processed_count
                self.batch_jobs[job_id]['current_message'] = message
                
                # Extract current company from message if not provided
                if current_company:
                    self.batch_jobs[job_id]['current_company'] = current_company
                elif 'Processing ' in message:
                    # Extract company name from "Processing CompanyName..." message
                    import re
                    match = re.search(r'Processing ([^.]+)\.\.\.', message)
                    if match:
                        self.batch_jobs[job_id]['current_company'] = match.group(1)
                elif 'Completed' in message or 'Failed' in message:
                    # Extract company name from completion messages
                    import re
                    match = re.search(r'(?:Completed|Failed) ([^:]+)', message)
                    if match:
                        self.batch_jobs[job_id]['current_company'] = match.group(1)
    
    def complete_batch_job(self, job_id: str, successful_count: int, failed_count: int, results: dict):
        """Complete a batch processing job"""
        with self.lock:
            if job_id in self.batch_jobs:
                job = self.batch_jobs[job_id]
                job['successful'] = successful_count
                job['failed'] = failed_count
                job['status'] = 'completed'
                job['end_time'] = datetime.now().isoformat()
                job['current_message'] = f'Completed: {successful_count} successful, {failed_count} failed'
                job['results'] = results
    
    def get_batch_progress(self, job_id: str):
        """Get progress for a specific batch job"""
        with self.lock:
            return self.batch_jobs.get(job_id)

# Global batch progress logger instance
batch_progress_logger = BatchProgressLogger()

# Add batch methods to the main progress_logger for compatibility
def start_batch_job(job_id: str, total_companies: int):
    """Start batch job tracking"""
    batch_progress_logger.start_batch_job(job_id, total_companies)

def update_batch_progress(job_id: str, processed_count: int, message: str):
    """Update batch progress"""
    batch_progress_logger.update_batch_progress(job_id, processed_count, message)

def complete_batch_job(job_id: str, successful_count: int, failed_count: int, results: dict):
    """Complete batch job"""
    batch_progress_logger.complete_batch_job(job_id, successful_count, failed_count, results)

def get_batch_progress(job_id: str):
    """Get batch progress"""
    return batch_progress_logger.get_batch_progress(job_id)

# Attach batch methods to progress_logger instance for easy access
progress_logger.start_batch_job = start_batch_job
progress_logger.update_batch_progress = update_batch_progress 
progress_logger.complete_batch_job = complete_batch_job
progress_logger.get_batch_progress = get_batch_progress