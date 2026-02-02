/**
 * Document Node - displays document with streaming content
 */
'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { FileText, Loader2, Check } from 'lucide-react';
import { CanvasNode } from '@/lib/canvas-store';

export type DocumentNodeData = CanvasNode['data'] & {
  content?: string;
  isGenerating?: boolean;
  generationProgress?: number;
  version?: number;
};

const DocumentNode = memo(({ data, selected }: NodeProps<DocumentNodeData>) => {
  const {
    label,
    content = '',
    isGenerating = false,
    generationProgress = 0,
    version = 1,
  } = data;

  // Truncate content for preview
  const previewContent = content.substring(0, 200);
  const hasMore = content.length > 200;

  return (
    <div
      className={`
        relative w-80 bg-white rounded-lg shadow-lg border-2 transition-all
        ${selected ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-300'}
        ${isGenerating ? 'animate-pulse' : ''}
        ${version > 1 ? 'version-stack' : ''}
      `}
    >
      {/* Handles for connections */}
      <Handle type="target" position={Position.Top} className="w-3 h-3" />
      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />

      {/* Header */}
      <div className="flex items-center gap-2 p-3 border-b border-gray-200 bg-blue-50">
        <FileText className="w-5 h-5 text-blue-600" />
        <div className="flex-1">
          <div className="font-semibold text-sm text-gray-900">{label}</div>
          {version > 1 && (
            <div className="text-xs text-gray-500">v{version}</div>
          )}
        </div>
        {isGenerating && (
          <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
        )}
        {!isGenerating && content && (
          <Check className="w-4 h-4 text-green-600" />
        )}
      </div>

      {/* Content Preview */}
      <div className="p-3">
        {isGenerating && !content && (
          <div className="text-sm text-gray-400 italic">
            Generating content...
          </div>
        )}
        {content && (
          <div className="text-xs text-gray-700 leading-relaxed streaming-content">
            {previewContent}
            {hasMore && <span className="text-gray-400">...</span>}
          </div>
        )}
        {!isGenerating && !content && (
          <div className="text-sm text-gray-400 italic">
            Empty document
          </div>
        )}
      </div>

      {/* Generation Progress Bar */}
      {isGenerating && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200 rounded-b-lg overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${generationProgress * 100}%` }}
          />
        </div>
      )}

      {/* Version indicator */}
      {version > 1 && (
        <div className="absolute -top-2 -right-2 bg-purple-500 text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center">
          {version}
        </div>
      )}
    </div>
  );
});

DocumentNode.displayName = 'DocumentNode';

export default DocumentNode;
