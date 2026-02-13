import React, { useState, useEffect, useRef } from 'react';

interface Column {
  key: string;
  label: string;
  visible?: boolean;
}

interface ColumnVisibilityProps {
  columns: Column[];
  onChange: (key: string) => void;
  onToggleAll: (visible: boolean) => void;
}

export const ColumnVisibility: React.FC<ColumnVisibilityProps> = ({ columns, onChange, onToggleAll }) => {
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
    <div ref={dropdownRef} className="column-visibility-dropdown" style={{ position: 'relative' }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          padding: '0.5rem',
          borderRadius: '6px',
          border: '1px solid #30363d',
          background: '#0d1117',
          color: 'white',
          cursor: 'pointer'
        }}
      >
        Columns ▾
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
          maxHeight: '300px',
          overflowY: 'auto',
          width: '200px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
        }}>
          <div style={{ paddingBottom: '8px', marginBottom: '8px', borderBottom: '1px solid #30363d', display: 'flex', gap: '8px', justifyContent: 'center' }}>
            <button onClick={() => onToggleAll(true)} style={{ fontSize: '0.7rem', padding: '4px 8px', cursor: 'pointer', background: '#238636', color: 'white', border: 'none', borderRadius: '4px' }}>Select All</button>
            <button onClick={() => onToggleAll(false)} style={{ fontSize: '0.7rem', padding: '4px 8px', cursor: 'pointer', background: '#da3633', color: 'white', border: 'none', borderRadius: '4px' }}>Deselect All</button>
          </div>
          {columns.map(col => (
            <label key={col.key} style={{ display: 'block', padding: '4px 0', cursor: 'pointer', fontSize: '0.8rem' }}>
              <input
                type="checkbox"
                checked={col.visible !== false}
                onChange={() => onChange(col.key)}
                style={{ marginRight: '8px' }}
              />
              {col.label}
            </label>
          ))}
        </div>
      )}
    </div>
  );
};
