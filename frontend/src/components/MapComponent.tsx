import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { analyticsService } from '../services/api';

interface MapData {
    institution_name: string;
    latitude: number;
    longitude: number;
    total_funding: number;
    project_count: number;
    researcher_count: number;
    top_funders: string[];
}

const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-AU', {
        style: 'currency',
        currency: 'AUD',
        maximumFractionDigits: 0,
    }).format(amount);
};

interface MapComponentProps {
    filters: any;
}

const MapComponent: React.FC<MapComponentProps> = ({ filters }) => {
    const [data, setData] = useState<MapData[]>([]);
    const [loading, setLoading] = useState(true);
    const [center, setCenter] = useState<[number, number]>([-25.2744, 133.7751]); // Australia Center
    const [zoom, setZoom] = useState(4);

    useEffect(() => {
        const fetchMapData = async () => {
            setLoading(true);
            try {
                // Clean filters to remove empty strings which cause 422 errors on backend for int fields
                const cleanedFilters = Object.fromEntries(
                    Object.entries(filters).filter(([_, v]) => v !== "" && v !== null && v !== undefined)
                );
                
                const response = await analyticsService.getMapData(cleanedFilters);
                setData(response.data);
            } catch (error) {
                console.error("Error fetching map data:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchMapData();
    }, [filters]);

    // Debug logging can be removed or kept minimal
    useEffect(() => {
        // console.log("Map Data:", data);
        // console.log("Map Filters:", filters);
    }, [data, filters]);

    if (loading) {
        return (
            <div className="flex justify-center items-center h-[400px]">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    return (
        <div className="p-1 rounded-lg bg-white shadow overflow-hidden h-[500px] w-full relative">
            <MapContainer 
                center={center} 
                zoom={zoom} 
                className="h-full w-full rounded-md z-0"
                scrollWheelZoom={true}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                
                {data.map((inst, idx) => (
                    <CircleMarker 
                        key={idx} 
                        center={[inst.latitude, inst.longitude]}
                        pathOptions={{ 
                            color: '#2563eb', // Blue-600
                            fillColor: '#3b82f6', // Blue-500
                            fillOpacity: 0.4,
                            weight: 1
                        }}
                        // Sqrt scale: $1M -> ~6px, $100M -> ~12px, $1B -> ~30px
                        radius={Math.max(5, (Math.sqrt(inst.total_funding || 0) / 1200) + 4)} 
                    >
                        <Popup>
                            <div className="min-w-[200px] font-sans">
                                <h4 className="font-bold text-base mb-2">{inst.institution_name}</h4>
                                
                                <div className="space-y-1 text-sm text-gray-700">
                                    <p>
                                        <strong className="font-semibold text-gray-900">Total Funding:</strong> {formatCurrency(inst.total_funding)}
                                    </p>
                                    <p>
                                        <strong className="font-semibold text-gray-900">Projects:</strong> {inst.project_count}
                                    </p>
                                    <p>
                                        <strong className="font-semibold text-gray-900">Researchers:</strong> {inst.researcher_count}
                                    </p>
                                </div>
                                
                                <div className="mt-3">
                                    <p className="font-semibold text-sm text-gray-900">Top Funders:</p>
                                    <ul className="list-disc pl-5 mt-1 text-xs text-gray-600 space-y-0.5">
                                        {inst.top_funders.map((funder, i) => (
                                            <li key={i}>{funder}</li>
                                        ))}
                                    </ul>
                                </div>

                                <a 
                                    href={`https://www.google.com/search?q=${encodeURIComponent(inst.institution_name)}`} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="block mt-3 text-sm text-blue-600 hover:text-blue-800 hover:underline"
                                >
                                    Visit Website &rarr;
                                </a>
                            </div>
                        </Popup>
                    </CircleMarker>
                ))}
            </MapContainer>
        </div>
    );
};

export default MapComponent;
