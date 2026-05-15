# Cellytics System Architecture & Design Decisions

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Technology Choices](#technology-choices)
4. [Data Flow](#data-flow)
5. [Security Architecture](#security-architecture)
6. [Scalability & Performance](#scalability--performance)
7. [Deployment Architecture](#deployment-architecture)
8. [Design Decisions Rationale](#design-decisions-rationale)

---

## System Overview

### High-Level System Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Flutter Mobile Apps (iOS, Android) + Flutter Web        │   │
│  │ ┌──────────────────┐  ┌──────────────────┐             │   │
│  │ │ Cell Leaders     │  │ Leadership       │             │   │
│  │ │ - Submit Reports │  │ Dashboard        │             │   │
│  │ │ - View History   │  │ - Analytics      │             │   │
│  │ │ - Basic Stats    │  │ - Export Reports │             │   │
│  │ └──────────────────┘  └──────────────────┘             │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
                           ↓ HTTPS/REST API
┌────────────────────────────────────────────────────────────────┐
│                    INTEGRATION LAYER                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Offline-First Sync Engine                              │   │
│  │ - Detect network status (connectivity_plus)            │   │
│  │ - Queue reports when offline (Hive)                    │   │
│  │ - Auto-sync when online (background tasks)             │   │
│  │ - Conflict resolution (last-write-wins)                │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────────┐
│                   API LAYER (FastAPI Backend)                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Routes:                                                 │   │
│  │ - /auth/login                (Authentication)          │   │
│  │ - /admin/* (Zones, Cells, Users)   (Management)        │   │
│  │ - /reports/*                (Report CRUD)              │   │
│  │ - /dashboards/*             (Analytics)                │   │
│  │ - /notifications/*          (FCM)                      │   │
│  │ - /uploads/*                (Media)                    │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────────┐
│              BUSINESS LOGIC LAYER (Services)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ AdminService │  │ReportService │  │DashboardSvc. │         │
│  │ - CRUD ops   │  │ - Validate   │  │ - Aggregate  │         │
│  │ - Hierarchy  │  │ - Status mgmt│  │ - Filter     │         │
│  │ - Perms      │  │ - Sync queue │  │ - Export     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐                           │
│  │ FCMService   │  │SecurityUtils │                           │
│  │ - Push notif │  │ - JWT verify  │                           │
│  │ - Topics     │  │ - Role checks │                           │
│  └──────────────┘  └──────────────┘                           │
└────────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────────┐
│              DATA LAYER (SQLAlchemy ORM)                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Models:                                                 │   │
│  │ - Region, Zone, Fellowship, SeniorCell, Cell           │   │
│  │ - User (with roles), CellReport, Notification          │   │
│  │ - Relationships: FK, cascades, constraints             │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────────┐
│              PERSISTENCE LAYER                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ PostgreSQL Database (Neon.tech - Serverless)            │  │
│  │ - 8+ relational tables                                  │  │
│  │ - UUID primary keys                                    │  │
│  │ - Async connection pooling (asyncpg)                    │  │
│  │ - SSL/TLS encryption                                    │  │
│  │ - Automated backups                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ External Services:                                       │  │
│  │ - Firebase Cloud Messaging (Push notifications)         │  │
│  │ - Appwrite (File storage for attachments)               │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

---

## Architecture Patterns

### 1. **Clean Architecture** (3-Tier Separation)

The system strictly separates concerns:

```
┌──────────────────────────────────┐
│   PRESENTATION LAYER             │
│  - Routes (API endpoints)        │
│  - Request/response validation   │
│  - Error formatting              │
└──────────────────────────────────┘
            ↓ Depends on
┌──────────────────────────────────┐
│   BUSINESS LOGIC LAYER           │
│  - Services (admin, report, etc) │
│  - Domain rules                  │
│  - Data transformations          │
└──────────────────────────────────┘
            ↓ Depends on
┌──────────────────────────────────┐
│    DATA LAYER                    │
│  - ORM Models                    │
│  - Repository patterns           │
│  - Database queries              │
└──────────────────────────────────┘
```

**Benefits:**

- ✅ Easy to test (mock services)
- ✅ Low coupling (services don't know about routes)
- ✅ Easy to replace parts (swap DB, API framework)

### 2. **Repository Pattern** (Data Access)

Services never directly query the database. All data access goes through typed repositories:

```python
# Bad (tightly coupled):
user = await session.execute(select(User))

# Good (abstraction):
class UserRepository:
    async def get_by_id(self, id: UUID) -> User:
        ...
    async def get_by_phone(self, phone: str) -> User:
        ...

user = await user_repo.get_by_phone("+237...")
```

### 3. **Dependency Injection** (Backend)

All dependencies explicitly passed, never imported globally:

```python
# Route depends on service
@router.get("/reports")
async def get_reports(
    session: AsyncSession = Depends(get_session),      # DB
    current_user: User = Depends(get_current_user),    # Auth
    report_service: ReportService = Depends(...),      # Business logic
):
    ...
```

### 4. **Provider Pattern** (Frontend - Riverpod)

All state accessed through providers, never direct instantiation:

```dart
// Define provider
final authProvider = StateNotifierProvider((ref) => AuthNotifier());

// In widget
final auth = ref.watch(authProvider);  // Subscribe to state

// Update state
ref.read(authProvider.notifier).login(phone, pin);
```

---

## Technology Choices

### Backend: Why FastAPI + PostgreSQL?

| Choice             | Reason                                                             | Alternative                                   |
| ------------------ | ------------------------------------------------------------------ | --------------------------------------------- |
| **FastAPI**        | Async-first, built-in Swagger, automatic validation, modern Python | Django (heavier), Flask (less batteries)      |
| **SQLAlchemy 2.0** | Async ORM, relationship management, type hints                     | Raw SQL (error-prone), Tortoise (less mature) |
| **PostgreSQL**     | Relational (hierarchies), JSONB (flexible schemas), async support  | MySQL (no JSONB), MongoDB (no joins)          |
| **Asyncpg**        | Fastest async Postgres driver, connection pooling                  | psycopg (blocking)                            |
| **Pydantic v2**    | Automatic validation, JSON serialization, performance              | Manual validation, marshmallow                |
| **PyJWT**          | Lightweight JWT handling, no external dependencies                 | python-jose (heavier)                         |
| **Bcrypt**         | Industry standard, slow by design (brute-force resistant)          | MD5/SHA (insecure), SCRYPT (overkill)         |

### Frontend: Why Flutter?

| Choice                | Reason                                                        | Alternative                                                  |
| --------------------- | ------------------------------------------------------------- | ------------------------------------------------------------ |
| **Flutter**           | One codebase → iOS/Android/Web, hot reload, great performance | React Native (JS, worse perf), Swift/Kotlin (separate teams) |
| **Riverpod**          | Modern state mgmt, dependency injection, testability          | Provider (less features), Bloc (more boilerplate)            |
| **Hive**              | Fast local NoSQL, Flutter-native, no setup                    | SQLite (slower), GetStorage (limited features)               |
| **Dio**               | Rich HTTP client, interceptors, retry logic                   | http package (basic), Chopper (complex)                      |
| **Connectivity Plus** | Cross-platform network detection, simple API                  | Manual URL pinging                                           |

---

## Data Flow

### 1. Authentication Flow

```
User enters phone + PIN
    ↓
Request: POST /auth/login { phone, pin }
    ↓
Backend: find user by phone
    ↓ User found?
    ├─ Yes: verify PIN with bcrypt
    │   ├─ Valid? → Create JWT, return token
    │   └─ Invalid? → Return 401 Unauthorized
    └─ No: Return 401 Unauthorized
    ↓
Frontend: Store JWT in Hive encrypted box
    ↓
Add Authorization header to all future requests
    ↓
If 401 received → Refresh token (call /auth/login again)
    ↓
If refresh fails → Redirect to LoginScreen
```

### 2. Report Submission Flow (Offline-First)

```
User fills form in ReportFormScreen
    ↓
Watch connectivity_provider
    ├─ Online? → Show "Submitting..."
    └─ Offline? → Show "Queued for sync"
    ↓
User taps Submit
    ↓
Validate form (all required fields)
    ↓
Try to POST /reports/submit
    ├─ Success → Update local report status
    │   ├─ Update Hive (status=submitted)
    │   └─ Remove from sync queue
    │   └─ Show success toast
    │
    └─ Failure (offline/error) → Add to sync queue
        ├─ Save to Hive sync_queue box
        ├─ Show "Will sync when online"
        └─ User can see it in history as "Draft"
    ↓
SyncService monitors connectivity
    ├─ When online detected
    ├─ Retry all queued reports
    ├─ Max 3 retries with backoff
    └─ On final failure → Mark as sync error
```

### 3. Dashboard Data Flow

```
User navigates to Dashboard
    ↓
Fetch from cache first (Hive)
    ├─ Cache exists & fresh? → Display immediately
    └─ Cache missing/stale? → Show skeleton loader
    ↓
FutureProvider triggers API call
    ↓
Backend queries reports filtered by user's scope
    ├─ If cellLeader → Only own cell reports
    ├─ If seniorCellLeader → All cells under supervision
    ├─ If fellowshipPastor → All cells in fellowship
    └─ If zonal → All cells in zone
    ↓
Calculate aggregates:
    ├─ total_attendance = SUM(attendance_count)
    ├─ avg_attendance = AVG(attendance_count)
    ├─ cells_reported = COUNT(DISTINCT cell_id)
    ├─ submission_rate = cells_reported / total_cells
    └─ souls_won = SUM(souls_won)
    ↓
Return aggregated stats
    ↓
Frontend updates UI with fresh data
    ├─ Update Hive cache
    └─ Animate transitions
```

---

## Security Architecture

### 1. Authentication Layer

```
┌──────────────────────────────────────┐
│  Client: Login with Phone + PIN      │
└──────────────────────────────────────┘
              ↓ HTTPS
┌──────────────────────────────────────┐
│ Backend: Verify PIN with bcrypt      │
│ - PIN hashed with 12 rounds          │
│ - Timing-safe comparison             │
│ - No cleartext storage               │
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│ Create JWT Token                     │
│ - Algorithm: HS256                   │
│ - Secret: 32+ char random string     │
│ - Expiration: 30 days                │
│ - Payload: { sub: user_id, exp, iat }│
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│ Return Token to Client               │
│ - Store in Hive (encrypted box)      │
│ - Include in Authorization header    │
└──────────────────────────────────────┘
```

### 2. Authorization (Role-Based Access Control)

Every endpoint enforces role hierarchy:

```python
# Example: Only system_admin can create zones
@router.post("/admin/zones")
async def create_zone(
    request: ZoneCreate,
    current_user: User = Depends(get_current_user),
):
    require_system_admin(current_user)  # ← Check permission
    ...
```

**Role Levels (1 = highest privilege):**

```
1. system_admin         → All operations
2. zonal_pastor         → View zone + below
3. zonal_admin          → Manage zone + below
4. fellowship_pastor    → Manage fellowship + below
5. senior_cell_leader   → Manage senior cell + cells
6. cell_leader          → Submit own cell reports only
```

### 3. Data Scope Enforcement

Users can only see data within their jurisdiction:

```python
# For cell_leader: only own cell
# For senior_cell_leader: only cells under supervision
# For fellowship_pastor: only cells in fellowship

def scoped_cell_query(user: User, session: AsyncSession):
    if user.role == UserRole.cell_leader:
        return select(Cell).where(Cell.id == user.cell_id)
    elif user.role == UserRole.senior_cell_leader:
        return select(Cell).join(SeniorCell).where(
            SeniorCell.id == user.senior_cell_id
        )
    # ... etc
```

### 4. Network Security

- **HTTPS Only**: All traffic encrypted with TLS
- **CORS**: Whitelist frontend domains only
- **Rate Limiting**: (Recommended) Limit requests per IP
- **Input Validation**: Pydantic validates all inputs
- **SQL Injection Prevention**: SQLAlchemy parameterized queries

---

## Scalability & Performance

### 1. Database Optimization

**Indexing:**

```sql
CREATE INDEX idx_user_phone ON users(phone);
CREATE INDEX idx_cell_report_cell_id ON cell_reports(cell_id);
CREATE INDEX idx_cell_report_submitted_at ON cell_reports(submitted_at);
```

**Query Optimization:**

- Eager loading relationships (avoid N+1)
- Pagination for large result sets
- Cached aggregates (recalculated nightly if needed)

### 2. Async/Concurrency

FastAPI handles thousands of concurrent connections:

```python
@router.get("/dashboards/overview")
async def overview(session: AsyncSession = Depends(get_session)):
    # This endpoint doesn't block other requests
    # Even if DB query takes 5 seconds
    results = await session.execute(...)
    return results
```

### 3. Caching Strategy

**Mobile app caching (Hive):**

- Dashboard stats cached for 5 minutes
- Report history cached indefinitely (refreshed on pull)
- User data cached indefinitely

**Backend caching (optional):**

- Could add Redis for frequently accessed stats
- Currently: database queries are fast enough for MVP

### 4. Pagination

Reports endpoint returns paginated results:

```
GET /reports?page=1&limit=20
GET /reports?date_from=2026-01-01&date_to=2026-05-31
```

### 5. Background Tasks

Non-critical operations (notifications, exports) can be offloaded:

```python
from celery import shared_task

@shared_task
def export_zone_report(zone_id):
    # Heavy processing in background
    # Return download link to user
```

---

## Deployment Architecture

### Backend Deployment (Render.com)

```
┌────────────────────────────────────┐
│   GitHub Repository (Main branch)  │
│   - Commits trigger automatic build│
└────────────────────────────────────┘
              ↓
┌────────────────────────────────────┐
│   Render Build Process             │
│   1. Clone repo                    │
│   2. Install dependencies (pip)    │
│   3. Run migrations (if any)       │
│   4. Build Docker image            │
│   5. Push to registry              │
└────────────────────────────────────┘
              ↓
┌────────────────────────────────────┐
│   Render Container Runtime         │
│   - Start uvicorn server           │
│   - Listen on port 8000            │
│   - Health checks every 30s        │
└────────────────────────────────────┘
              ↓
┌────────────────────────────────────┐
│   Load Balancer / Reverse Proxy    │
│   - HTTPS/SSL termination          │
│   - Distribute traffic to replicas │
│   - Auto-scale on demand           │
└────────────────────────────────────┘
```

### Frontend Deployment

**Mobile (iOS):**

```
Xcode → Archive → Signer → TestFlight → AppStore
```

**Mobile (Android):**

```
Android Studio → Build APK/AAB → Google Play Console → PlayStore
```

**Web:**

```
flutter build web --release → Deploy to Firebase/Netlify
```

---

## Design Decisions Rationale

### Decision 1: Why Async/Await (asyncio) in Backend?

**Decision**: Use FastAPI (async) instead of Django (sync)

**Rationale:**

- ✅ Mobile users on 3G need fast response times
- ✅ Handles thousands of concurrent connections efficiently
- ✅ I/O operations (DB, API calls) don't block the event loop
- ✅ Can handle 100+ concurrent mobile users with single server

**Trade-off:**

- ❌ Team must understand async/await (slightly steeper learning curve)
- ✅ But the performance gains justify it for this use case

---

### Decision 2: Why Hive for Mobile Storage?

**Decision**: Use Hive instead of SQLite

**Rationale:**

- ✅ Zero setup needed (no SQL migrations)
- ✅ 10x faster than SQLite for small documents
- ✅ Flutter-native (not a third-party library bolted on)
- ✅ Perfect for storing drafts & sync queues

**Trade-off:**

- ❌ Less suitable for complex queries (we don't need them)
- ✅ Simple key-value fits our offline-first needs

---

### Decision 3: Why Role-Based, Not Permission-Based?

**Decision**: Use role hierarchy (6 levels) instead of granular permissions

**Rationale:**

- ✅ Church structure is naturally hierarchical
- ✅ Simpler to implement & understand
- ✅ Faster authorization checks (O(1) instead of O(n))
- ✅ Fewer database lookups

**Trade-off:**

- ❌ Can't have a user who can "read reports but not create users"
- ✅ But this flexibility isn't needed for MVP

---

### Decision 4: Why Neon.tech (Serverless)?

**Decision**: Use Neon.tech PostgreSQL instead of self-hosted

**Rationale:**

- ✅ No DevOps overhead (auto-scaling, backups, SSL)
- ✅ Pay for what you use (free tier generous)
- ✅ Zero initial cost (suitable for church org)
- ✅ Auto-failover & redundancy included

**Trade-off:**

- ❌ Slight latency from cold starts (< 100ms acceptable)
- ✅ Benefits outweigh cost

---

### Decision 5: Why NullPool for Connection Pooling?

**Decision**: Use NullPool instead of QueuePool

**Rationale:**

- ✅ Serverless databases (Neon) can't maintain persistent connections
- ✅ NullPool creates new connection per request (fine for async)
- ✅ Prevents "too many connections" errors

**Trade-off:**

- ❌ Slightly higher latency per request (connection overhead)
- ✅ Acceptable for MVP scale (100s of requests/minute, not 1000s)

---

### Decision 6: Why Last-Write-Wins for Sync Conflicts?

**Decision**: When offline edits conflict with server, use last write

**Rationale:**

- ✅ Simple to implement (no merge logic needed)
- ✅ Works for reports (immutable once submitted)
- ✅ Church leaders understand it naturally

**Trade-off:**

- ❌ Could lose data if user edits locally & remotely simultaneously
- ✅ Rare in practice (users edit on one device at a time)

---

### Decision 7: Why 30-Day JWT Expiration?

**Decision**: Set JWT expiration to 30 days (very long)

**Rationale:**

- ✅ Mobile users need long sessions (can't re-login weekly)
- ✅ PIN-based auth is already fairly secure
- ✅ Cells meet weekly, need to submit reports in same week

**Trade-off:**

- ❌ Compromised token valid for long time
- ✅ Mitigated by HTTPS, no token logging, Hive encryption

---

### Decision 8: Why Offline-First for Mobile?

**Decision**: Make mobile app work offline by default

**Rationale:**

- ✅ Many rural churches have poor internet (Cameroon context)
- ✅ Users shouldn't wait for network response
- ✅ Background sync reduces user friction
- ✅ Better UX: instant form save & submission

**Trade-off:**

- ❌ Added complexity (sync queue, conflict resolution)
- ✅ Essential for this geographic/cultural context

---

## Future Architecture Changes

### Phase 2: Real-Time Features

```
WebSocket connection → Backend → Message queue (Redis)
  - Live dashboard updates
  - Real-time notifications
  - Requires: Redis, WebSocket support, SSE or WS protocol
```

### Phase 3: Horizontal Scaling

```
Current: Single FastAPI server
Future: Multiple servers + load balancer
  - Requires: Stateless design (already done ✓)
  - Add: Redis for session cache, Celery for background jobs
  - Database: Keep Neon (managed scaling)
```

### Phase 4: Advanced Analytics

```
Current: Aggregated stats in POST request
Future: Data warehouse + BI tool
  - Postgres → Data pipeline → BigQuery/Snowflake → Looker/Tableau
  - Predictive models: attendance forecasting, giving trends
```

---

## Monitoring & Observability

### Recommended Monitoring Stack

1. **Application Monitoring**: Sentry (error tracking)
2. **Performance**: New Relic or Datadog
3. **Database**: Neon.tech dashboard
4. **Uptime**: StatusPage or Pagerduty

### Key Metrics to Monitor

**Backend:**

- Request latency (p50, p95, p99)
- Error rate (4xx, 5xx)
- Database query time
- JWT validation failures
- Sync success rate

**Mobile:**

- App crash rate (Firebase Crashlytics)
- Offline sync failures
- API timeout frequency
- Storage usage (Hive size)

---

## Disaster Recovery

### Backup Strategy

**Database (Neon.tech):**

- Automatic daily backups (retention: 7 days)
- WAL archiving to S3 (point-in-time recovery)

**Static Files (if using Appwrite):**

- Versioned storage buckets
- Multi-region replication

**Code:**

- GitHub as source of truth
- Deployments are immutable (builds from git tags)

### Recovery Procedures

**If database corrupted:**

```
1. Neon dashboard → Restore from backup
2. Select point-in-time to restore to
3. Run migrations if needed
4. Restart backend service
```

**If backend down:**

```
1. Render automatically retries failed deployments
2. Manual: Roll back to previous git commit
3. Or: Deploy to secondary region
```

---

**Last Updated**: May 15, 2026  
**Version**: 1.0.0  
**Status**: In Development
