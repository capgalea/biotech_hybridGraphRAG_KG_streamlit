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
  getStats: () => api.get('/analytics/stats'),
  getSchema: () => api.get('/analytics/schema'),
  getTopInstitutions: (limit: number = 10) => api.get(`/analytics/institutions?limit=${limit}`),
};

export const collaborationService = {
  getResearcher: (name: string) => api.get(`/collaboration/researcher/${name}`),
};

export const graphService = {
  getData: (limit: number) => api.get(`/graph/data?limit=${limit}`),
};
