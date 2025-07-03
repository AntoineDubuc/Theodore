#!/usr/bin/env python3
"""
Theodore v2 WebSocket API Router

FastAPI router for WebSocket connections and real-time updates.
"""

import json
import asyncio
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException

from ...infrastructure.observability.logging import get_logger
from ...infrastructure.observability.metrics import get_metrics_collector
from ..models.websocket import (
    WebSocketMessage, WebSocketMessageType, ProgressUpdate,
    JobCompletedMessage, SystemNotification, HeartbeatMessage,
    ConnectionAckMessage, SubscriptionRequest, ErrorMessage
)

logger = get_logger(__name__)
metrics = get_metrics_collector()

router = APIRouter()

# Simple connection manager for demonstration
# In production, this would be more sophisticated with Redis/database backing
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.job_subscriptions: dict[str, set[str]] = {}  # job_id -> connection_ids
        
    async def connect(self, websocket: WebSocket, connection_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        # Send connection acknowledgment
        ack_message = WebSocketMessage(
            type=WebSocketMessageType.CONNECTION_ACK,
            timestamp=None,  # Will be set by model
            data=ConnectionAckMessage(
                connection_id=connection_id,
                connection_type="general",
                capabilities=[
                    "progress_updates",
                    "job_notifications", 
                    "system_notifications"
                ]
            ).dict()
        )
        
        await self.send_message(connection_id, ack_message)
        
        logger.info(f"WebSocket connection established: {connection_id}")
        metrics.increment_counter("websocket_connections_total")
        
    def disconnect(self, connection_id: str):
        """Remove WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            
        # Remove from all job subscriptions
        for job_id, subscribers in self.job_subscriptions.items():
            subscribers.discard(connection_id)
            
        logger.info(f"WebSocket connection closed: {connection_id}")
        metrics.decrement_gauge("websocket_active_connections")
        
    async def send_message(self, connection_id: str, message: WebSocketMessage):
        """Send message to specific connection"""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(message.json())
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")
                self.disconnect(connection_id)
                
    async def broadcast_to_job_subscribers(self, job_id: str, message: WebSocketMessage):
        """Broadcast message to all subscribers of a job"""
        if job_id in self.job_subscriptions:
            for connection_id in self.job_subscriptions[job_id].copy():
                await self.send_message(connection_id, message)
                
    async def broadcast_system_notification(self, message: WebSocketMessage):
        """Broadcast system notification to all connections"""
        for connection_id in list(self.active_connections.keys()):
            await self.send_message(connection_id, message)
            
    def subscribe_to_job(self, connection_id: str, job_id: str):
        """Subscribe connection to job updates"""
        if job_id not in self.job_subscriptions:
            self.job_subscriptions[job_id] = set()
        self.job_subscriptions[job_id].add(connection_id)
        
    def unsubscribe_from_job(self, connection_id: str, job_id: str):
        """Unsubscribe connection from job updates"""
        if job_id in self.job_subscriptions:
            self.job_subscriptions[job_id].discard(connection_id)

# Global connection manager
manager = ConnectionManager()


@router.websocket("/progress/{job_id}")
async def websocket_job_progress(
    websocket: WebSocket, 
    job_id: str,
    user_id: Optional[str] = Query(None, description="User ID for authentication")
):
    """
    WebSocket endpoint for real-time job progress updates
    
    Provides real-time progress updates for a specific job.
    Automatically subscribes to the job and streams progress information.
    """
    
    connection_id = f"job_{job_id}_{id(websocket)}"
    
    try:
        # Accept connection
        await manager.connect(websocket, connection_id)
        
        # Subscribe to job updates
        manager.subscribe_to_job(connection_id, job_id)
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(send_heartbeat(connection_id))
        
        try:
            # Listen for client messages
            while True:
                data = await websocket.receive_text()
                
                try:
                    # Parse subscription request
                    request = SubscriptionRequest.parse_raw(data)
                    
                    if request.action == "subscribe" and request.job_id:
                        manager.subscribe_to_job(connection_id, request.job_id)
                        
                    elif request.action == "unsubscribe" and request.job_id:
                        manager.unsubscribe_from_job(connection_id, request.job_id)
                        
                except Exception as e:
                    # Send error message for invalid requests
                    error_msg = WebSocketMessage(
                        type=WebSocketMessageType.ERROR,
                        timestamp=None,
                        data=ErrorMessage(
                            error_code="INVALID_REQUEST",
                            error_message=str(e)
                        ).dict()
                    )
                    await manager.send_message(connection_id, error_msg)
                    
        except WebSocketDisconnect:
            pass
        finally:
            heartbeat_task.cancel()
            
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}", exc_info=True)
    finally:
        manager.disconnect(connection_id)


@router.websocket("/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None, description="User ID for authentication"),
    categories: Optional[str] = Query(None, description="Comma-separated notification categories")
):
    """
    WebSocket endpoint for real-time system notifications
    
    Provides real-time system notifications, alerts, and updates.
    Supports filtering by notification categories.
    """
    
    connection_id = f"notifications_{id(websocket)}"
    
    try:
        # Accept connection
        await manager.connect(websocket, connection_id)
        
        # Parse notification categories
        notification_categories = []
        if categories:
            notification_categories = [cat.strip() for cat in categories.split(",")]
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(send_heartbeat(connection_id))
        
        try:
            # Listen for client messages (subscription updates)
            while True:
                data = await websocket.receive_text()
                
                try:
                    # Parse subscription request
                    request = SubscriptionRequest.parse_raw(data)
                    
                    # Handle notification subscription updates
                    if request.notification_categories:
                        notification_categories = request.notification_categories
                        
                except Exception as e:
                    # Send error message
                    error_msg = WebSocketMessage(
                        type=WebSocketMessageType.ERROR,
                        timestamp=None,
                        data=ErrorMessage(
                            error_code="INVALID_REQUEST",
                            error_message=str(e)
                        ).dict()
                    )
                    await manager.send_message(connection_id, error_msg)
                    
        except WebSocketDisconnect:
            pass
        finally:
            heartbeat_task.cancel()
            
    except Exception as e:
        logger.error(f"WebSocket notifications error: {e}", exc_info=True)
    finally:
        manager.disconnect(connection_id)


@router.websocket("/monitoring")
async def websocket_monitoring(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None, description="User ID for authentication")
):
    """
    WebSocket endpoint for real-time system monitoring
    
    Provides real-time system metrics, health status, and performance data.
    Primarily used by admin dashboards and monitoring tools.
    """
    
    connection_id = f"monitoring_{id(websocket)}"
    
    try:
        # Accept connection
        await manager.connect(websocket, connection_id)
        
        # Start heartbeat and monitoring tasks
        heartbeat_task = asyncio.create_task(send_heartbeat(connection_id))
        monitoring_task = asyncio.create_task(send_monitoring_data(connection_id))
        
        try:
            # Listen for client messages
            while True:
                data = await websocket.receive_text()
                
                # Handle monitoring configuration updates
                try:
                    config = json.loads(data)
                    # Update monitoring configuration based on client preferences
                    
                except Exception as e:
                    logger.error(f"Invalid monitoring config: {e}")
                    
        except WebSocketDisconnect:
            pass
        finally:
            heartbeat_task.cancel()
            monitoring_task.cancel()
            
    except Exception as e:
        logger.error(f"WebSocket monitoring error: {e}", exc_info=True)
    finally:
        manager.disconnect(connection_id)


async def send_heartbeat(connection_id: str):
    """Send periodic heartbeat messages"""
    
    while True:
        try:
            heartbeat_msg = WebSocketMessage(
                type=WebSocketMessageType.HEARTBEAT,
                timestamp=None,
                data=HeartbeatMessage(
                    server_time=None,  # Will be set by model
                    connection_id=connection_id,
                    uptime_seconds=0.0  # Would calculate actual uptime
                ).dict()
            )
            
            await manager.send_message(connection_id, heartbeat_msg)
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Heartbeat error for {connection_id}: {e}")
            break


async def send_monitoring_data(connection_id: str):
    """Send periodic monitoring data"""
    
    while True:
        try:
            # Get system metrics (mock data for demonstration)
            monitoring_data = {
                "system": {
                    "cpu_percent": 45.2,
                    "memory_percent": 67.8,
                    "disk_percent": 23.1,
                    "network_io": {"bytes_sent": 1024000, "bytes_recv": 512000}
                },
                "api": {
                    "active_requests": 12,
                    "requests_per_minute": 156,
                    "avg_response_time_ms": 245
                },
                "jobs": {
                    "running": 3,
                    "queued": 8,
                    "completed_today": 127
                }
            }
            
            # Send monitoring message
            msg = WebSocketMessage(
                type=WebSocketMessageType.SYSTEM_NOTIFICATION,
                timestamp=None,
                data=monitoring_data
            )
            
            await manager.send_message(connection_id, msg)
            await asyncio.sleep(5)  # Send monitoring data every 5 seconds
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Monitoring data error for {connection_id}: {e}")
            break


# Function to send job progress updates (called by job processing systems)
async def send_job_progress_update(job_id: str, progress_data: dict):
    """Send progress update to all job subscribers"""
    
    try:
        progress_msg = WebSocketMessage(
            type=WebSocketMessageType.PROGRESS_UPDATE,
            timestamp=None,
            data=ProgressUpdate(**progress_data).dict()
        )
        
        await manager.broadcast_to_job_subscribers(job_id, progress_msg)
        
    except Exception as e:
        logger.error(f"Failed to send progress update for job {job_id}: {e}")


# Function to send job completion notifications
async def send_job_completed(job_id: str, completion_data: dict):
    """Send job completion notification"""
    
    try:
        completion_msg = WebSocketMessage(
            type=WebSocketMessageType.JOB_COMPLETED,
            timestamp=None,
            data=JobCompletedMessage(**completion_data).dict()
        )
        
        await manager.broadcast_to_job_subscribers(job_id, completion_msg)
        
    except Exception as e:
        logger.error(f"Failed to send completion notification for job {job_id}: {e}")


# Function to send system notifications
async def send_system_notification(notification_data: dict):
    """Send system-wide notification"""
    
    try:
        notification_msg = WebSocketMessage(
            type=WebSocketMessageType.SYSTEM_NOTIFICATION,
            timestamp=None,
            data=SystemNotification(**notification_data).dict()
        )
        
        await manager.broadcast_system_notification(notification_msg)
        
    except Exception as e:
        logger.error(f"Failed to send system notification: {e}")


# Export the connection manager for use by other modules
__all__ = ["manager", "send_job_progress_update", "send_job_completed", "send_system_notification"]