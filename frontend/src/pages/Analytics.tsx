import React, { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { analyticsService } from "../services/api";
import { Loader2 } from "lucide-react";

export const Analytics = () => {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const [fundingData, setFundingData] = useState<any[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, fundingRes] = await Promise.all([
          analyticsService.getStats(),
          analyticsService.getTopInstitutions(5)
        ]);
        setStats(statsRes.data);
        
        // Transform backend data for chart
        // Backend returns: { institution: "Name", total_funding: 12345.67, grant_count: 5 }
        // Recharts needs: { name: "Name", funding: 12345.67 }
        const chartData = fundingRes.data.map((item: any) => ({
          name: item.institution,
          funding: item.total_funding
        }));
        setFundingData(chartData);
      } catch (error) {
        console.error("Failed to fetch analytics data", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h3 className="text-gray-500 text-sm font-medium">Total Grants</h3>
          <p className="text-3xl font-bold text-blue-600">
            {stats?.grants || 0}
          </p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h3 className="text-gray-500 text-sm font-medium">Researchers</h3>
          <p className="text-3xl font-bold text-green-600">
            {stats?.researchers || 0}
          </p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h3 className="text-gray-500 text-sm font-medium">Institutions</h3>
          <p className="text-3xl font-bold text-purple-600">
            {stats?.institutions || 0}
          </p>
        </div>
      </div>

      {/* Charts */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold mb-6">
          Top Institutions by Funding
        </h3>
        <div className="h-[400px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={fundingData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={100} />
              <Tooltip />
              <Legend />
              <Bar dataKey="funding" fill="#3b82f6" name="Total Funding ($M)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
