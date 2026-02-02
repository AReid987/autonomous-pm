/**
 * Expandable Document Node with Monaco Editor
 * Click to expand and edit document content inline
 */
'use client';

import React, { memo, useState } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { FileText, Maximize2, Minimize2, Save, X } from 'lucide-react';
import Editor from '@monaco-editor/react';
import { CanvasNode } from '@/lib/canvas-store';
import { documentsApi } from '@/lib/api-client';

export type ExpandableDocumentNodeData = CanvasNode['data'] & {
  content?: string;
  documentId?: string;
  version?: number;
};

const ExpandableDocumentNode = memo(({ data, selected, id }: NodeProps<ExpandableDocumentNodeData>) => {
  const {
    label,
    content = '',
    documentId,
    version = 1,
    isExpanded: initialExpanded = false,
  } = data;

  const [isExpanded, setIsExpanded] = useState(initialExpanded);
  const [editedContent, setEditedContent] = useState(content);
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  const handleExpand = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsExpanded(!isExpanded);
  };

  const handleEditorChange = (value: string | undefined) => {
    setEditedContent(value || '');
    setHasChanges(value !== content);
  };

  const handleSave = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!documentId || !hasChanges) return;

    setIsSaving(true);
    try {
      // Create a new version when saving
      await documentsApi.createVersion(documentId, editedContent);
      setHasChanges(false);
      alert('New version created successfully!');
    } catch (error) {
      console.error('Failed to save:', error);
      alert('Failed to save document');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditedContent(content);
    setHasChanges(false);
  };

  // Collapsed view
  if (!isExpanded) {
    return (
      <div
        className={`
          relative w-80 bg-white rounded-lg shadow-lg border-2 transition-all
          ${selected ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-300'}
        `}
      >
        <Handle type="target" position={Position.Top} className="w-3 h-3" />
        <Handle type="source" position={Position.Bottom} className="w-3 h-3" />

        <div className="flex items-center gap-2 p-3 border-b border-gray-200 bg-blue-50">
          <FileText className="w-5 h-5 text-blue-600" />
          <div className="flex-1">
            <div className="font-semibold text-sm text-gray-900">{label}</div>
            {version > 1 && (
              <div className="text-xs text-gray-500">v{version}</div>
            )}
          </div>
          <button
            onClick={handleExpand}
            className="p-1 hover:bg-blue-100 rounded transition-colors"
            title="Expand to edit"
          >
            <Maximize2 className="w-4 h-4 text-blue-600" />
          </button>
        </div>

        <div className="p-3">
          <div className="text-xs text-gray-700 leading-relaxed line-clamp-3">
            {content.substring(0, 150)}
            {content.length > 150 && '...'}
          </div>
        </div>
      </div>
    );
  }

  // Expanded view with editor
  return (
    <div
      className={`
        relative w-[800px] h-[600px] bg-white rounded-lg shadow-2xl border-2
        ${selected ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-300'}
      `}
      style={{ zIndex: 1000 }} // Ensure expanded node is on top
    >
      <Handle type="target" position={Position.Top} className="w-3 h-3" />
      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />

      {/* Header */}
      <div className="flex items-center gap-2 p-3 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50">
        <FileText className="w-5 h-5 text-blue-600" />
        <div className="flex-1">
          <div className="font-semibold text-sm text-gray-900">{label}</div>
          <div className="text-xs text-gray-500">
            v{version} • {hasChanges ? 'Unsaved changes' : 'Saved'}
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-1">
          {hasChanges && (
            <>
              <button
                onClick={handleCancel}
                className="p-1.5 hover:bg-gray-100 rounded transition-colors"
                title="Cancel changes"
              >
                <X className="w-4 h-4 text-gray-600" />
              </button>
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="flex items-center gap-1 px-2 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded transition-colors disabled:bg-gray-400 text-xs font-medium"
                title="Save as new version"
              >
                <Save className="w-3 h-3" />
                {isSaving ? 'Saving...' : 'Save'}
              </button>
            </>
          )}
          <button
            onClick={handleExpand}
            className="p-1.5 hover:bg-blue-100 rounded transition-colors ml-1"
            title="Collapse"
          >
            <Minimize2 className="w-4 h-4 text-blue-600" />
          </button>
        </div>
      </div>

      {/* Monaco Editor */}
      <div className="h-[calc(100%-60px)]">
        <Editor
          height="100%"
          defaultLanguage="markdown"
          value={editedContent}
          onChange={handleEditorChange}
          theme="vs-light"
          options={{
            minimap: { enabled: true },
            fontSize: 13,
            lineNumbers: 'on',
            wordWrap: 'on',
            scrollBeyondLastLine: false,
            automaticLayout: true,
          }}
        />
      </div>

      {/* Info footer */}
      <div className="absolute bottom-0 left-0 right-0 px-3 py-1 bg-gray-50 text-[10px] text-gray-500 border-t border-gray-200">
        Tip: Saving creates a new version that stacks on top
      </div>
    </div>
  );
});

ExpandableDocumentNode.displayName = 'ExpandableDocumentNode';

export default ExpandableDocumentNode;
