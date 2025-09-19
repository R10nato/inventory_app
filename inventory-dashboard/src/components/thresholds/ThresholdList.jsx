// src/components/thresholds/ThresholdList.jsx
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { thresholdsApi } from '@/lib/api/thresholds';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Switch } from '@/components/ui/switch';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { toast } from 'react-toastify';
import { Edit, Trash2, TestTube, Plus } from 'lucide-react';

const METRIC_LABELS = {
  cpu: 'CPU',
  ram: 'Memória RAM',
  disk: 'Disco',
  temperature: 'Temperatura',
  battery: 'Bateria',
  usb: 'USB',
  network: 'Rede',
};

const SEVERITY_COLORS = {
  low: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
};

const ThresholdList = ({ onEdit, onCreate, deviceId = null }) => {
  const [thresholds, setThresholds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    loadThresholds();
  }, [deviceId]);

  const loadThresholds = async () => {
    try {
      setLoading(true);
      const params = {};
      if (deviceId) {
        params.device_id = deviceId;
      }
      const data = await thresholdsApi.getAll(params);
      setThresholds(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      toast.error('Erro ao carregar thresholds');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleActive = async (threshold) => {
    try {
      await thresholdsApi.update(threshold.id, {
        is_active: !threshold.is_active
      });
      await loadThresholds();
      toast.success(`Threshold ${!threshold.is_active ? 'ativado' : 'desativado'}`);
    } catch (err) {
      toast.error('Erro ao alterar status do threshold');
    }
  };

  const handleDelete = async (id) => {
    try {
      setDeletingId(id);
      await thresholdsApi.delete(id);
      await loadThresholds();
      toast.success('Threshold removido com sucesso');
    } catch (err) {
      toast.error('Erro ao remover threshold');
    } finally {
      setDeletingId(null);
    }
  };

  const handleTest = async (threshold) => {
    const testValue = prompt(`Digite um valor para testar o threshold (${threshold.metric_type.toUpperCase()} ${threshold.comparison} ${threshold.threshold_value}):`);
    if (testValue === null) return;

    try {
      const result = await thresholdsApi.test(threshold.id, parseFloat(testValue));
      toast[result.violated ? 'warning' : 'success'](
        `Teste: ${testValue} ${result.condition} = ${result.violated ? 'VIOLADO' : 'OK'}`
      );
    } catch (err) {
      toast.error('Erro ao testar threshold');
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2">Carregando thresholds...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-red-600">
            <p>Erro ao carregar thresholds: {error}</p>
            <Button onClick={loadThresholds} className="mt-2">
              Tentar novamente
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Thresholds de Alerta</CardTitle>
        <Button onClick={onCreate} size="sm">
          <Plus className="h-4 w-4 mr-2" />
          Novo Threshold
        </Button>
      </CardHeader>
      <CardContent>
        {thresholds.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>Nenhum threshold configurado</p>
            <Button onClick={onCreate} variant="outline" className="mt-2">
              Criar primeiro threshold
            </Button>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Métrica</TableHead>
                <TableHead>Condição</TableHead>
                <TableHead>Ativo</TableHead>
                <TableHead>Criado</TableHead>
                <TableHead>Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {thresholds.map((threshold) => (
                <TableRow key={threshold.id}>
                  <TableCell className="font-medium">
                    {METRIC_LABELS[threshold.metric_type] || threshold.metric_type.toUpperCase()}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {threshold.threshold_value} {threshold.comparison}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Switch
                      checked={threshold.is_active}
                      onCheckedChange={() => handleToggleActive(threshold)}
                    />
                  </TableCell>
                  <TableCell>
                    {new Date(threshold.created_at).toLocaleDateString('pt-BR')}
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleTest(threshold)}
                      >
                        <TestTube className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onEdit(threshold)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button variant="outline" size="sm" disabled={deletingId === threshold.id}>
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Remover Threshold</AlertDialogTitle>
                            <AlertDialogDescription>
                              Tem certeza que deseja remover este threshold?
                              Esta ação não pode ser desfeita.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancelar</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => handleDelete(threshold.id)}
                              className="bg-red-600 hover:bg-red-700"
                            >
                              Remover
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
};

ThresholdList.propTypes = {
  onEdit: PropTypes.func.isRequired,
  onCreate: PropTypes.func.isRequired,
  deviceId: PropTypes.number,
};

export default ThresholdList;
