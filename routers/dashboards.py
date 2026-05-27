from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
 
from database import get_session
from models import User, Zone, Fellowship, SeniorCell, Cell
from services.dashboard_service import DashboardService
from utils.security import (
    ensure_fellowship_access,
    ensure_cell_access,
    ensure_senior_cell_access,
    ensure_zone_access,
    get_current_user,
)
 
router = APIRouter()
 
 
@router.get("/dashboards/cell/{cell_id}")
async def get_cell_dashboard(
    cell_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Dashboard for a normal cell leader."""
    try:
        result = await session.execute(select(Cell).where(Cell.id == cell_id))
        cell = result.scalar_one_or_none()

        if not cell:
            raise HTTPException(status_code=404, detail="Cell not found")
        await ensure_cell_access(session, current_user, cell_id)

        dashboard = await DashboardService.build_cell_dashboard(
            session=session,
            cell_id=cell_id
        )

        return dashboard

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard")


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
    period: str = "week",
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Fellowship Pastor dashboard with period filtering"""
    try:
        result = await session.execute(
            select(Fellowship).where(Fellowship.id == fellowship_id)
        )
        fellowship = result.scalar_one_or_none()
 
        if not fellowship:
            raise HTTPException(status_code=404, detail="Fellowship not found")
        await ensure_fellowship_access(session, current_user, fellowship_id)
 
        # Validate period
        if period not in ["week", "month", "year", "all"]:
            period = "week"
 
        # Use service
        dashboard = await DashboardService.build_fellowship_dashboard(
            session=session,
            fellowship_id=fellowship_id,
            period=period
        )
 
        return dashboard
 
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Dashboard error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard: {str(e)}")


@router.get("/dashboards/fellowship/{fellowship_id}/senior-cells")
async def get_fellowship_senior_cells(
    fellowship_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get all senior cells in a fellowship with their stats"""
    try:
        result = await session.execute(
            select(Fellowship).where(Fellowship.id == fellowship_id)
        )
        fellowship = result.scalar_one_or_none()
 
        if not fellowship:
            raise HTTPException(status_code=404, detail="Fellowship not found")
        await ensure_fellowship_access(session, current_user, fellowship_id)
 
        senior_cells = await DashboardService.get_fellowship_senior_cells(
            session=session,
            fellowship_id=fellowship_id
        )
 
        return {
            "fellowship_id": str(fellowship_id),
            "fellowship_name": fellowship.name,
            "senior_cells": senior_cells,
        }
 
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch senior cells")


@router.get("/dashboards/senior-cell/{senior_cell_id}/details")
async def get_senior_cell_details(
    senior_cell_id: UUID,
    period: str = "week",
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get detailed view of a senior cell with all cells and reports"""
    try:
        result = await session.execute(
            select(SeniorCell).where(SeniorCell.id == senior_cell_id)
        )
        senior_cell = result.scalar_one_or_none()
 
        if not senior_cell:
            raise HTTPException(status_code=404, detail="Senior cell not found")
        await ensure_senior_cell_access(session, current_user, senior_cell_id)
 
        # Validate period
        if period not in ["week", "month", "year"]:
            period = "week"
 
        details = await DashboardService.get_senior_cell_details(
            session=session,
            senior_cell_id=senior_cell_id,
            period=period
        )
 
        return details
 
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch senior cell details")


@router.post("/dashboards/fellowship/{fellowship_id}/ping-leader")
async def ping_leader(
    fellowship_id: UUID,
    leader_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Send a notification to a senior cell or cell leader about unsubmitted report"""
    try:
        result = await session.execute(
            select(Fellowship).where(Fellowship.id == fellowship_id)
        )
        fellowship = result.scalar_one_or_none()
 
        if not fellowship:
            raise HTTPException(status_code=404, detail="Fellowship not found")
        await ensure_fellowship_access(session, current_user, fellowship_id)
 
        # Get the leader
        result = await session.execute(
            select(User).where(User.id == leader_id)
        )
        leader = result.scalar_one_or_none()
 
        if not leader:
            raise HTTPException(status_code=404, detail="Leader not found")
 
        # TODO: Implement FCM notification to leader
        # For now, just return success
 
        return {
            "message": f"Notification sent to {leader.name}",
            "leader_id": str(leader_id),
        }
 
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send notification")
 
 
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
 
