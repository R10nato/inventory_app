from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime


# ----------------------------
# Hardware Details
# ----------------------------
class HardwareDetailBase(BaseModel):
    cpu_info: dict[str, Any] | None = None
    ram_info: dict[str, Any] | list[dict[str, Any]] | None = None
    disk_info: list[dict[str, Any]] | None = None
    gpu_info: dict[str, Any] | None = None
    motherboard_info: dict[str, Any] | None = None
    network_info: list[dict[str, Any]] | None = None
    temperature_info: dict[str, Any] | None = None
    power_supply_info: dict[str, Any] | None = None
    custom_notes: str | None = None

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
    details_before: str | None = None
    details_after: str | None = None
    user: str | None = None


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
    name: str | None = None
    ip_address: str = Field(..., description="Endereço IPv4 ou IPv6 do dispositivo")
    mac_address: str | None = Field(
        default=None,
        pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",
        description="Endereço MAC no formato AA:BB:CC:DD:EE:FF"
    )
    device_type: str | None = Field(default="unknown")
    os: str | None = None
    status: str | None = Field(default="online")


class DeviceCreate(DeviceBase):
    hardware_details: HardwareDetailCreate | None = None


class DeviceUpdate(BaseModel):
    name: str | None = None
    ip_address: str | None = None
    mac_address: str | None = Field(
        default=None,
        pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",
        description="Endereço MAC no formato AA:BB:CC:DD:EE:FF"
    )
    device_type: str | None = None
    os: str | None = None
    status: str | None = None
    hardware_details: HardwareDetailCreate | None = None


class Device(DeviceBase):
    id: int
    last_seen: datetime
    created_at: datetime
    hardware_details: HardwareDetail | None = None

    model_config = {"from_attributes": True}


# ----------------------------
# Device with History (para o endpoint /devices/{id}/full)
# ----------------------------
class DeviceFull(Device):
    history_logs: list[HistoryLog] = Field(default_factory=list)
