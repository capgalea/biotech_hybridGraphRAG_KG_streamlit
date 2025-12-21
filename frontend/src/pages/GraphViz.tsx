import { useEffect, useRef, useState } from "react";
import { Network } from "vis-network";
import type { Node, Edge } from "vis-network";
import { DataSet } from "vis-data";
import { graphService } from "../services/api";
import { Loader2, RefreshCw } from "lucide-react";

export const GraphViz = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(false);
  const [limit, setLimit] = useState(50);

  const loadGraph = async () => {
    if (!containerRef.current) return;
    setLoading(true);

    try {
      const response = await graphService.getData(limit);
      const { nodes, links } = response.data;

      // Transform data for vis-network
      // Assuming backend returns { nodes: [{id, labels, properties}], links: [{source, target, type}] }
      // We need to adapt this based on actual backend response structure from graph.py

      // Since the backend graph.py I saw earlier returns a list of {n, r, m},
      // we might need to process it here if the backend doesn't do it perfectly.
      // But let's assume the backend returns the transformed structure I saw in the code snippet I read.

      // Actually, looking back at graph.py, it returns `{"nodes": list(nodes.values()), "links": links}`
      // where nodes have `id`, `labels`, `properties`
      // and links have `source`, `target`, `type`.

      const visNodes = new DataSet<Node>(
        nodes.map((n: any) => ({
          id: n.id,
          label: n.properties.name || n.properties.title || n.id,
          group: n.labels[0],
          title: JSON.stringify(n.properties, null, 2), // Tooltip
        }))
      );

      const visEdges = new DataSet<Edge>(
        links.map((l: any, i: number) => ({
          id: i,
          from: l.source,
          to: l.target,
          label: l.type,
          arrows: "to",
        }))
      );

      const data = { nodes: visNodes, edges: visEdges };
      const options = {
        nodes: {
          shape: "dot",
          size: 16,
          font: { size: 12, color: "#000000" },
          borderWidth: 2,
        },
        edges: {
          width: 1,
          color: { inherit: "from" },
          smooth: { enabled: true, type: "continuous", roundness: 0.5 },
        },
        physics: {
          stabilization: false,
          barnesHut: {
            gravitationalConstant: -8000,
            springConstant: 0.04,
            springLength: 95,
          },
        },
        groups: {
          Grant: { color: { background: "#fb7185", border: "#e11d48" } }, // Rose
          Researcher: { color: { background: "#60a5fa", border: "#2563eb" } }, // Blue
          Institution: { color: { background: "#c084fc", border: "#9333ea" } }, // Purple
        },
      };

      new Network(containerRef.current, data, options);
    } catch (error) {
      console.error("Failed to load graph", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGraph();
  }, []);

  return (
    <div className="h-[calc(100vh-100px)] flex flex-col space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">
          Graph Visualization
        </h1>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Limit:</label>
            <input
              type="number"
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="border rounded px-2 py-1 w-20"
            />
          </div>
          <button
            onClick={loadGraph}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="animate-spin" size={16} />
            ) : (
              <RefreshCw size={16} />
            )}
            Refresh
          </button>
        </div>
      </div>

      <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden relative">
        <div ref={containerRef} className="absolute inset-0" />
        {loading && (
          <div className="absolute inset-0 bg-white/80 flex items-center justify-center z-10">
            <Loader2 className="animate-spin text-blue-600" size={48} />
          </div>
        )}
      </div>
    </div>
  );
};
