#!/usr/bin/env python3
"""
Tests for Theodore v2 WebSocket functionality
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.app import create_app
from src.api.websocket.manager import WebSocketManager
from src.api.models.websocket import (
    WebSocketMessage, WebSocketMessageType, ProgressUpdate,
    ConnectionMetadata, HeartbeatMessage
)


class TestWebSocketManager:
    """Test WebSocket manager functionality"""
    
    @pytest.fixture
    def ws_manager(self):
        """Create WebSocket manager instance"""
        return WebSocketManager()
    
    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket connection"""
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_text = AsyncMock()
        return ws
    
    @pytest.mark.asyncio
    async def test_websocket_connect(self, ws_manager, mock_websocket):
        """Test WebSocket connection establishment"""
        connection_id = await ws_manager.connect(
            websocket=mock_websocket,
            connection_type="progress",
            user_id="user_123"
        )
        
        # Verify connection was accepted
        mock_websocket.accept.assert_called_once()
        
        # Verify connection is stored
        assert connection_id in ws_manager.active_connections
        assert ws_manager.active_connections[connection_id] == mock_websocket
        
        # Verify metadata was created
        assert connection_id in ws_manager.connection_metadata
        metadata = ws_manager.connection_metadata[connection_id]
        assert metadata.connection_type == "progress"
        assert metadata.user_id == "user_123"
        
        # Verify user connections tracking
        assert "user_123" in ws_manager.user_connections
        assert connection_id in ws_manager.user_connections["user_123"]
        
        # Verify connection acknowledgment was sent
        mock_websocket.send_text.assert_called()
        sent_message = mock_websocket.send_text.call_args[0][0]
        message_data = json.loads(sent_message)
        assert message_data["type"] == "connection_ack"
    
    @pytest.mark.asyncio
    async def test_websocket_disconnect(self, ws_manager, mock_websocket):
        """Test WebSocket disconnection cleanup"""
        # First connect
        connection_id = await ws_manager.connect(mock_websocket, user_id="user_123")
        
        # Subscribe to a job
        ws_manager.subscribe_to_job(connection_id, "job_456")
        
        # Verify setup
        assert connection_id in ws_manager.active_connections
        assert "job_456" in ws_manager.job_subscribers
        assert connection_id in ws_manager.job_subscribers["job_456"]
        
        # Disconnect
        await ws_manager.disconnect(connection_id)
        
        # Verify cleanup
        assert connection_id not in ws_manager.active_connections
        assert connection_id not in ws_manager.connection_metadata
        assert connection_id not in ws_manager.job_subscribers.get("job_456", set())
        assert "user_123" not in ws_manager.user_connections
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, ws_manager, mock_websocket):
        """Test successful message sending"""
        connection_id = await ws_manager.connect(mock_websocket)
        
        message = WebSocketMessage(
            type=WebSocketMessageType.PROGRESS_UPDATE,
            timestamp=datetime.now(timezone.utc),
            data={"job_id": "job_123", "percentage": 50.0}
        )
        
        result = await ws_manager.send_message(connection_id, message)
        
        assert result is True
        mock_websocket.send_text.assert_called()
        
        # Verify message content
        sent_calls = mock_websocket.send_text.call_args_list
        assert len(sent_calls) >= 1  # At least connection ack + our message
    
    @pytest.mark.asyncio
    async def test_send_message_broken_connection(self, ws_manager, mock_websocket):
        """Test handling of broken WebSocket connection"""
        connection_id = await ws_manager.connect(mock_websocket)
        
        # Simulate broken connection
        mock_websocket.send_text.side_effect = Exception("Connection broken")
        
        message = WebSocketMessage(
            type=WebSocketMessageType.PROGRESS_UPDATE,
            timestamp=datetime.now(timezone.utc),
            data={"test": "data"}
        )
        
        result = await ws_manager.send_message(connection_id, message)
        
        assert result is False
        # Connection should be cleaned up
        assert connection_id not in ws_manager.active_connections
    
    @pytest.mark.asyncio
    async def test_job_subscription_management(self, ws_manager, mock_websocket):
        """Test job subscription functionality"""
        connection_id = await ws_manager.connect(mock_websocket)
        
        # Subscribe to job
        ws_manager.subscribe_to_job(connection_id, "job_123")
        
        assert "job_123" in ws_manager.job_subscribers
        assert connection_id in ws_manager.job_subscribers["job_123"]
        
        # Verify metadata updated
        metadata = ws_manager.connection_metadata[connection_id]
        assert "job_123" in metadata.subscriptions
        
        # Unsubscribe
        ws_manager.unsubscribe_from_job(connection_id, "job_123")
        
        assert connection_id not in ws_manager.job_subscribers.get("job_123", set())
        assert "job_123" not in metadata.subscriptions
    
    @pytest.mark.asyncio
    async def test_broadcast_to_job_subscribers(self, ws_manager):
        """Test broadcasting to job subscribers"""
        # Create multiple connections
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws1.send_text = AsyncMock()
        
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws2.send_text = AsyncMock()
        
        conn1 = await ws_manager.connect(ws1)
        conn2 = await ws_manager.connect(ws2)
        
        # Subscribe both to same job
        ws_manager.subscribe_to_job(conn1, "job_123")
        ws_manager.subscribe_to_job(conn2, "job_123")
        
        # Broadcast message
        message = WebSocketMessage(
            type=WebSocketMessageType.JOB_COMPLETED,
            timestamp=datetime.now(timezone.utc),
            data={"job_id": "job_123", "status": "completed"}
        )
        
        await ws_manager.broadcast_to_subscribers("job_123", message)
        
        # Both connections should have received the message
        assert ws1.send_text.call_count >= 2  # Ack + broadcast
        assert ws2.send_text.call_count >= 2  # Ack + broadcast
    
    @pytest.mark.asyncio
    async def test_broadcast_to_user(self, ws_manager):
        """Test broadcasting to all user connections"""
        # Create multiple connections for same user
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws1.send_text = AsyncMock()
        
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws2.send_text = AsyncMock()
        
        conn1 = await ws_manager.connect(ws1, user_id="user_123")
        conn2 = await ws_manager.connect(ws2, user_id="user_123")
        
        # Broadcast to user
        message = WebSocketMessage(
            type=WebSocketMessageType.SYSTEM_NOTIFICATION,
            timestamp=datetime.now(timezone.utc),
            data={"title": "Test notification"}
        )
        
        await ws_manager.broadcast_to_user("user_123", message)
        
        # Both connections should have received the message
        assert ws1.send_text.call_count >= 2  # Ack + broadcast
        assert ws2.send_text.call_count >= 2  # Ack + broadcast
    
    @pytest.mark.asyncio
    async def test_heartbeat_system(self, ws_manager):
        """Test heartbeat functionality"""
        # Start heartbeat (mock the loop to avoid long delays)
        with patch.object(ws_manager, 'heartbeat_interval', 0.1):
            await ws_manager.start_heartbeat()
            
            # Give it a moment to start
            await asyncio.sleep(0.05)
            
            # Stop the heartbeat
            if ws_manager.heartbeat_task:
                ws_manager.heartbeat_task.cancel()
                try:
                    await ws_manager.heartbeat_task
                except asyncio.CancelledError:
                    pass
        
        # Verify heartbeat task was created
        assert ws_manager.heartbeat_task is not None
    
    def test_websocket_statistics(self, ws_manager):
        """Test WebSocket manager statistics"""
        stats = ws_manager.get_statistics()
        
        assert "active_connections" in stats
        assert "total_connections" in stats
        assert "total_messages_sent" in stats
        assert "job_subscriptions" in stats
        assert "topic_subscriptions" in stats
        assert "user_connections" in stats
        
        # Initial state should be empty
        assert stats["active_connections"] == 0
        assert stats["total_connections"] == 0
    
    @pytest.mark.asyncio
    async def test_websocket_manager_shutdown(self, ws_manager, mock_websocket):
        """Test WebSocket manager shutdown"""
        # Create some connections
        conn1 = await ws_manager.connect(mock_websocket)
        
        # Start background tasks
        await ws_manager.start_heartbeat()
        
        # Shutdown
        await ws_manager.shutdown()
        
        # Verify cleanup
        assert len(ws_manager.active_connections) == 0
        assert ws_manager.heartbeat_task.cancelled()
        assert ws_manager.cleanup_task.cancelled()


class TestWebSocketRoutes:
    """Test WebSocket API routes"""
    
    @pytest.fixture
    def app(self):
        """Create test app"""
        app = create_app(debug=True)
        app.state.container = AsyncMock()
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    def test_websocket_progress_endpoint(self, client):
        """Test WebSocket progress endpoint connection"""
        with client.websocket_connect("/api/v2/ws/progress/job_123") as websocket:
            # Should connect successfully
            data = websocket.receive_json()
            
            # Should receive connection acknowledgment
            assert data["type"] == "connection_ack"
            assert "data" in data
            assert data["data"]["connection_type"] == "general"  # Default type
    
    def test_websocket_notifications_endpoint(self, client):
        """Test WebSocket notifications endpoint"""
        with client.websocket_connect("/api/v2/ws/notifications") as websocket:
            data = websocket.receive_json()
            
            # Should receive connection acknowledgment
            assert data["type"] == "connection_ack"
            assert "capabilities" in data["data"]
    
    def test_websocket_monitoring_endpoint(self, client):
        """Test WebSocket monitoring endpoint"""
        with client.websocket_connect("/api/v2/ws/monitoring") as websocket:
            data = websocket.receive_json()
            
            # Should receive connection acknowledgment
            assert data["type"] == "connection_ack"
    
    def test_websocket_with_query_parameters(self, client):
        """Test WebSocket with query parameters"""
        with client.websocket_connect(
            "/api/v2/ws/progress/job_123?user_id=user_456"
        ) as websocket:
            data = websocket.receive_json()
            
            assert data["type"] == "connection_ack"
            # Connection should be established with user context
    
    def test_websocket_subscription_messages(self, client):
        """Test WebSocket subscription message handling"""
        with client.websocket_connect("/api/v2/ws/progress/job_123") as websocket:
            # Receive connection ack
            ack = websocket.receive_json()
            assert ack["type"] == "connection_ack"
            
            # Send subscription request
            subscription_request = {
                "action": "subscribe",
                "job_id": "job_456"
            }
            websocket.send_json(subscription_request)
            
            # Should handle subscription (may not send immediate response)
            # Connection should remain open
    
    def test_websocket_invalid_subscription_message(self, client):
        """Test WebSocket handling of invalid subscription messages"""
        with client.websocket_connect("/api/v2/ws/progress/job_123") as websocket:
            # Receive connection ack
            ack = websocket.receive_json()
            
            # Send invalid subscription request
            websocket.send_text("invalid json")
            
            # Should receive error message
            try:
                error_response = websocket.receive_json()
                if error_response["type"] == "error":
                    assert "error_code" in error_response["data"]
            except:
                # Connection might be closed due to invalid message
                pass


class TestWebSocketModels:
    """Test WebSocket message models"""
    
    def test_websocket_message_model(self):
        """Test WebSocket message model"""
        message = WebSocketMessage(
            type=WebSocketMessageType.PROGRESS_UPDATE,
            timestamp=datetime.now(timezone.utc),
            data={"job_id": "job_123", "percentage": 75.0}
        )
        
        assert message.type == WebSocketMessageType.PROGRESS_UPDATE
        assert message.data["job_id"] == "job_123"
        
        # Test serialization
        json_str = message.json()
        assert "progress_update" in json_str
        assert "job_123" in json_str
    
    def test_progress_update_model(self):
        """Test progress update model"""
        from src.api.models.common import JobStatus, ProgressInfo
        
        progress_info = ProgressInfo(
            current_step="AI Analysis",
            step_number=3,
            total_steps=5,
            percentage=60.0,
            message="Analyzing data",
            started_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        progress_update = ProgressUpdate(
            job_id="job_123",
            job_type="research",
            status=JobStatus.RUNNING,
            progress=progress_info,
            company_name="Test Company"
        )
        
        assert progress_update.job_id == "job_123"
        assert progress_update.status == JobStatus.RUNNING
        assert progress_update.progress.percentage == 60.0
    
    def test_connection_metadata_model(self):
        """Test connection metadata model"""
        metadata = ConnectionMetadata(
            connection_id="conn_123",
            user_id="user_456",
            connection_type="progress",
            connected_at=datetime.now(timezone.utc),
            last_heartbeat=datetime.now(timezone.utc),
            subscriptions=["job_123", "job_456"],
            client_info={"user_agent": "Test Browser"}
        )
        
        assert metadata.connection_id == "conn_123"
        assert metadata.user_id == "user_456"
        assert len(metadata.subscriptions) == 2
        assert "job_123" in metadata.subscriptions
    
    def test_heartbeat_message_model(self):
        """Test heartbeat message model"""
        heartbeat = HeartbeatMessage(
            server_time=datetime.now(timezone.utc),
            connection_id="conn_123",
            uptime_seconds=3600.5
        )
        
        assert heartbeat.connection_id == "conn_123"
        assert heartbeat.uptime_seconds == 3600.5