# Cellytics Project - Complete Documentation Summary

**Version**: 1.0.0  
**Last Updated**: May 15, 2026  
**Status**: In Development

---

## 📚 Documentation Files Overview

This project has comprehensive documentation across multiple files. Use this as your navigation guide.

### 1. **README.md** - START HERE ⭐

**Location**: [README.md](README.md)  
**Purpose**: Project overview, features, architecture diagram, quick start guide  
**Best for**: New team members, understanding the big picture  
**Contents**:

- Project overview & features
- Full system architecture diagram
- Repository structure
- Role & permission hierarchy
- Setup instructions (backend & mobile)
- API endpoints overview
- Testing guide
- Deployment checklist

**When to read**: First thing when joining the project

---

### 2. **ARCHITECTURE.md** - System Design 🏗️

**Location**: [ARCHITECTURE.md](ARCHITECTURE.md)  
**Purpose**: Detailed architecture patterns, design decisions, rationale  
**Best for**: Understanding why we made certain choices, system design questions  
**Contents**:

- High-level system diagram
- Clean architecture pattern explanation
- Technology choices & alternatives
- Data flow diagrams (auth, reports, dashboards)
- Security architecture deep-dive
- Scalability & performance strategy
- Deployment architecture
- Design decisions with trade-offs (8 major decisions)
- Monitoring & disaster recovery

**When to read**: When making architectural changes, comparing alternatives, planning phase 2

---

### 3. **BACKEND_DOCUMENTATION.md** - API & Backend 🔧

**Location**: [BACKEND_DOCUMENTATION.md](BACKEND_DOCUMENTATION.md)  
**Purpose**: Complete backend API reference, database schema, services  
**Best for**: Backend developers, API integration, database questions  
**Contents**:

- Tech stack details
- Project structure (files & purpose)
- Core architecture (3-tier pattern)
- Complete data models (Region, Zone, Fellowship, Cell, User, CellReport)
- All API endpoints with request/response examples
- JWT & PIN authentication details
- Database schema & connection management
- Services layer (AdminService, DashboardService, ReportService, FCMService)
- Error handling (HTTP status codes)
- Deployment (Docker, environment variables)
- Development workflow

**When to read**: When working on backend features, integrating with API, debugging

---

### 4. **FRONTEND_DOCUMENTATION.md** - Flutter Mobile App 📱

**Location**: [FRONTEND_DOCUMENTATION.md](FRONTEND_DOCUMENTATION.md)  
**Purpose**: Complete Flutter app guide, screens, state management, data models  
**Best for**: Mobile developers, understanding UI/UX, implementing features  
**Contents**:

- Tech stack (Flutter dependencies)
- Project structure (lib/, assets/, etc)
- Core architecture (Riverpod state management)
- Riverpod providers (StateNotifier, FutureProvider, StreamProvider)
- API integration (APIService, error handling)
- Offline-first strategy (Hive, SyncService)
- All screens with responsibilities
- Data models (User, CellReport, CellSummary)
- Services (APIService, LocalStorageService)
- Custom widgets & reusable components
- Build & deployment (iOS, Android, Web)
- Testing strategy
- Best practices & performance tips

**When to read**: When working on mobile features, understanding state flow, building new screens

---

### 5. **functional_requirements.md** - MVP Requirements 📋

**Location**: [functional_requirements.md](functional_requirements.md)  
**Purpose**: Original MVP requirements, user stories, non-functional requirements  
**Best for**: Product understanding, feature acceptance criteria, scope questions  
**Contents**:

- Functional requirements (must-have, nice-to-have)
- User stories with acceptance criteria
- Non-functional requirements (performance, scalability, security)
- Data flow diagrams
- System architecture overview
- MVP scope & phase 1 requirements

**When to read**: Understanding what we're building, acceptance testing, scope clarification

---

## 🗂️ Quick Navigation by Role

### If you're a **Backend Developer** (Python/FastAPI):

1. Read: [README.md](README.md) (5 min)
2. Read: [ARCHITECTURE.md](ARCHITECTURE.md) (20 min) - Focus on "Data Flow" section
3. Deep dive: [BACKEND_DOCUMENTATION.md](BACKEND_DOCUMENTATION.md) (30 min)
4. Reference: Check `routers/`, `services/`, `models.py` as needed

**Key Files to Know:**

- `main.py` - Application entry point
- `models.py` - Database models (Region, Zone, Cell, etc)
- `schemas.py` - Request/response validation
- `auth.py` - JWT & PIN authentication
- `database.py` - PostgreSQL connection setup
- `routers/` - API endpoints (auth, admin, reports, dashboards)
- `services/` - Business logic

---

### If you're a **Mobile Developer** (Flutter/Dart):

1. Read: [README.md](README.md) (5 min)
2. Read: [ARCHITECTURE.md](ARCHITECTURE.md) (20 min) - Focus on "Offline-First Strategy"
3. Deep dive: [FRONTEND_DOCUMENTATION.md](FRONTEND_DOCUMENTATION.md) (40 min)
4. Reference: Check `lib/screens/`, `lib/providers/`, `lib/services/` as needed

**Key Files to Know:**

- `lib/main.dart` - App entry point, initialization
- `lib/screens/` - All UI pages (login, reports, dashboard)
- `lib/providers/` - Riverpod state management
- `lib/services/api_service.dart` - HTTP client setup
- `lib/services/local_storage.dart` - Hive persistence
- `lib/models/` - Data classes (User, CellReport)
- `pubspec.yaml` - Dependencies

---

### If you're a **Product Manager / Stakeholder**:

1. Read: [README.md](README.md) (10 min) - Focus on "Features" & "Roles"
2. Skim: [functional_requirements.md](functional_requirements.md) (15 min)
3. Reference: Check FAQ section below

---

### If you're **DevOps / Infrastructure**:

1. Read: [README.md](README.md) - "Deployment" section (5 min)
2. Deep dive: [ARCHITECTURE.md](ARCHITECTURE.md) - "Deployment Architecture" (15 min)
3. Reference: [BACKEND_DOCUMENTATION.md](BACKEND_DOCUMENTATION.md) - "Deployment" section

**Key Environment Variables:**

```
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
JWT_SECRET_KEY=<random-32-char-string>
FCM_CREDENTIALS_JSON=/path/to/firebase.json
API_ENVIRONMENT=production|development
CORS_ORIGINS=["https://app.cellytics.com"]
```

---

## 🔍 Quick Reference

### API Endpoints (Quick List)

**Authentication**

```
POST   /auth/login                 # Phone + PIN → JWT token
```

**Admin Management**

```
POST   /admin/zones                # Create zone (System Admin)
GET    /admin/zones                # List zones
POST   /admin/fellowships          # Create fellowship (Zonal Admin+)
POST   /admin/cells                # Create cell (Senior Cell Leader+)
POST   /admin/users                # Create user (role-based)
```

**Reports**

```
POST   /reports/submit             # Submit cell report (Cell Leader+)
GET    /reports                    # List reports (scoped to user)
GET    /reports/{id}               # Get report details
PUT    /reports/{id}               # Update draft report
GET    /reports/cell/{cell-id}     # Get cell's reports
```

**Dashboards**

```
GET    /dashboards/overview        # Summary stats
GET    /dashboards/cell/{id}       # Cell metrics
GET    /dashboards/zone/{id}       # Zone analytics
GET    /dashboards/trends          # Time-series data
```

**Notifications**

```
POST   /notifications/register     # Register device token
GET    /notifications              # List notifications
POST   /notifications/{id}/read    # Mark as read
```

---

### Data Models (Quick Reference)

**User Roles (Hierarchy)**

```
1. system_admin          (All access)
2. zonal_pastor          (Zone + below)
3. zonal_admin           (Manage zone)
4. fellowship_pastor     (Manage fellowship + below)
5. senior_cell_leader    (Manage senior cell + cells)
6. cell_leader           (Submit cell reports only)
```

**Report Status**

```
draft      → Not submitted yet
submitted  → Submitted on time
late       → Submitted > 3 days late
overdue    → Not submitted > 7 days
```

**Organizational Hierarchy**

```
Region (1) → Zone (1:N) → Fellowship (1:N) → SeniorCell (1:N) → Cell (1:N) → CellReport (1:N)
```

---

### Environment Setup

**Backend**

```bash
cd celltrack_backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # Edit with your DATABASE_URL, JWT_SECRET
uvicorn main:app --reload        # http://localhost:8000/docs
```

**Mobile**

```bash
cd cellytics_mobile/cellytics_ap
flutter pub get
flutter run                       # Interactive device selection
```

---

## ❓ FAQ

**Q: How do users authenticate?**  
A: Phone number + 6-digit PIN. Backend verifies PIN with bcrypt, returns JWT token valid for 30 days.

**Q: Can the mobile app work offline?**  
A: Yes! Reports saved to Hive, synced when online. Automatic retry with 3 attempts.

**Q: What happens if a report is submitted while offline?**  
A: Added to sync queue. When online, automatically synced. User sees status as "Draft" until sync completes.

**Q: How does permission checking work?**  
A: Role-based hierarchy. Each endpoint checks user.role and only allows higher-level users. Also filters data by user's jurisdiction (zone, fellowship, cell).

**Q: Where is the database?**  
A: PostgreSQL on Neon.tech (serverless). Neon handles scaling, backups, and SSL automatically.

**Q: How are reports stored?**  
A: PostgreSQL table `cell_reports` with FK to `cells`. Each report immutable once submitted.

**Q: Can dashboards be cached?**  
A: Yes. Mobile app caches stats for 5 minutes. Backend queries are optimized with indexes.

**Q: What about real-time updates?**  
A: Not in MVP. Phase 2 would add WebSockets for live dashboard.

**Q: How do I add a new API endpoint?**  
A: See BACKEND_DOCUMENTATION.md "Development Workflow" section.

**Q: How do I add a new screen?**  
A: See FRONTEND_DOCUMENTATION.md "Screens & Navigation" section.

---

## 📞 Common Issues & Solutions

### Backend

**"Database connection refused"**

- Check DATABASE_URL format in .env
- Verify Neon.tech dashboard shows database is online
- Test: `python -c "import asyncpg; print('OK')"`

**"JWT token expired"**

- Mobile app auto-refreshes on 401
- If manual: call /auth/login again
- Check system time is correct (JWT uses exp timestamp)

**"CORS error in browser"**

- Update CORS_ORIGINS in .env
- Include both protocol & domain: `https://app.cellytics.com`

### Mobile

**"API request times out"**

- Check backend is running: `curl http://localhost:8000/health`
- Check API_BASE_URL in lib/config/api_config.dart
- Verify network connectivity

**"Offline sync not working"**

- Check Hive is initialized (main.dart)
- Check connectivity_plus detects network
- Look at sync_service.dart logs

**"State not updating in widget"**

- Verify you're using `ref.watch()` not `ref.read()`
- Check AsyncValue states are handled correctly
- Rebuild Riverpod providers if dependencies changed

---

## 🚀 Next Steps

1. **Backend**: Implement missing endpoints (currently: auth, admin CRUD, basic reports)
2. **Mobile**: Complete report form screen (currently: shell & basic auth)
3. **Testing**: Add unit tests for services (currently: basic tests)
4. **Deployment**: Set up CI/CD pipeline on GitHub Actions
5. **Analytics**: Add Sentry for error tracking
6. **Monitoring**: Set up Neon.tech monitoring & alerts

---

## 📖 Reading Order Recommendation

**For New Team Members (First Week):**

1. README.md (quick overview)
2. functional_requirements.md (understand scope)
3. ARCHITECTURE.md (understand design)
4. Your role's specific doc (BACKEND_DOCUMENTATION or FRONTEND_DOCUMENTATION)

**For Feature Implementation:**

1. Check functional_requirements.md for what to build
2. Check ARCHITECTURE.md for where it fits
3. Check role-specific documentation for HOW
4. Reference actual code files

**For Troubleshooting:**

1. Check FAQ & Common Issues above
2. Check role-specific documentation's troubleshooting section
3. Check code comments & logs

---

## 📄 File Locations

```
celltrack_backend/
├── README.md                          # ← You are here (navigation guide)
├── ARCHITECTURE.md                    # System design & decisions
├── BACKEND_DOCUMENTATION.md           # API & backend reference
├── FRONTEND_DOCUMENTATION.md          # Flutter app guide
├── functional_requirements.md         # MVP requirements
│
├── Backend Implementation (Python)
│   ├── main.py
│   ├── auth.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── fcm_service.py
│   ├── requirements.txt
│   ├── routers/ (auth, admin, reports, dashboards, notifications, uploads)
│   ├── services/ (admin_service, dashboard_service, report_service)
│   └── utils/ (helpers, security)
│
└── Frontend Implementation (Flutter)
    └── cellytics_mobile/cellytics_ap/
        ├── pubspec.yaml
        ├── lib/
        │   ├── main.dart
        │   ├── screens/ (login, home, reports, dashboard, profile)
        │   ├── models/ (user, cell_report, cell_summary)
        │   ├── services/ (api_service, local_storage, sync_service)
        │   ├── providers/ (auth, connectivity, report)
        │   ├── config/
        │   ├── theme/
        │   ├── widgets/
        │   ├── utils/
        │   └── l10n/ (localization)
        ├── assets/
        ├── android/
        ├── ios/
        └── web/
```

---

## 📊 Documentation Statistics

| Document                   | Pages   | Focus                  | Read Time   |
| -------------------------- | ------- | ---------------------- | ----------- |
| README.md                  | 15      | Overview & Quick Start | 10 min      |
| ARCHITECTURE.md            | 20      | System Design          | 25 min      |
| BACKEND_DOCUMENTATION.md   | 25      | API & Backend          | 30 min      |
| FRONTEND_DOCUMENTATION.md  | 30      | Mobile App             | 40 min      |
| functional_requirements.md | 10      | Requirements           | 15 min      |
| **TOTAL**                  | **100** | **Complete Project**   | **2 hours** |

---

**Maintained by**: Development Team  
**Last Review**: May 15, 2026  
**Next Review**: June 15, 2026
