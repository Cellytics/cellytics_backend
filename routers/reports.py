from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import date
from uuid import UUID
from typing import Optional
 
from database import get_session
from models import User, Cell, CellReport, SeniorCell, Fellowship
from schemas import CellReportSubmit, CellReportResponse
from services.report_service import ReportService
from utils.security import (
    ensure_cell_access,
    ensure_report_access,
    get_current_user,
    require_roles,
    scoped_report_query,
)
 
router = APIRouter()
 
 
@router.post("/reports/submit", response_model=CellReportResponse)
async def submit_report(
    request: CellReportSubmit,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Submit a cell report"""
    try:
        require_roles(
            current_user,
            {"cell_leader", "senior_cell_leader", "fellowship_pastor", "zonal_admin", "system_admin"},
        )
 
        # Verify cell exists
        result = await session.execute(select(Cell).where(Cell.id == request.cell_id))
        cell = result.scalar_one_or_none()
        if not cell:
            raise HTTPException(status_code=404, detail="Cell not found")
        await ensure_cell_access(session, current_user, request.cell_id)
 
        # Check for duplicate
        result = await session.execute(
            select(CellReport).where(
                CellReport.cell_id == request.cell_id,
                CellReport.week_start_date == request.week_start_date
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Report already exists")
 
        # Use service to create report
        report = await ReportService.create_report(
            session=session,
            request=request,
            user_id=current_user.id
        )
 
        return CellReportResponse(
            id=str(report.id),
            cell_id=str(report.cell_id),
            status=report.status,
            submitted_at=report.submitted_at,
            submission_deadline=report.submission_deadline,
            message=f"Report submitted {'on time' if report.status == 'submitted' else 'late'}!",
        )
 
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Report submission failed")
 
 
@router.get("/reports/{report_id}")
async def get_report(
    report_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get single report"""
    try:
        result = await session.execute(
            select(CellReport).where(CellReport.id == report_id)
        )
        report = result.scalar_one_or_none()
 
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        await ensure_report_access(session, current_user, report_id)
 
        return report
 
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch report")
 
 
@router.get("/reports")
async def list_reports(
    cell_id: Optional[UUID] = None,
    status: Optional[str] = Query(None, regex="^(draft|submitted|late|overdue)$"),
    week_start: Optional[date] = None,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List reports with optional filtering"""
    try:
        query = select(CellReport)
 
        if cell_id:
            await ensure_cell_access(session, current_user, cell_id)
            query = query.where(CellReport.cell_id == cell_id)
        if status:
            query = query.where(CellReport.status == status)
        if week_start:
            query = query.where(CellReport.week_start_date == week_start)

        query = scoped_report_query(query, current_user)
 
        query = query.order_by(desc(CellReport.submitted_at)).offset(offset).limit(limit)
 
        result = await session.execute(query)
        reports = result.scalars().all()
 
        cell_ids = {r.cell_id for r in reports}
        cells_by_id = {}
        senior_cells_by_id = {}
        fellowships_by_id = {}

        if cell_ids:
            cells_result = await session.execute(select(Cell).where(Cell.id.in_(cell_ids)))
            cells = cells_result.scalars().all()
            cells_by_id = {c.id: c for c in cells}

            senior_cell_ids = {c.senior_cell_id for c in cells}
            if senior_cell_ids:
                senior_cells_result = await session.execute(
                    select(SeniorCell).where(SeniorCell.id.in_(senior_cell_ids))
                )
                senior_cells = senior_cells_result.scalars().all()
                senior_cells_by_id = {sc.id: sc for sc in senior_cells}

                fellowship_ids = {sc.fellowship_id for sc in senior_cells}
                if fellowship_ids:
                    fellowships_result = await session.execute(
                        select(Fellowship).where(Fellowship.id.in_(fellowship_ids))
                    )
                    fellowships = fellowships_result.scalars().all()
                    fellowships_by_id = {f.id: f for f in fellowships}

        return {
            "count": len(reports),
            "offset": offset,
            "limit": limit,
            "reports": [
                {
                    "id": str(r.id),
                    "cell_id": str(r.cell_id),
                    "cell_name": cells_by_id.get(r.cell_id).name if cells_by_id.get(r.cell_id) else None,
                    "senior_cell_id": str(cells_by_id.get(r.cell_id).senior_cell_id) if cells_by_id.get(r.cell_id) else None,
                    "senior_cell_name": (
                        senior_cells_by_id.get(cells_by_id.get(r.cell_id).senior_cell_id).name
                        if cells_by_id.get(r.cell_id)
                        and senior_cells_by_id.get(cells_by_id.get(r.cell_id).senior_cell_id)
                        else None
                    ),
                    "fellowship_id": (
                        str(senior_cells_by_id.get(cells_by_id.get(r.cell_id).senior_cell_id).fellowship_id)
                        if cells_by_id.get(r.cell_id)
                        and senior_cells_by_id.get(cells_by_id.get(r.cell_id).senior_cell_id)
                        else None
                    ),
                    "fellowship_name": (
                        fellowships_by_id.get(
                            senior_cells_by_id.get(cells_by_id.get(r.cell_id).senior_cell_id).fellowship_id
                        ).name
                        if cells_by_id.get(r.cell_id)
                        and senior_cells_by_id.get(cells_by_id.get(r.cell_id).senior_cell_id)
                        and fellowships_by_id.get(
                            senior_cells_by_id.get(cells_by_id.get(r.cell_id).senior_cell_id).fellowship_id
                        )
                        else None
                    ),
                    "status": r.status,
                    "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
                    "week_start_date": r.week_start_date.isoformat(),
                    "total_attendance": r.total_attendance,
                    "first_timers": r.first_timers,
                    "filled_holy_ghost": r.filled_holy_ghost,
                    "new_members": r.new_members,
                    "number_saved": r.number_saved,
                    "souls_won": r.souls_won,
                    "finance_oblation": float(r.finance_oblation or 0),
                    "finance_offerings": float(r.finance_offerings or 0),
                    "finance_tithes": float(r.finance_tithes or 0),
                    "finance_thanksgiving": float(r.finance_thanksgiving or 0),
                    "finance_seed": float(r.finance_seed or 0),
                    "finance_partnership": float(r.finance_partnership or 0),
                    "finance_first_fruits": float(r.finance_first_fruits or 0),
                    "finance_total": float(r.finance_total or 0),
                }
                for r in reports
            ]
        }
 
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to list reports")
 
