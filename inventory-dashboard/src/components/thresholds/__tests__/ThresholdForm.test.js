import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ThresholdForm from '../src/components/thresholds/ThresholdForm';

// Mock do toast
jest.mock('react-toastify', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

// Mock da API
jest.mock('../src/lib/api/thresholds', () => ({
  thresholdsApi: {
    create: jest.fn(),
    update: jest.fn(),
  },
}));

const mockThresholdsApi = require('../src/lib/api/thresholds').thresholdsApi;

describe('ThresholdForm', () => {
  const mockOnClose = jest.fn();
  const mockOnSuccess = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Criação de Threshold', () => {
    test('renderiza formulário vazio para criação', () => {
      render(
        <ThresholdForm
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      expect(screen.getByText('Novo Threshold')).toBeInTheDocument();
      expect(screen.getByLabelText('Tipo de Métrica')).toBeInTheDocument();
      expect(screen.getByLabelText('Valor do Threshold')).toBeInTheDocument();
      expect(screen.getByLabelText('Condição')).toBeInTheDocument();
    });

    test('submete formulário com dados válidos', async () => {
      mockThresholdsApi.create.mockResolvedValue({ id: 1 });

      render(
        <ThresholdForm
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      // Preencher formulário
      fireEvent.change(screen.getByLabelText('Valor do Threshold'), {
        target: { value: '80' }
      });

      // Submeter
      fireEvent.click(screen.getByText('Criar'));

      await waitFor(() => {
        expect(mockThresholdsApi.create).toHaveBeenCalledWith({
          metric_type: '',
          threshold_value: 80,
          comparison: '>',
          is_active: true,
          device_id: null,
        });
        expect(mockOnSuccess).toHaveBeenCalled();
        expect(mockOnClose).toHaveBeenCalled();
      });
    });

    test('mostra erros de validação', async () => {
      render(
        <ThresholdForm
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      // Deixar valor vazio e tentar submeter
      fireEvent.click(screen.getByText('Criar'));

      await waitFor(() => {
        expect(screen.getByText('Valor do threshold é obrigatório')).toBeInTheDocument();
      });
    });
  });

  describe('Edição de Threshold', () => {
    const existingThreshold = {
      id: 1,
      metric_type: 'cpu',
      threshold_value: 75.0,
      comparison: '>',
      is_active: true,
      device_id: 1,
    };

    test('pré-preenche formulário com dados existentes', () => {
      render(
        <ThresholdForm
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          threshold={existingThreshold}
        />
      );

      expect(screen.getByText('Editar Threshold')).toBeInTheDocument();
      expect(screen.getByDisplayValue('75')).toBeInTheDocument();
    });

    test('atualiza threshold existente', async () => {
      mockThresholdsApi.update.mockResolvedValue(existingThreshold);

      render(
        <ThresholdForm
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          threshold={existingThreshold}
        />
      );

      // Alterar valor
      fireEvent.change(screen.getByLabelText('Valor do Threshold'), {
        target: { value: '85' }
      });

      // Submeter
      fireEvent.click(screen.getByText('Atualizar'));

      await waitFor(() => {
        expect(mockThresholdsApi.update).toHaveBeenCalledWith(1, {
          threshold_value: 85,
          device_id: 1,
        });
      });
    });
  });

  describe('Interação com Usuário', () => {
    test('fecha modal ao clicar em Cancelar', () => {
      render(
        <ThresholdForm
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      fireEvent.click(screen.getByText('Cancelar'));
      expect(mockOnClose).toHaveBeenCalled();
    });

    test('mostra estado de carregamento durante submissão', async () => {
      mockThresholdsApi.create.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({ id: 1 }), 100))
      );

      render(
        <ThresholdForm
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      fireEvent.change(screen.getByLabelText('Valor do Threshold'), {
        target: { value: '80' }
      });

      fireEvent.click(screen.getByText('Criar'));

      expect(screen.getByText('Salvando...')).toBeInTheDocument();

      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalled();
      });
    });
  });
});
