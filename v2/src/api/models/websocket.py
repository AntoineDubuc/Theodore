#!/usr/bin/env python3
"""
Theodore v2 API WebSocket Models

Pydantic models for WebSocket message validation and serialization.
"""

from datetime import datetime
from typing import Optional, Dict, Any, Union, List
from pydantic import BaseModel, Field
from enum import Enum

from .common import JobStatus, ProgressInfo


class WebSocketMessageType(str, Enum):
    """WebSocket message types"""
    PROGRESS_UPDATE = "progress_update"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    JOB_STARTED = "job_started"
    SYSTEM_NOTIFICATION = "system_notification"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    CONNECTION_ACK = "connection_ack"
    SUBSCRIPTION_ACK = "subscription_ack"
    UNSUBSCRIPTION_ACK = "unsubscription_ack"


class NotificationLevel(str, Enum):
    """Notification severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class WebSocketMessage(BaseModel):
    """Base WebSocket message structure"""
    
    type: WebSocketMessageType = Field(..., description="Message type")
    timestamp: datetime = Field(..., description="Message timestamp")
    data: Optional[Dict[str, Any]] = Field(None, description="Message payload")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "progress_update",
                "timestamp": "2025-01-02T10:30:00Z",
                "data": {
                    "job_id": "research_123456",
                    "progress": {
                        "current_step": "AI Analysis",
                        "percentage": 75.0
                    }
                }
            }
        }


class ProgressUpdate(BaseModel):
    """Progress update message payload"""
    
    job_id: str = Field(..., description="Job identifier")
    job_type: str = Field(..., description="Type of job (research/discovery/batch)")
    status: JobStatus = Field(..., description="Current job status")
    progress: ProgressInfo = Field(..., description="Progress information")
    company_name: Optional[str] = Field(None, description="Company being processed")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "research_123456",
                "job_type": "research",
                "status": "running",
                "progress": {
                    "current_step": "AI Analysis",
                    "step_number": 3,
                    "total_steps": 5,
                    "percentage": 60.0,
                    "message": "Analyzing company data",
                    "started_at": "2025-01-02T10:30:00Z",
                    "updated_at": "2025-01-02T10:32:00Z"
                },
                "company_name": "Anthropic"
            }
        }


class JobCompletedMessage(BaseModel):
    """Job completion message payload"""
    
    job_id: str = Field(..., description="Job identifier")
    job_type: str = Field(..., description="Type of job")
    company_name: Optional[str] = Field(None, description="Company processed")
    duration_seconds: float = Field(..., description="Job duration in seconds")
    result_summary: Optional[Dict[str, Any]] = Field(None, description="Brief result summary")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "research_123456",
                "job_type": "research",
                "company_name": "Anthropic",
                "duration_seconds": 45.2,
                "result_summary": {
                    "data_quality": "high",
                    "pages_analyzed": 15,
                    "confidence_score": 0.92
                }
            }
        }


class JobFailedMessage(BaseModel):
    """Job failure message payload"""
    
    job_id: str = Field(..., description="Job identifier")
    job_type: str = Field(..., description="Type of job")
    company_name: Optional[str] = Field(None, description="Company being processed")
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error description")
    retry_count: int = Field(..., description="Number of retry attempts")
    will_retry: bool = Field(..., description="Whether job will be retried")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "research_123456",
                "job_type": "research",
                "company_name": "Anthropic",
                "error_code": "SCRAPING_TIMEOUT",
                "error_message": "Website scraping timed out after 300 seconds",
                "retry_count": 1,
                "will_retry": True
            }
        }


class SystemNotification(BaseModel):
    """System notification message payload"""
    
    notification_id: str = Field(..., description="Notification identifier")
    level: NotificationLevel = Field(..., description="Notification severity")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    category: Optional[str] = Field(None, description="Notification category")
    action_url: Optional[str] = Field(None, description="Optional action URL")
    expires_at: Optional[datetime] = Field(None, description="Notification expiration")
    
    class Config:
        schema_extra = {
            "example": {
                "notification_id": "notif_789012",
                "level": "warning",
                "title": "API Rate Limit Warning",
                "message": "You are approaching your daily API rate limit",
                "category": "rate_limiting",
                "action_url": "/dashboard/usage",
                "expires_at": "2025-01-02T23:59:59Z"
            }
        }


class HeartbeatMessage(BaseModel):
    """Heartbeat message payload"""
    
    server_time: datetime = Field(..., description="Server timestamp")
    connection_id: str = Field(..., description="Connection identifier")
    uptime_seconds: float = Field(..., description="Server uptime")
    
    class Config:
        schema_extra = {
            "example": {
                "server_time": "2025-01-02T10:30:00Z",
                "connection_id": "conn_345678",
                "uptime_seconds": 3600.5
            }
        }


class ConnectionAckMessage(BaseModel):
    """Connection acknowledgment message payload"""
    
    connection_id: str = Field(..., description="Connection identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    connection_type: str = Field(..., description="Connection type")
    capabilities: List[str] = Field(..., description="Available capabilities")
    
    class Config:
        schema_extra = {
            "example": {
                "connection_id": "conn_345678",
                "user_id": "usr_123456",
                "connection_type": "progress",
                "capabilities": [
                    "progress_updates",
                    "job_notifications",
                    "system_notifications"
                ]
            }
        }


class SubscriptionRequest(BaseModel):
    """WebSocket subscription request"""
    
    action: str = Field(..., regex="^(subscribe|unsubscribe)$", description="Subscription action")
    job_id: Optional[str] = Field(None, description="Job ID to subscribe to")
    job_type: Optional[str] = Field(None, description="Job type filter")
    notification_categories: Optional[List[str]] = Field(None, description="Notification categories")
    
    class Config:
        schema_extra = {
            "example": {
                "action": "subscribe",
                "job_id": "research_123456",
                "job_type": "research",
                "notification_categories": ["rate_limiting", "system_maintenance"]
            }
        }


class SubscriptionAckMessage(BaseModel):
    """Subscription acknowledgment message payload"""
    
    action: str = Field(..., description="Subscription action performed")
    job_id: Optional[str] = Field(None, description="Job ID subscribed/unsubscribed")
    success: bool = Field(..., description="Whether subscription was successful")
    message: Optional[str] = Field(None, description="Additional information")
    
    class Config:
        schema_extra = {
            "example": {
                "action": "subscribe",
                "job_id": "research_123456",
                "success": True,
                "message": "Successfully subscribed to job progress updates"
            }
        }


class ErrorMessage(BaseModel):
    """WebSocket error message payload"""
    
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error description")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
    class Config:
        schema_extra = {
            "example": {
                "error_code": "INVALID_SUBSCRIPTION",
                "error_message": "Job ID not found or access denied",
                "details": {
                    "job_id": "research_999999",
                    "user_id": "usr_123456"
                }
            }
        }


class ConnectionMetadata(BaseModel):
    """WebSocket connection metadata"""
    
    connection_id: str = Field(..., description="Unique connection identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    connection_type: str = Field(..., description="Connection type")
    connected_at: datetime = Field(..., description="Connection timestamp")
    last_heartbeat: datetime = Field(..., description="Last heartbeat timestamp")
    subscriptions: List[str] = Field(default_factory=list, description="Active subscriptions")
    client_info: Optional[Dict[str, str]] = Field(None, description="Client information")
    
    class Config:
        schema_extra = {
            "example": {
                "connection_id": "conn_345678",
                "user_id": "usr_123456",
                "connection_type": "progress",
                "connected_at": "2025-01-02T10:30:00Z",
                "last_heartbeat": "2025-01-02T10:35:00Z",
                "subscriptions": ["research_123456", "discovery_789012"],
                "client_info": {
                    "user_agent": "Mozilla/5.0...",
                    "ip_address": "192.168.1.100"
                }
            }
        }


class BatchProgressUpdate(BaseModel):
    """Batch job progress update payload"""
    
    job_id: str = Field(..., description="Batch job identifier")
    total_companies: int = Field(..., description="Total companies to process")
    completed: int = Field(..., description="Companies completed")
    failed: int = Field(..., description="Companies failed")
    pending: int = Field(..., description="Companies pending")
    current_company: Optional[str] = Field(None, description="Currently processing company")
    progress_percentage: float = Field(..., ge=0.0, le=100.0, description="Overall progress")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "batch_345678",
                "total_companies": 100,
                "completed": 45,
                "failed": 2,
                "pending": 53,
                "current_company": "Anthropic",
                "progress_percentage": 45.0,
                "estimated_completion": "2025-01-02T12:00:00Z"
            }
        }