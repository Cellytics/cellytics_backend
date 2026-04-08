# fcm_service.py - Firebase Cloud Messaging Integration

import os
import logging
from typing import List, Optional, Dict, Any
import firebase_admin
from firebase_admin import credentials, messaging
from datetime import datetime

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# FIREBASE SETUP
# ═══════════════════════════════════════════════════════════════════════════════

# Initialize Firebase (requires FIREBASE_CREDENTIALS_JSON env var or firebase-adminsdk file)
def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Try to get credentials from environment variable
        credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
        
        if credentials_json:
            # If JSON string is provided, write to temp file
            import json
            import tempfile
            
            creds_dict = json.loads(credentials_json)
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                json.dump(creds_dict, f)
                creds_path = f.name
            
            cred = credentials.Certificate(creds_path)
        else:
            # Try to use default Firebase credentials file
            cred = credentials.Certificate("firebase-adminsdk.json")
        
        firebase_admin.initialize_app(cred)
        logger.info("✅ Firebase initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Firebase initialization failed: {e}")
        logger.warning("⚠️  FCM notifications will be disabled. Set up Firebase to enable.")
        return False


# Try to initialize on import
FIREBASE_ENABLED = False
try:
    FIREBASE_ENABLED = init_firebase()
except Exception as e:
    logger.warning(f"Firebase not available: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# FCM SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class FCMService:
    """Firebase Cloud Messaging Service"""
    
    @staticmethod
    async def send_to_user(
        fcm_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        notification_type: str = "general"
    ) -> bool:
        """
        Send notification to a single user via FCM
        
        Args:
            fcm_token: User's FCM device token
            title: Notification title
            body: Notification body
            data: Custom data dict
            notification_type: Type of notification (for analytics)
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not FIREBASE_ENABLED or not fcm_token:
            logger.warning(f"FCM disabled or no token provided")
            return False
        
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=fcm_token,
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        sound="default",
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound="default",
                            alert=messaging.ApsAlert(
                                title=title,
                                body=body,
                            ),
                        ),
                    ),
                ),
            )
            
            response = messaging.send(message)
            logger.info(f"✅ FCM sent to {fcm_token[:20]}...: {response}")
            return True
            
        except Exception as e:
            logger.error(f"❌ FCM send failed: {e}")
            return False
    
    @staticmethod
    async def send_to_multiple(
        fcm_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, bool]:
        """
        Send notification to multiple users
        
        Returns:
            Dict mapping token -> success boolean
        """
        results = {}
        for token in fcm_tokens:
            success = await FCMService.send_to_user(token, title, body, data)
            results[token] = success
        return results


# ═══════════════════════════════════════════════════════════════════════════════
# NOTIFICATION TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

class NotificationTemplates:
    """Pre-defined notification messages"""
    
    @staticmethod
    def submission_reminder(cell_name: str, days_until_deadline: int) -> tuple:
        """Remind cell leader to submit report"""
        title = "Cell Report Due"
        body = f"{cell_name}: Please submit your report. {days_until_deadline} day(s) left!"
        return title, body
    
    @staticmethod
    def overdue_alert(cell_name: str) -> tuple:
        """Alert that report is overdue"""
        title = "Report Overdue ⚠️"
        body = f"{cell_name}: Your cell report is now overdue. Please submit immediately."
        return title, body
    
    @staticmethod
    def late_alert(cell_name: str) -> tuple:
        """Alert that report was submitted late"""
        title = "Late Submission"
        body = f"{cell_name}: Report submitted after deadline."
        return title, body
    
    @staticmethod
    def manual_nudge(message: str) -> tuple:
        """Custom message from pastor"""
        title = "Message from Leadership"
        body = message
        return title, body
    
    @staticmethod
    def new_cell_report(cell_name: str, submitted_by: str) -> tuple:
        """Alert pastor of new report submission"""
        title = "New Report Submitted"
        body = f"{cell_name} report submitted by {submitted_by}"
        return title, body


# ═══════════════════════════════════════════════════════════════════════════════
# NOTIFICATION SCHEDULER (for use with APScheduler)
# ═══════════════════════════════════════════════════════════════════════════════

async def send_submission_reminders(session):
    """
    Scheduled job: Send reminders on Thursday (4 days before deadline)
    Called by APScheduler
    """
    from sqlalchemy import select
    from models import User, Cell
    from datetime import date, timedelta
    
    try:
        # Find all cells with reports due this week
        today = date.today()
        sunday = today + timedelta(days=(6 - today.weekday()))
        
        # Get all active cells
        result = await session.execute(select(Cell).where(Cell.is_active == True))
        cells = result.scalars().all()
        
        sent_count = 0
        
        for cell in cells:
            # Get cell leader
            leader = cell.leader
            if leader and leader.fcm_token:
                title, body = NotificationTemplates.submission_reminder(
                    cell.name,
                    days_until_deadline=3
                )
                success = await FCMService.send_to_user(
                    leader.fcm_token,
                    title,
                    body,
                    data={"cell_id": str(cell.id), "type": "reminder"},
                    notification_type="submission_reminder"
                )
                if success:
                    sent_count += 1
        
        logger.info(f"✅ Sent {sent_count} submission reminders")
        return sent_count
        
    except Exception as e:
        logger.error(f"❌ Error sending reminders: {e}")
        return 0


async def mark_overdue_and_notify(session):
    """
    Scheduled job: Mark reports overdue and send alerts
    Called every Sunday 9:05 AM by APScheduler
    """
    from sqlalchemy import select, and_
    from models import CellReport, User, Notification
    from datetime import datetime
    
    try:
        now = datetime.utcnow()
        
        # Find all draft reports past deadline
        result = await session.execute(
            select(CellReport).where(
                and_(
                    CellReport.status.in_(["draft", "submitted"]),
                    CellReport.submission_deadline < now
                )
            )
        )
        overdue_reports = result.scalars().all()
        
        updated_count = 0
        notified_count = 0
        
        for report in overdue_reports:
            # Mark as overdue
            report.status = "overdue"
            updated_count += 1
            
            # Get cell leader
            cell = report.cell
            if cell and cell.leader and cell.leader.fcm_token:
                title, body = NotificationTemplates.overdue_alert(cell.name)
                success = await FCMService.send_to_user(
                    cell.leader.fcm_token,
                    title,
                    body,
                    data={"report_id": str(report.id), "type": "overdue"},
                    notification_type="overdue_alert"
                )
                if success:
                    notified_count += 1
                
                # Create in-app notification
                notification = Notification(
                    user_id=cell.leader.id,
                    message=f"Your {cell.name} report is overdue",
                    type="overdue_alert",
                    fcm_token=cell.leader.fcm_token,
                    is_sent=success,
                )
                session.add(notification)
        
        await session.commit()
        logger.info(f"✅ Marked {updated_count} reports overdue, notified {notified_count} leaders")
        return updated_count
        
    except Exception as e:
        logger.error(f"❌ Error marking overdue: {e}")
        return 0


# ═══════════════════════════════════════════════════════════════════════════════
# SETUP INSTRUCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

"""
HOW TO SET UP FCM:

1. Create Firebase Project:
   - Go to https://console.firebase.google.com
   - Create new project
   - Enable Cloud Messaging

2. Get Service Account Key:
   - Go to Project Settings > Service Accounts
   - Click "Generate New Private Key"
   - Download JSON file as firebase-adminsdk.json

3. Add to your project:
   Option A: Place file in project root
   Option B: Set environment variable:
   
   export FIREBASE_CREDENTIALS_JSON='{"type":"service_account",...}'

4. Add to requirements.txt:
   firebase-admin==6.2.0

5. Enable FCM in mobile app:
   - Initialize Firebase in Flutter
   - Request notification permissions
   - Get device FCM token on login
   - Send to backend: POST /api/users/fcm-token

6. Test:
   - Login to app
   - Trigger a notification event
   - Check if you receive notification on device
"""