import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

/**
 * Busca o histórico de alterações de um dispositivo
 * @param {number} deviceId - ID do dispositivo
 * @param {Object} filters - Filtros para a busca
 * @param {string} [filters.component] - Componente específico para filtrar
 * @param {string} [filters.changeType] - Tipo de mudança para filtrar
 * @param {Date} [filters.startDate] - Data de início para filtrar
 * @param {Date} [filters.endDate] - Data de término para filtrar
 * @param {string} [filters.severity] - Nível de severidade para filtrar
 * @returns {Promise<Object>} - Dados do histórico paginados
 */
export const fetchDeviceHistory = async (deviceId, filters = {}) => {
  try {
    const params = new URLSearchParams();
    
    // Adiciona os filtros aos parâmetros da requisição
    if (filters.component) params.append('component', filters.component);
    if (filters.changeType) params.append('change_type', filters.changeType);
    if (filters.severity) params.append('severity', filters.severity);
    
    // Formata as datas para o formato ISO
    if (filters.startDate) {
      params.append('start_date', filters.startDate.toISOString());
    }
    
    if (filters.endDate) {
      params.append('end_date', filters.endDate.toISOString());
    }
    
    const response = await axios.get(
      `${API_BASE_URL}/history_logs/device/${deviceId}`, 
      { params }
    );
    
    return response.data;
  } catch (error) {
    console.error('Erro ao buscar histórico do dispositivo:', error);
    throw error;
  }
};

/**
 * Busca os detalhes de um log de histórico específico
 * @param {number} logId - ID do log de histórico
 * @returns {Promise<Object>} - Detalhes do log de histórico
 */
export const fetchHistoryLog = async (logId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/history_logs/${logId}`);
    return response.data;
  } catch (error) {
    console.error('Erro ao buscar detalhes do log:', error);
    throw error;
  }
};

/**
 * Busca snapshots antes/depois de um evento de histórico
 * @param {number} logId - ID do log de histórico
 * @returns {Promise<Object>} - Objeto com snapshots antes e depois
 */
export const fetchSnapshotsForLog = async (logId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/history_logs/${logId}/snapshots`);
    return response.data;
  } catch (error) {
    console.error('Erro ao buscar snapshots do log:', error);
    throw error;
  }
};

// Configuração global do axios para incluir o token JWT
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);
