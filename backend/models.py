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
    device_type = Column(String, index=True)
    os = Column(String, nullable=True)
    status = Column(String, default="unknown")
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    hardware_details = relationship("HardwareDetail", back_populates="device", uselist=False, cascade="all, delete-orphan")
    history_logs = relationship("HistoryLog", back_populates="device", cascade="all, delete-orphan")

class HardwareDetail(Base):
    __tablename__ = "hardware_details"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), unique=True)

    cpu_info = Column(JSON, nullable=True)
    ram_info = Column(JSON, nullable=True)
    disk_info = Column(JSON, nullable=True)
    gpu_info = Column(JSON, nullable=True)
    motherboard_info = Column(JSON, nullable=True)
    network_info = Column(JSON, nullable=True)
    temperature_info = Column(JSON, nullable=True)
    power_supply_info = Column(JSON, nullable=True)
    custom_notes = Column(Text, nullable=True)

    device = relationship("Device", back_populates="hardware_details")

class HistoryLog(Base):
    __tablename__ = "history_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    component = Column(String, index=True)
    change_description = Column(Text)
    details_before = Column(Text, nullable=True)
    details_after = Column(Text, nullable=True)
    user = Column(String, nullable=True)

    device = relationship("Device", back_populates="history_logs")