/**
 * Main application page with multi-layer navigation
 */
'use client';

import React, { useState } from 'react';
import { useCanvasStore } from '@/lib/canvas-store';
import PortfolioCanvas from '@/components/PortfolioCanvas';
import ProjectCanvas from '@/components/ProjectCanvas';
import DocumentationCanvas from '@/components/DocumentationCanvas';
import { ChevronRight, Home } from 'lucide-react';

export default function HomePage() {
  const {
    currentLayer,
    currentProjectId,
    navigationHistory,
    navigateBack,
    setCurrentLayer,
  } = useCanvasStore();

  const handleNavigateToPortfolio = () => {
    setCurrentLayer('portfolio', undefined);
    // Clear history to just portfolio
    while (navigationHistory.length > 1) {
      navigateBack();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Global Navigation Bar */}
      <nav className="bg-white border-b border-gray-200 shadow-sm">
        <div className="px-6 py-3">
          <div className="flex items-center justify-between">
            {/* Logo/Brand */}
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">AP</span>
              </div>
              <h1 className="text-xl font-bold text-gray-900">
                Autonomous PM
              </h1>
            </div>

            {/* Breadcrumb Navigation */}
            <div className="flex items-center gap-2 bg-gray-50 px-3 py-2 rounded-lg">
              <button
                onClick={handleNavigateToPortfolio}
                className="flex items-center gap-1 text-sm text-gray-600 hover:text-blue-600 transition-colors"
              >
                <Home className="w-4 h-4" />
              </button>
              
              {navigationHistory.slice(1).map((item, index) => (
                <React.Fragment key={index}>
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                  <button
                    onClick={() => {
                      // Navigate back to this level
                      const targetIndex = index + 1;
                      const stepsBack = navigationHistory.length - targetIndex - 1;
                      for (let i = 0; i < stepsBack; i++) {
                        navigateBack();
                      }
                    }}
                    className={`
                      text-sm transition-colors
                      ${index === navigationHistory.length - 2
                        ? 'text-blue-600 font-semibold'
                        : 'text-gray-600 hover:text-blue-600'}
                    `}
                  >
                    {item.label}
                  </button>
                </React.Fragment>
              ))}
            </div>

            {/* Layer Indicator */}
            <div className="flex items-center gap-2">
              <div className="text-xs text-gray-500">Layer:</div>
              <div className={`
                px-3 py-1 rounded-full text-xs font-medium
                ${currentLayer === 'portfolio' ? 'bg-purple-100 text-purple-700' : ''}
                ${currentLayer === 'project' ? 'bg-blue-100 text-blue-700' : ''}
                ${currentLayer === 'documentation' ? 'bg-green-100 text-green-700' : ''}
              `}>
                {currentLayer === 'portfolio' && 'Level 3: Portfolio'}
                {currentLayer === 'project' && 'Level 2: Project'}
                {currentLayer === 'documentation' && 'Level 1: Documentation'}
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Canvas Area - switches based on current layer */}
      <div className="flex-1 relative">
        {currentLayer === 'portfolio' && (
          <PortfolioCanvas
            onNavigate={(layer, projectId) => {
              // Navigation handled by store
            }}
          />
        )}

        {currentLayer === 'project' && currentProjectId && (
          <ProjectCanvas
            projectId={currentProjectId}
            onNavigate={(layer) => {
              if (layer === 'portfolio') {
                navigateBack();
              }
            }}
          />
        )}

        {currentLayer === 'documentation' && currentProjectId && (
          <DocumentationCanvas projectId={currentProjectId} />
        )}
      </div>

      {/* Keyboard shortcuts hint */}
      <div className="absolute bottom-4 right-4 bg-white/90 backdrop-blur rounded-lg shadow-lg p-3 text-xs text-gray-600 max-w-xs">
        <div className="font-semibold text-gray-800 mb-2">Navigation Tips</div>
        <div className="space-y-1">
          <div>• Click nodes to drill down to deeper layers</div>
          <div>• Use breadcrumbs to navigate back up</div>
          <div>• Drag nodes to rearrange your layout</div>
          <div>• Click "Expand" on docs to edit inline</div>
        </div>
      </div>
    </div>
  );
}
