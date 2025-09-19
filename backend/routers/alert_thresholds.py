from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
import crud_alert_thresholds as crud
import alert_threshold_schemas as schemas

router = APIRouter()

@router.post("/", response_model=schemas.AlertThresholdInDB)
def create_threshold(
    threshold: schemas.AlertThresholdCreate,
    db: Session = Depends(get_db)
):
    """
    Cria um novo threshold de alerta.

    - **device_id**: ID do dispositivo (opcional, null para thresholds globais)
    - **metric_type**: Tipo da métrica (cpu, ram, disk, etc.)
    - **threshold_value**: Valor do threshold
    - **comparison**: Operador de comparação (>, <, ==, >=, <=)
    - **is_active**: Se o threshold está ativo (padrão: True)
    """
    return crud.create_threshold(db=db, threshold_data=threshold.dict())

@router.get("/", response_model=List[schemas.AlertThresholdInDB])
def read_thresholds(
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    device_id: Optional[int] = Query(None, description="Filtrar por ID do dispositivo"),
    metric_type: Optional[str] = Query(None, description="Filtrar por tipo de métrica"),
    is_active: bool = Query(True, description="Filtrar por status ativo"),
    db: Session = Depends(get_db)
):
    """
    Lista todos os thresholds com filtros opcionais.

    - **skip**: Número de registros para pular (paginação)
    - **limit**: Número máximo de registros (paginação)
    - **device_id**: Filtrar por dispositivo específico
    - **metric_type**: Filtrar por tipo de métrica
    - **is_active**: Filtrar por status ativo
    """
    return crud.get_thresholds(
        db,
        skip=skip,
        limit=limit,
        device_id=device_id,
        metric_type=metric_type,
        is_active=is_active
    )

@router.get("/{threshold_id}", response_model=schemas.AlertThresholdInDB)
def read_threshold(
    threshold_id: int,
    db: Session = Depends(get_db)
):
    """
    Busca um threshold específico por ID.

    - **threshold_id**: ID do threshold
    """
    db_threshold = crud.get_threshold(db, threshold_id=threshold_id)
    if db_threshold is None:
        raise HTTPException(status_code=404, detail="Threshold não encontrado")
    return db_threshold

@router.put("/{threshold_id}", response_model=schemas.AlertThresholdInDB)
def update_threshold(
    threshold_id: int,
    threshold: schemas.AlertThresholdUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza um threshold existente.

    - **threshold_id**: ID do threshold a ser atualizado
    - **threshold**: Dados para atualização (apenas campos fornecidos serão atualizados)
    """
    db_threshold = crud.update_threshold(
        db, threshold_id=threshold_id, threshold_data=threshold.dict(exclude_unset=True)
    )
    if db_threshold is None:
        raise HTTPException(status_code=404, detail="Threshold não encontrado")
    return db_threshold

@router.delete("/{threshold_id}", response_model=schemas.AlertThresholdInDB)
def delete_threshold(
    threshold_id: int,
    db: Session = Depends(get_db)
):
    """
    Remove um threshold.

    - **threshold_id**: ID do threshold a ser removido
    """
    db_threshold = crud.delete_threshold(db, threshold_id=threshold_id)
    if db_threshold is None:
        raise HTTPException(status_code=404, detail="Threshold não encontrado")
    return db_threshold

@router.post("/{threshold_id}/test", response_model=dict)
def test_threshold(
    threshold_id: int,
    test_value: float = Query(..., description="Valor para testar contra o threshold"),
    db: Session = Depends(get_db)
):
    """
    Testa se um valor viola um threshold específico.

    - **threshold_id**: ID do threshold
    - **test_value**: Valor para testar
    - **returns**: Resultado do teste (violated: true/false, details: detalhes da avaliação)
    """
    threshold = crud.get_threshold(db, threshold_id=threshold_id)
    if threshold is None:
        raise HTTPException(status_code=404, detail="Threshold não encontrado")

    try:
        condition = f"{test_value} {threshold.comparison} {threshold.threshold_value}"
        violated = eval(condition)

        return {
            "threshold_id": threshold.id,
            "metric_type": threshold.metric_type,
            "threshold_value": threshold.threshold_value,
            "comparison": threshold.comparison,
            "test_value": test_value,
            "violated": violated,
            "condition": condition
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao avaliar threshold: {str(e)}")

@router.get("/device/{device_id}/active", response_model=List[schemas.AlertThresholdInDB])
def get_active_thresholds_for_device(
    device_id: int,
    metric_type: Optional[str] = Query(None, description="Filtrar por tipo de métrica"),
    db: Session = Depends(get_db)
):
    """
    Busca todos os thresholds ativos para um dispositivo (incluindo globais).

    - **device_id**: ID do dispositivo
    - **metric_type**: Filtrar por tipo de métrica (opcional)
    """
    return crud.get_active_thresholds_for_device(db, device_id, metric_type)
