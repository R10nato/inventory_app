from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    ip_address = Column(String(45), unique=True, index=True, nullable=False)
    mac_address = Column(String(17), index=True)
    device_type = Column(String(50), default="unknown")
    os = Column(String(255))
    status = Column(String(20), default="online", index=True)
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Identificadores únicos estáveis
    system_uuid = Column(String(36), unique=True, index=True, nullable=True)
    motherboard_serial = Column(String(255), index=True, nullable=True)
    bios_version = Column(String(255), nullable=True)
    bios_vendor = Column(String(255), nullable=True)
    bios_date = Column(String(20), nullable=True)
    chassis_serial = Column(String(255), nullable=True)

    # Metadados de coleta
    agent_version = Column(String(50), nullable=True)
    collection_method = Column(String(50), nullable=True)  # WMI, lshw, etc
    uptime_seconds = Column(BigInteger, nullable=True)

    # Timestamps em UTC ISO8601
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

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

    # Informações de hardware com identificadores únicos e metadados
    cpu_info = Column(JSON, nullable=True)  # + model, vendor, cores, threads, cache_sizes
    ram_info = Column(JSON, nullable=True)  # + serial, part_number, capacity_bytes, speed_mhz, slot_location
    disk_info = Column(JSON, nullable=True)  # + serial, model, capacity_bytes, interface_type, firmware_version
    gpu_info = Column(JSON, nullable=True)  # + device_id, vendor_id, uuid, vram_bytes, driver_version
    motherboard_info = Column(JSON, nullable=True)  # + serial, model, vendor, bios_version, chipset
    network_info = Column(JSON, nullable=True)  # + mac_address, vendor, speed_mbps, driver_version
    temperature_info = Column(JSON, nullable=True)
    power_supply_info = Column(JSON, nullable=True)  # + serial, model, wattage, efficiency_rating
    installed_software = Column(JSON, nullable=True)
    usb_devices = Column(JSON, nullable=True)  # + vendor_id, product_id, serial, description
    os = Column(String(255), nullable=True)
    custom_notes = Column(Text, nullable=True)
    
    # Evidência de coleta (dados brutos)
    wmi_raw_data = Column(JSON, nullable=True)  # Dados brutos WMI para auditoria
    lshw_raw_data = Column(JSON, nullable=True)  # Dados brutos lshw para Linux
    collection_hash = Column(String(64), nullable=True)  # Hash dos dados coletados
    collection_timestamp = Column(DateTime(timezone=True), nullable=True)  # UTC ISO8601

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
    
    # Enhanced fields for new structure
    change_hash = Column(String(64), nullable=True, index=True)  # SHA256 for deduplication
    change_type = Column(String(50), nullable=True, index=True)  # added, removed, modified, replaced
    path = Column(String(500), nullable=True)  # hardware.disks[0].serial
    old_value = Column(JSON, nullable=True)  # structured old value
    new_value = Column(JSON, nullable=True)  # structured new value
    evidence = Column(JSON, nullable=True)  # raw WMI/lshw snippets
    agent_version = Column(String(50), nullable=True)

    device = relationship("Device", back_populates="history_logs")


class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    hash_sha256 = Column(String(64), unique=True, index=True, nullable=False)
    device_count = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    
    # Enhanced fields for new structure
    device_id = Column(String(255), nullable=True, index=True)  # device identifier
    agent_id = Column(String(255), nullable=True)
    agent_version = Column(String(50), nullable=True)
    data = Column(JSON, nullable=True)  # normalized hardware data
    
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
