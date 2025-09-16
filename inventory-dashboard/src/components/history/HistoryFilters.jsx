import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import { subDays } from "date-fns";
import { ptBR } from "date-fns/locale";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// Opções de filtro
const COMPONENT_OPTIONS = [
  { value: "", label: "Todos os componentes" },
  { value: "cpu", label: "CPU" },
  { value: "memory", label: "Memória" },
  { value: "disk", label: "Disco" },
  { value: "network", label: "Rede" },
  { value: "os", label: "Sistema Operacional" },
  { value: "software", label: "Software" },
  { value: "hardware", label: "Hardware" },
];

const CHANGE_TYPE_OPTIONS = [
  { value: "", label: "Todos os tipos" },
  { value: "adicionado", label: "Adicionado" },
  { value: "removido", label: "Removido" },
  { value: "modificado", label: "Modificado" },
  { value: "erro", label: "Erro" },
];

const SEVERITY_OPTIONS = [
  { value: "", label: "Todas as severidades" },
  { value: "info", label: "Informativo" },
  { value: "low", label: "Baixa" },
  { value: "medium", label: "Média" },
  { value: "high", label: "Alta" },
  { value: "critical", label: "Crítica" },
];

const HistoryFilters = ({ filters, onFilterChange }) => {
  const [localFilters, setLocalFilters] = useState({
    component: "",
    changeType: "",
    startDate: subDays(new Date(), 30),
    endDate: new Date(),
    severity: "",
  });

  // Sincroniza os filtros recebidos via props
  useEffect(() => {
    if (filters) {
      setLocalFilters((prev) => ({
        ...prev,
        ...filters,
      }));
    }
  }, [filters]);

  // Atualiza valores dos selects e inputs
  const handleInputChange = (name, value) => {
    setLocalFilters((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Atualiza as datas garantindo consistência
  const handleDateChange = (date, field) => {
    if (!date) return;
    setLocalFilters((prev) => {
      let updated = { ...prev, [field]: date };
      if (field === "startDate" && date > prev.endDate) {
        updated.endDate = date;
      }
      if (field === "endDate" && date < prev.startDate) {
        updated.startDate = date;
      }
      return updated;
    });
  };

  // Aplica os filtros
  const handleSubmit = (e) => {
    e.preventDefault();
    onFilterChange?.(localFilters);
  };

  // Reseta os filtros
  const handleClear = () => {
    const clearedFilters = {
      component: "",
      changeType: "",
      startDate: subDays(new Date(), 30),
      endDate: new Date(),
      severity: "",
    };
    setLocalFilters(clearedFilters);
    onFilterChange?.(clearedFilters);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white p-4 rounded-lg shadow-sm border border-gray-200"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 items-end">
        {/* Filtro por Componente */}
        <div className="space-y-1">
          <Label htmlFor="component">Componente</Label>
          <Select
            value={localFilters.component}
            onValueChange={(value) => handleInputChange("component", value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Selecione um componente" />
            </SelectTrigger>
            <SelectContent>
              {COMPONENT_OPTIONS.map(({ value, label }) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Tipo de Mudança */}
        <div className="space-y-1">
          <Label htmlFor="changeType">Tipo de Mudança</Label>
          <Select
            value={localFilters.changeType}
            onValueChange={(value) => handleInputChange("changeType", value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Selecione um tipo" />
            </SelectTrigger>
            <SelectContent>
              {CHANGE_TYPE_OPTIONS.map(({ value, label }) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Severidade */}
        <div className="space-y-1">
          <Label htmlFor="severity">Severidade</Label>
          <Select
            value={localFilters.severity}
            onValueChange={(value) => handleInputChange("severity", value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Todas as severidades" />
            </SelectTrigger>
            <SelectContent>
              {SEVERITY_OPTIONS.map(({ value, label }) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Período (Datas) */}
        <div className="space-y-1">
          <Label>Período</Label>
          <div className="flex items-center space-x-2">
            <DatePicker
              selected={localFilters.startDate}
              onChange={(date) => handleDateChange(date, "startDate")}
              selectsStart
              startDate={localFilters.startDate}
              endDate={localFilters.endDate}
              maxDate={localFilters.endDate}
              locale={ptBR}
              dateFormat="dd/MM/yyyy"
              aria-label="Data inicial"
              className="flex h-9 w-full rounded-md border px-3 py-1 text-sm shadow-sm"
              placeholderText="Data inicial"
            />
            <span className="text-gray-500 text-sm">até</span>
            <DatePicker
              selected={localFilters.endDate}
              onChange={(date) => handleDateChange(date, "endDate")}
              selectsEnd
              startDate={localFilters.startDate}
              endDate={localFilters.endDate}
              minDate={localFilters.startDate}
              maxDate={new Date()}
              locale={ptBR}
              dateFormat="dd/MM/yyyy"
              aria-label="Data final"
              className="flex h-9 w-full rounded-md border px-3 py-1 text-sm shadow-sm"
              placeholderText="Data final"
            />
          </div>
        </div>

        {/* Botões */}
        <div className="flex space-x-2">
          <Button
            type="button"
            variant="outline"
            onClick={handleClear}
            className="flex-1"
          >
            Limpar
          </Button>
          <Button type="submit" className="flex-1 bg-blue-600 hover:bg-blue-700">
            Aplicar
          </Button>
        </div>
      </div>
    </form>
  );
};

HistoryFilters.propTypes = {
  filters: PropTypes.object,
  onFilterChange: PropTypes.func,
};

export default HistoryFilters;
