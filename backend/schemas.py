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
    installed_software: list[dict[str, Any]] | None = None
    usb_devices: list[dict[str, Any]] | None = None
    os: str | None = None
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


# ----------------------------
# Snapshots
# ----------------------------
class SnapshotBase(BaseModel):
    hash_sha256: str = Field(..., min_length=64, max_length=64, description="Hash SHA256 do snapshot")
    device_count: int = Field(..., ge=0, description="Número de dispositivos no snapshot")
    file_path: str = Field(..., description="Caminho do arquivo do snapshot")
    file_size: int | None = Field(default=None, ge=0, description="Tamanho do arquivo em bytes")


class SnapshotCreate(SnapshotBase):
    pass


class Snapshot(SnapshotBase):
    id: int
    timestamp: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


# ----------------------------
# Alerts
# ----------------------------
class AlertBase(BaseModel):
    title: str = Field(..., description="Título do alerta")
    message: str = Field(..., description="Mensagem do alerta")
    alert_type: str = Field(..., description="Tipo do alerta: info, warning, error, success")
    severity: str = Field(default="medium", description="Severidade: low, medium, high, critical")
    source: str | None = Field(default=None, description="Origem do alerta")
    device_id: int | None = Field(default=None, description="ID do dispositivo relacionado")
    snapshot_id: int | None = Field(default=None, description="ID do snapshot relacionado")
    alert_metadata: dict[str, Any] | None = Field(default=None, description="Metadados adicionais")


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    is_read: bool | None = None
    is_resolved: bool | None = None
    resolved_by: str | None = None


class Alert(AlertBase):
    id: int
    is_read: bool
    is_resolved: bool
    resolved_by: str | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
