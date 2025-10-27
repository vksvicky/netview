from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import List, Dict, Any
import json
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    """Manages WebSocket connections and broadcasting"""
    
    def __init__(self):
        # Store active connections
        self.active_connections: List[WebSocket] = []
        # Store connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Store connection metadata
        self.connection_metadata[websocket] = {
            "client_id": client_id or f"client_{len(self.active_connections)}",
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow()
        }
        
        logger.info(f"WebSocket connected: {self.connection_metadata[websocket]['client_id']}")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "message": "Connected to NetView real-time updates",
            "client_id": self.connection_metadata[websocket]["client_id"],
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            client_id = self.connection_metadata.get(websocket, {}).get("client_id", "unknown")
            self.active_connections.remove(websocket)
            if websocket in self.connection_metadata:
                del self.connection_metadata[websocket]
            logger.info(f"WebSocket disconnected: {client_id}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected WebSocket clients"""
        if not self.active_connections:
            return
            
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
            
        # Create a copy of connections to avoid modification during iteration
        connections_to_remove = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                connections_to_remove.append(connection)
        
        # Remove failed connections
        for connection in connections_to_remove:
            self.disconnect(connection)

    async def broadcast_device_update(self, device_data: Dict[str, Any]):
        """Broadcast device status updates"""
        message = {
            "type": "device_update",
            "data": device_data
        }
        await self.broadcast(message)

    async def broadcast_topology_update(self, topology_data: Dict[str, Any]):
        """Broadcast topology changes"""
        message = {
            "type": "topology_update", 
            "data": topology_data
        }
        await self.broadcast(message)

    async def broadcast_notification(self, notification_data: Dict[str, Any]):
        """Broadcast new notifications"""
        message = {
            "type": "notification",
            "data": notification_data
        }
        await self.broadcast(message)

    async def broadcast_system_status(self, status_data: Dict[str, Any]):
        """Broadcast system status updates"""
        message = {
            "type": "system_status",
            "data": status_data
        }
        await self.broadcast(message)

    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)

    def get_connection_info(self) -> List[Dict[str, Any]]:
        """Get information about all active connections"""
        return [
            {
                "client_id": metadata["client_id"],
                "connected_at": metadata["connected_at"].isoformat(),
                "last_ping": metadata["last_ping"].isoformat()
            }
            for metadata in self.connection_metadata.values()
        ]

# Global connection manager instance
manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    # Update last ping time
                    if websocket in manager.connection_metadata:
                        manager.connection_metadata[websocket]["last_ping"] = datetime.utcnow()
                    
                    # Send pong response
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
                    
                elif message_type == "subscribe":
                    # Handle subscription requests (for future filtering)
                    subscriptions = message.get("subscriptions", [])
                    logger.info(f"Client {manager.connection_metadata[websocket]['client_id']} subscribed to: {subscriptions}")
                    
                elif message_type == "unsubscribe":
                    # Handle unsubscription requests
                    subscriptions = message.get("subscriptions", [])
                    logger.info(f"Client {manager.connection_metadata[websocket]['client_id']} unsubscribed from: {subscriptions}")
                    
                else:
                    logger.warning(f"Unknown message type: {message_type}")
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket disconnected")

@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status"""
    return {
        "active_connections": manager.get_connection_count(),
        "connections": manager.get_connection_info(),
        "timestamp": datetime.utcnow().isoformat()
    }

# Export the manager for use in other modules
__all__ = ["router", "manager"]
