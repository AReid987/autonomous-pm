"""WebSocket and SSE infrastructure for real-time streaming."""
import asyncio
import json
from typing import Dict, Set, Optional, Any
from uuid import UUID
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from starlette.responses import StreamingResponse


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        # Project-level connections: project_id -> set of websockets
        self.project_connections: Dict[str, Set[WebSocket]] = {}
        
        # Document-level connections: document_id -> set of websockets
        self.document_connections: Dict[str, Set[WebSocket]] = {}
        
        # Global connections for portfolio view
        self.global_connections: Set[WebSocket] = set()
        
    async def connect(self, websocket: WebSocket, scope: str = "global", scope_id: Optional[str] = None):
        """Connect a websocket to a specific scope."""
        await websocket.accept()
        
        if scope == "global":
            self.global_connections.add(websocket)
        elif scope == "project" and scope_id:
            if scope_id not in self.project_connections:
                self.project_connections[scope_id] = set()
            self.project_connections[scope_id].add(websocket)
        elif scope == "document" and scope_id:
            if scope_id not in self.document_connections:
                self.document_connections[scope_id] = set()
            self.document_connections[scope_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, scope: str = "global", scope_id: Optional[str] = None):
        """Disconnect a websocket from a specific scope."""
        if scope == "global":
            self.global_connections.discard(websocket)
        elif scope == "project" and scope_id:
            if scope_id in self.project_connections:
                self.project_connections[scope_id].discard(websocket)
                if not self.project_connections[scope_id]:
                    del self.project_connections[scope_id]
        elif scope == "document" and scope_id:
            if scope_id in self.document_connections:
                self.document_connections[scope_id].discard(websocket)
                if not self.document_connections[scope_id]:
                    del self.document_connections[scope_id]
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific websocket."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending message: {e}")
    
    async def broadcast_to_project(self, project_id: str, message: Dict[str, Any]):
        """Broadcast a message to all connections watching a project."""
        if project_id in self.project_connections:
            disconnected = set()
            for connection in self.project_connections[project_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.add(connection)
            
            # Clean up disconnected sockets
            for connection in disconnected:
                self.project_connections[project_id].discard(connection)
    
    async def broadcast_to_document(self, document_id: str, message: Dict[str, Any]):
        """Broadcast a message to all connections watching a document."""
        if document_id in self.document_connections:
            disconnected = set()
            for connection in self.document_connections[document_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.add(connection)
            
            # Clean up disconnected sockets
            for connection in disconnected:
                self.document_connections[document_id].discard(connection)
    
    async def broadcast_global(self, message: Dict[str, Any]):
        """Broadcast a message to all global connections."""
        disconnected = set()
        for connection in self.global_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # Clean up disconnected sockets
        for connection in disconnected:
            self.global_connections.discard(connection)


# Global connection manager instance
manager = ConnectionManager()


class StreamEvent:
    """Base class for stream events."""
    
    def __init__(self, event_type: str, data: Dict[str, Any]):
        self.event_type = event_type
        self.data = data
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "event": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp
        }
    
    def to_sse(self) -> str:
        """Convert to SSE format."""
        return f"event: {self.event_type}\ndata: {json.dumps(self.data)}\n\n"


class DocumentStreamEvent(StreamEvent):
    """Event for document generation streaming."""
    
    def __init__(
        self,
        document_id: UUID,
        event_type: str,
        content_chunk: Optional[str] = None,
        progress: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        data = {
            "document_id": str(document_id),
            "progress": progress,
        }
        
        if content_chunk:
            data["content_chunk"] = content_chunk
        
        if metadata:
            data["metadata"] = metadata
        
        super().__init__(event_type, data)


class NodeUpdateEvent(StreamEvent):
    """Event for node updates (creation, position changes, etc)."""
    
    def __init__(
        self,
        node_id: UUID,
        update_type: str,
        node_data: Dict[str, Any]
    ):
        data = {
            "node_id": str(node_id),
            "update_type": update_type,
            "node_data": node_data
        }
        super().__init__("node_update", data)


class EdgeUpdateEvent(StreamEvent):
    """Event for edge updates."""
    
    def __init__(
        self,
        edge_id: UUID,
        update_type: str,
        edge_data: Dict[str, Any]
    ):
        data = {
            "edge_id": str(edge_id),
            "update_type": update_type,
            "edge_data": edge_data
        }
        super().__init__("edge_update", data)


async def document_stream_generator(document_id: UUID, content_generator):
    """
    Generator for streaming document content via SSE.
    
    Args:
        document_id: ID of the document being generated
        content_generator: Async generator that yields content chunks
    """
    try:
        # Send start event
        start_event = DocumentStreamEvent(
            document_id=document_id,
            event_type="start",
            progress=0.0
        )
        yield start_event.to_sse()
        
        # Stream content chunks
        total_chars = 0
        async for chunk in content_generator:
            total_chars += len(chunk)
            event = DocumentStreamEvent(
                document_id=document_id,
                event_type="content_chunk",
                content_chunk=chunk,
                progress=min(total_chars / 10000, 1.0)  # Estimate progress
            )
            yield event.to_sse()
            await asyncio.sleep(0)  # Allow other tasks to run
        
        # Send complete event
        complete_event = DocumentStreamEvent(
            document_id=document_id,
            event_type="complete",
            progress=1.0
        )
        yield complete_event.to_sse()
        
    except Exception as e:
        # Send error event
        error_event = DocumentStreamEvent(
            document_id=document_id,
            event_type="error",
            metadata={"error": str(e)}
        )
        yield error_event.to_sse()


def create_sse_response(generator):
    """Create an SSE StreamingResponse from a generator."""
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


async def handle_websocket_connection(
    websocket: WebSocket,
    scope: str = "global",
    scope_id: Optional[str] = None
):
    """
    Generic WebSocket connection handler.
    
    Args:
        websocket: The WebSocket connection
        scope: Connection scope (global, project, document)
        scope_id: ID of the scope (project_id or document_id)
    """
    await manager.connect(websocket, scope, scope_id)
    
    try:
        while True:
            # Wait for messages from client (heartbeat, commands, etc)
            data = await websocket.receive_json()
            
            # Handle different message types
            message_type = data.get("type")
            
            if message_type == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
                    websocket
                )
            elif message_type == "subscribe":
                # Handle subscription to specific events
                pass
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, scope, scope_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, scope, scope_id)


class StreamingQueue:
    """Queue for managing multiple concurrent streams."""
    
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.active_streams: Dict[UUID, asyncio.Task] = {}
        self.queue: asyncio.Queue = asyncio.Queue()
        
    async def add_stream(self, document_id: UUID, stream_task):
        """Add a new stream to the queue."""
        if len(self.active_streams) >= self.max_concurrent:
            await self.queue.put((document_id, stream_task))
        else:
            task = asyncio.create_task(stream_task)
            self.active_streams[document_id] = task
            task.add_done_callback(lambda _: self._on_stream_complete(document_id))
    
    def _on_stream_complete(self, document_id: UUID):
        """Handle stream completion."""
        if document_id in self.active_streams:
            del self.active_streams[document_id]
        
        # Start next queued stream if available
        if not self.queue.empty():
            asyncio.create_task(self._start_next_stream())
    
    async def _start_next_stream(self):
        """Start the next stream from the queue."""
        if not self.queue.empty():
            document_id, stream_task = await self.queue.get()
            task = asyncio.create_task(stream_task)
            self.active_streams[document_id] = task
            task.add_done_callback(lambda _: self._on_stream_complete(document_id))


# Global streaming queue
streaming_queue = StreamingQueue(max_concurrent=5)
