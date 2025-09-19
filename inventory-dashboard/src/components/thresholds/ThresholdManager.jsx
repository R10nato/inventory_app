// src/components/thresholds/ThresholdManager.jsx
import React, { useState } from 'react';
import PropTypes from 'prop-types';
import ThresholdList from './ThresholdList';
import ThresholdForm from './ThresholdForm';

const ThresholdManager = ({ deviceId = null }) => {
  const [showForm, setShowForm] = useState(false);
  const [editingThreshold, setEditingThreshold] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleCreate = () => {
    setEditingThreshold(null);
    setShowForm(true);
  };

  const handleEdit = (threshold) => {
    setEditingThreshold(threshold);
    setShowForm(true);
  };

  const handleCloseForm = () => {
    setShowForm(false);
    setEditingThreshold(null);
  };

  const handleSuccess = () => {
    setRefreshKey(prev => prev + 1); // Force refresh of the list
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">
            Gerenciamento de Thresholds
          </h2>
          <p className="text-muted-foreground">
            Configure limites de alerta para métricas do sistema
            {deviceId && ` - Dispositivo ID: ${deviceId}`}
          </p>
        </div>
      </div>

      <ThresholdList
        key={refreshKey}
        onEdit={handleEdit}
        onCreate={handleCreate}
        deviceId={deviceId}
      />

      <ThresholdForm
        isOpen={showForm}
        onClose={handleCloseForm}
        threshold={editingThreshold}
        deviceId={deviceId}
        onSuccess={handleSuccess}
      />
    </div>
  );
};

ThresholdManager.propTypes = {
  deviceId: PropTypes.number,
};

export default ThresholdManager;
