import os
import sqlite3
import re
from io import BytesIO
from flask import Flask, g, render_template_string, request, url_for, abort, send_file
import dotenv

dotenv.load_dotenv()

sql_path = "/mnt/db"
if os.path.exists("/db"):
    sql_path = "/db"
elif not os.path.exists("/mnt/db"):
    raise "I need a db path"


app = Flask(__name__)
DB_PATH = os.environ.get("DB_PATH", os.path.join(
            sql_path,
            'sengoku_bot.db'
        ))

DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "sengoku_bot.db"),
)

ARCHIVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "archives")

with open(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "base.html"),
    encoding="utf-8",
) as f:
    BASE_HTML = f.read()

with open(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "index.html"),
    encoding="utf-8",
) as f:
    INDEX_HTML = f.read()

with open(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "user.html"),
    encoding="utf-8",
) as f:
    USER_HTML = f.read()

with open(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'static', 'payments.html'
)) as f:
    PAYMENTS_HTML = f.read()

with open(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'static', 'timeout.html'
)) as f:
    TECHNICAL_TIMEOUT_HTML = f.read()


def get_archives():
    if not os.path.exists(ARCHIVE_DIR):
        return []
    files = [f for f in os.listdir(ARCHIVE_DIR) if f.endswith(".db")]
    archives = []
    for f in files:
        base = f[:-3]
        if re.match(r"^[a-z]+_\d{4}$", base):
            month, year = base.split("_", 1)
            name = f"{month.capitalize()} {year}"
            archives.append({"file": base, "name": name})
    archives.sort(key=lambda x: x["file"], reverse=True)
    return archives


def resolve_db_path(db_param: str | None):
    if not db_param:
        return None, None
    if not re.match(r"^[a-z]+_\d{4}$", db_param):
        abort(404)
    db_path = os.path.join(ARCHIVE_DIR, f"{db_param}.db")
    if not os.path.exists(db_path):
        abort(404)
    history_title = " ".join([word.capitalize() for word in db_param.split("_")])
    return db_path, history_title


def get_db(db_path=None) -> sqlite3.Connection:
    if not hasattr(g, "_db_cache"):
        g._db_cache = {}
    key = db_path or "default"
    if key not in g._db_cache:
        path = db_path or DB_PATH
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        g._db_cache[key] = conn
    return g._db_cache[key]


@app.teardown_appcontext
def close_db(exception):
    cache = getattr(g, "_db_cache", None)
    if not cache:
        return
    for _, conn in list(cache.items()):
        try:
            conn.close()
        except Exception:
            pass
    try:
        delattr(g, "_db_cache")
    except Exception:
        pass


def export_button_html(db_param: str | None):
    href = url_for("export_xlsx") + (f"?db={db_param}" if db_param else "")
    return f"""
    <div style="margin: 10px 0 18px 0;">
      <a href="{href}" style="display:inline-block;padding:10px 14px;border-radius:10px;text-decoration:none;border:1px solid rgba(255,255,255,.2);">
        ⬇ выгрузить xlsx
      </a>
    </div>
    """


def safe_sheet_name(name: str, used: set[str]):
    base = re.sub(r"[\[\]\:\*\?\/\\]", "_", name).strip() or "Sheet"
    base = base[:31]
    if base not in used:
        used.add(base)
        return base
    i = 2
    while True:
        suffix = f"_{i}"
        cand = (base[: 31 - len(suffix)] + suffix)[:31]
        if cand not in used:
            used.add(cand)
            return cand
        i += 1


def list_tables(conn: sqlite3.Connection):
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name ASC"
    )
    return [r[0] for r in cur.fetchall()]


def fetch_table_as_rows(conn: sqlite3.Connection):
    cur = conn.execute(f'''
           SELECT u.uid,
           COALESCE(NULLIF(u.server_username, ''), u.global_username) AS display_name,
           u.liable,
           COUNT(DISTINCT CASE WHEN e.disband != 1 THEN e.message_id END) AS event_count,
           COALESCE(SUM(CASE WHEN e.disband != 1 THEN e.points ELSE 0 END), 0) AS total_points,
           u.need_to_get,
           u.is_member,
           u.roles
      FROM USERS u
      LEFT JOIN EVENTS_TO_USERS etu ON etu.ds_uid = u.uid
      LEFT JOIN EVENTS e ON e.message_id = etu.message_id
      WHERE COALESCE(NULLIF(u.server_username, ''), u.global_username) != 'D9dka'
      GROUP BY u.uid
      ORDER BY total_points DESC, event_count DESC, display_name COLLATE NOCASE ASC
    ''')
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    return cols, rows


def build_xlsx_bytes(conn: sqlite3.Connection) -> bytes:
    from openpyxl import Workbook

    wb = Workbook(write_only=True)
    used = set()

    cols, rows = fetch_table_as_rows(conn)
    ws = wb.create_sheet(title=safe_sheet_name("members", used))
    ws.append(cols)
    for r in rows:
        ws.append(list(r))

    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio.read()


@app.route("/export.xlsx")
def export_xlsx():
    db_param = request.args.get("db")
    db_path, _ = resolve_db_path(db_param)
    db = get_db(db_path)

    xlsx_bytes = build_xlsx_bytes(db)

    filename = "export.xlsx"
    if db_param:
        filename = f"export_{db_param}.xlsx"

    return send_file(
        BytesIO(xlsx_bytes),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename,
    )


@app.route("/")
def index():
    db_param = request.args.get("db")
    db_path, history_title = resolve_db_path(db_param)

    if os.getenv("TECHNICAL_TIMEOUT", "0") == "1":
        return render_template_string(
            TECHNICAL_TIMEOUT_HTML
            + "<body><h1>Ведутся технические работы</h1><p>Извините за неудобства, скоро всё починим.</p></body></html>"
        )

    db = get_db(db_path)
    q = db.execute("""
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

    """)
    rows = q.fetchall()

    archives = get_archives()

    subtitle = f"Всего мемберов: {len(rows)}"
    if history_title:
        subtitle = f"Historical Data: {history_title} | {subtitle}"

    html = render_template_string(INDEX_HTML, rows=rows, db_param=db_param)
    html = export_button_html(db_param) + html
    return render_template_string(
        BASE_HTML,
        title="мемберы × контент",
        subtitle=subtitle,
        content=html,
        archives=archives,
        db_param=db_param,
    )


@app.template_filter("money")
def money(v):
    if v is None:
        return "—"
    return f"{v:,}".replace(",", " ")

 
@app.route('/user/<int:uid>')
def user_detail(uid):
    db_param = request.args.get("db")
    db_path, history_title = resolve_db_path(db_param)

    db = get_db(db_path)
    uq = db.execute(
        "SELECT uid, COALESCE(NULLIF(global_username, ''), server_username) AS display_name FROM USERS WHERE uid=?",
        (uid,),
    )
    user = uq.fetchone()
    if not user:
        abort(404)

    eq = db.execute(
        """
        SELECT e.message_id, e.guild_id, e.channel_id, e.channel_name, e.message_text, e.read_time, e.disband, e.points, e.hidden
        FROM EVENTS_TO_USERS etu
        JOIN EVENTS e ON e.message_id = etu.message_id
        WHERE etu.ds_uid = ?
        ORDER BY e.message_id DESC
    """,
        (uid,),
    )
    events = eq.fetchall()

    events = list(events)
    for i in range(len(events)):
        if events[i]["hidden"]:
            d = dict(events[i])
            d["channel_name"] = "None"
            d["message_text"] = "А тебя это ебать не должно"
            d["channel_id"] = 0
            d["message_id"] = 0
            d["guild_id"] = 0
            events[i] = d

    archives = get_archives()

    subtitle = f"Сходил на {len(events)} контентов (✓ — проведенные, ✗ — дизбанднутые)"
    if history_title:
        subtitle = f"{subtitle} (Historical: {history_title})"

    html = render_template_string(USER_HTML, events=events, db_param=db_param)
    html = export_button_html(db_param) + html
    return render_template_string(
        BASE_HTML,
        title=f"{user['display_name'] or 'без имени'}",
        subtitle=subtitle,
        content=html,
        archives=archives,
        db_param=db_param,
    )


@app.route('/payment/<int:uid>')
def payment_detail(uid):
    db_param = request.args.get('db')
    db_path = None
    history_title = None
    if db_param:
        if not re.match(r'^[a-z]+_\d{4}$', db_param):
            abort(404)
        db_path = os.path.join(ARCHIVE_DIR, f"{db_param}.db")
        if not os.path.exists(db_path):
            abort(404)
        history_title = ' '.join([word.capitalize() for word in db_param.split('_')])
    
    db = get_db(db_path)
    uq = db.execute("SELECT uid, COALESCE(NULLIF(global_username, ''), server_username) AS display_name FROM USERS WHERE uid=?", (uid,))
    user = uq.fetchone()
    if not user:
        abort(404)
    eq = db.execute("""
            select ROUND((p.payment_ammount * 1.0) / (p.user_amount * 1.0), 2) as payment_sum, p.message_id, p.channel_id, p.guild_id, p.payment_ammount, p.user_amount, p.pay_time
            from PAYMENTS p
            join PAYMENTS_TO_USERS ul on p.message_id = ul.message_id
            where ul.ds_uid = ?
    """, (uid,))
    payments = eq.fetchall()

    archives = get_archives()
    
    subtitle = f"{len(payments)} выплат мембера {uq}"
    if history_title:
        subtitle = f"{subtitle} (Historical: {history_title})"
    
    html = render_template_string(PAYMENTS_HTML, events=payments, db_param=db_param)
    return render_template_string(BASE_HTML, title=f"{user['display_name'] or 'без имени'}", subtitle=subtitle, content=html, archives=archives, db_param=db_param)



from werkzeug.middleware.proxy_fix import ProxyFix


class PrefixMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        prefix = environ.get("HTTP_X_SCRIPT_NAME") or environ.get(
            "HTTP_X_FORWARDED_PREFIX"
        )
        if prefix:
            prefix = prefix.rstrip("/")
            environ["SCRIPT_NAME"] = prefix
            path = environ.get("PATH_INFO", "")
            if path.startswith(prefix):
                environ["PATH_INFO"] = path[len(prefix) :] or "/"
        return self.app(environ, start_response)


app.wsgi_app = PrefixMiddleware(app.wsgi_app)
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
