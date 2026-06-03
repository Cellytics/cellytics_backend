from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from datetime import datetime, date, timedelta
from uuid import UUID
from collections import defaultdict
 
from models import Cell, CellReport, SeniorCell, Fellowship, Zone, User
from utils.helpers import get_current_week
 
 
class DashboardService:
    """Business logic for dashboards"""

    @staticmethod
    async def build_cell_dashboard(
        session: AsyncSession,
        cell_id: UUID
    ) -> dict:
        """Build dashboard for a single cell leader."""

        result = await session.execute(
            select(Cell).where(Cell.id == cell_id, Cell.is_active == True)
        )
        cell = result.scalar_one_or_none()
        if not cell:
            return {}

        week_start, week_end = get_current_week()

        result = await session.execute(
            select(CellReport).where(
                CellReport.cell_id == cell_id,
                CellReport.week_start_date == week_start
            )
        )
        current_report = result.scalar_one_or_none()

        result = await session.execute(
            select(CellReport)
            .where(CellReport.cell_id == cell_id)
            .order_by(desc(CellReport.week_start_date))
            .limit(7)
        )
        recent_reports = result.scalars().all()

        streak = 0
        expected_week = week_start
        reported_weeks = {r.week_start_date for r in recent_reports}
        while expected_week in reported_weeks:
            streak += 1
            expected_week = expected_week - timedelta(days=7)

        attendance = current_report.total_attendance if current_report else 0
        souls_won = current_report.souls_won if current_report else 0
        new_members = current_report.new_members if current_report else 0
        finances = float(current_report.finance_total or 0) if current_report else 0.0

        return {
            "dashboard_type": "cell_leader",
            "cell_id": str(cell.id),
            "cell_name": cell.name,
            "senior_cell_id": str(cell.senior_cell_id),
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "has_submitted_this_week": current_report is not None,
            "status": current_report.status if current_report else "NO_REPORT",
            "total_attendance": attendance or 0,
            "total_souls_won": souls_won or 0,
            "new_members": new_members or 0,
            "total_finances": round(finances, 2),
            "submission_rate_percent": 100.0 if current_report else 0.0,
            "cells_reported": 1 if current_report else 0,
            "total_cells": 1,
            "submission_streak": streak,
            "default_meeting_day": cell.default_meeting_day,
            "meeting_time": cell.meeting_time.isoformat() if cell.meeting_time else None,
            "next_meeting": f"{cell.default_meeting_day.title()}"
                + (f", {cell.meeting_time.strftime('%I:%M %p')}" if cell.meeting_time else ""),
        }
 
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
        fellowship_id: UUID,
        period: str = "week"
    ) -> dict:
        """Build comprehensive Fellowship Pastor dashboard"""
 
        result = await session.execute(
            select(Fellowship).where(Fellowship.id == fellowship_id)
        )
        fellowship = result.scalar_one_or_none()
        if not fellowship:
            return {}
 
        # Calculate date range based on period
        today = date.today()
        if period == "week":
            week_start, week_end = get_current_week()
            period_start = week_start
            period_end = week_end
        elif period == "month":
            period_start = today.replace(day=1)
            # Get first day of next month, then go back one day
            if today.month == 12:
                period_end = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                period_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
        elif period == "year":
            period_start = date(today.year, 1, 1)
            period_end = date(today.year, 12, 31)
        else:  # all
            period_start = date(1900, 1, 1)
            period_end = today
 
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
 
        # Get reports in period
        result = await session.execute(
            select(CellReport).where(
                CellReport.cell_id.in_(cell_ids),
                CellReport.week_start_date >= period_start,
                CellReport.week_start_date <= period_end
            )
        )
        reports = result.scalars().all()
 
        # Calculate aggregates
        total_attendance = sum(r.total_attendance or 0 for r in reports)
        total_souls_won = sum(r.souls_won or 0 for r in reports)
        total_first_timers = sum(r.first_timers or 0 for r in reports)
        total_finances = sum(float(r.finance_total or 0) for r in reports)
        total_new_members = sum(r.new_members or 0 for r in reports)
 
        submission_rate = (len(reports) / len(all_cells) * 100) if all_cells else 0
 
        # Calculate growth rate (compare with previous period)
        if period == "week":
            prev_week_start = period_start - timedelta(days=7)
            prev_week_end = period_start - timedelta(days=1)
        elif period == "month":
            if today.month == 1:
                prev_month_end = date(today.year - 1, 12, 31)
                prev_month_start = date(today.year - 1, 12, 1)
            else:
                prev_month_end = period_start - timedelta(days=1)
                prev_month_start = date(today.year if today.month > 1 else today.year - 1,
                                        today.month - 1 if today.month > 1 else 12, 1)
            prev_week_start = prev_month_start
            prev_week_end = prev_month_end
        else:
            prev_week_start = period_start - timedelta(days=365)
            prev_week_end = period_start - timedelta(days=1)
 
        result = await session.execute(
            select(CellReport).where(
                CellReport.cell_id.in_(cell_ids),
                CellReport.week_start_date >= prev_week_start,
                CellReport.week_start_date <= prev_week_end
            )
        )
        prev_reports = result.scalars().all()
        prev_attendance = sum(r.total_attendance or 0 for r in prev_reports)
 
        growth_rate = 0
        if prev_attendance > 0:
            growth_rate = round(((total_attendance - prev_attendance) / prev_attendance) * 100, 1)
 
        # Get cells needing attention
        cells_needing_attention = await DashboardService._get_cells_needing_attention(
            session, cell_ids, all_cells
        )
 
        # Get top performers
        top_performers = await DashboardService._get_top_performers(
            session, senior_cells, cell_ids, reports
        )
 
        # Get trends
        trends = await DashboardService._get_fellowship_trends(
            session, cell_ids, period_start, period_end, period
        )
 
        # Get conversion sources
        conversion_sources = await DashboardService._get_conversion_sources(reports)
 
        # Get pastor name if pastor is assigned
        pastor_name = "Fellowship Pastor"
        if fellowship.pastor_id:
            result = await session.execute(
                select(User).where(User.id == fellowship.pastor_id)
            )
            pastor = result.scalar_one_or_none()
            if pastor:
                pastor_name = pastor.name
 
        return {
            "dashboard_type": "fellowship_pastor",
            "fellowship_id": str(fellowship.id),
            "fellowship_name": fellowship.name,
            "pastor_name": pastor_name,
            "location": fellowship.location,
            "period": period,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "stats": {
                "total_senior_cells": len(senior_cells),
                "total_cells": len(all_cells),
                "cells_reported": len(reports),
                "submission_rate_percent": round(submission_rate, 1),
                "total_attendance": total_attendance,
                "total_first_timers": total_first_timers,
                "total_souls_won": total_souls_won,
                "total_new_members": total_new_members,
                "total_finances": round(total_finances, 2),
                "growth_rate_percent": growth_rate,
            },
            "cells_needing_attention": cells_needing_attention,
            "top_performers": top_performers,
            "trends": trends,
            "conversion_sources": conversion_sources,
        }
 
    @staticmethod
    async def _get_cells_needing_attention(
        session: AsyncSession,
        cell_ids: list,
        all_cells: list
    ) -> list:
        """Get cells that need attention (no report >7 days or declining attendance)"""
        
        if not cell_ids:
            return []
 
        # Get recent reports (last 2 weeks)
        two_weeks_ago = date.today() - timedelta(days=14)
        result = await session.execute(
            select(CellReport).where(
                CellReport.cell_id.in_(cell_ids),
                CellReport.week_start_date >= two_weeks_ago
            ).order_by(desc(CellReport.week_start_date))
        )
        recent_reports = result.scalars().all()
        latest_reports = {}
        for report in recent_reports:
            if report.cell_id not in latest_reports:
                latest_reports[report.cell_id] = report
 
        # Get previous period reports
        four_weeks_ago = date.today() - timedelta(days=28)
        result = await session.execute(
            select(CellReport).where(
                CellReport.cell_id.in_(cell_ids),
                CellReport.week_start_date >= four_weeks_ago,
                CellReport.week_start_date < two_weeks_ago
            ).order_by(desc(CellReport.week_start_date))
        )
        prev_reports = result.scalars().all()
        previous_reports = {}
        for report in prev_reports:
            if report.cell_id not in previous_reports:
                previous_reports[report.cell_id] = report
 
        attention_cells = []
 
        # Check each cell
        for cell in all_cells:
            latest = latest_reports.get(cell.id)
            previous = previous_reports.get(cell.id)
 
            reason = None
            status = "ok"
 
            # Check if no report in last 7 days
            if not latest:
                reason = "No report in 7 days"
                status = "critical"
            # Check for declining attendance
            elif previous and latest.total_attendance and previous.total_attendance:
                decline_percent = ((previous.total_attendance - latest.total_attendance) / 
                                 previous.total_attendance) * 100
                if decline_percent >= 20:
                    reason = f"Attendance declined {decline_percent:.0f}%"
                    status = "warning"
 
            if reason:
                attention_cells.append({
                    "cell_id": str(cell.id),
                    "cell_name": cell.name,
                    "leader_name": cell.leader_name or "Unassigned",
                    "reason": reason,
                    "status": status,
                    "last_report_date": latest.meeting_date.isoformat() if latest else None,
                    "last_attendance": latest.total_attendance if latest else None,
                    "previous_attendance": previous.total_attendance if previous else None,
                })
 
        return sorted(attention_cells, key=lambda x: (x["status"] == "ok", x["cell_name"]))
 
    @staticmethod
    async def _get_top_performers(
        session: AsyncSession,
        senior_cells: list,
        cell_ids: list,
        reports: list
    ) -> dict:
        """Get top senior cells and cells of the week"""
 
        # Calculate senior cell stats
        sc_stats = {}
        for sc in senior_cells:
            sc_stats[sc.id] = {
                "id": str(sc.id),
                "name": sc.name,
                "leader_name": sc.leader_name or "Unassigned",
                "total_attendance": 0,
                "cells_reported": 0,
                "total_souls_won": 0,
                "total_finances": 0,
            }
 
        for report in reports:
            result = await session.execute(
                select(Cell).where(Cell.id == report.cell_id)
            )
            cell = result.scalar_one_or_none()
            if cell and cell.senior_cell_id in sc_stats:
                sc_stats[cell.senior_cell_id]["total_attendance"] += report.total_attendance or 0
                sc_stats[cell.senior_cell_id]["total_souls_won"] += report.souls_won or 0
                sc_stats[cell.senior_cell_id]["total_finances"] += float(report.finance_total or 0)
                sc_stats[cell.senior_cell_id]["cells_reported"] += 1
 
        top_senior_cells = sorted(
            sc_stats.values(),
            key=lambda x: x["total_attendance"],
            reverse=True
        )[:3]
 
        # Calculate cell stats
        cell_stats = {}
        cells_by_id = {}
        if cell_ids:
            result = await session.execute(
                select(Cell).where(Cell.id.in_(cell_ids))
            )
            cells = result.scalars().all()
            cells_by_id = {c.id: c for c in cells}
 
        for report in reports:
            if report.cell_id not in cell_stats:
                cell = cells_by_id.get(report.cell_id)
                cell_stats[report.cell_id] = {
                    "id": str(report.cell_id),
                    "name": cell.name if cell else "Unknown",
                    "leader_name": cell.leader_name if cell else "Unassigned",
                    "total_attendance": 0,
                    "total_souls_won": 0,
                    "total_finances": 0,
                }
            cell_stats[report.cell_id]["total_attendance"] += report.total_attendance or 0
            cell_stats[report.cell_id]["total_souls_won"] += report.souls_won or 0
            cell_stats[report.cell_id]["total_finances"] += float(report.finance_total or 0)
 
        top_cells = sorted(
            cell_stats.values(),
            key=lambda x: x["total_attendance"],
            reverse=True
        )[:3]
 
        return {
            "top_senior_cells": top_senior_cells,
            "top_cells": top_cells,
        }
 
    @staticmethod
    async def _get_fellowship_trends(
        session: AsyncSession,
        cell_ids: list,
        period_start: date,
        period_end: date,
        period: str
    ) -> list:
        """Get attendance trends over the period"""
 
        if not cell_ids:
            return []
 
        result = await session.execute(
            select(CellReport).where(
                CellReport.cell_id.in_(cell_ids),
                CellReport.week_start_date >= period_start,
                CellReport.week_start_date <= period_end
            ).order_by(CellReport.week_start_date)
        )
        reports = result.scalars().all()
 
        # Group by week
        weeks_data = defaultdict(lambda: {
            "attendance": 0,
            "first_timers": 0,
            "souls_won": 0,
            "count": 0
        })
 
        for report in reports:
            week_key = report.week_start_date.isoformat()
            weeks_data[week_key]["attendance"] += report.total_attendance or 0
            weeks_data[week_key]["first_timers"] += report.first_timers or 0
            weeks_data[week_key]["souls_won"] += report.souls_won or 0
            weeks_data[week_key]["count"] += 1
 
        trends = []
        for week_key in sorted(weeks_data.keys()):
            data = weeks_data[week_key]
            trends.append({
                "week": week_key,
                "attendance": data["attendance"],
                "first_timers": data["first_timers"],
                "souls_won": data["souls_won"],
                "reports_count": data["count"],
            })
 
        return trends
 
    @staticmethod
    async def _get_conversion_sources(reports: list) -> list:
        """Get breakdown of conversion sources (first timers, souls won, etc.)"""
 
        total_first_timers = sum(r.first_timers or 0 for r in reports)
        total_souls_won = sum(r.souls_won or 0 for r in reports)
        total_new_members = sum(r.new_members or 0 for r in reports)
        total_souls_retained = sum(r.souls_retained or 0 for r in reports)
 
        total_conversions = total_first_timers + total_souls_won
 
        return [
            {
                "source": "First Timers",
                "count": total_first_timers,
                "percentage": round((total_first_timers / total_conversions * 100), 1) if total_conversions > 0 else 0,
            },
            {
                "source": "Souls Won",
                "count": total_souls_won,
                "percentage": round((total_souls_won / total_conversions * 100), 1) if total_conversions > 0 else 0,
            },
            {
                "source": "New Members",
                "count": total_new_members,
                "percentage": 0,
            },
            {
                "source": "Souls Retained",
                "count": total_souls_retained,
                "percentage": 0,
            },
        ]
 
    @staticmethod
    async def get_fellowship_senior_cells(
        session: AsyncSession,
        fellowship_id: UUID
    ) -> list:
        """Get all senior cells for a fellowship with their stats"""
 
        result = await session.execute(
            select(SeniorCell).where(SeniorCell.fellowship_id == fellowship_id)
        )
        senior_cells = result.scalars().all()
 
        week_start, week_end = get_current_week()
 
        senior_cells_data = []
        for sc in senior_cells:
            # Get cells in this senior cell
            result = await session.execute(
                select(Cell).where(Cell.senior_cell_id == sc.id, Cell.is_active == True)
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
 
            total_attendance = sum(r.total_attendance or 0 for r in reports)
            total_souls_won = sum(r.souls_won or 0 for r in reports)
            total_finances = sum(float(r.finance_total or 0) for r in reports)
            submission_rate = (len(reports) / len(cells) * 100) if cells else 0
 
            senior_cells_data.append({
                "id": str(sc.id),
                "name": sc.name,
                "leader_name": sc.leader_name or "Unassigned",
                "total_cells": len(cells),
                "cells_reported": len(reports),
                "submission_rate": round(submission_rate, 1),
                "total_attendance": total_attendance,
                "total_souls_won": total_souls_won,
                "total_finances": round(total_finances, 2),
            })
 
        return senior_cells_data
 
    @staticmethod
    async def get_senior_cell_details(
        session: AsyncSession,
        senior_cell_id: UUID,
        period: str = "week"
    ) -> dict:
        """Get detailed view of a senior cell"""
 
        result = await session.execute(
            select(SeniorCell).where(SeniorCell.id == senior_cell_id)
        )
        senior_cell = result.scalar_one_or_none()
        if not senior_cell:
            return {}
 
        # Get date range
        today = date.today()
        if period == "week":
            week_start, week_end = get_current_week()
            period_start = week_start
            period_end = week_end
        elif period == "month":
            period_start = today.replace(day=1)
            if today.month == 12:
                period_end = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                period_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
        else:
            period_start = date(today.year, 1, 1)
            period_end = date(today.year, 12, 31)
 
        # Get all cells
        result = await session.execute(
            select(Cell).where(Cell.senior_cell_id == senior_cell_id, Cell.is_active == True)
        )
        cells = result.scalars().all()
        cell_ids = [c.id for c in cells]
 
        # Get reports in period
        result = await session.execute(
            select(CellReport).where(
                CellReport.cell_id.in_(cell_ids),
                CellReport.week_start_date >= period_start,
                CellReport.week_start_date <= period_end
            )
        )
        reports = result.scalars().all()
 
        # Build cell list with reports
        cells_data = []
        for cell in cells:
            cell_reports = [r for r in reports if r.cell_id == cell.id]
            total_attendance = sum(r.total_attendance or 0 for r in cell_reports)
            total_souls_won = sum(r.souls_won or 0 for r in cell_reports)
            total_finances = sum(float(r.finance_total or 0) for r in cell_reports)
 
            cells_data.append({
                "id": str(cell.id),
                "name": cell.name,
                "leader_name": cell.leader_name or "Unassigned",
                "reports_count": len(cell_reports),
                "total_attendance": total_attendance,
                "total_souls_won": total_souls_won,
                "total_finances": round(total_finances, 2),
            })
 
        return {
            "senior_cell_id": str(senior_cell.id),
            "senior_cell_name": senior_cell.name,
            "leader_name": senior_cell.leader_name or "Unassigned",
            "period": period,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "total_cells": len(cells),
            "cells": cells_data,
            "stats": {
                "total_attendance": sum(c["total_attendance"] for c in cells_data),
                "total_souls_won": sum(c["total_souls_won"] for c in cells_data),
                "total_finances": sum(c["total_finances"] for c in cells_data),
            }
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
