/**
 * API client for backend communication
 */
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface Project {
  id: string;
  name: string;
  description?: string;
  status: string;
  created_at: string;
}

export interface DocumentNode {
  id: string;
  title: string;
  doc_type: string;
  content: string;
  version: number;
  is_latest: boolean;
  is_generating: boolean;
  generation_progress: number;
  created_at: string;
}

export interface GraphNode {
  id: string;
  node_type: string;
  layer: string;
  label: string;
  description?: string;
  position: { x: number; y: number; z: number };
  width: number;
  height: number;
  color?: string;
  is_expanded: boolean;
  data: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  edge_type: string;
  source_id: string;
  target_id: string;
  label?: string;
  color?: string;
  is_animated: boolean;
}

// API functions
export const projectsApi = {
  list: () => apiClient.get<Project[]>('/projects'),
  get: (id: string) => apiClient.get<Project>(`/projects/${id}`),
  create: (data: Partial<Project>) => apiClient.post<Project>('/projects', data),
  update: (id: string, data: Partial<Project>) => apiClient.put<Project>(`/projects/${id}`, data),
  delete: (id: string) => apiClient.delete(`/projects/${id}`),
};

export const documentsApi = {
  generate: (projectId: string, docTypes: string[], context?: Record<string, any>) =>
    apiClient.post('/documents/generate', { project_id: projectId, doc_types: docTypes, context }),
  
  list: (projectId: string) =>
    apiClient.get<DocumentNode[]>(`/documents/project/${projectId}`),
  
  get: (id: string) =>
    apiClient.get<DocumentNode>(`/documents/${id}`),
  
  update: (id: string, content: string, createVersion: boolean = true) =>
    apiClient.put(`/documents/${id}`, null, { params: { content, create_version: createVersion } }),
  
  getVersions: (id: string) =>
    apiClient.get(`/documents/${id}/versions`),
  
  createVersion: (id: string, content: string, metadata?: Record<string, any>) =>
    apiClient.post(`/documents/${id}/versions`, { content, metadata }),
  
  revertToVersion: (id: string, version: number) =>
    apiClient.post(`/documents/${id}/revert/${version}`),
  
  compareVersions: (id: string, versionA: number, versionB: number) =>
    apiClient.get(`/documents/${id}/compare/${versionA}/${versionB}`),
  
  templates: () =>
    apiClient.get('/documents/templates'),
};

export const graphApi = {
  getView: (layer: string, projectId?: string) => {
    const params = projectId ? { project_id: projectId } : {};
    return apiClient.get(`/graph/${layer}`, { params });
  },
  
  updateNodePosition: (nodeId: string, x: number, y: number, z: number) =>
    apiClient.put(`/graph/nodes/${nodeId}/position`, { x, y, z }),
  
  createNode: (data: Partial<GraphNode>) =>
    apiClient.post('/graph/nodes', data),
  
  updateNode: (nodeId: string, data: Partial<GraphNode>) =>
    apiClient.put(`/graph/nodes/${nodeId}`, data),
  
  deleteNode: (nodeId: string) =>
    apiClient.delete(`/graph/nodes/${nodeId}`),
  
  createEdge: (sourceId: string, targetId: string, edgeType: string, data?: Record<string, any>) =>
    apiClient.post('/graph/edges', { source_id: sourceId, target_id: targetId, edge_type: edgeType, data }),
  
  deleteEdge: (edgeId: string) =>
    apiClient.delete(`/graph/edges/${edgeId}`),
};

// WebSocket connection helper
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  
  constructor(
    private url: string,
    private onMessage: (data: any) => void,
    private onConnect?: () => void,
    private onDisconnect?: () => void
  ) {}
  
  connect() {
    const wsUrl = this.url.replace('http://', 'ws://').replace('https://', 'wss://');
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected:', this.url);
      this.reconnectAttempts = 0;
      this.onConnect?.();
    };
    
    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.onMessage(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.onDisconnect?.();
      this.attemptReconnect();
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }
  
  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * this.reconnectAttempts;
      console.log(`Attempting reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
      setTimeout(() => this.connect(), delay);
    }
  }
  
  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
  
  disconnect() {
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnection
    this.ws?.close();
  }
}

export function createProjectWebSocket(
  projectId: string,
  onMessage: (data: any) => void,
  onConnect?: () => void,
  onDisconnect?: () => void
): WebSocketClient {
  const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/api/v1/ws/project/${projectId}`;
  return new WebSocketClient(wsUrl, onMessage, onConnect, onDisconnect);
}

export function createDocumentWebSocket(
  documentId: string,
  onMessage: (data: any) => void,
  onConnect?: () => void,
  onDisconnect?: () => void
): WebSocketClient {
  const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/api/v1/ws/document/${documentId}`;
  return new WebSocketClient(wsUrl, onMessage, onConnect, onDisconnect);
}
