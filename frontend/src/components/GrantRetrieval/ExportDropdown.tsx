import React, { useState, useEffect, useRef } from 'react';

interface ExportDropdownProps {
  onExport: (format: string) => void;
}

export const ExportDropdown: React.FC<ExportDropdownProps> = ({ onExport }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  return (
    <div ref={dropdownRef} className="export-dropdown" style={{ position: 'relative' }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          padding: '0.5rem',
          borderRadius: '6px',
          border: '1px solid #30363d',
          background: '#238636',
          color: 'white',
          cursor: 'pointer'
        }}
      >
        Export ▾
      </button>

      {isOpen && (
        <div style={{
          position: 'absolute',
          top: '100%',
          right: 0,
          zIndex: 1000,
          background: '#161b22',
          border: '1px solid #30363d',
          borderRadius: '6px',
          padding: '8px',
          width: '120px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
        }}>
          <button onClick={() => { onExport('csv'); setIsOpen(false); }} style={{ display: 'block', width: '100%', padding: '8px', textAlign: 'left', background: 'transparent', border: 'none', color: 'white', cursor: 'pointer', fontSize: '0.9rem' }}>CSV</button>
          <button onClick={() => { onExport('json'); setIsOpen(false); }} style={{ display: 'block', width: '100%', padding: '8px', textAlign: 'left', background: 'transparent', border: 'none', color: 'white', cursor: 'pointer', fontSize: '0.9rem' }}>JSON</button>
          <button onClick={() => { onExport('xlsx'); setIsOpen(false); }} style={{ display: 'block', width: '100%', padding: '8px', textAlign: 'left', background: 'transparent', border: 'none', color: 'white', cursor: 'pointer', fontSize: '0.9rem' }}>Excel</button>
        </div>
      )}
    </div>
  );
};
