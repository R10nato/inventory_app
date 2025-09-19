from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any
from database import get_db
import alert_service
from pydantic import BaseModel

router = APIRouter()

class MonitoringData(BaseModel):
    device_id: str = None
    cpu_usage: float = None
    ram_usage_percent: float = None
    disk_usage: list = None
    temperatures: list = None
    battery: dict = None
    network_stats: dict = None
    usb_devices: list = None
    timestamp: str = None

@router.post("/metrics")
async def receive_monitoring_data(
    data: MonitoringData,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Recebe dados de monitoramento do agent e verifica thresholds.
    
    Este endpoint é chamado pelo agent para enviar métricas em tempo real
    e verificar automaticamente contra os thresholds configurados.
    """
    try:
        # Converte os dados para dict para processamento
        metrics_data = data.dict(exclude_unset=True)
        
        # Busca o device_id numérico se foi enviado como string
        device_id = None
        if data.device_id:
            # Tenta converter para int, ou busca por identificador único
            try:
                device_id = int(data.device_id)
            except ValueError:
                # Se não for numérico, pode ser MAC address ou UUID
                from crud import get_device_by_identifier
                device = get_device_by_identifier(db, data.device_id)
                device_id = device.id if device else None
        
        # Executa verificação de thresholds em background
        background_tasks.add_task(
            alert_service.monitor_system_metrics,
            metrics_data,
            device_id
        )
        
        return {
            "status": "received",
            "device_id": device_id,
            "metrics_processed": len([k for k in metrics_data.keys() if k != 'device_id' and metrics_data[k] is not None])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar dados de monitoramento: {str(e)}"
        )

@router.post("/health-check")
async def health_check(
    device_id: str = None,
    db: Session = Depends(get_db)
):
    """
    Endpoint simples para heartbeat/health check do agent.
    
    Pode ser usado para verificar se o dispositivo está online
    e executar verificações básicas de thresholds.
    """
    try:
        device_id_num = None
        if device_id:
            try:
                device_id_num = int(device_id)
            except ValueError:
                from crud import get_device_by_identifier
                device = get_device_by_identifier(db, device_id)
                device_id_num = device.id if device else None
        
        return {
            "status": "healthy",
            "timestamp": "2025-01-01T00:00:00Z",  # Usar datetime.utcnow().isoformat()
            "device_id": device_id_num
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro no health check: {str(e)}"
        )
