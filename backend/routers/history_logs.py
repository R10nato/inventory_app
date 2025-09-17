import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime

from security import verify_hmac_signature, get_agent_secret, get_current_agent
from services.history_service import HistoryService
import models, schemas, database, crud

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
def get_db():
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

# ======================
# GET /history_logs/
# ======================
@router.get("/", response_model=schemas.PaginatedResponse[schemas.HistoryLog])
async def get_history_logs(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    device_id: Optional[int] = None,
    component: Optional[str] = None,
    change_type: Optional[schemas.ChangeType] = None,
    # severity removido - não é um campo de HistoryLog
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
    # current_agent: Dict[str, Any] = Depends(get_current_active_agent)  # Removido temporariamente para frontend
):
    """
    Retorna logs de histórico do sistema com suporte a paginação e filtros.
    """
    query = db.query(models.HistoryLog)

    if device_id:
        query = query.filter(models.HistoryLog.device_id == device_id)
    if component:
        query = query.filter(models.HistoryLog.component.ilike(f"%{component}%"))
    if change_type:
        query = query.filter(models.HistoryLog.change_type == change_type)
    # severity não é um campo de HistoryLog, apenas de Alert
    # if severity:
    #     query = query.filter(models.HistoryLog.severity == severity)
    if start_date:
        query = query.filter(models.HistoryLog.timestamp >= start_date)
    if end_date:
        end_date = end_date.replace(hour=23, minute=59, second=59)
        query = query.filter(models.HistoryLog.timestamp <= end_date)

    total = query.count()
    logs = query.order_by(models.HistoryLog.timestamp.desc()).offset(skip).limit(limit).all()

    return schemas.PaginatedResponse[schemas.HistoryLog](
        items=[schemas.HistoryLog.model_validate(log) for log in logs],
        total=total,
        skip=skip,
        limit=limit
    )

# ======================
# GET /history_logs/device/{device_id}
# ======================
@router.get("/device/{device_id}", response_model=schemas.PaginatedResponse[schemas.HistoryLog])
async def get_history_logs_for_device(
    device_id: int,
    request: Request,
    skip: int = 0,
    limit: int = 100,
    component: Optional[str] = None,
    change_type: Optional[schemas.ChangeType] = None,
    # severity removido - não é um campo de HistoryLog
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
    # current_agent: Dict[str, Any] = Depends(get_current_active_agent)  # Removido temporariamente para frontend
):
    """Retorna os logs de histórico para um dispositivo específico."""
    device = crud.get_device(db, device_id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Dispositivo {device_id} não encontrado.")

    query = db.query(models.HistoryLog).filter(models.HistoryLog.device_id == device_id)

    if component:
        query = query.filter(models.HistoryLog.component.ilike(f"%{component}%"))
    if change_type:
        query = query.filter(models.HistoryLog.change_type == change_type)
    # severity não é um campo de HistoryLog, apenas de Alert
    # if severity:
    #     query = query.filter(models.HistoryLog.severity == severity)
    if start_date:
        query = query.filter(models.HistoryLog.timestamp >= start_date)
    if end_date:
        end_date = end_date.replace(hour=23, minute=59, second=59)
        query = query.filter(models.HistoryLog.timestamp <= end_date)

    total = query.count()
    logs = query.order_by(models.HistoryLog.timestamp.desc()).offset(skip).limit(limit).all()

    return schemas.PaginatedResponse[schemas.HistoryLog](
        items=[schemas.HistoryLog.model_validate(log) for log in logs],
        total=total,
        skip=skip,
        limit=limit
    )

# ======================
# POST /history_logs/
# ======================
@router.post("/", response_model=schemas.BatchProcessResult, status_code=status.HTTP_201_CREATED)
async def create_history_logs_batch(
    request: Request,
    background_tasks: BackgroundTasks,
    batch: schemas.HistoryLogBatchCreate,
    db: Session = Depends(get_db),
    current_agent: Dict[str, Any] = Depends(get_current_active_agent)
):
    """Cria múltiplos logs de histórico em uma única requisição."""
    device = crud.get_device(db, device_id=batch.device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Dispositivo {batch.device_id} não encontrado.")

    if batch.signature:
        batch_data = batch.model_dump()
        signature = batch_data.get("signature")
        if signature:
            batch_data.pop("signature")
            if not verify_agent_signature(batch_data, signature, current_agent["agent_id"]):
                raise HTTPException(status_code=401, detail="Assinatura inválida ou expirada")

    batch_id = str(uuid.uuid4())
    logger.info(f"Recebido lote {batch_id} com {len(batch.logs)} logs para device {batch.device_id}")

    background_tasks.add_task(
        _process_history_batch_async,
        batch=batch,
        agent_id=current_agent["agent_id"],
        request_ip=request.client.host,
        batch_id=batch_id
    )

    return schemas.BatchProcessResult(
        success=True,
        logs_processed=len(batch.logs),
        snapshot_processed=batch.snapshot is not None,
        warnings=[],
        batch_id=batch_id,
        message="Lote recebido e em processamento"
    )

async def _process_history_batch_async(
    batch: schemas.HistoryLogBatchCreate,
    agent_id: str,
    request_ip: str,
    batch_id: str
):
    """Processa lote de logs em segundo plano."""
    db = database.SessionLocal()
    try:
        history_service = HistoryService(db)
        logs, snapshot = await history_service.process_history_batch(batch, agent_id, request_ip)
        logger.info(f"Lote {batch_id} processado: {len(logs)} logs, snapshot={'sim' if snapshot else 'não'}")
    except Exception as e:
        logger.error(f"Erro ao processar lote {batch_id}: {e}", exc_info=True)
    finally:
        db.close()

# ======================
# POST /history_logs/single
# ======================
@router.post("/single", response_model=schemas.HistoryLog, status_code=status.HTTP_201_CREATED)
async def create_single_history_log(
    request: Request,
    log: schemas.HistoryLogCreate,
    device_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_agent: Dict[str, Any] = Depends(get_current_active_agent)
):
    """Cria um único log de histórico manualmente para um dispositivo."""
    batch = schemas.HistoryLogBatchCreate(
        device_id=device_id,
        logs=[log],
        agent_version=current_agent.get("version")
    )
    return await create_history_logs_batch(request, background_tasks, batch, db, current_agent)
