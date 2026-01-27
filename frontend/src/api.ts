import axios from 'axios';
import { AnalysisResponse, SQLResponse, UIConfig } from './types';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getUIConfig = async (): Promise<UIConfig> => {
  const response = await api.get('/config/init');
  return response.data;
};

export const analyzeQuery = async (query: string): Promise<AnalysisResponse> => {
  const response = await api.post('/chat/analyze', { query });
  return response.data;
};

export const getDimensionValues = async (kpi: string, dimension_type: string): Promise<string[]> => {
  const response = await api.post('/config/dimension', { kpi, dimension_type });
  return response.data.values;
};

export const generateAndExecuteSQL = async (kpi: string, time_range: string, scope: string[]): Promise<SQLResponse> => {
  const response = await api.post('/chat/sql', { kpi, time_range, scope });
  return response.data;
};

export const downloadDetail = async (kpi: string, time_range: string, scope: string[]): Promise<void> => {
  const response = await api.post('/chat/download', { kpi, time_range, scope }, { responseType: 'blob' });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `${kpi}_details.xlsx`);
  document.body.appendChild(link);
  link.click();
  link.remove();
};

export default api;
