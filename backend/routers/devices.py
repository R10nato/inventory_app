from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.exc import IntegrityError

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

@router.post("/", response_model=schemas.Device)
def create_device(device: schemas.DeviceCreate, db: Session = Depends(get_db)):
    """Create a new device or update an existing one based on IP address."""
    # Check if device already exists by IP address
    db_device = crud.get_device_by_ip(db, ip_address=device.ip_address)
    if db_device:
        # Update existing device
        device_update = schemas.DeviceUpdate(**device.dict())
        return crud.update_device(db, device_id=db_device.id, device=device_update)
    else:
        # Create new device
        try:
            return crud.create_device(db=db, device=device)
        except IntegrityError:
            raise HTTPException(status_code=409, detail="MAC address already exists.")

@router.get("/", response_model=List[schemas.Device])
def read_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all devices."""
    devices = crud.get_devices(db, skip=skip, limit=limit)
    return devices

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
    db_device = crud.delete_device(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"message": "Device deleted successfully"}

@router.post("/{device_id}/history", response_model=schemas.HistoryLog)
def create_history_log(device_id: int, log: schemas.HistoryLogCreate, db: Session = Depends(get_db)):
    """Create a history log for a device."""
    db_device = crud.get_device(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return crud.create_history_log(db=db, log=log, device_id=device_id)

@router.get("/{device_id}/history", response_model=List[schemas.HistoryLog])
def read_history_logs(device_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get history logs for a device."""
    db_device = crud.get_device(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return crud.get_history_logs(db=db, device_id=device_id, skip=skip, limit=limit)

