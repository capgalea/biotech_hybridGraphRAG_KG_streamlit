import React, { useState } from 'react';
import { Network, X } from 'lucide-react';
import { WorkflowViewer } from './WorkflowViewer';

interface WorkflowButtonProps {
  chart: string;
  title?: string;
}

export const WorkflowButton: React.FC<WorkflowButtonProps> = ({ chart, title = "AI Agent Workflow" }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-40 flex items-center gap-2 px-4 py-3 bg-indigo-600 text-white rounded-full shadow-lg hover:bg-indigo-700 transition-all hover:scale-105 group"
        title="View AI Agent Workflow"
      >
        <Network size={20} className="group-hover:rotate-12 transition-transform" />
        <span className="font-medium text-sm hidden group-hover:block animate-in fade-in slide-in-from-right-2">View Agent Workflow</span>
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl overflow-hidden animate-in zoom-in-95 slide-in-from-bottom-5">
            <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50/50">
              <div className="flex items-center gap-2">
                 <Network className="text-indigo-600" size={20} />
                 <h3 className="font-bold text-gray-900">{title}</h3>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 rounded-full hover:bg-gray-200 text-gray-500 hover:text-gray-900 transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="p-0 bg-white">
               <WorkflowViewer chart={chart} />
            </div>
            
            <div className="p-4 border-t border-gray-100 bg-gray-50 text-xs text-gray-500 flex justify-between">
                <span>Diagram generated with Mermaid.js</span>
                <span>Biotech Hybrid GraphRAG Agent</span>
            </div>
          </div>
          
          {/* Close on background click */}
          <div className="absolute inset-0 -z-10" onClick={() => setIsOpen(false)} />
        </div>
      )}
    </>
  );
};
