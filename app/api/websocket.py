"""WebSocket endpoints for real-time updates."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional

from app.services.streaming import handle_websocket_connection, manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_global_endpoint(websocket: WebSocket):
    """
    Global WebSocket endpoint for portfolio-level updates.
    
    Receives updates about:
    - New projects created
    - Project status changes
    - High-level notifications
    """
    await handle_websocket_connection(websocket, scope="global")


@router.websocket("/ws/project/{project_id}")
async def websocket_project_endpoint(
    websocket: WebSocket,
    project_id: str
):
    """
    Project-level WebSocket endpoint.
    
    Receives updates about:
    - Project component changes
    - Task/Epic updates
    - Resource additions
    - GitHub sync events
    """
    await handle_websocket_connection(websocket, scope="project", scope_id=project_id)


@router.websocket("/ws/document/{document_id}")
async def websocket_document_endpoint(
    websocket: WebSocket,
    document_id: str
):
    """
    Document-level WebSocket endpoint for streaming generation.
    
    Receives:
    - Content chunks as they're generated
    - Progress updates
    - Completion/error events
    """
    await handle_websocket_connection(websocket, scope="document", scope_id=document_id)


@router.websocket("/ws/canvas/{project_id}")
async def websocket_canvas_endpoint(
    websocket: WebSocket,
    project_id: str,
    layer: Optional[str] = Query(default="documentation")
):
    """
    Canvas-level WebSocket for real-time graph updates.
    
    Receives:
    - Node creation/updates/deletions
    - Edge creation/updates/deletions
    - Position changes
    - Multi-user cursor positions (future)
    """
    await handle_websocket_connection(websocket, scope="project", scope_id=project_id)
