# schemas.py - Pydantic Models for API Validation

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from uuid import UUID
import re

# ═══════════════════════════════════════════════════════════════════════════════
# AUTH SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    """User login request"""
    phone: str = Field(..., description="Phone number (e.g., +237690123456)")
    pin: str = Field(..., min_length=6, max_length=6, description="6-digit PIN")

    @validator('phone')
    def validate_phone(cls, v):
        if not re.match(r'^\+\d{10,15}$', v):
            raise ValueError('Invalid phone format (use +237...)')
        return v

    @validator('pin')
    def validate_pin(cls, v):
        if not v.isdigit():
            raise ValueError('PIN must be 6 digits')
        return v


class LoginResponse(BaseModel):
    """User login response"""
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGc...",
                "token_type": "bearer",
                "user": {
                    "id": "uuid",
                    "phone": "+237690123456",
                    "name": "John Doe",
                    "role": "cell_leader",
                    "cell_id": "uuid"
                }
            }
        }


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: UUID  # user_id
    exp: int   # expiration timestamp


# ═══════════════════════════════════════════════════════════════════════════════
# CELL REPORT SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class ActivityRecord(BaseModel):
    """Activity within a meeting"""
    type: str = Field(..., description="e.g., prayers, praise_worship, bible_study, etc.")
    duration: int = Field(..., gt=0, le=180, description="Duration in minutes")
    handler: Optional[str] = Field(None, description="Person who handled this activity")


class SoulWinningRecord(BaseModel):
    """Soul winning record"""
    name: str = Field(..., max_length=100)
    phone: str = Field(..., max_length=20)
    is_first_timer: bool
    follow_up_date: date
    response: str = Field(..., max_length=200, description="How they responded")


class CellReportSubmit(BaseModel):
    """Submit a cell report"""
    cell_id: UUID
    meeting_date: date
    week_start_date: date
    week_end_date: date
    actual_meeting_day: str

    # Meeting Details
    meeting_week: str = Field(..., max_length=10)
    meeting_type: str = Field(..., max_length=50)
    meeting_duration: int = Field(..., gt=0, le=300)
    bible_class_teachers: List[str] = Field(default_factory=list, max_items=4)
    activities: List[ActivityRecord] = Field(default_factory=list)

    # Attendance
    first_timers: int = Field(default=0, ge=0)
    number_saved: int = Field(default=0, ge=0)
    filled_holy_ghost: int = Field(default=0, ge=0)
    total_attendance: int = Field(default=0, ge=0)
    new_members: int = Field(default=0, ge=0)
    souls_retained: int = Field(default=0, ge=0)
    souls_won: int = Field(default=0, ge=0)
    souls_on_tracker: int = Field(default=0, ge=0)

    # Finances
    finance_oblation: float = Field(default=0, ge=0)
    finance_offerings: float = Field(default=0, ge=0)
    finance_tithes: float = Field(default=0, ge=0)
    finance_thanksgiving: float = Field(default=0, ge=0)
    finance_seed: float = Field(default=0, ge=0)
    finance_partnership: float = Field(default=0, ge=0)
    finance_first_fruits: float = Field(default=0, ge=0)
    finance_collected_by: Optional[str] = Field(None, max_length=100)

    # Text Fields
    testimonies: Optional[str] = Field(None, max_length=2000)
    monthly_plans: Optional[str] = Field(None, max_length=2000)
    challenges: Optional[str] = Field(None, max_length=2000)

    # Soul Winning
    soul_winning_records: List[SoulWinningRecord] = Field(default_factory=list)

    # Optional
    pastors_remarks: Optional[str] = Field(None, max_length=2000)
    other_info: Optional[str] = Field(None, max_length=2000)
    photo_urls: List[str] = Field(default_factory=list, max_items=2)

    @validator('total_attendance')
    def validate_attendance(cls, v, values):
        if 'first_timers' in values and v < values['first_timers']:
            raise ValueError('total_attendance must be >= first_timers')
        return v


class CellReportResponse(BaseModel):
    """Cell report response"""
    id: UUID
    cell_id: UUID
    status: str
    submitted_at: Optional[datetime]
    submission_deadline: datetime
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "uuid",
                "cell_id": "uuid",
                "status": "SUBMITTED",
                "submitted_at": "2026-03-13T15:00:00Z",
                "submission_deadline": "2026-03-16T09:00:00Z",
                "message": "Report submitted on time!"
            }
        }


class CellReportDetail(BaseModel):
    """Full cell report details"""
    id: UUID
    cell_id: UUID
    submitted_by: UUID
    meeting_date: date
    week_start_date: date
    week_end_date: date
    status: str
    submitted_at: Optional[datetime]
    submission_deadline: datetime

    # All report fields
    meeting_week: Optional[str]
    meeting_type: Optional[str]
    meeting_duration: Optional[int]
    bible_class_teachers: List[str]
    activities: List[Dict[str, Any]]

    first_timers: int
    number_saved: int
    filled_holy_ghost: int
    total_attendance: int
    new_members: int
    souls_retained: int
    souls_won: int
    souls_on_tracker: int

    finance_oblation: float
    finance_offerings: float
    finance_tithes: float
    finance_thanksgiving: float
    finance_seed: float
    finance_partnership: float
    finance_first_fruits: float
    finance_total: float
    finance_collected_by: Optional[str]

    testimonies: Optional[str]
    monthly_plans: Optional[str]
    challenges: Optional[str]

    soul_winning_records: List[Dict[str, Any]]
    photo_urls: List[str]
    pastors_remarks: Optional[str]
    other_info: Optional[str]

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# USER SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class UserCreate(BaseModel):
    """Create new user (admin only)"""
    phone: str = Field(..., description="Phone number (e.g., +237690123456)")
    name: str = Field(..., max_length=100)
    role: str = Field(..., description="cell_leader, senior_cell_leader, fellowship_pastor, etc.")
    cell_id: Optional[UUID] = None
    senior_cell_id: Optional[UUID] = None
    fellowship_id: Optional[UUID] = None
    zone_id: Optional[UUID] = None

    @validator('phone')
    def validate_phone(cls, v):
        if not re.match(r'^\+\d{10,15}$', v):
            raise ValueError('Invalid phone format')
        return v

    @validator('role')
    def validate_role(cls, v):
        valid_roles = ['cell_leader', 'senior_cell_leader', 'fellowship_pastor', 'zonal_pastor', 'zonal_admin', 'system_admin']
        if v not in valid_roles:
            raise ValueError(f'Invalid role: {v}')
        return v


class UserCreateResponse(BaseModel):
    """Response after creating user"""
    user_id: UUID
    phone: str
    name: str
    role: str
    initial_pin: str
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "uuid",
                "phone": "+237690123456",
                "name": "John Doe",
                "role": "cell_leader",
                "initial_pin": "123456",
                "message": "User created. Share phone and PIN with leader."
            }
        }


class UserProfile(BaseModel):
    """User profile"""
    id: UUID
    phone: str
    name: str
    role: str
    cell_id: Optional[UUID]
    senior_cell_id: Optional[UUID]
    fellowship_id: Optional[UUID]
    zone_id: Optional[UUID]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class CellStatus(BaseModel):
    """Cell submission status for dashboard"""
    id: UUID
    name: str
    leader_name: Optional[str]
    status: str
    last_report_date: Optional[date]
    total_attendance: int
    souls_won: int


class SeniorCellDashboard(BaseModel):
    """Senior Cell Leader dashboard data"""
    senior_cell_id: UUID
    senior_cell_name: str
    fellowship_id: UUID
    total_cells: int
    cells_reported: int
    cells_overdue: int
    submission_rate_percent: Optional[float]
    total_attendance: int
    total_souls_won: int
    cells: List[CellStatus] = []

    class Config:
        json_schema_extra = {
            "example": {
                "senior_cell_id": "uuid",
                "senior_cell_name": "Senior Cell A",
                "fellowship_id": "uuid",
                "total_cells": 8,
                "cells_reported": 6,
                "cells_overdue": 0,
                "submission_rate_percent": 75,
                "total_attendance": 245,
                "total_souls_won": 5
            }
        }


class FellowshipDashboard(BaseModel):
    """Fellowship Pastor dashboard data"""
    fellowship_id: UUID
    fellowship_name: str
    location: Optional[str]
    zone_id: UUID
    total_cells: int
    cells_reported: int
    submission_rate_percent: Optional[float]
    total_attendance: int
    total_souls_won: int
    total_first_timers: int
    total_finances: float

    class Config:
        json_schema_extra = {
            "example": {
                "fellowship_id": "uuid",
                "fellowship_name": "Bamenda Central",
                "location": "Bamenda",
                "zone_id": "uuid",                # Python bytecode caches
        
                "total_cells": 35,
                "cells_reported": 28,
                "submission_rate_percent": 80,
                "total_attendance": 1250,
                "total_souls_won": 25,
                "total_first_timers": 50,
                "total_finances": 625000
            }
        }


class ZoneDashboard(BaseModel):
    """Zone Admin dashboard data"""
    zone_id: UUID
    zone_name: str
    region_id: UUID
    total_cells: int
    cells_reported: int
    submission_rate_percent: Optional[float]
    total_attendance: int
    total_souls_won: int
    total_first_timers: int
    total_finances: float

    class Config:
        json_schema_extra = {
            "example": {
                "zone_id": "uuid",
                "zone_name": "Zone B",
                "region_id": "uuid",
                "total_cells": 102,
                "cells_reported": 85,
                "submission_rate_percent": 83,
                "total_attendance": 4500,
                "total_souls_won": 100,
                "total_first_timers": 200,
                "total_finances": 2500000
            }
        }


# ═══════════════════════════════════════════════════════════════════════════════
# ERROR SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None

    class Config:
        json_json_schema_extra = {
            "example": {
                "error": "validation_error",
                "message": "totalAttendance must be >= firstTimers",
                "details": None
            }
        }