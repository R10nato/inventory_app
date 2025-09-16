from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

import models, schemas, database, crud

router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"],
    responses={404: {"description": "Not found"}},
)

# Dependency para obter sessão do DB
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[schemas.Alert])
def get_all_alerts(
    skip: int = 0, 
    limit: int = 100,
    unread_only: bool = Query(False, description="Apenas alertas não lidos"),
    unresolved_only: bool = Query(False, description="Apenas alertas não resolvidos"),
    db: Session = Depends(get_db)
):
    """
    Retorna todos os alertas do sistema com filtros opcionais.
    """
    alerts = crud.get_alerts(db, skip=skip, limit=limit, unread_only=unread_only, unresolved_only=unresolved_only)
    return [schemas.Alert.model_validate(alert) for alert in alerts]


@router.get("/device/{device_id}", response_model=List[schemas.Alert])
def get_alerts_for_device(device_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retorna todos os alertas para um dispositivo específico.
    """
    alerts = crud.get_alerts_by_device(db, device_id=device_id, skip=skip, limit=limit)
    return [schemas.Alert.model_validate(alert) for alert in alerts]


@router.get("/stats")
def get_alert_stats(db: Session = Depends(get_db)):
    """
    Retorna estatísticas dos alertas.
    """
    total_alerts = len(crud.get_alerts(db, limit=10000))
    unread_alerts = len(crud.get_alerts(db, limit=10000, unread_only=True))
    unresolved_alerts = len(crud.get_alerts(db, limit=10000, unresolved_only=True))
    
    # Contar por severidade
    all_alerts = crud.get_alerts(db, limit=10000)
    severity_counts = {}
    type_counts = {}
    
    for alert in all_alerts:
        severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1
        type_counts[alert.alert_type] = type_counts.get(alert.alert_type, 0) + 1
    
    return {
        "total": total_alerts,
        "unread": unread_alerts,
        "unresolved": unresolved_alerts,
        "by_severity": severity_counts,
        "by_type": type_counts
    }


@router.get("/{alert_id}", response_model=schemas.Alert)
def get_alert_by_id(alert_id: int, db: Session = Depends(get_db)):
    """
    Retorna um alerta específico pelo ID.
    """
    alert = crud.get_alert(db, alert_id=alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta não encontrado.")
    return schemas.Alert.model_validate(alert)


@router.post("/", response_model=schemas.Alert, status_code=status.HTTP_201_CREATED)
def create_new_alert(alert: schemas.AlertCreate, db: Session = Depends(get_db)):
    """
    Cria um novo alerta.
    """
    created_alert = crud.create_alert(db, alert=alert)
    return schemas.Alert.model_validate(created_alert)


@router.patch("/{alert_id}", response_model=schemas.Alert)
def update_alert(alert_id: int, alert_update: schemas.AlertUpdate, db: Session = Depends(get_db)):
    """
    Atualiza um alerta existente (marcar como lido/resolvido).
    """
    updated_alert = crud.update_alert(db, alert_id=alert_id, alert_update=alert_update)
    if not updated_alert:
        raise HTTPException(status_code=404, detail="Alerta não encontrado.")
    return schemas.Alert.model_validate(updated_alert)


@router.post("/mark-all-read", response_model=dict)
def mark_all_alerts_as_read(db: Session = Depends(get_db)):
    """Marcar todos os alertas como lidos"""
    try:
        updated_count = crud.mark_all_alerts_as_read(db)
        return {"message": f"{updated_count} alertas marcados como lidos"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao marcar alertas como lidos: {str(e)}")


@router.get("/stats", response_model=dict)
def get_alert_stats(db: Session = Depends(get_db)):
    """Obter estatísticas dos alertas"""
    try:
        total = db.query(models.Alert).count()
        unread = db.query(models.Alert).filter(models.Alert.is_read == False).count()
        unresolved = db.query(models.Alert).filter(models.Alert.is_resolved == False).count()
        
        # Estatísticas por severidade
        severity_stats = {}
        for severity in ['low', 'medium', 'high', 'critical']:
            count = db.query(models.Alert).filter(models.Alert.severity == severity).count()
            if count > 0:
                severity_stats[severity] = count
        
        # Estatísticas por tipo
        type_stats = {}
        for alert_type in ['info', 'warning', 'error', 'success']:
            count = db.query(models.Alert).filter(models.Alert.alert_type == alert_type).count()
            if count > 0:
                type_stats[alert_type] = count
        
        return {
            "total": total,
            "unread": unread,
            "unresolved": unresolved,
            "by_severity": severity_stats,
            "by_type": type_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    """
    Remove um alerta do sistema.
    """
    alert = crud.delete_alert(db, alert_id=alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta não encontrado.")
    return None

@router.get("/", response_model=schemas.PaginatedResponse[schemas.Alert])
def list_alerts(
    db: Session = Depends(get_db),
    page: int = 1,
    size: int = 20,
):
    skip = (page - 1) * size
    total, alerts = crud.get_alerts_paginated(db, skip=skip, limit=size)
    return schemas.PaginatedResponse[schemas.Alert](
        total=total,
        page=page,
        size=size,
        items=alerts,
    )

