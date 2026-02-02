/**
 * Project Canvas - Layer 2
 * Shows project components: docs, resources, GitHub repo, tasks
 */
'use client';

import React, { useEffect } from 'react';
import { NodeTypes, EdgeTypes } from 'reactflow';
import Canvas from '@/components/Canvas';
import ComponentNode from '@/components/nodes/ComponentNode';
import { useCanvasStore } from '@/lib/canvas-store';
import { projectsApi, documentsApi } from '@/lib/api-client';
import { ArrowLeft } from 'lucide-react';

interface ProjectCanvasProps {
  projectId: string;
  onNavigate?: (layer: string) => void;
}

const nodeTypes: NodeTypes = {
  componentNode: ComponentNode,
};

const edgeTypes: EdgeTypes = {};

export default function ProjectCanvas({ projectId, onNavigate }: ProjectCanvasProps) {
  const { setNodes, setEdges, navigateToLayer } = useCanvasStore();

  useEffect(() => {
    loadProjectComponents();
  }, [projectId]);

  const loadProjectComponents = async () => {
    try {
      // Load project details
      const projectRes = await projectsApi.get(projectId);
      const project = projectRes.data;

      // Load document count
      const docsRes = await documentsApi.list(projectId);
      const docCount = docsRes.data.length;

      // Create component nodes
      const nodes = [
        // Documentation subgraph
        {
          id: 'docs-component',
          type: 'componentNode',
          position: { x: 200, y: 100 },
          data: {
            label: 'Documentation',
            description: 'Project documentation with real-time generation',
            nodeType: 'component',
            componentType: 'docs',
            isExpanded: false,
            count: docCount,
            status: 'active',
          },
        },
        // Resources
        {
          id: 'resources-component',
          type: 'componentNode',
          position: { x: 500, y: 100 },
          data: {
            label: 'Resources',
            description: 'Saved URLs, files, and references',
            nodeType: 'component',
            componentType: 'resources',
            isExpanded: false,
            count: 0, // TODO: Load from API
          },
        },
        // GitHub Repository
        {
          id: 'github-component',
          type: 'componentNode',
          position: { x: 200, y: 300 },
          data: {
            label: 'GitHub Repository',
            description: project.github_project_id || 'Not connected',
            nodeType: 'component',
            componentType: 'github',
            isExpanded: false,
            status: project.github_project_id ? 'syncing' : undefined,
          },
        },
        // Tasks & Epics
        {
          id: 'tasks-component',
          type: 'componentNode',
          position: { x: 500, y: 300 },
          data: {
            label: 'Tasks & Epics',
            description: 'Project management and tracking',
            nodeType: 'component',
            componentType: 'tasks',
            isExpanded: false,
            count: 0, // TODO: Load from API
          },
        },
      ];

      // Create edges between related components
      const edges = [
        {
          id: 'docs-to-github',
          source: 'docs-component',
          target: 'github-component',
          label: 'syncs with',
          animated: true,
        },
        {
          id: 'tasks-to-docs',
          source: 'tasks-component',
          target: 'docs-component',
          label: 'documented in',
        },
        {
          id: 'resources-to-docs',
          source: 'resources-component',
          target: 'docs-component',
          label: 'referenced in',
        },
      ];

      setNodes('project', nodes);
      setEdges('project', edges);
    } catch (error) {
      console.error('Failed to load project components:', error);
    }
  };

  const handleNodeClick = (event: React.MouseEvent, node: any) => {
    // Navigate to the appropriate layer based on component type
    if (node.data.componentType === 'docs') {
      navigateToLayer('documentation', projectId, 'Documentation');
      onNavigate?.('documentation');
    }
    // Add handlers for other component types as needed
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Toolbar */}
      <div className="bg-white border-b border-gray-200 p-4 shadow-sm">
        <div className="flex items-center gap-4">
          <button
            onClick={() => {
              onNavigate?.('portfolio');
            }}
            className="p-2 hover:bg-gray-100 rounded-md transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h2 className="text-lg font-semibold text-gray-900">
            Project Components
          </h2>
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1 bg-gray-50">
        <Canvas
          layer="project"
          projectId={projectId}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
        />
      </div>

      {/* Component Legend */}
      <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-3 text-xs space-y-2 max-w-xs">
        <div className="font-semibold text-gray-700">Components</div>
        <div className="space-y-1 text-gray-600">
          <div>• Click any component to drill down</div>
          <div>• Edges show relationships between components</div>
          <div>• Real-time updates via WebSocket</div>
        </div>
      </div>
    </div>
  );
}
