from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from uuid import UUID
from typing import Optional
from datetime import time as time_type
 
from database import get_session
from models import User, Cell, Zone, Fellowship, SeniorCell
from schemas import UserCreate, UserCreateResponse
from auth import hash_default_pin, decode_token
 
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
 
 
@router.post("/admin/users", response_model=UserCreateResponse)
async def create_user(
    request: UserCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create new user with role-based permissions"""
    try:
        # Check permissions
        if current_user.role == "system_admin":
            pass
        elif current_user.role == "zonal_admin":
            if request.zone_id != current_user.zone_id:
                raise HTTPException(status_code=403, detail="Can only create users in your zone")
        elif current_user.role == "fellowship_pastor":
            if request.fellowship_id != current_user.fellowship_id:
                raise HTTPException(status_code=403, detail="Can only create users in your fellowship")
        else:
            raise HTTPException(status_code=403, detail="Permission denied")
 
        # Check phone uniqueness
        result = await session.execute(select(User).where(User.phone == request.phone))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Phone already exists")
 
        # Validate cell_id if provided
        if request.cell_id:
            result = await session.execute(select(Cell).where(Cell.id == request.cell_id))
            if not result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="Cell not found")
 
        # Create user
        new_user = User(
            phone=request.phone,
            name=request.name,
            pin_hash=hash_default_pin(),
            role=request.role,
            cell_id=request.cell_id,
            senior_cell_id=request.senior_cell_id,
            fellowship_id=request.fellowship_id,
            zone_id=request.zone_id,
            is_active=True,
        )
 
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
 
        return UserCreateResponse(
            user_id=new_user.id,
            phone=new_user.phone,
            name=new_user.name,
            role=new_user.role,
            initial_pin="123456",
            message="User created. Share phone and PIN with leader.",
        )
 
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="User creation failed")
 
 
@router.post("/admin/fellowships")
async def create_fellowship(
    name: str,
    location: str,
    zone_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create fellowship. Zonal Admin only."""
    if current_user.role != "zonal_admin":
        raise HTTPException(status_code=403, detail="Only zonal admin can create fellowships")
 
    result = await session.execute(select(Zone).where(Zone.id == zone_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Zone not found")
 
    fellowship = Fellowship(name=name, location=location, zone_id=zone_id)
    session.add(fellowship)
    await session.commit()
    await session.refresh(fellowship)
 
    return {
        "id": str(fellowship.id),
        "name": fellowship.name,
        "location": fellowship.location,
        "zone_id": str(fellowship.zone_id),
    }
 
 
@router.post("/admin/senior-cells")
async def create_senior_cell(
    name: str,
    fellowship_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create senior cell. Fellowship Pastor only."""
    if current_user.role != "fellowship_pastor":
        raise HTTPException(status_code=403, detail="Only fellowship pastor can create senior cells")
 
    result = await session.execute(select(Fellowship).where(Fellowship.id == fellowship_id))
    fellowship = result.scalar_one_or_none()
    if not fellowship:
        raise HTTPException(status_code=404, detail="Fellowship not found")
 
    if fellowship.id != current_user.fellowship_id:
        raise HTTPException(status_code=403, detail="Can only create in your fellowship")
 
    senior_cell = SeniorCell(name=name, fellowship_id=fellowship_id)
    session.add(senior_cell)
    await session.commit()
    await session.refresh(senior_cell)
 
    return {"id": str(senior_cell.id), "name": senior_cell.name}
 
 
@router.post("/admin/cells")
async def create_cell(
    name: str,
    senior_cell_id: UUID,
    default_meeting_day: str = "monday",
    meeting_time: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create cell. Fellowship Pastor or Senior Cell Leader."""
    result = await session.execute(select(SeniorCell).where(SeniorCell.id == senior_cell_id))
    senior_cell = result.scalar_one_or_none()
    if not senior_cell:
        raise HTTPException(status_code=404, detail="Senior cell not found")
 
    if current_user.role == "fellowship_pastor":
        if senior_cell.fellowship_id != current_user.fellowship_id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == "senior_cell_leader":
        if senior_cell.id != current_user.senior_cell_id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        raise HTTPException(status_code=403, detail="Permission denied")
 
    meeting_time_obj = None
    if meeting_time:
        try:
            h, m = map(int, meeting_time.split(":"))
            meeting_time_obj = time_type(h, m)
        except:
            raise HTTPException(status_code=400, detail="Invalid time format")
 
    cell = Cell(
        name=name,
        senior_cell_id=senior_cell_id,
        default_meeting_day=default_meeting_day,
        meeting_time=meeting_time_obj,
    )
 
    session.add(cell)
    await session.commit()
    await session.refresh(cell)
 
    return {"id": str(cell.id), "name": cell.name}