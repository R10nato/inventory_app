# Sistema de Monitoramento e Alertas - Documentação

## Visão Geral

Este sistema implementa um conjunto completo de funcionalidades de monitoramento e alertas para inventário de dispositivos, incluindo thresholds configuráveis, alertas em tempo real, monitoramento de USB e heartbeat.

## Funcionalidades Implementadas

### 1. Thresholds Configuráveis ✅

**Arquivos Criados/Modificados:**
- `backend/models.py` - Modelo `AlertThreshold`
- `backend/alert_threshold_schemas.py` - Schemas Pydantic
- `backend/crud_alert_thresholds.py` - Operações CRUD
- `backend/routers/alert_thresholds.py` - Rotas FastAPI
- `backend/alembic/versions/add_alert_thresholds.py` - Migração banco

**Funcionalidades:**
- Criar, editar, excluir thresholds
- Suporte a métricas: CPU, RAM, Disco, Temperatura, Bateria, USB
- Operadores: >, <, ==, >=, <=
- Thresholds globais (device_id = null) e específicos por dispositivo
- API REST completa

**Exemplo de Uso:**
```bash
# Criar threshold
POST /api/alert-thresholds/
{
  "metric_type": "cpu",
  "threshold_value": 80,
  "comparison": ">",
  "device_id": 1
}

# Listar thresholds
GET /api/alert-thresholds/

# Testar threshold
POST /api/alert-thresholds/1/test?test_value=85
```

### 2. Alertas em Tempo Real ✅

**Arquivos Criados/Modificados:**
- `backend/websocket_manager.py` - Gerenciador WebSocket
- `backend/main.py` - Endpoint WebSocket
- `backend/alert_service.py` - Integração WebSocket
- `inventory-dashboard/src/hooks/useWebSocket.js` - Hook React
- `inventory-dashboard/src/App.jsx` - Integração Toast

**Funcionalidades:**
- Conexão WebSocket automática
- Notificações toast em tempo real
- Reconexão automática
- Tipos de mensagens: alertas, atualizações de dispositivo, violações de threshold

**Arquitetura:**
```
Frontend (React) ← WebSocket → Backend (FastAPI)
       ↓                           ↓
    Toast UI               Alert Service
```

### 3. Monitoramento de USB ✅

**Arquivos Criados:**
- `backend/usb_monitor.py` - Monitor USB
- `backend/main.py` - Integração startup

**Funcionalidades:**
- Detecção automática de conexão/desconexão USB
- Suporte Windows (WMI) e Linux (lsusb)
- Avaliação de risco do dispositivo
- Alertas automáticos com severidade baseada no risco
- Callbacks customizáveis

**Avaliação de Risco:**
- **Baixo**: Teclados, mouses, webcams
- **Médio**: Pendrives, HDs externos
- **Alto**: Dispositivos desconhecidos

## API Endpoints

### Thresholds
```
POST   /api/alert-thresholds/          # Criar threshold
GET    /api/alert-thresholds/          # Listar thresholds
GET    /api/alert-thresholds/{id}      # Obter threshold
PUT    /api/alert-thresholds/{id}      # Atualizar threshold
DELETE /api/alert-thresholds/{id}      # Remover threshold
POST   /api/alert-thresholds/{id}/test # Testar threshold
GET    /api/alert-thresholds/device/{device_id}/active # Thresholds ativos
```

### WebSocket
```
WebSocket: ws://localhost:8000/ws          # Conexão geral
WebSocket: ws://localhost:8000/ws/{user_id} # Conexão específica
```

## Estrutura de Dados

### AlertThreshold
```python
{
    "id": 1,
    "device_id": null,  # null = global
    "metric_type": "cpu",
    "threshold_value": 80.0,
    "comparison": ">",
    "is_active": true,
    "created_at": "2025-09-19T14:30:00Z",
    "updated_at": "2025-09-19T14:30:00Z"
}
```

### Mensagem WebSocket
```json
{
  "type": "alert",
  "data": {
    "id": 1,
    "title": "Alerta de CPU",
    "message": "Uso de CPU em 85%",
    "severity": "high",
    "created_at": "2025-09-19T14:30:00Z"
  },
  "timestamp": "2025-09-19T14:30:00Z"
}
```

## Integração com Sistema Existente

### Alert Service
- Função `check_thresholds_and_create_alerts()` integrada
- Alertas automáticos quando thresholds são violados
- WebSocket broadcasting automático

### Database
- Nova tabela `alert_thresholds`
- Índices otimizados para performance
- Compatibilidade com schema existente

## Testes Realizados

### Thresholds
```python
✅ Criação de threshold
✅ Validação de dados
✅ CRUD completo
✅ Migração banco aplicada
```

### WebSocket
```python
✅ Conexão estabelecida
✅ Mensagens recebidas
✅ Toast notifications
✅ Reconexão automática
```

### USB Monitor
```python
✅ Detecção Windows (WMI)
✅ Detecção Linux (lsusb)
✅ Alertas automáticos
✅ Avaliação de risco
```

## Próximos Passos

### Melhorias Sugeridas
1. **Interface Web** para gerenciar thresholds
2. **Dashboard** de alertas ativos
3. **Configurações** de notificação por usuário
4. **Histórico** de violações de threshold
5. **Testes de Performance** com múltiplos clientes WebSocket

### Monitoramento Adicional
1. **Rede**: Latência, uso de banda
2. **Serviços**: Status de aplicações críticas
3. **Logs**: Análise de logs do sistema
4. **Eventos**: Monitoramento de eventos Windows/Linux

## Dependências

### Backend
```
fastapi==0.104.1
websockets==12.0
pywin32==306 (Windows)
wmi==1.5.1 (Windows)
```

### Frontend
```
react-toastify==9.1.3
```

## Como Usar

### 1. Iniciar Backend
```bash
cd backend
call venv\Scripts\activate
python main.py
```

### 2. Iniciar Frontend
```bash
cd inventory-dashboard
npm run dev
```

### 3. Criar Thresholds
```bash
# CPU > 80%
curl -X POST http://localhost:8000/api/alert-thresholds/ \
  -H "Content-Type: application/json" \
  -d '{"metric_type":"cpu","threshold_value":80,"comparison":">"}'

# RAM > 90%
curl -X POST http://localhost:8000/api/alert-thresholds/ \
  -H "Content-Type: application/json" \
  -d '{"metric_type":"ram","threshold_value":90,"comparison":">"}'
```

### 4. Monitorar
- Alertas aparecem automaticamente via toast
- Thresholds são verificados durante coleta de dados
- Dispositivos USB são monitorados continuamente

---

**Status**: ✅ Implementado e Testado
**Data**: 19 de Setembro de 2025
**Versão**: 1.0.0
