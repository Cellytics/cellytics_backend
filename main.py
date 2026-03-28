# main.py - FastAPI Application (COMPLETE)
# Supports full organizational hierarchy: Zone -> Fellowship -> Senior Cell -> Cell -> Reports

from fastapi import FastAPI, Depends, HTTPException, status, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from datetime import datetime, date, timedelta
from uuid import UUID
from typing import Optional, List
import logging

from database import get_session, close_db
from models import User, Cell, CellReport, Zone, Fellowship, SeniorCell, Region
from schemas import (
    LoginRequest, LoginResponse, UserCreate, UserCreateResponse,
    CellReportSubmit, CellReportResponse, ErrorResponse
)
from auth import verify_pin, create_access_token, decode_token, hash_default_pin

# ═══════════════════════════════════════════════════════════════════════════════
# SETUP
# ═══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="BLW Cell Reporting System",
    description="API for cell report submission and dashboards across Regions -> Zones -> Fellowships -> Senior Cells -> Cells",
    version="1.0.0",
    swagger_ui_parameters={"persistAuthorization": True},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# SWAGGER BEARER AUTH
# ═══════════════════════════════════════════════════════════════════════════════

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return app.openapi_schema

app.openapi = custom_openapi


# ═══════════════════════════════════════════════════════════════════════════════
# STARTUP / SHUTDOWN
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup():
    logger.info("🚀 FastAPI starting up...")


@app.on_event("shutdown")
async def shutdown():
    logger.info("🛑 FastAPI shutting down...")
    await close_db()


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def get_current_user(
    authorization: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_session)
) -> User:
    """Get current authenticated user from Bearer token"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authorization header",
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid scheme")
    except (ValueError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use: Bearer <token>",
        )

    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    result = await session.execute(
        select(User).where(User.id == UUID(user_id), User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


def calculate_week_boundaries(meeting_date: date) -> tuple:
    """Calculate week start (Monday), end (Sunday), and deadline (Sunday 9am)"""
    day_of_week = meeting_date.weekday()
    week_start = meeting_date - timedelta(days=day_of_week)
    week_end = week_start + timedelta(days=6)
    deadline = datetime.combine(week_end, datetime.min.time()).replace(hour=9, minute=0, second=0)
    return week_start, week_end, deadline


def get_current_week():
    """Get current week's Monday and Sunday"""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTES: ROOT & HEALTH
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "BLW Cell Reporting API",
        "version": "1.0.0",
        "hierarchy": "Region -> Zone -> Fellowship -> Senior Cell -> Cell -> Reports",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "message": "BLW Cell Reporting API is running",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTES: AUTHENTICATION
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/auth/login", response_model=LoginResponse, tags=["Auth"])
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

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid phone or PIN",
            )

        if not verify_pin(request.pin, user.pin_hash):
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
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTES: ADMIN - USER MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/admin/users", response_model=UserCreateResponse, tags=["Admin"])
async def create_user(
    request: UserCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Create new user. 
    
    Permissions:
    - System Admin: Can create any role
    - Zonal Admin: Can create Fellowship Pastors, Senior Cell Leaders, Cell Leaders under their zone
    - Fellowship Pastor: Can create Senior Cell Leaders, Cell Leaders under their fellowship
    - Senior Cell Leader: Cannot create users
    - Cell Leader: Cannot create users
    """
    try:
        # Check permissions
        if current_user.role == "system_admin":
            # System admin can create anyone
            pass
        elif current_user.role == "zonal_admin":
            # Zonal admin can only create users in their zone
            if request.zone_id != current_user.zone_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only create users in your zone",
                )
        elif current_user.role == "fellowship_pastor":
            # Fellowship pastor can only create users in their fellowship
            if request.fellowship_id != current_user.fellowship_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only create users in your fellowship",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to create users",
            )

        # Check phone uniqueness
        result = await session.execute(
            select(User).where(User.phone == request.phone)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already exists",
            )

        # Validate cell_id if provided (must exist)
        if request.cell_id:
            result = await session.execute(
                select(Cell).where(Cell.id == request.cell_id)
            )
            if not result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Cell {request.cell_id} not found",
                )

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
        logger.error(f"Create user error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User creation failed: {str(e)}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTES: ORGANIZATION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/admin/fellowships", tags=["Admin"])
async def create_fellowship(
    name: str,
    location: str,
    zone_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new fellowship. Zonal Admin only."""
    try:
        if current_user.role != "zonal_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only zonal admin can create fellowships",
            )

        # Verify zone exists
        result = await session.execute(
            select(Zone).where(Zone.id == zone_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Zone {zone_id} not found",
            )

        fellowship = Fellowship(
            name=name,
            location=location,
            zone_id=zone_id,
        )

        session.add(fellowship)
        await session.commit()
        await session.refresh(fellowship)

        return {
            "id": str(fellowship.id),
            "name": fellowship.name,
            "location": fellowship.location,
            "zone_id": str(fellowship.zone_id),
            "message": "Fellowship created successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create fellowship error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fellowship creation failed: {str(e)}"
        )


@app.post("/api/admin/senior-cells", tags=["Admin"])
async def create_senior_cell(
    name: str,
    fellowship_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new senior cell. Fellowship Pastor only."""
    try:
        if current_user.role != "fellowship_pastor":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only fellowship pastor can create senior cells",
            )

        # Verify fellowship exists and belongs to current user
        result = await session.execute(
            select(Fellowship).where(Fellowship.id == fellowship_id)
        )
        fellowship = result.scalar_one_or_none()
        if not fellowship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fellowship {fellowship_id} not found",
            )

        if fellowship.id != current_user.fellowship_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create senior cells in your fellowship",
            )

        senior_cell = SeniorCell(
            name=name,
            fellowship_id=fellowship_id,
        )

        session.add(senior_cell)
        await session.commit()
        await session.refresh(senior_cell)

        return {
            "id": str(senior_cell.id),
            "name": senior_cell.name,
            "fellowship_id": str(senior_cell.fellowship_id),
            "message": "Senior cell created successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create senior cell error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Senior cell creation failed: {str(e)}"
        )


@app.post("/api/admin/cells", tags=["Admin"])
async def create_cell(
    name: str,
    senior_cell_id: UUID,
    default_meeting_day: str = "monday",
    meeting_time: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new cell. Fellowship Pastor or Senior Cell Leader."""
    try:
        # Verify senior cell exists
        result = await session.execute(
            select(SeniorCell).where(SeniorCell.id == senior_cell_id)
        )
        senior_cell = result.scalar_one_or_none()
        if not senior_cell:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Senior cell {senior_cell_id} not found",
            )

        # Check permissions
        if current_user.role == "fellowship_pastor":
            if senior_cell.fellowship_id != current_user.fellowship_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only create cells in your fellowship",
                )
        elif current_user.role == "senior_cell_leader":
            if senior_cell.id != current_user.senior_cell_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only create cells under your senior cell",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only fellowship pastor or senior cell leader can create cells",
            )

        # Parse meeting time if provided
        from datetime import time as time_type
        meeting_time_obj = None
        if meeting_time:
            try:
                h, m = map(int, meeting_time.split(":"))
                meeting_time_obj = time_type(h, m)
            except:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Meeting time must be in HH:MM format",
                )

        cell = Cell(
            name=name,
            senior_cell_id=senior_cell_id,
            default_meeting_day=default_meeting_day,
            meeting_time=meeting_time_obj,
        )

        session.add(cell)
        await session.commit()
        await session.refresh(cell)

        return {
            "id": str(cell.id),
            "name": cell.name,
            "senior_cell_id": str(cell.senior_cell_id),
            "default_meeting_day": cell.default_meeting_day,
            "meeting_time": str(cell.meeting_time) if cell.meeting_time else None,
            "message": "Cell created successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create cell error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cell creation failed: {str(e)}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTES: CELL REPORTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/reports/submit", response_model=CellReportResponse, tags=["Reports"])
async def submit_report(
    request: CellReportSubmit,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Submit a cell report. Cell Leaders only."""
    try:
        # Only cell leaders can submit (or higher roles for testing)
        if current_user.role == "cell_leader":
            if current_user.cell_id != request.cell_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only submit reports for your own cell",
                )
        elif current_user.role not in ["senior_cell_leader", "fellowship_pastor", "zonal_admin", "system_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only cell leaders can submit reports",
            )

        # Verify cell exists
        result = await session.execute(
            select(Cell).where(Cell.id == request.cell_id)
        )
        cell = result.scalar_one_or_none()
        if not cell:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cell {request.cell_id} not found",
            )

        # Check for duplicate
        result = await session.execute(
            select(CellReport).where(
                CellReport.cell_id == request.cell_id,
                CellReport.week_start_date == request.week_start_date
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Report already exists for week of {request.week_start_date}",
            )

        # Calculate deadline
        week_start, week_end, deadline = calculate_week_boundaries(request.meeting_date)
        now = datetime.utcnow()
        status_value = "submitted" if now <= deadline else "late"

        # status_value = "SUBMITTED" if now <= deadline else "LATE"

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
            submitted_by_id=current_user.id,
            meeting_date=request.meeting_date,
            week_start_date=request.week_start_date,
            week_end_date=request.week_end_date,
            actual_meeting_day=request.actual_meeting_day,
            submission_deadline=deadline,
            status=status_value,
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

        return CellReportResponse(
            id=cell_report.id,
            cell_id=cell_report.cell_id,
            status=cell_report.status,
            submitted_at=cell_report.submitted_at,
            submission_deadline=cell_report.submission_deadline,
            message=f"Report submitted {'on time' if status_value == 'SUBMITTED' else 'late'}!",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Submit report error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report submission failed: {str(e)}"
        )


@app.get("/api/reports/{report_id}", tags=["Reports"])
async def get_report(
    report_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a single report by ID."""
    try:
        result = await session.execute(
            select(CellReport).where(CellReport.id == report_id)
        )
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found",
            )

        # Check access
        if (
            report.submitted_by_id != current_user.id and
            current_user.cell_id != report.cell_id and
            current_user.role not in ["senior_cell_leader", "fellowship_pastor", "zonal_pastor", "zonal_admin", "system_admin"]
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this report",
            )

        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get report error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch report: {str(e)}"
        )


@app.get("/api/reports", tags=["Reports"])
async def list_reports(
    cell_id: Optional[UUID] = None,
    status: Optional[str] = Query(None, regex="^(draft|SUBMITTED|LATE|OVERDUE)$"),
    week_start: Optional[date] = None,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List reports with optional filtering."""
    try:
        query = select(CellReport)

        if cell_id:
            query = query.where(CellReport.cell_id == cell_id)
        if status:
            query = query.where(CellReport.status == status)
        if week_start:
            query = query.where(CellReport.week_start_date == week_start)

        query = query.order_by(desc(CellReport.submitted_at)).offset(offset).limit(limit)

        result = await session.execute(query)
        reports = result.scalars().all()

        return {
            "count": len(reports),
            "offset": offset,
            "limit": limit,
            "reports": [
                {
                    "id": str(r.id),
                    "cell_id": str(r.cell_id),
                    "status": r.status,
                    "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
                    "week_start_date": r.week_start_date.isoformat(),
                    "total_attendance": r.total_attendance,
                    "souls_won": r.souls_won,
                    "finance_total": float(r.finance_total or 0),
                }
                for r in reports
            ]
        }

    except Exception as e:
        logger.error(f"List reports error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list reports: {str(e)}"
        )




























# # main.py - FastAPI Application

# from fastapi import FastAPI, Depends, HTTPException, status, Header
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.openapi.utils import get_openapi
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select
# from datetime import datetime, date, timedelta
# from uuid import UUID
# from typing import Optional
# import logging

# from database import get_session, close_db
# from models import User, Cell, CellReport, Zone, Fellowship
# from schemas import (
#     LoginRequest, LoginResponse, UserCreate, UserCreateResponse,
#     CellReportSubmit, CellReportResponse, ErrorResponse
# )
# from auth import verify_pin, create_access_token, decode_token, hash_default_pin

# # ═══════════════════════════════════════════════════════════════════════════════
# # SETUP
# # ═══════════════════════════════════════════════════════════════════════════════

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = FastAPI(
#     title="BLW Cell Reporting System",
#     description="API for cell report submission and dashboards",
#     version="1.0.0",
#     swagger_ui_parameters={"persistAuthorization": True},
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # ═══════════════════════════════════════════════════════════════════════════════
# # SWAGGER BEARER AUTH
# # ═══════════════════════════════════════════════════════════════════════════════

# def custom_openapi():
#     if app.openapi_schema:
#         return app.openapi_schema
#     schema = get_openapi(
#         title=app.title,
#         version=app.version,
#         description=app.description,
#         routes=app.routes,
#     )
#     schema["components"]["securitySchemes"] = {
#         "BearerAuth": {
#             "type": "http",
#             "scheme": "bearer",
#             "bearerFormat": "JWT",
#         }
#     }
#     schema["security"] = [{"BearerAuth": []}]
#     app.openapi_schema = schema
#     return app.openapi_schema

# app.openapi = custom_openapi


# # ═══════════════════════════════════════════════════════════════════════════════
# # STARTUP / SHUTDOWN
# # ═══════════════════════════════════════════════════════════════════════════════

# @app.on_event("startup")
# async def startup():
#     logger.info("🚀 FastAPI starting up...")


# @app.on_event("shutdown")
# async def shutdown():
#     logger.info("🛑 FastAPI shutting down...")
#     await close_db()


# # ═══════════════════════════════════════════════════════════════════════════════
# # HELPER FUNCTIONS
# # ═══════════════════════════════════════════════════════════════════════════════

# async def get_current_user(
#     authorization: Optional[str] = Header(None),
#     session: AsyncSession = Depends(get_session)
# ) -> User:
#     """Get current authenticated user from Bearer token"""
#     if not authorization:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="No authorization header",
#         )

#     try:
#         scheme, token = authorization.split()
#         if scheme.lower() != "bearer":
#             raise ValueError("Invalid scheme")
#     except (ValueError, IndexError):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid authorization header format. Use: Bearer <token>",
#         )

#     user_id = decode_token(token)
#     if not user_id:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid or expired token",
#         )

#     result = await session.execute(
#         select(User).where(User.id == UUID(user_id), User.is_active == True)
#     )
#     user = result.scalar_one_or_none()

#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="User not found or inactive",
#         )

#     return user


# def calculate_week_boundaries(meeting_date: date) -> tuple:
#     """Calculate week start (Monday), end (Sunday), and deadline (Sunday 9am)"""
#     day_of_week = meeting_date.weekday()
#     week_start = meeting_date - timedelta(days=day_of_week)
#     week_end = week_start + timedelta(days=6)
#     deadline = datetime.combine(week_end, datetime.min.time()).replace(hour=9, minute=0, second=0)
#     return week_start, week_end, deadline


# # ═══════════════════════════════════════════════════════════════════════════════
# # ROUTES: ROOT & HEALTH
# # ═══════════════════════════════════════════════════════════════════════════════

# @app.get("/", tags=["Health"])
# async def root():
#     return {
#         "message": "BLW Cell Reporting API",
#         "version": "1.0.0",
#         "docs": "/docs",
#     }


# @app.get("/health", tags=["Health"])
# async def health_check():
#     return {
#         "status": "ok",
#         "message": "BLW Cell Reporting API is running",
#         "timestamp": datetime.utcnow().isoformat(),
#     }


# # ═══════════════════════════════════════════════════════════════════════════════
# # ROUTES: AUTHENTICATION
# # ═══════════════════════════════════════════════════════════════════════════════

# @app.post("/api/auth/login", response_model=LoginResponse, tags=["Auth"])
# async def login(
#     request: LoginRequest,
#     session: AsyncSession = Depends(get_session)
# ):
#     """
#     Login with phone and PIN.
#     Returns JWT token for subsequent requests.
#     """
#     try:
#         result = await session.execute(
#             select(User).where(User.phone == request.phone, User.is_active == True)
#         )
#         user = result.scalar_one_or_none()

#         if not user:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid phone or PIN",
#             )

#         if not verify_pin(request.pin, user.pin_hash):
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
#             }
#         )

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Login error: {e}", exc_info=True)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Login failed: {str(e)}"
#         )


# # ═══════════════════════════════════════════════════════════════════════════════
# # ROUTES: ADMIN
# # ═══════════════════════════════════════════════════════════════════════════════

# @app.post("/api/admin/users", response_model=UserCreateResponse, tags=["Admin"])
# async def create_user(
#     request: UserCreate,
#     session: AsyncSession = Depends(get_session),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Create new user. System Admin only.
#     """
#     try:
#         if current_user.role != "system_admin":
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Only system admin can create users",
#             )

#         result = await session.execute(
#             select(User).where(User.phone == request.phone)
#         )
#         if result.scalar_one_or_none():
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Phone number already exists",
#             )

#         new_user = User(
#             phone=request.phone,
#             name=request.name,
#             pin_hash=hash_default_pin(),
#             role=request.role,
#             cell_id=request.cell_id,
#             senior_cell_id=request.senior_cell_id,
#             fellowship_id=request.fellowship_id,
#             zone_id=request.zone_id,
#             is_active=True,
#         )

#         session.add(new_user)
#         await session.commit()
#         await session.refresh(new_user)

#         return UserCreateResponse(
#             user_id=new_user.id,
#             phone=new_user.phone,
#             name=new_user.name,
#             role=new_user.role,
#             initial_pin="123456",
#             message="User created. Share phone and PIN with leader.",
#         )

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Create user error: {e}", exc_info=True)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"User creation failed: {str(e)}"
#         )


# # ═══════════════════════════════════════════════════════════════════════════════
# # ROUTES: CELL REPORTS
# # ═══════════════════════════════════════════════════════════════════════════════

# @app.post("/api/reports/submit", response_model=CellReportResponse, tags=["Reports"])
# async def submit_report(
#     request: CellReportSubmit,
#     session: AsyncSession = Depends(get_session),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Submit a cell report.
#     """
#     try:
#         if current_user.cell_id != request.cell_id and current_user.role == "cell_leader":
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="You can only submit reports for your own cell",
#             )

#         result = await session.execute(
#             select(Cell).where(Cell.id == request.cell_id)
#         )
#         cell = result.scalar_one_or_none()
#         if not cell:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Cell not found",
#             )

#         result = await session.execute(
#             select(CellReport).where(
#                 CellReport.cell_id == request.cell_id,
#                 CellReport.week_start_date == request.week_start_date
#             )
#         )
#         if result.scalar_one_or_none():
#             raise HTTPException(
#                 status_code=status.HTTP_409_CONFLICT,
#                 detail=f"Report already exists for week of {request.week_start_date}",
#             )

#         week_start, week_end, deadline = calculate_week_boundaries(request.meeting_date)
#         now = datetime.utcnow()
#         status_value = "SUBMITTED" if now <= deadline else "LATE"

#         finance_total = (
#             request.finance_oblation +
#             request.finance_offerings +
#             request.finance_tithes +
#             request.finance_thanksgiving +
#             request.finance_seed +
#             request.finance_partnership +
#             request.finance_first_fruits
#         )

#         cell_report = CellReport(
#             cell_id=request.cell_id,
#             submitted_by_id=current_user.id,
#             meeting_date=request.meeting_date,
#             week_start_date=request.week_start_date,
#             week_end_date=request.week_end_date,
#             actual_meeting_day=request.actual_meeting_day,
#             submission_deadline=deadline,
#             status=status_value,
#             submitted_at=now,
#             synced_from_offline=False,
#             meeting_week=request.meeting_week,
#             meeting_type=request.meeting_type,
#             meeting_duration=request.meeting_duration,
#             bible_class_teachers=[t for t in request.bible_class_teachers if t],
#             activities=[a.dict() for a in request.activities],
#             first_timers=request.first_timers,
#             number_saved=request.number_saved,
#             filled_holy_ghost=request.filled_holy_ghost,
#             total_attendance=request.total_attendance,
#             new_members=request.new_members,
#             souls_retained=request.souls_retained,
#             souls_won=request.souls_won,
#             souls_on_tracker=request.souls_on_tracker,
#             finance_oblation=request.finance_oblation,
#             finance_offerings=request.finance_offerings,
#             finance_tithes=request.finance_tithes,
#             finance_thanksgiving=request.finance_thanksgiving,
#             finance_seed=request.finance_seed,
#             finance_partnership=request.finance_partnership,
#             finance_first_fruits=request.finance_first_fruits,
#             finance_total=finance_total,
#             finance_collected_by=request.finance_collected_by,
#             testimonies=request.testimonies,
#             monthly_plans=request.monthly_plans,
#             challenges=request.challenges,
#             soul_winning_records=[r.dict() for r in request.soul_winning_records],
#             pastors_remarks=request.pastors_remarks,
#             other_info=request.other_info,
#             photo_urls=request.photo_urls,
#         )

#         session.add(cell_report)
#         await session.commit()
#         await session.refresh(cell_report)

#         return CellReportResponse(
#             id=cell_report.id,
#             cell_id=cell_report.cell_id,
#             status=cell_report.status,
#             submitted_at=cell_report.submitted_at,
#             submission_deadline=cell_report.submission_deadline,
#             message=f"Report submitted {'on time' if status_value == 'SUBMITTED' else 'late'}!",
#         )

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Submit report error: {e}", exc_info=True)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Report submission failed: {str(e)}"
#         )


# @app.get("/api/reports/{report_id}", tags=["Reports"])
# async def get_report(
#     report_id: UUID,
#     session: AsyncSession = Depends(get_session),
#     current_user: User = Depends(get_current_user),
# ):
#     """Get a single report by ID."""
#     try:
#         result = await session.execute(
#             select(CellReport).where(CellReport.id == report_id)
#         )
#         report = result.scalar_one_or_none()

#         if not report:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Report not found",
#             )

#         if (
#             report.submitted_by_id != current_user.id and
#             current_user.cell_id != report.cell_id and
#             current_user.role not in ["senior_cell_leader", "fellowship_pastor", "zonal_pastor", "zonal_admin", "system_admin"]
#         ):
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="You don't have access to this report",
#             )

#         return report

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Get report error: {e}", exc_info=True)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to fetch report: {str(e)}"
#         )

































# # # main.py - FastAPI Application (FIXED)

# # from fastapi import FastAPI, Depends, HTTPException, status, Header
# # from fastapi.middleware.cors import CORSMiddleware
# # from sqlalchemy.ext.asyncio import AsyncSession
# # from sqlalchemy import select
# # from datetime import datetime, date, timedelta
# # from uuid import UUID
# # from typing import Optional
# # import logging

# # from database import get_session, init_db, close_db
# # from models import User, Cell, CellReport, Zone, Fellowship
# # from schemas import (
# #     LoginRequest, LoginResponse, UserCreate, UserCreateResponse,
# #     CellReportSubmit, CellReportResponse, ErrorResponse
# # )
# # from auth import hash_pin, verify_pin, create_access_token, decode_token, hash_default_pin

# # # ═══════════════════════════════════════════════════════════════════════════════
# # # SETUP
# # # ═══════════════════════════════════════════════════════════════════════════════

# # logging.basicConfig(level=logging.INFO)
# # logger = logging.getLogger(__name__)

# # app = FastAPI(
# #     title="BLW Cell Reporting System",
# #     description="API for cell report submission and dashboards",
# #     version="1.0.0",
# # )

# # app.add_middleware(
# #     CORSMiddleware,
# #     allow_origins=["*"],
# #     allow_credentials=True,
# #     allow_methods=["*"],
# #     allow_headers=["*"],
# # )

# # # ═══════════════════════════════════════════════════════════════════════════════
# # # STARTUP / SHUTDOWN
# # # ═══════════════════════════════════════════════════════════════════════════════

# # @app.on_event("startup")
# # async def startup():
# #     logger.info("🚀 FastAPI starting up...")


# # @app.on_event("shutdown")
# # async def shutdown():
# #     logger.info("🛑 FastAPI shutting down...")
# #     await close_db()

# # # ═══════════════════════════════════════════════════════════════════════════════
# # # HELPER FUNCTIONS
# # # ═══════════════════════════════════════════════════════════════════════════════

# # async def get_current_user(
# #     authorization: Optional[str] = Header(None),
# #     session: AsyncSession = Depends(get_session)
# # ) -> User:
# #     """Get current authenticated user from Bearer token"""
# #     if not authorization:
# #         raise HTTPException(
# #             status_code=status.HTTP_401_UNAUTHORIZED,
# #             detail="No authorization header",
# #         )

# #     try:
# #         scheme, token = authorization.split()
# #         if scheme.lower() != "bearer":
# #             raise ValueError("Invalid scheme")
# #     except (ValueError, IndexError):
# #         raise HTTPException(
# #             status_code=status.HTTP_401_UNAUTHORIZED,
# #             detail="Invalid authorization header format",
# #         )

# #     user_id = decode_token(token)
# #     if not user_id:
# #         raise HTTPException(
# #             status_code=status.HTTP_401_UNAUTHORIZED,
# #             detail="Invalid or expired token",
# #         )

# #     result = await session.execute(
# #         select(User).where(User.id == UUID(user_id), User.is_active == True)
# #     )
# #     user = result.scalar_one_or_none()

# #     if not user:
# #         raise HTTPException(
# #             status_code=status.HTTP_401_UNAUTHORIZED,
# #             detail="User not found or inactive",
# #         )

# #     return user


# # def calculate_week_boundaries(meeting_date: date) -> tuple:
# #     """Calculate week start (Monday), end (Sunday), and deadline (Sunday 9am)"""
# #     day_of_week = meeting_date.weekday()
# #     week_start = meeting_date - timedelta(days=day_of_week)
# #     week_end = week_start + timedelta(days=6)
# #     deadline = datetime.combine(week_end, datetime.min.time()).replace(hour=9, minute=0, second=0)

# #     return week_start, week_end, deadline


# # # ═══════════════════════════════════════════════════════════════════════════════
# # # ROUTES: ROOT & HEALTH
# # # ═══════════════════════════════════════════════════════════════════════════════

# # @app.get("/")
# # async def root():
# #     """Root endpoint"""
# #     return {
# #         "message": "BLW Cell Reporting API",
# #         "version": "1.0.0",
# #         "docs": "/docs",
# #     }


# # @app.get("/health")
# # async def health_check():
# #     """Health check endpoint"""
# #     return {
# #         "status": "ok",
# #         "message": "BLW Cell Reporting API is running",
# #         "timestamp": datetime.utcnow().isoformat(),
# #     }


# # # ═══════════════════════════════════════════════════════════════════════════════
# # # ROUTES: AUTHENTICATION
# # # ═══════════════════════════════════════════════════════════════════════════════

# # @app.post("/api/auth/login", response_model=LoginResponse, tags=["Auth"])
# # async def login(
# #     request: LoginRequest,
# #     session: AsyncSession = Depends(get_session)
# # ):
# #     """
# #     Login with phone and PIN
# #     Returns JWT token for subsequent requests
# #     """
# #     try:
# #         result = await session.execute(
# #             select(User).where(User.phone == request.phone, User.is_active == True)
# #         )
# #         user = result.scalar_one_or_none()

# #         if not user:
# #             raise HTTPException(
# #                 status_code=status.HTTP_401_UNAUTHORIZED,
# #                 detail="Invalid phone or PIN",
# #             )

# #         # Verify PIN
# #         if not verify_pin(request.pin, user.pin_hash):
# #             raise HTTPException(
# #                 status_code=status.HTTP_401_UNAUTHORIZED,
# #                 detail="Invalid phone or PIN",
# #             )

# #         # Update last login
# #         user.last_login = datetime.utcnow()
# #         await session.commit()

# #         # Create token
# #         access_token = create_access_token(subject=str(user.id))

# #         return LoginResponse(
# #             access_token=access_token,
# #             token_type="bearer",
# #             user={
# #                 "id": str(user.id),
# #                 "phone": user.phone,
# #                 "name": user.name,
# #                 "role": user.role,
# #                 "cell_id": str(user.cell_id) if user.cell_id else None,
# #                 "senior_cell_id": str(user.senior_cell_id) if user.senior_cell_id else None,
# #                 "fellowship_id": str(user.fellowship_id) if user.fellowship_id else None,
# #                 "zone_id": str(user.zone_id) if user.zone_id else None,
# #             }
# #         )

# #     except HTTPException:
# #         raise
# #     except Exception as e:
# #         logger.error(f"Login error: {e}", exc_info=True)
# #         raise HTTPException(
# #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
# #             detail="Login failed"
# #         )


# # # ═══════════════════════════════════════════════════════════════════════════════
# # # ROUTES: ADMIN
# # # ═══════════════════════════════════════════════════════════════════════════════

# # @app.post("/api/admin/users", response_model=UserCreateResponse, tags=["Admin"])
# # async def create_user(
# #     request: UserCreate,
# #     session: AsyncSession = Depends(get_session),
# #     current_user: User = Depends(get_current_user),
# # ):
# #     """
# #     Create new user (System Admin only)
# #     """
# #     try:
# #         if current_user.role != "system_admin":
# #             raise HTTPException(
# #                 status_code=status.HTTP_403_FORBIDDEN,
# #                 detail="Only system admin can create users",
# #             )

# #         result = await session.execute(
# #             select(User).where(User.phone == request.phone)
# #         )
# #         if result.scalar_one_or_none():
# #             raise HTTPException(
# #                 status_code=status.HTTP_400_BAD_REQUEST,
# #                 detail="Phone number already exists",
# #             )

# #         new_user = User(
# #             phone=request.phone,
# #             name=request.name,
# #             pin_hash=hash_default_pin(),
# #             role=request.role,
# #             cell_id=request.cell_id,
# #             senior_cell_id=request.senior_cell_id,
# #             fellowship_id=request.fellowship_id,
# #             zone_id=request.zone_id,
# #             is_active=True,
# #         )

# #         session.add(new_user)
# #         await session.commit()
# #         await session.refresh(new_user)

# #         return UserCreateResponse(
# #             user_id=new_user.id,
# #             phone=new_user.phone,
# #             name=new_user.name,
# #             role=new_user.role,
# #             initial_pin="123456",
# #             message="User created. Share phone and PIN with leader.",
# #         )

# #     except HTTPException:
# #         raise
# #     except Exception as e:
# #         logger.error(f"Create user error: {e}", exc_info=True)
# #         raise HTTPException(
# #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
# #             detail="User creation failed"
# #         )


# # # ═══════════════════════════════════════════════════════════════════════════════
# # # ROUTES: CELL REPORTS
# # # ═══════════════════════════════════════════════════════════════════════════════

# # @app.post("/api/reports/submit", response_model=CellReportResponse, tags=["Reports"])
# # async def submit_report(
# #     request: CellReportSubmit,
# #     session: AsyncSession = Depends(get_session),
# #     current_user: User = Depends(get_current_user),
# # ):
# #     """
# #     Submit a cell report
# #     """
# #     try:
# #         # Check access
# #         if current_user.cell_id != request.cell_id and current_user.role == "cell_leader":
# #             raise HTTPException(
# #                 status_code=status.HTTP_403_FORBIDDEN,
# #                 detail="You can only submit reports for your own cell",
# #             )

# #         # Get cell
# #         result = await session.execute(
# #             select(Cell).where(Cell.id == request.cell_id)
# #         )
# #         cell = result.scalar_one_or_none()
# #         if not cell:
# #             raise HTTPException(
# #                 status_code=status.HTTP_404_NOT_FOUND,
# #                 detail="Cell not found",
# #             )

# #         # Check for duplicate
# #         result = await session.execute(
# #             select(CellReport).where(
# #                 CellReport.cell_id == request.cell_id,
# #                 CellReport.week_start_date == request.week_start_date
# #             )
# #         )
# #         if result.scalar_one_or_none():
# #             raise HTTPException(
# #                 status_code=status.HTTP_409_CONFLICT,
# #                 detail=f"Report already exists for week of {request.week_start_date}",
# #             )

# #         # Calculate deadline
# #         week_start, week_end, deadline = calculate_week_boundaries(request.meeting_date)

# #         # Determine status
# #         now = datetime.utcnow()
# #         status_value = "SUBMITTED" if now <= deadline else "LATE"

# #         # Calculate finance total
# #         finance_total = (
# #             request.finance_oblation +
# #             request.finance_offerings +
# #             request.finance_tithes +
# #             request.finance_thanksgiving +
# #             request.finance_seed +
# #             request.finance_partnership +
# #             request.finance_first_fruits
# #         )

# #         # Create report
# #         cell_report = CellReport(
# #             cell_id=request.cell_id,
# #             submitted_by_id=current_user.id,
# #             meeting_date=request.meeting_date,
# #             week_start_date=request.week_start_date,
# #             week_end_date=request.week_end_date,
# #             actual_meeting_day=request.actual_meeting_day,
# #             submission_deadline=deadline,
# #             status=status_value,
# #             submitted_at=now,
# #             synced_from_offline=False,

# #             # Meeting details
# #             meeting_week=request.meeting_week,
# #             meeting_type=request.meeting_type,
# #             meeting_duration=request.meeting_duration,
# #             bible_class_teachers=[t for t in request.bible_class_teachers if t],
# #             activities=[a.dict() for a in request.activities],

# #             # Attendance
# #             first_timers=request.first_timers,
# #             number_saved=request.number_saved,
# #             filled_holy_ghost=request.filled_holy_ghost,
# #             total_attendance=request.total_attendance,
# #             new_members=request.new_members,
# #             souls_retained=request.souls_retained,
# #             souls_won=request.souls_won,
# #             souls_on_tracker=request.souls_on_tracker,

# #             # Finances
# #             finance_oblation=request.finance_oblation,
# #             finance_offerings=request.finance_offerings,
# #             finance_tithes=request.finance_tithes,
# #             finance_thanksgiving=request.finance_thanksgiving,
# #             finance_seed=request.finance_seed,
# #             finance_partnership=request.finance_partnership,
# #             finance_first_fruits=request.finance_first_fruits,
# #             finance_total=finance_total,
# #             finance_collected_by=request.finance_collected_by,

# #             # Text
# #             testimonies=request.testimonies,
# #             monthly_plans=request.monthly_plans,
# #             challenges=request.challenges,

# #             # Soul winning
# #             soul_winning_records=[r.dict() for r in request.soul_winning_records],

# #             # Optional
# #             pastors_remarks=request.pastors_remarks,
# #             other_info=request.other_info,
# #             photo_urls=request.photo_urls,
# #         )

# #         session.add(cell_report)
# #         await session.commit()
# #         await session.refresh(cell_report)

# #         return CellReportResponse(
# #             id=cell_report.id,
# #             cell_id=cell_report.cell_id,
# #             status=cell_report.status,
# #             submitted_at=cell_report.submitted_at,
# #             submission_deadline=cell_report.submission_deadline,
# #             message=f"Report submitted {'on time' if status_value == 'SUBMITTED' else 'late'}!",
# #         )

# #     except HTTPException:
# #         raise
# #     except Exception as e:
# #         logger.error(f"Submit report error: {e}", exc_info=True)
# #         raise HTTPException(
# #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
# #             detail="Report submission failed"
# #         )


# # @app.get("/api/reports/{report_id}", tags=["Reports"])
# # async def get_report(
# #     report_id: UUID,
# #     session: AsyncSession = Depends(get_session),
# #     current_user: User = Depends(get_current_user),
# # ):
# #     """Get a single report"""
# #     try:
# #         result = await session.execute(
# #             select(CellReport).where(CellReport.id == report_id)
# #         )
# #         report = result.scalar_one_or_none()

# #         if not report:
# #             raise HTTPException(
# #                 status_code=status.HTTP_404_NOT_FOUND,
# #                 detail="Report not found",
# #             )

# #         # Check access
# #         if (
# #             report.submitted_by_id != current_user.id and
# #             current_user.cell_id != report.cell_id and
# #             current_user.role not in ["senior_cell_leader", "fellowship_pastor", "zonal_pastor", "zonal_admin", "system_admin"]
# #         ):
# #             raise HTTPException(
# #                 status_code=status.HTTP_403_FORBIDDEN,
# #                 detail="You don't have access to this report",
# #             )

# #         return report

# #     except HTTPException:
# #         raise
# #     except Exception as e:
# #         logger.error(f"Get report error: {e}", exc_info=True)
# #         raise HTTPException(
# #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
# #             detail="Failed to fetch report"
# #         )
























# # # # main.py - FastAPI Application

# # # from fastapi import FastAPI, Depends, HTTPException, status
# # # from fastapi.middleware.cors import CORSMiddleware
# # # from sqlalchemy.ext.asyncio import AsyncSession
# # # from sqlalchemy import select
# # # from datetime import datetime, date
# # # from uuid import UUID
# # # import logging

# # # from database import get_session, init_db, close_db
# # # from models import User, Cell, CellReport, Zone, Fellowship
# # # from schemas import (
# # #     LoginRequest, LoginResponse, UserCreate, UserCreateResponse,
# # #     CellReportSubmit, CellReportResponse, ErrorResponse
# # # )
# # # from auth import hash_pin, verify_pin, create_access_token, decode_token, hash_default_pin

# # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # SETUP
# # # # ═══════════════════════════════════════════════════════════════════════════════

# # # logging.basicConfig(level=logging.INFO)
# # # logger = logging.getLogger(__name__)

# # # app = FastAPI(
# # #     title="BLW Cell Reporting System",
# # #     description="API for cell report submission and dashboards",
# # #     version="1.0.0",
# # # )

# # # app.add_middleware(
# # #     CORSMiddleware,
# # #     allow_origins=["*"],
# # #     allow_credentials=True,
# # #     allow_methods=["*"],
# # #     allow_headers=["*"],
# # # )

# # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # STARTUP / SHUTDOWN
# # # # ═══════════════════════════════════════════════════════════════════════════════

# # # @app.on_event("startup")
# # # async def startup():
# # #     logger.info("🚀 FastAPI starting up...")


# # # @app.on_event("shutdown")
# # # async def shutdown():
# # #     logger.info("🛑 FastAPI shutting down...")
# # #     await close_db()

# # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # HELPER FUNCTIONS
# # # # ═══════════════════════════════════════════════════════════════════════════════

# # # async def get_current_user(
# # #     token: str = None,
# # #     session: AsyncSession = Depends(get_session)
# # # ) -> User:
# # #     """Get current authenticated user"""
# # #     if not token:
# # #         raise HTTPException(
# # #             status_code=status.HTTP_401_UNAUTHORIZED,
# # #             detail="No token provided",
# # #         )

# # #     user_id = decode_token(token)
# # #     if not user_id:
# # #         raise HTTPException(
# # #             status_code=status.HTTP_401_UNAUTHORIZED,
# # #             detail="Invalid or expired token",
# # #         )

# # #     result = await session.execute(
# # #         select(User).where(User.id == UUID(user_id))
# # #     )
# # #     user = result.scalar_one_or_none()

# # #     if not user or not user.is_active:
# # #         raise HTTPException(
# # #             status_code=status.HTTP_401_UNAUTHORIZED,
# # #             detail="User not found or inactive",
# # #         )

# # #     return user


# # # def calculate_week_boundaries(meeting_date: date) -> tuple:
# # #     """Calculate week start (Monday), end (Sunday), and deadline (Sunday 9am)"""
# # #     from datetime import datetime, time, timedelta

# # #     day_of_week = meeting_date.weekday()
# # #     week_start = meeting_date - timedelta(days=day_of_week)
# # #     week_end = week_start + timedelta(days=6)
# # #     deadline = datetime.combine(week_end, time(9, 0, 0))

# # #     return week_start, week_end, deadline


# # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # ROUTES: HEALTH CHECK
# # # # ═══════════════════════════════════════════════════════════════════════════════

# # # @app.get("/health")
# # # async def health_check():
# # #     return {
# # #         "status": "ok",
# # #         "message": "BLW Cell Reporting API is running",
# # #         "timestamp": datetime.utcnow().isoformat(),
# # #     }


# # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # ROUTES: AUTHENTICATION
# # # # ═══════════════════════════════════════════════════════════════════════════════

# # # @app.post("/api/auth/login", response_model=LoginResponse, tags=["Auth"])
# # # async def login(
# # #     request: LoginRequest,
# # #     session: AsyncSession = Depends(get_session)
# # # ):
# # #     """Login with phone and PIN. Returns JWT token for subsequent requests."""
# # #     try:
# # #         result = await session.execute(
# # #             select(User).where(User.phone == request.phone).where(User.is_active == True)
# # #         )
# # #         user = result.scalar_one_or_none()

# # #         if not user:
# # #             raise HTTPException(
# # #                 status_code=status.HTTP_401_UNAUTHORIZED,
# # #                 detail="Invalid phone or PIN",
# # #             )

# # #         if not verify_pin(request.pin, user.pin_hash):
# # #             raise HTTPException(
# # #                 status_code=status.HTTP_401_UNAUTHORIZED,
# # #                 detail="Invalid phone or PIN",
# # #             )

# # #         user.last_login = datetime.utcnow()
# # #         await session.commit()

# # #         access_token = create_access_token(subject=str(user.id))

# # #         return LoginResponse(
# # #             access_token=access_token,
# # #             token_type="bearer",
# # #             user={
# # #                 "id": str(user.id),
# # #                 "phone": user.phone,
# # #                 "name": user.name,
# # #                 "role": user.role,
# # #                 "cell_id": str(user.cell_id) if user.cell_id else None,
# # #                 "senior_cell_id": str(user.senior_cell_id) if user.senior_cell_id else None,
# # #                 "fellowship_id": str(user.fellowship_id) if user.fellowship_id else None,
# # #                 "zone_id": str(user.zone_id) if user.zone_id else None,
# # #             }
# # #         )

# # #     except HTTPException:
# # #         raise
# # #     except Exception as e:
# # #         logger.error(f"Login error: {e}", exc_info=True)
# # #         raise HTTPException(
# # #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
# # #             detail=f"Login failed: {str(e)}"
# # #         )


# # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # ROUTES: ADMIN - CREATE USERS
# # # # ═══════════════════════════════════════════════════════════════════════════════

# # # @app.post("/api/admin/users", response_model=UserCreateResponse, tags=["Admin"])
# # # async def create_user(
# # #     request: UserCreate,
# # #     session: AsyncSession = Depends(get_session),
# # #     current_user: User = Depends(get_current_user),
# # # ):
# # #     """Create new user (Admin only)."""
# # #     try:
# # #         if current_user.role != "system_admin":
# # #             raise HTTPException(
# # #                 status_code=status.HTTP_403_FORBIDDEN,
# # #                 detail="Only system admin can create users",
# # #             )

# # #         result = await session.execute(
# # #             select(User).where(User.phone == request.phone)
# # #         )
# # #         if result.scalar_one_or_none():
# # #             raise HTTPException(
# # #                 status_code=status.HTTP_400_BAD_REQUEST,
# # #                 detail="Phone number already exists",
# # #             )

# # #         new_user = User(
# # #             phone=request.phone,
# # #             name=request.name,
# # #             pin_hash=hash_default_pin(),
# # #             role=request.role,
# # #             cell_id=request.cell_id,
# # #             senior_cell_id=request.senior_cell_id,
# # #             fellowship_id=request.fellowship_id,
# # #             zone_id=request.zone_id,
# # #             is_active=True,
# # #         )

# # #         session.add(new_user)
# # #         await session.commit()
# # #         await session.refresh(new_user)

# # #         return UserCreateResponse(
# # #             user_id=new_user.id,
# # #             phone=new_user.phone,
# # #             name=new_user.name,
# # #             role=new_user.role,
# # #             initial_pin="123456",
# # #             message="User created. Share phone and PIN with leader.",
# # #         )

# # #     except HTTPException:
# # #         raise
# # #     except Exception as e:
# # #         logger.error(f"Create user error: {e}", exc_info=True)
# # #         raise HTTPException(
# # #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
# # #             detail=f"User creation failed: {str(e)}"
# # #         )


# # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # ROUTES: CELL REPORTS
# # # # ═══════════════════════════════════════════════════════════════════════════════

# # # @app.post("/api/reports/submit", response_model=CellReportResponse, tags=["Reports"])
# # # async def submit_report(
# # #     request: CellReportSubmit,
# # #     session: AsyncSession = Depends(get_session),
# # #     current_user: User = Depends(get_current_user),
# # # ):
# # #     """
# # #     Submit a cell report.

# # #     - Validates all required fields
# # #     - Calculates deadline (Sunday 9am)
# # #     - Determines status (SUBMITTED or LATE)
# # #     - Checks for duplicates (only one report per cell per week)
# # #     """
# # #     try:
# # #         if current_user.cell_id != request.cell_id and current_user.role == "cell_leader":
# # #             raise HTTPException(
# # #                 status_code=status.HTTP_403_FORBIDDEN,
# # #                 detail="You can only submit reports for your own cell",
# # #             )

# # #         result = await session.execute(
# # #             select(Cell).where(Cell.id == request.cell_id)
# # #         )
# # #         cell = result.scalar_one_or_none()
# # #         if not cell:
# # #             raise HTTPException(
# # #                 status_code=status.HTTP_404_NOT_FOUND,
# # #                 detail="Cell not found",
# # #             )

# # #         result = await session.execute(
# # #             select(CellReport).where(
# # #                 (CellReport.cell_id == request.cell_id) &
# # #                 (CellReport.week_start_date == request.week_start_date)
# # #             )
# # #         )
# # #         if result.scalar_one_or_none():
# # #             raise HTTPException(
# # #                 status_code=status.HTTP_409_CONFLICT,
# # #                 detail=f"Report already exists for week of {request.week_start_date}",
# # #             )

# # #         week_start, week_end, deadline = calculate_week_boundaries(request.meeting_date)

# # #         now = datetime.utcnow()
# # #         status_value = "SUBMITTED" if now <= deadline else "LATE"

# # #         finance_total = (
# # #             request.finance_oblation +
# # #             request.finance_offerings +
# # #             request.finance_tithes +
# # #             request.finance_thanksgiving +
# # #             request.finance_seed +
# # #             request.finance_partnership +
# # #             request.finance_first_fruits
# # #         )

# # #         cell_report = CellReport(
# # #             cell_id=request.cell_id,
# # #             submitted_by_id=current_user.id,  # FIX: renamed from submitted_by to match models.py
# # #             meeting_date=request.meeting_date,
# # #             week_start_date=request.week_start_date,
# # #             week_end_date=request.week_end_date,
# # #             actual_meeting_day=request.actual_meeting_day,
# # #             submission_deadline=deadline,
# # #             status=status_value,
# # #             submitted_at=now,
# # #             synced_from_offline=False,

# # #             # Meeting details
# # #             meeting_week=request.meeting_week,
# # #             meeting_type=request.meeting_type,
# # #             meeting_duration=request.meeting_duration,
# # #             bible_class_teachers=[t for t in request.bible_class_teachers if t],
# # #             activities=[a.dict() for a in request.activities],

# # #             # Attendance
# # #             first_timers=request.first_timers,
# # #             number_saved=request.number_saved,
# # #             filled_holy_ghost=request.filled_holy_ghost,
# # #             total_attendance=request.total_attendance,
# # #             new_members=request.new_members,
# # #             souls_retained=request.souls_retained,
# # #             souls_won=request.souls_won,
# # #             souls_on_tracker=request.souls_on_tracker,

# # #             # Finances
# # #             finance_oblation=request.finance_oblation,
# # #             finance_offerings=request.finance_offerings,
# # #             finance_tithes=request.finance_tithes,
# # #             finance_thanksgiving=request.finance_thanksgiving,
# # #             finance_seed=request.finance_seed,
# # #             finance_partnership=request.finance_partnership,
# # #             finance_first_fruits=request.finance_first_fruits,
# # #             finance_total=finance_total,
# # #             finance_collected_by=request.finance_collected_by,

# # #             # Text
# # #             testimonies=request.testimonies,
# # #             monthly_plans=request.monthly_plans,
# # #             challenges=request.challenges,

# # #             # Soul winning
# # #             soul_winning_records=[r.dict() for r in request.soul_winning_records],

# # #             # Optional
# # #             pastors_remarks=request.pastors_remarks,
# # #             other_info=request.other_info,
# # #             photo_urls=request.photo_urls,
# # #         )

# # #         session.add(cell_report)
# # #         await session.commit()
# # #         await session.refresh(cell_report)

# # #         return CellReportResponse(
# # #             id=cell_report.id,
# # #             cell_id=cell_report.cell_id,
# # #             status=cell_report.status,
# # #             submitted_at=cell_report.submitted_at,
# # #             submission_deadline=cell_report.submission_deadline,
# # #             message=f"Report submitted {'on time' if status_value == 'SUBMITTED' else 'late'}! Deadline was {deadline.strftime('%A %I:%M %p')}",
# # #         )

# # #     except HTTPException:
# # #         raise
# # #     except Exception as e:
# # #         logger.error(f"Submit report error: {e}", exc_info=True)
# # #         raise HTTPException(
# # #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
# # #             detail=f"Report submission failed: {str(e)}"
# # #         )


# # # @app.get("/api/reports/{report_id}", tags=["Reports"])
# # # async def get_report(
# # #     report_id: UUID,
# # #     session: AsyncSession = Depends(get_session),
# # #     current_user: User = Depends(get_current_user),
# # # ):
# # #     """Get a single report"""
# # #     try:
# # #         result = await session.execute(
# # #             select(CellReport).where(CellReport.id == report_id)
# # #         )
# # #         report = result.scalar_one_or_none()

# # #         if not report:
# # #             raise HTTPException(
# # #                 status_code=status.HTTP_404_NOT_FOUND,
# # #                 detail="Report not found",
# # #             )

# # #         # Check access (only cell leader, senior CL, or pastors can view)
# # #         if (
# # #             report.submitted_by_id != current_user.id and  # FIX: renamed from report.submitted_by to match models.py
# # #             current_user.cell_id != report.cell_id and
# # #             current_user.role not in ["senior_cell_leader", "fellowship_pastor", "zonal_pastor", "zonal_admin", "system_admin"]
# # #         ):
# # #             raise HTTPException(
# # #                 status_code=status.HTTP_403_FORBIDDEN,
# # #                 detail="You don't have access to this report",
# # #             )

# # #         return report

# # #     except HTTPException:
# # #         raise
# # #     except Exception as e:
# # #         logger.error(f"Get report error: {e}", exc_info=True)
# # #         raise HTTPException(
# # #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
# # #             detail=f"Failed to fetch report: {str(e)}"
# # #         )


# # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # ROOT
# # # # ═══════════════════════════════════════════════════════════════════════════════

# # # @app.get("/")
# # # async def root():
# # #     return {
# # #         "message": "BLW Cell Reporting API",
# # #         "version": "1.0.0",
# # #         "docs": "/docs",
# # #     }












# # # # # main.py - FastAPI Application

# # # # from fastapi import FastAPI, Depends, HTTPException, status
# # # # from fastapi.middleware.cors import CORSMiddleware
# # # # from sqlalchemy.ext.asyncio import AsyncSession
# # # # from sqlalchemy import select
# # # # from datetime import datetime, date
# # # # from uuid import UUID
# # # # import logging

# # # # from database import get_session, init_db, close_db
# # # # from models import User, Cell, CellReport, Zone, Fellowship
# # # # from schemas import (
# # # #     LoginRequest, LoginResponse, UserCreate, UserCreateResponse,
# # # #     CellReportSubmit, CellReportResponse, ErrorResponse
# # # # )
# # # # from auth import hash_pin, verify_pin, create_access_token, decode_token, hash_default_pin

# # # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # # SETUP
# # # # # ═══════════════════════════════════════════════════════════════════════════════

# # # # # Logging
# # # # logging.basicConfig(level=logging.INFO)
# # # # logger = logging.getLogger(__name__)

# # # # # FastAPI app
# # # # app = FastAPI(
# # # #     title="BLW Cell Reporting System",
# # # #     description="API for cell report submission and dashboards",
# # # #     version="1.0.0",
# # # # )

# # # # # CORS middleware
# # # # app.add_middleware(
# # # #     CORSMiddleware,
# # # #     allow_origins=["*"],
# # # #     allow_credentials=True,
# # # #     allow_methods=["*"],
# # # #     allow_headers=["*"],
# # # # )

# # # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # # STARTUP / SHUTDOWN
# # # # # ═══════════════════════════════════════════════════════════════════════════════

# # # # @app.on_event("startup")
# # # # async def startup():
# # # #     logger.info("🚀 FastAPI starting up...")
# # # #     # Database is already initialized via schema.sql
# # # #     # This is just for logging


# # # # @app.on_event("shutdown")
# # # # async def shutdown():
# # # #     logger.info("🛑 FastAPI shutting down...")
# # # #     await close_db()

# # # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # # HELPER FUNCTIONS
# # # # # ═══════════════════════════════════════════════════════════════════════════════

# # # # async def get_current_user(
# # # #     token: str = None,
# # # #     session: AsyncSession = Depends(get_session)
# # # # ) -> User:
# # # #     """Get current authenticated user"""
# # # #     if not token:
# # # #         raise HTTPException(
# # # #             status_code=status.HTTP_401_UNAUTHORIZED,
# # # #             detail="No token provided",
# # # #         )

# # # #     user_id = decode_token(token)
# # # #     if not user_id:
# # # #         raise HTTPException(
# # # #             status_code=status.HTTP_401_UNAUTHORIZED,
# # # #             detail="Invalid or expired token",
# # # #         )

# # # #     result = await session.execute(
# # # #         select(User).where(User.id == UUID(user_id))
# # # #     )
# # # #     user = result.scalar_one_or_none()

# # # #     if not user or not user.is_active:
# # # #         raise HTTPException(
# # # #             status_code=status.HTTP_401_UNAUTHORIZED,
# # # #             detail="User not found or inactive",
# # # #         )

# # # #     return user


# # # # def calculate_week_boundaries(meeting_date: date) -> tuple:
# # # #     """Calculate week start (Monday), end (Sunday), and deadline (Sunday 9am)"""
# # # #     from datetime import datetime, time, timedelta

# # # #     # Get the day of week (0=Monday, 6=Sunday)
# # # #     day_of_week = meeting_date.weekday()

# # # #     # Calculate Monday of this week
# # # #     week_start = meeting_date - timedelta(days=day_of_week)

# # # #     # Calculate Sunday of this week
# # # #     week_end = week_start + timedelta(days=6)

# # # #     # Deadline: Sunday 9am UTC
# # # #     deadline = datetime.combine(week_end, time(9, 0, 0))

# # # #     return week_start, week_end, deadline


# # # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # # ROUTES: HEALTH CHECK
# # # # # ═══════════════════════════════════════════════════════════════════════════════

# # # # @app.get("/health")
# # # # async def health_check():
# # # #     """Health check endpoint"""
# # # #     return {
# # # #         "status": "ok",
# # # #         "message": "BLW Cell Reporting API is running",
# # # #         "timestamp": datetime.utcnow().isoformat(),
# # # #     }


# # # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # # ROUTES: AUTHENTICATION
# # # # # ═══════════════════════════════════════════════════════════════════════════════

# # # # @app.post("/api/auth/login", response_model=LoginResponse, tags=["Auth"])
# # # # async def login(
# # # #     request: LoginRequest,
# # # #     session: AsyncSession = Depends(get_session)
# # # # ):
# # # #     """
# # # #     Login with phone and PIN

# # # #     Returns JWT token for subsequent requests
# # # #     """
# # # #     try:
# # # #         # Find user by phone
# # # #         result = await session.execute(
# # # #             select(User).where(User.phone == request.phone).where(User.is_active == True)
# # # #         )
# # # #         user = result.scalar_one_or_none()

# # # #         if not user:
# # # #             raise HTTPException(
# # # #                 status_code=status.HTTP_401_UNAUTHORIZED,
# # # #                 detail="Invalid phone or PIN",
# # # #             )

# # # #         # Verify PIN
# # # #         if not verify_pin(request.pin, user.pin_hash):
# # # #             raise HTTPException(
# # # #                 status_code=status.HTTP_401_UNAUTHORIZED,
# # # #                 detail="Invalid phone or PIN",
# # # #             )

# # # #         # Update last login
# # # #         user.last_login = datetime.utcnow()
# # # #         await session.commit()

# # # #         # Create token
# # # #         access_token = create_access_token(subject=str(user.id))

# # # #         return LoginResponse(
# # # #             access_token=access_token,
# # # #             token_type="bearer",
# # # #             user={
# # # #                 "id": str(user.id),
# # # #                 "phone": user.phone,
# # # #                 "name": user.name,
# # # #                 "role": user.role,
# # # #                 "cell_id": str(user.cell_id) if user.cell_id else None,
# # # #                 "senior_cell_id": str(user.senior_cell_id) if user.senior_cell_id else None,
# # # #                 "fellowship_id": str(user.fellowship_id) if user.fellowship_id else None,
# # # #                 "zone_id": str(user.zone_id) if user.zone_id else None,
# # # #             }
# # # #         )

# # # #     except HTTPException:
# # # #         raise
# # # #     except Exception as e:
# # # #         logger.error(f"Login error: {e}", exc_info=True)
# # # #         raise HTTPException(
# # # #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
# # # #             detail=f"Login failed: {str(e)}"
# # # #         )


# # # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # # ROUTES: ADMIN - CREATE USERS
# # # # # ═══════════════════════════════════════════════════════════════════════════════

# # # # @app.post("/api/admin/users", response_model=UserCreateResponse, tags=["Admin"])
# # # # async def create_user(
# # # #     request: UserCreate,
# # # #     session: AsyncSession = Depends(get_session),
# # # #     current_user: User = Depends(get_current_user),
# # # # ):
# # # #     """
# # # #     Create new user (Admin only)

# # # #     System admin can create cell leaders, senior cell leaders, pastors, etc.
# # # #     """
# # # #     try:
# # # #         # Check if requester is system admin
# # # #         if current_user.role != "system_admin":
# # # #             raise HTTPException(
# # # #                 status_code=status.HTTP_403_FORBIDDEN,
# # # #                 detail="Only system admin can create users",
# # # #             )

# # # #         # Check if phone already exists
# # # #         result = await session.execute(
# # # #             select(User).where(User.phone == request.phone)
# # # #         )
# # # #         if result.scalar_one_or_none():
# # # #             raise HTTPException(
# # # #                 status_code=status.HTTP_400_BAD_REQUEST,
# # # #                 detail="Phone number already exists",
# # # #             )

# # # #         # Create new user with default PIN
# # # #         new_user = User(
# # # #             phone=request.phone,
# # # #             name=request.name,
# # # #             pin_hash=hash_default_pin(),
# # # #             role=request.role,
# # # #             cell_id=request.cell_id,
# # # #             senior_cell_id=request.senior_cell_id,
# # # #             fellowship_id=request.fellowship_id,
# # # #             zone_id=request.zone_id,
# # # #             is_active=True,
# # # #         )

# # # #         session.add(new_user)
# # # #         await session.commit()
# # # #         await session.refresh(new_user)

# # # #         return UserCreateResponse(
# # # #             user_id=new_user.id,
# # # #             phone=new_user.phone,
# # # #             name=new_user.name,
# # # #             role=new_user.role,
# # # #             initial_pin="123456",
# # # #             message="User created. Share phone and PIN with leader.",
# # # #         )

# # # #     except HTTPException:
# # # #         raise
# # # #     except Exception as e:
# # # #         logger.error(f"Create user error: {e}", exc_info=True)
# # # #         raise HTTPException(
# # # #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
# # # #             detail=f"User creation failed: {str(e)}"
# # # #         )


# # # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # # ROUTES: CELL REPORTS
# # # # # ═══════════════════════════════════════════════════════════════════════════════

# # # # @app.post("/api/reports/submit", response_model=CellReportResponse, tags=["Reports"])
# # # # async def submit_report(
# # # #     request: CellReportSubmit,
# # # #     session: AsyncSession = Depends(get_session),
# # # #     current_user: User = Depends(get_current_user),
# # # # ):
# # # #     """
# # # #     Submit a cell report

# # # #     - Validates all required fields
# # # #     - Calculates deadline (Sunday 9am)
# # # #     - Determines status (SUBMITTED or LATE)
# # # #     - Checks for duplicates (only one report per cell per week)
# # # #     """
# # # #     try:
# # # #         # Verify user has access to this cell
# # # #         if current_user.cell_id != request.cell_id and current_user.role == "cell_leader":
# # # #             raise HTTPException(
# # # #                 status_code=status.HTTP_403_FORBIDDEN,
# # # #                 detail="You can only submit reports for your own cell",
# # # #             )

# # # #         # Get cell info
# # # #         result = await session.execute(
# # # #             select(Cell).where(Cell.id == request.cell_id)
# # # #         )
# # # #         cell = result.scalar_one_or_none()
# # # #         if not cell:
# # # #             raise HTTPException(
# # # #                 status_code=status.HTTP_404_NOT_FOUND,
# # # #                 detail="Cell not found",
# # # #             )

# # # #         # Check for duplicate report (only one per week)
# # # #         result = await session.execute(
# # # #             select(CellReport).where(
# # # #                 (CellReport.cell_id == request.cell_id) &
# # # #                 (CellReport.week_start_date == request.week_start_date)
# # # #             )
# # # #         )
# # # #         if result.scalar_one_or_none():
# # # #             raise HTTPException(
# # # #                 status_code=status.HTTP_409_CONFLICT,
# # # #                 detail=f"Report already exists for week of {request.week_start_date}",
# # # #             )

# # # #         # Calculate deadline
# # # #         week_start, week_end, deadline = calculate_week_boundaries(request.meeting_date)

# # # #         # Determine status
# # # #         now = datetime.utcnow()
# # # #         status_value = "SUBMITTED" if now <= deadline else "LATE"

# # # #         # Calculate finance total
# # # #         finance_total = (
# # # #             request.finance_oblation +
# # # #             request.finance_offerings +
# # # #             request.finance_tithes +
# # # #             request.finance_thanksgiving +
# # # #             request.finance_seed +
# # # #             request.finance_partnership +
# # # #             request.finance_first_fruits
# # # #         )

# # # #         # Create report
# # # #         cell_report = CellReport(
# # # #             cell_id=request.cell_id,
# # # #             submitted_by=current_user.id,
# # # #             meeting_date=request.meeting_date,
# # # #             week_start_date=request.week_start_date,
# # # #             week_end_date=request.week_end_date,
# # # #             actual_meeting_day=request.actual_meeting_day,
# # # #             submission_deadline=deadline,
# # # #             status=status_value,
# # # #             submitted_at=now,
# # # #             synced_from_offline=False,

# # # #             # Meeting details
# # # #             meeting_week=request.meeting_week,
# # # #             meeting_type=request.meeting_type,
# # # #             meeting_duration=request.meeting_duration,
# # # #             bible_class_teachers=[t for t in request.bible_class_teachers if t],
# # # #             activities=[a.dict() for a in request.activities],

# # # #             # Attendance
# # # #             first_timers=request.first_timers,
# # # #             number_saved=request.number_saved,
# # # #             filled_holy_ghost=request.filled_holy_ghost,
# # # #             total_attendance=request.total_attendance,
# # # #             new_members=request.new_members,
# # # #             souls_retained=request.souls_retained,
# # # #             souls_won=request.souls_won,
# # # #             souls_on_tracker=request.souls_on_tracker,

# # # #             # Finances
# # # #             finance_oblation=request.finance_oblation,
# # # #             finance_offerings=request.finance_offerings,
# # # #             finance_tithes=request.finance_tithes,
# # # #             finance_thanksgiving=request.finance_thanksgiving,
# # # #             finance_seed=request.finance_seed,
# # # #             finance_partnership=request.finance_partnership,
# # # #             finance_first_fruits=request.finance_first_fruits,
# # # #             finance_total=finance_total,
# # # #             finance_collected_by=request.finance_collected_by,

# # # #             # Text
# # # #             testimonies=request.testimonies,
# # # #             monthly_plans=request.monthly_plans,
# # # #             challenges=request.challenges,

# # # #             # Soul winning
# # # #             soul_winning_records=[r.dict() for r in request.soul_winning_records],

# # # #             # Optional
# # # #             pastors_remarks=request.pastors_remarks,
# # # #             other_info=request.other_info,
# # # #             photo_urls=request.photo_urls,
# # # #         )

# # # #         session.add(cell_report)
# # # #         await session.commit()
# # # #         await session.refresh(cell_report)

# # # #         return CellReportResponse(
# # # #             id=cell_report.id,
# # # #             cell_id=cell_report.cell_id,
# # # #             status=cell_report.status,
# # # #             submitted_at=cell_report.submitted_at,
# # # #             submission_deadline=cell_report.submission_deadline,
# # # #             message=f"Report submitted {'on time' if status_value == 'SUBMITTED' else 'late'}! Deadline was {deadline.strftime('%A %I:%M %p')}",
# # # #         )

# # # #     except HTTPException:
# # # #         raise
# # # #     except Exception as e:
# # # #         logger.error(f"Submit report error: {e}", exc_info=True)
# # # #         raise HTTPException(
# # # #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
# # # #             detail=f"Report submission failed: {str(e)}"
# # # #         )


# # # # @app.get("/api/reports/{report_id}", tags=["Reports"])
# # # # async def get_report(
# # # #     report_id: UUID,
# # # #     session: AsyncSession = Depends(get_session),
# # # #     current_user: User = Depends(get_current_user),
# # # # ):
# # # #     """Get a single report"""
# # # #     try:
# # # #         result = await session.execute(
# # # #             select(CellReport).where(CellReport.id == report_id)
# # # #         )
# # # #         report = result.scalar_one_or_none()

# # # #         if not report:
# # # #             raise HTTPException(
# # # #                 status_code=status.HTTP_404_NOT_FOUND,
# # # #                 detail="Report not found",
# # # #             )

# # # #         # Check access (only cell leader, senior CL, or pastors can view)
# # # #         if (
# # # #             report.submitted_by != current_user.id and
# # # #             current_user.cell_id != report.cell_id and
# # # #             current_user.role not in ["senior_cell_leader", "fellowship_pastor", "zonal_pastor", "zonal_admin", "system_admin"]
# # # #         ):
# # # #             raise HTTPException(
# # # #                 status_code=status.HTTP_403_FORBIDDEN,
# # # #                 detail="You don't have access to this report",
# # # #             )

# # # #         return report

# # # #     except HTTPException:
# # # #         raise
# # # #     except Exception as e:
# # # #         logger.error(f"Get report error: {e}", exc_info=True)
# # # #         raise HTTPException(
# # # #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
# # # #             detail=f"Failed to fetch report: {str(e)}"
# # # #         )


# # # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # # ROOT
# # # # # ═══════════════════════════════════════════════════════════════════════════════

# # # # @app.get("/")
# # # # async def root():
# # # #     """Root endpoint"""
# # # #     return {
# # # #         "message": "BLW Cell Reporting API",
# # # #         "version": "1.0.0",
# # # #         "docs": "/docs",
# # # #     }












# # # # # # main.py - FastAPI Application

# # # # # from fastapi import FastAPI, Depends, HTTPException, status
# # # # # from fastapi.middleware.cors import CORSMiddleware
# # # # # from sqlalchemy.ext.asyncio import AsyncSession
# # # # # from sqlalchemy import select
# # # # # from datetime import datetime, date
# # # # # from uuid import UUID
# # # # # import logging

# # # # # from database import get_session, init_db, close_db
# # # # # from models import User, Cell, CellReport, Zone, Fellowship
# # # # # from schemas import (
# # # # #     LoginRequest, LoginResponse, UserCreate, UserCreateResponse,
# # # # #     CellReportSubmit, CellReportResponse, ErrorResponse
# # # # # )
# # # # # from auth import hash_pin, verify_pin, create_access_token, decode_token, hash_default_pin

# # # # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # # # SETUP
# # # # # # ═══════════════════════════════════════════════════════════════════════════════

# # # # # # Logging
# # # # # logging.basicConfig(level=logging.INFO)
# # # # # logger = logging.getLogger(__name__)

# # # # # # FastAPI app
# # # # # app = FastAPI(
# # # # #     title="BLW Cell Reporting System",
# # # # #     description="API for cell report submission and dashboards",
# # # # #     version="1.0.0",
# # # # # )

# # # # # # CORS middleware
# # # # # app.add_middleware(
# # # # #     CORSMiddleware,
# # # # #     allow_origins=["*"],
# # # # #     allow_credentials=True,
# # # # #     allow_methods=["*"],
# # # # #     allow_headers=["*"],
# # # # # )

# # # # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # # # STARTUP / SHUTDOWN
# # # # # # ═══════════════════════════════════════════════════════════════════════════════

# # # # # @app.on_event("startup")
# # # # # async def startup():
# # # # #     logger.info("🚀 FastAPI starting up...")
# # # # #     # Database is already initialized via schema.sql
# # # # #     # This is just for logging


# # # # # @app.on_event("shutdown")
# # # # # async def shutdown():
# # # # #     logger.info("🛑 FastAPI shutting down...")
# # # # #     await close_db()

# # # # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # # # HELPER FUNCTIONS
# # # # # # ═══════════════════════════════════════════════════════════════════════════════

# # # # # async def get_current_user(
# # # # #     token: str = None,
# # # # #     session: AsyncSession = Depends(get_session)
# # # # # ) -> User:
# # # # #     """Get current authenticated user"""
# # # # #     if not token:
# # # # #         raise HTTPException(
# # # # #             status_code=status.HTTP_401_UNAUTHORIZED,
# # # # #             detail="No token provided",
# # # # #         )

# # # # #     user_id = decode_token(token)
# # # # #     if not user_id:
# # # # #         raise HTTPException(
# # # # #             status_code=status.HTTP_401_UNAUTHORIZED,
# # # # #             detail="Invalid or expired token",
# # # # #         )

# # # # #     result = await session.execute(
# # # # #         select(User).where(User.id == UUID(user_id))
# # # # #     )
# # # # #     user = result.scalar_one_or_none()

# # # # #     if not user or not user.is_active:
# # # # #         raise HTTPException(
# # # # #             status_code=status.HTTP_401_UNAUTHORIZED,
# # # # #             detail="User not found or inactive",
# # # # #         )

# # # # #     return user


# # # # # def calculate_week_boundaries(meeting_date: date) -> tuple:
# # # # #     """Calculate week start (Monday), end (Sunday), and deadline (Sunday 9am)"""
# # # # #     from datetime import datetime, time, timedelta
    
# # # # #     # Get the day of week (0=Monday, 6=Sunday)
# # # # #     day_of_week = meeting_date.weekday()
    
# # # # #     # Calculate Monday of this week
# # # # #     week_start = meeting_date - timedelta(days=day_of_week)
    
# # # # #     # Calculate Sunday of this week
# # # # #     week_end = week_start + timedelta(days=6)
    
# # # # #     # Deadline: Sunday 9am UTC
# # # # #     deadline = datetime.combine(week_end, time(9, 0, 0))
    
# # # # #     return week_start, week_end, deadline


# # # # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # # # ROUTES: HEALTH CHECK
# # # # # # ═══════════════════════════════════════════════════════════════════════════════

# # # # # @app.get("/health")
# # # # # async def health_check():
# # # # #     """Health check endpoint"""
# # # # #     return {
# # # # #         "status": "ok",
# # # # #         "message": "BLW Cell Reporting API is running",
# # # # #         "timestamp": datetime.utcnow().isoformat(),
# # # # #     }


# # # # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # # # ROUTES: AUTHENTICATION
# # # # # # ═══════════════════════════════════════════════════════════════════════════════

# # # # # @app.post("/api/auth/login", response_model=LoginResponse, tags=["Auth"])
# # # # # async def login(
# # # # #     request: LoginRequest,
# # # # #     session: AsyncSession = Depends(get_session)
# # # # # ):
# # # # #     """
# # # # #     Login with phone and PIN
    
# # # # #     Returns JWT token for subsequent requests
# # # # #     """
# # # # #     # Find user by phone
# # # # #     result = await session.execute(
# # # # #         select(User).where(User.phone == request.phone).where(User.is_active == True)
# # # # #     )
# # # # #     user = result.scalar_one_or_none()

# # # # #     if not user:
# # # # #         raise HTTPException(
# # # # #             status_code=status.HTTP_401_UNAUTHORIZED,
# # # # #             detail="Invalid phone or PIN",
# # # # #         )

# # # # #     # Verify PIN
# # # # #     if not verify_pin(request.pin, user.pin_hash):
# # # # #         raise HTTPException(
# # # # #             status_code=status.HTTP_401_UNAUTHORIZED,
# # # # #             detail="Invalid phone or PIN",
# # # # #         )

# # # # #     # Update last login
# # # # #     user.last_login = datetime.utcnow()
# # # # #     await session.commit()

# # # # #     # Create token
# # # # #     access_token = create_access_token(subject=str(user.id))

# # # # #     return LoginResponse(
# # # # #         access_token=access_token,
# # # # #         token_type="bearer",
# # # # #         user={
# # # # #             "id": str(user.id),
# # # # #             "phone": user.phone,
# # # # #             "name": user.name,
# # # # #             "role": user.role,
# # # # #             "cell_id": str(user.cell_id) if user.cell_id else None,
# # # # #             "senior_cell_id": str(user.senior_cell_id) if user.senior_cell_id else None,
# # # # #             "fellowship_id": str(user.fellowship_id) if user.fellowship_id else None,
# # # # #             "zone_id": str(user.zone_id) if user.zone_id else None,
# # # # #         }
# # # # #     )


# # # # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # # # ROUTES: ADMIN - CREATE USERS
# # # # # # ═══════════════════════════════════════════════════════════════════════════════

# # # # # @app.post("/api/admin/users", response_model=UserCreateResponse, tags=["Admin"])
# # # # # async def create_user(
# # # # #     request: UserCreate,
# # # # #     session: AsyncSession = Depends(get_session),
# # # # #     current_user: User = Depends(get_current_user),
# # # # # ):
# # # # #     """
# # # # #     Create new user (Admin only)
    
# # # # #     System admin can create cell leaders, senior cell leaders, pastors, etc.
# # # # #     """
# # # # #     # Check if requester is system admin
# # # # #     if current_user.role != "system_admin":
# # # # #         raise HTTPException(
# # # # #             status_code=status.HTTP_403_FORBIDDEN,
# # # # #             detail="Only system admin can create users",
# # # # #         )

# # # # #     # Check if phone already exists
# # # # #     result = await session.execute(
# # # # #         select(User).where(User.phone == request.phone)
# # # # #     )
# # # # #     if result.scalar_one_or_none():
# # # # #         raise HTTPException(
# # # # #             status_code=status.HTTP_400_BAD_REQUEST,
# # # # #             detail="Phone number already exists",
# # # # #         )

# # # # #     # Create new user with default PIN
# # # # #     new_user = User(
# # # # #         phone=request.phone,
# # # # #         name=request.name,
# # # # #         pin_hash=hash_default_pin(),
# # # # #         role=request.role,
# # # # #         cell_id=request.cell_id,
# # # # #         senior_cell_id=request.senior_cell_id,
# # # # #         fellowship_id=request.fellowship_id,
# # # # #         zone_id=request.zone_id,
# # # # #         is_active=True,
# # # # #     )

# # # # #     session.add(new_user)
# # # # #     await session.commit()
# # # # #     await session.refresh(new_user)

# # # # #     return UserCreateResponse(
# # # # #         user_id=new_user.id,
# # # # #         phone=new_user.phone,
# # # # #         name=new_user.name,
# # # # #         role=new_user.role,
# # # # #         initial_pin="123456",
# # # # #         message="User created. Share phone and PIN with leader.",
# # # # #     )


# # # # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # # # ROUTES: CELL REPORTS
# # # # # # ═══════════════════════════════════════════════════════════════════════════════

# # # # # @app.post("/api/reports/submit", response_model=CellReportResponse, tags=["Reports"])
# # # # # async def submit_report(
# # # # #     request: CellReportSubmit,
# # # # #     session: AsyncSession = Depends(get_session),
# # # # #     current_user: User = Depends(get_current_user),
# # # # # ):
# # # # #     """
# # # # #     Submit a cell report
    
# # # # #     - Validates all required fields
# # # # #     - Calculates deadline (Sunday 9am)
# # # # #     - Determines status (SUBMITTED or LATE)
# # # # #     - Checks for duplicates (only one report per cell per week)
# # # # #     """
# # # # #     # Verify user has access to this cell
# # # # #     if current_user.cell_id != request.cell_id and current_user.role == "cell_leader":
# # # # #         raise HTTPException(
# # # # #             status_code=status.HTTP_403_FORBIDDEN,
# # # # #             detail="You can only submit reports for your own cell",
# # # # #         )

# # # # #     # Get cell info
# # # # #     result = await session.execute(
# # # # #         select(Cell).where(Cell.id == request.cell_id)
# # # # #     )
# # # # #     cell = result.scalar_one_or_none()
# # # # #     if not cell:
# # # # #         raise HTTPException(
# # # # #             status_code=status.HTTP_404_NOT_FOUND,
# # # # #             detail="Cell not found",
# # # # #         )

# # # # #     # Check for duplicate report (only one per week)
# # # # #     result = await session.execute(
# # # # #         select(CellReport).where(
# # # # #             (CellReport.cell_id == request.cell_id) &
# # # # #             (CellReport.week_start_date == request.week_start_date)
# # # # #         )
# # # # #     )
# # # # #     if result.scalar_one_or_none():
# # # # #         raise HTTPException(
# # # # #             status_code=status.HTTP_409_CONFLICT,
# # # # #             detail=f"Report already exists for week of {request.week_start_date}",
# # # # #         )

# # # # #     # Calculate deadline
# # # # #     week_start, week_end, deadline = calculate_week_boundaries(request.meeting_date)

# # # # #     # Determine status
# # # # #     now = datetime.utcnow()
# # # # #     status_value = "SUBMITTED" if now <= deadline else "LATE"

# # # # #     # Calculate finance total
# # # # #     finance_total = (
# # # # #         request.finance_oblation +
# # # # #         request.finance_offerings +
# # # # #         request.finance_tithes +
# # # # #         request.finance_thanksgiving +
# # # # #         request.finance_seed +
# # # # #         request.finance_partnership +
# # # # #         request.finance_first_fruits
# # # # #     )

# # # # #     # Create report
# # # # #     cell_report = CellReport(
# # # # #         cell_id=request.cell_id,
# # # # #         submitted_by=current_user.id,
# # # # #         meeting_date=request.meeting_date,
# # # # #         week_start_date=request.week_start_date,
# # # # #         week_end_date=request.week_end_date,
# # # # #         actual_meeting_day=request.actual_meeting_day,
# # # # #         submission_deadline=deadline,
# # # # #         status=status_value,
# # # # #         submitted_at=now,
# # # # #         synced_from_offline=False,
        
# # # # #         # Meeting details
# # # # #         meeting_week=request.meeting_week,
# # # # #         meeting_type=request.meeting_type,
# # # # #         meeting_duration=request.meeting_duration,
# # # # #         bible_class_teachers=[t for t in request.bible_class_teachers if t],
# # # # #         activities=[a.dict() for a in request.activities],
        
# # # # #         # Attendance
# # # # #         first_timers=request.first_timers,
# # # # #         number_saved=request.number_saved,
# # # # #         filled_holy_ghost=request.filled_holy_ghost,
# # # # #         total_attendance=request.total_attendance,
# # # # #         new_members=request.new_members,
# # # # #         souls_retained=request.souls_retained,
# # # # #         souls_won=request.souls_won,
# # # # #         souls_on_tracker=request.souls_on_tracker,
        
# # # # #         # Finances
# # # # #         finance_oblation=request.finance_oblation,
# # # # #         finance_offerings=request.finance_offerings,
# # # # #         finance_tithes=request.finance_tithes,
# # # # #         finance_thanksgiving=request.finance_thanksgiving,
# # # # #         finance_seed=request.finance_seed,
# # # # #         finance_partnership=request.finance_partnership,
# # # # #         finance_first_fruits=request.finance_first_fruits,
# # # # #         finance_total=finance_total,
# # # # #         finance_collected_by=request.finance_collected_by,
        
# # # # #         # Text
# # # # #         testimonies=request.testimonies,
# # # # #         monthly_plans=request.monthly_plans,
# # # # #         challenges=request.challenges,
        
# # # # #         # Soul winning
# # # # #         soul_winning_records=[r.dict() for r in request.soul_winning_records],
        
# # # # #         # Optional
# # # # #         pastors_remarks=request.pastors_remarks,
# # # # #         other_info=request.other_info,
# # # # #         photo_urls=request.photo_urls,
# # # # #     )

# # # # #     session.add(cell_report)
# # # # #     await session.commit()
# # # # #     await session.refresh(cell_report)

# # # # #     return CellReportResponse(
# # # # #         id=cell_report.id,
# # # # #         cell_id=cell_report.cell_id,
# # # # #         status=cell_report.status,
# # # # #         submitted_at=cell_report.submitted_at,
# # # # #         submission_deadline=cell_report.submission_deadline,
# # # # #         message=f"Report submitted {'on time' if status_value == 'SUBMITTED' else 'late'}! Deadline was {deadline.strftime('%A %I:%M %p')}",
# # # # #     )


# # # # # @app.get("/api/reports/{report_id}", tags=["Reports"])
# # # # # async def get_report(
# # # # #     report_id: UUID,
# # # # #     session: AsyncSession = Depends(get_session),
# # # # #     current_user: User = Depends(get_current_user),
# # # # # ):
# # # # #     """Get a single report"""
# # # # #     result = await session.execute(
# # # # #         select(CellReport).where(CellReport.id == report_id)
# # # # #     )
# # # # #     report = result.scalar_one_or_none()

# # # # #     if not report:
# # # # #         raise HTTPException(
# # # # #             status_code=status.HTTP_404_NOT_FOUND,
# # # # #             detail="Report not found",
# # # # #         )

# # # # #     # Check access (only cell leader, senior CL, or pastors can view)
# # # # #     if (
# # # # #         report.submitted_by != current_user.id and
# # # # #         current_user.cell_id != report.cell_id and
# # # # #         current_user.role not in ["senior_cell_leader", "fellowship_pastor", "zonal_pastor", "zonal_admin", "system_admin"]
# # # # #     ):
# # # # #         raise HTTPException(
# # # # #             status_code=status.HTTP_403_FORBIDDEN,
# # # # #             detail="You don't have access to this report",
# # # # #         )

# # # # #     return report


# # # # # # ═══════════════════════════════════════════════════════════════════════════════
# # # # # # ROOT
# # # # # # ═══════════════════════════════════════════════════════════════════════════════

# # # # # @app.get("/")
# # # # # async def root():
# # # # #     """Root endpoint"""
# # # # #     return {
# # # # #         "message": "BLW Cell Reporting API",
# # # # #         "version": "1.0.0",
# # # # #         "docs": "/docs",
# # # # #     }