# services/admin_service.py - Business logic for admin operations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from models import Zone, Fellowship, SeniorCell, Cell, User
from auth import hash_default_pin


class AdminService:
    """Business logic for admin hierarchy and user management"""
###
    @staticmethod
    async def validate_zone_exists(session: AsyncSession, zone_id: UUID) -> bool:
        """Check if zone exists"""
        result = await session.execute(
            select(Zone).where(Zone.id == zone_id)
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def validate_fellowship_belongs_to_zone(
        session: AsyncSession,
        fellowship_id: UUID,
        zone_id: UUID
    ) -> bool:
        """Ensure fellowship belongs to specified zone"""
        result = await session.execute(
            select(Fellowship).where(
                Fellowship.id == fellowship_id,
                Fellowship.zone_id == zone_id
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def validate_senior_cell_belongs_to_fellowship(
        session: AsyncSession,
        senior_cell_id: UUID,
        fellowship_id: UUID
    ) -> bool:
        """Ensure senior cell belongs to specified fellowship"""
        result = await session.execute(
            select(SeniorCell).where(
                SeniorCell.id == senior_cell_id,
                SeniorCell.fellowship_id == fellowship_id
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def validate_cell_belongs_to_senior_cell(
        session: AsyncSession,
        cell_id: UUID,
        senior_cell_id: UUID
    ) -> bool:
        """Ensure cell belongs to specified senior cell"""
        result = await session.execute(
            select(Cell).where(
                Cell.id == cell_id,
                Cell.senior_cell_id == senior_cell_id
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def phone_exists(session: AsyncSession, phone: str) -> bool:
        """Check if phone already registered"""
        result = await session.execute(
            select(User).where(User.phone == phone)
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_zone_by_id(session: AsyncSession, zone_id: UUID) -> Zone:
        """Get zone by ID"""
        result = await session.execute(
            select(Zone).where(Zone.id == zone_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_fellowship_by_id(session: AsyncSession, fellowship_id: UUID) -> Fellowship:
        """Get fellowship by ID"""
        result = await session.execute(
            select(Fellowship).where(Fellowship.id == fellowship_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_senior_cell_by_id(session: AsyncSession, senior_cell_id: UUID) -> SeniorCell:
        """Get senior cell by ID"""
        result = await session.execute(
            select(SeniorCell).where(SeniorCell.id == senior_cell_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_cell_by_id(session: AsyncSession, cell_id: UUID) -> Cell:
        """Get cell by ID"""
        result = await session.execute(
            select(Cell).where(Cell.id == cell_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User:
        """Get user by ID"""
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_users_in_zone(session: AsyncSession, zone_id: UUID):
        """List all users in a zone"""
        result = await session.execute(
            select(User).where(User.zone_id == zone_id)
        )
        return result.scalars().all()

    @staticmethod
    async def list_fellowships_in_zone(session: AsyncSession, zone_id: UUID):
        """List all fellowships in a zone"""
        result = await session.execute(
            select(Fellowship).where(Fellowship.zone_id == zone_id)
        )
        return result.scalars().all()

    @staticmethod
    async def list_senior_cells_in_fellowship(session: AsyncSession, fellowship_id: UUID):
        """List all senior cells in a fellowship"""
        result = await session.execute(
            select(SeniorCell).where(SeniorCell.fellowship_id == fellowship_id)
        )
        return result.scalars().all()

    @staticmethod
    async def list_cells_in_senior_cell(session: AsyncSession, senior_cell_id: UUID):
        """List all cells in a senior cell"""
        result = await session.execute(
            select(Cell).where(Cell.senior_cell_id == senior_cell_id)
        )
        return result.scalars().all()

    @staticmethod
    def get_user_hierarchy_based_on_role(user_role: str) -> dict:
        """Get required hierarchy fields based on role"""
        hierarchy_requirements = {
            "system_admin": [],
            "zonal_admin": ["zone_id"],
            "fellowship_pastor": ["fellowship_id"],
            "senior_cell_leader": ["senior_cell_id"],
            "cell_leader": ["cell_id"],
        }
        return hierarchy_requirements.get(user_role, [])