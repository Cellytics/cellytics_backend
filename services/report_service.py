from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date, timedelta
from uuid import UUID
 
from models import CellReport
from schemas import CellReportSubmit
from utils.helpers import calculate_week_boundaries
 
 
class ReportService:
    """Business logic for cell reports"""
 
    @staticmethod
    async def create_report(
        session: AsyncSession,
        request: CellReportSubmit,
        user_id: UUID
    ) -> CellReport:
        """Create and save cell report"""
 
        # Calculate deadline
        week_start, week_end, deadline = calculate_week_boundaries(request.meeting_date)
        now = datetime.utcnow()
        status = "submitted" if now <= deadline else "late"
 
        # Calculate finance total
        finance_total = (
            request.finance_oblation +
            request.finance_offerings +
            request.finance_tithes +
            request.finance_thanksgiving +
            request.finance_seed +
            request.finance_partnership +
            request.finance_first_fruits
        )
 
        # Create report
        cell_report = CellReport(
            cell_id=request.cell_id,
            submitted_by_id=user_id,
            meeting_date=request.meeting_date,
            week_start_date=request.week_start_date,
            week_end_date=request.week_end_date,
            actual_meeting_day=request.actual_meeting_day,
            submission_deadline=deadline,
            status=status,
            submitted_at=now,
            synced_from_offline=False,
            meeting_week=request.meeting_week,
            meeting_type=request.meeting_type,
            meeting_duration=request.meeting_duration,
            bible_class_teachers=[t for t in request.bible_class_teachers if t],
            activities=[a.dict() for a in request.activities],
            first_timers=request.first_timers,
            number_saved=request.number_saved,
            filled_holy_ghost=request.filled_holy_ghost,
            total_attendance=request.total_attendance,
            new_members=request.new_members,
            souls_retained=request.souls_retained,
            souls_won=request.souls_won,
            souls_on_tracker=request.souls_on_tracker,
            finance_oblation=request.finance_oblation,
            finance_offerings=request.finance_offerings,
            finance_tithes=request.finance_tithes,
            finance_thanksgiving=request.finance_thanksgiving,
            finance_seed=request.finance_seed,
            finance_partnership=request.finance_partnership,
            finance_first_fruits=request.finance_first_fruits,
            finance_total=finance_total,
            finance_collected_by=request.finance_collected_by,
            testimonies=request.testimonies,
            monthly_plans=request.monthly_plans,
            challenges=request.challenges,
            soul_winning_records=[r.dict() for r in request.soul_winning_records],
            pastors_remarks=request.pastors_remarks,
            other_info=request.other_info,
            photo_urls=request.photo_urls,
        )
 
        session.add(cell_report)
        await session.commit()
        await session.refresh(cell_report)
 
        return cell_report
 