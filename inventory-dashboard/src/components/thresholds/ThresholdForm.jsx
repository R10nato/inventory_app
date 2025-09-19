// src/components/thresholds/ThresholdForm.jsx
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { thresholdsApi } from '@/lib/api/thresholds';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { toast } from 'react-toastify';

const METRIC_OPTIONS = [
  { value: 'cpu', label: 'CPU (%)' },
  { value: 'ram', label: 'Memória RAM (%)' },
  { value: 'disk', label: 'Disco (%)' },
  { value: 'temperature', label: 'Temperatura (°C)' },
  { value: 'battery', label: 'Bateria (%)' },
  { value: 'usb', label: 'USB (conexões)' },
  { value: 'network', label: 'Rede (Mbps)' },
];

const COMPARISON_OPTIONS = [
  { value: '>', label: 'Maior que (>)' },
  { value: '<', label: 'Menor que (<)' },
  { value: '==', label: 'Igual a (==)' },
  { value: '>=', label: 'Maior ou igual (>=)' },
  { value: '<=', label: 'Menor ou igual (<=)' },
];

const ThresholdForm = ({ isOpen, onClose, threshold, deviceId = null, onSuccess }) => {
  const [formData, setFormData] = useState({
    metric_type: '',
    threshold_value: '',
    comparison: '>',
    is_active: true,
    device_id: deviceId,
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (threshold) {
      setFormData({
        metric_type: threshold.metric_type,
        threshold_value: threshold.threshold_value.toString(),
        comparison: threshold.comparison,
        is_active: threshold.is_active,
        device_id: threshold.device_id,
      });
    } else {
      setFormData({
        metric_type: '',
        threshold_value: '',
        comparison: '>',
        is_active: true,
        device_id: deviceId,
      });
    }
    setErrors({});
  }, [threshold, deviceId, isOpen]);

  const validateForm = () => {
    const newErrors = {};

    if (!formData.metric_type) {
      newErrors.metric_type = 'Tipo de métrica é obrigatório';
    }

    if (!formData.threshold_value) {
      newErrors.threshold_value = 'Valor do threshold é obrigatório';
    } else {
      const value = parseFloat(formData.threshold_value);
      if (isNaN(value)) {
        newErrors.threshold_value = 'Valor deve ser um número válido';
      } else if (value < 0) {
        newErrors.threshold_value = 'Valor deve ser positivo';
      }
    }

    if (!formData.comparison) {
      newErrors.comparison = 'Operador de comparação é obrigatório';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      const submitData = {
        ...formData,
        threshold_value: parseFloat(formData.threshold_value),
        device_id: formData.device_id || null,
      };

      if (threshold) {
        await thresholdsApi.update(threshold.id, submitData);
        toast.success('Threshold atualizado com sucesso');
      } else {
        await thresholdsApi.create(submitData);
        toast.success('Threshold criado com sucesso');
      }

      onSuccess();
      onClose();
    } catch (err) {
      toast.error(err.message || 'Erro ao salvar threshold');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {threshold ? 'Editar Threshold' : 'Novo Threshold'}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Tipo de Métrica */}
          <div className="space-y-2">
            <Label htmlFor="metric_type">Tipo de Métrica</Label>
            <Select
              value={formData.metric_type}
              onValueChange={(value) => handleInputChange('metric_type', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Selecione o tipo de métrica" />
              </SelectTrigger>
              <SelectContent>
                {METRIC_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.metric_type && (
              <p className="text-sm text-red-600">{errors.metric_type}</p>
            )}
          </div>

          {/* Valor do Threshold */}
          <div className="space-y-2">
            <Label htmlFor="threshold_value">Valor do Threshold</Label>
            <Input
              id="threshold_value"
              type="number"
              step="0.1"
              min="0"
              value={formData.threshold_value}
              onChange={(e) => handleInputChange('threshold_value', e.target.value)}
              placeholder="Ex: 80.5"
            />
            {errors.threshold_value && (
              <p className="text-sm text-red-600">{errors.threshold_value}</p>
            )}
          </div>

          {/* Operador de Comparação */}
          <div className="space-y-2">
            <Label htmlFor="comparison">Condição</Label>
            <Select
              value={formData.comparison}
              onValueChange={(value) => handleInputChange('comparison', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Selecione a condição" />
              </SelectTrigger>
              <SelectContent>
                {COMPARISON_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.comparison && (
              <p className="text-sm text-red-600">{errors.comparison}</p>
            )}
          </div>

          {/* Ativo/Inativo */}
          <div className="flex items-center space-x-2">
            <Switch
              id="is_active"
              checked={formData.is_active}
              onCheckedChange={(checked) => handleInputChange('is_active', checked)}
            />
            <Label htmlFor="is_active">Threshold ativo</Label>
          </div>

          {/* Device ID (opcional) */}
          {!deviceId && (
            <div className="space-y-2">
              <Label htmlFor="device_id">ID do Dispositivo (opcional)</Label>
              <Input
                id="device_id"
                type="number"
                min="1"
                value={formData.device_id || ''}
                onChange={(e) => handleInputChange('device_id', e.target.value ? parseInt(e.target.value) : null)}
                placeholder="Deixe vazio para threshold global"
              />
              <p className="text-xs text-gray-500">
                Se vazio, o threshold será aplicado a todos os dispositivos
              </p>
            </div>
          )}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Salvando...' : (threshold ? 'Atualizar' : 'Criar')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

ThresholdForm.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  threshold: PropTypes.object,
  deviceId: PropTypes.number,
  onSuccess: PropTypes.func.isRequired,
};

export default ThresholdForm;
