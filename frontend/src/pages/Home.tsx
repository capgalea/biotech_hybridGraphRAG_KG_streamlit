import React, { useState } from "react";
import { Send, Loader2, RotateCcw } from "lucide-react";
import { queryService } from "../services/api";
import ReactMarkdown from "react-markdown";
import rehypeRaw from "rehype-raw";
import { useGlobalState } from "../context/GlobalStateContext";
import { WorkflowButton } from "../components/WorkflowButton";

export const Home = () => {
    const { homeState, setHomeState } = useGlobalState();
    const { query, result, llmModel, enableSearch } = homeState;
    const [loading, setLoading] = useState(false);

    const updateState = (updates: Partial<typeof homeState>) => {
        setHomeState(prev => ({ ...prev, ...updates }));
    };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const response = await queryService.processQuery(
        query,
        llmModel,
        enableSearch
      );
      updateState({ result: response.data });
    } catch (error: any) {
      console.error("Search failed", error);
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        "Failed to process query";
      updateState({ result: { error: errorMessage } });
    } finally {
      setLoading(false);
    }
  };
  
  const handleReset = () => {
      setHomeState({
          query: "",
          result: null,
          llmModel: "claude-4-5-sonnet",
          enableSearch: false
      });
  };

  /* AI Workflow Definition */
  const grantWorkflowChart = `
graph TD
    User([User]) -->|Natural Language Query| Agent{AI Agent}
    
    subgraph "Phase 1: Retrieval & Expansion"
    Agent -->|Enhance & Parse| LLM1[LLM: Query Master]
    LLM1 -->|Cypher Query| KG[(Neo4j Graph)]
    KG -->|Graph Data| Results[Raw Grant Data]
    end
    
    subgraph "Phase 2: Deep Research"
    Results -->|Analyze Grants| LLM2[LLM: Insight Engine]
    LLM2 -.->|Identify Top Grants| DeepAgent[Deep Research Agent]
    DeepAgent -->|Search Query| Tools[Google Search / OpenAlex]
    Tools -->|Papers & Citations| Validator{Validation}
    Validator -->|Verified Matches| EnrichedData[Enriched Context]
    DeepAgent --x|Unrelated| Discard[Discard]
    end
    
    subgraph "Phase 3: Synthesis"
    EnrichedData -->|Combine| Summarizer[LLM: Final Synthesis]
    Summarizer -->|Markdown Report| UI[Dashboard Output]
    end
    
    style Agent fill:#4f46e5,stroke:#312e81,color:#fff
    style KG fill:#0ea5e9,stroke:#0369a1,color:#fff
    style DeepAgent fill:#db2777,stroke:#9d174d,color:#fff
    style LLM1 fill:#8b5cf6,color:#fff
    style LLM2 fill:#8b5cf6,color:#fff
    style Summarizer fill:#8b5cf6,color:#fff
`;

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <WorkflowButton chart={grantWorkflowChart} title="Grant Explorer AI Workflow" />
      <div className="text-center space-y-4 pt-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Research Grant Explorer
        </h1>
        <p className="text-gray-500">
          Ask questions about grants, researchers, and institutions
        </p>
      </div>

      {/* Search Box */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => updateState({ query: e.target.value })}
              placeholder="e.g., Find grants related to CRISPR in 2024..."
              className="w-full pl-4 pr-12 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
            />
            {/* Action Buttons */}
            <div className="absolute right-2 top-2 flex gap-1">
                {result && (
                     <button
                        type="button"
                        onClick={handleReset}
                        className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                        title="Clear Results"
                     >
                        <RotateCcw size={20} />
                     </button>
                )}
                <button
                type="submit"
                disabled={loading}
                className="p-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                {loading ? (
                    <Loader2 className="animate-spin" size={20} />
                ) : (
                    <Send size={20} />
                )}
                </button>
            </div>
          </div>

          <div className="flex flex-wrap gap-4 items-center text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <label>Model:</label>
              <select
                value={llmModel}
                onChange={(e) => updateState({ llmModel: e.target.value })}
                className="border rounded px-2 py-1 bg-gray-50"
              >
                <option value="claude-4-5-sonnet">Claude 4.5 Sonnet</option>
                <option value="claude-3-5-sonnet">Claude 3.5 Sonnet</option>
                <option value="gemini-2-0-flash">Gemini 2.0 Flash</option>
                <option value="deepseek-r1">DeepSeek R1</option>
                <option value="deepseek-v3">DeepSeek V3</option>
              </select>
            </div>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={enableSearch}
                onChange={(e) => updateState({ enableSearch: e.target.checked })}
                className="rounded text-blue-600 focus:ring-blue-500"
              />
              <span>Enable Web Search <span className="text-gray-400 text-xs italic ml-1">(Required for Researcher Overview)</span></span>
            </label>
          </div>
        </form>
      </div>

      {/* Results */}
      {result && (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 animate-in fade-in slide-in-from-bottom-4">
          {result.error ? (
            <div className="text-red-500">{result.error}</div>
          ) : (
            <div className="space-y-6">
              {/* Summary Section */}
              {result.summary && (
                <div className="prose max-w-none">
                  <ReactMarkdown
                    rehypePlugins={[rehypeRaw]}
                    components={{
                      a: ({ node, ...props }) => {
                        const isScholar = props.href?.includes('scholar.google.com');
                        return (
                          <a
                            {...props}
                            className={isScholar ? 'text-blue-800 hover:text-blue-900 hover:underline font-bold' : 'text-blue-600 hover:underline'}
                            target="_blank"
                            rel="noopener noreferrer"
                          />
                        );
                      },
                      blockquote: ({ node, ...props }) => (
                        <blockquote 
                          {...props} 
                          className="!p-0 !m-0 !border-0 !not-italic text-lg text-gray-800 font-medium leading-relaxed"
                        />
                      ),
                      h2: ({ node, ...props }) => (
                         <h2 {...props} className="text-xl font-bold mt-6 mb-3 text-gray-900" />
                      )
                    }}
                  >
                    {result.summary}
                  </ReactMarkdown>
                </div>
              )}

              {/* Data Table Section */}
              {result.data && result.data.length > 0 ? (
                <div className="overflow-x-auto">
                  <h3 className="text-lg font-semibold mb-3">Data Results</h3>
                  <DataTable data={result.data} />
                </div>
              ) : (
                <div className="text-gray-500 italic">
                  No data results found in database.
                </div>
              )}

              {/* Debug Info (Collapsible) */}
              <details className="mt-4">
                <summary className="cursor-pointer text-sm text-gray-400 hover:text-gray-600">
                  Debug Information
                </summary>
                <pre className="mt-2 bg-gray-50 p-4 rounded-lg overflow-x-auto text-xs text-gray-600">
                  {JSON.stringify(
                    {
                      query: result.query,
                      cypher: result.cypher,
                      count: result.count,
                    },
                    null,
                    2
                  )}
                </pre>
              </details>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const DataTable = ({ data }: { data: any[] }) => {
  const [sortConfig, setSortConfig] = useState<{
    key: string;
    direction: "asc" | "desc" | null;
  }>({ key: "", direction: null });
  
  // Initialize column order based on data keys
  const [columns, setColumns] = useState<string[]>([]);
  // Track visible columns
  const [visibleColumns, setVisibleColumns] = useState<Set<string>>(new Set());
  
  // Hover state for popup
  const [hoveredCell, setHoveredCell] = useState<{ content: string; x: number; y: number } | null>(null);

  // Row selection state (stores _internal_id)
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set());

  // Show selected only toggle
  const [showSelectedOnly, setShowSelectedOnly] = useState(false);

  // Augment data with internal ID for stable selection
  const processedData = React.useMemo(() => {
    return data.map((item, index) => ({ ...item, _internal_id: index }));
  }, [data]);

  React.useEffect(() => {
    if (data && data.length > 0) {
      // Get all unique keys from data
      const allKeys = Array.from(new Set(data.flatMap(Object.keys)));
      // Prioritize specific columns order if preferred
      const preferred = ["grant_title", "title", "description", "amount", "start_year", "researcher_name", "institution_name"];
      const sortedKeys = allKeys.sort((a, b) => {
        const idxA = preferred.indexOf(a);
        const idxB = preferred.indexOf(b);
        if (idxA !== -1 && idxB !== -1) return idxA - idxB;
        if (idxA !== -1) return -1;
        if (idxB !== -1) return 1;
        return a.localeCompare(b);
      });
      setColumns(sortedKeys);
      // Default all to visible
      setVisibleColumns(new Set(sortedKeys));
      // Clear selection on new data
      setSelectedRows(new Set());
      setShowSelectedOnly(false);
    }
  }, [data]);

  const handleSort = (key: string) => {
    let direction: "asc" | "desc" = "asc";
    if (sortConfig.key === key && sortConfig.direction === "asc") {
      direction = "desc";
    }
    setSortConfig({ key, direction });
  };

  const moveColumn = (index: number, direction: "left" | "right") => {
    const newCols = [...columns];
    if (direction === "left" && index > 0) {
      [newCols[index - 1], newCols[index]] = [newCols[index], newCols[index - 1]];
    } else if (direction === "right" && index < newCols.length - 1) {
      [newCols[index], newCols[index + 1]] = [newCols[index + 1], newCols[index]];
    }
    setColumns(newCols);
  };

  const toggleColumn = (key: string) => {
    const newVisible = new Set(visibleColumns);
    if (newVisible.has(key)) {
      newVisible.delete(key);
    } else {
      newVisible.add(key);
    }
    setVisibleColumns(newVisible);
  };

  const sortedData = React.useMemo(() => {
    let sortableItems = [...processedData];
    if (sortConfig.key && sortConfig.direction) {
      sortableItems.sort((a, b) => {
        const aVal = a[sortConfig.key];
        const bVal = b[sortConfig.key];
        
        // Handle numbers
        if (!isNaN(parseFloat(aVal)) && !isNaN(parseFloat(bVal))) {
           return sortConfig.direction === "asc" 
             ? parseFloat(aVal) - parseFloat(bVal) 
             : parseFloat(bVal) - parseFloat(aVal);
        }
        
        // Handle strings
        const aString = String(aVal || "").toLowerCase();
        const bString = String(bVal || "").toLowerCase();
        
        if (aString < bString) return sortConfig.direction === "asc" ? -1 : 1;
        if (aString > bString) return sortConfig.direction === "asc" ? 1 : -1;
        return 0;
      });
    }
    return sortableItems;
  }, [processedData, sortConfig]);

  const displayData = React.useMemo(() => {
    if (showSelectedOnly) {
      return sortedData.filter(row => selectedRows.has(row._internal_id));
    }
    return sortedData;
  }, [sortedData, showSelectedOnly, selectedRows]);

  const toggleRow = (id: number) => {
    const newSelected = new Set(selectedRows);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedRows(newSelected);
  };

  const toggleAll = () => {
    // If showing selected only, select/deselect visible rows? 
    // Usually "Select All" selects all current view results.
    const allIds = displayData.map(r => r._internal_id);
    const allSelected = allIds.every(id => selectedRows.has(id));
    
    const newSelected = new Set(selectedRows);
    if (allSelected) {
      allIds.forEach(id => newSelected.delete(id));
    } else {
      allIds.forEach(id => newSelected.add(id));
    }
    setSelectedRows(newSelected);
  };

  const downloadData = (format: 'csv' | 'json') => {
    // Export selected rows regardless of visibility, or only filtering?
    // "Export (N)" usually implies exporting the selected set.
    // If nothing selected, export all sortedData (or displayData?).
    // Previous logic: selected > 0 ? selected : all.
    
    const rowsToExport = selectedRows.size > 0 
      ? sortedData.filter(r => selectedRows.has(r._internal_id))
      : sortedData;
    
    // Filter out hidden columns for export
    const exportColumns = columns.filter(col => visibleColumns.has(col));

    if (format === 'json') {
      // Create JSON with only visible columns
      const jsonData = rowsToExport.map(row => {
        const filteredRow: any = {};
        exportColumns.forEach(col => {
          filteredRow[col] = row[col];
        });
        return filteredRow;
      });
      
      const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `grant_data_${new Date().toISOString().slice(0,10)}.json`;
      a.click();
    } else if (format === 'csv') {
      // Create CSV headers
      const headerRow = exportColumns.map(col => `"${col.replace(/"/g, '""')}"`).join(',');
      
      // Create CSV rows
      const dataRows = rowsToExport.map(row => {
        return exportColumns.map(col => {
          const val = row[col];
          const strVal = typeof val === 'object' ? JSON.stringify(val) : String(val || '');
          return `"${strVal.replace(/"/g, '""')}"`;
        }).join(',');
      });
      
      const csvContent = [headerRow, ...dataRows].join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `grant_data_${new Date().toISOString().slice(0,10)}.csv`;
      a.click();
    }
  };

  return (
    <div>
      {/* Controls Bar */}
      <div className="mb-4 flex justify-between items-center bg-gray-50 p-2 rounded border border-gray-200">
        <div className="text-sm text-gray-600 flex items-center space-x-4">
          <span>
            {selectedRows.size > 0 
              ? `${selectedRows.size} row(s) selected` 
              : `Showing ${displayData.length} rows`}
          </span>
          {selectedRows.size > 0 && (
            <button 
              onClick={() => setShowSelectedOnly(!showSelectedOnly)}
              className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
                showSelectedOnly 
                  ? 'bg-blue-100 text-blue-800 hover:bg-blue-200'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {showSelectedOnly ? 'Show All' : 'Show Selected Only'}
            </button>
          )}
        </div>
        
        <div className="flex space-x-2">
          {/* Export Dropdown */}
          <details className="relative inline-block text-left">
            <summary className="inline-flex justify-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md shadow-sm hover:bg-blue-700 focus:outline-none cursor-pointer">
              Export {selectedRows.size > 0 ? `(${selectedRows.size})` : 'All'} ▼
            </summary>
            <div className="origin-top-right absolute right-0 mt-2 w-40 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-20">
              <div className="py-1">
                <button
                  onClick={() => downloadData('csv')}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Download CSV
                </button>
                <button
                  onClick={() => downloadData('json')}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Download JSON
                </button>
              </div>
            </div>
          </details>

          {/* Column Visibility Control */}
          <details className="relative inline-block text-left">
            <summary className="inline-flex justify-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none cursor-pointer">
              Columns ▼
            </summary>
            <div className="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-20 p-2 max-h-60 overflow-y-auto">
              <div className="space-y-2">
                {columns.map(col => (
                  <label key={col} className="flex items-center space-x-2 px-2 py-1 hover:bg-gray-100 rounded cursor-pointer">
                    <input
                      type="checkbox"
                      checked={visibleColumns.has(col)}
                      onChange={() => toggleColumn(col)}
                      className="rounded text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700 truncate" title={col}>
                      {col.replace(/_/g, " ")}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          </details>
        </div>
      </div>

      <table className="min-w-full divide-y divide-gray-200" onMouseLeave={() => setHoveredCell(null)}>
        <thead className="bg-gray-50">
          <tr>
            {/* Checkbox Column */}
            <th className="px-6 py-3 text-left">
              <input
                type="checkbox"
                checked={displayData.length > 0 && displayData.every(r => selectedRows.has(r._internal_id))}
                onChange={toggleAll}
                className="rounded text-blue-600 focus:ring-blue-500"
              />
            </th>
            {columns.filter(col => visibleColumns.has(col)).map((key, idx) => (
              <th
                key={key}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider select-none relative group"
              >
                <div className="flex items-center space-x-2">
                  <span 
                    className="cursor-pointer hover:text-blue-600"
                    onClick={() => handleSort(key)}
                  >
                    {key.replace(/_/g, " ")}
                    {sortConfig.key === key && (
                      <span className="ml-1 text-blue-600">
                        {sortConfig.direction === "asc" ? "↑" : "↓"}
                      </span>
                    )}
                  </span>
                  
                  {/* Simple Reorder Controls (Visible on hover) */}
                  <div className="hidden group-hover:flex items-center space-x-1 ml-2">
                    <button 
                      onClick={(e) => { e.stopPropagation(); moveColumn(columns.indexOf(key), "left"); }}
                      disabled={columns.indexOf(key) === 0}
                      className="p-1 hover:bg-gray-200 rounded disabled:opacity-30"
                      title="Move Left"
                    >
                      ←
                    </button>
                    <button 
                      onClick={(e) => { e.stopPropagation(); moveColumn(columns.indexOf(key), "right"); }}
                      disabled={columns.indexOf(key) === columns.length - 1}
                      className="p-1 hover:bg-gray-200 rounded disabled:opacity-30"
                      title="Move Right"
                    >
                      →
                    </button>
                  </div>
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {displayData.map((row: any) => {
             // row has _internal_id now
             const isSelected = selectedRows.has(row._internal_id);
             return (
              <tr key={row._internal_id} className={isSelected ? "bg-blue-50 hover:bg-blue-100 transition-colors" : "hover:bg-gray-50 transition-colors"}>
                {/* Checkbox Cell */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleRow(row._internal_id)}
                    className="rounded text-blue-600 focus:ring-blue-500"
                  />
                </td>
                {columns.filter(col => visibleColumns.has(col)).map((key) => {
                  let content = typeof row[key] === "object" && row[key] !== null ? JSON.stringify(row[key]) : String(row[key] ?? "");
                  if (content === "null" || content === "None") content = "";
                  return (
                    <td
                      key={key}
                      className="px-6 py-4 text-sm text-gray-500 cursor-default align-top"
                      onMouseEnter={(e) => {
                         if (content) {
                           setHoveredCell({
                             content,
                             x: e.clientX,
                             y: e.clientY
                           });
                         }
                      }}
                      onMouseMove={(e) => {
                         if (hoveredCell) setHoveredCell(prev => prev ? ({ ...prev, x: e.clientX, y: e.clientY }) : null);
                      }}
                      onMouseLeave={() => setHoveredCell(null)}
                    >
                      <div className="line-clamp-3 whitespace-normal break-words max-w-xs">
                        {content || <span className="text-gray-300 italic">N/A</span>}
                      </div>
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
      
      {/* Popup Portal/Overlay */}
      {hoveredCell && (
        <div 
          className="fixed z-50 bg-gray-900 text-white text-xs rounded shadow-lg p-2 max-w-md break-words pointer-events-none"
          style={{
            top: hoveredCell.y + 10,
            left: hoveredCell.x + 10,
            transform: 'translate(0, 0)' 
          }}
        >
          {hoveredCell.content}
        </div>
      )}
    </div>
  );
};
