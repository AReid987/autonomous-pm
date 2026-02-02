/**
 * Project Node - represents a project in portfolio view
 */
'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { FolderKanban, Clock, CheckCircle2, AlertCircle } from 'lucide-react';
import { CanvasNode } from '@/lib/canvas-store';

export type ProjectNodeData = CanvasNode['data'] & {
  status?: 'active' | 'completed' | 'on-hold' | 'archived';
  lastUpdated?: string;
  documentCount?: number;
  taskCount?: number;
};

const STATUS_CONFIG = {
  active: {
    color: 'text-green-600',
    bgColor: 'bg-green-100',
    icon: CheckCircle2,
  },
  completed: {
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
    icon: CheckCircle2,
  },
  'on-hold': {
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-100',
    icon: Clock,
  },
  archived: {
    color: 'text-gray-600',
    bgColor: 'bg-gray-100',
    icon: AlertCircle,
  },
};

const ProjectNode = memo(({ data, selected }: NodeProps<ProjectNodeData>) => {
  const {
    label,
    description,
    status = 'active',
    lastUpdated,
    documentCount = 0,
    taskCount = 0,
  } = data;

  const statusConfig = STATUS_CONFIG[status];
  const StatusIcon = statusConfig.icon;

  // Format last updated date
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <div
      className={`
        relative w-80 bg-white rounded-lg shadow-lg border-2 transition-all cursor-pointer
        hover:shadow-2xl hover:scale-105
        ${selected ? 'border-blue-500 ring-4 ring-blue-200' : 'border-gray-300'}
      `}
    >
      {/* Handles */}
      <Handle type="target" position={Position.Top} className="w-3 h-3" />
      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />

      {/* Header */}
      <div className="flex items-center gap-3 p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50">
        <div className="p-2 bg-white rounded-lg shadow-sm">
          <FolderKanban className="w-6 h-6 text-blue-600" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-base text-gray-900 truncate">
            {label}
          </h3>
          <div className={`flex items-center gap-1 text-xs ${statusConfig.color} mt-0.5`}>
            <StatusIcon className="w-3 h-3" />
            <span className="capitalize">{status}</span>
          </div>
        </div>
      </div>

      {/* Description */}
      {description && (
        <div className="px-4 py-3 text-sm text-gray-600 line-clamp-2 border-b border-gray-100">
          {description}
        </div>
      )}

      {/* Stats */}
      <div className="px-4 py-3 grid grid-cols-2 gap-3">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-blue-500" />
          <div className="text-xs">
            <div className="font-semibold text-gray-900">{documentCount}</div>
            <div className="text-gray-500">Docs</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500" />
          <div className="text-xs">
            <div className="font-semibold text-gray-900">{taskCount}</div>
            <div className="text-gray-500">Tasks</div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="px-4 py-2 bg-gray-50 rounded-b-lg flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          <span>{formatDate(lastUpdated)}</span>
        </div>
        <div className="text-gray-400 italic">
          click to open
        </div>
      </div>
    </div>
  );
});

ProjectNode.displayName = 'ProjectNode';

export default ProjectNode;
