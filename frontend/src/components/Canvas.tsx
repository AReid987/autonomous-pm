/**
 * Base Canvas component with ReactFlow
 */
'use client';

import React, { useCallback, useEffect } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  NodeTypes,
  EdgeTypes,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { useCanvasStore, CanvasLayer } from '@/lib/canvas-store';
import { createProjectWebSocket, WebSocketClient } from '@/lib/api-client';

interface CanvasProps {
  layer: CanvasLayer;
  projectId?: string;
  nodeTypes?: NodeTypes;
  edgeTypes?: EdgeTypes;
}

function CanvasInner({ layer, projectId, nodeTypes, edgeTypes }: CanvasProps) {
  const {
    getCurrentLayerState,
    setNodes: setStoreNodes,
    setEdges: setStoreEdges,
    handleNodeCreated,
    handleNodeUpdated,
    handleEdgeCreated,
    handleContentChunk,
  } = useCanvasStore();

  const layerState = getCurrentLayerState();
  const [nodes, setNodes, onNodesChange] = useNodesState(layerState.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(layerState.edges);

  // Sync local ReactFlow state with Zustand store
  useEffect(() => {
    setNodes(layerState.nodes);
    setEdges(layerState.edges);
  }, [layerState.nodes, layerState.edges, setNodes, setEdges]);

  // Update store when local state changes
  useEffect(() => {
    setStoreNodes(layer, nodes);
  }, [nodes, layer, setStoreNodes]);

  useEffect(() => {
    setStoreEdges(layer, edges);
  }, [edges, layer, setStoreEdges]);

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!projectId) return;

    let wsClient: WebSocketClient | null = null;

    const handleMessage = (data: any) => {
      const { event, data: eventData } = data;

      switch (event) {
        case 'node_created':
          handleNodeCreated(layer, eventData);
          break;
        case 'node_update':
          handleNodeUpdated(layer, eventData.node_id, eventData.node_data);
          break;
        case 'edge_created':
          handleEdgeCreated(layer, eventData);
          break;
        case 'content_chunk':
          handleContentChunk(eventData.document_id, eventData.chunk, eventData.progress);
          break;
        case 'generation_complete':
          // Mark generation as complete
          handleContentChunk(eventData.document_id, '', 1.0);
          break;
      }
    };

    wsClient = createProjectWebSocket(
      projectId,
      handleMessage,
      () => console.log('WebSocket connected'),
      () => console.log('WebSocket disconnected')
    );

    wsClient.connect();

    return () => {
      wsClient?.disconnect();
    };
  }, [projectId, layer, handleNodeCreated, handleNodeUpdated, handleEdgeCreated, handleContentChunk]);

  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) => addEdge(connection, eds));
    },
    [setEdges]
  );

  return (
    <div className="w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        attributionPosition="bottom-left"
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}

export default function Canvas(props: CanvasProps) {
  return (
    <ReactFlowProvider>
      <CanvasInner {...props} />
    </ReactFlowProvider>
  );
}
