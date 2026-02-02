/**
 * Zustand store for managing multi-layer canvas state
 */
import { create } from 'zustand';
import { Node, Edge, XYPosition } from 'reactflow';
import { GraphNode, GraphEdge } from './api-client';

export type CanvasLayer = 'portfolio' | 'project' | 'documentation';

export interface CanvasNode extends Node {
  data: {
    label: string;
    description?: string;
    nodeType: string;
    isExpanded: boolean;
    content?: string;
    version?: number;
    isGenerating?: boolean;
    generationProgress?: number;
    metadata?: Record<string, any>;
  };
}

export interface CanvasEdge extends Edge {
  data?: {
    edgeType: string;
    isVersionLink?: boolean;
    metadata?: Record<string, any>;
  };
}

interface LayerState {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  selectedNodeId: string | null;
}

interface CanvasState {
  // Current layer and context
  currentLayer: CanvasLayer;
  currentProjectId: string | null;
  
  // Layer states
  portfolioLayer: LayerState;
  projectLayer: LayerState;
  documentationLayer: LayerState;
  
  // Navigation history for breadcrumbs
  navigationHistory: Array<{ layer: CanvasLayer; projectId?: string; label: string }>;
  
  // Actions
  setCurrentLayer: (layer: CanvasLayer, projectId?: string) => void;
  navigateToLayer: (layer: CanvasLayer, projectId?: string, label?: string) => void;
  navigateBack: () => void;
  
  // Node operations
  addNode: (layer: CanvasLayer, node: CanvasNode) => void;
  updateNode: (layer: CanvasLayer, nodeId: string, updates: Partial<CanvasNode>) => void;
  deleteNode: (layer: CanvasLayer, nodeId: string) => void;
  setNodes: (layer: CanvasLayer, nodes: CanvasNode[]) => void;
  
  // Edge operations
  addEdge: (layer: CanvasLayer, edge: CanvasEdge) => void;
  deleteEdge: (layer: CanvasLayer, edgeId: string) => void;
  setEdges: (layer: CanvasLayer, edges: CanvasEdge[]) => void;
  
  // Selection
  selectNode: (layer: CanvasLayer, nodeId: string | null) => void;
  
  // Real-time updates
  handleNodeCreated: (layer: CanvasLayer, graphNode: GraphNode) => void;
  handleNodeUpdated: (layer: CanvasLayer, nodeId: string, updates: Partial<GraphNode>) => void;
  handleEdgeCreated: (layer: CanvasLayer, graphEdge: GraphEdge) => void;
  handleContentChunk: (documentId: string, chunk: string, progress: number) => void;
  
  // Utility
  getCurrentLayerState: () => LayerState;
  clearLayer: (layer: CanvasLayer) => void;
}

const createEmptyLayerState = (): LayerState => ({
  nodes: [],
  edges: [],
  selectedNodeId: null,
});

export const useCanvasStore = create<CanvasState>((set, get) => ({
  // Initial state
  currentLayer: 'portfolio',
  currentProjectId: null,
  portfolioLayer: createEmptyLayerState(),
  projectLayer: createEmptyLayerState(),
  documentationLayer: createEmptyLayerState(),
  navigationHistory: [{ layer: 'portfolio', label: 'Portfolio' }],
  
  // Layer navigation
  setCurrentLayer: (layer, projectId) => {
    set({ currentLayer: layer, currentProjectId: projectId });
  },
  
  navigateToLayer: (layer, projectId, label) => {
    const { navigationHistory } = get();
    const newHistory = [
      ...navigationHistory,
      { layer, projectId, label: label || layer },
    ];
    set({
      currentLayer: layer,
      currentProjectId: projectId,
      navigationHistory: newHistory,
    });
  },
  
  navigateBack: () => {
    const { navigationHistory } = get();
    if (navigationHistory.length > 1) {
      const newHistory = navigationHistory.slice(0, -1);
      const previous = newHistory[newHistory.length - 1];
      set({
        currentLayer: previous.layer,
        currentProjectId: previous.projectId,
        navigationHistory: newHistory,
      });
    }
  },
  
  // Node operations
  addNode: (layer, node) => {
    set((state) => {
      const layerKey = `${layer}Layer` as keyof Pick<CanvasState, 'portfolioLayer' | 'projectLayer' | 'documentationLayer'>;
      const currentLayer = state[layerKey] as LayerState;
      return {
        [layerKey]: {
          ...currentLayer,
          nodes: [...currentLayer.nodes, node],
        },
      };
    });
  },
  
  updateNode: (layer, nodeId, updates) => {
    set((state) => {
      const layerKey = `${layer}Layer` as keyof Pick<CanvasState, 'portfolioLayer' | 'projectLayer' | 'documentationLayer'>;
      const currentLayer = state[layerKey] as LayerState;
      return {
        [layerKey]: {
          ...currentLayer,
          nodes: currentLayer.nodes.map((node) =>
            node.id === nodeId ? { ...node, ...updates } : node
          ),
        },
      };
    });
  },
  
  deleteNode: (layer, nodeId) => {
    set((state) => {
      const layerKey = `${layer}Layer` as keyof Pick<CanvasState, 'portfolioLayer' | 'projectLayer' | 'documentationLayer'>;
      const currentLayer = state[layerKey] as LayerState;
      return {
        [layerKey]: {
          ...currentLayer,
          nodes: currentLayer.nodes.filter((node) => node.id !== nodeId),
          edges: currentLayer.edges.filter(
            (edge) => edge.source !== nodeId && edge.target !== nodeId
          ),
        },
      };
    });
  },
  
  setNodes: (layer, nodes) => {
    set((state) => {
      const layerKey = `${layer}Layer` as keyof Pick<CanvasState, 'portfolioLayer' | 'projectLayer' | 'documentationLayer'>;
      const currentLayer = state[layerKey] as LayerState;
      return {
        [layerKey]: {
          ...currentLayer,
          nodes,
        },
      };
    });
  },
  
  // Edge operations
  addEdge: (layer, edge) => {
    set((state) => {
      const layerKey = `${layer}Layer` as keyof Pick<CanvasState, 'portfolioLayer' | 'projectLayer' | 'documentationLayer'>;
      const currentLayer = state[layerKey] as LayerState;
      return {
        [layerKey]: {
          ...currentLayer,
          edges: [...currentLayer.edges, edge],
        },
      };
    });
  },
  
  deleteEdge: (layer, edgeId) => {
    set((state) => {
      const layerKey = `${layer}Layer` as keyof Pick<CanvasState, 'portfolioLayer' | 'projectLayer' | 'documentationLayer'>;
      const currentLayer = state[layerKey] as LayerState;
      return {
        [layerKey]: {
          ...currentLayer,
          edges: currentLayer.edges.filter((edge) => edge.id !== edgeId),
        },
      };
    });
  },
  
  setEdges: (layer, edges) => {
    set((state) => {
      const layerKey = `${layer}Layer` as keyof Pick<CanvasState, 'portfolioLayer' | 'projectLayer' | 'documentationLayer'>;
      const currentLayer = state[layerKey] as LayerState;
      return {
        [layerKey]: {
          ...currentLayer,
          edges,
        },
      };
    });
  },
  
  // Selection
  selectNode: (layer, nodeId) => {
    set((state) => {
      const layerKey = `${layer}Layer` as keyof Pick<CanvasState, 'portfolioLayer' | 'projectLayer' | 'documentationLayer'>;
      const currentLayer = state[layerKey] as LayerState;
      return {
        [layerKey]: {
          ...currentLayer,
          selectedNodeId: nodeId,
        },
      };
    });
  },
  
  // Real-time WebSocket handlers
  handleNodeCreated: (layer, graphNode) => {
    const newNode: CanvasNode = {
      id: graphNode.id,
      type: graphNode.node_type === 'document' ? 'documentNode' : 'defaultNode',
      position: { x: graphNode.position.x, y: graphNode.position.y },
      data: {
        label: graphNode.label,
        description: graphNode.description,
        nodeType: graphNode.node_type,
        isExpanded: graphNode.is_expanded,
        metadata: graphNode.data,
      },
    };
    get().addNode(layer, newNode);
  },
  
  handleNodeUpdated: (layer, nodeId, updates) => {
    get().updateNode(layer, nodeId, {
      position: updates.position ? { x: updates.position.x, y: updates.position.y } : undefined,
      data: updates.data ? { ...updates.data } : undefined,
    } as Partial<CanvasNode>);
  },
  
  handleEdgeCreated: (layer, graphEdge) => {
    const newEdge: CanvasEdge = {
      id: graphEdge.id,
      source: graphEdge.source_id,
      target: graphEdge.target_id,
      label: graphEdge.label,
      animated: graphEdge.is_animated,
      style: graphEdge.color ? { stroke: graphEdge.color } : undefined,
      data: {
        edgeType: graphEdge.edge_type,
      },
    };
    get().addEdge(layer, newEdge);
  },
  
  handleContentChunk: (documentId, chunk, progress) => {
    // Find the document node in documentation layer
    const { documentationLayer } = get();
    const nodeIndex = documentationLayer.nodes.findIndex(
      (node) => node.data.metadata?.document_id === documentId
    );
    
    if (nodeIndex !== -1) {
      get().updateNode('documentation', documentationLayer.nodes[nodeIndex].id, {
        data: {
          ...documentationLayer.nodes[nodeIndex].data,
          content: (documentationLayer.nodes[nodeIndex].data.content || '') + chunk,
          generationProgress: progress,
          isGenerating: progress < 1,
        },
      } as Partial<CanvasNode>);
    }
  },
  
  // Utility
  getCurrentLayerState: () => {
    const { currentLayer, portfolioLayer, projectLayer, documentationLayer } = get();
    switch (currentLayer) {
      case 'portfolio':
        return portfolioLayer;
      case 'project':
        return projectLayer;
      case 'documentation':
        return documentationLayer;
      default:
        return portfolioLayer;
    }
  },
  
  clearLayer: (layer) => {
    set((state) => {
      const layerKey = `${layer}Layer` as keyof Pick<CanvasState, 'portfolioLayer' | 'projectLayer' | 'documentationLayer'>;
      return {
        [layerKey]: createEmptyLayerState(),
      };
    });
  },
}));
