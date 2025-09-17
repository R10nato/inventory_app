from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import models, schemas
from datetime import datetime, timezone
from typing import Optional, Tuple, List


# ----------------------------
# Device Queries
# ----------------------------
def get_device(db: Session, device_id: int) -> Optional[models.Device]:
    return db.query(models.Device).filter(models.Device.id == device_id).first()


def get_device_by_id(db: Session, device_id: int) -> Optional[models.Device]:
    return get_device(db, device_id)


def get_device_by_ip(db: Session, ip_address: str) -> Optional[models.Device]:
    return db.query(models.Device).filter(models.Device.ip_address == ip_address).first()


def get_device_by_ip_or_mac(db: Session, ip_address: str, mac_address: Optional[str] = None) -> Optional[models.Device]:
    device = get_device_by_ip(db, ip_address)
    if not device and mac_address:
        device = db.query(models.Device).filter(models.Device.mac_address == mac_address).first()
    return device


def get_devices(db: Session, skip: int = 0, limit: int = 100) -> List[models.Device]:
    return db.query(models.Device).offset(skip).limit(limit).all()


def get_devices_paginated(db: Session, skip: int = 0, limit: int = 100) -> Tuple[int, List[models.Device]]:
    query = db.query(models.Device)
    total = query.count()
    devices = query.order_by(models.Device.last_seen.desc()).offset(skip).limit(limit).all()
    return total, devices


# ----------------------------
# Device Create / Update
# ----------------------------
def create_device(db: Session, device: schemas.DeviceCreate) -> models.Device:
    """Cria um novo dispositivo ou atualiza se já existir pelo MAC address."""
    try:
        existing_device = db.query(models.Device).filter(models.Device.mac_address == device.mac_address).first()
        if existing_device:
            return update_device(db, existing_device.id, device)

        device_data = device.model_dump(exclude={"hardware_details"})
        db_device = models.Device(**device_data)
        db.add(db_device)
        db.flush()  # garante ID antes de hardware_details

        if device.hardware_details:
            hw_data = (
                device.hardware_details.model_dump(exclude_unset=True)
                if hasattr(device.hardware_details, "model_dump")
                else dict(device.hardware_details)
            )
            db_hardware = models.HardwareDetail(**hw_data, device_id=db_device.id)
            db.add(db_hardware)

        db.commit()
        db.refresh(db_device)
        return db_device
    except IntegrityError:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Erro ao criar dispositivo: {e}")


def update_device(db: Session, device_id: int, device: schemas.DeviceUpdate) -> Optional[models.Device]:
    """Atualiza um dispositivo existente."""
    db_device = get_device_by_id(db, device_id=device_id)
    if not db_device:
        return None

    update_data = device.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if key == "hardware_details" and value is not None:
            hw_data = value.model_dump(exclude_unset=True) if hasattr(value, "model_dump") else dict(value)
            if db_device.hardware_details:
                for hw_key, hw_value in hw_data.items():
                    if hw_value is not None:
                        setattr(db_device.hardware_details, hw_key, hw_value)
            else:
                db_hardware = models.HardwareDetail(**hw_data, device_id=db_device.id)
                db.add(db_hardware)
                db_device.hardware_details = db_hardware
        elif hasattr(db_device, key) and value is not None:
            setattr(db_device, key, value)

    db_device.last_seen = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(db_device)
    except IntegrityError:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Erro ao atualizar dispositivo: {e}")

    return db_device


def create_or_update_device(db: Session, device: schemas.DeviceCreate) -> models.Device:
    """Cria ou atualiza dispositivo com base no IP/MAC address."""
    db_device = get_device_by_ip_or_mac(db, device.ip_address, device.mac_address)
    if db_device:
        return update_device(db, db_device.id, device)
    return create_device(db, device)


def delete_device(db: Session, device_id: int) -> bool:
    db_device = get_device_by_id(db, device_id=device_id)
    if db_device:
        db.delete(db_device)
        db.commit()
        return True
    return False


# ----------------------------
# History Logs
# ----------------------------
def create_history_log(db: Session, log: schemas.HistoryLogCreate, device_id: int) -> models.HistoryLog:
    """Cria um log de histórico para um dispositivo."""
    log_data = log.model_dump() if hasattr(log, "model_dump") else dict(log)
    db_log = models.HistoryLog(**log_data, device_id=device_id)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def get_history_logs_paginated(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    device_id: Optional[int] = None,
    component: Optional[str] = None,
    change_type: Optional[schemas.ChangeType] = None,
    # severity removido - não é um campo de HistoryLog
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Tuple[int, List[models.HistoryLog]]:
    """Busca logs de histórico com paginação e filtros opcionais."""
    query = db.query(models.HistoryLog)

    if device_id is not None:
        query = query.filter(models.HistoryLog.device_id == device_id)
    if component:
        query = query.filter(models.HistoryLog.component == component)
    if change_type:
        query = query.filter(models.HistoryLog.change_type == change_type)
    # severity não é um campo de HistoryLog, apenas de Alert
    # if severity:
    #     query = query.filter(models.HistoryLog.severity == severity)
    if start_date:
        query = query.filter(models.HistoryLog.timestamp >= start_date)
    if end_date:
        query = query.filter(models.HistoryLog.timestamp <= end_date)

    total = query.count()
    logs = query.order_by(models.HistoryLog.timestamp.desc()).offset(skip).limit(limit).all()
    return total, logs


# ----------------------------
# Snapshot Queries
# ----------------------------
def get_snapshot(db: Session, snapshot_id: int) -> Optional[models.Snapshot]:
    return db.query(models.Snapshot).filter(models.Snapshot.id == snapshot_id).first()


def get_snapshot_by_hash(db: Session, hash_sha256: str) -> Optional[models.Snapshot]:
    return db.query(models.Snapshot).filter(models.Snapshot.hash_sha256 == hash_sha256).first()


def get_snapshots(db: Session, skip: int = 0, limit: int = 100) -> List[models.Snapshot]:
    return db.query(models.Snapshot).order_by(models.Snapshot.timestamp.desc()).offset(skip).limit(limit).all()


def create_snapshot(db: Session, snapshot: schemas.SnapshotCreate) -> models.Snapshot:
    """Cria um novo snapshot no banco de dados."""
    try:
        existing = get_snapshot_by_hash(db, snapshot.hash_sha256)
        if existing:
            return existing
        db_snapshot = models.Snapshot(**snapshot.model_dump())
        db.add(db_snapshot)
        db.commit()
        db.refresh(db_snapshot)
        return db_snapshot
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Erro ao criar snapshot: {e}")


def delete_snapshot(db: Session, snapshot_id: int) -> Optional[models.Snapshot]:
    snapshot = get_snapshot(db, snapshot_id)
    if snapshot:
        db.delete(snapshot)
        db.commit()
    return snapshot


# ----------------------------
# Alert Queries
# ----------------------------
def get_alert(db: Session, alert_id: int) -> Optional[models.Alert]:
    return db.query(models.Alert).filter(models.Alert.id == alert_id).first()


def get_alerts(
    db: Session, skip: int = 0, limit: int = 100, unread_only: bool = False, unresolved_only: bool = False
) -> List[models.Alert]:
    query = db.query(models.Alert)
    if unread_only:
        query = query.filter(models.Alert.is_read == False)
    if unresolved_only:
        query = query.filter(models.Alert.is_resolved == False)

    return query.order_by(models.Alert.created_at.desc()).offset(skip).limit(limit).all()


def get_alerts_by_device(db: Session, device_id: int, skip: int = 0, limit: int = 100) -> List[models.Alert]:
    return (
        db.query(models.Alert)
        .filter(models.Alert.device_id == device_id)
        .order_by(models.Alert.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_alert(db: Session, alert: schemas.AlertCreate) -> models.Alert:
    db_alert = models.Alert(**alert.model_dump())
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


def update_alert(db: Session, alert_id: int, alert_update: schemas.AlertUpdate) -> Optional[models.Alert]:
    db_alert = get_alert(db, alert_id)
    if not db_alert:
        return None

    update_data = alert_update.model_dump(exclude_unset=True)

    if update_data.get("is_resolved") and not db_alert.is_resolved:
        update_data["resolved_at"] = datetime.now(timezone.utc)

    for key, value in update_data.items():
        setattr(db_alert, key, value)

    db.commit()
    db.refresh(db_alert)
    return db_alert


def delete_alert(db: Session, alert_id: int) -> Optional[models.Alert]:
    alert = get_alert(db, alert_id)
    if alert:
        db.delete(alert)
        db.commit()
    return alert


def mark_all_alerts_as_read(db: Session, device_id: Optional[int] = None) -> bool:
    query = db.query(models.Alert).filter(models.Alert.is_read == False)
    if device_id:
        query = query.filter(models.Alert.device_id == device_id)
    query.update({"is_read": True})
    db.commit()
    return True
