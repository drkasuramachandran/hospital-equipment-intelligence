from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional

class LoginIn(BaseModel):
    email: str
    password: str

class EquipmentIn(BaseModel):
    asset_code: str
    name: str
    category: str = "General"
    manufacturer: str = ""
    model: str = ""
    serial_number: str = ""
    department: str = "Unassigned"
    location: str = ""
    status: str = "Available"
    risk_level: str = "Medium"
    next_pm_date: Optional[date] = None
    next_calibration_date: Optional[date] = None

class EquipmentOut(EquipmentIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

class WorkOrderIn(BaseModel):
    equipment_id: Optional[int] = None
    title: str
    description: str = ""
    priority: str = "Medium"
    reported_by: str = "Staff"

class WorkOrderOut(WorkOrderIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    created_at: datetime

class TaskIn(BaseModel):
    equipment_id: int
    task_type: str
    due_date: date
    assigned_to: str = ""

class InspectionIn(BaseModel):
    equipment_id: int
    inspection_date: date
    outcome: str = "Pending"
    findings: str = ""
    inspector: str = ""
