from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), unique=True, index=True, nullable=False)
    mac_address = Column(String(17), unique=True, index=True, nullable=True)
    device_type = Column(String(100), nullable=True, index=True)
    os = Column(String(100), nullable=True)
    status = Column(String(50), default="unknown", index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relacionamentos
    hardware_details = relationship(
        "HardwareDetail",
        back_populates="device",
        uselist=False,
        cascade="all, delete-orphan"
    )
    history_logs = relationship(
        "HistoryLog",
        back_populates="device",
        cascade="all, delete-orphan"
    )


class HardwareDetail(Base):
    __tablename__ = "hardware_details"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), unique=True, nullable=False)

    cpu_info = Column(JSON, nullable=True)
    ram_info = Column(JSON, nullable=True)
    disk_info = Column(JSON, nullable=True)
    gpu_info = Column(JSON, nullable=True)
    motherboard_info = Column(JSON, nullable=True)
    network_info = Column(JSON, nullable=True)
    temperature_info = Column(JSON, nullable=True)
    power_supply_info = Column(JSON, nullable=True)
    installed_software = Column(JSON, nullable=True)
    usb_devices = Column(JSON, nullable=True)
    os = Column(String(255), nullable=True)
    custom_notes = Column(Text, nullable=True)

    device = relationship("Device", back_populates="hardware_details")


class HistoryLog(Base):
    __tablename__ = "history_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    component = Column(String(100), index=True)
    change_description = Column(Text, nullable=False)
    details_before = Column(Text, nullable=True)
    details_after = Column(Text, nullable=True)
    user = Column(String(100), nullable=True)

    device = relationship("Device", back_populates="history_logs")


class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    hash_sha256 = Column(String(64), unique=True, index=True, nullable=False)
    device_count = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    alert_type = Column(String(50), nullable=False, index=True)  # 'info', 'warning', 'error', 'success'
    severity = Column(String(20), default="medium", index=True)  # 'low', 'medium', 'high', 'critical'
    source = Column(String(100), nullable=True)  # 'system', 'snapshot', 'device', etc.
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=True)
    snapshot_id = Column(Integer, ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=True)
    
    # Status do alerta
    is_read = Column(Boolean, default=False, index=True)
    is_resolved = Column(Boolean, default=False, index=True)
    resolved_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadados adicionais
    alert_metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relacionamentos
    device = relationship("Device", backref="alerts")
    snapshot = relationship("Snapshot", backref="alerts")
