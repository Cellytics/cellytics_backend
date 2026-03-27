# models.py - SQLAlchemy ORM Models
# Complete data model for all 9 tables

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Date, Time, 
    Numeric, Text, ForeignKey, CheckConstraint, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, date, time
import uuid

Base = declarative_base()

# ═══════════════════════════════════════════════════════════════════════════════
# TABLE 1: REGIONS
# ═══════════════════════════════════════════════════════════════════════════════

class Region(Base):
    """Top-level organizational region (e.g., East & Central Africa Region)"""
    __tablename__ = "regions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    zones = relationship("Zone", back_populates="region", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Region(name={self.name})>"


# ═══════════════════════════════════════════════════════════════════════════════
# TABLE 2: ZONES
# ═══════════════════════════════════════════════════════════════════════════════

class Zone(Base):
    """Zone (led by Zonal Pastor, coordinated by Zonal Admin)"""
    __tablename__ = "zones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    region_id = Column(UUID(as_uuid=True), ForeignKey("regions.id", ondelete="CASCADE"), nullable=False)
    zonal_pastor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    zonal_admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Unique constraint
    __table_args__ = (UniqueConstraint('name', 'region_id', name='uq_zone_name_region'),)

    # Relationships
    region = relationship("Region", back_populates="zones")
    fellowships = relationship("Fellowship", back_populates="zone", cascade="all, delete-orphan")
    zonal_pastor = relationship("User", foreign_keys=[zonal_pastor_id], back_populates="zones_as_pastor")
    zonal_admin = relationship("User", foreign_keys=[zonal_admin_id], back_populates="zones_as_admin")

    def __repr__(self):
        return f"<Zone(name={self.name})>"


# ═══════════════════════════════════════════════════════════════════════════════
# TABLE 3: FELLOWSHIPS
# ═══════════════════════════════════════════════════════════════════════════════

class Fellowship(Base):
    """Fellowship (congregation led by Fellowship Pastor)"""
    __tablename__ = "fellowships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    location = Column(String(200), nullable=True)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False)
    pastor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Unique constraint
    __table_args__ = (UniqueConstraint('name', 'zone_id', name='uq_fellowship_name_zone'),)

    # Relationships
    zone = relationship("Zone", back_populates="fellowships")
    senior_cells = relationship("SeniorCell", back_populates="fellowship", cascade="all, delete-orphan")
    pastor = relationship("User", back_populates="fellowships_led")

    def __repr__(self):
        return f"<Fellowship(name={self.name}, location={self.location})>"


# ═══════════════════════════════════════════════════════════════════════════════
# TABLE 4: SENIOR_CELLS
# ═══════════════════════════════════════════════════════════════════════════════

class SeniorCell(Base):
    """Senior Cell (supervisor of 5-10 cells)"""
    __tablename__ = "senior_cells"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    fellowship_id = Column(UUID(as_uuid=True), ForeignKey("fellowships.id", ondelete="CASCADE"), nullable=False)
    leader_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    leader_name = Column(String(100), nullable=True)  # Denormalized
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Unique constraint
    __table_args__ = (UniqueConstraint('name', 'fellowship_id', name='uq_senior_cell_name_fellowship'),)

    # Relationships
    fellowship = relationship("Fellowship", back_populates="senior_cells")
    cells = relationship("Cell", back_populates="senior_cell", cascade="all, delete-orphan")
    leader = relationship("User", back_populates="senior_cells_led")

    def __repr__(self):
        return f"<SeniorCell(name={self.name})>"


# ═══════════════════════════════════════════════════════════════════════════════
# TABLE 5: CELLS
# ═══════════════════════════════════════════════════════════════════════════════

class Cell(Base):
    """Cell (small group led by Cell Leader)"""
    __tablename__ = "cells"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    senior_cell_id = Column(UUID(as_uuid=True), ForeignKey("senior_cells.id", ondelete="CASCADE"), nullable=False)
    leader_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    leader_name = Column(String(100), nullable=True)  # Denormalized
    default_meeting_day = Column(String(20), default="monday", nullable=False)
    actual_meeting_day = Column(String(20), nullable=True)
    meeting_time = Column(Time, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Constraint: valid day of week
    __table_args__ = (
        UniqueConstraint('name', 'senior_cell_id', name='uq_cell_name_senior_cell'),
        CheckConstraint("default_meeting_day IN ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')", name='check_default_meeting_day'),
    )

    # Relationships
    senior_cell = relationship("SeniorCell", back_populates="cells")
    leader = relationship("User", back_populates="cells_led")
    cell_reports = relationship("CellReport", back_populates="cell", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Cell(name={self.name}, day={self.default_meeting_day})>"


# ═══════════════════════════════════════════════════════════════════════════════
# TABLE 6: USERS
# ═══════════════════════════════════════════════════════════════════════════════

class User(Base):
    """User (Cell Leader, Senior CL, Pastor, Admin)"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = Column(String(20), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    pin_hash = Column(String(255), nullable=False)
    role = Column(
        String(50),
        nullable=False,
        default="cell_leader",
    )
    cell_id = Column(UUID(as_uuid=True), ForeignKey("cells.id", ondelete="SET NULL"), nullable=True)
    senior_cell_id = Column(UUID(as_uuid=True), ForeignKey("senior_cells.id", ondelete="SET NULL"), nullable=True)
    fellowship_id = Column(UUID(as_uuid=True), ForeignKey("fellowships.id", ondelete="SET NULL"), nullable=True)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="SET NULL"), nullable=True)
    fcm_token = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Constraint: valid role
    __table_args__ = (
        CheckConstraint(
            "role IN ('cell_leader', 'senior_cell_leader', 'fellowship_pastor', 'zonal_pastor', 'zonal_admin', 'system_admin')",
            name='check_user_role'
        ),
    )

    # Relationships
    cell = relationship("Cell", foreign_keys=[cell_id], back_populates="leader")
    senior_cell = relationship("SeniorCell", foreign_keys=[senior_cell_id], back_populates="leader")
    cells_led = relationship("Cell", foreign_keys=[Cell.leader_id], back_populates="leader", viewonly=True)
    senior_cells_led = relationship("SeniorCell", foreign_keys=[SeniorCell.leader_id], back_populates="leader", viewonly=True)
    fellowship = relationship("Fellowship", foreign_keys=[fellowship_id], back_populates="pastor")
    fellowships_led = relationship("Fellowship", foreign_keys=[Fellowship.pastor_id], back_populates="pastor", viewonly=True)
    zone = relationship("Zone", foreign_keys=[zone_id], back_populates=None)
    zones_as_pastor = relationship("Zone", foreign_keys=[Zone.zonal_pastor_id], back_populates="zonal_pastor", viewonly=True)
    zones_as_admin = relationship("Zone", foreign_keys=[Zone.zonal_admin_id], back_populates="zonal_admin", viewonly=True)
    cell_reports = relationship("CellReport", back_populates="submitted_by", cascade="all, delete-orphan")
    sync_queue_items = relationship("SyncQueue", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(phone={self.phone}, name={self.name}, role={self.role})>"


# ═══════════════════════════════════════════════════════════════════════════════
# TABLE 7: CELL_REPORTS (CORE TABLE)
# ═══════════════════════════════════════════════════════════════════════════════

class CellReport(Base):
    """Cell Report (weekly submission with all booklet data)"""
    __tablename__ = "cell_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cell_id = Column(UUID(as_uuid=True), ForeignKey("cells.id", ondelete="CASCADE"), nullable=False)
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    # Timing & Status
    meeting_date = Column(Date, nullable=False)
    week_start_date = Column(Date, nullable=False)
    week_end_date = Column(Date, nullable=False)
    actual_meeting_day = Column(String(20), nullable=True)
    submission_deadline = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), default="draft", nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    synced_from_offline = Column(Boolean, default=False)

    # Meeting Details (Page 1)
    meeting_week = Column(String(10), nullable=True)
    meeting_type = Column(String(50), nullable=True)
    meeting_duration = Column(Integer, nullable=True)
    bible_class_teachers = Column(JSONB, default=[], nullable=False)
    activities = Column(JSONB, default=[], nullable=False)

    # Attendance (Page 1)
    first_timers = Column(Integer, default=0)
    number_saved = Column(Integer, default=0)
    filled_holy_ghost = Column(Integer, default=0)
    total_attendance = Column(Integer, default=0)
    new_members = Column(Integer, default=0)
    souls_retained = Column(Integer, default=0)
    souls_won = Column(Integer, default=0)
    souls_on_tracker = Column(Integer, default=0)

    # Finances (Page 2)
    finance_oblation = Column(Numeric(12, 2), default=0)
    finance_offerings = Column(Numeric(12, 2), default=0)
    finance_tithes = Column(Numeric(12, 2), default=0)
    finance_thanksgiving = Column(Numeric(12, 2), default=0)
    finance_seed = Column(Numeric(12, 2), default=0)
    finance_partnership = Column(Numeric(12, 2), default=0)
    finance_first_fruits = Column(Numeric(12, 2), default=0)
    finance_total = Column(Numeric(12, 2), default=0)
    finance_collected_by = Column(String(100), nullable=True)

    # Text Fields (Page 2)
    testimonies = Column(Text, nullable=True)
    monthly_plans = Column(Text, nullable=True)
    challenges = Column(Text, nullable=True)

    # Soul Winning (Page 3)
    soul_winning_records = Column(JSONB, default=[], nullable=False)

    # Optional (Page 4)
    pastors_remarks = Column(Text, nullable=True)
    other_info = Column(Text, nullable=True)
    photo_urls = Column(JSONB, default=[], nullable=False)

    # Audit
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraint: only one report per cell per week
    __table_args__ = (
        UniqueConstraint('cell_id', 'week_start_date', name='uq_cell_week'),
        CheckConstraint("status IN ('draft', 'submitted', 'late', 'overdue')", name='check_status'),
    )

    # Relationships
    cell = relationship("Cell", back_populates="cell_reports")
    submitted_by_user = relationship("User", back_populates="cell_reports")

    def __repr__(self):
        return f"<CellReport(cell={self.cell_id}, week={self.week_start_date}, status={self.status})>"


# ═══════════════════════════════════════════════════════════════════════════════
# TABLE 8: SYNC_QUEUE
# ═══════════════════════════════════════════════════════════════════════════════

class SyncQueue(Base):
    """Offline submissions queue"""
    __tablename__ = "sync_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    report_data = Column(JSONB, nullable=False)
    retry_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="sync_queue_items")

    def __repr__(self):
        return f"<SyncQueue(user={self.user_id}, retries={self.retry_count})>"


# ═══════════════════════════════════════════════════════════════════════════════
# TABLE 9: NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════════

class Notification(Base):
    """Push notification history"""
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)
    fcm_token = Column(String(255), nullable=True)
    fcm_message_id = Column(String(255), nullable=True)
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Constraint: valid notification type
    __table_args__ = (
        CheckConstraint(
            "type IN ('submission_reminder', 'overdue_alert', 'manual_nudge', 'meeting_reminder', 'late_alert')",
            name='check_notification_type'
        ),
    )

    # Relationships
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(user={self.user_id}, type={self.type})>"