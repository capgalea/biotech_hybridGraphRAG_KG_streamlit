import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { GrantTable } from '../components/GrantRetrieval/GrantTable';

const API_Base = 'http://127.0.0.1:8001/api/retrieval';

// Helper to determine if status is Neo4j related
const isNeo4jStatus = (msg: string) => msg.toLowerCase().includes('neo4j');

export const GrantRetrieval: React.FC = () => {
  const [retrieving, setRetrieving] = useState(false);
  const [globalStatus, setGlobalStatus] = useState("Ready");
  const [refreshKey, setRefreshKey] = useState(0);
  const [neo4jStats, setNeo4jStats] = useState<{ grants: number, researchers: number, institutions: number } | null>(null);
  const [neo4jError, setNeo4jError] = useState<string | null>(null);

  const fetchNeo4jStats = useCallback(async () => {
    try {
      const res = await axios.get(`${API_Base}/neo4j_stats`);
      if (res.data.status === 'ok') {
        setNeo4jStats(res.data.stats);
        setNeo4jError(null);
      } else {
        setNeo4jError(res.data.message || 'Failed to connect');
        setNeo4jStats(null);
      }
    } catch {
      setNeo4jError('Neo4j not available');
      setNeo4jStats(null);
    }
  }, []);

  // Poll status
  useEffect(() => {
    let interval: any;
    let errorCount = 0;
    const maxErrors = 5;

    if (retrieving) {
      interval = setInterval(async () => {
        try {
          const res = await axios.get(`${API_Base}/status`);
          const { is_running, message } = res.data;
          setGlobalStatus(message);
          errorCount = 0; // Reset on success

          if (!is_running) {
            setRetrieving(false);
            setRefreshKey(prev => prev + 1);
            fetchNeo4jStats();
          }
        } catch (error) {
          console.error("Status check failed", error);
          errorCount++;
          if (errorCount >= maxErrors) {
              setGlobalStatus("Connection lost. Retrying...");
              // We don't setRetrieving(false) yet, we let it keep trying for a bit longer
              // but if it's really dead, maybe eventually stop
              if (errorCount > 30) { // ~30 seconds of total failure
                  setRetrieving(false);
                  setGlobalStatus("Connection timed out.");
              }
          }
        }
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [retrieving, fetchNeo4jStats]);

  useEffect(() => {
    // eslint-disable-next-line
    fetchNeo4jStats();
  }, [fetchNeo4jStats]);
  const handleRetrieve = async () => {
    try {
      await axios.post(`${API_Base}/start`);
      setRetrieving(true);
      setGlobalStatus("Starting retrieval...");
    } catch (error) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const err = error as any;
        if (err.response?.status === 409) {
             setGlobalStatus("Task already running");
        } else {
            console.error(err);
            setGlobalStatus(`Error: ${err.message}`);
        }
    }
  };

  const handleLoadNeo4j = async () => {
    try {
      await axios.post(`${API_Base}/load-neo4j`);
      setRetrieving(true);
      setGlobalStatus("Starting Neo4j load...");
    } catch (error) {
         // eslint-disable-next-line @typescript-eslint/no-explicit-any
         const err = error as any;
         if (err.response?.status === 409) {
             setGlobalStatus("Task already running");
        } else {
            console.error(err);
            setGlobalStatus(`Error: ${err.message}`);
        }
    }
  };

  const isNeo4j = isNeo4jStatus(globalStatus);

  const [selectedSources, setSelectedSources] = useState<string[]>(['combined']);

  const toggleSource = (source: string) => {
    setSelectedSources(prev => 
      prev.includes(source) 
        ? prev.filter(s => s !== source)
        : [...prev, source]
    );
  };

  return (
    <div className="max-w-[1600px] mx-auto p-8 text-gray-900">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Grant Retrieval Dashboard</h1>
        <p className="text-gray-500">Retrieve grant data from NHMRC/ARC and load into the Knowledge Graph.</p>

        {/* Status Bar */}
        <div 
          className={`min-h-[40px] my-5 p-3 rounded-lg border flex items-center gap-3 transition-all ${
            retrieving 
              ? 'bg-blue-50 border-blue-200' 
              : 'bg-gray-50 border-gray-200'
          }`}
        >
          {retrieving && (
            <div className={`w-5 h-5 border-2 rounded-full animate-spin ${
              isNeo4j ? 'border-green-600 border-t-transparent' : 'border-blue-500 border-t-transparent'
            }`} />
          )}
          <span className={`text-sm font-medium ${
            retrieving 
              ? (isNeo4j ? 'text-green-700' : 'text-blue-700') 
              : 'text-gray-500'
          }`}>
            {globalStatus}
          </span>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap gap-4 mt-4 items-center">
          <button 
            onClick={handleRetrieve} 
            disabled={retrieving}
            className={`px-6 py-3 rounded-md font-semibold text-white transition-opacity disabled:opacity-70 disabled:cursor-not-allowed ${
                retrieving ? 'bg-gray-800' : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {retrieving && !isNeo4j ? "Retrieval in Progress..." : "Retrieve New Data"}
          </button>

          <button
            onClick={handleLoadNeo4j}
            disabled={retrieving}
            className={`px-6 py-3 rounded-md font-semibold text-white transition-opacity disabled:opacity-70 disabled:cursor-not-allowed ${
                retrieving ? 'bg-gray-800' : 'bg-green-600 hover:bg-green-700'
            }`}
          >
            {retrieving && isNeo4j ? "Loading to Neo4j..." : "Load to Neo4j"}
          </button>
          
          <div className="h-8 w-px bg-gray-300 mx-2"></div>
          
          <div className="flex items-center gap-4 bg-gray-50 p-2 rounded-lg border border-gray-200">
              <span className="text-sm font-semibold text-gray-700">Display:</span>
              <label className="flex items-center gap-2 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={selectedSources.includes('combined')} 
                    onChange={() => toggleSource('combined')}
                    className="rounded text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">Combined</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={selectedSources.includes('nhmrc')} 
                    onChange={() => toggleSource('nhmrc')}
                    className="rounded text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">NHMRC</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={selectedSources.includes('arc')} 
                    onChange={() => toggleSource('arc')}
                    className="rounded text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">ARC</span>
              </label>
          </div>
        </div>

        {/* Neo4j Stats */}
        <div className="mt-6 p-4 rounded-xl bg-gray-50 border border-gray-200">
            <div className="flex items-center justify-between mb-3">
                <span className="font-semibold text-green-700 text-sm">
                    Neo4j Database Statistics
                </span>
                <button 
                    onClick={fetchNeo4jStats}
                    className="text-gray-500 hover:text-gray-700 text-xs underline bg-transparent border-none cursor-pointer"
                >
                    Refresh Stats
                </button>
            </div>
            
            {neo4jError ? (
                <div className="text-red-500 text-sm">⚠️ {neo4jError}</div>
            ) : neo4jStats ? (
                <div className="flex flex-wrap gap-6">
                    <StatItem label="Grants" value={neo4jStats.grants} />
                    <StatItem label="Researchers" value={neo4jStats.researchers} />
                    <StatItem label="Institutions" value={neo4jStats.institutions} />
                </div>
            ) : (
                <div className="text-gray-500 text-sm">Loading stats...</div>
            )}
        </div>
      </header>

      <main className="space-y-8">
        {selectedSources.includes('combined') && (
            <GrantTable 
                apiBase={API_Base} 
                refreshKey={refreshKey} 
                source="combined" 
                title="Combined Grants" 
            />
        )}
        {selectedSources.includes('nhmrc') && (
            <GrantTable 
                apiBase={API_Base} 
                refreshKey={refreshKey} 
                source="nhmrc" 
                title="NHMRC Grants" 
            />
        )}
        {selectedSources.includes('arc') && (
            <GrantTable 
                apiBase={API_Base} 
                refreshKey={refreshKey} 
                source="arc" 
                title="ARC Grants" 
            />
        )}
        {selectedSources.length === 0 && (
             <div className="text-center p-12 bg-gray-50 rounded-xl border border-dashed border-gray-300 text-gray-500">
                 Select a dataset above to view grants.
             </div>
        )}
      </main>
    </div>
  );
};

const StatItem = ({ label, value }: { label: string, value: number }) => (
    <div className="text-center">
        <div className="text-xl font-bold text-gray-900">{value?.toLocaleString() || 0}</div>
        <div className="text-xs text-gray-500">{label}</div>
    </div>
);
