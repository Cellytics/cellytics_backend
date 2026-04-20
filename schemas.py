# schemas.py - Pydantic models for request/response validation

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from uuid import UUID
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class UserRole(str, Enum):
    system_admin = "system_admin"
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

    @validator("role", "zone_id", "fellowship_id", "senior_cell_id", "cell_id", always=True)
    def validate_role_hierarchy(cls, v, values):
        role = values.get("role")
        
        if role == UserRole.zonal_admin:
            if not values.get("zone_id"):
                raise ValueError("zonal_admin must have zone_id")
        elif role == UserRole.fellowship_pastor:
            if not values.get("fellowship_id"):
                raise ValueError("fellowship_pastor must have fellowship_id")
        elif role == UserRole.senior_cell_leader:
            if not values.get("senior_cell_id"):
                raise ValueError("senior_cell_leader must have senior_cell_id")
        elif role == UserRole.cell_leader:
            if not values.get("cell_id"):
                raise ValueError("cell_leader must have cell_id")
        
        return v


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

















# # schemas.py - Pydantic Models for API Validation

# from pydantic import BaseModel, Field, validator
# from typing import Optional, List, Dict, Any
# from datetime import datetime, date, time
# from uuid import UUID
# import re

# # ═══════════════════════════════════════════════════════════════════════════════
# # AUTH SCHEMAS
# # ═══════════════════════════════════════════════════════════════════════════════

# class LoginRequest(BaseModel):
#     """User login request"""
#     phone: str = Field(..., description="Phone number (e.g., +237690123456)")
#     pin: str = Field(..., min_length=6, max_length=6, description="6-digit PIN")

#     @validator('phone')
#     def validate_phone(cls, v):
#         if not re.match(r'^\+\d{10,15}$', v):
#             raise ValueError('Invalid phone format (use +237...)')
#         return v

#     @validator('pin')
#     def validate_pin(cls, v):
#         if not v.isdigit():
#             raise ValueError('PIN must be 6 digits')
#         return v


# class LoginResponse(BaseModel):
#     """User login response"""
#     access_token: str
#     token_type: str = "bearer"
#     user: Dict[str, Any]

#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "access_token": "eyJhbGc...",
#                 "token_type": "bearer",
#                 "user": {
#                     "id": "uuid",
#                     "phone": "+237690123456",
#                     "name": "John Doe",
#                     "role": "cell_leader",
#                     "cell_id": "uuid"
#                 }
#             }
#         }


# class TokenPayload(BaseModel):
#     """JWT token payload"""
#     sub: UUID  # user_id
#     exp: int   # expiration timestamp


# # ═══════════════════════════════════════════════════════════════════════════════
# # CELL REPORT SCHEMAS
# # ═══════════════════════════════════════════════════════════════════════════════

# class ActivityRecord(BaseModel):
#     """Activity within a meeting"""
#     type: str = Field(..., description="e.g., prayers, praise_worship, bible_study, etc.")
#     duration: int = Field(..., gt=0, le=180, description="Duration in minutes")
#     handler: Optional[str] = Field(None, description="Person who handled this activity")


# class SoulWinningRecord(BaseModel):
#     """Soul winning record"""
#     name: str = Field(..., max_length=100)
#     phone: str = Field(..., max_length=20)
#     is_first_timer: bool
#     follow_up_date: date
#     response: str = Field(..., max_length=200, description="How they responded")


# class CellReportSubmit(BaseModel):
#     """Submit a cell report"""
#     cell_id: UUID
#     meeting_date: date
#     week_start_date: date
#     week_end_date: date
#     actual_meeting_day: str

#     # Meeting Details
#     meeting_week: str = Field(..., max_length=10)
#     meeting_type: str = Field(..., max_length=50)
#     meeting_duration: int = Field(..., gt=0, le=300)
#     bible_class_teachers: List[str] = Field(default_factory=list, max_items=4)
#     activities: List[ActivityRecord] = Field(default_factory=list)

#     # Attendance
#     first_timers: int = Field(default=0, ge=0)
#     number_saved: int = Field(default=0, ge=0)
#     filled_holy_ghost: int = Field(default=0, ge=0)
#     total_attendance: int = Field(default=0, ge=0)
#     new_members: int = Field(default=0, ge=0)
#     souls_retained: int = Field(default=0, ge=0)
#     souls_won: int = Field(default=0, ge=0)
#     souls_on_tracker: int = Field(default=0, ge=0)

#     # Finances
#     finance_oblation: float = Field(default=0, ge=0)
#     finance_offerings: float = Field(default=0, ge=0)
#     finance_tithes: float = Field(default=0, ge=0)
#     finance_thanksgiving: float = Field(default=0, ge=0)
#     finance_seed: float = Field(default=0, ge=0)
#     finance_partnership: float = Field(default=0, ge=0)
#     finance_first_fruits: float = Field(default=0, ge=0)
#     finance_collected_by: Optional[str] = Field(None, max_length=100)

#     # Text Fields
#     testimonies: Optional[str] = Field(None, max_length=2000)
#     monthly_plans: Optional[str] = Field(None, max_length=2000)
#     challenges: Optional[str] = Field(None, max_length=2000)

#     # Soul Winning
#     soul_winning_records: List[SoulWinningRecord] = Field(default_factory=list)

#     # Optional
#     pastors_remarks: Optional[str] = Field(None, max_length=2000)
#     other_info: Optional[str] = Field(None, max_length=2000)
#     photo_urls: List[str] = Field(default_factory=list, max_items=2)

#     @validator('total_attendance')
#     def validate_attendance(cls, v, values):
#         if 'first_timers' in values and v < values['first_timers']:
#             raise ValueError('total_attendance must be >= first_timers')
#         return v


# class CellReportResponse(BaseModel):
#     """Cell report response"""
#     id: UUID
#     cell_id: UUID
#     status: str
#     submitted_at: Optional[datetime]
#     submission_deadline: datetime
#     message: str

#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "id": "uuid",
#                 "cell_id": "uuid",
#                 "status": "SUBMITTED",
#                 "submitted_at": "2026-03-13T15:00:00Z",
#                 "submission_deadline": "2026-03-16T09:00:00Z",
#                 "message": "Report submitted on time!"
#             }
#         }


# class CellReportDetail(BaseModel):
#     """Full cell report details"""
#     id: UUID
#     cell_id: UUID
#     submitted_by: UUID
#     meeting_date: date
#     week_start_date: date
#     week_end_date: date
#     status: str
#     submitted_at: Optional[datetime]
#     submission_deadline: datetime

#     # All report fields
#     meeting_week: Optional[str]
#     meeting_type: Optional[str]
#     meeting_duration: Optional[int]
#     bible_class_teachers: List[str]
#     activities: List[Dict[str, Any]]

#     first_timers: int
#     number_saved: int
#     filled_holy_ghost: int
#     total_attendance: int
#     new_members: int
#     souls_retained: int
#     souls_won: int
#     souls_on_tracker: int

#     finance_oblation: float
#     finance_offerings: float
#     finance_tithes: float
#     finance_thanksgiving: float
#     finance_seed: float
#     finance_partnership: float
#     finance_first_fruits: float
#     finance_total: float
#     finance_collected_by: Optional[str]

#     testimonies: Optional[str]
#     monthly_plans: Optional[str]
#     challenges: Optional[str]

#     soul_winning_records: List[Dict[str, Any]]
#     photo_urls: List[str]
#     pastors_remarks: Optional[str]
#     other_info: Optional[str]

#     created_at: datetime
#     updated_at: datetime

#     class Config:
#         from_attributes = True


# # ═══════════════════════════════════════════════════════════════════════════════
# # USER SCHEMAS
# # ═══════════════════════════════════════════════════════════════════════════════

# class UserCreate(BaseModel):
#     """Create new user (admin only)"""
#     phone: str = Field(..., description="Phone number (e.g., +237690123456)")
#     name: str = Field(..., max_length=100)
#     role: str = Field(..., description="cell_leader, senior_cell_leader, fellowship_pastor, etc.")
#     cell_id: Optional[UUID] = None
#     senior_cell_id: Optional[UUID] = None
#     fellowship_id: Optional[UUID] = None
#     zone_id: Optional[UUID] = None

#     @validator('phone')
#     def validate_phone(cls, v):
#         if not re.match(r'^\+\d{10,15}$', v):
#             raise ValueError('Invalid phone format')
#         return v

#     @validator('role')
#     def validate_role(cls, v):
#         valid_roles = ['cell_leader', 'senior_cell_leader', 'fellowship_pastor', 'zonal_pastor', 'zonal_admin', 'system_admin']
#         if v not in valid_roles:
#             raise ValueError(f'Invalid role: {v}')
#         return v


# class UserCreateResponse(BaseModel):
#     """Response after creating user"""
#     user_id: UUID
#     phone: str
#     name: str
#     role: str
#     initial_pin: str
#     message: str

#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "user_id": "uuid",
#                 "phone": "+237690123456",
#                 "name": "John Doe",
#                 "role": "cell_leader",
#                 "initial_pin": "123456",
#                 "message": "User created. Share phone and PIN with leader."
#             }
#         }


# class UserProfile(BaseModel):
#     """User profile"""
#     id: UUID
#     phone: str
#     name: str
#     role: str
#     cell_id: Optional[UUID]
#     senior_cell_id: Optional[UUID]
#     fellowship_id: Optional[UUID]
#     zone_id: Optional[UUID]
#     is_active: bool
#     created_at: datetime
#     last_login: Optional[datetime]

#     class Config:
#         from_attributes = True


# # ═══════════════════════════════════════════════════════════════════════════════
# # DASHBOARD SCHEMAS
# # ═══════════════════════════════════════════════════════════════════════════════

# class CellStatus(BaseModel):
#     """Cell submission status for dashboard"""
#     id: UUID
#     name: str
#     leader_name: Optional[str]
#     status: str
#     last_report_date: Optional[date]
#     total_attendance: int
#     souls_won: int


# class SeniorCellDashboard(BaseModel):
#     """Senior Cell Leader dashboard data"""
#     senior_cell_id: UUID
#     senior_cell_name: str
#     fellowship_id: UUID
#     total_cells: int
#     cells_reported: int
#     cells_overdue: int
#     submission_rate_percent: Optional[float]
#     total_attendance: int
#     total_souls_won: int
#     cells: List[CellStatus] = []

#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "senior_cell_id": "uuid",
#                 "senior_cell_name": "Senior Cell A",
#                 "fellowship_id": "uuid",
#                 "total_cells": 8,
#                 "cells_reported": 6,
#                 "cells_overdue": 0,
#                 "submission_rate_percent": 75,
#                 "total_attendance": 245,
#                 "total_souls_won": 5
#             }
#         }


# class FellowshipDashboard(BaseModel):
#     """Fellowship Pastor dashboard data"""
#     fellowship_id: UUID
#     fellowship_name: str
#     location: Optional[str]
#     zone_id: UUID
#     total_cells: int
#     cells_reported: int
#     submission_rate_percent: Optional[float]
#     total_attendance: int
#     total_souls_won: int
#     total_first_timers: int
#     total_finances: float

#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "fellowship_id": "uuid",
#                 "fellowship_name": "Bamenda Central",
#                 "location": "Bamenda",
#                 "zone_id": "uuid",                # Python bytecode caches
        
#                 "total_cells": 35,
#                 "cells_reported": 28,
#                 "submission_rate_percent": 80,
#                 "total_attendance": 1250,
#                 "total_souls_won": 25,
#                 "total_first_timers": 50,
#                 "total_finances": 625000
#             }
#         }


# class ZoneDashboard(BaseModel):
#     """Zone Admin dashboard data"""
#     zone_id: UUID
#     zone_name: str
#     region_id: UUID
#     total_cells: int
#     cells_reported: int
#     submission_rate_percent: Optional[float]
#     total_attendance: int
#     total_souls_won: int
#     total_first_timers: int
#     total_finances: float

#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "zone_id": "uuid",
#                 "zone_name": "Zone B",
#                 "region_id": "uuid",
#                 "total_cells": 102,
#                 "cells_reported": 85,
#                 "submission_rate_percent": 83,
#                 "total_attendance": 4500,
#                 "total_souls_won": 100,
#                 "total_first_timers": 200,
#                 "total_finances": 2500000
#             }
#         }


# # ═══════════════════════════════════════════════════════════════════════════════
# # ERROR SCHEMAS
# # ═══════════════════════════════════════════════════════════════════════════════

# class ErrorResponse(BaseModel):
#     """Standard error response"""
#     error: str
#     message: str
#     details: Optional[Dict[str, Any]] = None

#     class Config:
#         json_json_schema_extra = {
#             "example": {
#                 "error": "validation_error",
#                 "message": "totalAttendance must be >= firstTimers",
#                 "details": None
#             }
#         }