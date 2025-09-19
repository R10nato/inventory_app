import { useState, useEffect, useRef } from 'react';
import { toast } from 'react-toastify';

export const useWebSocket = (url = 'ws://localhost:8000/ws') => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const ws = useRef(null);

  useEffect(() => {
    connect();

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [url]);

  const connect = () => {
    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        console.log('WebSocket conectado');
        setIsConnected(true);
        toast.success('Conectado ao servidor de notificações', {
          position: 'bottom-right',
          autoClose: 2000,
          hideProgressBar: false,
        });
      };

      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          setLastMessage(message);
          handleMessage(message);
        } catch (error) {
          console.error('Erro ao processar mensagem WebSocket:', error);
        }
      };

      ws.current.onclose = () => {
        console.log('WebSocket desconectado');
        setIsConnected(false);
        toast.warning('Desconectado do servidor de notificações', {
          position: 'bottom-right',
          autoClose: 3000,
        });

        // Tenta reconectar após 5 segundos
        setTimeout(() => {
          if (!isConnected) {
            connect();
          }
        }, 5000);
      };

      ws.current.onerror = (error) => {
        console.error('Erro no WebSocket:', error);
        setIsConnected(false);
      };

    } catch (error) {
      console.error('Erro ao conectar WebSocket:', error);
    }
  };

  const handleMessage = (message) => {
    switch (message.type) {
      case 'alert':
        handleAlertMessage(message.data);
        break;
      case 'device_update':
        handleDeviceUpdate(message.data);
        break;
      case 'threshold_alert':
        handleThresholdAlert(message.data);
        break;
      default:
        console.log('Tipo de mensagem desconhecido:', message.type);
    }
  };

  const handleAlertMessage = (alertData) => {
    const severityMap = {
      'low': 'info',
      'medium': 'warning',
      'high': 'error',
      'critical': 'error'
    };

    const toastType = severityMap[alertData.severity] || 'info';

    toast[toastType](`${alertData.title}: ${alertData.message}`, {
      position: 'top-right',
      autoClose: alertData.severity === 'critical' ? false : 8000,
      hideProgressBar: false,
      closeOnClick: true,
      pauseOnHover: true,
      draggable: true,
      progress: undefined,
    });
  };

  const handleDeviceUpdate = (updateData) => {
    console.log('Atualização de dispositivo:', updateData);
    // Pode emitir um evento customizado para atualizar componentes
    window.dispatchEvent(new CustomEvent('deviceUpdate', { detail: updateData }));
  };

  const handleThresholdAlert = (thresholdData) => {
    toast.warning(`Threshold violado: ${thresholdData.metric_type.toUpperCase()} = ${thresholdData.current_value}`, {
      position: 'top-right',
      autoClose: 10000,
      hideProgressBar: false,
    });
  };

  const sendMessage = (message) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    }
  };

  return {
    isConnected,
    lastMessage,
    sendMessage
  };
};

export default useWebSocket;
