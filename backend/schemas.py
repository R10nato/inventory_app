from pydantic import BaseModel, Field
from typing import Any, List, Optional
from datetime import datetime
from uuid import UUID


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
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, HttpUrl, validator, root_validator
import hashlib
import hmac
import base64
import json
from datetime import datetime
from enum import Enum

class ChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    REPLACED = "replaced"

class SeverityLevel(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class HistoryLogBase(BaseModel):
    """Base schema for history log entries."""
    component: str = Field(..., description="Componente afetado (ex: 'cpu', 'memory', 'disk')")
    change_type: ChangeType = Field(..., description="Tipo de mudança ocorrida")
    change_description: str = Field(..., description="Descrição legível da mudança")
    severity: SeverityLevel = Field(default=SeverityLevel.INFO, description="Nível de severidade da mudança")
    
    # Detalhes estruturados
    path: Optional[str] = Field(None, description="Caminho do campo alterado (ex: 'hardware.cpu.0.model')")
    old_value: Optional[Any] = Field(None, description="Valor anterior (estruturado)")
    new_value: Optional[Any] = Field(None, description="Novo valor (estruturado)")
    
    # Metadados
    source: Optional[str] = Field(None, description="Fonte da mudança (agente, usuário, sistema)")
    user: Optional[str] = Field(None, description="Usuário responsável pela mudança, se aplicável")
    evidence: Optional[Dict[str, Any]] = Field(None, description="Evidências da mudança (dados brutos, hashes, etc.)")
    
    # Validação de dados estruturados
    @validator('old_value', 'new_value', pre=True)
    def validate_json_serializable(cls, v):
        if v is not None and not isinstance(v, (str, int, float, bool, type(None))):
            try:
                json.dumps(v)
            except (TypeError, OverflowError):
                raise ValueError("Valor deve ser serializável em JSON")
        return v

class HistoryLogCreate(HistoryLogBase):
    """Schema para criação de logs de histórico."""
    pass

class HistoryLog(HistoryLogBase):
    """Schema completo de um log de histórico."""
    id: int
    device_id: int
    timestamp: datetime
    agent_version: Optional[str] = Field(None, description="Versão do agente que reportou a mudança")
    
    class Config:
        from_attributes = True

class HistoryLogBatchCreate(BaseModel):
    """Schema para criação em lote de logs de histórico."""
    device_id: int
    logs: List[HistoryLogCreate] = Field(..., min_items=1)
    snapshot: Optional[Dict[str, Any]] = Field(
        None, 
        description="Snapshot opcional do estado atual do dispositivo"
    )
    agent_version: Optional[str] = Field(
        None, 
        description="Versão do agente que está enviando os logs"
    )
    signature: Optional[str] = Field(
        None,
        description="Assinatura HMAC-SHA256 dos dados usando a chave secreta do agente"
    )
    
    @root_validator
    def validate_signature(cls, values):
        # A validação real da assinatura será feita no endpoint
        # usando a chave secreta armazenada no servidor
        return values
    
    model_config = {"from_attributes": True}


class BatchProcessResult(BaseModel):
    """Modelo de resposta para operações em lote."""
    success: bool = Field(..., description="Indica se a operação foi bem-sucedida")
    logs_processed: int = Field(..., description="Número de logs processados")
    snapshot_processed: bool = Field(..., description="Indica se um snapshot foi processado")
    warnings: List[str] = Field(default_factory=list, description="Avisos não fatais")
    batch_id: str = Field(..., description="ID único para rastreamento do lote")
    message: str = Field(..., description="Mensagem descritiva do resultado")


# ----------------------------
# Devices
# ----------------------------
class DeviceBase(BaseModel):
    name: str | None = None
    ip_address: str = Field(..., description="Endereço IPv4 ou IPv6 do dispositivo")
    mac_address: str | None = Field(
        default=None,
        pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",
        description="Endereço MAC no formato AA:BB:CC:DD:EE:FF (WMI, lshw, etc)")
    device_type: str | None = Field(default="unknown")
    os: str | None = None
    status: str | None = Field(default="online")
    
    # Identificadores únicos estáveis
    system_uuid: str | None = Field(default=None, description="UUID único do sistema")
    motherboard_serial: str | None = Field(default=None, description="Serial da placa-mãe")
    bios_version: str | None = Field(default=None, description="Versão da BIOS/UEFI")
    bios_vendor: str | None = Field(default=None, description="Fabricante da BIOS")
    bios_date: str | None = Field(default=None, description="Data da BIOS")
    chassis_serial: str | None = Field(default=None, description="Serial do chassi")
    
    # Metadados de coleta
    agent_version: str | None = Field(default=None, description="Versão do agente de coleta")
    collection_method: str | None = Field(default=None, description="Método de coleta")
    uptime_seconds: int | None = Field(default=None, description="Uptime em segundos")


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
# Enhanced Snapshots (New Structure)
# ----------------------------
class EnhancedSnapshot(BaseModel):
    """New snapshot structure with normalized hardware data"""
    device_id: str
    agent_id: Optional[str] = None
    agent_version: Optional[str] = None
    timestamp: datetime
    hardware: dict = Field(..., description="Normalized hardware structure")
    snapshot_hash: str = Field(..., min_length=64, max_length=64, description="SHA256 hash of snapshot")

    model_config = {"from_attributes": True}


class EnhancedSnapshotCreate(BaseModel):
    device_id: str
    agent_id: Optional[str] = None
    agent_version: Optional[str] = None
    hardware: dict
    snapshot_hash: str


# ----------------------------
# Change Event Items (New Structure)
# ----------------------------
class ChangeEventItem(BaseModel):
    """Structured change event for precise tracking"""
    change_id: Optional[str] = None  # UUID gerado pelo agente ou backend
    device_id: str
    timestamp: datetime
    component: str = Field(..., description="Component type: ram, disk, nic, bios, etc.")
    change_type: str = Field(..., description="Change type: added, removed, modified, replaced")
    path: str = Field(..., description="Path in snapshot: hardware.disks[0].serial")
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    evidence: Optional[dict] = Field(default=None, description="Raw snippets / WMI output")
    change_hash: str = Field(..., description="SHA256 hash for deduplication/idempotency")
    agent_version: Optional[str] = None

    model_config = {"from_attributes": True}


class ChangeEventItemCreate(BaseModel):
    device_id: str
    component: str
    change_type: str
    path: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    evidence: Optional[dict] = None
    agent_version: Optional[str] = None


# ----------------------------
# Legacy Snapshots (Backward Compatibility)
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
