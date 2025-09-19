import React from 'react';

const TimelineViewSimple = ({ deviceId, initialLogs = [], loading }) => {
  console.log('TimelineViewSimple rendered with:', { deviceId, initialLogs, loading });
  
  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-2">Carregando histórico...</span>
      </div>
    );
  }

  if (!initialLogs || initialLogs.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>Nenhum registro de histórico encontrado.</p>
        <p className="text-xs mt-2">Device ID: {deviceId}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Histórico de Alterações</h3>
      <div className="space-y-2">
        {initialLogs.map((log, index) => (
          <div key={log.id || index} className="p-4 border rounded-lg bg-gray-50">
            <div className="flex justify-between items-start">
              <div>
                <p className="font-medium">{log.component || 'Sistema'}</p>
                <p className="text-sm text-gray-600">{log.change_description || 'Sem descrição'}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Tipo: {log.change_type || 'N/A'} | ID: {log.id || 'N/A'}
                </p>
              </div>
              <span className="text-xs text-gray-500">
                {log.timestamp ? new Date(log.timestamp).toLocaleString('pt-BR') : 'N/A'}
              </span>
            </div>
            {log.details_before && (
              <div className="mt-2 text-xs">
                <span className="font-medium">Antes:</span> {log.details_before}
              </div>
            )}
            {log.details_after && (
              <div className="text-xs">
                <span className="font-medium">Depois:</span> {log.details_after}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default TimelineViewSimple;
