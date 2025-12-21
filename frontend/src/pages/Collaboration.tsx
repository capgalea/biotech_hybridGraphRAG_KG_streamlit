import React, { useState } from "react";
import { Search, Loader2, User } from "lucide-react";
import { collaborationService } from "../services/api";

export const Collaboration = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchTerm.trim()) return;

    setLoading(true);
    setError("");
    setProfile(null);

    try {
      const response = await collaborationService.getResearcher(searchTerm);
      setProfile(response.data);
    } catch (err) {
      setError("Researcher not found or error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">
        Researcher Collaboration
      </h1>

      {/* Search */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
        <form onSubmit={handleSearch} className="flex gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-3 text-gray-400" size={20} />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search researcher name..."
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? <Loader2 className="animate-spin" /> : "Search"}
          </button>
        </form>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-50 text-red-600 rounded-lg border border-red-200">
          {error}
        </div>
      )}

      {/* Profile */}
      {profile && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="p-6 border-b border-gray-200 bg-gray-50 flex items-center gap-4">
            <div className="p-3 bg-blue-100 rounded-full text-blue-600">
              <User size={32} />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                {profile.researcher_name}
              </h2>
              <p className="text-gray-600">
                {profile.title} • {profile.department}
              </p>
            </div>
          </div>

          <div className="p-6 space-y-6">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Institutions</h3>
              <div className="flex flex-wrap gap-2">
                {profile.institutions.map((inst: string, i: number) => (
                  <span
                    key={i}
                    className="px-3 py-1 bg-gray-100 rounded-full text-sm text-gray-700"
                  >
                    {inst}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 mb-2">
                Grants ({profile.grants.length})
              </h3>
              <div className="space-y-4">
                {profile.grants.map((grant: any, i: number) => (
                  <div
                    key={i}
                    className="p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-medium text-blue-600">
                        {grant.title}
                      </h4>
                      <span className="text-sm font-mono bg-green-50 text-green-700 px-2 py-1 rounded">
                        {grant.amount}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 line-clamp-2">
                      {grant.description}
                    </p>
                    <div className="mt-2 text-xs text-gray-500 flex gap-4">
                      <span>{grant.agency}</span>
                      <span>
                        {grant.start_date} - {grant.end_date}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
