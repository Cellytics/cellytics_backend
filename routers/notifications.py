from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from uuid import UUID
from typing import Optional
 
from database import get_session
from models import User, Cell, Notification
from auth import decode_token
 
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
 
 
@router.post("/users/fcm-token")
async def update_fcm_token(
    fcm_token: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Register FCM token for push notifications"""
    try:
        current_user.fcm_token = fcm_token
        await session.commit()
 
        return {
            "success": True,
            "message": "FCM token updated",
            "user_id": str(current_user.id),
        }
 
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update FCM token")
 
 
@router.post("/notifications/send-nudge/{cell_id}")
async def send_nudge(
    cell_id: UUID,
    message: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Send manual nudge/reminder to cell leader"""
    try:
        if current_user.role not in ["fellowship_pastor", "zonal_admin", "system_admin"]:
            raise HTTPException(status_code=403, detail="Permission denied")
 
        result = await session.execute(
            select(Cell).where(Cell.id == cell_id)
        )
        cell = result.scalar_one_or_none()
 
        if not cell:
            raise HTTPException(status_code=404, detail="Cell not found")
 
        # Create notification
        notification = Notification(
            user_id=cell.leader_id,
            message=message,
            type="manual_nudge",
            fcm_token=cell.leader.fcm_token if cell.leader else None,
            is_sent=True,
            sent_at=datetime.utcnow(),
        )
        session.add(notification)
        await session.commit()
 
        return {
            "success": True,
            "cell_name": cell.name,
            "leader_name": cell.leader.name if cell.leader else "Unknown",
            "message": message,
        }
 
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send nudge")
 
 
@router.get("/notifications")
async def get_notifications(
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get user's notifications"""
    try:
        result = await session.execute(
            select(Notification)
            .where(Notification.user_id == current_user.id)
            .order_by(desc(Notification.created_at))
            .offset(offset)
            .limit(limit)
        )
        notifications = result.scalars().all()
 
        return {
            "count": len(notifications),
            "offset": offset,
            "limit": limit,
            "notifications": [
                {
                    "id": str(n.id),
                    "message": n.message,
                    "type": n.type,
                    "is_read": n.is_read,
                    "created_at": n.created_at.isoformat(),
                }
                for n in notifications
            ]
        }
 
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch notifications")
 