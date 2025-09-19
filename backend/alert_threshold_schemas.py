from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum

class MetricType(str, Enum):
    CPU = "cpu"
    RAM = "ram"
    DISK = "disk"
    TEMPERATURE = "temperature"
    NETWORK = "network"
    BATTERY = "battery"
    USB = "usb"

class ComparisonOperator(str, Enum):
    GREATER_THAN = ">"
    LESS_THAN = "<"
    EQUAL = "=="
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="

class AlertThresholdBase(BaseModel):
    device_id: Optional[int] = None
    metric_type: MetricType = Field(..., description="Tipo da métrica a ser monitorada")
    threshold_value: float = Field(..., gt=0, description="Valor do threshold")
    comparison: ComparisonOperator = Field(..., description="Operador de comparação")
    is_active: bool = True

class AlertThresholdCreate(AlertThresholdBase):
    pass

class AlertThresholdUpdate(BaseModel):
    device_id: Optional[int] = None
    metric_type: Optional[MetricType] = None
    threshold_value: Optional[float] = None
    comparison: Optional[ComparisonOperator] = None
    is_active: Optional[bool] = None

class AlertThresholdInDB(AlertThresholdBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class AlertThresholdResponse(AlertThresholdInDB):
    device_name: Optional[str] = None
