import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

interface FilterDropdownProps {
  columnKey: string;
  label: string;
  selected: string[];
  onChange: (selected: string[]) => void;
  apiBase: string;
}

export const FilterDropdown: React.FC<FilterDropdownProps> = ({ columnKey, label, selected = [], onChange, apiBase }) => {
  const [options, setOptions] = useState<string[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch options only when opened for the first time
  const toggleOpen = async () => {
    if (!isOpen && options.length === 0) {
      setLoading(true);
      try {
        // We use the existing endpoint structure or one we create
        // The original app used /unique_values?column=...
        // We need to ensure backend supports this or we add it to retrieval router?
        // Wait, retrieval router has /data but not /unique_values yet.
        // Let's assume we might need to add it or use a static list for now if endpoint missing.
        // Actually, let's try to hit the endpoint, if it fails we show empty.
        // Note: The original `main.py` had `get_unique_values`. We didn't port that to `retrieval.py`.
        // We should probably add it or mocked it. For now let's try.
        const res = await axios.get(`${apiBase}/unique_values`, { params: { column: columnKey } });
        setOptions(res.data.values);
      } catch (err) {
        console.warn("Failed to load options, maybe endpoint missing", err);
        setOptions([]); 
      } finally {
        setLoading(false);
      }
    }
    setIsOpen(!isOpen);
  };

  const handleCheckboxChange = (val: string) => {
    const newSelected = selected.includes(val)
      ? selected.filter(item => item !== val)
      : [...selected, val];
    onChange(newSelected);
  };

  // Close when clicking outside
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
    <div ref={dropdownRef} className={`filter-dropdown-${columnKey}`} style={{ position: 'relative', width: '90%' }}>
      <div
        onClick={toggleOpen}
        style={{
          padding: '6px 8px',
          borderRadius: '4px',
          border: '1px solid #d1d5db',
          background: '#ffffff',
          color: '#374151',
          fontSize: '0.875rem',
          cursor: 'pointer',
          minHeight: '28px',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          fontWeight: '500'
        }}>
        {selected.length > 0 ? `${selected.length} selected` : `Filter ${label}...`}
      </div>

      {isOpen && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          zIndex: 1000,
          background: '#ffffff',
          border: '1px solid #d1d5db',
          borderRadius: '6px',
          padding: '8px',
          maxHeight: '250px',
          overflowY: 'auto',
          width: '220px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          marginTop: '4px'
        }}>
          {!loading && selected.length > 0 && (
            <div 
              onClick={(e) => {
                e.stopPropagation();
                onChange([]);
              }}
              style={{
                padding: '6px',
                marginBottom: '6px',
                borderBottom: '1px solid #e5e7eb',
                color: '#2563eb',
                cursor: 'pointer',
                fontSize: '0.875rem',
                textAlign: 'center',
                fontWeight: '600'
              }}
            >
              Clear All
            </div>
          )}
          {loading ? <div style={{ color: '#6b7280', padding: '4px' }}>Loading...</div> : (
            options.length === 0 ? <div style={{padding: '6px', fontStyle: 'italic', color: '#9ca3af'}}>No options available</div> : (
              options.map(opt => (
                <label key={opt} style={{ 
                  display: 'block', 
                  padding: '6px 4px', 
                  cursor: 'pointer', 
                  fontSize: '0.875rem',
                  color: '#374151',
                  borderRadius: '4px',
                  transition: 'background-color 0.15s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  <input
                    type="checkbox"
                    checked={selected.includes(opt)}
                    onChange={() => handleCheckboxChange(opt)}
                    style={{ marginRight: '8px', cursor: 'pointer' }}
                  />
                  {opt}
                </label>
              ))
            )
          )}
        </div>
      )}
    </div>
  );
};
