from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

import crud, schemas, database

router = APIRouter(
    prefix="/devices",
    tags=["devices"],
    responses={404: {"description": "Not found"}},
)

# Dependency to get DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Função para comparar dados antigos e novos e gerar logs de mudança
def generate_change_logs(old_device, new_device_data):
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
        if old_device.hardware_details:
            for hw_field, hw_value in new_hw.items():
                old_hw_value = getattr(old_device.hardware_details, hw_field, None)
                if hw_value is not None and old_hw_value != hw_value:
                    changes.append(f"{hw_field} alterado de '{old_hw_value}' para '{hw_value}'")

    return changes


@router.post("/", response_model=schemas.Device)
def create_or_update_device(device: schemas.DeviceCreate, db: Session = Depends(get_db)):
    """
    Cria um novo dispositivo ou atualiza um existente com base no IP ou MAC address.
    Se houver mudanças, registra no histórico.
    """
    # Buscar por IP ou MAC
    db_device = crud.get_device_by_ip_or_mac(db, device.ip_address, device.mac_address)

    if db_device:
        # Gerar logs de alteração antes de atualizar
        changes = generate_change_logs(db_device, device.model_dump())

        # Atualizar dispositivo
        device_update = schemas.DeviceUpdate(**device.model_dump())
        updated_device = crud.update_device(db, device_id=db_device.id, device=device_update)

        # Salvar logs no histórico
        for change in changes:
            log = schemas.HistoryLogCreate(
                change_type="update",
                component="device",  # ou "hardware", depende de onde você detectou a mudança
                change_description=change,  # nome correto
                timestamp=datetime.now()
            )
            crud.create_history_log(db, log, device_id=db_device.id)

        return updated_device
    else:
        # Criar novo dispositivo
        new_device = crud.create_device(db=db, device=device)

        # Log de criação
        log = schemas.HistoryLogCreate(
            change_type="create",
            component="device",
            change_description="Dispositivo adicionado ao inventário",
            timestamp=datetime.now()
        )
        crud.create_history_log(db, log, device_id=new_device.id)

        return new_device


@router.get("/", response_model=List[schemas.Device])
def read_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all devices."""
    return crud.get_devices(db, skip=skip, limit=limit)


@router.get("/{device_id}", response_model=schemas.Device)
def read_device(device_id: int, db: Session = Depends(get_db)):
    """Get a specific device by ID."""
    db_device = crud.get_device(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return db_device


@router.put("/{device_id}", response_model=schemas.Device)
def update_device(device_id: int, device: schemas.DeviceUpdate, db: Session = Depends(get_db)):
    """Update a device."""
    db_device = crud.update_device(db, device_id=device_id, device=device)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return db_device


@router.delete("/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    """Delete a device."""
    if crud.delete_device(db, device_id=device_id):
        return {"message": "Device deleted successfully"}
    raise HTTPException(status_code=404, detail="Device not found")


@router.post("/{device_id}/history", response_model=schemas.HistoryLog)
def create_history_log(device_id: int, log: schemas.HistoryLogCreate, db: Session = Depends(get_db)):
    """Create a history log for a device."""
    db_device = crud.get_device(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return crud.create_history_log(db=db, log=log, device_id=device_id)

@router.get("/{device_id}/full", response_model=schemas.DeviceFull)
def read_device_with_history(device_id: int, db: Session = Depends(get_db)):
    """
    Retorna um dispositivo específico junto com seus logs de histórico.
    """
    db_device = crud.get_device(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    # Buscar histórico
    history_logs = crud.get_history_logs(db, device_id=device_id)

    # Converter o dispositivo em dict
    device_dict = db_device.__dict__.copy()

    # Adicionar o histórico
    device_dict["history_logs"] = history_logs

    return device_dict


    return device_dict

@router.get("/{device_id}/history", response_model=List[schemas.HistoryLog])
def read_history_logs(device_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get history logs for a device."""
    db_device = crud.get_device(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return crud.get_history_logs(db=db, device_id=device_id, skip=skip, limit=limit)
