import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import { ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

interface WorkflowViewerProps {
  chart: string;
}

mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
  fontFamily: 'Inter, sans-serif',
});

export const WorkflowViewer: React.FC<WorkflowViewerProps> = ({ chart }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);

  useEffect(() => {
    const renderChart = async () => {
      if (containerRef.current) {
        try {
          // Reset explicitly before rendering to avoid artifacts
          containerRef.current.innerHTML = ''; 
          // Generate unique ID
          const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;
          // Render returns an object { svg }
          const { svg } = await mermaid.render(id, chart);
          containerRef.current.innerHTML = svg;
        } catch (error) {
          console.error("Mermaid rendering failed:", error);
          // Fallback if rendering fails (e.g. bad syntax)
          containerRef.current.innerHTML = '<div class="text-red-500 p-4">Failed to render workflow diagram.</div>'; 
        }
      }
    };
    
    renderChart();
  }, [chart]);

  return (
    <div className="relative w-full h-[60vh] bg-gray-50/50 rounded-xl overflow-hidden border border-gray-100 flex flex-col group">
       {/* Zoom Controls */}
       <div className="absolute bottom-4 right-4 flex items-center gap-1 bg-white shadow-lg border border-gray-100 p-1 rounded-lg z-20 opacity-0 group-hover:opacity-100 transition-all duration-200 translate-y-2 group-hover:translate-y-0">
          <button 
            onClick={() => setScale(s => Math.max(0.5, s - 0.2))} 
            className="p-2 hover:bg-gray-100 rounded-md text-gray-500 hover:text-indigo-600 transition-colors" 
            title="Zoom Out"
          >
            <ZoomOut size={16} />
          </button>
          <span className="text-xs font-mono font-medium text-gray-400 w-12 text-center select-none">{Math.round(scale * 100)}%</span>
          <button 
            onClick={() => setScale(s => Math.min(3, s + 0.2))} 
            className="p-2 hover:bg-gray-100 rounded-md text-gray-500 hover:text-indigo-600 transition-colors" 
            title="Zoom In"
          >
            <ZoomIn size={16} />
          </button>
          <div className="w-px h-4 bg-gray-200 mx-1"></div>
          <button 
            onClick={() => setScale(1)} 
            className="p-2 hover:bg-gray-100 rounded-md text-gray-500 hover:text-gray-900 transition-colors" 
            title="Reset Zoom"
          >
            <RotateCcw size={16} />
          </button>
       </div>

       {/* Scrollable Canvas */}
       <div className="flex-1 overflow-auto p-8 cursor-grab active:cursor-grabbing">
          <div className="min-w-full min-h-full flex items-center justify-center">
            <div 
                ref={containerRef} 
                className="mermaid transition-transform duration-200 ease-out origin-center"
                style={{ transform: `scale(${scale})` }}
            >
                {/* Content injected by mermaid */}
            </div>
          </div>
       </div>
    </div>
  );
};
