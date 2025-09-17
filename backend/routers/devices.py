from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
import logging

import crud, schemas, database

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
# Funções auxiliares
# ----------------------------
def detect_change_type(change: str) -> str:
    """Detecta o tipo de alteração com base na descrição."""
    text = change.lower()
    if "adicionado" in text or "criado" in text or "novo" in text or "added" in text or "created" in text or "new" in text:
        return "added"
    if "removido" in text or "excluído" in text or "deletado" in text or "removed" in text or "deleted" in text:
        return "removed"
    if "substituído" in text or "replaced" in text or "trocado" in text:
        return "replaced"
    return "modified"


def generate_change_logs(old_device, new_device_data: dict):
    """Compara o estado antigo e novo do dispositivo e gera descrições de alterações."""
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


def create_history_log_safe(db: Session, device_id: int, component: str, description: str):
    """Cria log garantindo que `change_type` nunca falte."""
    change_type = detect_change_type(description)
    log = schemas.HistoryLogCreate(
        component=component,
        change_type=change_type,
        change_description=description,
    )
    return crud.create_history_log(db, log, device_id=device_id)


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
                create_history_log_safe(db, db_device.id, "device", change)

            return updated_device

        # Criar novo dispositivo
        new_device = crud.create_device(db=db, device=device)

        # Registrar log de criação
        create_history_log_safe(db, new_device.id, "device", "Dispositivo adicionado ao inventário")

        return new_device
    
    except Exception as e:
        import traceback
        error_msg = f"Erro ao criar/atualizar dispositivo: {e}"
        traceback_msg = traceback.format_exc()
        print(error_msg)
        print(f"Traceback: {traceback_msg}")
        
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
        create_history_log_safe(db, device_id, "device", "Dispositivo removido do inventário")
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
    """Retorna um dispositivo junto com seus logs de histórico."""
    db_device = crud.get_device(db, device_id=device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")

    history_logs = crud.get_history_logs(db, device_id=device_id)
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
