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


def _ensure_pov_columns(conn: sqlite3.Connection) -> None:
    """Add pov_count, checked_pov_count, last_pov, last_checked_pov to USERS if missing (migration)."""
    cursor = conn.execute("PRAGMA table_info(USERS)")
    columns = [row[1] for row in cursor.fetchall()]
    if "pov_count" not in columns:
        conn.execute("ALTER TABLE USERS ADD COLUMN pov_count INTEGER DEFAULT 0")
        conn.commit()
    if "checked_pov_count" not in columns:
        conn.execute("ALTER TABLE USERS ADD COLUMN checked_pov_count INTEGER DEFAULT 0")
        conn.commit()
    if "last_pov" not in columns:
        conn.execute("ALTER TABLE USERS ADD COLUMN last_pov TEXT")
        conn.commit()
    if "last_checked_pov" not in columns:
        conn.execute("ALTER TABLE USERS ADD COLUMN last_checked_pov TEXT")
        conn.commit()


@contextmanager
def get_db_connection(db_path: Optional[str] = None):
    """Context manager for database connections."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        _ensure_pov_columns(conn)
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
        COALESCE(pay.total_amount, 0) AS total_amount,
        COALESCE(u.pov_count, 0) AS pov_count,
        COALESCE(u.checked_pov_count, 0) AS checked_pov_count,
        u.last_pov,
        u.last_checked_pov
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
    query = """SELECT uid, COALESCE(NULLIF(global_username, ''), server_username) AS display_name,
                COALESCE(pov_count, 0) AS pov_count, COALESCE(checked_pov_count, 0) AS checked_pov_count,
                last_pov, last_checked_pov
                FROM USERS WHERE uid=?"""
    
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


def get_levels_and_achievements(db_path: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all BP levels and all achievements from the main database (read-only).
    Returns {"levels": [{"level": int, "attendance": int}, ...], "achievements": [{"id": int, "bp_level": int, "description": str, "picture": str}, ...]}.
    """
    levels_query = "SELECT level, attendence FROM BP_LEVELS ORDER BY level ASC"
    achievements_query = (
        "SELECT id, bp_level, description, picture FROM ACHIVEMENTS ORDER BY bp_level ASC, id ASC"
    )
    with get_db_connection(db_path) as conn:
        cursor = conn.execute(levels_query)
        levels = [{"level": row[0], "attendance": row[1]} for row in cursor.fetchall()]
        cursor = conn.execute(achievements_query)
        achievements = [
            {"id": row[0], "bp_level": row[1], "description": row[2] or "", "picture": row[3] or ""}
            for row in cursor.fetchall()
        ]
    return {"levels": levels, "achievements": achievements}


def get_user_achievements(uid: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get all achievements granted to a user (from ACHIVEMENTS_TO_USERS + ACHIVEMENTS). Read-only.
    Returns list of {"id": int, "bp_level": int, "description": str, "picture": str}.
    """
    query = """
        SELECT a.id, a.bp_level, a.description, a.picture
        FROM ACHIVEMENTS a
        JOIN ACHIVEMENTS_TO_USERS atu ON atu.achivement_id = a.id
        WHERE atu.ds_uid = ?
        ORDER BY a.bp_level ASC, a.id ASC
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.execute(query, (int(uid),))
        rows = cursor.fetchall()
        return [
            {"id": row[0], "bp_level": row[1], "description": row[2] or "", "picture": row[3] or ""}
            for row in rows
        ]
