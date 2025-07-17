from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Hardware Detail Schemas ---
class HardwareDetailBase(BaseModel):
    cpu_info: Optional[Dict[str, Any]] = None
    ram_info: Optional[Dict[str, Any]] = None
    disk_info: Optional[List[Dict[str, Any]]] = None
    gpu_info: Optional[Dict[str, Any]] = None
    motherboard_info: Optional[Dict[str, Any]] = None
    network_info: Optional[List[Dict[str, Any]]] = None
    temperature_info: Optional[Dict[str, Any]] = None
    power_supply_info: Optional[Dict[str, Any]] = None
    custom_notes: Optional[str] = None

class HardwareDetailCreate(HardwareDetailBase):
    pass

class HardwareDetail(HardwareDetailBase):
    id: int
    device_id: int

    class Config:
        from_attributes = True

# --- History Log Schemas ---
class HistoryLogBase(BaseModel):
    component: str
    change_description: str
    details_before: Optional[str] = None
    details_after: Optional[str] = None
    user: Optional[str] = None

class HistoryLogCreate(HistoryLogBase):
    pass

class HistoryLog(HistoryLogBase):
    id: int
    device_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# --- Device Schemas ---
class DeviceBase(BaseModel):
    name: Optional[str] = None
    ip_address: str
    mac_address: Optional[str] = None
    device_type: Optional[str] = Field(default="unknown")
    os: Optional[str] = None
    status: Optional[str] = Field(default="unknown")
    machine_id: Optional[str] = None  # novo campo
    network_info: Optional[List[Dict[str, Any]]] = None  # novo campo

class DeviceCreate(DeviceBase):
    hardware_details: Optional[HardwareDetailCreate] = None

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    device_type: Optional[str] = None
    os: Optional[str] = None
    status: Optional[str] = None
    machine_id: Optional[str] = None
    network_info: Optional[List[Dict[str, Any]]] = None
    hardware_details: Optional[HardwareDetailCreate] = None

class Device(DeviceBase):
    id: int
    last_seen: datetime
    created_at: datetime
    hardware_details: Optional[HardwareDetail] = None
    history_logs: List[HistoryLog] = []

    class Config:
        from_attributes = True
