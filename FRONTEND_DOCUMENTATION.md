# Cellytics Flutter Frontend Documentation

## Table of Contents

1. [Overview](#overview)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Core Architecture](#core-architecture)
5. [State Management (Riverpod)](#state-management-riverpod)
6. [API Integration](#api-integration)
7. [Offline-First Strategy](#offline-first-strategy)
8. [Screens & Navigation](#screens--navigation)
9. [Data Models](#data-models)
10. [Services Layer](#services-layer)
11. [Widget Library](#widget-library)
12. [Build & Deployment](#build--deployment)

---

## Overview

**Cellytics Mobile** is a Flutter application providing cell leaders and church administrators with a mobile-first interface to:

- Submit weekly cell meeting reports
- View submission history and status
- Access personal dashboard with meeting reminders
- Manage profile and settings
- Support offline-first workflows with automatic sync

### Platform Support

- ✅ **iOS** (iPhone)
- ✅ **Android** (Phones & Tablets)
- ✅ **Web** (Tablets & Desktops)

### Key Characteristics

- **Offline-First**: Full functionality without internet
- **Responsive Design**: Optimized for mobile (390×844) and scalable
- **Real-time Sync**: Background sync when online
- **Secure**: JWT tokens, encrypted local storage
- **Localized**: Multi-language support (English, others TBD)

---

## Tech Stack

### Core Framework

- **Flutter** (SDK ^3.6.2) — Cross-platform UI framework
- **Dart** — Programming language

### State Management

- **Riverpod** (v2.6.1) — Advanced state management with providers

### Local Storage

- **Hive** (v1.1.0) — Fast, local NoSQL database
- **SharedPreferences** — Key-value storage for settings

### Networking

- **Dio** (v5.9.2) — HTTP client with interceptors, retry logic
- **Connectivity Plus** (v7.1.1) — Internet connectivity detection

### UI & Design

- **Flutter ScreenUtil** (v5.9.3) — Responsive design utilities
- **CupertinoIcons** (v1.0.8) — iOS-style icons
- **Material & Cupertino** — Built-in design systems

### Media & Localization

- **Image Picker** (v1.1.2) — Camera & gallery access
- **Easy Localization** (v3.0.8) — i18n/l10n support

### Development Tools

- **Flutter Lints** — Code quality analysis
- **Flutter Test** — Unit & widget testing

---

## Project Structure

```
cellytics_mobile/
└── cellytics_ap/                    # Main Flutter app
    ├── pubspec.yaml                 # Dependencies & metadata
    ├── analysis_options.yaml        # Linting rules
    ├── README.md                    # App README
    │
    ├── lib/
    │   ├── main.dart                # App entry point & configuration
    │   │
    │   ├── screens/                 # UI Pages (5 main + shared)
    │   │   ├── auth/
    │   │   │   └── login_screen.dart
    │   │   ├── home/
    │   │   │   └── home_screen.dart
    │   │   ├── profile/
    │   │   │   └── profile_screen.dart
    │   │   ├── reports/
    │   │   │   ├── report_form_screen.dart      # Multi-page form
    │   │   │   ├── report_detail_screen.dart    # View report
    │   │   │   └── report_history_screen.dart   # List reports
    │   │   ├── dashboard/
    │   │   │   └── dashboard_screen.dart
    │   │   ├── shared/
    │   │   │   ├── bottom_navigation.dart
    │   │   │   └── loading_overlay.dart
    │   │   └── app_shell.dart                   # Main layout wrapper
    │   │
    │   ├── models/                  # Data classes (Dart/JSON)
    │   │   ├── user.dart            # User + roles + jurisdiction
    │   │   ├── cell_report.dart     # Report data structure
    │   │   ├── cell_summary.dart    # Cell metadata
    │   │   └── api_response.dart    # Generic API wrapper
    │   │
    │   ├── services/                # Business logic & integration
    │   │   ├── api_service.dart     # Dio HTTP client setup
    │   │   ├── local_storage.dart   # Hive + SharedPrefs
    │   │   └── sync_service.dart    # Offline sync orchestration
    │   │
    │   ├── providers/               # State (Riverpod)
    │   │   ├── auth_provider.dart   # User state & login/logout
    │   │   ├── connectivity_provider.dart # Network status
    │   │   └── report_provider.dart # Report draft & form state
    │   │
    │   ├── config/                  # App configuration
    │   │   ├── api_config.dart      # API endpoints, timeouts
    │   │   ├── app_constants.dart   # Enums, constants
    │   │   └── branding.dart        # App branding config
    │   │
    │   ├── theme/                   # Design system
    │   │   ├── app_theme.dart       # Light/dark themes
    │   │   ├── colors.dart          # Color palette
    │   │   ├── text_styles.dart     # Typography
    │   │   └── dimensions.dart      # Spacing, sizes
    │   │
    │   ├── widgets/                 # Reusable components
    │   │   ├── buttons/
    │   │   │   ├── primary_button.dart
    │   │   │   └── secondary_button.dart
    │   │   ├── inputs/
    │   │   │   ├── text_field.dart
    │   │   │   ├── pin_input.dart
    │   │   │   └── number_input.dart
    │   │   ├── cards/
    │   │   │   ├── report_card.dart
    │   │   │   └── stat_card.dart
    │   │   ├── navigation/
    │   │   │   └── custom_bottom_nav.dart
    │   │   └── common/
    │   │       ├── app_bar.dart
    │   │       ├── empty_state.dart
    │   │       └── error_widget.dart
    │   │
    │   ├── utils/                   # Helper functions
    │   │   ├── validators.dart      # Form validation
    │   │   ├── formatters.dart      # Date, currency formatting
    │   │   ├── logger.dart          # Debug logging
    │   │   └── extensions.dart      # Dart extensions
    │   │
    │   └── l10n/                    # Localization (i18n)
    │       └── en.json              # English translations
    │
    ├── assets/
    │   ├── images/                  # PNG, JPEG images
    │   ├── icons/                   # SVG icons (if using)
    │   ├── fonts/                   # Custom fonts
    │   └── translations/            # i18n JSON files
    │       ├── en.json              # English
    │       ├── fr.json              # French (optional)
    │       └── (other languages)
    │
    ├── android/                     # Android native code
    │   ├── app/src/                 # Android app source
    │   ├── build.gradle             # Android build config
    │   └── local.properties         # Local SDK paths
    │
    ├── ios/                         # iOS native code
    │   ├── Runner/                  # iOS app target
    │   ├── Runner.xcodeproj/        # Xcode project
    │   ├── Podfile                  # CocoaPods dependencies
    │   └── Runner.xcworkspace/      # Workspace for development
    │
    ├── web/                         # Web (Flutter for Web)
    │   ├── index.html               # Web entry point
    │   ├── manifest.json            # PWA manifest
    │   ├── icons/                   # Web icons
    │   └── styles/                  # CSS (if needed)
    │
    ├── test/                        # Unit & widget tests
    │   └── widget_test.dart
    │
    └── build/                       # Build artifacts (generated)
        ├── app/                     # App build outputs
        ├── connectivity_plus/       # Plugin builds
        ├── path_provider_android/
        ├── shared_preferences_android/
        └── ...
```

---

## Core Architecture

### Clean Architecture Pattern

```
┌─────────────────────────────────┐
│      PRESENTATION LAYER         │
│  Screens & Widgets (UI)         │
│  - State management via Riverpod│
│  - User interactions            │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│    BUSINESS LOGIC LAYER         │
│  Providers (Riverpod)           │
│  - StateNotifier<T>             │
│  - FutureProvider               │
│  - AsyncValue handling          │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│     SERVICES LAYER              │
│  - APIService (Dio)             │
│  - LocalStorageService (Hive)   │
│  - SyncService                  │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│     DATA LAYER                  │
│  Models & Data Classes          │
│  - User, CellReport, etc        │
│  - JSON serialization           │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│   LOCAL & REMOTE STORAGE        │
│  - Hive (local)                 │
│  - PostgreSQL (backend)         │
└─────────────────────────────────┘
```

### Dependency Injection

Riverpod handles all dependency injection:

```dart
// Define a service
final apiServiceProvider = Provider((ref) => ApiService());

// Define a provider that depends on service
final userProvider = StateNotifierProvider((ref) {
  final apiService = ref.watch(apiServiceProvider);
  return UserNotifier(apiService);
});

// In widgets, access via Riverpod
final user = ref.watch(userProvider);
```

---

## State Management (Riverpod)

### Provider Types Used

#### 1. **StateNotifierProvider** — Mutable state

```dart
final authProvider = StateNotifierProvider((ref) {
  return AuthNotifier();
});

// Usage in widget
final isLoggedIn = ref.watch(authProvider);
ref.read(authProvider.notifier).login(phone, pin);
```

#### 2. **FutureProvider** — Async data fetching

```dart
final reportsProvider = FutureProvider((ref) async {
  final apiService = ref.watch(apiServiceProvider);
  return apiService.getReports();
});

// Usage
final reports = ref.watch(reportsProvider);
// Returns AsyncValue<List<CellReport>>
```

#### 3. **StreamProvider** — Real-time streams

```dart
final connectivityProvider = StreamProvider((ref) {
  return Connectivity().onConnectivityChanged;
});
```

#### 4. **Provider** — Simple, read-only state

```dart
final apiServiceProvider = Provider((ref) => ApiService());
```

### AsyncValue Handling

When using FutureProvider, handle all states:

```dart
final reportsAsync = ref.watch(reportsProvider);

reportsAsync.when(
  data: (reports) => ListView(...),
  loading: () => LoadingWidget(),
  error: (err, stack) => ErrorWidget(err),
);
```

### Provider Patterns

**Scoped Queries** (user can only see own data):

```dart
final myReportsProvider = FutureProvider((ref) async {
  final apiService = ref.watch(apiServiceProvider);
  final currentUser = ref.watch(authProvider);
  return apiService.getReportsByCell(currentUser.cellId);
});
```

**Dependent Providers**:

```dart
final cellStatsProvider = FutureProvider((ref) async {
  final reports = await ref.watch(myReportsProvider.future);
  return calculateStats(reports);
});
```

---

## API Integration

### APIService Architecture

Located in `lib/services/api_service.dart`:

```dart
class ApiService {
  late Dio _dio;
  final _tokenBox = Hive.box('auth');

  ApiService() {
    _initDio();
  }

  void _initDio() {
    _dio = Dio(BaseOptions(
      baseUrl: ApiConfig.baseUrl,
      connectTimeout: ApiConfig.timeout,
    ));

    // JWT token interceptor
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        final token = _tokenBox.get('token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (error, handler) {
        if (error.response?.statusCode == 401) {
          // Handle token expiration
          _refreshToken();
        }
        return handler.next(error);
      },
    ));

    // Retry interceptor for failed requests
    _dio.interceptors.add(RetryInterceptor(...));

    // Logging interceptor (debug only)
    if (ApiConfig.enableLogging) {
      _dio.interceptors.add(LoggingInterceptor(...));
    }
  }

  Future<LoginResponse> login(String phone, String pin) async {
    try {
      final response = await _dio.post('/auth/login', data: {
        'phone': phone,
        'pin': pin,
      });
      return LoginResponse.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(e.message ?? 'Login failed');
    }
  }

  Future<List<CellReport>> getReports() async {
    try {
      final response = await _dio.get('/reports');
      return (response.data as List)
          .map((r) => CellReport.fromJson(r))
          .toList();
    } on DioException catch (e) {
      throw ApiException(e.message ?? 'Failed to fetch reports');
    }
  }

  Future<void> submitReport(CellReport report) async {
    try {
      await _dio.post('/reports/submit', data: report.toJson());
    } on DioException catch (e) {
      throw ApiException(e.message ?? 'Failed to submit report');
    }
  }
}
```

### Error Handling

All API calls wrapped with try-catch and custom exception handling:

```dart
class ApiException implements Exception {
  final String message;
  final int? statusCode;
  ApiException(this.message, {this.statusCode});

  @override
  String toString() => 'ApiException: $message';
}
```

---

## Offline-First Strategy

### Architecture

```
┌─────────────────────────────────┐
│    User Fills Form              │
│  - Edits saved to Hive as draft │
│  - No internet required         │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│  User Submits Report            │
│  - Check internet (connectivity)│
│  - If online: POST to backend   │
│  - If offline: add to sync queue│
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│  SyncService Monitors Network   │
│  - Listens to connectivity      │
│  - When online detected         │
│  - Flush sync queue             │
│  - Retry failed syncs (3x)      │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│  Backend Validation & Storage   │
│  - Validate all fields          │
│  - Store in PostgreSQL          │
│  - Return success response      │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│  Update Local State             │
│  - Mark draft as submitted      │
│  - Remove from sync queue       │
│  - Update Hive cache            │
└─────────────────────────────────┘
```

### Hive Boxes

```dart
// auth box: stores JWT token, user data
await Hive.openBox('auth');

// reports box: stores draft reports
await Hive.openBox('reports');

// sync_queue box: reports waiting to sync
await Hive.openBox('sync_queue');

// preferences box: user settings
await Hive.openBox('preferences');
```

### SyncService Implementation

```dart
class SyncService {
  final apiService = ApiService();
  final localStorage = LocalStorageService();

  Future<void> syncOfflineData() async {
    final syncQueue = await localStorage.getSyncQueue();

    for (final report in syncQueue) {
      try {
        await apiService.submitReport(report);
        await localStorage.removeSyncQueueItem(report.id);
      } on ApiException {
        // Retry logic: retry up to 3 times with backoff
        await _retryWithBackoff(report);
      }
    }
  }

  Future<void> _retryWithBackoff(CellReport report) async {
    int retries = 0;
    while (retries < 3) {
      try {
        await Future.delayed(Duration(seconds: 2 ^ retries));
        await apiService.submitReport(report);
        await localStorage.removeSyncQueueItem(report.id);
        return;
      } catch (e) {
        retries++;
        if (retries == 3) {
          // Mark as failed, notify user
          await localStorage.markSyncFailed(report.id, e.toString());
        }
      }
    }
  }
}
```

---

## Screens & Navigation

### Navigation Flow

```
Splash/Init
    ↓
┌─────────────────────────────────┐
│ Check if logged in (token)      │
└─────────────────────────────────┘
    ↓ Yes                    ↓ No
┌──────────────┐      ┌──────────────┐
│  AppShell    │      │ LoginScreen  │
│ (Main layout)│      │              │
└──────────────┘      └──────────────┘
    ↓                       ↓
┌──────────────────────────────────────┐
│ BottomNavigation with 5 tabs:        │
│ Home | Reports | Dashboard | Sync... │
└──────────────────────────────────────┘
```

### Screens & Responsibilities

#### 1. **LoginScreen**

- **File**: `lib/screens/auth/login_screen.dart`
- **Purpose**: Authenticate user with phone + PIN
- **State**: Uses `authProvider` to handle login logic
- **Features**:
  - Input validation (phone format, PIN length)
  - Error messaging
  - Loading state during API call
  - Persistent login (token saved in Hive)

#### 2. **HomeScreen**

- **File**: `lib/screens/home/home_screen.dart`
- **Purpose**: Main dashboard with quick actions
- **State**: Displays user info from `authProvider`
- **Features**:
  - User role & cell assignment
  - Quick action buttons (New Report, View History)
  - Sync status indicator
  - Next meeting reminder

#### 3. **ReportFormScreen** (Multi-page)

- **File**: `lib/screens/reports/report_form_screen.dart`
- **Purpose**: Comprehensive cell report submission
- **State**: Uses `reportProvider` for draft management
- **Features**:
  - 4-page form (Page 1-4 as per requirements)
  - Auto-save to Hive as draft
  - Photo attachment support
  - Form validation & error handling
  - Submit button (queues if offline)

#### 4. **ReportHistoryScreen**

- **File**: `lib/screens/reports/report_history_screen.dart`
- **Purpose**: View submitted reports & drafts
- **State**: Uses `FutureProvider` to fetch reports
- **Features**:
  - List of all reports with status
  - Filter by date range
  - Tap to view details or edit draft
  - Sync status per report

#### 5. **ReportDetailScreen**

- **File**: `lib/screens/reports/report_detail_screen.dart`
- **Purpose**: View full report details (read-only or edit draft)
- **State**: Displays single report from `reportProvider`
- **Features**:
  - Display all report fields
  - Edit button (if draft)
  - Delete button (if draft)
  - Share/export functionality

#### 6. **ProfileScreen**

- **File**: `lib/screens/profile/profile_screen.dart`
- **Purpose**: User profile & app settings
- **State**: Displays user from `authProvider`
- **Features**:
  - User info display
  - App settings (notifications, language)
  - Logout button
  - About & version info

#### 7. **DashboardScreen**

- **File**: `lib/screens/dashboard/dashboard_screen.dart`
- **Purpose**: Quick stats & summary (basic mobile version)
- **State**: Fetches from `dashboardProvider`
- **Features**:
  - Attendance stats
  - Last submission date
  - Next meeting info
  - Recent reports preview

### Shared Components

**BottomNavigation** (`lib/screens/shared/bottom_navigation.dart`):

- 5 tabs: Home, Reports, Dashboard, Sync, Profile
- Persists during navigation
- Shows sync indicator on tab

**LoadingOverlay** (`lib/screens/shared/loading_overlay.dart`):

- Modal loading indicator
- Blocks user interaction while loading
- Shows progress message

**AppShell** (`lib/screens/app_shell.dart`):

- Wrapper for authenticated screens
- Includes BottomNavigation
- Handles deep linking

---

## Data Models

### User Model

```dart
class User {
  final String id;
  final String phone;
  final String name;
  final UserRole role;

  // Jurisdiction (scope of access)
  final String? cellId;
  final String? seniorCellId;
  final String? fellowshipId;
  final String? zoneId;

  final bool isActive;

  User({
    required this.id,
    required this.phone,
    required this.name,
    required this.role,
    this.cellId,
    this.seniorCellId,
    this.fellowshipId,
    this.zoneId,
    required this.isActive,
  });

  // Can view data for this scope
  bool canViewCell(String cellId) => this.cellId == cellId || isLeaderOf(cellId);

  // Check role hierarchy
  bool isLeaderOf(String cellId) =>
    role.level <= UserRole.seniorCellLeader.level;

  factory User.fromJson(Map<String, dynamic> json) => User(
    id: json['id'],
    phone: json['phone'],
    name: json['name'],
    role: UserRole.values.byName(json['role']),
    cellId: json['cell_id'],
    seniorCellId: json['senior_cell_id'],
    fellowshipId: json['fellowship_id'],
    zoneId: json['zone_id'],
    isActive: json['is_active'],
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'phone': phone,
    'name': name,
    'role': role.name,
    'cell_id': cellId,
    'senior_cell_id': seniorCellId,
    'fellowship_id': fellowshipId,
    'zone_id': zoneId,
    'is_active': isActive,
  };
}

enum UserRole {
  systemAdmin(level: 1),
  zonalPastor(level: 2),
  zonalAdmin(level: 3),
  fellowshipPastor(level: 4),
  seniorCellLeader(level: 5),
  cellLeader(level: 6);

  final int level;
  const UserRole({required this.level});
}
```

### CellReport Model

```dart
class CellReport {
  final String id;
  final String cellId;
  final String cellName;
  final DateTime? meetingDate;

  // Attendance
  final int attendanceCount;
  final int newMembersCount;
  final int firstTimers;
  final int soulsWon;

  // Finances
  final double tithesGiven;
  final double offeringsGiven;
  final double specialOfferings;

  // Activities (boolean flags)
  final bool praiseWorship;
  final bool wordStudy;
  final bool prayer;

  // Text fields
  final String? testimonies;
  final String? challenges;
  final String? monthlyPlans;

  // Status tracking
  final ReportStatus status;
  final DateTime? submittedAt;
  final DateTime createdAt;

  CellReport({
    required this.id,
    required this.cellId,
    required this.cellName,
    this.meetingDate,
    required this.attendanceCount,
    required this.newMembersCount,
    this.firstTimers = 0,
    this.soulsWon = 0,
    required this.tithesGiven,
    required this.offeringsGiven,
    this.specialOfferings = 0,
    required this.praiseWorship,
    required this.wordStudy,
    required this.prayer,
    this.testimonies,
    this.challenges,
    this.monthlyPlans,
    required this.status,
    this.submittedAt,
    required this.createdAt,
  });

  get totalFinances => tithesGiven + offeringsGiven + specialOfferings;

  bool get isDraft => status == ReportStatus.draft;
  bool get isSubmitted => status == ReportStatus.submitted;
  bool get isLate => status == ReportStatus.late;
  bool get isOverdue => status == ReportStatus.overdue;

  factory CellReport.fromJson(Map<String, dynamic> json) => CellReport(
    id: json['id'],
    cellId: json['cell_id'],
    cellName: json['cell_name'],
    meetingDate: json['meeting_date'] != null
      ? DateTime.parse(json['meeting_date'])
      : null,
    attendanceCount: json['attendance_count'] ?? 0,
    newMembersCount: json['new_members_count'] ?? 0,
    firstTimers: json['first_timers'] ?? 0,
    soulsWon: json['souls_won'] ?? 0,
    tithesGiven: (json['tithes_given'] ?? 0).toDouble(),
    offeringsGiven: (json['offerings_given'] ?? 0).toDouble(),
    specialOfferings: (json['special_offerings'] ?? 0).toDouble(),
    praiseWorship: json['praise_worship'] ?? false,
    wordStudy: json['word_study'] ?? false,
    prayer: json['prayer'] ?? false,
    testimonies: json['testimonies'],
    challenges: json['challenges'],
    monthlyPlans: json['monthly_plans'],
    status: ReportStatus.values.byName(json['status'] ?? 'draft'),
    submittedAt: json['submitted_at'] != null
      ? DateTime.parse(json['submitted_at'])
      : null,
    createdAt: DateTime.parse(json['created_at']),
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'cell_id': cellId,
    'cell_name': cellName,
    'meeting_date': meetingDate?.toIso8601String(),
    'attendance_count': attendanceCount,
    'new_members_count': newMembersCount,
    'first_timers': firstTimers,
    'souls_won': soulsWon,
    'tithes_given': tithesGiven,
    'offerings_given': offeringsGiven,
    'special_offerings': specialOfferings,
    'praise_worship': praiseWorship,
    'word_study': wordStudy,
    'prayer': prayer,
    'testimonies': testimonies,
    'challenges': challenges,
    'monthly_plans': monthlyPlans,
    'status': status.name,
    'submitted_at': submittedAt?.toIso8601String(),
    'created_at': createdAt.toIso8601String(),
  };
}

enum ReportStatus {
  draft,       // Not submitted
  submitted,   // On time
  late,        // > 3 days late
  overdue,     // > 7 days late
}
```

### CellSummary Model

```dart
class CellSummary {
  final String id;
  final String name;
  final String meetingDay;
  final String? meetingTime;
  final String seniorCellId;
  final bool isActive;

  CellSummary({
    required this.id,
    required this.name,
    required this.meetingDay,
    this.meetingTime,
    required this.seniorCellId,
    required this.isActive,
  });

  factory CellSummary.fromJson(Map<String, dynamic> json) => CellSummary(
    id: json['id'],
    name: json['name'],
    meetingDay: json['meeting_day'] ?? 'Monday',
    meetingTime: json['meeting_time'],
    seniorCellId: json['senior_cell_id'],
    isActive: json['is_active'] ?? true,
  );
}
```

---

## Services Layer

### LocalStorageService

```dart
class LocalStorageService {
  // Keys
  static const String _tokenKey = 'token';
  static const String _userKey = 'user';
  static const String _reportsBoxName = 'reports';
  static const String _syncQueueBoxName = 'sync_queue';
  static const String _prefsBoxName = 'preferences';

  // Boxes
  late final Box _authBox;
  late final Box<CellReport> _reportsBox;
  late final Box<String> _syncQueueBox;
  late final Box _prefsBox;

  Future<void> init() async {
    _authBox = await Hive.openBox('auth');
    _reportsBox = await Hive.openBox<CellReport>('reports');
    _syncQueueBox = await Hive.openBox<String>('sync_queue');
    _prefsBox = await Hive.openBox('preferences');
  }

  // Token management
  String? getToken() => _authBox.get(_tokenKey);
  Future<void> saveToken(String token) => _authBox.put(_tokenKey, token);
  Future<void> deleteToken() => _authBox.delete(_tokenKey);

  // User data
  User? getUser() {
    final json = _authBox.get(_userKey);
    return json != null ? User.fromJson(json) : null;
  }
  Future<void> saveUser(User user) => _authBox.put(_userKey, user.toJson());
  Future<void> deleteUser() => _authBox.delete(_userKey);

  // Draft reports
  Future<void> saveDraftReport(CellReport report) =>
    _reportsBox.put(report.id, report);

  CellReport? getDraftReport(String id) => _reportsBox.get(id);

  Future<void> deleteDraftReport(String id) => _reportsBox.delete(id);

  List<CellReport> getAllDrafts() =>
    _reportsBox.values.where((r) => r.isDraft).toList();

  // Sync queue
  Future<void> addToSyncQueue(String reportId) =>
    _syncQueueBox.put(reportId, reportId);

  Future<void> removeFromSyncQueue(String reportId) =>
    _syncQueueBox.delete(reportId);

  List<String> getSyncQueue() => _syncQueueBox.values.toList();

  // Preferences
  Future<void> setPreference(String key, dynamic value) =>
    _prefsBox.put(key, value);

  dynamic getPreference(String key) => _prefsBox.get(key);
}
```

---

## Widget Library

### Custom Components (Reusable)

#### PrimaryButton

```dart
class PrimaryButton extends StatelessWidget {
  final String label;
  final VoidCallback onPressed;
  final bool isLoading;

  const PrimaryButton({
    required this.label,
    required this.onPressed,
    this.isLoading = false,
  });

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: isLoading ? null : onPressed,
      child: isLoading
        ? SizedBox.square(
            dimension: 20,
            child: CircularProgressIndicator(strokeWidth: 2),
          )
        : Text(label),
    );
  }
}
```

#### ReportCard

```dart
class ReportCard extends StatelessWidget {
  final CellReport report;
  final VoidCallback onTap;

  const ReportCard({required this.report, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Card(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(report.cellName, style: Theme.of(context).textTheme.titleMedium),
                  _statusBadge(report.status),
                ],
              ),
              SizedBox(height: 8),
              Text('Attendance: ${report.attendanceCount}'),
              Text('Finances: ${report.totalFinances}'),
            ],
          ),
        ),
      ),
    );
  }

  Widget _statusBadge(ReportStatus status) {
    final color = {
      ReportStatus.draft: Colors.grey,
      ReportStatus.submitted: Colors.green,
      ReportStatus.late: Colors.orange,
      ReportStatus.overdue: Colors.red,
    }[status] ?? Colors.grey;

    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(status.name.toUpperCase(), style: TextStyle(color: Colors.white, fontSize: 12)),
    );
  }
}
```

---

## Build & Deployment

### iOS (TestFlight / App Store)

```bash
# 1. Update version in pubspec.yaml
version: 1.0.0+1

# 2. Build IPA for TestFlight
flutter build ipa --release

# 3. Upload to TestFlight via Xcode or Transporter
# open build/ios/ipa/*.ipa

# 4. For AppStore, submit via App Store Connect
```

### Android (Play Store)

```bash
# 1. Configure signing key (keystore)
# Create keystore if not exists:
keytool -genkey -v -keystore android/app/upload-key.jks \
  -storetype JKS -keyalg RSA -keysize 2048 -validity 10000 \
  -alias upload-key

# 2. Configure android/key.properties
storePassword=...
keyPassword=...
keyAlias=upload-key
storeFile=upload-key.jks

# 3. Build APK/AAB for Play Store
flutter build appbundle --release

# 4. Upload to Play Console
# build/app/outputs/bundle/release/app-release.aab
```

### Web (Firebase Hosting / Netlify)

```bash
# 1. Build web version
flutter build web --release

# 2. Deploy to Firebase Hosting
firebase deploy --only hosting

# Or Netlify
netlify deploy --prod --dir=build/web
```

---

## Testing

### Unit Tests

```bash
flutter test
```

### Widget Tests

```bash
flutter test test/widget_test.dart
```

### Integration Tests

```bash
flutter test integration_test/
```

### Test Coverage

```bash
flutter test --coverage
lcov --list coverage/lcov.info
```

---

## Best Practices

### State Management

- Keep Riverpod providers simple & focused
- Use `select()` to watch only needed fields
- Avoid deeply nested provider dependencies

### Async Operations

- Always handle `AsyncValue.when()` states (data, loading, error)
- Use `.future` when you need to await

### Error Handling

- Create custom exceptions for different error types
- Provide user-friendly error messages
- Log errors for debugging

### Performance

- Use `const` constructors where possible
- Implement lazy loading for lists
- Cache expensive computations

### Code Organization

- One screen per file
- Group related widgets in subdirectories
- Keep models simple (no business logic)

---

## Configuration

### API Configuration (`lib/config/api_config.dart`)

```dart
class ApiConfig {
  static const String baseUrl = 'https://api.cellytics.com';
  static const Duration timeout = Duration(seconds: 30);
  static const bool enableLogging = true;
  static const int maxRetries = 3;
}
```

### App Branding (`lib/config/branding.dart`)

```dart
class AppBranding {
  static const String appName = 'Cellytics';
  static const String appVersion = '1.0.0';
  static const String appDescription = 'Church Cell Management';
}
```

---

## Debugging & Logging

### Flutter DevTools

```bash
flutter pub global activate devtools
devtools
```

### Logcat (Android)

```bash
flutter logs
```

### Console (iOS)

```bash
flutter attach
```

---

## Future Enhancements

- [ ] Offline analytics cache
- [ ] Real-time notifications via WebSocket
- [ ] Photo gallery in report attachments
- [ ] Biometric authentication
- [ ] Dark mode support
- [ ] Multi-language support (FR, PT, etc)
- [ ] Export reports to PDF

---

**Last Updated**: May 15, 2026  
**Version**: 1.0.0  
**Status**: In Development
