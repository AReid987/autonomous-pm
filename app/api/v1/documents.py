"""Document generation and management endpoints."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from pydantic import BaseModel

from app.database import get_session
from app.models import DocumentNode, Project, GraphNode
from app.services.doc_generator import SwarmCoordinator, STANDARD_DOC_TEMPLATES
from app.services.streaming import create_sse_response, document_stream_generator
from app.services.version_manager import VersionManager, VersionDiffService

router = APIRouter(prefix="/documents")


class DocumentGenerateRequest(BaseModel):
    """Request to generate documents."""
    project_id: UUID
    doc_types: List[str]
    context: Optional[dict] = None


class DocumentGenerateResponse(BaseModel):
    """Response from document generation."""
    document_ids: List[UUID]
    message: str


class DocumentListResponse(BaseModel):
    """Document list item."""
    id: UUID
    title: str
    doc_type: str
    version: int
    is_latest: bool
    is_generating: bool
    generation_progress: float
    created_at: str


@router.get("/templates")
async def list_document_templates():
    """List available document templates."""
    return [
        {
            "doc_type": template.doc_type,
            "title": template.title,
            "dependencies": template.dependencies,
            "estimated_tokens": template.estimated_tokens
        }
        for template in STANDARD_DOC_TEMPLATES
    ]


@router.post("/generate", response_model=DocumentGenerateResponse)
async def generate_documents(
    request: DocumentGenerateRequest,
    session: Session = Depends(get_session)
):
    """
    Generate multiple documents in parallel for a project.
    
    Documents are generated respecting dependencies (e.g., TechnicalSpec 
    depends on PRD). Real-time updates are sent via WebSocket to 
    /ws/project/{project_id}.
    """
    # Verify project exists
    project = session.get(Project, request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate doc types
    valid_types = {t.doc_type for t in STANDARD_DOC_TEMPLATES}
    invalid_types = set(request.doc_types) - valid_types
    if invalid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid doc types: {invalid_types}"
        )
    
    # Build context
    context = request.context or {}
    context.update({
        "project_name": project.name,
        "description": project.description or "",
    })
    
    # Generate documents in parallel
    coordinator = SwarmCoordinator(session)
    doc_ids = await coordinator.generate_documents_parallel(
        project_id=request.project_id,
        doc_types=request.doc_types,
        context=context
    )
    
    return DocumentGenerateResponse(
        document_ids=doc_ids,
        message=f"Generated {len(doc_ids)} documents"
    )


@router.get("/project/{project_id}", response_model=List[DocumentListResponse])
async def list_project_documents(
    project_id: UUID,
    include_old_versions: bool = Query(default=False),
    session: Session = Depends(get_session)
):
    """List all documents for a project."""
    query = select(DocumentNode).where(DocumentNode.project_id == project_id)
    
    if not include_old_versions:
        query = query.where(DocumentNode.is_latest == True)
    
    docs = session.exec(query).all()
    
    return [
        DocumentListResponse(
            id=doc.id,
            title=doc.title,
            doc_type=doc.doc_type,
            version=doc.version,
            is_latest=doc.is_latest,
            is_generating=doc.is_generating,
            generation_progress=doc.generation_progress,
            created_at=doc.created_at.isoformat()
        )
        for doc in docs
    ]


@router.get("/{document_id}")
async def get_document(
    document_id: UUID,
    session: Session = Depends(get_session)
):
    """Get a specific document with full content."""
    doc = session.get(DocumentNode, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": doc.id,
        "title": doc.title,
        "doc_type": doc.doc_type,
        "content": doc.content,
        "content_format": doc.content_format,
        "version": doc.version,
        "is_latest": doc.is_latest,
        "parent_version_id": doc.parent_version_id,
        "tags": doc.tags,
        "metadata": doc.metadata,
        "created_at": doc.created_at.isoformat(),
        "updated_at": doc.updated_at.isoformat(),
    }


@router.get("/stream/{document_id}")
async def stream_document_generation(
    document_id: UUID,
    session: Session = Depends(get_session)
):
    """
    Stream document generation progress via Server-Sent Events.
    
    Connect to this endpoint to receive real-time updates as a document
    is being generated.
    """
    doc = session.get(DocumentNode, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not doc.is_generating:
        raise HTTPException(
            status_code=400,
            detail="Document generation already complete"
        )
    
    # Create a generator that simulates streaming
    # In production, this would connect to the actual generation stream
    async def content_generator():
        # Yield existing content in chunks
        chunk_size = 100
        for i in range(0, len(doc.content), chunk_size):
            yield doc.content[i:i + chunk_size]
    
    return create_sse_response(
        document_stream_generator(document_id, content_generator())
    )


@router.put("/{document_id}")
async def update_document(
    document_id: UUID,
    content: str,
    create_version: bool = Query(default=True),
    session: Session = Depends(get_session)
):
    """
    Update a document's content.
    
    If create_version=True (default), creates a new version that stacks on top.
    If False, overwrites the existing version.
    """
    doc = session.get(DocumentNode, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if create_version:
        # Mark current version as not latest
        doc.is_latest = False
        session.add(doc)
        
        # Create new version
        new_doc = DocumentNode(
            graph_node_id=doc.graph_node_id,
            title=doc.title,
            doc_type=doc.doc_type,
            content=content,
            content_format=doc.content_format,
            version=doc.version + 1,
            parent_version_id=doc.id,
            is_latest=True,
            project_id=doc.project_id,
            tags=doc.tags,
            metadata=doc.metadata
        )
        session.add(new_doc)
        
        # Update graph node position (stack vertically)
        graph_node = session.get(GraphNode, doc.graph_node_id)
        if graph_node:
            # Create new graph node for version (stacked on top)
            new_graph_node = GraphNode(
                node_type=graph_node.node_type,
                layer=graph_node.layer,
                label=f"{graph_node.label} v{new_doc.version}",
                description=graph_node.description,
                position_x=graph_node.position_x,
                position_y=graph_node.position_y,
                position_z=graph_node.position_z + 1,  # Stack on top
                width=graph_node.width,
                height=graph_node.height,
                color=graph_node.color,
                parent_id=graph_node.id,
                project_id=graph_node.project_id,
                data=graph_node.data
            )
            session.add(new_graph_node)
            session.commit()
            session.refresh(new_graph_node)
            
            # Update document to point to new graph node
            new_doc.graph_node_id = new_graph_node.id
            session.add(new_doc)
        
        session.commit()
        session.refresh(new_doc)
        
        return {
            "id": new_doc.id,
            "message": f"Created version {new_doc.version}",
            "version": new_doc.version
        }
    else:
        # Update existing version
        doc.content = content
        session.add(doc)
        session.commit()
        
        return {
            "id": doc.id,
            "message": "Document updated",
            "version": doc.version
        }


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    delete_all_versions: bool = Query(default=False),
    session: Session = Depends(get_session)
):
    """
    Delete a document.
    
    If delete_all_versions=True, deletes all versions of this document.
    Otherwise, only deletes the specified version.
    """
    doc = session.get(DocumentNode, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if delete_all_versions:
        # Find all versions (parent and children)
        root_id = doc.parent_version_id or doc.id
        all_versions = session.exec(
            select(DocumentNode).where(
                (DocumentNode.id == root_id) |
                (DocumentNode.parent_version_id == root_id)
            )
        ).all()
        
        for version in all_versions:
            session.delete(version)
        
        session.commit()
        return {"message": f"Deleted {len(all_versions)} versions"}
    else:
        session.delete(doc)
        session.commit()
        return {"message": "Document deleted"}



# Version Management Endpoints

@router.get("/{document_id}/versions")
async def get_document_versions(
    document_id: UUID,
    session: Session = Depends(get_session)
):
    """Get all versions of a document in stack order."""
    version_manager = VersionManager(session)
    
    try:
        stack = version_manager.get_version_stack(document_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return {
        "root_id": stack.root_id,
        "total_versions": stack.get_stack_height(),
        "latest_version": stack.get_latest().version,
        "versions": [
            {
                "id": v.id,
                "version": v.version,
                "is_latest": v.is_latest,
                "created_at": v.created_at.isoformat(),
                "content_length": len(v.content),
                "parent_version_id": v.parent_version_id
            }
            for v in stack.versions
        ]
    }


@router.post("/{document_id}/versions")
async def create_document_version(
    document_id: UUID,
    content: str,
    metadata: Optional[dict] = None,
    session: Session = Depends(get_session)
):
    """Create a new version of a document (stacks on top)."""
    version_manager = VersionManager(session)
    
    try:
        new_version = version_manager.create_new_version(
            document_id=document_id,
            new_content=content,
            metadata=metadata
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return {
        "id": new_version.id,
        "version": new_version.version,
        "message": f"Created version {new_version.version}",
        "graph_node_id": new_version.graph_node_id
    }


@router.post("/{document_id}/revert/{version_number}")
async def revert_to_version(
    document_id: UUID,
    version_number: int,
    session: Session = Depends(get_session)
):
    """Revert to a specific version by creating a new version with that content."""
    version_manager = VersionManager(session)
    
    try:
        new_version = version_manager.revert_to_version(document_id, version_number)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return {
        "id": new_version.id,
        "version": new_version.version,
        "message": f"Reverted to version {version_number} (created as v{new_version.version})"
    }


@router.post("/{document_id}/collapse")
async def collapse_version_stack(
    document_id: UUID,
    session: Session = Depends(get_session)
):
    """Collapse version stack, keeping only the latest version."""
    version_manager = VersionManager(session)
    
    try:
        deleted_ids = version_manager.collapse_stack(document_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return {
        "message": f"Collapsed stack, deleted {len(deleted_ids)} versions",
        "deleted_count": len(deleted_ids)
    }


@router.get("/{document_id}/compare/{version_a}/{version_b}")
async def compare_versions(
    document_id: UUID,
    version_a: int,
    version_b: int,
    session: Session = Depends(get_session)
):
    """Compare two versions of a document."""
    version_manager = VersionManager(session)
    
    try:
        comparison = version_manager.compare_versions(document_id, version_a, version_b)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    # Get actual content for diff
    stack = version_manager.get_version_stack(document_id)
    doc_a = stack.get_version(version_a)
    doc_b = stack.get_version(version_b)
    
    if doc_a and doc_b:
        diff_result = VersionDiffService.compute_diff(doc_a.content, doc_b.content)
        similarity = VersionDiffService.compute_similarity(doc_a.content, doc_b.content)
        
        comparison.update({
            "diff": diff_result,
            "similarity": similarity
        })
    
    return comparison


@router.get("/{document_id}/stack-positions")
async def get_stack_positions(
    document_id: UUID,
    session: Session = Depends(get_session)
):
    """Get visual positions of all versions in the stack."""
    version_manager = VersionManager(session)
    
    try:
        positions = version_manager.get_version_graph_positions(document_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return {
        "positions": [
            {
                "node_id": str(node_id),
                "x": x,
                "y": y,
                "z": z
            }
            for node_id, x, y, z in positions
        ]
    }
