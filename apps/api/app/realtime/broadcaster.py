import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class Broadcaster:
    def __init__(self) -> None:
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("WebSocket client connected. Total connections: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)
        logger.info("WebSocket client disconnected. Remaining connections: %d", len(self.active_connections))

    async def broadcast(self, message: dict) -> None:
        if not self.active_connections:
            return
        
        # Use list copy to prevent modification issues during iteration
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as exc:
                logger.warning("Failed to send message to client; removing connection. Error: %s", exc)
                self.active_connections.discard(connection)

broadcaster = Broadcaster()
