# Cellytics Backend Documentation

## Table of Contents

1. [Overview](#overview)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Core Architecture](#core-architecture)
5. [Data Models](#data-models)
6. [API Endpoints](#api-endpoints)
7. [Authentication](#authentication)
8. [Database](#database)
9. [Services Layer](#services-layer)
10. [Deployment](#deployment)

---

## Overview

**CellTrack** (also called **BLW Cell Reporting System** or **Cellytics**) is a mobile-first REST API built with FastAPI for managing cell-based church organizational structures. The system enables:

- Multi-level hierarchical organization (Regions → Zones → Fellowships → Senior Cells → Cells)
- User role-based access control (System Admin, Zonal Pastor, Zonal Admin, Fellowship Pastor, Senior Cell Leader, Cell Leader)
- Cell meeting reporting and tracking
- Analytics and dashboards for leadership
- Push notifications via Firebase Cloud Messaging
- Secure authentication with JWT tokens

---

## Tech Stack

### Backend Framework & ORM

- **FastAPI** (v0.103.2) - Modern async web framework
- **SQLAlchemy** (v2.0.23) - SQL toolkit and ORM
- **Uvicorn** (v0.24.0) - ASGI server

### Database

- **PostgreSQL** (via asyncpg v0.29.0)
- **Neon.tech** - Serverless PostgreSQL (production)

### Authentication & Security

- **PyJWT** (v2.8.0) - JWT token creation and verification
- **Passlib + Bcrypt** - Password/PIN hashing
- **Python-Jose** (v3.3.0) - JOSE cryptography

### Utilities

- **Pydantic** (v2.5.3) - Data validation
- **Python-Dotenv** - Environment configuration
- **HTTPX** (v0.25.2) - Async HTTP client
- **Python-Multipart** (v0.0.6) - File upload support

---

## Project Structure

```
celltrack_backend/
├── main.py                 # Application entry point
├── auth.py                 # Authentication & JWT token management
├── database.py             # Database connection & session management
├── models.py               # SQLAlchemy ORM models
├── schemas.py              # Pydantic request/response schemas
├── fcm_service.py          # Firebase Cloud Messaging service
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker containerization
│
├── routers/                # API route handlers
│   ├── __init__.py
│   ├── auth.py            # Login endpoint
│   ├── admin.py           # Zone, Fellowship, Cell management
│   ├── dashboards.py      # Analytics & dashboard data
│   ├── reports.py         # Cell report submission & retrieval
│   ├── notifications.py   # Notification management
│   └── uploads.py         # File upload handling
│
├── services/               # Business logic layer
│   ├── __init__.py
│   ├── admin_service.py   # Admin operations
│   ├── dashboard_service.py # Dashboard analytics
│   └── report_service.py   # Report processing
│
└── utils/                  # Utility functions
    ├── __init__.py
    ├── helpers.py         # General helpers
    └── security.py        # Permission checks & security utilities
```

---

## Core Architecture

### Clean Architecture Pattern

The codebase follows a **clean architecture** approach:

```
Routes (API Layer)
    ↓
Services (Business Logic)
    ↓
Models (Data Layer)
    ↓
Database (Persistence)
```

### Request Flow

1. **API Route** (`routers/`) - Receives HTTP request, validates input
2. **Authentication** - JWT token verification via `get_current_user()`
3. **Authorization** - Role-based access control via security utils
4. **Service Layer** - Business logic execution
5. **Database** - SQL operations via SQLAlchemy
6. **Response** - Serialized Pydantic model

---

## Data Models

### Organizational Hierarchy

The system implements a 5-level hierarchical structure:

#### 1. **Region**

```
Represents a geographic region
- id (UUID, primary key)
- name (string, unique)
- description (text, optional)
- created_at (datetime)
```

#### 2. **Zone**

```
Subdivisions within a region
- id (UUID, primary key)
- name (string)
- region_id (FK → Region)
- zonal_pastor_id (FK → User)
- zonal_admin_id (FK → User)
- location (string)
- created_at (datetime)
```

#### 3. **Fellowship**

```
Subdivisions within a zone
- id (UUID, primary key)
- name (string)
- zone_id (FK → Zone)
- pastor_id (FK → User)
- location (string)
- created_at (datetime)
```

#### 4. **SeniorCell**

```
Groups within a fellowship (led by a senior cell leader)
- id (UUID, primary key)
- name (string)
- fellowship_id (FK → Fellowship)
- leader_id (FK → User)
- leader_name (string)
- created_at (datetime)
```

#### 5. **Cell**

```
Basic unit (usually 5-10 members, meets weekly)
- id (UUID, primary key)
- name (string)
- senior_cell_id (FK → SeniorCell)
- leader_id (FK → User)
- leader_name (string)
- default_meeting_day (enum: monday-sunday)
- actual_meeting_day (string, for rescheduling)
- meeting_time (time, optional)
- is_active (boolean)
- created_at (datetime)
```

### User Model

```
class User:
    id (UUID, primary key)
    phone (string, unique)
    name (string)
    pin_hash (string)  # 6-digit PIN hashed with bcrypt
    role (enum: system_admin, zonal_pastor, zonal_admin,
                fellowship_pastor, senior_cell_leader, cell_leader)

    # Foreign keys (based on assigned role)
    zone_id (FK → Zone)
    fellowship_id (FK → Fellowship)
    senior_cell_id (FK → SeniorCell)
    cell_id (FK → Cell)

    is_active (boolean)
    last_login (datetime)
    created_at (datetime)
```

### Cell Report Model

```
class CellReport:
    id (UUID, primary key)
    cell_id (FK → Cell)
    submitted_by (FK → User)

    # Attendance
    attendance_count (integer)
    new_members_count (integer)

    # Activities
    praise_worship (boolean)
    word_study (boolean)
    prayer (boolean)
    tithes_given (decimal)
    offerings_given (decimal)
    special_offerings (decimal)

    # Status
    status (enum: draft, submitted, late, overdue)
    submitted_at (datetime)
    report_date (date)

    created_at (datetime)
```

---

## API Endpoints

### Authentication

#### Login

```
POST /auth/login
Request:
  {
    "phone": "+237690000000",
    "pin": "123456"
  }

Response (200):
  {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer",
    "user": {
      "id": "uuid",
      "phone": "+237690000000",
      "name": "John Doe",
      "role": "cell_leader",
      "cell_id": "uuid",
      "senior_cell_id": "uuid",
      "fellowship_id": "uuid",
      "zone_id": "uuid",
      "is_active": true
    }
  }

Error (401): Invalid phone or PIN
```

### Health Check

#### Root / Status

```
GET /
Response: { "message": "BLW Cell Reporting API", "version": "1.0.0", "status": "running" }

GET /health
Response: { "status": "ok", "timestamp": "2026-05-15T10:30:00Z" }
```

### Admin Endpoints (Zones, Fellowships, Cells)

#### Zone Management

```
POST /admin/zones
  - Create new zone (System Admin only)
  - Request: { name, location, description }

GET /admin/zones
  - List zones (with optional filtering)

GET /admin/zones/{zone_id}
  - Get zone details

PUT /admin/zones/{zone_id}
  - Update zone (System Admin only)

DELETE /admin/zones/{zone_id}
  - Delete zone (System Admin only)
```

#### Fellowship Management

```
POST /admin/fellowships
  - Create fellowship within a zone (Zonal Admin+)
  - Request: { name, location, zone_id }

GET /admin/fellowships
  - List fellowships

GET /admin/fellowships/{fellowship_id}
  - Get fellowship details

PUT /admin/fellowships/{fellowship_id}
  - Update fellowship

DELETE /admin/fellowships/{fellowship_id}
  - Delete fellowship
```

#### Cell Management

```
POST /admin/cells
  - Create cell within senior cell (Senior Cell Leader+)
  - Request: { name, senior_cell_id, default_meeting_day, meeting_time }

GET /admin/cells
  - List cells

GET /admin/cells/{cell_id}
  - Get cell details

PUT /admin/cells/{cell_id}
  - Update cell (meeting day, time, status)

DELETE /admin/cells/{cell_id}
  - Delete cell (soft/hard delete based on implementation)
```

#### User Management

```
POST /admin/users
  - Create user (role-based)
  - Request: { phone, name, role, cell_id, zone_id, ... }

GET /admin/users
  - List users (with role filtering)

GET /admin/users/{user_id}
  - Get user details

PUT /admin/users/{user_id}
  - Update user details or role

DELETE /admin/users/{user_id}
  - Deactivate/delete user
```

### Reports Endpoints

#### Submit Cell Report

```
POST /reports/submit
  - Cell leader submits weekly cell report
  - Auth Required: Bearer token (cell leader+)
  - Request:
    {
      "cell_id": "uuid",
      "attendance_count": 7,
      "new_members_count": 1,
      "praise_worship": true,
      "word_study": true,
      "prayer": true,
      "tithes_given": 50000,
      "offerings_given": 30000,
      "special_offerings": 0
    }

Response (201): { "id": "uuid", "status": "submitted", "submitted_at": "..." }
```

#### Get Reports

```
GET /reports
  - Get all reports for current user's scope
  - Query params: status, date_from, date_to, cell_id

GET /reports/{report_id}
  - Get specific report details

GET /reports/cell/{cell_id}
  - Get all reports for a specific cell
```

#### Update Report

```
PUT /reports/{report_id}
  - Update draft report before deadline

DELETE /reports/{report_id}
  - Delete report (draft only)
```

### Dashboards Endpoints

#### Analytics & Overview

```
GET /dashboards/overview
  - Summary stats for current user's scope
  - Returns: total_cells, total_members, avg_attendance, etc.

GET /dashboards/cell/{cell_id}
  - Detailed cell metrics and recent reports

GET /dashboards/zone/{zone_id}
  - Zone-level analytics (all fellowships, cells, members)

GET /dashboards/fellowship/{fellowship_id}
  - Fellowship-level analytics

GET /dashboards/trends
  - Time-series data for attendance, giving, etc.
```

### Notifications Endpoints

```
POST /notifications/register
  - Register device for push notifications
  - Request: { device_token, device_type }

GET /notifications
  - List notifications for current user

POST /notifications/{notification_id}/read
  - Mark notification as read

GET /notifications/settings
  - Get notification preferences

PUT /notifications/settings
  - Update notification preferences
```

### Uploads Endpoints

```
POST /uploads/report-attachment
  - Upload file attachment for cell report
  - Form data: file, report_id

POST /uploads/member-photo
  - Upload member photo
  - Form data: file, member_id
```

---

## Authentication

### JWT Token System

**Token Structure:**

```python
{
    "sub": "user_id",          # Subject (user UUID)
    "exp": 1716432000,         # Expiration (30 days from issue)
    "iat": 1713840000          # Issued at
}
```

**Configuration:**

- Algorithm: HS256
- Secret: `JWT_SECRET_KEY` environment variable
- Expiration: 30 days

### PIN Authentication

- Uses **bcrypt** with 12 rounds for hashing
- 6-digit numeric PIN stored securely
- Default PIN for new users (set during user creation)

### Authorization Levels

```
Role Hierarchy (top to bottom):
1. system_admin        → All access
2. zonal_pastor        → Zone & below operations
3. zonal_admin         → Zone & below operations
4. fellowship_pastor   → Fellowship & below operations
5. senior_cell_leader  → Senior cell & cell operations
6. cell_leader         → Cell operations only
```

**Implementation:**

```python
# From utils/security.py
def require_system_admin(user: User): ...
def require_zonal_admin_or_above(user: User): ...
def require_fellowship_pastor_or_above(user: User): ...

# Scoped queries filter results by user permissions
async def scoped_zone_query(user: User): ...
async def scoped_fellowship_query(user: User): ...
async def scoped_cell_query(user: User): ...
```

---

## Database

### Connection

- **Driver:** asyncpg (async PostgreSQL)
- **ORM:** SQLAlchemy 2.0 (async-compatible)
- **Connection Pool:** NullPool (for serverless compatibility)
- **SSL:** Required for Neon.tech connections

**Configuration:**

```python
# database.py
DATABASE_URL = os.getenv("DATABASE_URL")
# Automatically converted to: postgresql+asyncpg://...

# SSL context with certificate verification disabled
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
```

### Session Management

```python
# Dependency injection pattern
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# Usage in route handlers
@router.get("/example")
async def example(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(...))
```

### Migrations

Migrations are managed via SQL schema files (not Alembic). Tables are created in PostgreSQL directly.

### Tables

| Table              | Purpose                   |
| ------------------ | ------------------------- |
| `regions`          | Geographic regions        |
| `zones`            | Zone subdivisions         |
| `fellowships`      | Fellowship groups         |
| `senior_cells`     | Senior cell groups        |
| `cells`            | Individual cell units     |
| `users`            | User accounts & roles     |
| `cell_reports`     | Weekly cell reports       |
| `notifications`    | Notification records      |
| `pin_reset_tokens` | PIN reset security tokens |

---

## Services Layer

### AdminService (`services/admin_service.py`)

Handles administrative operations:

- Zone CRUD
- Fellowship CRUD
- Senior Cell CRUD
- Cell CRUD
- User creation and role assignment
- Hierarchical validation (e.g., cannot create fellowship in deleted zone)

### DashboardService (`services/dashboard_service.py`)

Generates analytics data:

- Cell-level metrics (attendance, giving)
- Fellowship summaries
- Zone overviews
- Trend analysis
- Scope-aware queries (user sees only data in their hierarchy)

### ReportService (`services/report_service.py`)

Manages cell reports:

- Report submission validation
- Status tracking (draft → submitted → late → overdue)
- Report deadline enforcement
- Financial summaries
- Attendance analytics

### FCMService (`fcm_service.py`)

Firebase Cloud Messaging integration:

- Device token registration
- Push notification sending
- Topic-based messaging (e.g., all cell leaders in a zone)

---

## Error Handling

### Standard HTTP Status Codes

```
200 OK              - Successful request
201 Created         - Resource created
400 Bad Request     - Invalid input
401 Unauthorized    - Authentication failed
403 Forbidden       - Insufficient permissions
404 Not Found       - Resource not found
409 Conflict        - Unique constraint violation
500 Internal Error  - Server error
```

### Example Error Response

```json
{
  "detail": "You do not have permission to access this resource"
}
```

---

## Deployment

### Docker

**Dockerfile** provided for containerization:

```dockerfile
# Includes Python 3.10+, dependencies, and uvicorn startup
```

**Build & Run:**

```bash
docker build -t celltrack-api .
docker run -e DATABASE_URL=... -p 8000:8000 celltrack-api
```

### Environment Variables

```
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
JWT_SECRET_KEY=your-super-secret-key-change-in-production
FCM_CREDENTIALS_JSON=path/to/firebase-credentials.json
API_ENVIRONMENT=production|development|testing
```

### Production Considerations

1. **Database:** Use Neon.tech or managed PostgreSQL
2. **JWT Secret:** Set strong random string in `.env`
3. **CORS:** Configure allowed origins for frontend
4. **SSL/TLS:** Enable HTTPS on deployed instance
5. **Logging:** Centralize logs (e.g., DataDog, CloudWatch)
6. **Rate Limiting:** Implement per IP/user request limiting
7. **Monitoring:** Health checks and alerting

---

## Development Workflow

### Local Setup

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file
cp .env.example .env
# Edit with local DATABASE_URL and JWT_SECRET_KEY

# 4. Run application
uvicorn main:app --reload

# 5. Access API docs
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

### Database Setup

```bash
# Create database
createdb celltrack

# Run migrations (if using Alembic)
alembic upgrade head

# Or seed with initial data
python seed_database.py
```

### Testing

```bash
# Run tests with pytest
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

---

## Future Enhancements

- [ ] Real-time notifications via WebSockets
- [ ] SMS reminders for report deadlines
- [ ] Export reports to PDF/Excel
- [ ] Offline mode sync for mobile app
- [ ] Multi-language support (localization)
- [ ] Advanced analytics & predictive metrics
- [ ] Integration with accounting software
- [ ] API rate limiting & quotas

---

## Contact & Support

For backend modifications or issues:

1. Check error logs: `VSCODE_TARGET_SESSION_LOG`
2. Review test coverage before deployment
3. Update API documentation after schema changes
