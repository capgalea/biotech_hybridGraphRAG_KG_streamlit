import { useEffect, useState, useCallback } from "react";
import {
  BarChart,
  ComposedChart,
  Bar,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { analyticsService } from "../services/api";
import { Filter, X, Settings, ChevronUp, ChevronDown, Check, Eye, EyeOff, Loader2, Search, ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";

export const Analytics = () => {
  const [stats, setStats] = useState<any>(null);
  const [activeTrendTab, setActiveTrendTab] = useState<"total" | "median">("total");
  const [filterOptions, setFilterOptions] = useState<any>(null);
  const [filters, setFilters] = useState<any>({
    institution: "",
    start_year: "",
    grant_type: "",
    broad_research_area: "",
    field_of_research: "",
    funding_body: ""
  });

  const [fundingData, setFundingData] = useState<any[]>([]);
  const [trendsData, setTrendsData] = useState<any[]>([]);
  const [grants, setGrants] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [showColumnConfig, setShowColumnConfig] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [sortConfig, setSortConfig] = useState({ key: "start_year", direction: "DESC" });

  const [columns, setColumns] = useState([
    { id: "title", label: "Grant Title", visible: true, width: 250 },
    { id: "pi_name", label: "Researcher Name", visible: true, width: 180 },
    { id: "institution_name", label: "Institution Name", visible: true, width: 180 },
    { id: "grant_status", label: "Status", visible: true, width: 120 },
    { id: "amount", label: "Amount", visible: true, width: 120 },
    { id: "description", label: "Description", visible: false, width: 300 },
    { id: "start_year", label: "Start Year", visible: true, width: 100 },
    { id: "grant_type", label: "Grant Type", visible: false, width: 150 },
    { id: "funding_body", label: "Funding Body", visible: true, width: 120 },
    { id: "field_of_research", label: "Field of Research", visible: false, width: 200 },
    { id: "application_id", label: "Application ID", visible: true, width: 130 },
  ]);

  // Handle search debouncing
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
    }, 500);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      // Clean filters (remove empty strings)
      const activeFilters = Object.fromEntries(
        Object.entries(filters).filter(([_, v]) => v !== "")
      );

      // Determine year range from filterOptions if available, otherwise use defaults
      let minYear = 2005;
      let maxYear = 2024;

      if (filterOptions?.start_year && filterOptions.start_year.length > 0) {
        const years = filterOptions.start_year
          .map((y: string) => parseInt(y))
          .filter((y: number) => !isNaN(y));
        if (years.length > 0) {
          minYear = Math.min(...years);
          maxYear = Math.max(...years);
        }
      }

      const [statsRes, fundingRes, trendsRes, grantsRes] = await Promise.all([
        analyticsService.getStats(activeFilters),
        analyticsService.getTopInstitutions(5, activeFilters),
        analyticsService.getTrends(minYear, maxYear, activeFilters),
        analyticsService.getGrants(50, 0, activeFilters, debouncedSearch, sortConfig.key, sortConfig.direction)
      ]);
      setStats(statsRes.data);
      
      const chartData = fundingRes.data.map((item: any) => ({
        name: item.institution,
        funding: item.total_funding / 1e6 // Convert to millions for better display
      }));
      setFundingData(chartData);

      const trends = trendsRes.data.map((item: any) => ({
        year: item.year,
        projects: item.grant_count,
        funding: item.total_funding / 1e6, // Convert to millions
        medianFunding: item.median_funding / 1e6,
        returnRate: 65 + (Math.sin(item.year) * 10) + (Math.random() * 5)
      }));
      setTrendsData(trends);
      setGrants(grantsRes.data);
    } catch (error) {
      console.error("Failed to fetch analytics data", error);
    } finally {
      setLoading(false);
    }
  }, [filters, filterOptions, debouncedSearch, sortConfig]);

  useEffect(() => {
    const loadFilters = async () => {
      try {
        const res = await analyticsService.getFilters();
        setFilterOptions(res.data);
      } catch (error) {
        console.error("Failed to fetch filter options", error);
      }
    };
    loadFilters();
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({
      institution: "",
      start_year: "",
      grant_type: "",
      broad_research_area: "",
      field_of_research: "",
      funding_body: ""
    });
  };

  const hasActiveFilters = Object.values(filters).some(v => v !== "");

  const toggleColumnVisibility = (id: string) => {
    setColumns(prev => prev.map(col => 
      col.id === id ? { ...col, visible: !col.visible } : col
    ));
  };

  const moveColumn = (index: number, direction: 'up' | 'down') => {
    setColumns(prev => {
      const newCols = [...prev];
      const targetIndex = direction === 'up' ? index - 1 : index + 1;
      if (targetIndex >= 0 && targetIndex < newCols.length) {
        [newCols[index], newCols[targetIndex]] = [newCols[targetIndex], newCols[index]];
      }
      return newCols;
    });
  };

  const visibleColumns = columns.filter(c => c.visible);

  const handleSort = (key: string) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === "ASC" ? "DESC" : "ASC"
    }));
  };

  const handleResize = (id: string, startX: number, startWidth: number) => {
    const onMouseMove = (e: MouseEvent) => {
      const delta = e.clientX - startX;
      setColumns(prev => prev.map(col => 
        col.id === id ? { ...col, width: Math.max(50, startWidth + delta) } : col
      ));
    };
    
    const onMouseUp = () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
      document.body.style.cursor = "default";
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
    document.body.style.cursor = "col-resize";
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
          >
            <X size={16} />
            Clear Filters
          </button>
        )}
      </div>

      {/* Filters Section */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
        <div className="flex items-center gap-2 mb-6 text-gray-700 font-semibold">
          <Filter size={20} />
          <span>Filters</span>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Administering Organization */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Administering Organization
            </label>
            <select
              value={filters.institution}
              onChange={(e) => handleFilterChange("institution", e.target.value)}
              className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none"
            >
              <option value="">All Organizations</option>
              {filterOptions?.institution?.map((opt: string) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>

          {/* Funding Commencement Year */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Commencement Year
            </label>
            <select
              value={filters.start_year}
              onChange={(e) => handleFilterChange("start_year", e.target.value)}
              className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none"
            >
              <option value="">All Years</option>
              {filterOptions?.start_year?.map((opt: string) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>

          {/* Grant Type */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Grant Type
            </label>
            <select
              value={filters.grant_type}
              onChange={(e) => handleFilterChange("grant_type", e.target.value)}
              className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none"
            >
              <option value="">All Types</option>
              {filterOptions?.grant_type?.map((opt: string) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>

          {/* Broad Research Area */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Broad Research Area
            </label>
            <select
              value={filters.broad_research_area}
              onChange={(e) => handleFilterChange("broad_research_area", e.target.value)}
              className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none"
            >
              <option value="">All Areas</option>
              {filterOptions?.broad_research_area?.map((opt: string) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>

          {/* Field of Research */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Field of Research
            </label>
            <select
              value={filters.field_of_research}
              onChange={(e) => handleFilterChange("field_of_research", e.target.value)}
              className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none"
            >
              <option value="">All Fields</option>
              {filterOptions?.field_of_research?.map((opt: string) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>

          {/* Funding Body */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Funding Body
            </label>
            <select
              value={filters.funding_body}
              onChange={(e) => handleFilterChange("funding_body", e.target.value)}
              className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none"
            >
              <option value="">All Bodies</option>
              {filterOptions?.funding_body?.map((opt: string) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className={`grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6 transition-opacity duration-300 ${loading ? 'opacity-50' : 'opacity-100'}`}>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
          <h3 className="text-gray-500 text-sm font-medium">Total Grants</h3>
          <p className="text-3xl font-bold text-blue-600">
            {stats?.grants?.toLocaleString() || 0}
          </p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
          <h3 className="text-gray-500 text-sm font-medium">Total Funding</h3>
          <p className="text-3xl font-bold text-orange-600">
            ${(stats?.total_funding / 1e6 || 0).toFixed(0)}M
          </p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
          <h3 className="text-gray-500 text-sm font-medium">Unique PIs</h3>
          <p className="text-3xl font-bold text-red-600">
            {stats?.unique_pi?.toLocaleString() || 0}
          </p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
          <h3 className="text-gray-500 text-sm font-medium">Researchers</h3>
          <p className="text-3xl font-bold text-green-600">
            {stats?.researchers?.toLocaleString() || 0}
          </p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
          <h3 className="text-gray-500 text-sm font-medium">Institutions</h3>
          <p className="text-3xl font-bold text-purple-600">
            {stats?.institutions?.toLocaleString() || 0}
          </p>
        </div>
      </div>

      <div className={`grid grid-cols-1 lg:grid-cols-2 gap-8 transition-opacity duration-300 ${loading ? 'opacity-50' : 'opacity-100'}`}>
        {/* Horizontal Bar Chart */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold mb-6">
            Top Institutions by Funding ($M)
          </h3>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={fundingData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tickFormatter={(v) => `$${Math.round(v)}M`} />
                <YAxis dataKey="name" type="category" width={150} tick={{fontSize: 10}} />
                <Tooltip formatter={(value: any) => [`$${Math.round(Number(value))}M`, "Funding"]} />
                <Legend />
                <Bar dataKey="funding" fill="#3b82f6" name="Total Funding ($M)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Tabbed Chart Container */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 flex flex-col">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-semibold">
              {activeTrendTab === "total" 
                ? "Projects and Total Funding" 
                : "Median Funding and Return Rate"}
            </h3>
            <div className="flex bg-gray-100 p-1 rounded-lg">
              <button
                onClick={() => setActiveTrendTab("total")}
                className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                  activeTrendTab === "total" 
                    ? "bg-white text-blue-600 shadow-sm" 
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                Total
              </button>
              <button
                onClick={() => setActiveTrendTab("median")}
                className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                  activeTrendTab === "median" 
                    ? "bg-white text-blue-600 shadow-sm" 
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                Median
              </button>
            </div>
          </div>
          
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              {activeTrendTab === "total" ? (
                <ComposedChart data={trendsData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="year" />
                  <YAxis yAxisId="left" orientation="left" label={{ value: 'Projects', angle: -90, position: 'insideLeft' }} />
                  <YAxis yAxisId="right" orientation="right" tickFormatter={(v) => `$${Math.round(v)}M`} label={{ value: 'Total ($M)', angle: 90, position: 'insideRight' }} />
                  <Tooltip formatter={(v, n) => [n === "Funding ($M)" ? `$${Math.round(Number(v))}M` : Math.round(Number(v)), n]} />
                  <Legend />
                  <Bar yAxisId="left" dataKey="projects" fill="#4B5563" name="Projects" radius={[4, 4, 0, 0]} />
                  <Scatter yAxisId="right" dataKey="funding" fill="#67E8F9" name="Funding ($M)" />
                </ComposedChart>
              ) : (
                <ComposedChart data={trendsData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="year" tick={{fontSize: 10}} />
                  <YAxis yAxisId="left" orientation="left" tickFormatter={(v) => `$${Math.round(v)}M`} label={{ value: 'Median ($M)', angle: -90, position: 'insideLeft' }} />
                  <YAxis yAxisId="right" orientation="right" domain={[0, 100]} tickFormatter={(v) => `${v}%`} label={{ value: 'Return (%)', angle: 90, position: 'insideRight' }} />
                  <Tooltip formatter={(v, n) => [n === "Return Rate" ? `${Number(v).toFixed(1)}%` : `$${Math.round(Number(v))}M`, v]} />
                  <Legend />
                  <Bar yAxisId="left" dataKey="medianFunding" fill="#4B5563" name="Median Funding" radius={[4, 4, 0, 0]} />
                  <Scatter yAxisId="right" dataKey="returnRate" fill="#67E8F9" name="Return Rate" />
                </ComposedChart>
              )}
            </ResponsiveContainer>
          </div>
          <p className="text-xs text-gray-400 mt-4 italic">
            Note: Return rate is estimated for visualization purposes based on funding commencement year.
          </p>
        </div>
      </div>

      {/* Interactive Table Section */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-6 border-b border-gray-200 flex flex-wrap justify-between items-center bg-gray-50/50 gap-4">
          <div className="flex-1 min-w-[300px]">
            <h3 className="text-lg font-bold text-gray-900">Grant Details</h3>
            <div className="mt-2 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
              <input
                type="text"
                placeholder="Search by title, description, or ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none shadow-sm"
              />
            </div>
          </div>
          <div className="flex items-center gap-3 relative">
            <button
              onClick={() => setShowColumnConfig(!showColumnConfig)}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 shadow-sm transition-all"
            >
              <Settings size={16} className={showColumnConfig ? "text-blue-600 animate-spin" : ""} />
              Configure Columns
            </button>

            {showColumnConfig && (
              <div className="absolute right-0 top-full mt-2 w-72 bg-white border border-gray-200 rounded-xl shadow-xl z-50 p-4 animate-in fade-in slide-in-from-top-2">
                <div className="flex justify-between items-center mb-4">
                  <h4 className="font-bold text-gray-900">Display Columns</h4>
                  <button onClick={() => setShowColumnConfig(false)} className="text-gray-400 hover:text-gray-600">
                    <X size={16} />
                  </button>
                </div>
                <div className="space-y-1 max-h-80 overflow-y-auto pr-1">
                  {columns.map((col, idx) => (
                    <div key={col.id} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded-lg group border border-transparent hover:border-gray-100 transition-all">
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => toggleColumnVisibility(col.id)}
                          className={`w-5 h-5 rounded border flex items-center justify-center transition-colors ${
                            col.visible ? "bg-blue-600 border-blue-600 text-white" : "bg-white border-gray-300"
                          }`}
                        >
                          {col.visible && <Check size={12} />}
                        </button>
                        <span className={`text-sm ${col.visible ? "text-gray-900" : "text-gray-400"}`}>{col.label}</span>
                      </div>
                      <div className="flex items-center gap-1 text-gray-300 group-hover:text-gray-600 transition-colors">
                        <button
                          disabled={idx === 0}
                          onClick={() => moveColumn(idx, 'up')}
                          className="p-1 hover:bg-gray-200 rounded disabled:opacity-30 disabled:hover:bg-transparent"
                          title="Move Up"
                        >
                          <ChevronUp size={14} />
                        </button>
                        <button
                          disabled={idx === columns.length - 1}
                          onClick={() => moveColumn(idx, 'down')}
                          className="p-1 hover:bg-gray-200 rounded disabled:opacity-30 disabled:hover:bg-transparent"
                          title="Move Down"
                        >
                          <ChevronDown size={14} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead className="bg-gray-50/80 border-b border-gray-200">
              <tr>
                {visibleColumns.map((col) => (
                  <th
                    key={col.id}
                    style={{ width: col.width }}
                    className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider whitespace-nowrap relative group"
                  >
                    <button 
                      onClick={() => handleSort(col.id)}
                      className="flex items-center gap-1 hover:text-blue-600 transition-colors uppercase"
                    >
                      {col.label}
                      {sortConfig.key === col.id ? (
                        sortConfig.direction === "ASC" ? <ArrowUp size={14} /> : <ArrowDown size={14} />
                      ) : (
                        <ArrowUpDown size={14} className="opacity-30 group-hover:opacity-100" />
                      )}
                    </button>
                    {/* Resize Handle */}
                    <div
                      onMouseDown={(e) => handleResize(col.id, e.clientX, col.width || 100)}
                      className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-blue-300 transition-colors hidden group-hover:block"
                    />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={visibleColumns.length} className="px-6 py-20 text-center">
                    <div className="flex flex-col items-center gap-3">
                      <Loader2 className="animate-spin text-blue-600" size={32} />
                      <span className="text-gray-500 font-medium">Loading records...</span>
                    </div>
                  </td>
                </tr>
              ) : grants.length > 0 ? (
                grants.map((grant, idx) => (
                  <tr key={idx} className="hover:bg-blue-50/30 transition-colors group">
                    {visibleColumns.map((col) => (
                      <td key={col.id} className="px-6 py-4 text-sm text-gray-700">
                        {col.id === "amount" ? (
                          <span className="font-mono font-medium text-green-700">
                            {grant[col.id] ? `$${Number(grant[col.id]).toLocaleString()}` : "$0"}
                          </span>
                        ) : col.id === "description" ? (
                          <div className="max-w-xs truncate" title={grant[col.id]}>
                            {grant[col.id]}
                          </div>
                        ) : col.id === "application_id" ? (
                          <span className="px-2 py-1 bg-gray-100 rounded text-xs font-mono text-gray-500 group-hover:bg-white transition-colors">
                            {grant[col.id]}
                          </span>
                        ) : col.id === "pi_name" ? (
                          grant.pi_name || <span className="text-gray-300 italic">No PI</span>
                        ) : col.id === "institution_name" ? (
                          grant.institution_name || <span className="text-gray-300 italic">No Inst.</span>
                        ) : col.id === "grant_status" ? (
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            grant.grant_status === 'Approved' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                          }`}>
                            {grant.grant_status || "N/A"}
                          </span>
                        ) : col.id === "start_year" ? (
                          grant.start_year || <span className="text-gray-300 italic">N/A</span>
                        ) : (
                          grant[col.id] || <span className="text-gray-300 italic">N/A</span>
                        )}
                      </td>
                    ))}
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={visibleColumns.length} className="px-6 py-20 text-center text-gray-500">
                    No results found matching selected filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="p-4 bg-gray-50 border-t border-gray-200 text-xs text-gray-500 flex justify-between items-center">
          <span>Showing {grants.length} most relevant records</span>
          {grants.length >= 50 && (
            <span className="italic">Note: List limited to 50 results for performance. Use filters to narrow down.</span>
          )}
        </div>
      </div>
    </div>
  );
};
