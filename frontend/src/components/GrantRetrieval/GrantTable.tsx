import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FilterDropdown } from './FilterDropdown';
import { ColumnVisibility } from './ColumnVisibility';
import { ExportDropdown } from './ExportDropdown';

interface GrantTableProps {
  apiBase: string;
  refreshKey?: number;
  source?: string;
  title?: string;
}

interface Column {
  key: string;
  label: string;
  visible?: boolean;
  isDropdown?: boolean;
}

export const GrantTable: React.FC<GrantTableProps> = ({ apiBase, refreshKey, source = 'combined', title }) => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(50);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState<Record<string, any>>({});
  const [sortBy, setSortBy] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [draggedColumnKey, setDraggedColumnKey] = useState<string | null>(null);
  
  // Row selection state
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set());
  const [showSelectedOnly, setShowSelectedOnly] = useState(false);
  
  // Reuse columns def from original App.jsx
  const [tableColumns, setTableColumns] = useState<Column[]>([
    { key: 'CIA_Name', label: 'CIA Name', visible: true }, 
    { key: 'Grant_Title', label: 'Grant Title', visible: true }, 
    { key: 'Grant_Type', label: 'Grant Type', isDropdown: true, visible: true },
    { key: 'Total_Amount', label: 'Total Amount', visible: true }, 
    { key: 'Broad_Research_Area', label: 'Broad Research Area', isDropdown: true, visible: true },
    { key: 'Field_of_Research', label: 'Field of Research', isDropdown: true, visible: true },
    { key: 'Plain_Description', label: 'Plain Description', visible: true },
    { key: 'Admin_Institution', label: 'Admin Institution', isDropdown: true, visible: true },
    { key: 'Grant_Start_Year', label: 'Grant Start Year', isDropdown: true, visible: true },
    { key: 'Grant_End_Date', label: 'Grant End Date', visible: true },
    { key: 'CIA_ORCID_ID', label: 'CIA ORCID ID', visible: true },
    { key: 'Funding_Body', label: 'Funding Body', isDropdown: true, visible: true },
    { key: 'Source_File', label: 'Source File', isDropdown: true, visible: true },
    { key: 'Grant_Status', label: 'Grant Status', isDropdown: true, visible: true },
    { key: 'Investigators', label: 'Investigators', visible: true },
  ]);

  const visibleColumns = tableColumns.filter(c => c.visible !== false);

  // Handle filter changes
  const handleFilterChange = (key: string, selected: string[]) => {
    setFilters(prev => {
        const newFilters = { ...prev, [key]: selected };
        if (selected.length === 0) {
            delete newFilters[key];
        }
        return newFilters;
    });
  };

  useEffect(() => {
    fetchData(1, limit, search);
  }, [limit, sortBy, sortOrder, refreshKey, source, filters]);

  // Debounce search/filter
  useEffect(() => {
    const handler = setTimeout(() => {
      fetchData(1, limit, search);
    }, 500);
    return () => clearTimeout(handler);
  }, [search]); // Intentionally verify if search depends on filters too? No, separate effect.

  const fetchData = async (pageNum: number, currentLimit: number, currentSearch: string, append = false) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', String(pageNum));
      params.append('limit', String(currentLimit));
      params.append('source', source);
      if (currentSearch) params.append('search', currentSearch);
      
      // Append filters
      Object.entries(filters).forEach(([key, value]) => {
         if (Array.isArray(value)) {
             value.forEach(v => params.append(key, v));
         } else {
             params.append(key, String(value));
         }
      });
      
      const res = await axios.get(`${apiBase}/data`, { params });
      const newRecords = res.data.data;
      const totalRecords = res.data.pagination.total;

      if (append) {
        setData(prev => [...prev, ...newRecords]);
      } else {
        setData(newRecords);
      }
      setTotal(totalRecords);
      setPage(pageNum);

    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadMore = () => {
    const nextPage = page + 1;
    fetchData(nextPage, limit, search, true);
  };
  
  const handleDragStart = (e: React.DragEvent, key: string) => {
    setDraggedColumnKey(key);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent, targetKey: string) => {
    e.preventDefault();
    if (!draggedColumnKey || draggedColumnKey === targetKey) return;
    const sourceIndex = tableColumns.findIndex(c => c.key === draggedColumnKey);
    const targetIndex = tableColumns.findIndex(c => c.key === targetKey);
    if (sourceIndex !== -1 && targetIndex !== -1) {
      const newColumns = [...tableColumns];
      const [removed] = newColumns.splice(sourceIndex, 1);
      newColumns.splice(targetIndex, 0, removed);
      setTableColumns(newColumns);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDraggedColumnKey(null);
  };
  
  // Row selection handlers
  const handleRowSelect = (idx: number) => {
    setSelectedRows(prev => {
      const newSet = new Set(prev);
      if (newSet.has(idx)) {
        newSet.delete(idx);
      } else {
        newSet.add(idx);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    if (selectedRows.size === displayedData.length) {
      setSelectedRows(new Set());
    } else {
      setSelectedRows(new Set(displayedData.map((_, idx) => idx)));
    }
  };

  // Filter data based on selection mode
  const displayedData = showSelectedOnly 
    ? data.filter((_, idx) => selectedRows.has(idx))
    : data;

  const handleExport = (format: string) => {
    // Export only selected rows if in selection mode
    if (showSelectedOnly && selectedRows.size > 0) {
      const selectedData = data.filter((_, idx) => selectedRows.has(idx));
      // Create a blob and download
      const exportData = format === 'json' 
        ? JSON.stringify(selectedData, null, 2)
        : convertToCSV(selectedData);
      
      const blob = new Blob([exportData], { 
        type: format === 'json' ? 'application/json' : 'text/csv' 
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `selected_grants_${source}.${format === 'json' ? 'json' : 'csv'}`;
      a.click();
      URL.revokeObjectURL(url);
    } else {
      // Export all with filters
      window.open(`${apiBase}/export?format=${format}&search=${search}&source=${source}`, '_blank');
    }
  };

  const convertToCSV = (dataArray: any[]) => {
    if (dataArray.length === 0) return '';
    const headers = Object.keys(dataArray[0]);
    const csvRows = [
      headers.join(','),
      ...dataArray.map(row => 
        headers.map(header => {
          const value = row[header] || '';
          return `"${String(value).replace(/"/g, '""')}"`;
        }).join(',')
      )
    ];
    return csvRows.join('\n');
  };

  return (
    <div className="mb-8 border border-gray-200 rounded-xl p-4 bg-white shadow-sm">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-blue-600 m-0">{title || "Retrieved Grants"} ({total})</h3>
        <div className="flex gap-4 items-center">
          {selectedRows.size > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600 font-medium">
                {selectedRows.size} selected
              </span>
              <button
                onClick={() => setShowSelectedOnly(!showSelectedOnly)}
                className={`px-3 py-1.5 text-sm rounded-md font-medium transition-colors ${
                  showSelectedOnly 
                    ? 'bg-blue-600 text-white hover:bg-blue-700' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {showSelectedOnly ? 'Show All' : 'Show Selected Only'}
              </button>
              <button
                onClick={() => {
                  setSelectedRows(new Set());
                  setShowSelectedOnly(false);
                }}
                className="px-3 py-1.5 text-sm rounded-md font-medium bg-red-100 text-red-700 hover:bg-red-200"
              >
                Deselect All
              </button>
            </div>
          )}
          <ExportDropdown onExport={handleExport} />
          <input
            type="text"
            placeholder="Search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="p-2 rounded-md border border-gray-300 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
           <ColumnVisibility columns={tableColumns} onChange={(key) => {
               setTableColumns(prev => prev.map(c => c.key === key ? { ...c, visible: !c.visible } : c));
           }} onToggleAll={(visible) => {
               setTableColumns(prev => prev.map(c => ({ ...c, visible })));
           }} />
        </div>
      </div>

      <div className="max-h-[600px] overflow-auto">
        <table className="min-w-full divide-y divide-gray-200 border-collapse">
          <thead className="bg-gray-50 text-gray-500 sticky top-0 z-10">
            <tr>
              <th className="px-4 py-3 text-left border-b border-gray-200 bg-gray-50">
                <input
                  type="checkbox"
                  checked={displayedData.length > 0 && selectedRows.size === displayedData.length}
                  onChange={handleSelectAll}
                  className="cursor-pointer"
                  title="Select all"
                />
              </th>
              {visibleColumns.map(col => (
                <th
                  key={col.key}
                  draggable
                  onDragStart={(e) => handleDragStart(e, col.key)}
                  onDragOver={(e) => handleDragOver(e, col.key)}
                  onDrop={handleDrop}
                  className={`px-4 py-3 text-left text-xs font-medium uppercase tracking-wider cursor-grab select-none border-b border-gray-200 ${
                    draggedColumnKey === col.key ? 'opacity-50 bg-gray-100' : 'bg-gray-50'
                  }`}
                >
                  {col.label}
                  {/* Basic filter dropdown integration - specific implementation can be expanded */}
                  {col.isDropdown && (
                     <div className="mt-1">
                        <FilterDropdown 
                            columnKey={col.key} 
                            label={col.label} 
                            selected={filters[col.key] || []} 
                            onChange={(selected) => handleFilterChange(col.key, selected)}
                            apiBase={apiBase}
                        />
                     </div>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200 text-gray-500 text-sm">
            {displayedData.map((row, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={selectedRows.has(idx)}
                    onChange={() => handleRowSelect(idx)}
                    className="cursor-pointer"
                  />
                </td>
                {visibleColumns.map(col => (
                  <td key={`${idx}-${col.key}`} title={row[col.key]} className="px-4 py-3 whitespace-nowrap max-w-[300px] overflow-hidden text-ellipsis">
                    {row[col.key]}
                  </td>
                ))}
              </tr>
            ))}
             {displayedData.length === 0 && !loading && (
              <tr><td colSpan={visibleColumns.length + 1} className="text-center p-8">No data found</td></tr>
            )}
          </tbody>
        </table>
        
        {loading && <div className="p-4 text-center">Loading...</div>}
        
        {!loading && !showSelectedOnly && data.length < total && (
            <div className="text-center p-4">
            <button onClick={loadMore} className="text-sm px-4 py-2 cursor-pointer bg-gray-100 hover:bg-gray-200 rounded text-gray-700">
                Load More
            </button>
            </div>
        )}
      </div>
    </div>
  );
};
