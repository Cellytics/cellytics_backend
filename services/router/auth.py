from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
 
from database import get_session
from models import User
from schemas import LoginRequest, LoginResponse
from auth import verify_pin, create_access_token
 
router = APIRouter()
 
@router.post("/auth/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_session)
):
    """Login with phone and PIN. Returns JWT token."""
    try:
        result = await session.execute(
            select(User).where(User.phone == request.phone, User.is_active == True)
        )
        user = result.scalar_one_or_none()
 
        if not user or not verify_pin(request.pin, user.pin_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid phone or PIN",
            )
 
        user.last_login = datetime.utcnow()
        await session.commit()
 
        access_token = create_access_token(subject=str(user.id))
 
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": str(user.id),
                "phone": user.phone,
                "name": user.name,
                "role": user.role,
                "cell_id": str(user.cell_id) if user.cell_id else None,
                "senior_cell_id": str(user.senior_cell_id) if user.senior_cell_id else None,
                "fellowship_id": str(user.fellowship_id) if user.fellowship_id else None,
                "zone_id": str(user.zone_id) if user.zone_id else None,
            }
        )
 
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Login failed")
 
 