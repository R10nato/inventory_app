import React from 'react';
import { format, formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { FaArrowUp, FaArrowDown, FaExchangeAlt, FaExclamationTriangle, FaInfoCircle, FaExternalLinkAlt } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';

const getChangeIcon = (changeType) => {
  const iconClass = 'h-4 w-4 mr-2';
  
  switch (changeType?.toLowerCase()) {
    case 'adicionado':
      return <FaArrowUp className={`${iconClass} text-green-600`} />;
    case 'removido':
      return <FaArrowDown className={`${iconClass} text-red-600`} />;
    case 'modificado':
      return <FaExchangeAlt className={`${iconClass} text-blue-600`} />;
    case 'erro':
      return <FaExclamationTriangle className={`${iconClass} text-yellow-600`} />;
    default:
      return <FaInfoCircle className={`${iconClass} text-gray-600`} />;
  }
};

const getSeverityClass = (severity) => {
  switch (severity?.toLowerCase()) {
    case 'high':
      return 'bg-red-100 text-red-800 border-red-200';
    case 'medium':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'low':
      return 'bg-blue-100 text-blue-800 border-blue-200';
    case 'critical':
      return 'bg-red-900 text-white border-red-800';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200';
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
  const severityClass = getSeverityClass(log.severity);
  
  const handleCardClick = () => {
    navigate(`/history/${log.id}`);
  };

  return (
    <Card 
      className={`mb-4 overflow-hidden transition-all hover:shadow-md cursor-pointer border-l-4 ${severityClass.includes('border-') ? '' : 'border-l-blue-500'}`}
      onClick={handleCardClick}
    >
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3">
            <div className="mt-0.5">
              {getChangeIcon(log.change_type)}
            </div>
            <div>
              <h3 className="font-medium text-gray-900">
                {log.component || 'Componente não especificado'}
              </h3>
              <div className="flex items-center text-sm text-gray-500 mt-1">
                <span title={timeAgo}>
                  {formattedTime}
                </span>
                {log.agent_name && (
                  <span className="mx-2">•</span>
                )}
                {log.agent_name && (
                  <span>Agente: {log.agent_name} (v{log.agent_version || '?'})</span>
                )}
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className={severityClass}>
              {log.change_type || 'Alteração'}
            </Badge>
            <FaExternalLinkAlt className="h-3 w-3 text-gray-400" />
          </div>
        </div>
        
        <div className="mt-3 text-sm text-gray-700">
          <p>{log.description || 'Sem descrição fornecida'}</p>
          
          {log.evidence && (
            <div className="mt-2 p-2 bg-gray-50 rounded text-xs font-mono overflow-x-auto">
              <pre>{JSON.stringify(log.evidence, null, 2)}</pre>
            </div>
          )}
        </div>
        
        <div className="mt-3 flex justify-end">
          <button 
            className="text-sm text-blue-600 hover:text-blue-800"
            onClick={(e) => {
              e.stopPropagation();
              // TODO: Implementar ação de ver detalhes
            }}
          >
            Ver detalhes completos
          </button>
        </div>
      </div>
    </Card>
  );
};

export default HistoryCard;
