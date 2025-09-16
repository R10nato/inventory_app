import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import HistoryCard from './HistoryCard';
import HistoryFilters from './HistoryFilters';
import { fetchDeviceHistory } from '../../lib/api';

const TimelineView = ({ deviceId, initialLogs = [], loading: externalLoading }) => {
  const [historyLogs, setHistoryLogs] = useState(initialLogs);
  const [loading, setLoading] = useState(!initialLogs?.length);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    component: '',
    changeType: '',
    startDate: null,
    endDate: null,
    severity: ''
  });

  useEffect(() => {
    // Se initialLogs foi fornecido, usa esses logs iniciais
    if (initialLogs?.length) {
      setHistoryLogs(initialLogs);
      setLoading(false);
    }
  }, [initialLogs]);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        setLoading(true);
        const data = await fetchDeviceHistory(deviceId, filters);
        setHistoryLogs(data.items || []);
        setError(null);
      } catch (err) {
        setError('Erro ao carregar o histórico. Tente novamente mais tarde.');
        console.error('Erro ao carregar histórico:', err);
      } finally {
        setLoading(false);
      }
    };

    // Só carrega via API se houver um deviceId e não estiver usando os logs iniciais
    if (deviceId && !initialLogs?.length) {
      loadHistory();
    }
  }, [deviceId, filters]);

  const handleFilterChange = (newFilters) => {
    setFilters(prev => ({
      ...prev,
      ...newFilters
    }));
  };

  // Agrupar logs por data
  const groupedLogs = historyLogs.reduce((acc, log) => {
    const date = format(new Date(log.timestamp), 'PPP', { locale: ptBR });
    if (!acc[date]) {
      acc[date] = [];
    }
    acc[date].push(log);
    return acc;
  }, {});

  const isLoading = externalLoading !== undefined ? externalLoading : loading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-2">Carregando histórico...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-500 p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="mb-4">
        <HistoryFilters 
          filters={filters} 
          onFilterChange={handleFilterChange} 
        />
      </div>
      
      <div className="space-y-8">
        {Object.entries(groupedLogs).length > 0 ? (
          Object.entries(groupedLogs).map(([date, logs]) => (
            <div key={date} className="space-y-4">
              <div className="flex items-center">
                <div className="flex-grow border-t border-gray-300"></div>
                <div className="px-4 font-semibold text-gray-700">{date}</div>
                <div className="flex-grow border-t border-gray-300"></div>
              </div>
              <div className="space-y-4">
                {logs.map(log => (
                  <HistoryCard key={log.id} log={log} />
                ))}
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-8 text-gray-500">
            Nenhum registro de histórico encontrado para os filtros selecionados.
          </div>
        )}
      </div>
    </div>
  );
};

export default TimelineView;
