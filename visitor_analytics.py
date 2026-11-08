"""Privacy-conscious anonymous visitor counters for BOOYAHJO.

Only a SHA-256 digest of a browser-generated random identifier is stored.
No IP address, user-agent, student/teacher identity, QR code, or page URL
is persisted. Counting begins on the date this feature is deployed.
"""
import hashlib
import re
import time
from urllib.parse import urlparse

import platform_store as store

SESSION_SECONDS = 30 * 60
JORDAN_OFFSET_SECONDS = 3 * 3600
PAGES = frozenset(('home', 'student', 'studio', 'stage', 'about', 'privacy'))
VISITOR_ID = re.compile(r'[0-9a-f]{32}\Z')


def initialize():
    """Create additive, cross-database tables without touching school records."""
    store.exec_sql("""CREATE TABLE IF NOT EXISTS site_visitors (
        visitor_hash TEXT PRIMARY KEY,
        first_seen BIGINT NOT NULL,
        last_seen BIGINT NOT NULL,
        visits INTEGER NOT NULL DEFAULT 1,
        pageviews INTEGER NOT NULL DEFAULT 1
    )""")
    store.exec_sql("""CREATE TABLE IF NOT EXISTS site_visit_days (
        visitor_hash TEXT NOT NULL,
        day_amman BIGINT NOT NULL,
        last_seen BIGINT NOT NULL,
        visits INTEGER NOT NULL DEFAULT 1,
        pageviews INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY(visitor_hash, day_amman)
    )""")
    store.exec_sql('CREATE INDEX IF NOT EXISTS idx_visitor_days_amman ON site_visit_days (day_amman)')


def _day(now):
    # Jordan has observed permanent UTC+03 since 2022. Do not store IP/location.
    return (now + JORDAN_OFFSET_SECONDS) // 86400


def record(visitor_id, page, *, now=None):
    """Atomic count, with each browser counting once in a 30-minute session."""
    if not isinstance(visitor_id, str) or not VISITOR_ID.fullmatch(visitor_id):
        raise ValueError('invalid_visitor_id')
    if page not in PAGES:
        raise ValueError('invalid_page')
    timestamp = int(time.time() if now is None else now)
    previous_session = timestamp - SESSION_SECONDS
    visitor_hash = hashlib.sha256(('booyahjo-anonymous-v1:' + visitor_id).encode('ascii')).hexdigest()
    day = _day(timestamp)
    with store.DB_LOCK:
        # Both upserts commit together. DB_LOCK serializes overlapping requests
        # within this process; database primary keys also protect multiple workers.
        with store.db_connection() as con:
            con.execute(store.sql("""INSERT INTO site_visitors
                (visitor_hash, first_seen, last_seen, visits, pageviews)
                VALUES (?, ?, ?, 1, 1)
                ON CONFLICT(visitor_hash) DO UPDATE SET
                    visits=site_visitors.visits +
                       CASE WHEN site_visitors.last_seen<=? THEN 1 ELSE 0 END,
                    pageviews=site_visitors.pageviews+1,
                    last_seen=excluded.last_seen
            """), (visitor_hash, timestamp, timestamp, previous_session))
            con.execute(store.sql("""INSERT INTO site_visit_days
                (visitor_hash, day_amman, last_seen, visits, pageviews)
                VALUES (?, ?, ?, 1, 1)
                ON CONFLICT(visitor_hash, day_amman) DO UPDATE SET
                    visits=site_visit_days.visits +
                       CASE WHEN site_visit_days.last_seen<=? THEN 1 ELSE 0 END,
                    pageviews=site_visit_days.pageviews+1,
                    last_seen=excluded.last_seen
            """), (visitor_hash, day, timestamp, previous_session))


def summary(now=None):
    """Aggregated counts only; used behind owner's authenticated admin API."""
    timestamp = int(time.time() if now is None else now)
    today = _day(timestamp)
    all_time = store.query("""SELECT COUNT(*) AS unique_visitors,
        COALESCE(SUM(visits),0) AS sessions,
        COALESCE(SUM(pageviews),0) AS pageviews,
        MIN(first_seen) AS since FROM site_visitors""")
    today_row = store.query('SELECT COUNT(*) AS n FROM site_visit_days WHERE day_amman=?', (today,))
    week_row = store.query('SELECT COUNT(DISTINCT visitor_hash) AS n FROM site_visit_days WHERE day_amman>=? AND day_amman<=?',
                           (today - 6, today))
    return {
        'total': int(all_time['unique_visitors']),
        'today': int(today_row['n']),
        'last7Days': int(week_row['n']),
        'visits': int(all_time['sessions']),
        'pageviews': int(all_time['pageviews']),
        'since': int(all_time['since']) if all_time['since'] is not None else None,
        'timezone': 'Asia/Amman'
    }


def handle_post(handler, data):
    """Public write-only endpoint. No anonymous read endpoint exists."""
    if not isinstance(data, dict):
        handler.send_json({'ok':False, 'error':'bad_request'}, 400)
        return
    origin = handler.headers.get('Origin', '')
    fetch_site = handler.headers.get('Sec-Fetch-Site', '')
    host = handler.headers.get('Host', '')
    if fetch_site == 'cross-site' or (origin and urlparse(origin).netloc != host):
        handler.send_json({'ok':False, 'error':'foreign_origin'}, 403)
        return
    try:
        record(data.get('id'), data.get('page'))
    except ValueError:
        handler.send_json({'ok':False, 'error':'invalid_tracking_data'}, 400)
        return
    except Exception as exc:
        handler.log_message('analytics write failed: %s', type(exc).__name__)
        handler.send_json({'ok':False, 'error':'tracking_unavailable'}, 503)
        return
    handler.send_json({'ok':True})
