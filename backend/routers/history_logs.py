from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import models, schemas, database, crud

router = APIRouter(
    prefix="/history_logs",
    tags=["History Logs"],
    responses={404: {"description": "Not found"}},
)

# Dependency para obter sessão do DB
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[schemas.HistoryLog])
def get_all_history_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retorna todos os logs de histórico do sistema.
    """
    logs = crud.get_all_history_logs(db, skip=skip, limit=limit)
    return [schemas.HistoryLog.model_validate(log) for log in logs]


@router.get("/device/{device_id}", response_model=List[schemas.HistoryLog])
def get_history_logs_for_device(device_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retorna todos os logs de histórico para um dispositivo específico.
    """
    logs = crud.get_history_logs_for_device(db, device_id=device_id, skip=skip, limit=limit)
    if not logs:
        raise HTTPException(status_code=404, detail="Nenhum log encontrado para este dispositivo.")
    return [schemas.HistoryLog.model_validate(log) for log in logs]


@router.post("/", response_model=schemas.HistoryLog, status_code=status.HTTP_201_CREATED)
def create_history_log(log: schemas.HistoryLogCreate, device_id: int, db: Session = Depends(get_db)):
    """
    Cria um novo log de histórico manualmente para um dispositivo.
    """
    db_device = crud.get_device(db, device_id=device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado.")

    created_log = crud.create_history_log(db, device_id=device_id, log=log)
    return schemas.HistoryLog.model_validate(created_log)
