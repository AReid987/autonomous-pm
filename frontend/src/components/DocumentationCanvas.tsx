/**
 * Documentation Canvas - Layer 1
 * Shows documents with real-time streaming generation
 */
'use client';

import React, { useEffect, useState } from 'react';
import { NodeTypes, EdgeTypes } from 'reactflow';
import Canvas from '@/components/Canvas';
import DocumentNode from '@/components/nodes/DocumentNode';
import { useCanvasStore } from '@/lib/canvas-store';
import { documentsApi, graphApi } from '@/lib/api-client';
import { Play, Loader2 } from 'lucide-react';

interface DocumentationCanvasProps {
  projectId: string;
}

const nodeTypes: NodeTypes = {
  documentNode: DocumentNode,
};

const edgeTypes: EdgeTypes = {
  // Can add custom edge types here
};

export default function DocumentationCanvas({ projectId }: DocumentationCanvasProps) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedTemplates, setSelectedTemplates] = useState<string[]>([]);
  const [templates, setTemplates] = useState<any[]>([]);
  const { setNodes, setEdges } = useCanvasStore();

  // Load available document templates
  useEffect(() => {
    documentsApi.templates()
      .then(res => setTemplates(res.data))
      .catch(err => console.error('Failed to load templates:', err));
  }, []);

  // Load existing documents for this project
  useEffect(() => {
    loadDocuments();
  }, [projectId]);

  const loadDocuments = async () => {
    try {
      // Load documents from backend
      const docsRes = await documentsApi.list(projectId);
      const docs = docsRes.data;

      // Convert to canvas nodes
      const nodes = docs.map((doc, index) => ({
        id: doc.id,
        type: 'documentNode',
        position: {
          x: (index % 3) * 400 + 100,
          y: Math.floor(index / 3) * 300 + 100,
        },
        data: {
          label: doc.title,
          nodeType: 'document',
          isExpanded: false,
          content: doc.content || '',
          version: doc.version,
          isGenerating: doc.is_generating,
          generationProgress: doc.generation_progress,
          metadata: {
            document_id: doc.id,
            doc_type: doc.doc_type,
          },
        },
      }));

      setNodes('documentation', nodes);

      // TODO: Load edges/relationships
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  const handleGenerate = async () => {
    if (selectedTemplates.length === 0) {
      alert('Please select at least one document type');
      return;
    }

    setIsGenerating(true);

    try {
      // Trigger parallel document generation
      await documentsApi.generate(projectId, selectedTemplates);
      
      // Documents will appear via WebSocket updates
      console.log('Document generation started');
    } catch (error) {
      console.error('Failed to generate documents:', error);
      alert('Failed to start document generation');
    } finally {
      setIsGenerating(false);
    }
  };

  const toggleTemplate = (docType: string) => {
    setSelectedTemplates(prev =>
      prev.includes(docType)
        ? prev.filter(t => t !== docType)
        : [...prev, docType]
    );
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Toolbar */}
      <div className="bg-white border-b border-gray-200 p-4 shadow-sm">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Documentation Canvas
          </h2>

          {/* Document Type Selection */}
          <div className="flex-1 flex items-center gap-2 flex-wrap">
            {templates.map(template => (
              <button
                key={template.doc_type}
                onClick={() => toggleTemplate(template.doc_type)}
                className={`
                  px-3 py-1 text-sm rounded-md transition-colors
                  ${selectedTemplates.includes(template.doc_type)
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}
                `}
              >
                {template.title}
              </button>
            ))}
          </div>

          {/* Generate Button */}
          <button
            onClick={handleGenerate}
            disabled={isGenerating || selectedTemplates.length === 0}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Generate Docs
              </>
            )}
          </button>
        </div>

        {selectedTemplates.length > 0 && (
          <div className="mt-2 text-sm text-gray-600">
            Selected: {selectedTemplates.join(', ')}
          </div>
        )}
      </div>

      {/* Canvas */}
      <div className="flex-1 bg-gray-50">
        <Canvas
          layer="documentation"
          projectId={projectId}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
        />
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-3 text-xs space-y-2">
        <div className="font-semibold text-gray-700">Legend</div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-blue-500" />
          <span>Generating</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span>Complete</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-purple-500 rounded text-white text-[8px] flex items-center justify-center">
            2+
          </div>
          <span>Versioned</span>
        </div>
      </div>
    </div>
  );
}
