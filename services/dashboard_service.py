from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, date, timedelta
from uuid import UUID
 
from models import Cell, CellReport, SeniorCell, Fellowship, Zone
from utils.helpers import get_current_week
 
 
class DashboardService:
    """Business logic for dashboards"""
 
    @staticmethod
    async def build_senior_cell_dashboard(
        session: AsyncSession,
        senior_cell_id: UUID
    ) -> dict:
        """Build Senior Cell Leader dashboard"""
 
        result = await session.execute(
            select(SeniorCell).where(SeniorCell.id == senior_cell_id)
        )
        senior_cell = result.scalar_one_or_none()
 
        week_start, week_end = get_current_week()
 
        # Get all cells
        result = await session.execute(
            select(Cell).where(Cell.senior_cell_id == senior_cell_id, Cell.is_active == True)
        )
        cells = result.scalars().all()
        cell_ids = [c.id for c in cells]
 
        # Get reports this week
        result = await session.execute(
            select(CellReport).where(
                CellReport.cell_id.in_(cell_ids),
                CellReport.week_start_date == week_start
            )
        )
        reports = result.scalars().all()
        reports_dict = {r.cell_id: r for r in reports}
 
        # Build response
        cell_statuses = []
        total_attendance = 0
        total_souls_won = 0
        total_finances = 0.0
 
        for cell in cells:
            report = reports_dict.get(cell.id)
            if report:
                status_val = report.status.upper()
                attendance = report.total_attendance or 0
                souls_won = report.souls_won or 0
                finance = float(report.finance_total or 0)
                total_attendance += attendance
                total_souls_won += souls_won
                total_finances += finance
            else:
                status_val = "NO_REPORT"
                attendance = 0
                souls_won = 0
                finance = 0
 
            cell_statuses.append({
                "cell_id": str(cell.id),
                "cell_name": cell.name,
                "leader_name": cell.leader_name or "Unassigned",
                "status": status_val,
                "attendance": attendance,
                "souls_won": souls_won,
                "finance": finance,
            })
 
        submission_rate = (len(reports) / len(cells) * 100) if cells else 0
 
        return {
            "dashboard_type": "senior_cell_leader",
            "senior_cell_id": str(senior_cell.id),
            "senior_cell_name": senior_cell.name,
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "total_cells": len(cells),
            "cells_reported": len(reports),
            "submission_rate_percent": round(submission_rate, 1),
            "total_attendance": total_attendance,
            "total_souls_won": total_souls_won,
            "total_finances": round(total_finances, 2),
            "cells": cell_statuses,
        }
 
    @staticmethod
    async def build_fellowship_dashboard(
        session: AsyncSession,
        fellowship_id: UUID
    ) -> dict:
        """Build Fellowship Pastor dashboard"""
 
        result = await session.execute(
            select(Fellowship).where(Fellowship.id == fellowship_id)
        )
        fellowship = result.scalar_one_or_none()
 
        week_start, week_end = get_current_week()
 
        # Get all senior cells
        result = await session.execute(
            select(SeniorCell).where(SeniorCell.fellowship_id == fellowship_id)
        )
        senior_cells = result.scalars().all()
        sc_ids = [sc.id for sc in senior_cells]
 
        # Get all cells
        result = await session.execute(
            select(Cell).where(Cell.senior_cell_id.in_(sc_ids), Cell.is_active == True)
        )
        all_cells = result.scalars().all()
        cell_ids = [c.id for c in all_cells]
 
        # Get reports
        result = await session.execute(
            select(CellReport).where(
                CellReport.cell_id.in_(cell_ids),
                CellReport.week_start_date == week_start
            )
        )
        reports = result.scalars().all()
 
        # Calculate aggregates
        total_attendance = sum(r.total_attendance or 0 for r in reports)
        total_souls_won = sum(r.souls_won or 0 for r in reports)
        total_finances = sum(float(r.finance_total or 0) for r in reports)
 
        submission_rate = (len(reports) / len(all_cells) * 100) if all_cells else 0
 
        return {
            "dashboard_type": "fellowship_pastor",
            "fellowship_id": str(fellowship.id),
            "fellowship_name": fellowship.name,
            "location": fellowship.location,
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "total_cells": len(all_cells),
            "cells_reported": len(reports),
            "submission_rate_percent": round(submission_rate, 1),
            "total_attendance": total_attendance,
            "total_souls_won": total_souls_won,
            "total_finances": round(total_finances, 2),
        }
 
    @staticmethod
    async def build_zone_dashboard(
        session: AsyncSession,
        zone_id: UUID
    ) -> dict:
        """Build Zonal Admin dashboard"""
 
        result = await session.execute(
            select(Zone).where(Zone.id == zone_id)
        )
        zone = result.scalar_one_or_none()
 
        week_start, week_end = get_current_week()
 
        # Get all fellowships
        result = await session.execute(
            select(Fellowship).where(Fellowship.zone_id == zone_id)
        )
        fellowships = result.scalars().all()
        f_ids = [f.id for f in fellowships]
 
        # Get all senior cells
        result = await session.execute(
            select(SeniorCell).where(SeniorCell.fellowship_id.in_(f_ids))
        )
        senior_cells = result.scalars().all()
        sc_ids = [sc.id for sc in senior_cells]
 
        # Get all cells
        result = await session.execute(
            select(Cell).where(Cell.senior_cell_id.in_(sc_ids), Cell.is_active == True)
        )
        all_cells = result.scalars().all()
        cell_ids = [c.id for c in all_cells]
 
        # Get reports
        result = await session.execute(
            select(CellReport).where(
                CellReport.cell_id.in_(cell_ids),
                CellReport.week_start_date == week_start
            )
        )
        reports = result.scalars().all()
 
        # Calculate aggregates
        total_attendance = sum(r.total_attendance or 0 for r in reports)
        total_souls_won = sum(r.souls_won or 0 for r in reports)
        total_finances = sum(float(r.finance_total or 0) for r in reports)
 
        submission_rate = (len(reports) / len(all_cells) * 100) if all_cells else 0
 
        return {
            "dashboard_type": "zonal_admin",
            "zone_id": str(zone.id),
            "zone_name": zone.name,
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "total_cells": len(all_cells),
            "cells_reported": len(reports),
            "submission_rate_percent": round(submission_rate, 1),
            "total_attendance": total_attendance,
            "total_souls_won": total_souls_won,
            "total_finances": round(total_finances, 2),
        }