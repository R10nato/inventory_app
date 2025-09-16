import React, { useState, useEffect } from 'react';
import { format, subDays } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import './HistoryFilters.css';

// Opções de filtro
const COMPONENT_OPTIONS = [
  { value: '', label: 'Todos os componentes' },
  { value: 'cpu', label: 'CPU' },
  { value: 'memory', label: 'Memória' },
  { value: 'disk', label: 'Disco' },
  { value: 'network', label: 'Rede' },
  { value: 'os', label: 'Sistema Operacional' },
  { value: 'software', label: 'Software' },
  { value: 'hardware', label: 'Hardware' },
];

const CHANGE_TYPE_OPTIONS = [
  { value: '', label: 'Todos os tipos' },
  { value: 'adicionado', label: 'Adicionado' },
  { value: 'removido', label: 'Removido' },
  { value: 'modificado', label: 'Modificado' },
  { value: 'erro', label: 'Erro' },
];

const SEVERITY_OPTIONS = [
  { value: '', label: 'Todas as severidades' },
  { value: 'info', label: 'Informativo' },
  { value: 'low', label: 'Baixa' },
  { value: 'medium', label: 'Média' },
  { value: 'high', label: 'Alta' },
  { value: 'critical', label: 'Crítica' },
];

const HistoryFilters = ({ filters, onFilterChange }) => {
  const [localFilters, setLocalFilters] = useState({
    component: '',
    changeType: '',
    startDate: subDays(new Date(), 30),
    endDate: new Date(),
    severity: ''
  });

  // Sincroniza os filtros locais com os props
  useEffect(() => {
    setLocalFilters(prev => ({
      ...prev,
      ...filters
    }));
  }, [filters]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    updateFilters({ [name]: value });
  };

  const handleDateChange = (date, field) => {
    updateFilters({ [field]: date });
  };

  const updateFilters = (updates) => {
    const newFilters = { ...localFilters, ...updates };
    setLocalFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleClearFilters = () => {
    const resetFilters = {
      component: '',
      changeType: '',
      startDate: subDays(new Date(), 30),
      endDate: new Date(),
      severity: ''
    };
    setLocalFilters(resetFilters);
    onFilterChange(resetFilters);
  };

  return (
    <div className="history-filters">
      <div className="filter-group">
        <label htmlFor="component">Componente</label>
        <select
          id="component"
          name="component"
          value={localFilters.component}
          onChange={handleInputChange}
          className="form-select"
        >
          {COMPONENT_OPTIONS.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="changeType">Tipo de Mudança</label>
        <select
          id="changeType"
          name="changeType"
          value={localFilters.changeType}
          onChange={handleInputChange}
          className="form-select"
        >
          {CHANGE_TYPE_OPTIONS.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="severity">Severidade</label>
        <select
          id="severity"
          name="severity"
          value={localFilters.severity}
          onChange={handleInputChange}
          className="form-select"
        >
          {SEVERITY_OPTIONS.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group date-range">
        <label>Período</label>
        <div className="date-pickers">
          <DatePicker
            selected={localFilters.startDate}
            onChange={(date) => handleDateChange(date, 'startDate')}
            selectsStart
            startDate={localFilters.startDate}
            endDate={localFilters.endDate}
            maxDate={localFilters.endDate}
            className="form-control"
            dateFormat="dd/MM/yyyy"
            locale={ptBR}
          />
          <span className="date-separator">até</span>
          <DatePicker
            selected={localFilters.endDate}
            onChange={(date) => handleDateChange(date, 'endDate')}
            selectsEnd
            startDate={localFilters.startDate}
            endDate={localFilters.endDate}
            minDate={localFilters.startDate}
            maxDate={new Date()}
            className="form-control"
            dateFormat="dd/MM/yyyy"
            locale={ptBR}
          />
        </div>
      </div>

      <div className="filter-actions">
        <button 
          type="button" 
          className="btn btn-outline-secondary"
          onClick={handleClearFilters}
        >
          Limpar Filtros
        </button>
      </div>
    </div>
  );
};

export default HistoryFilters;
