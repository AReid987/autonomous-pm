/**
 * Component Node - represents project components (docs, resources, repo, tasks)
 */
'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { FileText, Link2, Github, ListTodo, Folder } from 'lucide-react';
import { CanvasNode } from '@/lib/canvas-store';

export type ComponentNodeData = CanvasNode['data'] & {
  componentType: 'docs' | 'resources' | 'github' | 'tasks' | 'folder';
  count?: number;
  status?: string;
};

const COMPONENT_CONFIG = {
  docs: {
    icon: FileText,
    color: 'blue',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-400',
    iconColor: 'text-blue-600',
  },
  resources: {
    icon: Link2,
    color: 'purple',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-400',
    iconColor: 'text-purple-600',
  },
  github: {
    icon: Github,
    color: 'gray',
    bgColor: 'bg-gray-50',
    borderColor: 'border-gray-400',
    iconColor: 'text-gray-700',
  },
  tasks: {
    icon: ListTodo,
    color: 'green',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-400',
    iconColor: 'text-green-600',
  },
  folder: {
    icon: Folder,
    color: 'yellow',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-400',
    iconColor: 'text-yellow-600',
  },
};

const ComponentNode = memo(({ data, selected }: NodeProps<ComponentNodeData>) => {
  const {
    label,
    description,
    componentType = 'folder',
    count,
    status,
  } = data;

  const config = COMPONENT_CONFIG[componentType];
  const Icon = config.icon;

  return (
    <div
      className={`
        relative w-64 bg-white rounded-lg shadow-lg border-2 transition-all cursor-pointer
        hover:shadow-xl hover:scale-105
        ${selected ? `${config.borderColor} ring-2 ring-${config.color}-200` : 'border-gray-300'}
        ${config.bgColor}
      `}
    >
      {/* Handles */}
      <Handle type="target" position={Position.Top} className="w-3 h-3" />
      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />

      {/* Content */}
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className={`p-2 rounded-lg ${config.bgColor}`}>
            <Icon className={`w-6 h-6 ${config.iconColor}`} />
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="font-semibold text-sm text-gray-900 truncate">
              {label}
            </div>
            {description && (
              <div className="text-xs text-gray-600 mt-1 line-clamp-2">
                {description}
              </div>
            )}
          </div>
        </div>

        {/* Metadata */}
        <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
          {count !== undefined && (
            <div className="flex items-center gap-1">
              <span className="font-medium">{count}</span>
              <span>items</span>
            </div>
          )}
          {status && (
            <div className={`
              px-2 py-0.5 rounded-full text-xs font-medium
              ${status === 'active' ? 'bg-green-100 text-green-700' : ''}
              ${status === 'syncing' ? 'bg-blue-100 text-blue-700' : ''}
              ${status === 'error' ? 'bg-red-100 text-red-700' : ''}
            `}>
              {status}
            </div>
          )}
        </div>
      </div>

      {/* Click indicator */}
      <div className="absolute bottom-1 right-1 text-[10px] text-gray-400 italic">
        click to open
      </div>
    </div>
  );
});

ComponentNode.displayName = 'ComponentNode';

export default ComponentNode;
