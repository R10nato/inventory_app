from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)  # Nome do dispositivo é obrigatório
    ip_address = Column(String(45), unique=True, index=True, nullable=False)  # IPv6 cabe em 45 chars
    mac_address = Column(String(17), unique=True, index=True, nullable=True)  # Formato padrão: 17 chars
    device_type = Column(String(100), nullable=True, index=True)
    os = Column(String(100), nullable=True)
    status = Column(String(50), default="unknown", index=True)

    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

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

    cpu_info = Column(JSON, nullable=True)          # {"model": "Intel i7", "cores": 8, "threads": 16}
    ram_info = Column(JSON, nullable=True)          # [{"size": "8GB", "type": "DDR4", "speed": "3200MHz"}]
    disk_info = Column(JSON, nullable=True)         # [{"model": "Samsung SSD", "capacity": "500GB"}]
    gpu_info = Column(JSON, nullable=True)          # {"model": "NVIDIA RTX 3060"}
    motherboard_info = Column(JSON, nullable=True)  # {"model": "ASUS XYZ"}
    network_info = Column(JSON, nullable=True)      # [{"interface": "eth0", "mac": "...", "ip": "..."}]
    temperature_info = Column(JSON, nullable=True)  # {"cpu_temp": 45, "gpu_temp": 60}
    power_supply_info = Column(JSON, nullable=True) # {"status": "ok", "voltage": "220V"}
    custom_notes = Column(Text, nullable=True)

    device = relationship("Device", back_populates="hardware_details")


class HistoryLog(Base):
    __tablename__ = "history_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    component = Column(String(100), index=True)  # Exemplo: "CPU", "RAM", "GPU"
    change_description = Column(Text, nullable=False)
    details_before = Column(Text, nullable=True)
    details_after = Column(Text, nullable=True)
    user = Column(String(100), nullable=True)

    device = relationship("Device", back_populates="history_logs")
