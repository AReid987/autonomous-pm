"""Document version management with visual stacking."""
from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime

from sqlmodel import Session, select
from sqlalchemy import desc

from app.models import DocumentNode, GraphNode, GraphEdge, EdgeType
from app.services.streaming import manager


class VersionStack:
    """Manages a stack of document versions."""
    
    def __init__(self, root_document: DocumentNode):
        self.root_id = root_document.id
        self.root_version = root_document
        self.versions: List[DocumentNode] = []
    
    def add_version(self, version: DocumentNode):
        """Add a version to the stack."""
        self.versions.append(version)
    
    def get_latest(self) -> DocumentNode:
        """Get the latest version."""
        return max(self.versions, key=lambda v: v.version)
    
    def get_version(self, version_number: int) -> Optional[DocumentNode]:
        """Get a specific version by number."""
        for v in self.versions:
            if v.version == version_number:
                return v
        return None
    
    def get_stack_height(self) -> int:
        """Get total number of versions in stack."""
        return len(self.versions)


class VersionManager:
    """Manages document versioning and visual stacking."""
    
    # Visual constants for stacking
    STACK_Z_OFFSET = 1  # Z-index increment per version
    STACK_Y_OFFSET = 20  # Slight Y offset for 3D effect
    STACK_OPACITY_DECAY = 0.1  # Opacity reduction per version
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_new_version(
        self,
        document_id: UUID,
        new_content: str,
        metadata: Optional[dict] = None
    ) -> DocumentNode:
        """
        Create a new version of a document and stack it visually.
        
        Returns the new version document.
        """
        # Get current document
        current_doc = self.session.get(DocumentNode, document_id)
        if not current_doc:
            raise ValueError(f"Document {document_id} not found")
        
        # Mark current as not latest
        current_doc.is_latest = False
        self.session.add(current_doc)
        
        # Find root document
        root_id = self._get_root_id(current_doc)
        
        # Get current graph node
        current_graph_node = self.session.get(GraphNode, current_doc.graph_node_id)
        if not current_graph_node:
            raise ValueError(f"Graph node {current_doc.graph_node_id} not found")
        
        # Create new graph node (stacked on top)
        new_graph_node = GraphNode(
            node_type=current_graph_node.node_type,
            layer=current_graph_node.layer,
            label=f"{current_doc.title} v{current_doc.version + 1}",
            description=current_graph_node.description,
            position_x=current_graph_node.position_x,
            position_y=current_graph_node.position_y - self.STACK_Y_OFFSET,  # Slight offset
            position_z=current_graph_node.position_z + self.STACK_Z_OFFSET,  # Stack up
            width=current_graph_node.width,
            height=current_graph_node.height,
            color=current_graph_node.color,
            parent_id=current_graph_node.id,  # Link to previous version's node
            project_id=current_graph_node.project_id,
            data={
                **current_graph_node.data,
                "version": current_doc.version + 1,
                "parent_version_id": str(current_doc.id)
            }
        )
        self.session.add(new_graph_node)
        self.session.commit()
        self.session.refresh(new_graph_node)
        
        # Create new document version
        new_doc = DocumentNode(
            graph_node_id=new_graph_node.id,
            title=current_doc.title,
            doc_type=current_doc.doc_type,
            content=new_content,
            content_format=current_doc.content_format,
            version=current_doc.version + 1,
            parent_version_id=current_doc.id,
            is_latest=True,
            project_id=current_doc.project_id,
            tags=current_doc.tags,
            metadata={**(current_doc.metadata or {}), **(metadata or {})}
        )
        self.session.add(new_doc)
        
        # Create version edge (visual link between versions)
        version_edge = GraphEdge(
            edge_type=EdgeType.SUPERSEDES,
            source_id=new_graph_node.id,
            target_id=current_graph_node.id,
            label=f"v{new_doc.version}",
            is_animated=False,
            data={"version_link": True}
        )
        self.session.add(version_edge)
        
        self.session.commit()
        self.session.refresh(new_doc)
        
        # Broadcast version creation
        self._broadcast_version_created(new_doc, new_graph_node)
        
        return new_doc
    
    def get_version_stack(self, document_id: UUID) -> VersionStack:
        """
        Get all versions of a document as a stack.
        
        Returns a VersionStack object containing all versions.
        """
        doc = self.session.get(DocumentNode, document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")
        
        # Find root document
        root_id = self._get_root_id(doc)
        root_doc = self.session.get(DocumentNode, root_id)
        
        # Get all versions
        versions = self.session.exec(
            select(DocumentNode)
            .where(
                (DocumentNode.id == root_id) |
                (DocumentNode.parent_version_id == root_id)
            )
            .order_by(DocumentNode.version)
        ).all()
        
        stack = VersionStack(root_doc)
        for version in versions:
            stack.add_version(version)
        
        return stack
    
    def collapse_stack(self, document_id: UUID) -> List[UUID]:
        """
        Collapse a version stack, keeping only the latest version.
        
        Returns list of deleted document IDs.
        """
        stack = self.get_version_stack(document_id)
        latest = stack.get_latest()
        
        deleted_ids = []
        for version in stack.versions:
            if version.id != latest.id:
                # Delete graph node
                graph_node = self.session.get(GraphNode, version.graph_node_id)
                if graph_node:
                    self.session.delete(graph_node)
                
                # Delete document
                self.session.delete(version)
                deleted_ids.append(version.id)
        
        self.session.commit()
        
        # Broadcast collapse
        self._broadcast_stack_collapsed(latest.project_id, deleted_ids, latest.id)
        
        return deleted_ids
    
    def expand_stack(self, document_id: UUID) -> List[DocumentNode]:
        """
        Expand a collapsed stack to show all versions.
        
        This is mainly a query operation - returns all versions for display.
        """
        stack = self.get_version_stack(document_id)
        return stack.versions
    
    def revert_to_version(self, document_id: UUID, version_number: int) -> DocumentNode:
        """
        Revert to a specific version by creating a new version with that content.
        
        This creates a new "latest" version with the content from the specified version.
        """
        stack = self.get_version_stack(document_id)
        target_version = stack.get_version(version_number)
        
        if not target_version:
            raise ValueError(f"Version {version_number} not found")
        
        # Create new version with target version's content
        new_version = self.create_new_version(
            document_id=stack.get_latest().id,
            new_content=target_version.content,
            metadata={
                "reverted_from_version": version_number,
                "revert_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return new_version
    
    def compare_versions(
        self,
        document_id: UUID,
        version_a: int,
        version_b: int
    ) -> dict:
        """
        Compare two versions of a document.
        
        Returns diff information between the versions.
        """
        stack = self.get_version_stack(document_id)
        doc_a = stack.get_version(version_a)
        doc_b = stack.get_version(version_b)
        
        if not doc_a or not doc_b:
            raise ValueError("One or both versions not found")
        
        # Simple character-level comparison
        # In production, use a proper diff library like python-diff
        return {
            "version_a": version_a,
            "version_b": version_b,
            "content_a_length": len(doc_a.content),
            "content_b_length": len(doc_b.content),
            "size_diff": len(doc_b.content) - len(doc_a.content),
            "created_at_a": doc_a.created_at.isoformat(),
            "created_at_b": doc_b.created_at.isoformat(),
            # Add actual diff here in production
        }
    
    def get_version_graph_positions(
        self,
        document_id: UUID
    ) -> List[Tuple[UUID, float, float, int]]:
        """
        Get visual positions of all versions in a stack.
        
        Returns list of (node_id, x, y, z) tuples.
        """
        stack = self.get_version_stack(document_id)
        positions = []
        
        for version in stack.versions:
            graph_node = self.session.get(GraphNode, version.graph_node_id)
            if graph_node:
                positions.append((
                    graph_node.id,
                    graph_node.position_x,
                    graph_node.position_y,
                    graph_node.position_z
                ))
        
        return positions
    
    def _get_root_id(self, doc: DocumentNode) -> UUID:
        """Find the root document ID by traversing parent chain."""
        current = doc
        while current.parent_version_id:
            parent = self.session.get(DocumentNode, current.parent_version_id)
            if not parent:
                break
            current = parent
        return current.id
    
    async def _broadcast_version_created(
        self,
        new_doc: DocumentNode,
        new_graph_node: GraphNode
    ):
        """Broadcast version creation to WebSocket clients."""
        await manager.broadcast_to_project(
            str(new_doc.project_id),
            {
                "event": "version_created",
                "data": {
                    "document_id": str(new_doc.id),
                    "version": new_doc.version,
                    "graph_node_id": str(new_graph_node.id),
                    "position": {
                        "x": new_graph_node.position_x,
                        "y": new_graph_node.position_y,
                        "z": new_graph_node.position_z
                    }
                }
            }
        )
    
    async def _broadcast_stack_collapsed(
        self,
        project_id: UUID,
        deleted_ids: List[UUID],
        remaining_id: UUID
    ):
        """Broadcast stack collapse to WebSocket clients."""
        await manager.broadcast_to_project(
            str(project_id),
            {
                "event": "stack_collapsed",
                "data": {
                    "deleted_document_ids": [str(id) for id in deleted_ids],
                    "remaining_document_id": str(remaining_id)
                }
            }
        )


class VersionDiffService:
    """Service for computing diffs between document versions."""
    
    @staticmethod
    def compute_diff(content_a: str, content_b: str) -> dict:
        """
        Compute a diff between two content strings.
        
        In production, use difflib or a more sophisticated diff library.
        """
        import difflib
        
        lines_a = content_a.splitlines()
        lines_b = content_b.splitlines()
        
        diff = difflib.unified_diff(
            lines_a,
            lines_b,
            lineterm='',
            n=3  # Context lines
        )
        
        return {
            "diff_lines": list(diff),
            "added_lines": sum(1 for line in diff if line.startswith('+')),
            "removed_lines": sum(1 for line in diff if line.startswith('-')),
        }
    
    @staticmethod
    def compute_similarity(content_a: str, content_b: str) -> float:
        """
        Compute similarity ratio between two content strings.
        
        Returns value between 0.0 (completely different) and 1.0 (identical).
        """
        import difflib
        
        return difflib.SequenceMatcher(None, content_a, content_b).ratio()
