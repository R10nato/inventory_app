from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import models, schemas
from datetime import datetime
from typing import Optional

def get_device_by_id(db: Session, device_id: int):
    return db.query(models.Device).filter(models.Device.id == device_id).first()

def get_device_by_ip(db: Session, ip_address: str):
    return db.query(models.Device).filter(models.Device.ip_address == ip_address).first()

def get_device_by_ip_or_mac(db: Session, ip_address: str, mac_address: Optional[str] = None):
    device = db.query(models.Device).filter(models.Device.ip_address == ip_address).first()
    if not device and mac_address:
        device = db.query(models.Device).filter(models.Device.mac_address == mac_address).first()
    return device

def get_devices(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Device).offset(skip).limit(limit).all()

def create_or_update_device(db: Session, device: schemas.DeviceCreate):
    """Creates a new device or updates an existing one based on IP or MAC address."""
    db_device = get_device_by_ip_or_mac(db, device.ip_address, device.mac_address)

    if db_device:
        # Update existing device
        update_data = device.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == "hardware_details" and value is not None:
                if db_device.hardware_details:
                    for hw_key, hw_value in value.items():
                        setattr(db_device.hardware_details, hw_key, hw_value)
                else:
                    db_hardware = models.HardwareDetail(**value, device_id=db_device.id)
                    db.add(db_hardware)
                    db_device.hardware_details = db_hardware
            elif hasattr(db_device, key):
                setattr(db_device, key, value)
        db_device.last_seen = datetime.now()
    else:
        # Create new device
        hardware_data = device.hardware_details
        device_data = device.model_dump(exclude={"hardware_details"})
        db_device = models.Device(**device_data)
        db.add(db_device)
        db.flush()  # To get db_device.id

        if hardware_data:
            db_hardware = models.HardwareDetail(**hardware_data.model_dump(), device_id=db_device.id)
            db.add(db_hardware)

    try:
        db.commit()
        db.refresh(db_device)
    except IntegrityError:
        db.rollback()
        raise
    return db_device

def update_device_manual(db: Session, device_id: int, device_update: schemas.DeviceUpdate):
    db_device = get_device_by_id(db, device_id=device_id)
    if not db_device:
        return None

    update_data = device_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if key == "hardware_details" and value is not None:
            if db_device.hardware_details:
                for hw_key, hw_value in value.items():
                    setattr(db_device.hardware_details, hw_key, hw_value)
            else:
                db_hardware = models.HardwareDetail(**value, device_id=db_device.id)
                db.add(db_hardware)
                db_device.hardware_details = db_hardware
        elif hasattr(db_device, key):
            setattr(db_device, key, value)

    try:
        db.commit()
        db.refresh(db_device)
    except IntegrityError:
        db.rollback()
        raise
    return db_device

def delete_device(db: Session, device_id: int):
    db_device = get_device_by_id(db, device_id=device_id)
    if db_device:
        db.delete(db_device)
        db.commit()
        return True
    return False
