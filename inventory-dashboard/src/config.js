// frontend/src/config.js
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  devices: `${API_BASE_URL}/devices`,
  alerts: `${API_BASE_URL}/alerts`,
  history: `${API_BASE_URL}/history_logs`,
  snapshots: `${API_BASE_URL}/snapshots`,
  docs: `${API_BASE_URL}/docs`
};

// Configurações de desenvolvimento
export const DEV_CONFIG = {
  enableMockData: false, // false = usa dados reais do backend
  apiTimeout: 10000,
  retryAttempts: 3,
  enableDebugLogs: import.meta.env.DEV
};

export default {
  API_BASE_URL,
  API_ENDPOINTS,
  DEV_CONFIG
};
