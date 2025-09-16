from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

import crud, schemas, database
import models, schemas, database, crud

router = APIRouter(
    prefix="/devices",
    tags=["devices"],
    responses={404: {"description": "Not found"}},
)

# ----------------------------
# Dependency
# ----------------------------
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ----------------------------
# Função auxiliar para logs de alteração
# ----------------------------
def generate_change_logs(old_device, new_device_data: dict):
    changes = []

    # Verificar alterações simples no Device
    for field in ["name", "ip_address", "mac_address", "device_type", "os", "status"]:
        old_value = getattr(old_device, field)
        new_value = new_device_data.get(field)
        if new_value is not None and old_value != new_value:
            changes.append(f"{field} alterado de '{old_value}' para '{new_value}'")

    # Verificar alterações no Hardware
    if "hardware_details" in new_device_data and new_device_data["hardware_details"]:
        new_hw = new_device_data["hardware_details"]

        if hasattr(new_hw, "model_dump"):  # caso seja Pydantic
            new_hw = new_hw.model_dump(exclude_unset=True)
        elif isinstance(new_hw, dict):
            new_hw = new_hw
        else:
            new_hw = dict(new_hw)

        if old_device.hardware_details:
            for hw_field, hw_value in new_hw.items():
                old_hw_value = getattr(old_device.hardware_details, hw_field, None)
                if hw_value is not None and old_hw_value != hw_value:
                    changes.append(f"{hw_field} alterado de '{old_hw_value}' para '{hw_value}'")

    return changes


# ----------------------------
# Endpoints
# ----------------------------
@router.post("/", response_model=schemas.Device)
def create_or_update_device(device: schemas.DeviceCreate, db: Session = Depends(get_db)):
    """
    Cria um novo dispositivo ou atualiza um existente com base no IP ou MAC address.
    Se houver mudanças, registra no histórico.
    """
    try:
        db_device = crud.get_device_by_ip_or_mac(db, device.ip_address, device.mac_address)
        device_data = device.model_dump(exclude_unset=True)

        if db_device:
            # Gerar logs de alteração antes da atualização
            changes = generate_change_logs(db_device, device_data)

            # Atualizar
            device_update = schemas.DeviceUpdate(**device_data)
            updated_device = crud.update_device(db, device_id=db_device.id, device=device_update)

            # Registrar logs
            for change in changes:
                log = schemas.HistoryLogCreate(
                    component="device",
                    change_description=change,
                )
                crud.create_history_log(db, log, device_id=db_device.id)

            return updated_device

        # Criar novo dispositivo
        new_device = crud.create_device(db=db, device=device)

        # Registrar log de criação
        log = schemas.HistoryLogCreate(
            component="device",
            change_description="Dispositivo adicionado ao inventário",
        )
        crud.create_history_log(db, log, device_id=new_device.id)

        return new_device
    
    except Exception as e:
        import traceback
        error_msg = f"Erro ao criar/atualizar dispositivo: {e}"
        traceback_msg = traceback.format_exc()
        print(error_msg)
        print(f"Traceback: {traceback_msg}")
        
        # Log detalhado do erro
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"{error_msg}\nTraceback: {traceback_msg}")
        
        raise HTTPException(status_code=500, detail={"error": str(e), "traceback": traceback_msg})


@router.get("/", response_model=List[schemas.Device])
def read_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista todos os dispositivos."""
    return crud.get_devices(db, skip=skip, limit=limit)


@router.get("/{device_id}", response_model=schemas.Device)
def read_device(device_id: int, db: Session = Depends(get_db)):
    """Busca um dispositivo específico pelo ID."""
    db_device = crud.get_device(db, device_id=device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")
    return db_device


@router.put("/{device_id}", response_model=schemas.Device)
def update_device(device_id: int, device: schemas.DeviceUpdate, db: Session = Depends(get_db)):
    """Atualiza um dispositivo pelo ID."""
    db_device = crud.update_device(db, device_id=device_id, device=device)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")
    return db_device


@router.delete("/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    """Remove um dispositivo."""
    if crud.delete_device(db, device_id=device_id):
        return {"message": "Device deleted successfully"}
    raise HTTPException(status_code=404, detail="Device not found")


@router.post("/{device_id}/history", response_model=schemas.HistoryLog)
def create_history_log(device_id: int, log: schemas.HistoryLogCreate, db: Session = Depends(get_db)):
    """Cria um log de histórico manualmente para um dispositivo."""
    db_device = crud.get_device(db, device_id=device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")
    return crud.create_history_log(db=db, log=log, device_id=device_id)


@router.get("/{device_id}/history", response_model=List[schemas.HistoryLog])
def read_history_logs(device_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retorna apenas os logs de histórico de um dispositivo específico."""
    db_device = crud.get_device(db, device_id=device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")
    return crud.get_history_logs(db=db, device_id=device_id, skip=skip, limit=limit)


@router.get("/{device_id}/full", response_model=schemas.DeviceFull)
def read_device_with_history(device_id: int, db: Session = Depends(get_db)):
    """
    Retorna um dispositivo junto com seus logs de histórico.
    """
    db_device = crud.get_device(db, device_id=device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Buscar histórico do dispositivo
    history_logs = crud.get_history_logs(db, device_id=device_id)

    # Construir objeto Pydantic DeviceFull
    device_data = schemas.DeviceFull.model_validate(db_device)
    device_data.history_logs = history_logs

    return device_data

@router.get("/", response_model=schemas.PaginatedResponse[schemas.Device])
def list_devices(
    db: Session = Depends(get_db),
    page: int = 1,
    size: int = 20,
):
    skip = (page - 1) * size
    total, devices = crud.get_devices_paginated(db, skip=skip, limit=size)
    return schemas.PaginatedResponse[schemas.Device](
        total=total,
        page=page,
        size=size,
        items=devices,
    )

