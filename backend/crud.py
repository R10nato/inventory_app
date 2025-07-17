from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

import models, schemas

def get_device_by_id(db: Session, device_id: int):
    return db.query(models.Device).filter(models.Device.id == device_id).first()

def get_device_by_ip(db: Session, ip_address: str):
    return db.query(models.Device).filter(models.Device.ip_address == ip_address).first()

def get_devices(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Device).offset(skip).limit(limit).all()

def create_or_update_device(db: Session, device: schemas.DeviceCreate):
    """Creates a new device or updates an existing one based on IP address."""
    db_device = get_device_by_ip(db, ip_address=device.ip_address)
    if db_device:
        # Atualizar dispositivo existente
        update_data = device.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == "hardware_details" and value is not None:
                if db_device.hardware_details:
                    # Atualiza detalhes de hardware existentes
                    hw_update_data = value
                    for hw_key, hw_value in hw_update_data.items():
                        setattr(db_device.hardware_details, hw_key, hw_value)
                else:
                    db_hardware = models.HardwareDetail(**value, device_id=db_device.id)
                    db.add(db_hardware)
                    db_device.hardware_details = db_hardware
            elif hasattr(db_device, key):
                setattr(db_device, key, value)
        db_device.last_seen = datetime.now()
    else:
        # Criar novo dispositivo
        hardware_data = device.hardware_details
        device_data = device.model_dump(exclude={"hardware_details"})
        db_device = models.Device(**device_data)
        db.add(db_device)
        db.flush()  # garante que o db_device.id esteja disponível

        if hardware_data:
            hw_data_dict = hardware_data.model_dump(exclude_unset=True)
            hw_data_dict["device_id"] = db_device.id
            db_hardware = models.HardwareDetail(**hw_data_dict)
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
