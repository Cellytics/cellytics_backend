# routers/admin.py - Admin endpoints for setup and management

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import time as time_type
from uuid import UUID
from typing import Optional
import logging

from database import get_session
from models import User, Zone, Fellowship, SeniorCell, Cell, CellReport
from schemas import (
    ZoneCreate, ZoneUpdate, ZoneResponse,
    FellowshipCreate, FellowshipUpdate, FellowshipResponse,
    SeniorCellCreate, SeniorCellUpdate, SeniorCellResponse,
    CellCreate, CellUpdate, CellResponse,
    UserCreate, UserCreateResponse, UserUpdate
)
from auth import hash_default_pin
from services.admin_service import AdminService
from utils.security import (
    ensure_cell_access,
    ensure_fellowship_access,
    ensure_senior_cell_access,
    ensure_zone_access,
    get_current_user,
    require_fellowship_pastor_or_above,
    require_senior_cell_leader_or_above,
    require_system_admin,
    require_zonal_admin_or_above,
    scoped_cell_query,
    scoped_fellowship_query,
    scoped_senior_cell_query,
    scoped_zone_query,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: Check admin permissions
# ═══════════════════════════════════════════════════════════════════════════════

def check_system_admin(user: User):
    """Only system_admin can use this endpoint"""
    require_system_admin(user)


def check_zonal_admin(user: User):
    """Only zonal_admin or system_admin can use this endpoint"""
    require_zonal_admin_or_above(user)


def check_fellowship_pastor(user: User):
    """Only fellowship_pastor or above can use this endpoint"""
    require_fellowship_pastor_or_above(user)


def check_senior_cell_leader(user: User):
    """Only senior_cell_leader or above can use this endpoint"""
    require_senior_cell_leader_or_above(user)


# ═══════════════════════════════════════════════════════════════════════════════
# ZONE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/admin/zones", response_model=ZoneResponse)
async def create_zone(
    request: ZoneCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new zone. System admin only."""
    check_system_admin(current_user)

    try:
        zone = Zone(
            name=request.name,
            location=request.location,
            description=request.description,
        )
        session.add(zone)
        await session.commit()
        await session.refresh(zone)

        return ZoneResponse(
            id=str(zone.id),
            name=zone.name,
            location=zone.location,
            description=zone.description,
            created_at=zone.created_at,
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Zone creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Zone creation failed")


@router.get("/admin/zones/{zone_id}", response_model=ZoneResponse)
async def get_zone(
    zone_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get zone details"""
    zone = await AdminService.get_zone_by_id(session, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    await ensure_zone_access(current_user, zone_id)

    return ZoneResponse(
        id=str(zone.id),
        name=zone.name,
        location=zone.location,
        description=zone.description,
        created_at=zone.created_at,
    )


@router.get("/admin/zones", response_model=list)
async def list_zones(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List all zones"""
    result = await session.execute(scoped_zone_query(select(Zone), current_user))
    zones = result.scalars().all()

    return [
        {
            "id": str(z.id),
            "name": z.name,
            "location": z.location,
            "created_at": z.created_at.isoformat(),
        }
        for z in zones
    ]


@router.patch("/admin/zones/{zone_id}", response_model=ZoneResponse)
async def update_zone(
    zone_id: UUID,
    request: ZoneUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update zone. System admin only."""
    check_system_admin(current_user)

    zone = await AdminService.get_zone_by_id(session, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    try:
        if request.name:
            zone.name = request.name
        if request.location:
            zone.location = request.location
        if request.description:
            zone.description = request.description

        await session.commit()
        await session.refresh(zone)

        return ZoneResponse(
            id=str(zone.id),
            name=zone.name,
            location=zone.location,
            description=zone.description,
            created_at=zone.created_at,
        )

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Zone update failed")


@router.delete("/admin/zones/{zone_id}")
async def delete_zone(
    zone_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete zone. System admin only."""
    check_system_admin(current_user)

    zone = await AdminService.get_zone_by_id(session, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    try:
        await session.delete(zone)
        await session.commit()
        return {"message": "Zone deleted"}

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Zone deletion failed")


# ═══════════════════════════════════════════════════════════════════════════════
# FELLOWSHIP MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/admin/fellowships", response_model=FellowshipResponse)
async def create_fellowship(
    request: FellowshipCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create fellowship. Zonal admin only."""
    check_zonal_admin(current_user)

    try:
        # Verify zone exists
        zone = await AdminService.get_zone_by_id(session, request.zone_id)
        if not zone:
            raise HTTPException(status_code=404, detail="Zone not found")

        # Zonal admin can only create in their zone
        if current_user.role == "zonal_admin" and current_user.zone_id != request.zone_id:
            raise HTTPException(status_code=403, detail="Can only create fellowships in your zone")

        fellowship = Fellowship(
            name=request.name,
            location=request.location,
            zone_id=request.zone_id,
        )
        session.add(fellowship)
        await session.commit()
        await session.refresh(fellowship)

        return FellowshipResponse(
            id=str(fellowship.id),
            name=fellowship.name,
            location=fellowship.location,
            zone_id=str(fellowship.zone_id),
            created_at=fellowship.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Fellowship creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Fellowship creation failed")


@router.get("/admin/fellowships")
async def list_fellowships(
    zone_id: Optional[UUID] = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List fellowships. Filter by zone_id if provided."""
    try:
        query = select(Fellowship)

        if zone_id:
            await ensure_zone_access(current_user, zone_id)
            query = query.where(Fellowship.zone_id == zone_id)

        query = scoped_fellowship_query(query, current_user)

        result = await session.execute(query)
        fellowships = result.scalars().all()

        return [
            {
                "id": str(f.id),
                "name": f.name,
                "location": f.location,
                "zone_id": str(f.zone_id),
                "created_at": f.created_at.isoformat(),
            }
            for f in fellowships
        ]

    except Exception as e:
        logger.error(f"Fellowship list failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list fellowships")


@router.get("/admin/fellowships/{fellowship_id}", response_model=FellowshipResponse)
async def get_fellowship(
    fellowship_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get fellowship details"""
    fellowship = await AdminService.get_fellowship_by_id(session, fellowship_id)
    if not fellowship:
        raise HTTPException(status_code=404, detail="Fellowship not found")
    await ensure_fellowship_access(session, current_user, fellowship_id)

    return FellowshipResponse(
        id=str(fellowship.id),
        name=fellowship.name,
        location=fellowship.location,
        zone_id=str(fellowship.zone_id),
        created_at=fellowship.created_at,
    )


@router.patch("/admin/fellowships/{fellowship_id}", response_model=FellowshipResponse)
async def update_fellowship(
    fellowship_id: UUID,
    request: FellowshipUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update fellowship. Zonal admin only."""
    check_zonal_admin(current_user)

    fellowship = await AdminService.get_fellowship_by_id(session, fellowship_id)
    if not fellowship:
        raise HTTPException(status_code=404, detail="Fellowship not found")
    await ensure_fellowship_access(session, current_user, fellowship_id)

    # Zonal admin can only update fellowships in their zone
    if current_user.role == "zonal_admin" and current_user.zone_id != fellowship.zone_id:
        raise HTTPException(status_code=403, detail="Can only update fellowships in your zone")

    try:
        if request.name:
            fellowship.name = request.name
        if request.location:
            fellowship.location = request.location

        await session.commit()
        await session.refresh(fellowship)

        return FellowshipResponse(
            id=str(fellowship.id),
            name=fellowship.name,
            location=fellowship.location,
            zone_id=str(fellowship.zone_id),
            created_at=fellowship.created_at,
        )

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Fellowship update failed")


@router.delete("/admin/fellowships/{fellowship_id}")
async def delete_fellowship(
    fellowship_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete fellowship. Zonal admin only."""
    check_zonal_admin(current_user)

    fellowship = await AdminService.get_fellowship_by_id(session, fellowship_id)
    if not fellowship:
        raise HTTPException(status_code=404, detail="Fellowship not found")
    await ensure_fellowship_access(session, current_user, fellowship_id)

    if current_user.role == "zonal_admin" and current_user.zone_id != fellowship.zone_id:
        raise HTTPException(status_code=403, detail="Can only delete fellowships in your zone")

    try:
        await session.delete(fellowship)
        await session.commit()
        return {"message": "Fellowship deleted"}

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Fellowship deletion failed")


# ═══════════════════════════════════════════════════════════════════════════════
# SENIOR CELL MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/admin/senior-cells", response_model=SeniorCellResponse)
async def create_senior_cell(
    request: SeniorCellCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create senior cell. Fellowship pastor and above."""
    check_fellowship_pastor(current_user)

    try:
        # Verify fellowship exists
        fellowship = await AdminService.get_fellowship_by_id(session, request.fellowship_id)
        if not fellowship:
            raise HTTPException(status_code=404, detail="Fellowship not found")

        # Permission check
        if current_user.role == "fellowship_pastor":
            if current_user.fellowship_id != request.fellowship_id:
                raise HTTPException(status_code=403, detail="Can only create in your fellowship")
        elif current_user.role == "zonal_admin":
            if current_user.zone_id != fellowship.zone_id:
                raise HTTPException(status_code=403, detail="Fellowship not in your zone")

        senior_cell = SeniorCell(
            name=request.name,
            fellowship_id=request.fellowship_id,
        )
        session.add(senior_cell)
        await session.commit()
        await session.refresh(senior_cell)

        return SeniorCellResponse(
            id=str(senior_cell.id),
            name=senior_cell.name,
            fellowship_id=str(senior_cell.fellowship_id),
            created_at=senior_cell.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Senior cell creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Senior cell creation failed")


@router.get("/admin/senior-cells")
async def list_senior_cells(
    fellowship_id: Optional[UUID] = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List senior cells. Filter by fellowship_id if provided."""
    try:
        query = select(SeniorCell)

        if fellowship_id:
            await ensure_fellowship_access(session, current_user, fellowship_id)
            query = query.where(SeniorCell.fellowship_id == fellowship_id)

        query = scoped_senior_cell_query(query, current_user)

        result = await session.execute(query)
        senior_cells = result.scalars().all()

        return [
            {
                "id": str(sc.id),
                "name": sc.name,
                "fellowship_id": str(sc.fellowship_id),
                "created_at": sc.created_at.isoformat(),
            }
            for sc in senior_cells
        ]

    except Exception as e:
        logger.error(f"Senior cell list failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list senior cells")


@router.get("/admin/senior-cells/{senior_cell_id}", response_model=SeniorCellResponse)
async def get_senior_cell(
    senior_cell_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get senior cell details"""
    senior_cell = await AdminService.get_senior_cell_by_id(session, senior_cell_id)
    if not senior_cell:
        raise HTTPException(status_code=404, detail="Senior cell not found")
    await ensure_senior_cell_access(session, current_user, senior_cell_id)

    return SeniorCellResponse(
        id=str(senior_cell.id),
        name=senior_cell.name,
        fellowship_id=str(senior_cell.fellowship_id),
        created_at=senior_cell.created_at,
    )


@router.patch("/admin/senior-cells/{senior_cell_id}", response_model=SeniorCellResponse)
async def update_senior_cell(
    senior_cell_id: UUID,
    request: SeniorCellUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update senior cell. Fellowship pastor and above."""
    check_fellowship_pastor(current_user)

    senior_cell = await AdminService.get_senior_cell_by_id(session, senior_cell_id)
    if not senior_cell:
        raise HTTPException(status_code=404, detail="Senior cell not found")
    await ensure_senior_cell_access(session, current_user, senior_cell_id)

    try:
        if request.name:
            senior_cell.name = request.name

        await session.commit()
        await session.refresh(senior_cell)

        return SeniorCellResponse(
            id=str(senior_cell.id),
            name=senior_cell.name,
            fellowship_id=str(senior_cell.fellowship_id),
            created_at=senior_cell.created_at,
        )

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Senior cell update failed")


@router.delete("/admin/senior-cells/{senior_cell_id}")
async def delete_senior_cell(
    senior_cell_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete senior cell. Fellowship pastor and above."""
    check_fellowship_pastor(current_user)

    senior_cell = await AdminService.get_senior_cell_by_id(session, senior_cell_id)
    if not senior_cell:
        raise HTTPException(status_code=404, detail="Senior cell not found")
    await ensure_senior_cell_access(session, current_user, senior_cell_id)

    try:
        await session.delete(senior_cell)
        await session.commit()
        return {"message": "Senior cell deleted"}

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Senior cell deletion failed")


# ═══════════════════════════════════════════════════════════════════════════════
# CELL MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/admin/cells", response_model=CellResponse)
async def create_cell(
    request: CellCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create cell. Fellowship pastor and above."""
    check_fellowship_pastor(current_user)

    try:
        # Verify senior cell exists
        senior_cell = await AdminService.get_senior_cell_by_id(session, request.senior_cell_id)
        if not senior_cell:
            raise HTTPException(status_code=404, detail="Senior cell not found")

        # Permission check
        if current_user.role == "fellowship_pastor":
            if current_user.fellowship_id != senior_cell.fellowship_id:
                raise HTTPException(status_code=403, detail="Senior cell not in your fellowship")
        elif current_user.role == "zonal_admin":
            fellowship = await AdminService.get_fellowship_by_id(session, senior_cell.fellowship_id)
            if current_user.zone_id != fellowship.zone_id:
                raise HTTPException(status_code=403, detail="Senior cell not in your zone")

        # Parse meeting time if provided
        meeting_time_obj = None
        if request.meeting_time:
            try:
                h, m = map(int, request.meeting_time.split(":"))
                meeting_time_obj = time_type(h, m)
            except:
                raise HTTPException(status_code=400, detail="Invalid time format")

        cell = Cell(
            name=request.name,
            senior_cell_id=request.senior_cell_id,
            default_meeting_day=request.default_meeting_day,
            meeting_time=meeting_time_obj,
        )
        session.add(cell)
        await session.commit()
        await session.refresh(cell)

        return CellResponse(
            id=str(cell.id),
            name=cell.name,
            senior_cell_id=str(cell.senior_cell_id),
            default_meeting_day=cell.default_meeting_day,
            meeting_time=cell.meeting_time.isoformat() if cell.meeting_time else None,
            created_at=cell.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Cell creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Cell creation failed")


@router.get("/admin/cells")
async def list_cells(
    senior_cell_id: Optional[UUID] = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List cells. Filter by senior_cell_id if provided."""
    try:
        query = select(Cell)

        if senior_cell_id:
            await ensure_senior_cell_access(session, current_user, senior_cell_id)
            query = query.where(Cell.senior_cell_id == senior_cell_id)

        query = scoped_cell_query(query, current_user)

        result = await session.execute(query)
        cells = result.scalars().all()

        return [
            {
                "id": str(c.id),
                "name": c.name,
                "senior_cell_id": str(c.senior_cell_id),
                "default_meeting_day": c.default_meeting_day,
                "meeting_time": c.meeting_time.isoformat() if c.meeting_time else None,
                "created_at": c.created_at.isoformat(),
            }
            for c in cells
        ]

    except Exception as e:
        logger.error(f"Cell list failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list cells")


@router.get("/admin/cells/{cell_id}", response_model=CellResponse)
async def get_cell(
    cell_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get cell details"""
    cell = await AdminService.get_cell_by_id(session, cell_id)
    if not cell:
        raise HTTPException(status_code=404, detail="Cell not found")
    await ensure_cell_access(session, current_user, cell_id)

    return CellResponse(
        id=str(cell.id),
        name=cell.name,
        senior_cell_id=str(cell.senior_cell_id),
        default_meeting_day=cell.default_meeting_day,
        meeting_time=cell.meeting_time.isoformat() if cell.meeting_time else None,
        created_at=cell.created_at,
    )


@router.patch("/admin/cells/{cell_id}", response_model=CellResponse)
async def update_cell(
    cell_id: UUID,
    request: CellUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update cell. Fellowship pastor and above."""
    check_fellowship_pastor(current_user)

    cell = await AdminService.get_cell_by_id(session, cell_id)
    if not cell:
        raise HTTPException(status_code=404, detail="Cell not found")
    await ensure_cell_access(session, current_user, cell_id)

    try:
        if request.name:
            cell.name = request.name
        if request.default_meeting_day:
            cell.default_meeting_day = request.default_meeting_day
        if request.meeting_time:
            try:
                h, m = map(int, request.meeting_time.split(":"))
                cell.meeting_time = time_type(h, m)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid time format")

        await session.commit()
        await session.refresh(cell)

        return CellResponse(
            id=str(cell.id),
            name=cell.name,
            senior_cell_id=str(cell.senior_cell_id),
            default_meeting_day=cell.default_meeting_day,
            meeting_time=cell.meeting_time.isoformat() if cell.meeting_time else None,
            created_at=cell.created_at,
        )

    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Cell update failed")


@router.delete("/admin/cells/{cell_id}")
async def delete_cell(
    cell_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete cell. Fellowship pastor and above."""
    check_fellowship_pastor(current_user)

    cell = await AdminService.get_cell_by_id(session, cell_id)
    if not cell:
        raise HTTPException(status_code=404, detail="Cell not found")
    await ensure_cell_access(session, current_user, cell_id)

    try:
        await session.delete(cell)
        await session.commit()
        return {"message": "Cell deleted"}

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Cell deletion failed")


# ═══════════════════════════════════════════════════════════════════════════════
# USER MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/admin/users", response_model=UserCreateResponse)
async def create_user(
    request: UserCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create user with role-based hierarchy assignment"""
    check_system_admin(current_user)

    try:
        # Check phone doesn't already exist
        if await AdminService.phone_exists(session, request.phone):
            raise HTTPException(status_code=409, detail="Phone number already registered")

        role_value = request.role.value
        zone_id = request.zone_id
        fellowship_id = request.fellowship_id
        senior_cell_id = request.senior_cell_id
        cell_id = request.cell_id

        # Validate hierarchy based on role
        if role_value in {"zonal_admin", "zonal_pastor"}:
            zone = await AdminService.get_zone_by_id(session, zone_id)
            if not zone:
                raise HTTPException(status_code=404, detail="Zone not found")

        elif role_value == "fellowship_pastor":
            fellowship = await AdminService.get_fellowship_by_id(session, fellowship_id)
            if not fellowship:
                raise HTTPException(status_code=404, detail="Fellowship not found")
            zone_id = fellowship.zone_id

        elif role_value == "senior_cell_leader":
            senior_cell = await AdminService.get_senior_cell_by_id(session, senior_cell_id)
            if not senior_cell:
                raise HTTPException(status_code=404, detail="Senior cell not found")
            fellowship = await AdminService.get_fellowship_by_id(session, senior_cell.fellowship_id)
            fellowship_id = senior_cell.fellowship_id
            zone_id = fellowship.zone_id if fellowship else None

        elif role_value == "cell_leader":
            cell = await AdminService.get_cell_by_id(session, cell_id)
            if not cell:
                raise HTTPException(status_code=404, detail="Cell not found")
            senior_cell = await AdminService.get_senior_cell_by_id(session, cell.senior_cell_id)
            fellowship = await AdminService.get_fellowship_by_id(session, senior_cell.fellowship_id) if senior_cell else None
            senior_cell_id = cell.senior_cell_id
            fellowship_id = senior_cell.fellowship_id if senior_cell else None
            zone_id = fellowship.zone_id if fellowship else None

        # Create user
        new_user = User(
            phone=request.phone,
            name=request.name,
            pin_hash=hash_default_pin(),  # 123456
            role=role_value,
            zone_id=zone_id,
            fellowship_id=fellowship_id,
            senior_cell_id=senior_cell_id,
            cell_id=cell_id,
            is_active=True,
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        return UserCreateResponse(
            user_id=str(new_user.id),
            phone=new_user.phone,
            name=new_user.name,
            role=new_user.role,
            initial_pin="123456",
            message=f"User created. Phone: {new_user.phone}, PIN: 123456. Share with user via WhatsApp.",
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"User creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="User creation failed")


# ═══════════════════════════════════════════════════════════════════════════════
# FELLOWSHIP MANAGEMENT - CELL ASSIGNMENT & ACTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/admin/cells/{cell_id}/assign-senior-cell")
async def assign_cell_to_senior_cell(
    cell_id: UUID,
    senior_cell_id: UUID = Query(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Assign a cell to a senior cell. Fellowship pastor and above."""
    check_fellowship_pastor(current_user)

    try:
        # Verify cell exists
        cell = await AdminService.get_cell_by_id(session, cell_id)
        if not cell:
            raise HTTPException(status_code=404, detail="Cell not found")
        
        # Verify senior cell exists
        senior_cell = await AdminService.get_senior_cell_by_id(session, senior_cell_id)
        if not senior_cell:
            raise HTTPException(status_code=404, detail="Senior cell not found")
        
        # Check permission
        await ensure_fellowship_access(session, current_user, senior_cell.fellowship_id)
        
        # Assign cell
        cell.senior_cell_id = senior_cell_id
        await session.commit()
        await session.refresh(cell)
        
        return {
            "message": "Cell assigned to senior cell successfully",
            "cell_id": str(cell.id),
            "senior_cell_id": str(senior_cell_id)
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Cell assignment failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Cell assignment failed")


@router.post("/admin/users/{user_id}/poke")
async def poke_cell_leader(
    user_id: UUID,
    message: str = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Send in-app notification to cell leader for unsubmitted report"""
    check_fellowship_pastor(current_user)

    try:
        # Get user to poke
        user = await AdminService.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check permission - can only poke cell leaders in your fellowship
        if current_user.role == "fellowship_pastor":
            if user.fellowship_id != current_user.fellowship_id:
                raise HTTPException(status_code=403, detail="User not in your fellowship")
        
        # Create notification
        default_message = f"Please submit your cell report for this week. We're waiting for your update!"
        notification_message = message or default_message
        
        notification = await AdminService.create_notification(
            session=session,
            user_id=user_id,
            message=notification_message,
            notification_type="manual_nudge"
        )
        
        await session.commit()
        
        return {
            "message": "Notification sent successfully",
            "notification_id": str(notification.id),
            "user_id": str(user_id)
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Poke failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send notification")


@router.post("/admin/cell-reports/{report_id}/validate")
async def validate_cell_report(
    report_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Validate a cell report"""
    check_fellowship_pastor(current_user)

    try:
        from models import CellReport
        from datetime import datetime
        
        # Get report
        result = await session.execute(
            select(CellReport).where(CellReport.id == report_id)
        )
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Get cell and check permission
        cell = await AdminService.get_cell_by_id(session, report.cell_id)
        if cell.senior_cell_id:
            senior_cell = await AdminService.get_senior_cell_by_id(session, cell.senior_cell_id)
            if senior_cell:
                await ensure_fellowship_access(session, current_user, senior_cell.fellowship_id)
        
        # Validate report
        report.is_validated = True
        report.status = "VALIDATED"
        report.validated_by_id = current_user.id
        report.validated_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(report)
        
        return {
            "message": "Report validated successfully",
            "report_id": str(report.id),
            "status": report.status
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Report validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Report validation failed")


@router.post("/admin/cell-reports/{report_id}/confirm-finances")
async def confirm_report_finances(
    report_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Confirm finances for a cell report"""
    check_fellowship_pastor(current_user)

    try:
        from models import CellReport
        from datetime import datetime
        
        # Get report
        result = await session.execute(
            select(CellReport).where(CellReport.id == report_id)
        )
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Get cell and check permission
        cell = await AdminService.get_cell_by_id(session, report.cell_id)
        if cell.senior_cell_id:
            senior_cell = await AdminService.get_senior_cell_by_id(session, cell.senior_cell_id)
            if senior_cell:
                await ensure_fellowship_access(session, current_user, senior_cell.fellowship_id)
        
        # Confirm finances
        report.finance_confirmed = True
        report.finance_confirmed_by_id = current_user.id
        report.finance_confirmed_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(report)
        
        return {
            "message": "Finances confirmed successfully",
            "report_id": str(report.id),
            "total_finances": float(report.finance_total or 0)
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Finance confirmation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Finance confirmation failed")
        raise HTTPException(status_code=500, detail="User creation failed")


@router.get("/admin/users")
async def list_users(
    zone_id: Optional[UUID] = Query(None),
    role: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List users. Filter by zone_id or role if provided."""
    if current_user.role not in {"system_admin", "zonal_admin"}:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    try:
        query = select(User)

        if current_user.role == "zonal_admin":
            query = query.where(User.zone_id == current_user.zone_id)
            if zone_id and zone_id != current_user.zone_id:
                raise HTTPException(status_code=403, detail="Can only list users in your zone")
        elif zone_id:
            query = query.where(User.zone_id == zone_id)

        if role:
            query = query.where(User.role == role)

        result = await session.execute(query)
        users = result.scalars().all()

        return [
            {
                "id": str(u.id),
                "phone": u.phone,
                "name": u.name,
                "role": u.role,
                "zone_id": str(u.zone_id) if u.zone_id else None,
                "fellowship_id": str(u.fellowship_id) if u.fellowship_id else None,
                "senior_cell_id": str(u.senior_cell_id) if u.senior_cell_id else None,
                "cell_id": str(u.cell_id) if u.cell_id else None,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ]

    except Exception as e:
        logger.error(f"User list failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list users")


@router.get("/admin/users/{user_id}")
async def get_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get user details"""
    check_system_admin(current_user)

    user = await AdminService.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user.id),
        "phone": user.phone,
        "name": user.name,
        "role": user.role,
        "zone_id": str(user.zone_id) if user.zone_id else None,
        "fellowship_id": str(user.fellowship_id) if user.fellowship_id else None,
        "senior_cell_id": str(user.senior_cell_id) if user.senior_cell_id else None,
        "cell_id": str(user.cell_id) if user.cell_id else None,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
    }


@router.patch("/admin/users/{user_id}")
async def update_user(
    user_id: UUID,
    request: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update user. System admin only."""
    check_system_admin(current_user)

    user = await AdminService.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        if request.name:
            user.name = request.name
        if request.phone:
            user.phone = request.phone
        if request.zone_id:
            user.zone_id = request.zone_id
        if request.fellowship_id:
            user.fellowship_id = request.fellowship_id
        if request.senior_cell_id:
            user.senior_cell_id = request.senior_cell_id
        if request.cell_id:
            user.cell_id = request.cell_id

        await session.commit()
        await session.refresh(user)

        return {
            "id": str(user.id),
            "phone": user.phone,
            "name": user.name,
            "role": user.role,
            "is_active": user.is_active,
            "message": "User updated",
        }

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="User update failed")


@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Deactivate user. System admin only."""
    check_system_admin(current_user)

    user = await AdminService.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        user.is_active = False
        await session.commit()
        return {"message": "User deactivated"}

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="User deactivation failed")


@router.post("/admin/users/{user_id}/reset-pin")
async def reset_user_pin(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Reset user PIN to 123456. System admin only."""
    check_system_admin(current_user)

    user = await AdminService.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        user.pin_hash = hash_default_pin()
        await session.commit()

        return {
            "message": "PIN reset to 123456",
            "user_phone": user.phone,
            "new_pin": "123456",
        }

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="PIN reset failed")
