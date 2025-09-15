import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

from pydantic import BaseModel, Field

from .. import models, schemas, database, crud
from ..security import verify_hmac_signature, get_agent_secret, get_current_agent
from ..services.history_service import HistoryService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/history_logs",
    tags=["History Logs"],
    responses={
        404: {"description": "Not found"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        422: {"description": "Validation Error"}
    },
)

# Dependência para obter sessão do DB
async def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependência para verificar autenticação
async def get_current_active_agent(
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Obtém o agente autenticado ou levanta uma exceção se não autenticado."""
    try:
        return await get_current_agent(request)
    except Exception as e:
        logger.error(f"Falha na autenticação: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado ou credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_agent_signature(data: Dict[str, Any], signature: str, agent_id: str) -> bool:
    """Verifica a assinatura HMAC dos dados do agente."""
    agent_secret = get_agent_secret(agent_id)
    if not agent_secret:
        logger.warning(f"Agente {agent_id} não encontrado ou sem chave secreta")
        return False
    
    return verify_hmac_signature(data, signature, agent_secret)


@router.get("/", response_model=schemas.PaginatedResponse[schemas.HistoryLog])
async def get_all_history_logs(
    request: Request,
    skip: int = 0, 
    limit: int = 100,
    device_id: Optional[int] = None,
    component: Optional[str] = None,
    change_type: Optional[schemas.ChangeType] = None,
    severity: Optional[schemas.SeverityLevel] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_agent: Dict[str, Any] = Depends(get_current_active_agent)
):
    """
    Retorna todos os logs de histórico do sistema com filtros opcionais.
    
    Parâmetros:
    - skip: Número de registros a pular (paginação)
    - limit: Número máximo de registros a retornar (tamanho da página)
    - device_id: Filtrar por ID do dispositivo
    - component: Filtrar por componente afetado
    - change_type: Filtrar por tipo de mudança
    - severity: Filtrar por nível de severidade
    - start_date: Data de início para filtrar logs
    - end_date: Data de término para filtrar logs
    """
    # Aplica filtros
    query = db.query(models.HistoryLog)
    
    if device_id is not None:
        query = query.filter(models.HistoryLog.device_id == device_id)
    if component is not None:
        query = query.filter(models.HistoryLog.component.ilike(f"%{component}%"))
    if change_type is not None:
        query = query.filter(models.HistoryLog.change_type == change_type)
    if severity is not None:
        query = query.filter(models.HistoryLog.severity == severity)
    if start_date is not None:
        query = query.filter(models.HistoryLog.timestamp >= start_date)
    if end_date is not None:
        # Adiciona 1 dia para incluir o dia inteiro
        end_date = end_date.replace(hour=23, minute=59, second=59)
        query = query.filter(models.HistoryLog.timestamp <= end_date)
    
    # Ordena por data mais recente primeiro
    query = query.order_by(models.HistoryLog.timestamp.desc())
    
    # Paginação
    total = query.count()
    logs = query.offset(skip).limit(limit).all()
    
    # Retorna resposta paginada
    return {
        "items": [schemas.HistoryLog.model_validate(log) for log in logs],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/device/{device_id}", response_model=schemas.PaginatedResponse[schemas.HistoryLog])
async def get_history_logs_for_device(
    device_id: int, 
    request: Request,
    skip: int = 0, 
    limit: int = 100,
    component: Optional[str] = None,
    change_type: Optional[schemas.ChangeType] = None,
    severity: Optional[schemas.SeverityLevel] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_agent: Dict[str, Any] = Depends(get_current_active_agent)
):
    """
    Retorna os logs de histórico para um dispositivo específico com filtros opcionais.
    
    Parâmetros:
    - device_id: ID do dispositivo
    - skip: Número de registros a pular (paginação)
    - limit: Número máximo de registros a retornar (tamanho da página)
    - component: Filtrar por componente afetado
    - change_type: Filtrar por tipo de mudança
    - severity: Filtrar por nível de severidade
    - start_date: Data de início para filtrar logs
    - end_date: Data de término para filtrar logs
    """
    # Verifica se o dispositivo existe
    device = crud.get_device(db, device_id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Dispositivo com ID {device_id} não encontrado.")
    
    # Aplica filtros
    query = db.query(models.HistoryLog).filter(models.HistoryLog.device_id == device_id)
    
    if component is not None:
        query = query.filter(models.HistoryLog.component.ilike(f"%{component}%"))
    if change_type is not None:
        query = query.filter(models.HistoryLog.change_type == change_type)
    if severity is not None:
        query = query.filter(models.HistoryLog.severity == severity)
    if start_date is not None:
        query = query.filter(models.HistoryLog.timestamp >= start_date)
    if end_date is not None:
        # Adiciona 1 dia para incluir o dia inteiro
        end_date = end_date.replace(hour=23, minute=59, second=59)
        query = query.filter(models.HistoryLog.timestamp <= end_date)
    
    # Ordena por data mais recente primeiro
    query = query.order_by(models.HistoryLog.timestamp.desc())
    
    # Paginação
    total = query.count()
    logs = query.offset(skip).limit(limit).all()
    
    # Retorna resposta paginada
    return {
        "items": [schemas.HistoryLog.model_validate(log) for log in logs],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post(
    "/", 
    response_model=schemas.BatchProcessResult,
    status_code=status.HTTP_201_CREATED,
    summary="Cria logs de histórico em lote",
    response_description="Resultado do processamento do lote de logs"
)
async def create_history_logs_batch(
    request: Request,
    background_tasks: BackgroundTasks,
    batch: schemas.HistoryLogBatchCreate,
    db: Session = Depends(get_db),
    current_agent: Dict[str, Any] = Depends(get_current_active_agent)
):
    """
    Cria múltiplos logs de histórico em uma única requisição, com suporte a snapshot.
    
    Este endpoint aceita um array de eventos de histórico e opcionalmente um snapshot
    completo do estado atual do dispositivo. Os dados são validados, normalizados e 
    processados de forma assíncrona para melhor desempenho.
    
    **Autenticação**: Requer token JWT válido no cabeçalho `Authorization: Bearer <token>`
    
    **Validação de Assinatura**: 
    - Se o parâmetro `signature` for fornecido, a assinatura HMAC-SHA256 dos dados
      será validada usando a chave secreta do agente.
    - O cabeçalho `X-Agent-ID` deve conter o ID do agente que está enviando os dados.
    
    **Notificações**:
    - Eventos com severidade MEDIUM ou superior geram notificações nos canais configurados.
    - Um snapshot do estado anterior é mantido para referência futura.
    
    **Retorno**:
    - `success`: Indica se o processamento foi iniciado com sucesso
    - `logs_processed`: Número de logs aceitos para processamento
    - `snapshot_processed`: Indica se um snapshot foi processado
    - `warnings`: Lista de avisos não fatais
    - `batch_id`: ID único para rastreamento do lote
    """
    # Verifica se o dispositivo existe
    device = crud.get_device(db, device_id=batch.device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispositivo com ID {batch.device_id} não encontrado."
        )
    
    # Verifica a assinatura se fornecida
    if batch.signature:
        # Remove a assinatura do payload para validação
        batch_data = batch.model_dump()
        signature = batch_data.pop('signature')
        
        if not verify_agent_signature(batch_data, signature, current_agent['agent_id']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Assinatura inválida ou expirada"
            )
    
    # Prepara os dados para processamento em segundo plano
    batch_id = str(uuid.uuid4())
    
    # Registra a solicitação para rastreamento
    logger.info(
        f"Processando lote {batch_id} com {len(batch.logs)} logs "
        f"para o dispositivo {batch.device_id}"
    )
    
    # Adiciona a tarefa em segundo plano
    background_tasks.add_task(
        _process_history_batch_async,
        db=db,
        batch=batch,
        agent_id=current_agent['agent_id'],
        request_ip=request.client.host,
        batch_id=batch_id
    )
    
    # Retorna resposta imediata
    return {
        "success": True,
        "logs_processed": len(batch.logs),
        "snapshot_processed": batch.snapshot is not None,
        "warnings": [],
        "batch_id": batch_id,
        "message": "Lote recebido e em processamento"
    }


async def _process_history_batch_async(
    db: Session,
    batch: schemas.HistoryLogBatchCreate,
    agent_id: str,
    request_ip: str,
    batch_id: str
):
    """
    Processa um lote de logs de histórico de forma assíncrona.
    
    Esta função é executada em segundo plano para não bloquear a resposta da API.
    """
    try:
        # Cria uma nova sessão do banco de dados para o processamento em segundo plano
        db = database.SessionLocal()
        history_service = HistoryService(db)
        
        # Processa o lote
        logs, snapshot = await history_service.process_history_batch(
            batch=batch,
            agent_id=agent_id,
            request_ip=request_ip
        )
        
        logger.info(
            f"Lote {batch_id} processado com sucesso: "
            f"{len(logs)} logs salvos, snapshot={'sim' if snapshot else 'não'}"
        )
        
    except Exception as e:
        logger.error(f"Erro ao processar lote {batch_id}: {str(e)}", exc_info=True)
    finally:
        # Garante que a sessão seja fechada corretamente
        db.close()


@router.post(
    "/single", 
    response_model=schemas.HistoryLog, 
    status_code=status.HTTP_201_CREATED,
    summary="Cria um único log de histórico",
    response_description="Log de histórico criado"
)
async def create_single_history_log(
    request: Request,
    log: schemas.HistoryLogCreate,
    device_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_agent: Dict[str, Any] = Depends(get_current_active_agent)
):
    """
    Cria um único log de histórico manualmente para um dispositivo.
    
    Este endpoint é um wrapper em torno do endpoint de lote para compatibilidade
    com clientes que não suportam o envio em lote.
    """
    # Cria um lote com um único log
    batch = schemas.HistoryLogBatchCreate(
        device_id=device_id,
        logs=[log],
        agent_version=current_agent.get('version')
    )
    
    # Chama o endpoint de lote
    return await create_history_logs_batch(
        request=request,
        background_tasks=background_tasks,
        batch=batch,
        db=db,
        current_agent=current_agent
    )
