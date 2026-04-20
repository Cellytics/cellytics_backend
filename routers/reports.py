from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, date
from uuid import UUID
from typing import Optional
 
from database import get_session
from models import User, Cell, CellReport
from schemas import CellReportSubmit, CellReportResponse
from auth import decode_token
from services.report_service import ReportService
 
router = APIRouter()
 
async def get_current_user(
    authorization: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_session)
) -> User:
    """Extract current user from JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")
 
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError
    except (ValueError, IndexError):
        raise HTTPException(status_code=401, detail="Invalid auth header")
 
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
 
    result = await session.execute(
        select(User).where(User.id == UUID(user_id), User.is_active == True)
    )
    user = result.scalar_one_or_none()
 
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
 
    return user
 
 
@router.post("/reports/submit", response_model=CellReportResponse)
async def submit_report(
    request: CellReportSubmit,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Submit a cell report"""
    try:
        # Permission check
        if current_user.role == "cell_leader":
            if current_user.cell_id != request.cell_id:
                raise HTTPException(status_code=403, detail="Can only submit for your cell")
        elif current_user.role not in ["senior_cell_leader", "fellowship_pastor", "zonal_admin", "system_admin"]:
            raise HTTPException(status_code=403, detail="Permission denied")
 
        # Verify cell exists
        result = await session.execute(select(Cell).where(Cell.id == request.cell_id))
        cell = result.scalar_one_or_none()
        if not cell:
            raise HTTPException(status_code=404, detail="Cell not found")
 
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
            id=report.id,
            cell_id=report.cell_id,
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
            query = query.where(CellReport.cell_id == cell_id)
        if status:
            query = query.where(CellReport.status == status)
        if week_start:
            query = query.where(CellReport.week_start_date == week_start)
 
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
 
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to list reports")
 