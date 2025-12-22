import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_URL,
});

export const queryService = {
  processQuery: (query: string, llmModel: string, enableSearch: boolean) =>
    api.post('/query/', { query, llm_model: llmModel, enable_search: enableSearch }),
};

export const analyticsService = {
  getStats: (filters: any = {}) => api.get('/analytics/stats', { params: filters }),
  getSchema: () => api.get('/analytics/schema'),
  getTopInstitutions: (limit: number = 10, filters: any = {}) =>
    api.get(`/analytics/institutions`, { params: { limit, ...filters } }),
  getTrends: (startYear: number = 2000, endYear: number = 2024, filters: any = {}) =>
    api.get(`/analytics/trends`, { params: { start_year_min: startYear, start_year_max: endYear, ...filters } }),
  getFilters: () => api.get('/analytics/filters'),
};

export const collaborationService = {
  getResearcher: (name: string) => api.get(`/collaboration/researcher/${name}`),
};

export const graphService = {
  getData: (limit: number) => api.get(`/graph/data?limit=${limit}`),
};
