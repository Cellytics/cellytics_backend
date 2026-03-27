# dashboards.py - Dashboard Endpoints (Add these to main.py or create as separate file)

from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from datetime import datetime, date, timedelta
from uuid import UUID
from typing import Optional, List

from database import get_session
from models import (
    User, Cell, CellReport, Zone, Fellowship, SeniorCell,
    Notification
)
from schemas import (
    SeniorCellDashboard, FellowshipDashboard, ZoneDashboard,
    CellStatus, CellReportDetail
)
from auth import decode_token

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: Get current user from token
# ═══════════════════════════════════════════════════════════════════════════════

async def get_current_user(
    authorization: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
) -> User:
    """Extract user from Authorization header"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authorization header",
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError
    except (ValueError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    result = await session.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: Get this week's date range
# ═══════════════════════════════════════════════════════════════════════════════

def get_current_week():
    """Get current week's Monday and Sunday"""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: Senior Cell Leader Dashboard
# ═══════════════════════════════════════════════════════════════════════════════

async def get_senior_cell_dashboard(
    senior_cell_id: UUID,
    authorization: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """
    Senior Cell Leader dashboard
    Shows all cells under this senior cell with submission status
    """
    current_user = await get_current_user(authorization, session)

    # Get senior cell
    result = await session.execute(
        select(SeniorCell).where(SeniorCell.id == senior_cell_id)
    )
    senior_cell = result.scalar_one_or_none()

    if not senior_cell:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Senior cell not found",
        )

    # Check access: must be senior cell leader, fellowship pastor, or zonal admin
    if (
        current_user.role == "senior_cell_leader" and
        current_user.senior_cell_id != senior_cell_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this senior cell",
        )

    # Get this week's boundaries
    week_start, week_end = get_current_week()

    # Get all cells in this senior cell
    result = await session.execute(
        select(Cell).where(
            Cell.senior_cell_id == senior_cell_id,
            Cell.is_active == True
        )
    )
    cells = result.scalars().all()

    # Get all reports for this week
    result = await session.execute(
        select(CellReport).where(
            CellReport.senior_cell_id.in_([c.id for c in cells]),
            CellReport.week_start_date == week_start
        )
    )
    reports = {r.cell_id: r for r in result.scalars().all()}

    # Build cell status list
    cell_statuses = []
    total_attendance = 0
    total_souls_won = 0

    for cell in cells:
        report = reports.get(cell.id)
        status_val = report.status if report else "OVERDUE"
        last_report_date = report.submitted_at.date() if report and report.submitted_at else None

        cell_statuses.append(
            CellStatus(
                id=cell.id,
                name=cell.name,
                leader_name=cell.leader_name,
                status=status_val,
                last_report_date=last_report_date,
                total_attendance=report.total_attendance if report else 0,
                souls_won=report.souls_won if report else 0,
            )
        )

        if report:
            total_attendance += report.total_attendance or 0
            total_souls_won += report.souls_won or 0

    # Calculate submission rate
    cells_reported = len([r for r in reports.values()])
    submission_rate = (cells_reported / len(cells) * 100) if cells else 0

    return SeniorCellDashboard(
        senior_cell_id=senior_cell.id,
        senior_cell_name=senior_cell.name,
        fellowship_id=senior_cell.fellowship_id,
        total_cells=len(cells),
        cells_reported=cells_reported,
        cells_overdue=len([c for c in cell_statuses if c.status == "OVERDUE"]),
        submission_rate_percent=round(submission_rate, 1),
        total_attendance=total_attendance,
        total_souls_won=total_souls_won,
        cells=cell_statuses,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: Fellowship Pastor Dashboard
# ═══════════════════════════════════════════════════════════════════════════════

async def get_fellowship_dashboard(
    fellowship_id: UUID,
    authorization: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """
    Fellowship Pastor dashboard
    Shows all senior cells with aggregated stats
    """
    current_user = await get_current_user(authorization, session)

    # Get fellowship
    result = await session.execute(
        select(Fellowship).where(Fellowship.id == fellowship_id)
    )
    fellowship = result.scalar_one_or_none()

    if not fellowship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fellowship not found",
        )

    # Check access
    if (
        current_user.role == "fellowship_pastor" and
        current_user.fellowship_id != fellowship_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this fellowship",
        )

    # Get this week's boundaries
    week_start, week_end = get_current_week()

    # Get all cells in this fellowship (through senior cells)
    result = await session.execute(
        select(Cell).where(
            Cell.senior_cell_id.in_(
                select(SeniorCell.id).where(
                    SeniorCell.fellowship_id == fellowship_id
                )
            ),
            Cell.is_active == True
        )
    )
    all_cells = result.scalars().all()
    cell_ids = [c.id for c in all_cells]

    # Get reports for this week
    result = await session.execute(
        select(CellReport).where(
            CellReport.cell_id.in_(cell_ids),
            CellReport.week_start_date == week_start
        )
    )
    reports = result.scalars().all()

    # Calculate aggregates
    cells_reported = len(reports)
    total_attendance = sum(r.total_attendance or 0 for r in reports)
    total_souls_won = sum(r.souls_won or 0 for r in reports)
    total_first_timers = sum(r.first_timers or 0 for r in reports)
    total_finances = sum(float(r.finance_total or 0) for r in reports)

    submission_rate = (cells_reported / len(all_cells) * 100) if all_cells else 0

    return FellowshipDashboard(
        fellowship_id=fellowship.id,
        fellowship_name=fellowship.name,
        location=fellowship.location,
        zone_id=fellowship.zone_id,
        total_cells=len(all_cells),
        cells_reported=cells_reported,
        submission_rate_percent=round(submission_rate, 1),
        total_attendance=total_attendance,
        total_souls_won=total_souls_won,
        total_first_timers=total_first_timers,
        total_finances=total_finances,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: Zone Admin Dashboard
# ═══════════════════════════════════════════════════════════════════════════════

async def get_zone_dashboard(
    zone_id: UUID,
    authorization: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """
    Zone Admin dashboard
    Shows all fellowships with zone-wide aggregates
    """
    current_user = await get_current_user(authorization, session)

    # Get zone
    result = await session.execute(
        select(Zone).where(Zone.id == zone_id)
    )
    zone = result.scalar_one_or_none()

    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found",
        )

    # Check access
    if (
        current_user.role == "zonal_admin" and
        current_user.zone_id != zone_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this zone",
        )

    # Get this week's boundaries
    week_start, week_end = get_current_week()

    # Get all cells in this zone (through fellowships -> senior cells)
    result = await session.execute(
        select(Cell).where(
            Cell.senior_cell_id.in_(
                select(SeniorCell.id).where(
                    SeniorCell.fellowship_id.in_(
                        select(Fellowship.id).where(Fellowship.zone_id == zone_id)
                    )
                )
            ),
            Cell.is_active == True
        )
    )
    all_cells = result.scalars().all()
    cell_ids = [c.id for c in all_cells]

    # Get reports for this week
    result = await session.execute(
        select(CellReport).where(
            CellReport.cell_id.in_(cell_ids),
            CellReport.week_start_date == week_start
        )
    )
    reports = result.scalars().all()

    # Calculate aggregates
    cells_reported = len(reports)
    total_attendance = sum(r.total_attendance or 0 for r in reports)
    total_souls_won = sum(r.souls_won or 0 for r in reports)
    total_first_timers = sum(r.first_timers or 0 for r in reports)
    total_finances = sum(float(r.finance_total or 0) for r in reports)

    submission_rate = (cells_reported / len(all_cells) * 100) if all_cells else 0

    return ZoneDashboard(
        zone_id=zone.id,
        zone_name=zone.name,
        region_id=zone.region_id,
        total_cells=len(all_cells),
        cells_reported=cells_reported,
        submission_rate_percent=round(submission_rate, 1),
        total_attendance=total_attendance,
        total_souls_won=total_souls_won,
        total_first_timers=total_first_timers,
        total_finances=total_finances,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: Get All Reports (with filtering)
# ═══════════════════════════════════════════════════════════════════════════════

async def get_reports(
    cell_id: Optional[UUID] = None,
    status: Optional[str] = Query(None, regex="^(DRAFT|SUBMITTED|LATE|OVERDUE)$"),
    week_start: Optional[date] = None,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    authorization: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """
    Get reports with optional filtering
    Can filter by cell, status, week
    """
    current_user = await get_current_user(authorization, session)

    query = select(CellReport)

    # Apply filters
    if cell_id:
        query = query.where(CellReport.cell_id == cell_id)

    if status:
        query = query.where(CellReport.status == status)

    if week_start:
        query = query.where(CellReport.week_start_date == week_start)

    # Apply pagination
    query = query.order_by(desc(CellReport.submitted_at)).offset(offset).limit(limit)

    result = await session.execute(query)
    reports = result.scalars().all()

    return {
        "count": len(reports),
        "offset": offset,
        "limit": limit,
        "reports": [
            {
                "id": str(r.id),
                "cell_id": str(r.cell_id),
                "status": r.status,
                "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
                "week_start_date": r.week_start_date.isoformat(),
                "total_attendance": r.total_attendance,
                "souls_won": r.souls_won,
                "finance_total": float(r.finance_total or 0),
            }
            for r in reports
        ]
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: Mark Overdue Reports (Called by scheduled job)
# ═══════════════════════════════════════════════════════════════════════════════

async def mark_overdue_reports(
    session: AsyncSession = Depends(get_session),
):
    """
    Mark all draft reports as OVERDUE if past deadline
    This should be called by a scheduled job (APScheduler)
    """
    now = datetime.utcnow()

    # Find all draft reports past deadline
    result = await session.execute(
        select(CellReport).where(
            and_(
                CellReport.status == "DRAFT",
                CellReport.submission_deadline < now
            )
        )
    )
    overdue_reports = result.scalars().all()

    # Update status
    for report in overdue_reports:
        report.status = "OVERDUE"

    await session.commit()

    # Create notifications for cell leaders
    for report in overdue_reports:
        # Get cell leader
        result = await session.execute(
            select(User).where(User.cell_id == report.cell_id)
        )
        cell_leader = result.scalar_one_or_none()

        if cell_leader:
            notification = Notification(
                user_id=cell_leader.id,
                message=f"Cell report for week {report.week_start_date} is now OVERDUE",
                type="overdue_alert",
                fcm_token=cell_leader.fcm_token,
            )
            session.add(notification)

    await session.commit()

    return {
        "message": f"Marked {len(overdue_reports)} reports as overdue",
        "count": len(overdue_reports),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: Send Manual Nudge (Fellowship Pastor to cell leader)
# ═══════════════════════════════════════════════════════════════════════════════

async def send_nudge(
    cell_id: UUID,
    message: str = "Please submit your cell report",
    authorization: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """
    Send manual nudge to cell leader
    Only fellowship pastor or higher can do this
    """
    current_user = await get_current_user(authorization, session)

    # Check permission
    if current_user.role not in ["fellowship_pastor", "zonal_pastor", "zonal_admin", "system_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only pastors can send nudges",
        )

    # Get cell
    result = await session.execute(
        select(Cell).where(Cell.id == cell_id)
    )
    cell = result.scalar_one_or_none()

    if not cell:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cell not found",
        )

    # Get cell leader
    result = await session.execute(
        select(User).where(User.id == cell.leader_id)
    )
    cell_leader = result.scalar_one_or_none()

    if not cell_leader:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cell leader not found",
        )

    # Create notification
    notification = Notification(
        user_id=cell_leader.id,
        message=message,
        type="manual_nudge",
        fcm_token=cell_leader.fcm_token,
    )

    session.add(notification)
    await session.commit()

    return {
        "message": "Nudge sent to cell leader",
        "cell_leader": cell_leader.name,
        "cell": cell.name,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: Get Cells Needing Attention (for Fellowship Pastor)
# ═══════════════════════════════════════════════════════════════════════════════

async def get_cells_needing_attention(
    fellowship_id: UUID,
    authorization: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """
    Get list of cells that haven't submitted or are late
    """
    current_user = await get_current_user(authorization, session)

    # Get fellowship
    result = await session.execute(
        select(Fellowship).where(Fellowship.id == fellowship_id)
    )
    fellowship = result.scalar_one_or_none()

    if not fellowship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fellowship not found",
        )

    # Get this week's boundaries
    week_start, week_end = get_current_week()

    # Get all cells in this fellowship
    result = await session.execute(
        select(Cell).where(
            Cell.senior_cell_id.in_(
                select(SeniorCell.id).where(SeniorCell.fellowship_id == fellowship_id)
            ),
            Cell.is_active == True
        )
    )
    all_cells = result.scalars().all()

    # Get reports submitted this week
    result = await session.execute(
        select(CellReport).where(
            CellReport.cell_id.in_([c.id for c in all_cells]),
            CellReport.week_start_date == week_start
        )
    )
    reports = {r.cell_id: r for r in result.scalars().all()}

    # Find cells that haven't reported
    cells_needing_attention = []

    for cell in all_cells:
        if cell.id not in reports:
            cells_needing_attention.append({
                "cell_id": str(cell.id),
                "cell_name": cell.name,
                "leader_name": cell.leader_name,
                "status": "NO_REPORT",
                "days_overdue": (datetime.utcnow().date() - week_start).days,
            })
        elif reports[cell.id].status in ["LATE", "OVERDUE"]:
            cells_needing_attention.append({
                "cell_id": str(cell.id),
                "cell_name": cell.name,
                "leader_name": cell.leader_name,
                "status": reports[cell.id].status,
                "submitted_at": reports[cell.id].submitted_at.isoformat() if reports[cell.id].submitted_at else None,
            })

    return {
        "fellowship": fellowship.name,
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "total_cells": len(all_cells),
        "cells_needing_attention": len(cells_needing_attention),
        "cells": cells_needing_attention,
    }