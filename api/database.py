"""Database connection and query functions."""
import os
import re
import sqlite3
from typing import List, Optional, Dict, Any
from contextlib import contextmanager


# Database paths configuration
SQL_PATH = "/mnt/db"
if os.path.exists("/db"):
    SQL_PATH = "/db"
elif not os.path.exists("/mnt/db"):
    SQL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db")

DB_PATH = os.environ.get("DB_PATH", os.path.join(SQL_PATH, 'sengoku_bot.db'))
ARCHIVE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'archives')


@contextmanager
def get_db_connection(db_path: Optional[str] = None):
    """Context manager for database connections."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def validate_archive_name(archive_name: str) -> bool:
    """Validate archive name to prevent path traversal attacks."""
    return bool(re.match(r'^[a-z]+_\d{4}$', archive_name))


def get_archive_path(archive_name: str) -> Optional[str]:
    """Get the full path to an archive database file."""
    if not validate_archive_name(archive_name):
        return None
    
    db_path = os.path.join(ARCHIVE_DIR, f"{archive_name}.db")
    if not os.path.exists(db_path):
        return None
    
    return db_path


def get_archives() -> List[Dict[str, str]]:
    """Get list of available archive databases."""
    if not os.path.exists(ARCHIVE_DIR):
        return []
    
    files = [f for f in os.listdir(ARCHIVE_DIR) if f.endswith('.db')]
    archives = []
    
    for f in files:
        base = f[:-3]
        if re.match(r'^[a-z]+_\d{4}$', base):
            parts = base.split('_')
            month, year = parts
            name = f"{month.capitalize()} {year}"
            archives.append({'file': base, 'name': name})
    
    archives.sort(key=lambda x: x['file'], reverse=True)
    return archives


def get_members(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get list of all members with their event counts and payment totals.
    
    Reuses the SQL query from src/app.py lines 106-133.
    """
    query = """
    SELECT
        u.uid,
        COALESCE(NULLIF(u.server_username, ''), u.global_username) AS display_name,
        COALESCE(ev.event_count, 0) AS event_count,
        COALESCE(pay.total_amount, 0) AS total_amount
    FROM USERS u

    LEFT JOIN (
        SELECT
            etu.ds_uid AS uid,
            COUNT(DISTINCT CASE WHEN e.disband != 1 THEN e.message_id END) AS event_count
        FROM EVENTS_TO_USERS etu
        JOIN EVENTS e ON e.message_id = etu.message_id
        GROUP BY etu.ds_uid
    ) ev ON ev.uid = u.uid

    LEFT JOIN (
        SELECT
            ul.ds_uid AS uid,
            ROUND(SUM((p.payment_ammount * 1.0) / NULLIF(p.user_amount * 1.0, 0)), 2) AS total_amount
        FROM PAYMENTS p
        JOIN PAYMENTS_TO_USERS ul ON p.message_id = ul.message_id
        GROUP BY ul.ds_uid
    ) pay ON pay.uid = u.uid

    WHERE COALESCE(NULLIF(u.server_username, ''), u.global_username) != 'D9dka'
    ORDER BY total_amount DESC, event_count DESC, display_name COLLATE NOCASE ASC;
    """
    
    with get_db_connection(db_path) as conn:
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_user(uid: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get user details by UID (accepts string to handle large Discord UIDs)."""
    query = "SELECT uid, COALESCE(NULLIF(global_username, ''), server_username) AS display_name FROM USERS WHERE uid=?"
    
    with get_db_connection(db_path) as conn:
        cursor = conn.execute(query, (int(uid),))  # Convert to int for DB query
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_events(uid: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get all events for a specific user (accepts string to handle large Discord UIDs).
    
    Reuses the SQL query from src/app.py lines 173-179.
    """
    query = """
        SELECT e.message_id, e.guild_id, e.channel_id, e.channel_name, e.message_text, e.read_time, e.disband, e.points, e.hidden
        FROM EVENTS_TO_USERS etu
        JOIN EVENTS e ON e.message_id = etu.message_id
        WHERE etu.ds_uid = ?
        ORDER BY e.message_id DESC
    """
    
    with get_db_connection(db_path) as conn:
        cursor = conn.execute(query, (int(uid),))  # Convert to int for DB query
        rows = cursor.fetchall()
        events = []
        
        for row in rows:
            event = dict(row)
            # Hide sensitive information for hidden events
            if event['hidden']:
                event['channel_name'] = "None"
                event['message_text'] = "А тебя это ебать не должно"
                event['channel_id'] = 0
                event['message_id'] = 0
                event['guild_id'] = 0
            events.append(event)
        
        return events


def get_user_payments(uid: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get all payments for a specific user (accepts string to handle large Discord UIDs).
    
    Reuses the SQL query from src/app.py lines 218-223.
    """
    query = """
        select ROUND((p.payment_ammount * 1.0) / (p.user_amount * 1.0), 2) as payment_sum, p.message_id, p.channel_id, p.guild_id, p.payment_ammount, p.user_amount, p.pay_time
        from PAYMENTS p
        join PAYMENTS_TO_USERS ul on p.message_id = ul.message_id
        where ul.ds_uid = ?
    """
    
    with get_db_connection(db_path) as conn:
        cursor = conn.execute(query, (int(uid),))  # Convert to int for DB query
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
