"""
Serviço para gerenciamento de histórico de mudanças e snapshots.
"""
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

from sqlalchemy.orm import Session

from .. import models, schemas, crud
from .normalization_service import NormalizationService
from .notification_service import NotificationService, NotificationChannel

logger = logging.getLogger(__name__)

class HistoryService:
    """Serviço para gerenciamento de histórico de mudanças."""
    
    def __init__(self, db: Session):
        self.db = db
        self.normalizer = NormalizationService()
        self.notification_service = NotificationService(db)
    
    async def process_history_batch(
        self, 
        batch: schemas.HistoryLogBatchCreate,
        agent_id: Optional[str] = None,
        request_ip: Optional[str] = None
    ) -> Tuple[List[models.HistoryLog], Optional[Dict[str, Any]]]:
        """
        Processa um lote de eventos de histórico, opcionalmente com um snapshot.
        
        Args:
            batch: Dados do lote contendo eventos e opcionalmente um snapshot
            agent_id: ID do agente que está enviando os dados
            request_ip: Endereço IP da requisição
            
        Returns:
            Tuple contendo a lista de logs criados e o snapshot processado (se houver)
        """
        # Verifica se o dispositivo existe
        device = crud.get_device(self.db, device_id=batch.device_id)
        if not device:
            raise ValueError(f"Dispositivo com ID {batch.device_id} não encontrado")
        
        # Normaliza os dados do lote
        normalized_logs = []
        for log in batch.logs:
            # Adiciona metadados de auditoria
            log_dict = log.model_dump()
            log_dict['agent_version'] = batch.agent_version or agent_id or 'unknown'
            log_dict['source'] = log_dict.get('source') or 'agent'
            log_dict['ip_address'] = request_ip
            
            # Normaliza valores
            if log_dict.get('old_value'):
                log_dict['old_value'] = self.normalizer.normalize_device_data(log_dict['old_value'])
            if log_dict.get('new_value'):
                log_dict['new_value'] = self.normalizer.normalize_device_data(log_dict['new_value'])
            
            # Calcula o hash da mudança para detecção de duplicatas
            log_dict['change_hash'] = self._calculate_change_hash(log_dict)
            normalized_logs.append(log_dict)
        
        # Remove duplicatas baseado no hash
        unique_logs = self._deduplicate_logs(normalized_logs)
        
        # Salva os logs no banco de dados
        saved_logs = []
        for log_data in unique_logs:
            log = crud.create_history_log(
                self.db, 
                device_id=batch.device_id, 
                log=schemas.HistoryLogCreate(**log_data)
            )
            saved_logs.append(log)
            
            # Dispara notificações para mudanças importantes
            await self._process_notifications(log)
        
        # Processa o snapshot se fornecido
        snapshot = None
        if batch.snapshot:
            snapshot = await self._process_snapshot(
                device_id=batch.device_id,
                snapshot_data=batch.snapshot,
                agent_version=batch.agent_version,
                agent_id=agent_id
            )
        
        return saved_logs, snapshot
    
    def _calculate_change_hash(self, log_data: Dict[str, Any]) -> str:
        """Calcula um hash único para uma mudança baseado em seus atributos-chave."""
        # Usa apenas os campos relevantes para detecção de duplicatas
        hash_data = {
            'device_id': log_data.get('device_id'),
            'component': log_data.get('component'),
            'change_type': log_data.get('change_type'),
            'path': log_data.get('path'),
            'old_value': log_data.get('old_value'),
            'new_value': log_data.get('new_value'),
            'timestamp': log_data.get('timestamp')
        }
        
        # Converte para string JSON e calcula o hash
        hash_str = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_str.encode('utf-8')).hexdigest()
    
    def _deduplicate_logs(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove logs duplicados baseado no hash da mudança."""
        seen_hashes = set()
        unique_logs = []
        
        for log in logs:
            if log['change_hash'] not in seen_hashes:
                seen_hashes.add(log['change_hash'])
                unique_logs.append(log)
        
        return unique_logs
    
    async def _process_notifications(self, log: models.HistoryLog):
        """Processa notificações para um log de histórico."""
        # Determina a severidade da notificação com base no tipo de mudança
        severity = log.severity
        
        # Configurações de notificação baseadas na severidade
        notification_config = {
            schemas.SeverityLevel.INFO: {
                'channels': [NotificationChannel.IN_APP],
                'notify_admin': False
            },
            schemas.SeverityLevel.LOW: {
                'channels': [NotificationChannel.IN_APP, NotificationChannel.EMAIL],
                'notify_admin': False
            },
            schemas.SeverityLevel.MEDIUM: {
                'channels': [
                    NotificationChannel.IN_APP, 
                    NotificationChannel.EMAIL,
                    NotificationChannel.SLACK
                ],
                'notify_admin': True
            },
            schemas.SeverityLevel.HIGH: {
                'channels': [
                    NotificationChannel.IN_APP, 
                    NotificationChannel.EMAIL,
                    NotificationChannel.SLACK,
                    NotificationChannel.TICKET
                ],
                'notify_admin': True
            },
            schemas.SeverityLevel.CRITICAL: {
                'channels': [
                    NotificationChannel.IN_APP, 
                    NotificationChannel.EMAIL,
                    NotificationChannel.SLACK,
                    NotificationChannel.TICKET,
                    NotificationChannel.WEBHOOK
                ],
                'notify_admin': True
            }
        }
        
        config = notification_config.get(severity, notification_config[schemas.SeverityLevel.INFO])
        
        # Prepara o contexto da notificação
        context = {
            'log_id': log.id,
            'device_id': log.device_id,
            'component': log.component,
            'change_type': log.change_type,
            'severity': severity,
            'timestamp': log.timestamp.isoformat(),
            'source': log.source or 'system',
            'alert_type': 'inventory_change',
            'details': {
                'path': log.path,
                'description': log.change_description
            }
        }
        
        # Envia a notificação
        title = f"Alteração de Inventário: {log.component} - {log.change_type}"
        message = (
            f"Dispositivo ID: {log.device_id}\n"
            f"Componente: {log.component}\n"
            f"Tipo de mudança: {log.change_type}\n"
            f"Descrição: {log.change_description}\n"
            f"Severidade: {severity}"
        )
        
        await self.notification_service.send_notification(
            title=title,
            message=message,
            severity=severity,
            device_id=log.device_id,
            context=context,
            channels=config['channels']
        )
    
    async def _process_snapshot(
        self, 
        device_id: int, 
        snapshot_data: Dict[str, Any],
        agent_version: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Processa um snapshot de estado do dispositivo."""
        # Normaliza os dados do snapshot
        normalized_data = self.normalizer.normalize_device_data(snapshot_data)
        
        # Calcula o hash do snapshot
        snapshot_hash = self._calculate_snapshot_hash(normalized_data)
        
        # Verifica se já existe um snapshot idêntico
        existing_snapshot = crud.get_snapshot_by_hash(self.db, snapshot_hash)
        if existing_snapshot:
            logger.info(f"Snapshot duplicado ignorado para o dispositivo {device_id}")
            return None
        
        # Cria o registro do snapshot
        snapshot = crud.create_snapshot(
            self.db,
            snapshot=schemas.SnapshotCreate(
                hash_sha256=snapshot_hash,
                device_id=str(device_id),
                agent_id=agent_id,
                agent_version=agent_version,
                data=normalized_data,
                device_count=1  # Apenas um dispositivo por snapshot
            )
        )
        
        logger.info(f"Novo snapshot salvo para o dispositivo {device_id} com hash {snapshot_hash[:8]}...")
        return snapshot
    
    def _calculate_snapshot_hash(self, snapshot_data: Dict[str, Any]) -> str:
        """Calcula o hash SHA-256 de um snapshot."""
        # Remove campos que não devem afetar o hash
        data_to_hash = snapshot_data.copy()
        for field in ['last_seen', 'updated_at', 'collection_timestamp']:
            if field in data_to_hash:
                data_to_hash[field] = None
        
        # Ordena as chaves para garantir consistência
        sorted_data = json.dumps(data_to_hash, sort_keys=True)
        
        # Calcula o hash
        return hashlib.sha256(sorted_data.encode('utf-8')).hexdigest()
