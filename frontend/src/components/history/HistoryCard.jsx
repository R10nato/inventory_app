import React from 'react';
import { format, formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { FaArrowUp, FaArrowDown, FaExchangeAlt, FaExclamationTriangle, FaInfoCircle } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import './HistoryCard.css';

const getChangeIcon = (changeType) => {
  switch (changeType.toLowerCase()) {
    case 'adicionado':
      return <FaArrowUp className="icon added" />;
    case 'removido':
      return <FaArrowDown className="icon removed" />;
    case 'modificado':
      return <FaExchangeAlt className="icon modified" />;
    case 'erro':
      return <FaExclamationTriangle className="icon error" />;
    default:
      return <FaInfoCircle className="icon info" />;
  }
};

const getSeverityClass = (severity) => {
  switch (severity?.toLowerCase()) {
    case 'high':
      return 'severity-high';
    case 'medium':
      return 'severity-medium';
    case 'low':
      return 'severity-low';
    case 'critical':
      return 'severity-critical';
    default:
      return 'severity-info';
  }
};

const formatChangeValue = (value) => {
  if (value === null || value === undefined) return 'N/A';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
};

const HistoryCard = ({ log }) => {
  const navigate = useNavigate();
  const timestamp = new Date(log.timestamp);
  const timeAgo = formatDistanceToNow(timestamp, { addSuffix: true, locale: ptBR });
  const formattedTime = format(timestamp, 'HH:mm:ss');
  
  const handleCardClick = () => {
    navigate(`/history/${log.id}`);
  };

  return (
    <div 
      className={`history-card ${getSeverityClass(log.severity)}`}
      onClick={handleCardClick}
    >
      <div className="card-header">
        <div className="card-icon">
          {getChangeIcon(log.change_type)}
        </div>
        <div className="card-title">
          <h4>{log.change_description}</h4>
          <div className="card-meta">
            <span className="component">{log.component}</span>
            <span className="separator">•</span>
            <span className="time" title={format(timestamp, 'PPPp', { locale: ptBR })}>
              {timeAgo} ({formattedTime})
            </span>
            {log.agent_version && (
              <>
                <span className="separator">•</span>
                <span className="agent">v{log.agent_version}</span>
              </>
            )}
          </div>
        </div>
      </div>
      
      {(log.old_value !== undefined || log.new_value !== undefined) && (
        <div className="card-diff">
          <span className="old-value">{formatChangeValue(log.old_value)}</span>
          <span className="arrow">→</span>
          <span className="new-value">{formatChangeValue(log.new_value)}</span>
        </div>
      )}
      
      {log.evidence && (
        <div className="card-evidence">
          <span className="evidence-label">Evidência:</span>
          <pre className="evidence-content">
            {JSON.stringify(log.evidence, null, 2)}
          </pre>
        </div>
      )}
      
      <div className="card-actions">
        <button 
          className="btn btn-link"
          onClick={(e) => {
            e.stopPropagation();
            // TODO: Implementar ação de ver detalhes
          }}
        >
          Ver detalhes
        </button>
      </div>
    </div>
  );
};

export default HistoryCard;
