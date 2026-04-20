from datetime import datetime, date, timedelta
 
 
def calculate_week_boundaries(meeting_date: date) -> tuple:
    """Calculate week start (Monday), end (Sunday), and deadline (Sunday 9am)"""
    day_of_week = meeting_date.weekday()
    week_start = meeting_date - timedelta(days=day_of_week)
    week_end = week_start + timedelta(days=6)
    deadline = datetime.combine(week_end, datetime.min.time()).replace(hour=9, minute=0, second=0)
    return week_start, week_end, deadline
 
 
def get_current_week() -> tuple:
    """Get current week's Monday and Sunday"""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday
 
 