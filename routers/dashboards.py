from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
 
from database import get_session
from models import User, Zone, Fellowship, SeniorCell
from services.dashboard_service import DashboardService
from utils.security import (
    ensure_fellowship_access,
    ensure_senior_cell_access,
    ensure_zone_access,
    get_current_user,
)
 
router = APIRouter()
 
 
@router.get("/dashboards/senior-cell/{senior_cell_id}")
async def get_senior_cell_dashboard(
    senior_cell_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Senior Cell Leader dashboard"""
    try:
        result = await session.execute(
            select(SeniorCell).where(SeniorCell.id == senior_cell_id)
        )
        senior_cell = result.scalar_one_or_none()
 
        if not senior_cell:
            raise HTTPException(status_code=404, detail="Senior cell not found")
        await ensure_senior_cell_access(session, current_user, senior_cell_id)
 
        # Use service to build dashboard
        dashboard = await DashboardService.build_senior_cell_dashboard(
            session=session,
            senior_cell_id=senior_cell_id
        )
 
        return dashboard
 
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard")
 
 
@router.get("/dashboards/fellowship/{fellowship_id}")
async def get_fellowship_dashboard(
    fellowship_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Fellowship Pastor dashboard"""
    try:
        result = await session.execute(
            select(Fellowship).where(Fellowship.id == fellowship_id)
        )
        fellowship = result.scalar_one_or_none()
 
        if not fellowship:
            raise HTTPException(status_code=404, detail="Fellowship not found")
        await ensure_fellowship_access(session, current_user, fellowship_id)
 
        # Use service
        dashboard = await DashboardService.build_fellowship_dashboard(
            session=session,
            fellowship_id=fellowship_id
        )
 
        return dashboard
 
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard")
 
 
@router.get("/dashboards/zone/{zone_id}")
async def get_zone_dashboard(
    zone_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Zonal Admin dashboard"""
    try:
        result = await session.execute(
            select(Zone).where(Zone.id == zone_id)
        )
        zone = result.scalar_one_or_none()
 
        if not zone:
            raise HTTPException(status_code=404, detail="Zone not found")
        await ensure_zone_access(current_user, zone_id)
 
        # Use service
        dashboard = await DashboardService.build_zone_dashboard(
            session=session,
            zone_id=zone_id
        )
 
        return dashboard
 
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard")
 
