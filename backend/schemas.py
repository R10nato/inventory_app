from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime


# ----------------------------
# Hardware Details
# ----------------------------
class HardwareDetailBase(BaseModel):
    cpu_info: Optional[Dict[str, Any]] = None
    ram_info: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    disk_info: Optional[List[Dict[str, Any]]] = None
    gpu_info: Optional[Dict[str, Any]] = None
    motherboard_info: Optional[Dict[str, Any]] = None
    network_info: Optional[List[Dict[str, Any]]] = None
    temperature_info: Optional[Dict[str, Any]] = None
    power_supply_info: Optional[Dict[str, Any]] = None
    custom_notes: Optional[str] = None

    model_config = {"from_attributes": True}


class HardwareDetailCreate(HardwareDetailBase):
    pass


class HardwareDetail(HardwareDetailBase):
    id: int
    device_id: int

    model_config = {"from_attributes": True}


# ----------------------------
# History Logs
# ----------------------------
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

    model_config = {"from_attributes": True}


# ----------------------------
# Devices
# ----------------------------
class DeviceBase(BaseModel):
    name: Optional[str] = None
    ip_address: str = Field(..., description="Endereço IPv4 ou IPv6 do dispositivo")
    mac_address: Optional[str] = Field(
        default=None,
        pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",
        description="Endereço MAC no formato AA:BB:CC:DD:EE:FF"
    )
    device_type: Optional[str] = Field(default="unknown")
    os: Optional[str] = None
    status: Optional[str] = Field(default="online")


class DeviceCreate(DeviceBase):
    hardware_details: Optional[HardwareDetailCreate] = None


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = Field(
        default=None,
        pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",
        description="Endereço MAC no formato AA:BB:CC:DD:EE:FF"
    )
    device_type: Optional[str] = None
    os: Optional[str] = None
    status: Optional[str] = None
    hardware_details: Optional[HardwareDetailCreate] = None


class Device(DeviceBase):
    id: int
    last_seen: datetime
    created_at: datetime
    hardware_details: Optional[HardwareDetail] = None

    model_config = {"from_attributes": True}


# ----------------------------
# Device with History (para o endpoint /devices/{id}/full)
# ----------------------------
class DeviceFull(Device):
    history_logs: Optional[List[HistoryLog]] = []
