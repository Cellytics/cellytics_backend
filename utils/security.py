from typing import Iterable, Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import decode_token
from database import get_session
from models import Cell, CellReport, Fellowship, SeniorCell, User, Zone


SYSTEM_ROLES = {"system_admin"}
ZONE_ROLES = {"zonal_admin", "zonal_pastor"}
FELLOWSHIP_ROLES = {"fellowship_pastor"}
SENIOR_CELL_ROLES = {"senior_cell_leader"}
CELL_ROLES = {"cell_leader"}


async def get_current_user(
    authorization: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Extract the active user from the bearer token."""
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

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await session.execute(
        select(User).where(User.id == user_uuid, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def require_roles(user: User, roles: Iterable[str], detail: str = "Permission denied") -> None:
    if user.role not in set(roles):
        raise HTTPException(status_code=403, detail=detail)


def require_system_admin(user: User) -> None:
    require_roles(user, SYSTEM_ROLES, "Only system admin can perform this action")


def require_zonal_admin_or_above(user: User) -> None:
    require_roles(user, SYSTEM_ROLES | {"zonal_admin"}, "Only zonal admin can perform this action")


def require_fellowship_pastor_or_above(user: User) -> None:
    require_roles(user, SYSTEM_ROLES | {"zonal_admin"} | FELLOWSHIP_ROLES, "Permission denied")


def require_senior_cell_leader_or_above(user: User) -> None:
    require_roles(
        user,
        SYSTEM_ROLES | {"zonal_admin"} | FELLOWSHIP_ROLES | SENIOR_CELL_ROLES,
        "Permission denied",
    )


async def get_fellowship_for_senior_cell(
    session: AsyncSession,
    senior_cell_id: UUID,
) -> Optional[Fellowship]:
    result = await session.execute(
        select(Fellowship)
        .join(SeniorCell, SeniorCell.fellowship_id == Fellowship.id)
        .where(SeniorCell.id == senior_cell_id)
    )
    return result.scalar_one_or_none()


async def get_fellowship_for_cell(session: AsyncSession, cell_id: UUID) -> Optional[Fellowship]:
    result = await session.execute(
        select(Fellowship)
        .join(SeniorCell, SeniorCell.fellowship_id == Fellowship.id)
        .join(Cell, Cell.senior_cell_id == SeniorCell.id)
        .where(Cell.id == cell_id)
    )
    return result.scalar_one_or_none()


async def get_cell_by_report_id(session: AsyncSession, report_id: UUID) -> Optional[Cell]:
    result = await session.execute(
        select(Cell)
        .join(CellReport, CellReport.cell_id == Cell.id)
        .where(CellReport.id == report_id)
    )
    return result.scalar_one_or_none()


async def can_access_zone(user: User, zone_id: UUID) -> bool:
    if user.role in SYSTEM_ROLES:
        return True
    if user.role in ZONE_ROLES:
        return user.zone_id == zone_id
    return False


async def can_access_fellowship(
    session: AsyncSession,
    user: User,
    fellowship_id: UUID,
) -> bool:
    if user.role in SYSTEM_ROLES:
        return True
    if user.role in FELLOWSHIP_ROLES:
        return user.fellowship_id == fellowship_id

    result = await session.execute(select(Fellowship).where(Fellowship.id == fellowship_id))
    fellowship = result.scalar_one_or_none()
    if not fellowship:
        return False

    if user.role in ZONE_ROLES:
        return user.zone_id == fellowship.zone_id
    return False


async def can_access_senior_cell(
    session: AsyncSession,
    user: User,
    senior_cell_id: UUID,
) -> bool:
    if user.role in SYSTEM_ROLES:
        return True
    if user.role in SENIOR_CELL_ROLES:
        return user.senior_cell_id == senior_cell_id

    fellowship = await get_fellowship_for_senior_cell(session, senior_cell_id)
    if not fellowship:
        return False

    if user.role in FELLOWSHIP_ROLES:
        return user.fellowship_id == fellowship.id
    if user.role in ZONE_ROLES:
        return user.zone_id == fellowship.zone_id
    return False


async def can_access_cell(session: AsyncSession, user: User, cell_id: UUID) -> bool:
    if user.role in SYSTEM_ROLES:
        return True
    if user.role in CELL_ROLES:
        return user.cell_id == cell_id

    result = await session.execute(select(Cell).where(Cell.id == cell_id))
    cell = result.scalar_one_or_none()
    if not cell:
        return False

    if user.role in SENIOR_CELL_ROLES:
        return user.senior_cell_id == cell.senior_cell_id

    fellowship = await get_fellowship_for_cell(session, cell_id)
    if not fellowship:
        return False

    if user.role in FELLOWSHIP_ROLES:
        return user.fellowship_id == fellowship.id
    if user.role in ZONE_ROLES:
        return user.zone_id == fellowship.zone_id
    return False


async def can_access_report(session: AsyncSession, user: User, report_id: UUID) -> bool:
    if user.role in SYSTEM_ROLES:
        return True
    cell = await get_cell_by_report_id(session, report_id)
    if not cell:
        return False
    return await can_access_cell(session, user, cell.id)


async def ensure_zone_access(user: User, zone_id: UUID) -> None:
    if not await can_access_zone(user, zone_id):
        raise HTTPException(status_code=403, detail="Access denied")


async def ensure_fellowship_access(session: AsyncSession, user: User, fellowship_id: UUID) -> None:
    if not await can_access_fellowship(session, user, fellowship_id):
        raise HTTPException(status_code=403, detail="Access denied")


async def ensure_senior_cell_access(session: AsyncSession, user: User, senior_cell_id: UUID) -> None:
    if not await can_access_senior_cell(session, user, senior_cell_id):
        raise HTTPException(status_code=403, detail="Access denied")


async def ensure_cell_access(session: AsyncSession, user: User, cell_id: UUID) -> None:
    if not await can_access_cell(session, user, cell_id):
        raise HTTPException(status_code=403, detail="Access denied")


async def ensure_report_access(session: AsyncSession, user: User, report_id: UUID) -> None:
    if not await can_access_report(session, user, report_id):
        raise HTTPException(status_code=403, detail="Access denied")


def scoped_zone_query(query, user: User):
    if user.role in SYSTEM_ROLES:
        return query
    if user.zone_id:
        return query.where(Zone.id == user.zone_id)
    return query.where(False)


def scoped_fellowship_query(query, user: User):
    if user.role in SYSTEM_ROLES:
        return query
    if user.role in ZONE_ROLES and user.zone_id:
        return query.where(Fellowship.zone_id == user.zone_id)
    if user.fellowship_id:
        return query.where(Fellowship.id == user.fellowship_id)
    return query.where(False)


def scoped_senior_cell_query(query, user: User):
    if user.role in SYSTEM_ROLES:
        return query
    if user.role in ZONE_ROLES and user.zone_id:
        return query.join(Fellowship, SeniorCell.fellowship_id == Fellowship.id).where(
            Fellowship.zone_id == user.zone_id
        )
    if user.role in FELLOWSHIP_ROLES and user.fellowship_id:
        return query.where(SeniorCell.fellowship_id == user.fellowship_id)
    if user.senior_cell_id:
        return query.where(SeniorCell.id == user.senior_cell_id)
    return query.where(False)


def scoped_cell_query(query, user: User):
    if user.role in SYSTEM_ROLES:
        return query
    if user.role in ZONE_ROLES and user.zone_id:
        return (
            query.join(SeniorCell, Cell.senior_cell_id == SeniorCell.id)
            .join(Fellowship, SeniorCell.fellowship_id == Fellowship.id)
            .where(Fellowship.zone_id == user.zone_id)
        )
    if user.role in FELLOWSHIP_ROLES and user.fellowship_id:
        return query.join(SeniorCell, Cell.senior_cell_id == SeniorCell.id).where(
            SeniorCell.fellowship_id == user.fellowship_id
        )
    if user.role in SENIOR_CELL_ROLES and user.senior_cell_id:
        return query.where(Cell.senior_cell_id == user.senior_cell_id)
    if user.cell_id:
        return query.where(Cell.id == user.cell_id)
    return query.where(False)


def scoped_report_query(query, user: User):
    if user.role in SYSTEM_ROLES:
        return query
    if user.role in ZONE_ROLES and user.zone_id:
        return (
            query.join(Cell, CellReport.cell_id == Cell.id)
            .join(SeniorCell, Cell.senior_cell_id == SeniorCell.id)
            .join(Fellowship, SeniorCell.fellowship_id == Fellowship.id)
            .where(Fellowship.zone_id == user.zone_id)
        )
    if user.role in FELLOWSHIP_ROLES and user.fellowship_id:
        return (
            query.join(Cell, CellReport.cell_id == Cell.id)
            .join(SeniorCell, Cell.senior_cell_id == SeniorCell.id)
            .where(SeniorCell.fellowship_id == user.fellowship_id)
        )
    if user.role in SENIOR_CELL_ROLES and user.senior_cell_id:
        return query.join(Cell, CellReport.cell_id == Cell.id).where(
            Cell.senior_cell_id == user.senior_cell_id
        )
    if user.cell_id:
        return query.where(CellReport.cell_id == user.cell_id)
    return query.where(False)
