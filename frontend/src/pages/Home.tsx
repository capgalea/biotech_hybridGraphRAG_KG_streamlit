import React, { useState } from "react";
import { Send, Loader2 } from "lucide-react";
import { queryService } from "../services/api";
import ReactMarkdown from "react-markdown";

export const Home = () => {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [llmModel, setLlmModel] = useState("claude-4-5-sonnet");
  const [enableSearch, setEnableSearch] = useState(true);

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
      setResult(response.data);
    } catch (error: any) {
      console.error("Search failed", error);
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        "Failed to process query";
      setResult({ error: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="text-center space-y-2">
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
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., Find grants related to CRISPR in 2024..."
              className="w-full pl-4 pr-12 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
            />
            <button
              type="submit"
              disabled={loading}
              className="absolute right-2 top-2 p-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {loading ? (
                <Loader2 className="animate-spin" size={20} />
              ) : (
                <Send size={20} />
              )}
            </button>
          </div>

          <div className="flex flex-wrap gap-4 items-center text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <label>Model:</label>
              <select
                value={llmModel}
                onChange={(e) => setLlmModel(e.target.value)}
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
                onChange={(e) => setEnableSearch(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500"
              />
              <span>Enable Web Search</span>
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
                  <ReactMarkdown>{result.summary}</ReactMarkdown>
                </div>
              )}

              {/* Data Table Section */}
              {result.data && result.data.length > 0 ? (
                <div className="overflow-x-auto">
                  <h3 className="text-lg font-semibold mb-3">Data Results</h3>
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        {Object.keys(result.data[0]).map((key) => (
                          <th
                            key={key}
                            className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                          >
                            {key.replace(/_/g, " ")}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {result.data.map((row: any, idx: number) => (
                        <tr key={idx}>
                          {Object.values(row).map((val: any, i) => (
                            <td
                              key={i}
                              className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
                            >
                              {typeof val === "object"
                                ? JSON.stringify(val)
                                : String(val)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
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
