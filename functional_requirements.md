1. Functional Requirements (MVP Scope)
1.1 MUST HAVE (Core MVP - Weeks 1-4)
FR-1: Authentication & User Management
•	FR-1.1: Admin-created accounts (phone number-based registration, no OTP)
•	FR-1.2: Simple 6-digit PIN login for mobile users
•	FR-1.3: Role-based access control (Cell Leader, Senior Cell Leader, Fellowship Pastor, Zonal Admin)
•	FR-1.4: Admin panel to create users and assign roles/cells
•	FR-1.5: Auto-assign cell meeting day/time during user creation
FR-2: Cell Report Submission (Mobile-First)
•	FR-2.1: Multi-page form mirroring booklet structure
•	FR-2.2: Offline storage using Hive/SQLite
•	FR-2.3: Auto-fill cell name, leader name, date
•	FR-2.4: Form validation (required fields, numeric constraints)
•	FR-2.5: Save draft functionality
•	FR-2.6: Auto-sync when online (background sync)
•	FR-2.7: Submission confirmation with timestamp
•	FR-2.8: View own report history
•	FR-2.9: Attach 1-2 photos per report for visual confirmation (stored on free-tier storage like Appwrite bucket)
Fields (from booklet) - Page 1 - Meeting Details: - meeting_date: date (auto-filled) - bible_class_teachers: array[4] of strings - meeting_week: enum[Week 1-4] - meeting_type: enum[Bible Study, Prayer Meeting, Evangelism, Planning] - meeting_duration: integer (minutes) - Activities (each duration + handler): prayers, praise_worship, testimonies, special_presentations, rhapsody_reading, bible_study, planning, offerings, announcements - Attendance: first_timers, number_saved, filled_holy_ghost, total_attendance, new_members, souls_retained, souls_won, souls_on_tracker
•	Page 2 - Finances & Text:
o	Finances: oblation, offerings, tithes, thanksgiving, seed, partnership, first_fruits, total (auto-calculated), collected_by
o	Long-form text: testimonies, monthly_plans, challenges
•	Page 3 - Soul Winning Records:
o	soul_winning_records: array of objects with name, phone, is_first_timer, follow_up_date, response
•	Page 4 - Pastor’s Section:
o	pastors_remarks: text (filled by pastor)
o	other_info: text
FR-3: Dashboards (Web-First - Flutter Web)
•	FR-3.1: Cell Leader Dashboard (Mobile & Web)
o	View own submitted reports
o	See submission status (Submitted, Draft, Late)
o	Edit draft reports
o	Next meeting day/time reminder
•	FR-3.2: Senior Cell Leader Dashboard
o	List all cells under supervision
o	Submission status per cell
o	Aggregated stats: total attendance, souls won, cells reported
o	Click cell to view individual report
o	Filter by date range
•	FR-3.3: Fellowship Pastor Dashboard
o	List all senior cells in fellowship
o	Submission rate: X/Y cells reported
o	Aggregated stats: total attendance, souls won, total finances, first-timers
o	List of cells needing attention (no report >7 days, declining attendance >20%)
o	View any cell report
o	Export weekly report (CSV/PDF)
•	FR-3.4: Zonal Admin Dashboard
o	List all fellowships
o	Submission rate per fellowship
o	Zone-wide aggregated stats
o	Identify struggling fellowships (submission rate <70%)
o	Trend chart: attendance over last 8 weeks
o	Export zone report (CSV)
FR-4: Data Synchronization
•	Offline queue for submissions
•	Background sync when online
•	Conflict resolution: last write wins
•	Sync status indicator
•	Retry failed syncs automatically (3 attempts)
FR-5: Notifications (Post-MVP)
•	FCM push notifications via backend (FastAPI + Firebase)
•	Manual reminder: Senior Cell Leader can nudge cell leader
•	Badge count for unread notifications
FR-6: Reporting & Analytics
•	Export individual cell report as PDF
•	Export fellowship weekly summary as PDF
•	Basic trend charts (line chart for attendance)
❌ Won’t Have (MVP)
•	Individual member attendance tracking
•	WhatsApp/SMS auto-reminders
•	Multi-language support
•	Advanced predictive analytics
•	Pastor’s remarks editable by cell leaders
1.2 Non-Functional Requirements
NFR	Requirement	Target	How to Measure
Performance	Dashboard load time	< 3 sec on 3G	Lighthouse/manual testing
Performance	Report submission	< 2 sec	Backend logging
Performance	Offline form responsiveness	< 100ms	Flutter DevTools
Scalability	Concurrent users	100 users (Zone B)	Load testing
Scalability	Database growth	10,000 reports/year	PostgreSQL monitoring
Reliability	Uptime	99% (7 hrs downtime/month)	Render monitoring
Reliability	Data sync success rate	99%+	Sync failure logs
Security	Authentication	PIN + JWT tokens	Security audit
Security	Data encryption	HTTPS + encrypted DB	SSL verification
Usability	Mobile form completion time	< 5 minutes	User testing
Usability	Dashboard learning curve	< 15 minutes	User feedback
Cost	Monthly hosting	< $15/month	Billing dashboard
2. System Architecture
2.1 High-Level Architecture Diagram
MOBILE USERS (Cell Leaders/Senior Leaders) -- Flutter Mobile App
  - Offline-first forms, Hive local storage, Background sync
        |
        | HTTPS/REST API
        ▼
WEB USERS (Fellowship Pastors/Zonal Admin) -- Flutter Web
        |
        ▼
BACKEND - FastAPI (Render)
  - Authentication (PIN + JWT)
  - Business Logic
  - Data Aggregation
  - Sync Management
        |
        ▼
DATABASE - PostgreSQL (Neon)
  - Users, Cells, Reports, Sync Queue

PHOTO STORAGE - Free-tier bucket (e.g., Appwrite)
Data Flow: 1. Cell Leader fills report offline → saved locally 2. Taps Submit → queued if offline, auto-sync when online 3. Backend validates → Postgres stores data 4. Dashboard fetches aggregated stats for web users 5. FCM pushes notifications for reminders (optional post-MVP)
________________________________________
Document prepared as functional requirements & MVP blueprint for BLW Zone B Cell Reporting System