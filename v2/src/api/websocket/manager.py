#!/usr/bin/env python3
"""
Theodore v2 WebSocket Manager

Comprehensive WebSocket connection management with heartbeat,
subscription handling, and message broadcasting.
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Set, List, Optional, Any
from fastapi import WebSocket

from ...infrastructure.observability.logging import get_logger
from ...infrastructure.observability.metrics import get_metrics_collector
from ..models.websocket import (
    WebSocketMessage, WebSocketMessageType, ConnectionMetadata,
    HeartbeatMessage, ErrorMessage
)

logger = get_logger(__name__)
metrics = get_metrics_collector()


class WebSocketManager:
    """
    Comprehensive WebSocket connection manager with advanced features
    """
    
    def __init__(self):
        # Connection storage
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, ConnectionMetadata] = {}
        
        # Subscription management
        self.job_subscribers: Dict[str, Set[str]] = {}  # job_id -> connection_ids
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.topic_subscribers: Dict[str, Set[str]] = {}  # topic -> connection_ids
        
        # Background tasks
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        self.heartbeat_interval = 30  # seconds
        self.cleanup_interval = 300  # 5 minutes
        
        # Statistics
        self.total_connections = 0
        self.total_messages_sent = 0
        
    async def connect(
        self, 
        websocket: WebSocket, 
        connection_type: str = "general",
        user_id: Optional[str] = None,
        client_info: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Accept new WebSocket connection and set up metadata
        
        Args:
            websocket: WebSocket connection
            connection_type: Type of connection (progress, notifications, monitoring)
            user_id: User ID if authenticated
            client_info: Client information (user agent, IP, etc.)
            
        Returns:
            Connection ID
        """
        
        try:
            # Accept the connection
            await websocket.accept()
            
            # Generate unique connection ID
            connection_id = str(uuid.uuid4())
            
            # Store connection
            self.active_connections[connection_id] = websocket
            
            # Create metadata
            metadata = ConnectionMetadata(
                connection_id=connection_id,
                user_id=user_id,
                connection_type=connection_type,
                connected_at=datetime.now(timezone.utc),
                last_heartbeat=datetime.now(timezone.utc),
                subscriptions=[],
                client_info=client_info or {}
            )
            
            self.connection_metadata[connection_id] = metadata
            
            # Track user connections
            if user_id:
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = set()
                self.user_connections[user_id].add(connection_id)
            
            # Update statistics
            self.total_connections += 1
            metrics.increment_counter("websocket_connections_total")
            metrics.increment_gauge("websocket_active_connections")
            
            logger.info(
                f"WebSocket connected: {connection_id}",
                extra={
                    "connection_id": connection_id,
                    "connection_type": connection_type,
                    "user_id": user_id
                }
            )
            
            # Send connection acknowledgment
            await self._send_connection_ack(connection_id)
            
            return connection_id
            
        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection: {e}", exc_info=True)
            raise
    
    async def disconnect(self, connection_id: str):
        """
        Clean up WebSocket connection
        
        Args:
            connection_id: Connection to disconnect
        """
        
        try:
            # Get metadata before cleanup
            metadata = self.connection_metadata.get(connection_id)
            
            # Remove from active connections
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
            
            # Remove metadata
            if connection_id in self.connection_metadata:
                del self.connection_metadata[connection_id]
            
            # Remove from job subscriptions
            for job_id, subscribers in self.job_subscribers.items():
                subscribers.discard(connection_id)
            
            # Remove from topic subscriptions
            for topic, subscribers in self.topic_subscribers.items():
                subscribers.discard(connection_id)
            
            # Remove from user connections
            if metadata and metadata.user_id:
                user_connections = self.user_connections.get(metadata.user_id, set())
                user_connections.discard(connection_id)
                if not user_connections:
                    del self.user_connections[metadata.user_id]
            
            # Update statistics
            metrics.decrement_gauge("websocket_active_connections")
            
            logger.info(
                f"WebSocket disconnected: {connection_id}",
                extra={
                    "connection_id": connection_id,
                    "user_id": metadata.user_id if metadata else None
                }
            )
            
        except Exception as e:
            logger.error(f"Error during WebSocket disconnect: {e}", exc_info=True)
    
    async def send_message(self, connection_id: str, message: WebSocketMessage) -> bool:
        """
        Send message to specific connection
        
        Args:
            connection_id: Target connection
            message: Message to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        
        if connection_id not in self.active_connections:
            return False
        
        try:
            websocket = self.active_connections[connection_id]
            
            # Set timestamp if not set
            if not message.timestamp:
                message.timestamp = datetime.now(timezone.utc)
            
            # Send message
            await websocket.send_text(message.json())
            
            # Update statistics
            self.total_messages_sent += 1
            metrics.increment_counter("websocket_messages_sent")
            
            # Update last heartbeat if this is a heartbeat
            if message.type == WebSocketMessageType.HEARTBEAT:
                metadata = self.connection_metadata.get(connection_id)
                if metadata:
                    metadata.last_heartbeat = datetime.now(timezone.utc)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to {connection_id}: {e}")
            
            # Remove broken connection
            await self.disconnect(connection_id)
            return False
    
    async def broadcast_to_subscribers(self, job_id: str, message: WebSocketMessage):
        """
        Broadcast message to all job subscribers
        
        Args:
            job_id: Job ID to broadcast to
            message: Message to broadcast
        """
        
        if job_id not in self.job_subscribers:
            return
        
        # Get list of subscribers (copy to avoid modification during iteration)
        subscribers = list(self.job_subscribers[job_id])
        
        # Send to all subscribers
        for connection_id in subscribers:
            await self.send_message(connection_id, message)
    
    async def broadcast_to_user(self, user_id: str, message: WebSocketMessage):
        """
        Broadcast message to all connections for a user
        
        Args:
            user_id: User ID to broadcast to
            message: Message to broadcast
        """
        
        if user_id not in self.user_connections:
            return
        
        # Get user connections
        connections = list(self.user_connections[user_id])
        
        # Send to all user connections
        for connection_id in connections:
            await self.send_message(connection_id, message)
    
    async def broadcast_to_all(self, message: WebSocketMessage):
        """
        Broadcast message to all active connections
        
        Args:
            message: Message to broadcast
        """
        
        # Get all connection IDs
        connection_ids = list(self.active_connections.keys())
        
        # Send to all connections
        for connection_id in connection_ids:
            await self.send_message(connection_id, message)
    
    def subscribe_to_job(self, connection_id: str, job_id: str):
        """
        Subscribe connection to job updates
        
        Args:
            connection_id: Connection to subscribe
            job_id: Job to subscribe to
        """
        
        if job_id not in self.job_subscribers:
            self.job_subscribers[job_id] = set()
        
        self.job_subscribers[job_id].add(connection_id)
        
        # Update metadata
        metadata = self.connection_metadata.get(connection_id)
        if metadata and job_id not in metadata.subscriptions:
            metadata.subscriptions.append(job_id)
        
        logger.debug(f"Connection {connection_id} subscribed to job {job_id}")
    
    def unsubscribe_from_job(self, connection_id: str, job_id: str):
        """
        Unsubscribe connection from job updates
        
        Args:
            connection_id: Connection to unsubscribe
            job_id: Job to unsubscribe from
        """
        
        if job_id in self.job_subscribers:
            self.job_subscribers[job_id].discard(connection_id)
            
            # Remove empty subscription sets
            if not self.job_subscribers[job_id]:
                del self.job_subscribers[job_id]
        
        # Update metadata
        metadata = self.connection_metadata.get(connection_id)
        if metadata and job_id in metadata.subscriptions:
            metadata.subscriptions.remove(job_id)
        
        logger.debug(f"Connection {connection_id} unsubscribed from job {job_id}")
    
    def subscribe_to_topic(self, connection_id: str, topic: str):
        """
        Subscribe connection to topic updates
        
        Args:
            connection_id: Connection to subscribe
            topic: Topic to subscribe to
        """
        
        if topic not in self.topic_subscribers:
            self.topic_subscribers[topic] = set()
        
        self.topic_subscribers[topic].add(connection_id)
        
        logger.debug(f"Connection {connection_id} subscribed to topic {topic}")
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)
    
    def get_user_connection_count(self, user_id: str) -> int:
        """Get number of connections for a user"""
        return len(self.user_connections.get(user_id, set()))
    
    def get_job_subscriber_count(self, job_id: str) -> int:
        """Get number of subscribers for a job"""
        return len(self.job_subscribers.get(job_id, set()))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics"""
        return {
            "active_connections": len(self.active_connections),
            "total_connections": self.total_connections,
            "total_messages_sent": self.total_messages_sent,
            "job_subscriptions": len(self.job_subscribers),
            "topic_subscriptions": len(self.topic_subscribers),
            "user_connections": len(self.user_connections)
        }
    
    async def start_heartbeat(self):
        """Start heartbeat background task"""
        if self.heartbeat_task and not self.heartbeat_task.done():
            return
        
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("WebSocket heartbeat started")
    
    async def shutdown(self):
        """Shutdown WebSocket manager"""
        # Cancel background tasks
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        # Close all connections
        for connection_id in list(self.active_connections.keys()):
            await self.disconnect(connection_id)
        
        logger.info("WebSocket manager shutdown complete")
    
    async def _send_connection_ack(self, connection_id: str):
        """Send connection acknowledgment message"""
        
        metadata = self.connection_metadata.get(connection_id)
        if not metadata:
            return
        
        ack_message = WebSocketMessage(
            type=WebSocketMessageType.CONNECTION_ACK,
            timestamp=datetime.now(timezone.utc),
            data={
                "connection_id": connection_id,
                "user_id": metadata.user_id,
                "connection_type": metadata.connection_type,
                "capabilities": [
                    "progress_updates",
                    "job_notifications",
                    "system_notifications",
                    "heartbeat"
                ]
            }
        )
        
        await self.send_message(connection_id, ack_message)
    
    async def _heartbeat_loop(self):
        """Background heartbeat loop"""
        
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                # Send heartbeat to all connections
                heartbeat_message = WebSocketMessage(
                    type=WebSocketMessageType.HEARTBEAT,
                    timestamp=datetime.now(timezone.utc),
                    data=HeartbeatMessage(
                        server_time=datetime.now(timezone.utc),
                        connection_id="server",
                        uptime_seconds=0.0  # Would calculate actual uptime
                    ).dict()
                )
                
                # Send to all active connections
                for connection_id in list(self.active_connections.keys()):
                    await self.send_message(connection_id, heartbeat_message)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}", exc_info=True)
    
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                # Clean up stale connections
                current_time = datetime.now(timezone.utc)
                stale_connections = []
                
                for connection_id, metadata in self.connection_metadata.items():
                    # Check if connection is stale (no heartbeat for 2x interval)
                    time_since_heartbeat = (current_time - metadata.last_heartbeat).total_seconds()
                    
                    if time_since_heartbeat > (self.heartbeat_interval * 2):
                        stale_connections.append(connection_id)
                
                # Remove stale connections
                for connection_id in stale_connections:
                    logger.warning(f"Removing stale WebSocket connection: {connection_id}")
                    await self.disconnect(connection_id)
                
                # Clean up empty subscription sets
                empty_job_subs = [job_id for job_id, subs in self.job_subscribers.items() if not subs]
                for job_id in empty_job_subs:
                    del self.job_subscribers[job_id]
                
                empty_topic_subs = [topic for topic, subs in self.topic_subscribers.items() if not subs]
                for topic in empty_topic_subs:
                    del self.topic_subscribers[topic]
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}", exc_info=True)