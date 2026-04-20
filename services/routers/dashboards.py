from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, date, timedelta
from uuid import UUID
from typing import Optional
 
from database import get_session
from models import User, Cell, CellReport, Zone, Fellowship, SeniorCell
from auth import decode_token
from services.dashboard_service import DashboardService
 
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
 
 
@router.get("/dashboards/senior-cell/{senior_cell_id}")
async def get_senior_cell_dashboard(
    senior_cell_id: UUID,
    authorization: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_session),
):
    """Senior Cell Leader dashboard"""
    try:
        current_user = await get_current_user(authorization, session)
 
        result = await session.execute(
            select(SeniorCell).where(SeniorCell.id == senior_cell_id)
        )
        senior_cell = result.scalar_one_or_none()
 
        if not senior_cell:
            raise HTTPException(status_code=404, detail="Senior cell not found")
 
        # Check access
        if current_user.role == "senior_cell_leader" and current_user.senior_cell_id != senior_cell_id:
            raise HTTPException(status_code=403, detail="Access denied")
 
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
    authorization: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_session),
):
    """Fellowship Pastor dashboard"""
    try:
        current_user = await get_current_user(authorization, session)
 
        result = await session.execute(
            select(Fellowship).where(Fellowship.id == fellowship_id)
        )
        fellowship = result.scalar_one_or_none()
 
        if not fellowship:
            raise HTTPException(status_code=404, detail="Fellowship not found")
 
        if current_user.role == "fellowship_pastor" and current_user.fellowship_id != fellowship_id:
            raise HTTPException(status_code=403, detail="Access denied")
 
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
    authorization: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_session),
):
    """Zonal Admin dashboard"""
    try:
        current_user = await get_current_user(authorization, session)
 
        result = await session.execute(
            select(Zone).where(Zone.id == zone_id)
        )
        zone = result.scalar_one_or_none()
 
        if not zone:
            raise HTTPException(status_code=404, detail="Zone not found")
 
        if current_user.role == "zonal_admin" and current_user.zone_id != zone_id:
            raise HTTPException(status_code=403, detail="Access denied")
 
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
 