# Cellytics: Church Cell Management System

## 🎯 Project Overview

**Cellytics** (also known as **CellTrack** or **BLW Cell Reporting System**) is a full-stack mobile and web application for managing church cell-based organizational structures. It enables seamless reporting, analytics, and coordination across multi-level hierarchies (Regions → Zones → Fellowships → Senior Cells → Cells).

### Core Purpose

- Enable cell leaders to submit weekly meeting reports efficiently
- Provide leadership dashboards for supervision and analytics
- Maintain accurate attendance, financial, and spiritual metrics
- Support offline-first mobile workflows with automatic syncing

### Key Features

✅ **Multi-level Hierarchy**: 5-tier organizational structure with role-based permissions  
✅ **Mobile-First Reports**: Offline forms matching physical booklet structure  
✅ **Real-time Dashboards**: Leadership analytics for cells, fellowships, zones  
✅ **Secure Authentication**: PIN + JWT token-based system  
✅ **Push Notifications**: Firebase Cloud Messaging integration  
✅ **Cross-platform**: iOS, Android, Web (Flutter)  
✅ **Offline-Capable**: Hive local storage with automatic sync

---

## 📊 Project Status

| Component         | Status         | Version | Notes                          |
| ----------------- | -------------- | ------- | ------------------------------ |
| **Backend API**   | In Development | 1.0.0   | FastAPI, PostgreSQL, Neon.tech |
| **Mobile App**    | In Development | 1.0.0   | Flutter (iOS, Android)         |
| **Web Dashboard** | In Development | 1.0.0   | Flutter Web                    |
| **Documentation** | Complete       | 1.0     | This document                  |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Flutter Mobile App (iOS/Android)  │  Flutter Web    │   │
│  │  - Login Screen                    │  - Dashboards   │   │
│  │  - Report Form (Offline-First)     │  - Analytics    │   │
│  │  - Report History                  │  - Reports      │   │
│  │  - Basic Dashboard                 │                 │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           ↓
         ┌─────────────────────────────────────┐
         │  LOCAL STORAGE (Offline Support)   │
         │  ┌─────────────────────────────┐   │
         │  │ Hive: Draft reports, Queues │   │
         │  │ SharedPrefs: User, Settings │   │
         │  └─────────────────────────────┘   │
         └─────────────────────────────────────┘
                           ↓
         ┌─────────────────────────────────────┐
         │      SYNCHRONIZATION LAYER          │
         │  Auto-sync when online, Retry logic │
         └─────────────────────────────────────┘
                           ↓
      ┌──────────────────────────────────────────┐
      │        REST API (FastAPI Backend)        │
      │  ┌────────────────────────────────────┐  │
      │  │  Routes:                           │  │
      │  │  - /auth/login                     │  │
      │  │  - /admin/* (Zone, Fellowship...)  │  │
      │  │  - /reports/* (Submit, Get)        │  │
      │  │  - /dashboards/* (Analytics)       │  │
      │  │  - /notifications/*                │  │
      │  └────────────────────────────────────┘  │
      └──────────────────────────────────────────┘
                           ↓
      ┌──────────────────────────────────────────┐
      │      BUSINESS LOGIC LAYER (Services)     │
      │  - AdminService                          │
      │  - ReportService                         │
      │  - DashboardService                      │
      │  - FCMService (Notifications)            │
      └──────────────────────────────────────────┘
                           ↓
      ┌──────────────────────────────────────────┐
      │       DATA LAYER (SQLAlchemy ORM)        │
      │  - Models: Region, Zone, Fellowship...  │
      │  - Relationships & Constraints           │
      └──────────────────────────────────────────┘
                           ↓
         ┌──────────────────────────────────────┐
         │    PostgreSQL Database (Neon.tech)   │
         │  - 8+ tables with FK relationships   │
         │  - UUID primary keys                 │
         │  - Async connection pooling          │
         └──────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
celltrack_backend/
├── README.md                          # This file
├── BACKEND_DOCUMENTATION.md           # Detailed backend API docs
├── FRONTEND_DOCUMENTATION.md          # Flutter app docs
├── ARCHITECTURE.md                    # Architecture & design decisions
├── functional_requirements.md         # MVP requirements
│
├── Backend (Python/FastAPI)
│   ├── main.py                       # Application entry point
│   ├── auth.py                       # JWT & PIN authentication
│   ├── database.py                   # PostgreSQL async connection
│   ├── models.py                     # SQLAlchemy ORM models
│   ├── schemas.py                    # Pydantic validation schemas
│   ├── fcm_service.py                # Firebase Cloud Messaging
│   ├── requirements.txt              # Python dependencies
│   ├── Dockerfile                    # Docker containerization
│   │
│   ├── routers/                      # API endpoint handlers
│   │   ├── auth.py                  # Login endpoint
│   │   ├── admin.py                 # Zone/Fellowship/Cell/User management
│   │   ├── reports.py               # Report submission & retrieval
│   │   ├── dashboards.py            # Analytics endpoints
│   │   ├── notifications.py         # Notification management
│   │   └── uploads.py               # File upload handling
│   │
│   ├── services/                    # Business logic layer
│   │   ├── admin_service.py        # Admin operations
│   │   ├── dashboard_service.py    # Dashboard analytics
│   │   └── report_service.py       # Report processing
│   │
│   └── utils/                       # Utility functions
│       ├── helpers.py              # General helpers
│       └── security.py             # Auth checks & permissions
│
├── Mobile App (Flutter)
│   └── cellytics_mobile/
│       └── cellytics_ap/
│           ├── pubspec.yaml        # Flutter dependencies
│           ├── lib/
│           │   ├── main.dart       # App entry point
│           │   │
│           │   ├── screens/        # UI Pages
│           │   │   ├── login_screen.dart
│           │   │   ├── home_screen.dart
│           │   │   ├── profile_screen.dart
│           │   │   ├── report_form_screen.dart
│           │   │   ├── report_detail_screen.dart
│           │   │   ├── report_history_screen.dart
│           │   │   └── bottom_navigation.dart
│           │   │
│           │   ├── models/         # Data models
│           │   │   ├── user.dart
│           │   │   ├── cell_report.dart
│           │   │   ├── cell_summary.dart
│           │   │   └── api_response.dart
│           │   │
│           │   ├── services/       # API & storage
│           │   │   ├── api_service.dart    # Dio HTTP client
│           │   │   ├── local_storage.dart # Hive + SharedPrefs
│           │   │   └── sync_service.dart  # Offline sync
│           │   │
│           │   ├── providers/      # State management (Riverpod)
│           │   │   ├── auth_provider.dart
│           │   │   ├── connectivity_provider.dart
│           │   │   └── report_provider.dart
│           │   │
│           │   ├── config/         # Configuration
│           │   ├── theme/          # Design system
│           │   ├── utils/          # Helper functions
│           │   ├── widgets/        # Reusable components
│           │   └── l10n/           # Localization
│           │
│           ├── assets/
│           │   ├── images/
│           │   ├── icons/
│           │   ├── fonts/
│           │   └── translations/   # i18n JSON files
│           │
│           ├── android/            # Android native config
│           ├── ios/                # iOS native config
│           └── web/                # Web config
```

---

## 🔑 Key Roles & Permissions

The system implements a 6-level role hierarchy with cascading permissions:

| Role                   | Level | Permissions                 | Scope               |
| ---------------------- | ----- | --------------------------- | ------------------- |
| **System Admin**       | 1     | All CRUD for all levels     | Entire system       |
| **Zonal Pastor**       | 2     | View & report for zone      | Zone + below        |
| **Zonal Admin**        | 3     | Manage zone structure       | Zone + below        |
| **Fellowship Pastor**  | 4     | Manage fellowship & reports | Fellowship + below  |
| **Senior Cell Leader** | 5     | Manage senior cell          | Senior cell + cells |
| **Cell Leader**        | 6     | Submit own cell report      | Own cell only       |

---

## 🔐 Authentication & Authorization

### Login Flow

```
User (Phone + PIN)
    ↓
Backend validates against database
    ↓
PIN verified with bcrypt
    ↓
JWT token created (30-day expiration)
    ↓
Token + User data returned to mobile app
    ↓
Token stored in Hive (encrypted)
    ↓
Subsequent requests include: Authorization: Bearer <token>
```

### Security Features

- **PIN**: 6-digit numeric, hashed with bcrypt (12 rounds)
- **JWT**: HS256 algorithm, 30-day expiration
- **HTTPS**: Required for all communications
- **CORS**: Configured for frontend domains
- **Rate Limiting**: Recommended for production

---

## 📱 Mobile App Features

### Screens

1. **Login Screen**
   - Phone number + PIN entry
   - Persistent login with token storage
   - Error handling & validation

2. **Home Screen**
   - Quick access to main functions
   - Display user role & assigned cell
   - Sync status indicator

3. **Report Form** (Multi-page)
   - **Page 1**: Meeting details, activities, attendance
   - **Page 2**: Finances, testimonies, plans
   - **Page 3**: Soul-winning records
   - **Page 4**: Pastor's remarks (read-only)
   - Auto-save to Hive as draft
   - Photo attachments support

4. **Report History**
   - List all submitted reports
   - Filter by date range
   - View report status (Draft/Submitted/Late)
   - Edit draft reports

5. **Dashboard** (Basic on Mobile)
   - Own cell submission status
   - Next meeting reminder
   - Recent activity

6. **Profile Screen**
   - User info & role
   - Logout button
   - Settings

### Offline Capabilities

- **Hive Storage**: Draft reports, sync queue, settings
- **Auto-sync**: Submits queued reports when online
- **Retry Logic**: Automatic retry on failures
- **Conflict Resolution**: Last-write-wins strategy
- **Status Indicators**: Shows sync state to user

---

## 🌐 Web Dashboard Features

### Intended for Tablets/Desktop

- **Cell Leader View**: Own reports, submission status
- **Senior Cell Leader Dashboard**
  - All cells under supervision
  - Submission rates & attendance
  - Quick cell details view
  - Manage cell settings

- **Fellowship Pastor Dashboard**
  - All senior cells in fellowship
  - Aggregated stats (attendance, souls won, finances)
  - Cells needing attention alerts
  - Export weekly reports (CSV/PDF)

- **Zonal Admin Dashboard**
  - All fellowships overview
  - Submission rates by fellowship
  - Zone-wide trends & analytics
  - Identify struggling areas
  - Export zone reports

---

## 🗄️ Database Schema (Hierarchical)

```
Region (1)
  ├─ Zone (1:N)
  │   ├─ Fellowship (1:N)
  │   │   └─ SeniorCell (1:N)
  │   │       └─ Cell (1:N)
  │   │           └─ CellReport (1:N)
  │   ├─ User (Zonal Admin)
  │   └─ User (Zonal Pastor)
  │
  └─ User (System Admin)
```

### Core Tables

| Table           | Records          | Purpose                         |
| --------------- | ---------------- | ------------------------------- |
| `regions`       | ~5-10            | Geographic areas                |
| `zones`         | ~20-50           | Zone divisions                  |
| `fellowships`   | ~100-200         | Fellowship groups               |
| `senior_cells`  | ~300-500         | Senior cell groups              |
| `cells`         | ~1000-2000       | Basic units (5-10 members each) |
| `users`         | ~1000-2000       | Leaders & admins                |
| `cell_reports`  | ~1000-5000/month | Weekly reports                  |
| `notifications` | Auto-cleanup     | Push notifications              |

---

## 🚀 Getting Started

### Backend Setup

```bash
# 1. Clone & enter directory
cd celltrack_backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with:
# - DATABASE_URL=postgresql+asyncpg://user:pass@host/db
# - JWT_SECRET_KEY=<random-secret>
# - FCM_CREDENTIALS_JSON=<path-to-firebase-json>

# 5. Run migrations (if needed)
# Tables are pre-created via SQL schema

# 6. Start server
uvicorn main:app --reload

# 7. Access API documentation
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

### Mobile App Setup

```bash
# 1. Navigate to app directory
cd cellytics_mobile/cellytics_ap

# 2. Install Flutter dependencies
flutter pub get

# 3. Configure backend URL
# Edit lib/config/api_config.dart (or similar)
# Set API_BASE_URL = "http://your-backend-api.com"

# 4. Run on device/emulator
flutter run                    # Interactive device selection
flutter run -d <device-id>   # Specific device
flutter run -d web           # Web version

# 5. Build for production
flutter build apk             # Android
flutter build ipa             # iOS
flutter build web             # Web
```

---

## 🧪 Testing

### Backend Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html

# Specific test file
pytest tests/test_auth.py -v
```

### Mobile App Testing

```bash
# Run widget tests
flutter test

# With coverage
flutter test --coverage

# Integration tests
flutter test integration_test/
```

---

## 📈 API Overview

### Core Endpoints

**Authentication**

```
POST   /auth/login              # Login with phone + PIN
```

**Admin Management**

```
POST   /admin/zones             # Create zone
GET    /admin/zones             # List zones
GET    /admin/zones/{id}        # Get zone details
PUT    /admin/zones/{id}        # Update zone
DELETE /admin/zones/{id}        # Delete zone

POST   /admin/fellowships       # Create fellowship
GET    /admin/fellowships       # List fellowships
PUT    /admin/fellowships/{id}  # Update fellowship
DELETE /admin/fellowships/{id}  # Delete fellowship

POST   /admin/cells             # Create cell
GET    /admin/cells             # List cells
PUT    /admin/cells/{id}        # Update cell
DELETE /admin/cells/{id}        # Delete cell

POST   /admin/users             # Create user
GET    /admin/users             # List users
PUT    /admin/users/{id}        # Update user
DELETE /admin/users/{id}        # Deactivate user
```

**Reports**

```
POST   /reports/submit          # Submit cell report
GET    /reports                 # List reports (scoped)
GET    /reports/{id}            # Get report details
PUT    /reports/{id}            # Update draft report
DELETE /reports/{id}            # Delete draft report
GET    /reports/cell/{cell-id}  # Get cell's reports
```

**Dashboards**

```
GET    /dashboards/overview     # Summary stats
GET    /dashboards/cell/{id}    # Cell metrics
GET    /dashboards/zone/{id}    # Zone analytics
GET    /dashboards/fellowship/{id} # Fellowship analytics
GET    /dashboards/trends       # Time-series data
```

**Notifications**

```
POST   /notifications/register  # Register device token
GET    /notifications           # List notifications
POST   /notifications/{id}/read # Mark as read
GET    /notifications/settings  # Get preferences
PUT    /notifications/settings  # Update preferences
```

---

## 🔧 Configuration

### Environment Variables

**Backend (.env)**

```
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
JWT_SECRET_KEY=your-super-secret-key-min-32-chars
FCM_CREDENTIALS_JSON=/path/to/firebase-adminsdk.json
API_ENVIRONMENT=production|development
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000","https://app.cellytics.com"]
```

**Mobile (lib/config/api_config.dart)**

```dart
const String API_BASE_URL = 'https://api.cellytics.com';
const Duration API_TIMEOUT = Duration(seconds: 30);
const bool ENABLE_LOGGING = true;
```

---

## 📊 Data Flow Diagrams

### Report Submission (Offline-First)

```
User fills form offline
    ↓
Auto-save to Hive as draft
    ↓
User submits report
    ↓
Queue added to sync queue (Hive)
    ↓
App detects internet (connectivity_plus)
    ↓
Sync service retries queued reports
    ↓
Backend validates & stores in DB
    ↓
Response returned to app
    ↓
Local report updated with server ID
    ↓
Sync queue cleared for that report
    ↓
User notification: "Submitted successfully"
```

### Dashboard Data Fetch

```
User navigates to dashboard
    ↓
App checks local cache (Hive)
    ↓
If cache exists & fresh, show cached data
    ↓
Meanwhile, fetch fresh data from backend
    ↓
Backend service runs aggregation query
    ↓
Calculates stats: attendance, finances, souls won
    ↓
Applies user-scoped filters (zone, fellowship, etc)
    ↓
Returns JSON response
    ↓
App updates Hive cache
    ↓
UI refreshes with new data
    ↓
User sees latest stats
```

---

## 🛠️ Development Workflow

### Making Backend Changes

1. **Update Models** (`models.py`)

   ```python
   class NewModel(Base):
       __tablename__ = "new_models"
       # Define columns...
   ```

2. **Create Schemas** (`schemas.py`)

   ```python
   class NewModelCreate(BaseModel):
       # Define fields...
   ```

3. **Add Service Logic** (`services/`)

   ```python
   class MyService:
       async def process_something(self, data):
           # Business logic...
   ```

4. **Create Endpoints** (`routers/`)

   ```python
   @router.post("/endpoint")
   async def endpoint(request: NewModelCreate, session: AsyncSession = Depends(get_session)):
       # Call service...
   ```

5. **Test**
   ```bash
   pytest tests/test_endpoint.py -v
   ```

### Making Mobile Changes

1. **Update Models** (`lib/models/`)

   ```dart
   class NewModel {
       final String id;
       // Fields...
       factory NewModel.fromJson(Map<String, dynamic> json) {
           // Parse JSON...
       }
   }
   ```

2. **Add Service Methods** (`lib/services/api_service.dart`)

   ```dart
   Future<NewModel> fetchNewModel() async {
       final response = await _dio.get('/endpoint');
       return NewModel.fromJson(response.data);
   }
   ```

3. **Create Provider** (`lib/providers/`)

   ```dart
   final newModelProvider = StateNotifierProvider((ref) => NewModelNotifier());
   ```

4. **Build UI** (`lib/screens/`)

   ```dart
   class NewScreen extends ConsumerWidget {
       @override
       Widget build(BuildContext context, WidgetRef ref) {
           // Use providers...
       }
   }
   ```

5. **Test**
   ```bash
   flutter test
   ```

---

## 🚢 Deployment

### Backend Deployment (Render)

```bash
# 1. Push to GitHub
git add .
git commit -m "Update: ..."
git push origin main

# 2. Render auto-deploys from GitHub
# - Builds Docker image
# - Runs migrations
# - Starts uvicorn server

# 3. Set environment variables in Render dashboard
# - DATABASE_URL
# - JWT_SECRET_KEY
# - FCM credentials
```

### Mobile Deployment

**iOS (TestFlight/AppStore)**

```bash
flutter build ipa --release
# Upload to Apple App Store
```

**Android (TestFlight/Play Store)**

```bash
flutter build apk --release
# Upload to Google Play Console
```

**Web**

```bash
flutter build web --release
# Deploy dist/ folder to hosting (Firebase, Netlify, etc)
```

---

## 📚 Documentation Files

- [BACKEND_DOCUMENTATION.md](BACKEND_DOCUMENTATION.md) — Complete API reference, database schema, authentication
- [FRONTEND_DOCUMENTATION.md](FRONTEND_DOCUMENTATION.md) — Flutter app structure, screens, state management
- [ARCHITECTURE.md](ARCHITECTURE.md) — System design, decision rationale, diagrams
- [functional_requirements.md](functional_requirements.md) — MVP requirements, user stories

---

## 🤝 Contributing

### Code Style

- **Backend**: PEP 8, type hints for all functions
- **Mobile**: Dart style guide, camelCase for variables
- **Commits**: Semantic commit messages (feat:, fix:, docs:, etc)

### Pull Request Process

1. Create feature branch: `git checkout -b feature/description`
2. Make changes with tests
3. Submit PR with description
4. Code review & approval
5. Merge to main

---

## 🐛 Troubleshooting

### Backend Issues

**Database Connection Error**

- Check DATABASE_URL format
- Verify PostgreSQL is running
- Test SSL certificate (Neon.tech)

**JWT Token Expired**

- Mobile app will auto-refresh token
- If manual: request new token via `/auth/login`

**CORS Error**

- Update CORS_ORIGINS in .env
- Include frontend domain with protocol

### Mobile Issues

**API Connection Failed**

- Check backend URL in config
- Verify network connectivity
- Check firewall/VPN

**Offline Sync Not Working**

- Verify Hive is initialized
- Check sync_service.dart logs
- Clear app cache & retry

**State Not Updating**

- Rebuild Riverpod providers
- Check provider dependencies
- Verify AsyncValue handling

---

## 📞 Support & Contact

For issues or questions:

1. Check documentation files
2. Review error logs
3. Search existing GitHub issues
4. Contact development team

---

## 📄 License

[Your License Here]

---

**Last Updated**: May 15, 2026  
**Version**: 1.0.0  
**Status**: In Development
