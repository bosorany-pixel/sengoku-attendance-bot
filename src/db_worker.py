import sqlite3
import datetime
import src.datatypes as datatypes
import os
import pandas as pd

sql_path = "/mnt/db"
if os.path.exists("/db"):
    sql_path = "/db"
elif not os.path.exists("/mnt/db"):
    sql_path = os.path.dirname(os.path.abspath(__file__))


class DBWorker:
    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db_path = os.environ.get("DB_PATH") or os.path.join(sql_path, "sengoku_bot.db")
        self._db_path = db_path
        print(f"connected to db on {db_path}")
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS USERS (
    uid INTEGER PRIMARY KEY,
    server_username TEXT,
    global_username TEXT,
    liable INTEGER,
    visible INTEGER,
    timeout DATETIME,
    need_to_get INTEGER DEFAULT 45,
    is_member INTEGER DEFAULT 1,
    join_date DATETIME,
    roles TEXT
);
        ''')
        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS EVENTS_TO_USERS (
    ds_uid INTEGER,
    message_id INTEGER,
    PRIMARY KEY (ds_uid, message_id),
    FOREIGN KEY (ds_uid) REFERENCES USERS(uid),
    FOREIGN KEY (message_id) REFERENCES EVENTS(message_id)
);
        ''')
        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS EVENTS (
    message_id INTEGER PRIMARY KEY,
    author_user_id INTEGER,
    message_text TEXT,
    disband INTEGER,
    read_time DATETIME,
    channel_id INTEGER,
    channel_name TEXT,
    guild_id INTEGER,
    points INTEGER DEFAULT 0,
    hidden INTEGER DEFAULT 0,
    usefull_event INTEGER DEFAULT 0,
    FOREIGN KEY (author_user_id) REFERENCES USERS(uid)
);
        ''')
        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS BRANCH_MESSAGES (
    message_id INTEGER PRIMARY KEY,
    parent_message_id INTEGER,
    message_text TEXT,
    read_time DATETIME,
    FOREIGN KEY (parent_message_id) REFERENCES EVENTS(message_id)
);
''')
        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS PAYMENTS (
    payment_ammount REAL,
    message_id INTEGER PRIMARY KEY,
    channel_id INTEGER,
    guild_id INTEGER,
    pay_time DATETIME,
    user_amount INTEGER DEFAULT 0
)
''')
        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS ACHIVEMENTS (
    id INTEGER PRIMARY KEY,
    bp_level INTEGER,
    description TEXT,
    picture TEXT DEFAULT ''
)
''')
        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS BP_LEVELS (
    attendence INTEGER,
    level INTEGER
)
''')
        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS ACHIVEMENTS_TO_USERS (
    ds_uid INTEGER,
    achivement_id INTEGER,
    created DATETIME,
    taken INTEGER default 1,
    PRIMARY KEY (ds_uid, achivement_id),
    FOREIGN KEY (ds_uid) REFERENCES USERS(uid),
    FOREIGN KEY (achivement_id) REFERENCES ACHIVEMENTS(id)
);
        ''')
        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS PAYMENTS_TO_USERS (
    ds_uid INTEGER,
    message_id INTEGER,
    PRIMARY KEY (ds_uid, message_id),
    FOREIGN KEY (ds_uid) REFERENCES USERS(uid),
    FOREIGN KEY (message_id) REFERENCES PAYMENTS(message_id)
)
''')
        self._ensure_pov_columns()

    def _ensure_pov_columns(self):
        """Add pov_count, checked_pov_count, last_pov, last_checked_pov to USERS if missing (migration)."""
        self.cursor.execute("PRAGMA table_info(USERS)")
        columns = [row[1] for row in self.cursor.fetchall()]
        if "pov_count" not in columns:
            self.cursor.execute("ALTER TABLE USERS ADD COLUMN pov_count INTEGER DEFAULT 0")
            self.conn.commit()
        if "checked_pov_count" not in columns:
            self.cursor.execute("ALTER TABLE USERS ADD COLUMN checked_pov_count INTEGER DEFAULT 0")
            self.conn.commit()
        if "last_pov" not in columns:
            self.cursor.execute("ALTER TABLE USERS ADD COLUMN last_pov TEXT")
            self.conn.commit()
        if "last_checked_pov" not in columns:
            self.cursor.execute("ALTER TABLE USERS ADD COLUMN last_checked_pov TEXT")
            self.conn.commit()

    def execute(self, query: str, params: tuple = (), commit: bool = False):
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
        except sqlite3.OperationalError as e:
            if "readonly" in str(e).lower() or "attempt to write" in str(e).lower():
                raise sqlite3.OperationalError(
                    f"Database is read-only (path: {self._db_path}). "
                    "Check write permissions or set DB_PATH to a writable path."
                ) from e
            raise
        return self.cursor

    def fetchall(self, query: str, params: tuple = ()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def fetchone(self, query: str, params: tuple = ()):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def close(self):
        self.conn.close()

    def get_user_info(self) -> list[datatypes.User]:
        data = self.cursor.execute("""
      SELECT u.uid,
           COALESCE(NULLIF(u.server_username, ''), u.global_username) AS display_name,
           u.liable,
           COUNT(DISTINCT CASE WHEN e.disband != 1 THEN e.message_id END) AS event_count,
           COALESCE(SUM(CASE WHEN e.disband != 1 THEN e.points ELSE 0 END), 0) AS total_points,
           u.need_to_get,
           u.is_member
      FROM USERS u
      LEFT JOIN EVENTS_TO_USERS etu ON etu.ds_uid = u.uid
      LEFT JOIN EVENTS e ON e.message_id = etu.message_id
      WHERE COALESCE(NULLIF(u.server_username, ''), u.global_username) != 'D9dka'
      GROUP BY u.uid
      ORDER BY total_points DESC, event_count DESC, display_name COLLATE NOCASE ASC
    """)
        return data.fetchall()
    
    def load_database_as_dataframe(self) -> pd.DataFrame:
        data = self.get_user_info()
        columns = ['uid', 'display_name', 'liable', 'event_count', 'total_points', 'need_to_get', 'is_member']
        df = pd.DataFrame(data, columns=columns)
        return df

    def add_user(self, user: datatypes.User):
        row = self.fetchone(
            "SELECT pov_count, checked_pov_count, last_pov, last_checked_pov FROM USERS WHERE uid = ?",
            (user.uuid,),
        )
        pov_count = checked_pov_count = 0
        last_pov = last_checked_pov = None
        if row is not None and len(row) >= 2:
            pov_count = row[0] if row[0] is not None else 0
            checked_pov_count = row[1] if row[1] is not None else 0
            if len(row) >= 4:
                last_pov = row[2]
                last_checked_pov = row[3]
        self.execute('''
INSERT OR REPLACE INTO USERS (
                     uid,
                     server_username,
                     global_username,
                     liable,
                     visible,
                     timeout,
                     need_to_get,
                     is_member,
                     join_date,
                     roles,
                     pov_count,
                     checked_pov_count,
                     last_pov,
                     last_checked_pov
                    )
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
        user.uuid,
        user.server_username,
        user.global_username,
        user.liable,
        user.visible,
        user.timeout.isoformat() if user.timeout else None,
        user.need_to_get,
        user.is_member,
        user.join_date.isoformat() if user.join_date else None,
        user.roles,
        pov_count,
        checked_pov_count,
        last_pov,
        last_checked_pov,
    ))

    def update_pov_counts(
        self,
        uid: int,
        pov_count: int,
        checked_pov_count: int,
        last_pov: str | None = None,
        last_checked_pov: str | None = None,
    ) -> None:
        """Set pov_count, checked_pov_count, last_pov, last_checked_pov for a user (used by POV collector)."""
        self.execute(
            """UPDATE USERS SET pov_count = ?, checked_pov_count = ?,
               last_pov = CASE WHEN ? IS NOT NULL AND (last_pov IS NULL OR ? > last_pov) THEN ? ELSE last_pov END,
               last_checked_pov = CASE WHEN ? IS NOT NULL AND (last_checked_pov IS NULL OR ? > last_checked_pov) THEN ? ELSE last_checked_pov END
               WHERE uid = ?""",
            (
                pov_count,
                checked_pov_count,
                last_pov,
                last_pov,
                last_pov,
                last_checked_pov,
                last_checked_pov,
                last_checked_pov,
                uid,
            ),
        )

    def ensure_user_for_pov(self, uid: int, display_name: str) -> None:
        """Ensure USERS has a row for this uid (for POV collector); preserve existing pov counts."""
        row = self.fetchone("SELECT uid FROM USERS WHERE uid = ?", (uid,))
        if row is not None:
            return
        self.cursor.execute("PRAGMA table_info(USERS)")
        columns = [r[1] for r in self.cursor.fetchall()]
        has_last = "last_pov" in columns
        if has_last:
            self.execute(
                """INSERT INTO USERS (uid, server_username, global_username, liable, visible, timeout, need_to_get, is_member, join_date, roles, pov_count, checked_pov_count, last_pov, last_checked_pov)
                   VALUES (?, ?, '', 0, 0, NULL, 45, 1, NULL, NULL, 0, 0, NULL, NULL)""",
                (uid, display_name or str(uid)),
            )
        else:
            self.execute(
                """INSERT INTO USERS (uid, server_username, global_username, liable, visible, timeout, need_to_get, is_member, join_date, roles, pov_count, checked_pov_count)
                   VALUES (?, ?, '', 0, 0, NULL, 45, 1, NULL, NULL, 0, 0)""",
                (uid, display_name or str(uid)),
            )
        
    def add_branch_message(self, branch_message: datatypes.BranchMessage, parent_message_id: int):
        self.execute('''
INSERT OR REPLACE INTO BRANCH_MESSAGES (message_id, parent_message_id, message_text, read_time)
VALUES (?, ?, ?, ?)
''', (branch_message.message_id, parent_message_id, branch_message.message_text, branch_message.read_time.isoformat() if branch_message.read_time else None))
        
    def add_event_user_link(self, user_id: int, message_id: int):
        self.execute('''
INSERT OR REPLACE INTO EVENTS_TO_USERS (ds_uid, message_id)
VALUES (?, ?)
''', (user_id, message_id))

    def add_event(self, event: datatypes.Event):
        self.add_user(event.author)
        self.execute('''
INSERT OR REPLACE INTO EVENTS (message_id, author_user_id, message_text, disband, read_time, channel_id, channel_name, guild_id, points, hidden, usefull_event)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
        event.message_id,
        event.author.uuid,
        event.message_text,
        event.disband,
        event.read_time.isoformat() if event.read_time else None,
        event.channel_id,
        event.channel_name,
        event.guild_id,
        event.points,
        1 if event.hidden else 0,
        1 if event.usefull_event else 0
        ))
        for mu in event.mentioned_users:
            self.add_user(mu)
        for bm in event.branch_messages:
            self.add_branch_message(bm, event.message_id)
        for mu in event.mentioned_users:
            self.add_event_user_link(mu.uuid, event.message_id)

    def get_user(self, uid: int) -> datatypes.User | None:
        row = self.fetchone('SELECT * FROM USERS WHERE uid=?', (uid,))
        if row:
            return datatypes.User(
                uuid=row[0],
                server_username=row[1],
                global_username=row[2],
                liable=row[3],
                visible=row[4],
                timeout=row[5]
            )
        return None

    def get_uid_by_name(self, server_name: str) -> datatypes.User | None:
        """
        Get user ID by server name using exact matching only.
        
        Strategy:
        1. Skip very short queries (likely OCR noise like "95")
        2. Try exact match first
        3. Try case-insensitive exact match
        
        This prevents false positives from substring matches.
        For OCR use case, exact matching is safer than fuzzy matching
        to avoid false positives like "95" matching "charlatan95".
        """
        # Strip whitespace
        server_name = server_name.strip()
        
        # Skip very short queries (likely OCR noise like "95", "D9", etc.)
        if len(server_name) < 3:
            return None
        
        # Strategy 1: Exact match (fastest, most accurate)
        uid = self.fetchone(
            "SELECT uid FROM USERS WHERE server_username = ?",
            (server_name,)
        )
        if uid:
            return uid[0]
        
        # Strategy 2: Case-insensitive exact match
        uid = self.fetchone(
            "SELECT uid FROM USERS WHERE LOWER(server_username) = LOWER(?)",
            (server_name,)
        )
        if uid:
            return uid[0]
        
        # No fuzzy matching - exact match only for payment system
        # This is intentionally strict to prevent false positives
        return None

    def get_server_names(self) -> list[str]:
        rows = self.fetchall(
            "select server_username from USERS where server_username != ''"
        )
        return [row[0] for row in rows]

    def add_payment(self, payment: datatypes.Payment) -> None:
        self.execute("""
INSERT OR REPLACE INTO PAYMENTS (payment_ammount, message_id, channel_id, guild_id, pay_time)
VALUES (?, ?, ?, ?, ?)
""", (
        payment.payment_ammount,
        payment.message_id,
        payment.channel_id,
        payment.guild_id,
        payment.pay_time
    ))
        
    def link_user_to_payment(self, uid, payment_id) -> None:
        """
        Link a user to a payment. Only increments user_amount if a new link is created.
        Uses INSERT OR IGNORE to prevent duplicate entries.
        """
        cursor = self.execute('''
INSERT OR IGNORE INTO PAYMENTS_TO_USERS (ds_uid, message_id)
VALUES (?, ?)
''', (uid, payment_id))
        
        # Only increment user_amount if a new row was actually inserted
        if cursor.rowcount > 0:
            self.execute('UPDATE PAYMENTS SET user_amount = user_amount + 1 WHERE message_id = ?', (payment_id,))

    def get_balance(self, uid) -> float:
        rows = self.fetchall(
            """
            select (p.payment_ammount * 1.0) / (p.user_amount * 1.0)
            from PAYMENTS p
            join PAYMENTS_TO_USERS ul on p.message_id = ul.message_id
            where ul.ds_uid = ?
            """,
            (uid,)
        )
        print(rows)
        return round(sum(row[0] for row in rows if row[0] is not None), 3)


    def get_top_users(self, top_n: int) -> list[tuple]:
        return self.fetchall(
            """
            SELECT
                COALESCE(NULLIF(u.server_username, ''), u.global_username) AS display_name,
                SUM((p.payment_ammount * 1.0) / NULLIF(p.user_amount * 1.0, 0)) AS total_amount
            FROM PAYMENTS p
            JOIN PAYMENTS_TO_USERS ul ON p.message_id = ul.message_id
            JOIN USERS u ON u.uid = ul.ds_uid
            GROUP BY u.uid, display_name
            ORDER BY total_amount DESC
            LIMIT ?
            """,
            (top_n,),
        )

    # --- BP_LEVELS and ACHIVEMENTS (modular, no changes to existing code) ---

    def get_bp_levels(self) -> list[tuple]:
        """Return list of (level, attendance) ordered by level."""
        return self.fetchall(
            "SELECT level, attendence FROM BP_LEVELS ORDER BY level ASC",
            (),
        )

    def get_all_achievements(self) -> list[tuple]:
        """Return list of (id, bp_level, description, picture)."""
        return self.fetchall(
            "SELECT id, bp_level, description, picture FROM ACHIVEMENTS ORDER BY bp_level ASC, id ASC",
            (),
        )

    def get_achievement_by_level(self, level: int) -> tuple | None:
        """Return (id, bp_level, description, picture) for achievement at this level or None."""
        row = self.fetchone(
            "SELECT id, bp_level, description, picture FROM ACHIVEMENTS WHERE bp_level = ? LIMIT 1",
            (level,),
        )
        return row if row else None

    def get_achievement_by_id(self, achivement_id: int) -> tuple | None:
        """Return (id, bp_level, description, picture) or None."""
        row = self.fetchone(
            "SELECT id, bp_level, description, picture FROM ACHIVEMENTS WHERE id = ?",
            (achivement_id,),
        )
        return row if row else None

    def get_user_achievement_ids(self, uid: int) -> list[int]:
        """Return list of achievement ids currently granted to the user."""
        rows = self.fetchall(
            "SELECT achivement_id FROM ACHIVEMENTS_TO_USERS WHERE ds_uid = ?",
            (uid,),
        )
        return [r[0] for r in rows]

    def set_level_attendance(self, level: int, attendance: int) -> None:
        """Set or update attendance threshold for a level. Creates row if level missing."""
        self.cursor.execute(
            "UPDATE BP_LEVELS SET attendence = ? WHERE level = ?",
            (attendance, level),
        )
        self.conn.commit()
        if self.cursor.rowcount == 0:
            self.execute(
                "INSERT INTO BP_LEVELS (attendence, level) VALUES (?, ?)",
                (attendance, level),
                commit=True,
            )

    def set_achievement_for_level(self, level: int, description: str, picture: str = "") -> None:
        """Create or update the achievement for this bp_level (single achievement per level)."""
        row = self.get_achievement_by_level(level)
        if row:
            self.execute(
                "UPDATE ACHIVEMENTS SET description = ?, picture = ? WHERE id = ?",
                (description, picture or "", row[0]),
                commit=True,
            )
        else:
            self.execute(
                "INSERT INTO ACHIVEMENTS (bp_level, description, picture) VALUES (?, ?, ?)",
                (level, description, picture or ""),
                commit=True,
            )

    def create_achievement(self, bp_level: int, description: str, picture: str = "") -> int:
        """Insert a new achievement. Returns new id."""
        self.cursor.execute(
            "INSERT INTO ACHIVEMENTS (bp_level, description, picture) VALUES (?, ?, ?)",
            (bp_level, description, picture or ""),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def update_achievement(
        self, achivement_id: int, bp_level: int, description: str, picture: str = ""
    ) -> bool:
        """Update existing achievement. Returns True if a row was updated."""
        self.cursor.execute(
            "UPDATE ACHIVEMENTS SET bp_level = ?, description = ?, picture = ? WHERE id = ?",
            (bp_level, description, picture or "", achivement_id),
        )
        self.conn.commit()
        return self.cursor.rowcount > 0

    def delete_achievement(self, achivement_id: int) -> bool:
        """Delete achievement by id. Returns True if a row was deleted."""
        self.cursor.execute("DELETE FROM ACHIVEMENTS WHERE id = ?", (achivement_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def _get_user_attendance(self, uid: int) -> int:
        """Count user's attendance: distinct non-disbanded events they participated in."""
        row = self.fetchone(
            """
            SELECT COUNT(DISTINCT etu.message_id)
            FROM EVENTS_TO_USERS etu
            JOIN EVENTS e ON e.message_id = etu.message_id
            WHERE etu.ds_uid = ? AND (e.disband IS NULL OR e.disband != 1)
            """,
            (uid,),
        )
        return row[0] if row else 0

    def calculate_user_achivements(self, uid: int) -> list[tuple]:
        """
        Calculate user's level from attendance, sync ACHIVEMENTS_TO_USERS with all
        achievements they should have, and return those achievements.
        Returns list of (id, bp_level, description, picture) for the user.
        """
        attendance = self._get_user_attendance(uid)
        levels = self.get_bp_levels()
        levels_reached = sorted(set(lev for lev, thresh in levels if attendance >= thresh))
        if not levels_reached:
            return []

        placeholders = ",".join("?" * len(levels_reached))
        achievements_to_grant = self.fetchall(
            f"SELECT id, bp_level, description, picture FROM ACHIVEMENTS WHERE bp_level IN ({placeholders})",
            tuple(levels_reached),
        )
        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        for row in achievements_to_grant:
            aid = row[0]
            self.cursor.execute(
                """
                INSERT OR IGNORE INTO ACHIVEMENTS_TO_USERS (ds_uid, achivement_id, created, taken)
                VALUES (?, ?, ?, 1)
                """,
                (uid, aid, now_utc),
            )
        self.conn.commit()

        return self.fetchall(
            """
            SELECT a.id, a.bp_level, a.description, a.picture
            FROM ACHIVEMENTS a
            JOIN ACHIVEMENTS_TO_USERS atu ON atu.achivement_id = a.id
            WHERE atu.ds_uid = ?
            ORDER BY a.bp_level ASC, a.id ASC
            """,
            (uid,),
        )

    def calculate_all_users_achivements(self) -> list[tuple]:
        """
        Run calculate_user_achivements for every user in USERS.
        Returns list of (uid, achievement_count) for each user after sync.
        """
        uids = [row[0] for row in self.fetchall("SELECT uid FROM USERS", ())]
        result = []
        for uid in uids:
            achievements = self.calculate_user_achivements(uid)
            result.append((uid, len(achievements)))
        return result


def format_sqlite_rows(rows, headers=None, max_rows=20):
    if not rows:
        return "пусто. совсем."

    rows = rows[:max_rows]

    if headers:
        rows = [headers] + list(rows)

    cols = list(zip(*rows))
    widths = [max(len(str(cell)) for cell in col) for col in cols]

    lines = []
    for i, row in enumerate(rows):
        line = " | ".join(
            str(cell).ljust(widths[idx])
            for idx, cell in enumerate(row)
        )
        if headers and i == 0:
            sep = "-+-".join("-" * w for w in widths)
            lines.append(line)
            lines.append(sep)
        else:
            lines.append(line)

    result = "```\n" + "\n".join(lines) + "\n```"
    return result
