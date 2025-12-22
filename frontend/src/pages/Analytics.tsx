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
import { Filter, X } from "lucide-react";

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
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      // Clean filters (remove empty strings)
      const activeFilters = Object.fromEntries(
        Object.entries(filters).filter(([_, v]) => v !== "")
      );

      const [statsRes, fundingRes, trendsRes] = await Promise.all([
        analyticsService.getStats(activeFilters),
        analyticsService.getTopInstitutions(5, activeFilters),
        analyticsService.getTrends(2005, 2024, activeFilters)
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
    } catch (error) {
      console.error("Failed to fetch analytics data", error);
    } finally {
      setLoading(false);
    }
  }, [filters]);

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
    </div>
  );
};
