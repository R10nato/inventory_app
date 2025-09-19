from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from models import AlertThreshold
import alert_threshold_schemas as schemas

def get_threshold(db: Session, threshold_id: int):
    """Busca um threshold específico por ID"""
    return db.query(AlertThreshold).filter(AlertThreshold.id == threshold_id).first()

def get_thresholds(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    device_id: Optional[int] = None,
    metric_type: Optional[str] = None,
    is_active: bool = True
):
    """Busca todos os thresholds com filtros opcionais"""
    query = db.query(AlertThreshold)

    if device_id is not None:
        query = query.filter(AlertThreshold.device_id == device_id)
    if metric_type:
        query = query.filter(AlertThreshold.metric_type == metric_type)
    if is_active is not None:
        query = query.filter(AlertThreshold.is_active == is_active)

    return query.offset(skip).limit(limit).all()

def get_active_thresholds_for_device(db: Session, device_id: int, metric_type: Optional[str] = None):
    """Busca thresholds ativos para um dispositivo específico ou globais"""
    query = db.query(AlertThreshold).filter(
        and_(
            AlertThreshold.is_active == True,
            or_(
                AlertThreshold.device_id == device_id,
                AlertThreshold.device_id.is_(None)
            )
        )
    )

    if metric_type:
        query = query.filter(AlertThreshold.metric_type == metric_type)

    return query.all()

def create_threshold(db: Session, threshold_data: dict):
    """Cria um novo threshold"""
    db_threshold = AlertThreshold(**threshold_data)
    db.add(db_threshold)
    db.commit()
    db.refresh(db_threshold)
    return db_threshold

def update_threshold(db: Session, threshold_id: int, threshold_data: dict):
    """Atualiza um threshold existente"""
    db_threshold = get_threshold(db, threshold_id)
    if not db_threshold:
        return None

    for key, value in threshold_data.items():
        setattr(db_threshold, key, value)

    db.commit()
    db.refresh(db_threshold)
    return db_threshold

def delete_threshold(db: Session, threshold_id: int):
    """Remove um threshold"""
    db_threshold = get_threshold(db, threshold_id)
    if db_threshold:
        db.delete(db_threshold)
        db.commit()
    return db_threshold

def check_threshold_violation(db: Session, metric_type: str, current_value: float, device_id: int):
    """
    Verifica se algum threshold foi violado para a métrica e dispositivo
    Retorna lista de thresholds violados
    """
    thresholds = get_active_thresholds_for_device(db, device_id, metric_type)

    violations = []
    for threshold in thresholds:
        # Avalia a condição do threshold
        try:
            condition = f"{current_value} {threshold.comparison} {threshold.threshold_value}"
            if eval(condition):
                violations.append({
                    "threshold_id": threshold.id,
                    "metric_type": threshold.metric_type,
                    "threshold_value": threshold.threshold_value,
                    "comparison": threshold.comparison,
                    "current_value": current_value,
                    "device_id": threshold.device_id
                })
        except Exception as e:
            print(f"Erro ao avaliar threshold {threshold.id}: {e}")
            continue

    return violations
