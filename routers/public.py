# routers/public.py
# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC endpoints — NO authentication required.
# Used exclusively by the mobile app's ScopeSelectorScreen BEFORE the user
# logs in, to let them drill down: Zone → Fellowship → Senior Cell → Cell.
#
# These endpoints intentionally return a minimal payload (id + name + location)
# so they cannot be used to harvest sensitive data.
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Optional
import logging

from database import get_session
from models import Zone, Fellowship, SeniorCell, Cell

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/public", tags=["public"])


# ── Zones ─────────────────────────────────────────────────────────────────────

@router.get("/zones")
async def list_zones_public(
    session: AsyncSession = Depends(get_session),
):
    """List all active zones. No authentication required."""
    try:
        result = await session.execute(select(Zone))
        zones = result.scalars().all()
        return [
            {
                "id": str(z.id),
                "name": z.name,
                "location": z.location,
            }
            for z in zones
        ]
    except Exception as e:
        logger.error(f"Public zones list failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch zones")


# ── Fellowships ───────────────────────────────────────────────────────────────

@router.get("/fellowships")
async def list_fellowships_public(
    zone_id: Optional[UUID] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """List fellowships, optionally filtered by zone_id. No auth required."""
    try:
        query = select(Fellowship)
        if zone_id:
            query = query.where(Fellowship.zone_id == zone_id)
        result = await session.execute(query)
        fellowships = result.scalars().all()
        return [
            {
                "id": str(f.id),
                "name": f.name,
                "location": f.location,
                "zone_id": str(f.zone_id),
            }
            for f in fellowships
        ]
    except Exception as e:
        logger.error(f"Public fellowships list failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch fellowships")


# ── Senior Cells ──────────────────────────────────────────────────────────────

@router.get("/senior-cells")
async def list_senior_cells_public(
    fellowship_id: Optional[UUID] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """List senior cells, optionally filtered by fellowship_id. No auth required."""
    try:
        query = select(SeniorCell)
        if fellowship_id:
            query = query.where(SeniorCell.fellowship_id == fellowship_id)
        result = await session.execute(query)
        senior_cells = result.scalars().all()
        return [
            {
                "id": str(sc.id),
                "name": sc.name,
                "fellowship_id": str(sc.fellowship_id),
            }
            for sc in senior_cells
        ]
    except Exception as e:
        logger.error(f"Public senior cells list failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch senior cells")


# ── Cells ─────────────────────────────────────────────────────────────────────

@router.get("/cells")
async def list_cells_public(
    senior_cell_id: Optional[UUID] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """List active cells, optionally filtered by senior_cell_id. No auth required."""
    try:
        query = select(Cell).where(Cell.is_active == True)
        if senior_cell_id:
            query = query.where(Cell.senior_cell_id == senior_cell_id)
        result = await session.execute(query)
        cells = result.scalars().all()
        return [
            {
                "id": str(c.id),
                "name": c.name,
                "senior_cell_id": str(c.senior_cell_id),
                "default_meeting_day": c.default_meeting_day,
            }
            for c in cells
        ]
    except Exception as e:
        logger.error(f"Public cells list failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch cells")