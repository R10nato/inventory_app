from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    ip_address = Column(String, unique=True, index=True)
    mac_address = Column(String, unique=True, index=True, nullable=True)
    device_type = Column(String, index=True) # e.g., 'computer', 'printer', 'smartphone'
    os = Column(String, nullable=True)
    status = Column(String, default="unknown") # e.g., 'online', 'offline', 'unknown'
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to detailed hardware components (if it's a computer)
    hardware_details = relationship("HardwareDetail", back_populates="device", uselist=False, cascade="all, delete-orphan")
    history_logs = relationship("HistoryLog", back_populates="device", cascade="all, delete-orphan")

class HardwareDetail(Base):
    __tablename__ = "hardware_details"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), unique=True)

    # Using JSON for flexibility initially, can be normalized later
    cpu_info = Column(JSON, nullable=True) # { "brand": "Intel", "model": "i7-9700K", "cores": 8, ... }
    ram_info = Column(JSON, nullable=True) # { "total_gb": 16, "type": "DDR4", "slots_used": 2, "slots_total": 4, "modules": [...] }
    disk_info = Column(JSON, nullable=True) # [ { "name": "C:", "type": "SSD", "total_gb": 512, "free_gb": 250, "smart_status": "Good" }, ... ]
    gpu_info = Column(JSON, nullable=True) # { "brand": "NVIDIA", "model": "RTX 3070", "vram_mb": 8192 }
    motherboard_info = Column(JSON, nullable=True) # { "manufacturer": "ASUS", "model": "ROG STRIX Z390-E" }
    network_info = Column(JSON, nullable=True) # [ { "type": "Ethernet", "mac": "...", "speed": 1000 }, ... ]
    temperature_info = Column(JSON, nullable=True) # { "cpu": 55.5, "gpu": 60.0 }
    power_supply_info = Column(JSON, nullable=True) # { "type": "ATX", "power_watts": 750 }
    custom_notes = Column(Text, nullable=True)

    device = relationship("Device", back_populates="hardware_details")

class HistoryLog(Base):
    __tablename__ = "history_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    component = Column(String, index=True) # e.g., 'RAM', 'Disk', 'OS'
    change_description = Column(Text)
    details_before = Column(Text, nullable=True)
    details_after = Column(Text, nullable=True)
    user = Column(String, nullable=True) # Optional: who made the change

    device = relationship("Device", back_populates="history_logs")

