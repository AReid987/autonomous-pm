/**
 * Portfolio Canvas - Layer 3
 * Shows all projects with relationships
 */
'use client';

import React, { useEffect, useState } from 'react';
import { NodeTypes, EdgeTypes } from 'reactflow';
import Canvas from '@/components/Canvas';
import ProjectNode from '@/components/nodes/ProjectNode';
import { useCanvasStore } from '@/lib/canvas-store';
import { projectsApi } from '@/lib/api-client';
import { Plus, RefreshCw } from 'lucide-react';

interface PortfolioCanvasProps {
  onNavigate?: (layer: string, projectId?: string) => void;
}

const nodeTypes: NodeTypes = {
  projectNode: ProjectNode,
};

const edgeTypes: EdgeTypes = {};

export default function PortfolioCanvas({ onNavigate }: PortfolioCanvasProps) {
  const [isLoading, setIsLoading] = useState(false);
  const { setNodes, setEdges, navigateToLayer } = useCanvasStore();

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    setIsLoading(true);
    try {
      const response = await projectsApi.list();
      const projects = response.data;

      // Convert projects to nodes with grid layout
      const nodes = projects.map((project, index) => {
        const col = index % 3;
        const row = Math.floor(index / 3);
        
        return {
          id: project.id,
          type: 'projectNode',
          position: {
            x: col * 400 + 100,
            y: row * 400 + 100,
          },
          data: {
            label: project.name,
            description: project.description,
            nodeType: 'project',
            isExpanded: false,
            status: project.status,
            lastUpdated: project.updated_at || project.created_at,
            documentCount: 0, // TODO: Load from API
            taskCount: 0, // TODO: Load from API
          },
        };
      });

      setNodes('portfolio', nodes);

      // TODO: Load project relationships and create edges
      // For now, empty edges
      setEdges('portfolio', []);
    } catch (error) {
      console.error('Failed to load projects:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateProject = async () => {
    const name = prompt('Enter project name:');
    if (!name) return;

    const description = prompt('Enter project description (optional):');

    try {
      await projectsApi.create({ name, description: description || undefined });
      loadProjects(); // Reload to show new project
    } catch (error) {
      console.error('Failed to create project:', error);
      alert('Failed to create project');
    }
  };

  const handleNodeClick = (event: React.MouseEvent, node: any) => {
    // Navigate to project view
    navigateToLayer('project', node.id, node.data.label);
    onNavigate?.('project', node.id);
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Toolbar */}
      <div className="bg-white border-b border-gray-200 p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold text-gray-900">
              Portfolio
            </h1>
            <div className="text-sm text-gray-500">
              All Projects
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={loadProjects}
              disabled={isLoading}
              className="flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>

            <button
              onClick={handleCreateProject}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
            >
              <Plus className="w-4 h-4" />
              New Project
            </button>
          </div>
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1 bg-gradient-to-br from-gray-50 to-blue-50">
        <Canvas
          layer="portfolio"
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
        />
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-3 text-xs space-y-2 max-w-xs">
        <div className="font-semibold text-gray-700">Portfolio View</div>
        <div className="space-y-1 text-gray-600">
          <div>• Click any project to view components</div>
          <div>• Edges show dependencies between projects</div>
          <div>• Drag nodes to organize your layout</div>
        </div>
        <div className="pt-2 border-t border-gray-200 space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500" />
            <span>Active</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-blue-500" />
            <span>Completed</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-yellow-500" />
            <span>On Hold</span>
          </div>
        </div>
      </div>
    </div>
  );
}
