# main.py - FastAPI Application

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, date
from uuid import UUID
import logging

from database import get_session, init_db, close_db
from models import User, Cell, CellReport, Zone, Fellowship
from schemas import (
    LoginRequest, LoginResponse, UserCreate, UserCreateResponse,
    CellReportSubmit, CellReportResponse, ErrorResponse
)
from auth import hash_pin, verify_pin, create_access_token, decode_token, hash_default_pin

# ═══════════════════════════════════════════════════════════════════════════════
# SETUP
# ═══════════════════════════════════════════════════════════════════════════════

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="BLW Cell Reporting System",
    description="API for cell report submission and dashboards",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════════════════════
# STARTUP / SHUTDOWN
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup():
    logger.info("🚀 FastAPI starting up...")
    # Database is already initialized via schema.sql
    # This is just for logging


@app.on_event("shutdown")
async def shutdown():
    logger.info("🛑 FastAPI shutting down...")
    await close_db()

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def get_current_user(
    token: str = None,
    session: AsyncSession = Depends(get_session)
) -> User:
    """Get current authenticated user"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided",
        )

    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    result = await session.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


def calculate_week_boundaries(meeting_date: date) -> tuple:
    """Calculate week start (Monday), end (Sunday), and deadline (Sunday 9am)"""
    from datetime import datetime, time, timedelta

    # Get the day of week (0=Monday, 6=Sunday)
    day_of_week = meeting_date.weekday()

    # Calculate Monday of this week
    week_start = meeting_date - timedelta(days=day_of_week)

    # Calculate Sunday of this week
    week_end = week_start + timedelta(days=6)

    # Deadline: Sunday 9am UTC
    deadline = datetime.combine(week_end, time(9, 0, 0))

    return week_start, week_end, deadline


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTES: HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health_check():
    """Health check endpoint"""
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
    """
    Login with phone and PIN

    Returns JWT token for subsequent requests
    """
    try:
        # Find user by phone
        result = await session.execute(
            select(User).where(User.phone == request.phone).where(User.is_active == True)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid phone or PIN",
            )

        # Verify PIN
        if not verify_pin(request.pin, user.pin_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid phone or PIN",
            )

        # Update last login
        user.last_login = datetime.utcnow()
        await session.commit()

        # Create token
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
            detail=f"Login failed: {str(e)}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTES: ADMIN - CREATE USERS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/admin/users", response_model=UserCreateResponse, tags=["Admin"])
async def create_user(
    request: UserCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Create new user (Admin only)

    System admin can create cell leaders, senior cell leaders, pastors, etc.
    """
    try:
        # Check if requester is system admin
        if current_user.role != "system_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only system admin can create users",
            )

        # Check if phone already exists
        result = await session.execute(
            select(User).where(User.phone == request.phone)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already exists",
            )

        # Create new user with default PIN
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
# ROUTES: CELL REPORTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/reports/submit", response_model=CellReportResponse, tags=["Reports"])
async def submit_report(
    request: CellReportSubmit,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Submit a cell report

    - Validates all required fields
    - Calculates deadline (Sunday 9am)
    - Determines status (SUBMITTED or LATE)
    - Checks for duplicates (only one report per cell per week)
    """
    try:
        # Verify user has access to this cell
        if current_user.cell_id != request.cell_id and current_user.role == "cell_leader":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only submit reports for your own cell",
            )

        # Get cell info
        result = await session.execute(
            select(Cell).where(Cell.id == request.cell_id)
        )
        cell = result.scalar_one_or_none()
        if not cell:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cell not found",
            )

        # Check for duplicate report (only one per week)
        result = await session.execute(
            select(CellReport).where(
                (CellReport.cell_id == request.cell_id) &
                (CellReport.week_start_date == request.week_start_date)
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Report already exists for week of {request.week_start_date}",
            )

        # Calculate deadline
        week_start, week_end, deadline = calculate_week_boundaries(request.meeting_date)

        # Determine status
        now = datetime.utcnow()
        status_value = "SUBMITTED" if now <= deadline else "LATE"

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
            submitted_by=current_user.id,
            meeting_date=request.meeting_date,
            week_start_date=request.week_start_date,
            week_end_date=request.week_end_date,
            actual_meeting_day=request.actual_meeting_day,
            submission_deadline=deadline,
            status=status_value,
            submitted_at=now,
            synced_from_offline=False,

            # Meeting details
            meeting_week=request.meeting_week,
            meeting_type=request.meeting_type,
            meeting_duration=request.meeting_duration,
            bible_class_teachers=[t for t in request.bible_class_teachers if t],
            activities=[a.dict() for a in request.activities],

            # Attendance
            first_timers=request.first_timers,
            number_saved=request.number_saved,
            filled_holy_ghost=request.filled_holy_ghost,
            total_attendance=request.total_attendance,
            new_members=request.new_members,
            souls_retained=request.souls_retained,
            souls_won=request.souls_won,
            souls_on_tracker=request.souls_on_tracker,

            # Finances
            finance_oblation=request.finance_oblation,
            finance_offerings=request.finance_offerings,
            finance_tithes=request.finance_tithes,
            finance_thanksgiving=request.finance_thanksgiving,
            finance_seed=request.finance_seed,
            finance_partnership=request.finance_partnership,
            finance_first_fruits=request.finance_first_fruits,
            finance_total=finance_total,
            finance_collected_by=request.finance_collected_by,

            # Text
            testimonies=request.testimonies,
            monthly_plans=request.monthly_plans,
            challenges=request.challenges,

            # Soul winning
            soul_winning_records=[r.dict() for r in request.soul_winning_records],

            # Optional
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
            message=f"Report submitted {'on time' if status_value == 'SUBMITTED' else 'late'}! Deadline was {deadline.strftime('%A %I:%M %p')}",
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
    """Get a single report"""
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

        # Check access (only cell leader, senior CL, or pastors can view)
        if (
            report.submitted_by != current_user.id and
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


# ═══════════════════════════════════════════════════════════════════════════════
# ROOT
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "BLW Cell Reporting API",
        "version": "1.0.0",
        "docs": "/docs",
    }












# # main.py - FastAPI Application

# from fastapi import FastAPI, Depends, HTTPException, status
# from fastapi.middleware.cors import CORSMiddleware
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select
# from datetime import datetime, date
# from uuid import UUID
# import logging

# from database import get_session, init_db, close_db
# from models import User, Cell, CellReport, Zone, Fellowship
# from schemas import (
#     LoginRequest, LoginResponse, UserCreate, UserCreateResponse,
#     CellReportSubmit, CellReportResponse, ErrorResponse
# )
# from auth import hash_pin, verify_pin, create_access_token, decode_token, hash_default_pin

# # ═══════════════════════════════════════════════════════════════════════════════
# # SETUP
# # ═══════════════════════════════════════════════════════════════════════════════

# # Logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # FastAPI app
# app = FastAPI(
#     title="BLW Cell Reporting System",
#     description="API for cell report submission and dashboards",
#     version="1.0.0",
# )

# # CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ═══════════════════════════════════════════════════════════════════════════════
# # STARTUP / SHUTDOWN
# # ═══════════════════════════════════════════════════════════════════════════════

# @app.on_event("startup")
# async def startup():
#     logger.info("🚀 FastAPI starting up...")
#     # Database is already initialized via schema.sql
#     # This is just for logging


# @app.on_event("shutdown")
# async def shutdown():
#     logger.info("🛑 FastAPI shutting down...")
#     await close_db()

# # ═══════════════════════════════════════════════════════════════════════════════
# # HELPER FUNCTIONS
# # ═══════════════════════════════════════════════════════════════════════════════

# async def get_current_user(
#     token: str = None,
#     session: AsyncSession = Depends(get_session)
# ) -> User:
#     """Get current authenticated user"""
#     if not token:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="No token provided",
#         )

#     user_id = decode_token(token)
#     if not user_id:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid or expired token",
#         )

#     result = await session.execute(
#         select(User).where(User.id == UUID(user_id))
#     )
#     user = result.scalar_one_or_none()

#     if not user or not user.is_active:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="User not found or inactive",
#         )

#     return user


# def calculate_week_boundaries(meeting_date: date) -> tuple:
#     """Calculate week start (Monday), end (Sunday), and deadline (Sunday 9am)"""
#     from datetime import datetime, time, timedelta
    
#     # Get the day of week (0=Monday, 6=Sunday)
#     day_of_week = meeting_date.weekday()
    
#     # Calculate Monday of this week
#     week_start = meeting_date - timedelta(days=day_of_week)
    
#     # Calculate Sunday of this week
#     week_end = week_start + timedelta(days=6)
    
#     # Deadline: Sunday 9am UTC
#     deadline = datetime.combine(week_end, time(9, 0, 0))
    
#     return week_start, week_end, deadline


# # ═══════════════════════════════════════════════════════════════════════════════
# # ROUTES: HEALTH CHECK
# # ═══════════════════════════════════════════════════════════════════════════════

# @app.get("/health")
# async def health_check():
#     """Health check endpoint"""
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
#     Login with phone and PIN
    
#     Returns JWT token for subsequent requests
#     """
#     # Find user by phone
#     result = await session.execute(
#         select(User).where(User.phone == request.phone).where(User.is_active == True)
#     )
#     user = result.scalar_one_or_none()

#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid phone or PIN",
#         )

#     # Verify PIN
#     if not verify_pin(request.pin, user.pin_hash):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid phone or PIN",
#         )

#     # Update last login
#     user.last_login = datetime.utcnow()
#     await session.commit()

#     # Create token
#     access_token = create_access_token(subject=str(user.id))

#     return LoginResponse(
#         access_token=access_token,
#         token_type="bearer",
#         user={
#             "id": str(user.id),
#             "phone": user.phone,
#             "name": user.name,
#             "role": user.role,
#             "cell_id": str(user.cell_id) if user.cell_id else None,
#             "senior_cell_id": str(user.senior_cell_id) if user.senior_cell_id else None,
#             "fellowship_id": str(user.fellowship_id) if user.fellowship_id else None,
#             "zone_id": str(user.zone_id) if user.zone_id else None,
#         }
#     )


# # ═══════════════════════════════════════════════════════════════════════════════
# # ROUTES: ADMIN - CREATE USERS
# # ═══════════════════════════════════════════════════════════════════════════════

# @app.post("/api/admin/users", response_model=UserCreateResponse, tags=["Admin"])
# async def create_user(
#     request: UserCreate,
#     session: AsyncSession = Depends(get_session),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Create new user (Admin only)
    
#     System admin can create cell leaders, senior cell leaders, pastors, etc.
#     """
#     # Check if requester is system admin
#     if current_user.role != "system_admin":
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Only system admin can create users",
#         )

#     # Check if phone already exists
#     result = await session.execute(
#         select(User).where(User.phone == request.phone)
#     )
#     if result.scalar_one_or_none():
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Phone number already exists",
#         )

#     # Create new user with default PIN
#     new_user = User(
#         phone=request.phone,
#         name=request.name,
#         pin_hash=hash_default_pin(),
#         role=request.role,
#         cell_id=request.cell_id,
#         senior_cell_id=request.senior_cell_id,
#         fellowship_id=request.fellowship_id,
#         zone_id=request.zone_id,
#         is_active=True,
#     )

#     session.add(new_user)
#     await session.commit()
#     await session.refresh(new_user)

#     return UserCreateResponse(
#         user_id=new_user.id,
#         phone=new_user.phone,
#         name=new_user.name,
#         role=new_user.role,
#         initial_pin="123456",
#         message="User created. Share phone and PIN with leader.",
#     )


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
#     Submit a cell report
    
#     - Validates all required fields
#     - Calculates deadline (Sunday 9am)
#     - Determines status (SUBMITTED or LATE)
#     - Checks for duplicates (only one report per cell per week)
#     """
#     # Verify user has access to this cell
#     if current_user.cell_id != request.cell_id and current_user.role == "cell_leader":
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="You can only submit reports for your own cell",
#         )

#     # Get cell info
#     result = await session.execute(
#         select(Cell).where(Cell.id == request.cell_id)
#     )
#     cell = result.scalar_one_or_none()
#     if not cell:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Cell not found",
#         )

#     # Check for duplicate report (only one per week)
#     result = await session.execute(
#         select(CellReport).where(
#             (CellReport.cell_id == request.cell_id) &
#             (CellReport.week_start_date == request.week_start_date)
#         )
#     )
#     if result.scalar_one_or_none():
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail=f"Report already exists for week of {request.week_start_date}",
#         )

#     # Calculate deadline
#     week_start, week_end, deadline = calculate_week_boundaries(request.meeting_date)

#     # Determine status
#     now = datetime.utcnow()
#     status_value = "SUBMITTED" if now <= deadline else "LATE"

#     # Calculate finance total
#     finance_total = (
#         request.finance_oblation +
#         request.finance_offerings +
#         request.finance_tithes +
#         request.finance_thanksgiving +
#         request.finance_seed +
#         request.finance_partnership +
#         request.finance_first_fruits
#     )

#     # Create report
#     cell_report = CellReport(
#         cell_id=request.cell_id,
#         submitted_by=current_user.id,
#         meeting_date=request.meeting_date,
#         week_start_date=request.week_start_date,
#         week_end_date=request.week_end_date,
#         actual_meeting_day=request.actual_meeting_day,
#         submission_deadline=deadline,
#         status=status_value,
#         submitted_at=now,
#         synced_from_offline=False,
        
#         # Meeting details
#         meeting_week=request.meeting_week,
#         meeting_type=request.meeting_type,
#         meeting_duration=request.meeting_duration,
#         bible_class_teachers=[t for t in request.bible_class_teachers if t],
#         activities=[a.dict() for a in request.activities],
        
#         # Attendance
#         first_timers=request.first_timers,
#         number_saved=request.number_saved,
#         filled_holy_ghost=request.filled_holy_ghost,
#         total_attendance=request.total_attendance,
#         new_members=request.new_members,
#         souls_retained=request.souls_retained,
#         souls_won=request.souls_won,
#         souls_on_tracker=request.souls_on_tracker,
        
#         # Finances
#         finance_oblation=request.finance_oblation,
#         finance_offerings=request.finance_offerings,
#         finance_tithes=request.finance_tithes,
#         finance_thanksgiving=request.finance_thanksgiving,
#         finance_seed=request.finance_seed,
#         finance_partnership=request.finance_partnership,
#         finance_first_fruits=request.finance_first_fruits,
#         finance_total=finance_total,
#         finance_collected_by=request.finance_collected_by,
        
#         # Text
#         testimonies=request.testimonies,
#         monthly_plans=request.monthly_plans,
#         challenges=request.challenges,
        
#         # Soul winning
#         soul_winning_records=[r.dict() for r in request.soul_winning_records],
        
#         # Optional
#         pastors_remarks=request.pastors_remarks,
#         other_info=request.other_info,
#         photo_urls=request.photo_urls,
#     )

#     session.add(cell_report)
#     await session.commit()
#     await session.refresh(cell_report)

#     return CellReportResponse(
#         id=cell_report.id,
#         cell_id=cell_report.cell_id,
#         status=cell_report.status,
#         submitted_at=cell_report.submitted_at,
#         submission_deadline=cell_report.submission_deadline,
#         message=f"Report submitted {'on time' if status_value == 'SUBMITTED' else 'late'}! Deadline was {deadline.strftime('%A %I:%M %p')}",
#     )


# @app.get("/api/reports/{report_id}", tags=["Reports"])
# async def get_report(
#     report_id: UUID,
#     session: AsyncSession = Depends(get_session),
#     current_user: User = Depends(get_current_user),
# ):
#     """Get a single report"""
#     result = await session.execute(
#         select(CellReport).where(CellReport.id == report_id)
#     )
#     report = result.scalar_one_or_none()

#     if not report:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Report not found",
#         )

#     # Check access (only cell leader, senior CL, or pastors can view)
#     if (
#         report.submitted_by != current_user.id and
#         current_user.cell_id != report.cell_id and
#         current_user.role not in ["senior_cell_leader", "fellowship_pastor", "zonal_pastor", "zonal_admin", "system_admin"]
#     ):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="You don't have access to this report",
#         )

#     return report


# # ═══════════════════════════════════════════════════════════════════════════════
# # ROOT
# # ═══════════════════════════════════════════════════════════════════════════════

# @app.get("/")
# async def root():
#     """Root endpoint"""
#     return {
#         "message": "BLW Cell Reporting API",
#         "version": "1.0.0",
#         "docs": "/docs",
#     }