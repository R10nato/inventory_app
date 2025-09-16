"""
Serviço de notificações para alertas e eventos do sistema.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from sqlalchemy.orm import Session
import models
import schemas
import crud
from config import settings

logger = logging.getLogger(__name__)

class NotificationChannel(str, Enum):
    """Canais de notificação suportados."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    IN_APP = "in_app"
    TICKET = "ticket"

class NotificationService:
    """Serviço para gerenciar notificações de alertas e eventos."""
    
    def __init__(self, db: Session):
        self.db = db
        self.enabled_channels = self._load_enabled_channels()
    
    def _load_enabled_channels(self) -> List[NotificationChannel]:
        """Carrega os canais de notificação ativos a partir das configurações."""
        # TODO: Carregar do banco de dados/ambiente
        return [
            NotificationChannel.IN_APP,  # Sempre habilitado para notificações internas
            NotificationChannel.EMAIL if settings.EMAIL_ENABLED else None,
            NotificationChannel.SLACK if settings.SLACK_WEBHOOK_URL else None,
        ]
    
    async def send_notification(
        self,
        title: str,
        message: str,
        severity: schemas.SeverityLevel = schemas.SeverityLevel.INFO,
        device_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        channels: Optional[List[NotificationChannel]] = None
    ) -> bool:
        """
        Envia uma notificação através dos canais especificados.
        
        Args:
            title: Título da notificação
            message: Mensagem detalhada
            severity: Nível de severidade
            device_id: ID do dispositivo relacionado (opcional)
            context: Dados adicionais para a notificação
            channels: Lista de canais para enviar. Se None, usa os canais padrão
            
        Returns:
            bool: True se todas as notificações foram enviadas com sucesso
        """
        if channels is None:
            channels = self.enabled_channels
        
        # Cria o alerta no banco de dados
        alert = self._create_alert(
            title=title,
            message=message,
            severity=severity,
            device_id=device_id,
            context=context
        )
        
        # Envia para os canais configurados
        results = []
        
        if NotificationChannel.IN_APP in channels:
            # Já foi criado no banco, então marcamos como sucesso
            results.append(True)
        
        if NotificationChannel.EMAIL in channels:
            results.append(
                await self._send_email_notification(alert, context)
            )
            
        if NotificationChannel.SLACK in channels:
            results.append(
                await self._send_slack_notification(alert, context)
            )
            
        if NotificationChannel.WEBHOOK in channels:
            results.append(
                await self._send_webhook_notification(alert, context)
            )
            
        if NotificationChannel.TICKET in channels:
            results.append(
                await self._create_ticket(alert, context)
            )
        
        return all(results)
    
    def _create_alert(
        self,
        title: str,
        message: str,
        severity: schemas.SeverityLevel,
        device_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> models.Alert:
        """Cria um alerta no banco de dados."""
        alert_data = schemas.AlertCreate(
            title=title,
            message=message,
            alert_type=context.get("alert_type", "system") if context else "system",
            severity=severity,
            source=context.get("source", "inventory_api"),
            device_id=device_id,
            alert_metadata=context
        )
        
        return crud.create_alert(self.db, alert=alert_data)
    
    async def _send_email_notification(
        self,
        alert: models.Alert,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Envia notificação por e-mail."""
        # TODO: Implementar envio de e-mail real
        try:
            logger.info(f"[EMAIL] Enviando notificação para {settings.ADMIN_EMAIL}")
            logger.info(f"[EMAIL] Assunto: {alert.title}")
            logger.info(f"[EMAIL] Mensagem: {alert.message}")
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail: {str(e)}")
            return False
    
    async def _send_slack_notification(
        self,
        alert: models.Alert,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Envia notificação para o Slack."""
        try:
            # TODO: Implementar integração com Slack
            logger.info(f"[SLACK] Enviando notificação para o canal {settings.SLACK_CHANNEL}")
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar notificação para o Slack: {str(e)}")
            return False
    
    async def _send_webhook_notification(
        self,
        alert: models.Alert,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Envia notificação para um webhook configurado."""
        try:
            # TODO: Implementar chamada de webhook
            logger.info("[WEBHOOK] Disparando webhook de notificação")
            return True
        except Exception as e:
            logger.error(f"Erro ao chamar webhook: {str(e)}")
            return False
    
    async def _create_ticket(
        self,
        alert: models.Alert,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Cria um ticket em um sistema externo (ex: Jira, ServiceNow)."""
        try:
            # TODO: Implementar integração com sistema de tickets
            logger.info("[TICKET] Criando ticket para o alerta")
            return True
        except Exception as e:
            logger.error(f"Erro ao criar ticket: {str(e)}")
            return False
