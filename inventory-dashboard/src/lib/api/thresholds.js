// src/lib/api/thresholds.js
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const thresholdsApi = {
  // Buscar todos os thresholds
  async getAll(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = `${API_BASE_URL}/alert-thresholds/${queryString ? '?' + queryString : ''}`;

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Erro ao buscar thresholds: ${response.statusText}`);
    }
    return response.json();
  },

  // Buscar threshold por ID
  async getById(id) {
    const response = await fetch(`${API_BASE_URL}/alert-thresholds/${id}`);
    if (!response.ok) {
      throw new Error(`Erro ao buscar threshold: ${response.statusText}`);
    }
    return response.json();
  },

  // Buscar thresholds ativos para um dispositivo
  async getActiveForDevice(deviceId, metricType = null) {
    const params = new URLSearchParams();
    if (metricType) params.append('metric_type', metricType);

    const response = await fetch(`${API_BASE_URL}/alert-thresholds/device/${deviceId}/active?${params}`);
    if (!response.ok) {
      throw new Error(`Erro ao buscar thresholds ativos: ${response.statusText}`);
    }
    return response.json();
  },

  // Criar novo threshold
  async create(thresholdData) {
    const response = await fetch(`${API_BASE_URL}/alert-thresholds/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(thresholdData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Erro ao criar threshold: ${response.statusText}`);
    }

    return response.json();
  },

  // Atualizar threshold
  async update(id, thresholdData) {
    const response = await fetch(`${API_BASE_URL}/alert-thresholds/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(thresholdData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Erro ao atualizar threshold: ${response.statusText}`);
    }

    return response.json();
  },

  // Deletar threshold
  async delete(id) {
    const response = await fetch(`${API_BASE_URL}/alert-thresholds/${id}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Erro ao deletar threshold: ${response.statusText}`);
    }

    return response.json();
  },

  // Testar threshold
  async test(id, testValue) {
    const response = await fetch(`${API_BASE_URL}/alert-thresholds/${id}/test?test_value=${testValue}`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Erro ao testar threshold: ${response.statusText}`);
    }

    return response.json();
  },
};

export default thresholdsApi;
