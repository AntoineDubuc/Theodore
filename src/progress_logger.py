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
                logger.warning(f"Job {job_id} not found for phase update")
                return
            
            job = self.progress_data["jobs"][job_id]
            
            phase_data = {
                "name": phase_name,
                "status": status,
                "start_time": datetime.now().isoformat(),
                "end_time": None if status == "running" else datetime.now().isoformat(),
                "details": details or {},
                "duration": None
            }
            
            # Update or add phase
            phase_found = False
            for i, existing_phase in enumerate(job["phases"]):
                if existing_phase["name"] == phase_name:
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
            
            self.progress_data["last_updated"] = datetime.now().isoformat()
            self._save_progress()
            
            logger.info(f"Job {job_id}: {phase_name} - {status}")
    
    def complete_job(self, job_id: str, success: bool = True, 
                    error: Optional[str] = None, result_summary: Optional[str] = None) -> None:
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
                return self.progress_data["jobs"].get(job_id, {})
            return self.progress_data.copy()
    
    def get_current_job_progress(self) -> Optional[Dict]:
        """Get progress for currently running job"""
        with self.lock:
            current_job_id = self.progress_data.get("current_job")
            if current_job_id and current_job_id in self.progress_data["jobs"]:
                return self.progress_data["jobs"][current_job_id].copy()
            return None
    
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
    progress_logger.update_phase(job_id, phase_name, status, details)


def start_company_processing(company_name: str) -> str:
    """Start tracking company processing, returns job_id"""
    job_id = f"company_{int(time.time() * 1000)}"
    progress_logger.start_job(job_id, company_name, total_phases=4)
    return job_id


def complete_company_processing(job_id: str, success: bool, error: str = None, summary: str = None):
    """Complete company processing tracking"""
    progress_logger.complete_job(job_id, success, error, summary)