from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import logging

from database import get_session
from models import User, Cell, SeniorCell, Fellowship, Zone
from schemas import LoginRequest, LoginResponse
from auth import verify_pin, create_access_token

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/auth/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_session)
):
    """Login with phone and PIN. Returns JWT token + full user context."""
    try:
        logger.info(f"Login attempt for phone: {request.phone}")

        result = await session.execute(
            select(User).where(
                User.phone == request.phone,
                User.is_active == True
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"User not found for phone: {request.phone}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid phone number or PIN",
            )

        if not verify_pin(request.pin, user.pin_hash):
            logger.warning(f"Invalid PIN for user: {user.name}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid phone number or PIN",
            )

        # ── Resolve display names for all scope levels ──────────────────────
        cell_name = None
        senior_cell_name = None
        fellowship_name = None
        zone_name = None

        if user.cell_id:
            cell_res = await session.execute(
                select(Cell.name).where(Cell.id == user.cell_id)
            )
            cell_name = cell_res.scalar_one_or_none()

        if user.senior_cell_id:
            sc_res = await session.execute(
                select(SeniorCell.name).where(SeniorCell.id == user.senior_cell_id)
            )
            senior_cell_name = sc_res.scalar_one_or_none()

        if user.fellowship_id:
            f_res = await session.execute(
                select(Fellowship.name).where(Fellowship.id == user.fellowship_id)
            )
            fellowship_name = f_res.scalar_one_or_none()

        if user.zone_id:
            z_res = await session.execute(
                select(Zone.name).where(Zone.id == user.zone_id)
            )
            zone_name = z_res.scalar_one_or_none()

        # ── Update last login ───────────────────────────────────────────────
        user.last_login = datetime.utcnow()
        await session.commit()

        access_token = create_access_token(subject=str(user.id))

        logger.info(
            f"Login success: {user.name} | role: {user.role} | "
            f"cell: {cell_name} | fellowship: {fellowship_name}"
        )

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": str(user.id),
                "phone": user.phone,
                "name": user.name,
                "role": user.role.value if hasattr(user.role, "value") else str(user.role),

                # IDs
                "cell_id": str(user.cell_id) if user.cell_id else None,
                "senior_cell_id": str(user.senior_cell_id) if user.senior_cell_id else None,
                "fellowship_id": str(user.fellowship_id) if user.fellowship_id else None,
                "zone_id": str(user.zone_id) if user.zone_id else None,

                # Display names (needed by Flutter home screen)
                "cell_name": cell_name,
                "senior_cell_name": senior_cell_name,
                "fellowship_name": fellowship_name,
                "zone_name": zone_name,

                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected login error for {request.phone}: {e}")
        raise HTTPException(status_code=500, detail="Login failed")










# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select
# from datetime import datetime
# import logging
 
# from database import get_session
# from models import User
# from schemas import LoginRequest, LoginResponse
# from auth import verify_pin, create_access_token
 
# logger = logging.getLogger(__name__)
 
# router = APIRouter()
 
# @router.post("/auth/login", response_model=LoginResponse)
# async def login(
#     request: LoginRequest,
#     session: AsyncSession = Depends(get_session)
# ):
#     """Login with phone and PIN. Returns JWT token."""
#     try:
#         logger.info(f"Login attempt for phone: {request.phone}")
        
#         result = await session.execute(
#             select(User).where(User.phone == request.phone, User.is_active == True)
#         )
#         user = result.scalar_one_or_none()
 
#         if not user:
#             logger.warning(f"User not found for phone: {request.phone}")
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid phone or PIN",
#             )
 
#         pin_valid = verify_pin(request.pin, user.pin_hash)
#         logger.info(f"PIN verification for user {user.name}: {pin_valid}")
        
#         if not pin_valid:
#             logger.warning(f"Invalid PIN for user: {user.name}")
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid phone or PIN",
#             )
 
#         user.last_login = datetime.utcnow()
#         await session.commit()
 
#         access_token = create_access_token(subject=str(user.id))
 
#         return LoginResponse(
#             access_token=access_token,
#             token_type="bearer",
#             user={
#                 "id": str(user.id),
#                 "phone": user.phone,
#                 "name": user.name,
#                 "role": user.role,
#                 "cell_id": str(user.cell_id) if user.cell_id else None,
#                 "senior_cell_id": str(user.senior_cell_id) if user.senior_cell_id else None,
#                 "fellowship_id": str(user.fellowship_id) if user.fellowship_id else None,
#                 "zone_id": str(user.zone_id) if user.zone_id else None,
#                 "is_active": user.is_active,
#             }
#         )
 
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="Login failed")
 
 
