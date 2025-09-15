from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import models, schemas
from datetime import datetime, timezone


# ----------------------------
# Device Queries
# ----------------------------
def get_device(db: Session, device_id: int):
    return db.query(models.Device).filter(models.Device.id == device_id).first()


def get_device_by_id(db: Session, device_id: int):
    return get_device(db, device_id)


def get_device_by_ip(db: Session, ip_address: str):
    return db.query(models.Device).filter(models.Device.ip_address == ip_address).first()


def get_device_by_ip_or_mac(db: Session, ip_address: str, mac_address: str | None = None):
    device = db.query(models.Device).filter(models.Device.ip_address == ip_address).first()
    if not device and mac_address:
        device = db.query(models.Device).filter(models.Device.mac_address == mac_address).first()
    return device


def get_devices(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Device).offset(skip).limit(limit).all()


# ----------------------------
# Device Create / Update
# ----------------------------
def create_device(db: Session, device: schemas.DeviceCreate):
    """Cria um novo dispositivo ou atualiza se já existir pelo MAC address."""
    existing_device = db.query(models.Device).filter(models.Device.mac_address == device.mac_address).first()

    if existing_device:
        # Atualiza dispositivo existente
        update_data = device.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            if key == "hardware_details" and value is not None:
                hw_data = (
                    device.hardware_details.model_dump(exclude_unset=True)
                    if hasattr(device.hardware_details, "model_dump")
                    else dict(value)
                )
                if existing_device.hardware_details:
                    for hw_key, hw_value in hw_data.items():
                        if hw_value is not None:
                            setattr(existing_device.hardware_details, hw_key, hw_value)
                else:
                    db_hardware = models.HardwareDetail(**hw_data, device_id=existing_device.id)
                    db.add(db_hardware)
                    existing_device.hardware_details = db_hardware
            elif hasattr(existing_device, key) and value is not None:
                setattr(existing_device, key, value)

        existing_device.last_seen = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing_device)
        return existing_device

    # Criar novo dispositivo
    device_data = device.model_dump(exclude={"hardware_details"})
    db_device = models.Device(**device_data)
    db.add(db_device)
    db.flush()  # gera ID

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


def update_device(db: Session, device_id: int, device: schemas.DeviceUpdate):
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
    return db_device


def create_or_update_device(db: Session, device: schemas.DeviceCreate):
    """Cria ou atualiza dispositivo com base no IP/MAC address."""
    db_device = get_device_by_ip_or_mac(db, device.ip_address, device.mac_address)

    if db_device:
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
    else:
        db_device = create_device(db, device)

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


# ----------------------------
# History Logs
# ----------------------------
def create_history_log(db: Session, log: schemas.HistoryLogCreate, device_id: int):
    """Cria um log de histórico para um dispositivo."""
    log_data = log.model_dump() if hasattr(log, "model_dump") else dict(log)
    db_log = models.HistoryLog(**log_data, device_id=device_id)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def get_history_logs(db: Session, device_id: int, skip: int = 0, limit: int = 100):
    """Busca os logs de histórico de um dispositivo específico."""
    return (
        db.query(models.HistoryLog)
        .filter(models.HistoryLog.device_id == device_id)
        .order_by(models.HistoryLog.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_all_history_logs(db: Session, skip: int = 0, limit: int = 100):
    """Busca todos os logs de histórico do sistema (debug/auditoria)."""
    return (
        db.query(models.HistoryLog)
        .order_by(models.HistoryLog.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ----------------------------
# Snapshot Queries
# ----------------------------
def get_snapshot(db: Session, snapshot_id: int):
    return db.query(models.Snapshot).filter(models.Snapshot.id == snapshot_id).first()


def get_snapshot_by_hash(db: Session, hash_sha256: str):
    return db.query(models.Snapshot).filter(models.Snapshot.hash_sha256 == hash_sha256).first()


def get_snapshots(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Snapshot)
        .order_by(models.Snapshot.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_snapshot(db: Session, snapshot: schemas.SnapshotCreate):
    """Cria um novo snapshot no banco de dados."""
    # Verifica se já existe um snapshot com o mesmo hash
    existing = get_snapshot_by_hash(db, snapshot.hash_sha256)
    if existing:
        return existing
    
    db_snapshot = models.Snapshot(**snapshot.model_dump())
    db.add(db_snapshot)
    db.commit()
    db.refresh(db_snapshot)
    return db_snapshot


def delete_snapshot(db: Session, snapshot_id: int):
    """Remove um snapshot do banco de dados."""
    snapshot = get_snapshot(db, snapshot_id)
    if snapshot:
        db.delete(snapshot)
        db.commit()
    return snapshot


# ----------------------------
# Alert Queries
# ----------------------------
def get_alert(db: Session, alert_id: int):
    return db.query(models.Alert).filter(models.Alert.id == alert_id).first()


def get_alerts(db: Session, skip: int = 0, limit: int = 100, unread_only: bool = False, unresolved_only: bool = False):
    query = db.query(models.Alert)
    
    if unread_only:
        query = query.filter(models.Alert.is_read == False)
    
    if unresolved_only:
        query = query.filter(models.Alert.is_resolved == False)
    
    return (
        query.order_by(models.Alert.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_alerts_by_device(db: Session, device_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Alert)
        .filter(models.Alert.device_id == device_id)
        .order_by(models.Alert.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_alert(db: Session, alert: schemas.AlertCreate):
    """Cria um novo alerta."""
    db_alert = models.Alert(**alert.model_dump())
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


def update_alert(db: Session, alert_id: int, alert_update: schemas.AlertUpdate):
    """Atualiza um alerta existente."""
    db_alert = get_alert(db, alert_id)
    if not db_alert:
        return None
    
    update_data = alert_update.model_dump(exclude_unset=True)
    
    # Se está sendo resolvido, adicionar timestamp
    if update_data.get("is_resolved") and not db_alert.is_resolved:
        update_data["resolved_at"] = datetime.now(timezone.utc)
    
    for key, value in update_data.items():
        setattr(db_alert, key, value)
    
    db.commit()
    db.refresh(db_alert)
    return db_alert


def delete_alert(db: Session, alert_id: int):
    """Remove um alerta do banco de dados."""
    alert = get_alert(db, alert_id)
    if alert:
        db.delete(alert)
        db.commit()
    return alert


def mark_all_alerts_as_read(db: Session, device_id: int = None):
    """Marca todos os alertas como lidos."""
    query = db.query(models.Alert).filter(models.Alert.is_read == False)
    
    if device_id:
        query = query.filter(models.Alert.device_id == device_id)
    
    query.update({"is_read": True})
    db.commit()
    return True
