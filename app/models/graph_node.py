"""Graph node models for multi-layer visualization system."""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, Relationship, JSON, Column
from sqlalchemy import Text


class NodeType(str, Enum):
    """Types of nodes in the graph."""
    # Layer 3: Portfolio
    PROJECT = "project"
    
    # Layer 2: Project components
    DOCS_SUBGRAPH = "docs_subgraph"
    RESOURCES = "resources"
    GITHUB_REPO = "github_repo"
    TASKS_EPICS = "tasks_epics"
    
    # Layer 1: Documentation
    DOCUMENT = "document"
    DOCUMENT_VERSION = "document_version"


class EdgeType(str, Enum):
    """Types of edges between nodes."""
    # Cross-project relationships
    DEPENDS_ON = "depends_on"
    RELATED_TO = "related_to"
    BLOCKS = "blocks"
    
    # Component relationships
    CONTAINS = "contains"
    REFERENCES = "references"
    IMPLEMENTS = "implements"
    
    # Document relationships
    DERIVED_FROM = "derived_from"
    SUPERSEDES = "supersedes"
    LINKS_TO = "links_to"


class GraphLayer(str, Enum):
    """Graph visualization layers."""
    PORTFOLIO = "portfolio"  # Layer 3: All projects
    PROJECT = "project"      # Layer 2: Project components
    DOCUMENTATION = "documentation"  # Layer 1: Docs canvas


class GraphNode(SQLModel, table=True):
    """Base model for all graph nodes."""
    __tablename__ = "graph_nodes"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    node_type: NodeType = Field(index=True)
    layer: GraphLayer = Field(index=True)
    
    # Display properties
    label: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # Canvas position
    position_x: float = Field(default=0.0)
    position_y: float = Field(default=0.0)
    position_z: int = Field(default=0)  # For stacking versions
    
    # Visual properties
    width: float = Field(default=300.0)
    height: float = Field(default=200.0)
    color: Optional[str] = Field(default=None)
    is_expanded: bool = Field(default=False)
    
    # Relationships
    parent_id: Optional[UUID] = Field(default=None, foreign_key="graph_nodes.id", index=True)
    project_id: Optional[UUID] = Field(default=None, foreign_key="projects.id", index=True)
    
    # Content (flexible JSON for different node types)
    data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = Field(default=None, foreign_key="users.id")
    
    # Relationships
    edges_out: List["GraphEdge"] = Relationship(
        back_populates="source_node",
        sa_relationship_kwargs={"foreign_keys": "GraphEdge.source_id"}
    )
    edges_in: List["GraphEdge"] = Relationship(
        back_populates="target_node",
        sa_relationship_kwargs={"foreign_keys": "GraphEdge.target_id"}
    )


class GraphEdge(SQLModel, table=True):
    """Edges connecting graph nodes."""
    __tablename__ = "graph_edges"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    edge_type: EdgeType = Field(index=True)
    
    # Source and target nodes
    source_id: UUID = Field(foreign_key="graph_nodes.id", index=True)
    target_id: UUID = Field(foreign_key="graph_nodes.id", index=True)
    
    # Display properties
    label: Optional[str] = Field(default=None)
    color: Optional[str] = Field(default=None)
    is_animated: bool = Field(default=False)
    
    # Edge metadata
    data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    source_node: GraphNode = Relationship(
        back_populates="edges_out",
        sa_relationship_kwargs={"foreign_keys": "[GraphEdge.source_id]"}
    )
    target_node: GraphNode = Relationship(
        back_populates="edges_in",
        sa_relationship_kwargs={"foreign_keys": "[GraphEdge.target_id]"}
    )


class DocumentNode(SQLModel, table=True):
    """Specialized model for document nodes with versioning."""
    __tablename__ = "document_nodes"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    graph_node_id: UUID = Field(foreign_key="graph_nodes.id", unique=True, index=True)
    
    # Document metadata
    title: str = Field(max_length=500)
    doc_type: str = Field(max_length=100)  # e.g., "PRD", "TechnicalSpec", "API Doc"
    
    # Content
    content: str = Field(default="", sa_column=Column(Text))
    content_format: str = Field(default="markdown")  # markdown, html, plain
    
    # Versioning
    version: int = Field(default=1)
    parent_version_id: Optional[UUID] = Field(default=None, foreign_key="document_nodes.id")
    is_latest: bool = Field(default=True, index=True)
    
    # Generation status
    is_generating: bool = Field(default=False)
    generation_progress: float = Field(default=0.0)  # 0.0 to 1.0
    generated_by_agent: Optional[str] = Field(default=None)
    
    # Metadata
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    project_id: UUID = Field(foreign_key="projects.id", index=True)


class ResourceNode(SQLModel, table=True):
    """Resources linked to projects (URLs, files, references)."""
    __tablename__ = "resource_nodes"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    graph_node_id: UUID = Field(foreign_key="graph_nodes.id", unique=True, index=True)
    
    # Resource details
    title: str = Field(max_length=500)
    resource_type: str = Field(max_length=100)  # url, file, reference, api
    url: Optional[str] = Field(default=None)
    file_path: Optional[str] = Field(default=None)
    
    # Content/metadata
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    project_id: UUID = Field(foreign_key="projects.id", index=True)


class GraphSnapshot(SQLModel, table=True):
    """Snapshots of graph state for versioning/history."""
    __tablename__ = "graph_snapshots"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    layer: GraphLayer = Field(index=True)
    
    # Snapshot data
    nodes: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    edges: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Metadata
    label: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = Field(default=None, foreign_key="users.id")


# Pydantic models for API responses
class NodePosition(SQLModel):
    """Node position on canvas."""
    x: float
    y: float
    z: int = 0


class GraphNodeRead(SQLModel):
    """API response model for graph nodes."""
    id: UUID
    node_type: NodeType
    layer: GraphLayer
    label: str
    description: Optional[str]
    position: NodePosition
    width: float
    height: float
    color: Optional[str]
    is_expanded: bool
    data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class GraphEdgeRead(SQLModel):
    """API response model for graph edges."""
    id: UUID
    edge_type: EdgeType
    source_id: UUID
    target_id: UUID
    label: Optional[str]
    color: Optional[str]
    is_animated: bool
    data: Dict[str, Any]


class GraphViewResponse(SQLModel):
    """Complete graph view for a layer."""
    layer: GraphLayer
    nodes: List[GraphNodeRead]
    edges: List[GraphEdgeRead]
    project_id: Optional[UUID] = None


class DocumentStreamEvent(SQLModel):
    """Real-time document generation event."""
    event_type: str  # "content_chunk", "complete", "error"
    document_id: UUID
    content_chunk: Optional[str] = None
    progress: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
