import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import HistoryCard from './HistoryCard';
import HistoryFilters from './HistoryFilters';
import { fetchDeviceHistory } from '../../services/api';
import './TimelineView.css';

const TimelineView = ({ deviceId }) => {
  const [historyLogs, setHistoryLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    component: '',
    changeType: '',
    startDate: null,
    endDate: null,
    severity: ''
  });

  useEffect(() => {
    const loadHistory = async () => {
      try {
        setLoading(true);
        const data = await fetchDeviceHistory(deviceId, filters);
        setHistoryLogs(data.items || []);
      } catch (err) {
        setError('Erro ao carregar o histórico. Tente novamente mais tarde.');
        console.error('Erro ao carregar histórico:', err);
      } finally {
        setLoading(false);
      }
    };

    if (deviceId) {
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

  if (loading && historyLogs.length === 0) {
    return <div className="loading">Carregando histórico...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="timeline-container">
      <div className="timeline-filters">
        <HistoryFilters 
          filters={filters} 
          onFilterChange={handleFilterChange} 
        />
      </div>
      
      <div className="timeline">
        {Object.entries(groupedLogs).length > 0 ? (
          Object.entries(groupedLogs).map(([date, logs]) => (
            <div key={date} className="timeline-day">
              <div className="timeline-date">
                <div className="timeline-date-line"></div>
                <div className="timeline-date-label">{date}</div>
                <div className="timeline-date-line"></div>
              </div>
              <div className="timeline-events">
                {logs.map(log => (
                  <HistoryCard key={log.id} log={log} />
                ))}
              </div>
            </div>
          ))
        ) : (
          <div className="no-results">
            Nenhum registro de histórico encontrado para os filtros selecionados.
          </div>
        )}
      </div>
    </div>
  );
};

export default TimelineView;
