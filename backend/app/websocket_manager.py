from fastapi import WebSocket, WebSocketDisconnect, status, HTTPException
from typing import Dict, List, Optional
from app.core.config import settings
from app.api.auth import get_current_user
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # token: websocket
        self.connection_times: Dict[str, datetime] = {}  # token: connect_time

    async def connect(self, websocket: WebSocket, token: Optional[str] = None):
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise WebSocketDisconnect(reason="Token required")

        try:
            username = await get_current_user(token)
            await websocket.accept()
            
            # Check max connections
            if len(self.active_connections) >= settings.websocket_max_connections:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                raise WebSocketDisconnect(reason="Max connections reached")

            self.active_connections[token] = websocket
            self.connection_times[token] = datetime.now()
            logger.info(f"WebSocket connected: {username}")
            
        except HTTPException as e:
            if e.status_code == status.HTTP_401_UNAUTHORIZED:
                error_detail = e.detail
                if isinstance(error_detail, dict):
                    reason = error_detail.get("message", "Authentication failed")
                    code = error_detail.get("code", 40102)
                else:
                    reason = str(error_detail)
                    code = 40102
                
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                raise WebSocketDisconnect(reason=f"{reason} (code: {code})")
            else:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                raise WebSocketDisconnect(reason=str(e.detail))
        except Exception as e:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise WebSocketDisconnect(reason="Internal server error")

    def disconnect(self, websocket: WebSocket):
        for token, ws in list(self.active_connections.items()):
            if ws == websocket:
                self.active_connections.pop(token, None)
                self.connection_times.pop(token, None)
                logger.info(f"WebSocket disconnected: {token[:8]}...")
                break

    async def broadcast(self, message: dict):
        for token, connection in list(self.active_connections.items()):
            try:
                if message.get("type") == "ping":
                    # Handle ping message from client
                    await connection.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
                else:
                    await connection.send_json(message)
            except WebSocketDisconnect:
                self.disconnect(connection)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                self.disconnect(connection)

    def get_connection_count(self) -> int:
        return len(self.active_connections)

websocket_manager = WebSocketManager()
