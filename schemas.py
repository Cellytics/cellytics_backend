# schemas.py - Pydantic models for request/response validation

from pydantic import BaseModel, Field, model_validator, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from uuid import UUID
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class UserRole(str, Enum):
    system_admin = "system_admin"
    zonal_pastor = "zonal_pastor"
    zonal_admin = "zonal_admin"
    fellowship_pastor = "fellowship_pastor"
    senior_cell_leader = "senior_cell_leader"
    cell_leader = "cell_leader"


class CellStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    late = "late"
    overdue = "overdue"


# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION
# ═══════════════════════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    phone: str = Field(..., description="Phone number with country code e.g. +237690000000")
    pin: str = Field(..., description="6-digit PIN")

    @validator("phone")
    def validate_phone(cls, v):
        if not v.startswith("+"):
            raise ValueError("Phone must start with +")
        if not v[1:].isdigit():
            raise ValueError("Phone must contain only digits after +")
        return v

    @validator("pin")
    def validate_pin(cls, v):
        if len(v) != 6 or not v.isdigit():
            raise ValueError("PIN must be 6 digits")
        return v


class UserResponse(BaseModel):
    id: str
    phone: str
    name: str
    role: UserRole
    cell_id: Optional[str] = None
    senior_cell_id: Optional[str] = None
    fellowship_id: Optional[str] = None
    zone_id: Optional[str] = None
    is_active: bool


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN - ZONE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

class ZoneCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=500)


class ZoneUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=500)


class ZoneResponse(BaseModel):
    id: str
    name: str
    location: Optional[str]
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN - FELLOWSHIP MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

class FellowshipCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    zone_id: UUID = Field(..., description="Zone this fellowship belongs to")


class FellowshipUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=255)


class FellowshipResponse(BaseModel):
    id: str
    name: str
    location: Optional[str]
    zone_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN - SENIOR CELL MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

class SeniorCellCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    fellowship_id: UUID = Field(..., description="Fellowship this senior cell belongs to")


class SeniorCellUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class SeniorCellResponse(BaseModel):
    id: str
    name: str
    fellowship_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN - CELL MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

class CellCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    senior_cell_id: UUID = Field(..., description="Senior cell this cell belongs to")
    default_meeting_day: str = Field("monday", description="Default meeting day: monday-sunday")
    meeting_time: Optional[str] = Field(None, description="Meeting time in HH:MM format")

    @validator("default_meeting_day")
    def validate_meeting_day(cls, v):
        valid_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        if v.lower() not in valid_days:
            raise ValueError(f"Meeting day must be one of {valid_days}")
        return v.lower()

    @validator("meeting_time")
    def validate_meeting_time(cls, v):
        if v:
            try:
                parts = v.split(":")
                if len(parts) != 2:
                    raise ValueError
                hour, minute = int(parts[0]), int(parts[1])
                if not (0 <= hour < 24 and 0 <= minute < 60):
                    raise ValueError
            except:
                raise ValueError("Meeting time must be in HH:MM format (24-hour)")
        return v


class CellUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    default_meeting_day: Optional[str] = None
    meeting_time: Optional[str] = None


class CellResponse(BaseModel):
    id: str
    name: str
    senior_cell_id: str
    default_meeting_day: str
    meeting_time: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN - USER MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

class UserCreate(BaseModel):
    phone: str = Field(..., description="Phone number with country code")
    name: str = Field(..., min_length=1, max_length=100)
    role: UserRole
    
    # Hierarchy assignment (optional based on role)
    zone_id: Optional[UUID] = None
    fellowship_id: Optional[UUID] = None
    senior_cell_id: Optional[UUID] = None
    cell_id: Optional[UUID] = None

    @validator("phone")
    def validate_phone(cls, v):
        if not v.startswith("+"):
            raise ValueError("Phone must start with +")
        if not v[1:].isdigit():
            raise ValueError("Phone must contain only digits after +")
        return v

    @model_validator(mode="after")
    def validate_role_hierarchy(self):
        if self.role in {UserRole.zonal_admin, UserRole.zonal_pastor} and not self.zone_id:
            raise ValueError(f"{self.role.value} must have zone_id")
        if self.role == UserRole.fellowship_pastor and not self.fellowship_id:
            raise ValueError("fellowship_pastor must have fellowship_id")
        if self.role == UserRole.senior_cell_leader and not self.senior_cell_id:
            raise ValueError("senior_cell_leader must have senior_cell_id")
        if self.role == UserRole.cell_leader and not self.cell_id:
            raise ValueError("cell_leader must have cell_id")
        return self


class UserCreateResponse(BaseModel):
    user_id: str
    phone: str
    name: str
    role: UserRole
    initial_pin: str = "123456"
    message: str


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = None
    zone_id: Optional[UUID] = None
    fellowship_id: Optional[UUID] = None
    senior_cell_id: Optional[UUID] = None
    cell_id: Optional[UUID] = None


class UserListResponse(BaseModel):
    id: str
    phone: str
    name: str
    role: UserRole
    zone_id: Optional[str]
    fellowship_id: Optional[str]
    senior_cell_id: Optional[str]
    cell_id: Optional[str]
    is_active: bool
    created_at: datetime


# ═══════════════════════════════════════════════════════════════════════════════
# REPORTS
# ═══════════════════════════════════════════════════════════════════════════════

class ActivityRecord(BaseModel):
    activity_name: str
    duration_minutes: int = 0
    handler: Optional[str] = None


class SoulWinningRecord(BaseModel):
    name: str
    phone: Optional[str] = None
    is_first_timer: bool = False
    follow_up_date: Optional[date] = None
    response: Optional[str] = None


class CellReportSubmit(BaseModel):
    cell_id: UUID
    meeting_date: date
    week_start_date: date
    week_end_date: date
    actual_meeting_day: str
    meeting_week: str = Field(..., description="Week 1-4")
    meeting_type: str = Field(..., description="Bible Study, Prayer Meeting, Evangelism, Planning")
    meeting_duration: int = Field(..., description="Minutes")
    
    # Bible class
    bible_class_teachers: List[str] = Field(default_factory=list, max_items=4)
    
    # Activities
    activities: List[ActivityRecord] = Field(default_factory=list)
    
    # Attendance
    first_timers: int = 0
    number_saved: int = 0
    filled_holy_ghost: int = 0
    total_attendance: int
    new_members: int = 0
    souls_retained: int = 0
    souls_won: int = 0
    souls_on_tracker: int = 0
    
    # Finances
    finance_oblation: float = 0.0
    finance_offerings: float = 0.0
    finance_tithes: float = 0.0
    finance_thanksgiving: float = 0.0
    finance_seed: float = 0.0
    finance_partnership: float = 0.0
    finance_first_fruits: float = 0.0
    finance_collected_by: Optional[str] = None
    
    # Text fields
    testimonies: Optional[str] = None
    monthly_plans: Optional[str] = None
    challenges: Optional[str] = None
    soul_winning_records: List[SoulWinningRecord] = Field(default_factory=list)
    
    # Pastor section
    pastors_remarks: Optional[str] = None
    other_info: Optional[str] = None
    
    # Photos
    photo_urls: List[str] = Field(default_factory=list, max_items=2)


class CellReportResponse(BaseModel):
    id: str
    cell_id: str
    status: CellStatus
    submitted_at: Optional[datetime]
    submission_deadline: datetime
    message: str

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARDS
# ═══════════════════════════════════════════════════════════════════════════════

class CellStatus(BaseModel):
    cell_id: str
    cell_name: str
    leader_name: Optional[str]
    status: str
    attendance: int
    souls_won: int
    finance: float


class SeniorCellDashboard(BaseModel):
    dashboard_type: str = "senior_cell_leader"
    senior_cell_id: str
    senior_cell_name: str
    week_start: str
    week_end: str
    total_cells: int
    cells_reported: int
    submission_rate_percent: float
    total_attendance: int
    total_souls_won: int
    total_finances: float
    cells: List[CellStatus]


class FellowshipDashboard(BaseModel):
    dashboard_type: str = "fellowship_pastor"
    fellowship_id: str
    fellowship_name: str
    location: Optional[str]
    week_start: str
    week_end: str
    total_cells: int
    cells_reported: int
    submission_rate_percent: float
    total_attendance: int
    total_souls_won: int
    total_finances: float


class ZoneDashboard(BaseModel):
    dashboard_type: str = "zonal_admin"
    zone_id: str
    zone_name: str
    week_start: str
    week_end: str
    total_cells: int
    cells_reported: int
    submission_rate_percent: float
    total_attendance: int
    total_souls_won: int
    total_finances: float














