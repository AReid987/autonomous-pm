"""Parallel agent swarm service for document generation."""
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import Session, select

from app.models import (
    DocumentNode,
    GraphNode,
    GraphEdge,
    NodeType,
    EdgeType,
    GraphLayer,
)
from app.services.streaming import manager, DocumentStreamEvent
from app.config import settings


class DocumentTemplate:
    """Template definition for a document type."""
    
    def __init__(
        self,
        doc_type: str,
        title: str,
        prompt_template: str,
        dependencies: List[str] = None,
        estimated_tokens: int = 2000
    ):
        self.doc_type = doc_type
        self.title = title
        self.prompt_template = prompt_template
        self.dependencies = dependencies or []
        self.estimated_tokens = estimated_tokens


# Standard document templates for software projects
STANDARD_DOC_TEMPLATES = [
    DocumentTemplate(
        doc_type="PRD",
        title="Product Requirements Document",
        prompt_template="""Write a comprehensive Product Requirements Document for {project_name}.

Include:
1. Executive Summary
2. Problem Statement
3. Goals and Objectives
4. User Stories and Use Cases
5. Feature Requirements
6. Success Metrics
7. Timeline and Milestones

Context: {context}""",
        dependencies=[],
        estimated_tokens=3000
    ),
    DocumentTemplate(
        doc_type="TechnicalSpec",
        title="Technical Specification",
        prompt_template="""Write a detailed Technical Specification for {project_name}.

Include:
1. Architecture Overview
2. System Components
3. Data Models
4. API Specifications
5. Security Considerations
6. Performance Requirements
7. Technology Stack

Context: {context}
Requirements: {requirements}""",
        dependencies=["PRD"],
        estimated_tokens=4000
    ),
    DocumentTemplate(
        doc_type="APIDoc",
        title="API Documentation",
        prompt_template="""Write comprehensive API Documentation for {project_name}.

Include:
1. Authentication
2. Endpoints (with request/response examples)
3. Error Codes
4. Rate Limiting
5. Webhooks
6. SDK Examples

Context: {context}
Technical Spec: {technical_spec}""",
        dependencies=["TechnicalSpec"],
        estimated_tokens=3500
    ),
    DocumentTemplate(
        doc_type="UserGuide",
        title="User Guide",
        prompt_template="""Write a user-friendly User Guide for {project_name}.

Include:
1. Getting Started
2. Key Features
3. Step-by-Step Tutorials
4. Best Practices
5. Troubleshooting
6. FAQ

Context: {context}
Requirements: {requirements}""",
        dependencies=["PRD"],
        estimated_tokens=2500
    ),
    DocumentTemplate(
        doc_type="TestPlan",
        title="Test Plan",
        prompt_template="""Write a comprehensive Test Plan for {project_name}.

Include:
1. Testing Strategy
2. Unit Tests
3. Integration Tests
4. E2E Test Scenarios
5. Performance Testing
6. Security Testing
7. Test Coverage Goals

Context: {context}
Technical Spec: {technical_spec}""",
        dependencies=["TechnicalSpec"],
        estimated_tokens=2500
    ),
    DocumentTemplate(
        doc_type="Architecture",
        title="Architecture Diagram Documentation",
        prompt_template="""Write detailed Architecture Documentation for {project_name}.

Include:
1. System Architecture (describe diagram)
2. Component Interactions
3. Data Flow
4. Deployment Architecture
5. Scalability Considerations
6. Technology Choices and Rationale

Context: {context}
Technical Spec: {technical_spec}""",
        dependencies=["TechnicalSpec"],
        estimated_tokens=2000
    ),
]


class DocumentGenerator:
    """Generates documents using AI with streaming support."""
    
    def __init__(self, session: Session):
        self.session = session
        self.ai_gateway_url = settings.ai_gateway_url
        self.ai_gateway_api_key = settings.ai_gateway_api_key
    
    async def generate_content_stream(
        self,
        prompt: str,
        doc_type: str
    ) -> AsyncGenerator[str, None]:
        """
        Generate document content as a stream of chunks.
        
        In production, this would call your AI Gateway.
        For now, we'll simulate streaming with placeholder content.
        """
        # TODO: Replace with actual AI Gateway call
        # Example:
        # async with httpx.AsyncClient() as client:
        #     async with client.stream(
        #         "POST",
        #         f"{self.ai_gateway_url}/generate",
        #         json={"prompt": prompt, "stream": True},
        #         headers={"Authorization": f"Bearer {self.ai_gateway_api_key}"}
        #     ) as response:
        #         async for chunk in response.aiter_text():
        #             yield chunk
        
        # Placeholder: Generate structured content based on doc type
        content_map = {
            "PRD": self._generate_prd_content(),
            "TechnicalSpec": self._generate_technical_spec_content(),
            "APIDoc": self._generate_api_doc_content(),
            "UserGuide": self._generate_user_guide_content(),
            "TestPlan": self._generate_test_plan_content(),
            "Architecture": self._generate_architecture_content(),
        }
        
        content = content_map.get(doc_type, self._generate_default_content())
        
        # Simulate streaming by yielding content in chunks
        chunk_size = 50
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            yield chunk
            await asyncio.sleep(0.05)  # Simulate network delay
    
    def _generate_prd_content(self) -> str:
        return """# Product Requirements Document

## 1. Executive Summary
This document outlines the requirements for building an autonomous project management system with real-time visualization.

## 2. Problem Statement
Traditional project management tools lack real-time collaboration and intelligent automation. Teams need a system that can automatically generate documentation, sync with code repositories, and provide visual insights.

## 3. Goals and Objectives
- Enable real-time collaborative project planning
- Automate documentation generation
- Provide multi-layer visualization of project components
- Integrate seamlessly with GitHub and other tools

## 4. User Stories
- As a PM, I want to see all project docs visualized so I can understand relationships
- As a developer, I want docs to auto-update when code changes
- As a team lead, I want to drill down from portfolio to individual tasks

## 5. Feature Requirements
- Multi-layer graph visualization (Portfolio > Project > Documentation)
- Real-time document streaming and generation
- Version control for all documents
- GitHub Projects v2 bidirectional sync
- WebSocket-based live updates

## 6. Success Metrics
- Document generation time < 30 seconds
- Real-time updates < 100ms latency
- User satisfaction score > 4.5/5
- 90% reduction in manual documentation time

## 7. Timeline
- Phase 1: Core backend (2 weeks)
- Phase 2: Visualization system (3 weeks)
- Phase 3: AI integration (2 weeks)
- Phase 4: Polish and launch (1 week)
"""
    
    def _generate_technical_spec_content(self) -> str:
        return """# Technical Specification

## 1. Architecture Overview
The system uses a microservices architecture with:
- FastAPI backend for REST and WebSocket APIs
- PostgreSQL for persistent storage
- Redis for real-time pub/sub
- React + ReactFlow for frontend visualization

## 2. System Components

### Backend Services
- **API Service**: FastAPI application handling HTTP/WS
- **Document Generator**: Parallel agent swarm for doc creation
- **Sync Service**: GitHub Projects v2 integration
- **Streaming Service**: WebSocket/SSE infrastructure

### Frontend Components
- **Canvas Manager**: ReactFlow-based visualization
- **Node Components**: Custom nodes for docs, resources, repos
- **Editor**: Monaco-based in-node text editor
- **Layer Navigator**: Multi-level graph navigation

## 3. Data Models
- GraphNode: Base node type for all visualizations
- DocumentNode: Specialized for versioned documents
- ResourceNode: URLs, files, external references
- GraphEdge: Relationships between nodes

## 4. API Specifications
- REST endpoints for CRUD operations
- WebSocket endpoints for real-time updates
- SSE endpoints for document streaming
- GraphQL for complex queries (future)

## 5. Security
- JWT-based authentication
- Role-based access control (RBAC)
- API rate limiting
- Input validation and sanitization

## 6. Performance Requirements
- API response time: < 200ms (p95)
- WebSocket latency: < 100ms
- Document generation: < 30s per doc
- Concurrent users: 100+

## 7. Technology Stack
- Backend: Python 3.11, FastAPI, SQLModel
- Database: PostgreSQL 15, Redis 7
- Frontend: Next.js 14, React 18, ReactFlow
- Deployment: Docker, Kubernetes
"""
    
    def _generate_api_doc_content(self) -> str:
        return """# API Documentation

## Authentication
All API requests require a Bearer token in the Authorization header:
```
Authorization: Bearer <your_token>
```

## Endpoints

### Projects

#### GET /api/v1/projects
List all projects with pagination.

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Number of records to return (default: 100)

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Project Name",
    "description": "Description",
    "status": "active",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### POST /api/v1/projects
Create a new project.

**Request Body:**
```json
{
  "name": "New Project",
  "description": "Project description",
  "github_project_id": "optional_github_id"
}
```

### Documents

#### GET /api/v1/documents/stream/{document_id}
Stream document generation in real-time using Server-Sent Events.

**Response:** SSE stream with events:
- `start`: Generation started
- `content_chunk`: Content chunk with progress
- `complete`: Generation complete
- `error`: Error occurred

#### POST /api/v1/documents/generate
Trigger parallel document generation for a project.

**Request Body:**
```json
{
  "project_id": "uuid",
  "doc_types": ["PRD", "TechnicalSpec", "APIDoc"]
}
```

### WebSocket

#### WS /api/v1/ws/canvas/{project_id}
Real-time canvas updates for nodes and edges.

**Message Format:**
```json
{
  "event": "node_update",
  "data": {
    "node_id": "uuid",
    "update_type": "position",
    "node_data": {...}
  }
}
```

## Error Codes
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 429: Rate Limit Exceeded
- 500: Internal Server Error

## Rate Limiting
- 100 requests per minute per API key
- 10 concurrent WebSocket connections per user
"""
    
    def _generate_user_guide_content(self) -> str:
        return """# User Guide

## Getting Started

### 1. Create Your First Project
1. Click "New Project" in the top navigation
2. Enter project name and description
3. Optionally connect to a GitHub repository
4. Click "Create"

### 2. Generate Documentation
1. Open your project
2. Navigate to the "Documentation" layer
3. Click "Generate Docs"
4. Select document types (PRD, Technical Spec, etc.)
5. Watch as documents appear and stream in real-time!

### 3. Navigate Between Layers
- **Portfolio View**: See all your projects as nodes
- **Project View**: View project components (docs, resources, repo)
- **Documentation View**: Detailed doc canvas with relationships

Click on nodes to drill down between layers.

## Key Features

### Real-Time Document Generation
Documents appear as nodes on the canvas and fill with content as they're generated. Multiple documents can generate simultaneously.

### Version Control
Edit any document and save. A new version will stack on top of the original, showing the evolution of your documentation.

### Graph Visualization
All relationships are visualized:
- Docs that reference each other
- Resources linked to docs
- GitHub issues connected to tasks

### Expandable Nodes
Click any node to expand it and edit content inline using the built-in text editor.

## Best Practices
1. Start with a PRD before generating technical specs
2. Use tags to organize documents
3. Save snapshots before major changes
4. Review AI-generated content and refine as needed

## Troubleshooting

**Documents not generating?**
- Check your AI Gateway connection
- Verify API keys are set correctly
- Check browser console for errors

**WebSocket not connecting?**
- Ensure your browser supports WebSockets
- Check firewall settings
- Try refreshing the page

## FAQ

**Q: Can I export documents?**
A: Yes, use the export button to download as Markdown or PDF.

**Q: How many versions can I create?**
A: Unlimited! Versions stack vertically on the canvas.

**Q: Can I customize document templates?**
A: Yes, go to Settings > Document Templates to create custom types.
"""
    
    def _generate_test_plan_content(self) -> str:
        return """# Test Plan

## 1. Testing Strategy
Comprehensive testing across all layers using automated and manual testing.

## 2. Unit Tests
- Model validation tests
- Service layer tests
- Utility function tests
- Target: 80% code coverage

## 3. Integration Tests
- API endpoint tests
- Database transaction tests
- WebSocket connection tests
- GitHub API integration tests

## 4. E2E Test Scenarios

### Scenario 1: Project Creation and Doc Generation
1. User creates new project
2. System saves to database
3. User triggers doc generation
4. Multiple docs generate in parallel
5. Real-time updates via WebSocket
6. Docs save with correct relationships

### Scenario 2: Version Control Flow
1. User views existing document
2. User expands node and edits content
3. User saves changes
4. New version creates and stacks
5. User can switch between versions

### Scenario 3: Multi-Layer Navigation
1. User starts at portfolio view
2. User clicks project node
3. View transitions to project layer
4. User clicks docs subgraph
5. View transitions to documentation canvas

## 5. Performance Testing
- Load test: 100 concurrent users
- Stress test: Document generation under load
- WebSocket scaling: 1000+ connections
- Database query optimization

## 6. Security Testing
- Authentication bypass attempts
- SQL injection tests
- XSS vulnerability scans
- Rate limiting validation
- JWT token expiration

## 7. Test Coverage Goals
- Unit tests: 80%
- Integration tests: 70%
- E2E tests: Critical paths covered
- Security: OWASP Top 10 tested
"""
    
    def _generate_architecture_content(self) -> str:
        return """# Architecture Documentation

## 1. System Architecture

### High-Level Overview
```
[Frontend: Next.js + ReactFlow]
           ↓ HTTP/WS
[API Gateway: FastAPI]
     ↓           ↓
[Services]   [Streaming]
     ↓           ↓
[PostgreSQL] [Redis PubSub]
```

## 2. Component Interactions

### Document Generation Flow
1. User triggers generation via UI
2. API creates DocumentNode records
3. Generator service spawns parallel agents
4. Each agent streams content via WebSocket
5. Frontend renders nodes with live updates
6. Completion triggers relationship detection
7. Edges auto-create between related docs

### Sync Flow (GitHub ↔ Local)
1. User initiates sync
2. Sync service fetches GitHub data
3. Diff algorithm identifies changes
4. Updates apply to local database
5. WebSocket broadcasts changes
6. Canvas updates in real-time

## 3. Data Flow

### Write Path
User Action → API Validation → Service Logic → Database Write → WebSocket Broadcast → UI Update

### Read Path
UI Request → API → Database Query → Response Serialization → JSON Response

### Stream Path
Generation Start → Chunk Producer → WebSocket → Client Buffer → Render

## 4. Deployment Architecture

### Production Setup
- Load Balancer (nginx)
- API Pods (3+ replicas)
- PostgreSQL (primary + replica)
- Redis Cluster (3 nodes)
- Object Storage (documents, assets)

### Development Setup
- docker-compose with all services
- Hot reload enabled
- Local PostgreSQL and Redis

## 5. Scalability Considerations

### Horizontal Scaling
- Stateless API servers
- WebSocket with sticky sessions
- Distributed task queue (Celery)

### Vertical Scaling
- Database connection pooling
- Redis caching layer
- CDN for static assets

### Bottleneck Mitigation
- Background job processing for heavy tasks
- Database read replicas
- Rate limiting per user

## 6. Technology Choices

**FastAPI**: High performance, async support, excellent docs
**SQLModel**: Type-safe ORM, Pydantic integration
**ReactFlow**: Powerful graph visualization, extensible
**PostgreSQL**: JSONB support for flexible schemas
**Redis**: PubSub for real-time, caching layer
**Docker**: Consistent environments, easy deployment
"""
    
    def _generate_default_content(self) -> str:
        return """# Document

## Overview
This is a generated document for your project.

## Content
Document content will be generated based on your project context and requirements.

## Next Steps
1. Review generated content
2. Edit as needed
3. Save to create new version
"""


class SwarmCoordinator:
    """Coordinates parallel document generation with dependency management."""
    
    def __init__(self, session: Session):
        self.session = session
        self.generator = DocumentGenerator(session)
        self.active_generations: Dict[UUID, asyncio.Task] = {}
    
    async def generate_documents_parallel(
        self,
        project_id: UUID,
        doc_types: List[str],
        context: Dict[str, Any]
    ) -> List[UUID]:
        """
        Generate multiple documents in parallel, respecting dependencies.
        
        Returns list of document IDs that were created.
        """
        # Get templates for requested doc types
        templates = [t for t in STANDARD_DOC_TEMPLATES if t.doc_type in doc_types]
        
        # Build dependency graph
        dep_graph = self._build_dependency_graph(templates)
        
        # Generate in waves based on dependencies
        doc_ids = []
        completed_docs = {}
        
        for wave in dep_graph:
            tasks = []
            for template in wave:
                task = self._generate_single_document(
                    project_id=project_id,
                    template=template,
                    context=context,
                    completed_docs=completed_docs
                )
                tasks.append(task)
            
            # Wait for all documents in this wave to complete
            results = await asyncio.gather(*tasks)
            
            for doc_id, doc_content in results:
                doc_ids.append(doc_id)
                completed_docs[doc_id] = doc_content
        
        # Create relationships between documents
        await self._create_document_relationships(doc_ids)
        
        return doc_ids
    
    def _build_dependency_graph(
        self,
        templates: List[DocumentTemplate]
    ) -> List[List[DocumentTemplate]]:
        """Build waves of documents that can be generated in parallel."""
        waves = []
        remaining = templates.copy()
        generated_types = set()
        
        while remaining:
            # Find all templates whose dependencies are satisfied
            current_wave = []
            for template in remaining:
                if all(dep in generated_types for dep in template.dependencies):
                    current_wave.append(template)
            
            if not current_wave:
                # Circular dependency or missing dependency
                # Generate remaining docs anyway
                current_wave = remaining.copy()
            
            waves.append(current_wave)
            for template in current_wave:
                remaining.remove(template)
                generated_types.add(template.doc_type)
        
        return waves
    
    async def _generate_single_document(
        self,
        project_id: UUID,
        template: DocumentTemplate,
        context: Dict[str, Any],
        completed_docs: Dict[UUID, str]
    ) -> tuple[UUID, str]:
        """Generate a single document with streaming."""
        # Create graph node for the document
        graph_node = GraphNode(
            node_type=NodeType.DOCUMENT,
            layer=GraphLayer.DOCUMENTATION,
            label=template.title,
            project_id=project_id,
            data={"doc_type": template.doc_type}
        )
        self.session.add(graph_node)
        self.session.commit()
        self.session.refresh(graph_node)
        
        # Broadcast node creation
        await manager.broadcast_to_project(
            str(project_id),
            {
                "event": "node_created",
                "data": {
                    "node_id": str(graph_node.id),
                    "node_type": "document",
                    "label": template.title
                }
            }
        )
        
        # Create document node
        doc_node = DocumentNode(
            graph_node_id=graph_node.id,
            title=template.title,
            doc_type=template.doc_type,
            project_id=project_id,
            is_generating=True,
            generated_by_agent="swarm_coordinator"
        )
        self.session.add(doc_node)
        self.session.commit()
        self.session.refresh(doc_node)
        
        # Generate content with streaming
        full_content = ""
        async for chunk in self.generator.generate_content_stream(
            template.prompt_template.format(
                project_name=context.get("project_name", "Project"),
                context=context.get("description", ""),
                **context
            ),
            template.doc_type
        ):
            full_content += chunk
            
            # Broadcast content chunk
            await manager.broadcast_to_document(
                str(doc_node.id),
                {
                    "event": "content_chunk",
                    "data": {
                        "document_id": str(doc_node.id),
                        "chunk": chunk,
                        "progress": len(full_content) / template.estimated_tokens
                    }
                }
            )
        
        # Update document with final content
        doc_node.content = full_content
        doc_node.is_generating = False
        doc_node.generation_progress = 1.0
        self.session.add(doc_node)
        self.session.commit()
        
        # Broadcast completion
        await manager.broadcast_to_document(
            str(doc_node.id),
            {
                "event": "generation_complete",
                "data": {
                    "document_id": str(doc_node.id)
                }
            }
        )
        
        return doc_node.id, full_content
    
    async def _create_document_relationships(self, doc_ids: List[UUID]):
        """Create edges between related documents."""
        # Simple heuristic: connect documents that reference each other
        # In production, this would use NLP to detect references
        
        docs = self.session.exec(
            select(DocumentNode).where(DocumentNode.id.in_(doc_ids))
        ).all()
        
        for i, doc1 in enumerate(docs):
            for doc2 in docs[i+1:]:
                # Check if doc1 mentions doc2's type or vice versa
                if (doc2.doc_type.lower() in doc1.content.lower() or 
                    doc1.doc_type.lower() in doc2.content.lower()):
                    
                    edge = GraphEdge(
                        edge_type=EdgeType.REFERENCES,
                        source_id=doc1.graph_node_id,
                        target_id=doc2.graph_node_id
                    )
                    self.session.add(edge)
        
        self.session.commit()
