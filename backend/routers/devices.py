from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import crud, models, schemas, database

router = APIRouter(
    prefix="/devices",
    tags=["Devices"],
    responses={404: {"description": "Not found"}},
)

# Dependency to get DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Device, status_code=status.HTTP_201_CREATED)
def create_or_update_device_endpoint(device: schemas.DeviceCreate, db: Session = Depends(get_db)):
    """
    Creates a new device or updates an existing one based on IP address.
    This endpoint is typically used by the collection agents.
    """
    try:
        db_device = crud.create_or_update_device(db=db, device=device)
        return db_device
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")

@router.get("/", response_model=List[schemas.Device])
def read_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of devices.
    """
    devices = crud.get_devices(db, skip=skip, limit=limit)
    return devices

@router.get("/{device_id}", response_model=schemas.Device)
def read_device(device_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific device by its ID.
    """
    db_device = crud.get_device_by_id(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return db_device

@router.put("/{device_id}", response_model=schemas.Device)
def update_device_endpoint(device_id: int, device_update: schemas.DeviceUpdate, db: Session = Depends(get_db)):
    """
    Manually update specific fields of a device.
    This endpoint is typically used by the frontend for user edits.
    """
    db_device = crud.update_device_manual(db=db, device_id=device_id, device_update=device_update)
    if db_device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return db_device

@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device_endpoint(device_id: int, db: Session = Depends(get_db)):
    """
    Delete a device by its ID.
    """
    deleted = crud.delete_device(db=db, device_id=device_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return

# Add endpoints for history logs if needed
# Example:
# @router.post("/{device_id}/history", response_model=schemas.HistoryLog, status_code=status.HTTP_201_CREATED)
# def create_history_log_for_device(...):
#     ...

