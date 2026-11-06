"""BOOYAHJO Control Center V1 — separate owner auth, 2FA, cross-tenant read models.
No admin privileges are derived from teacher tokens or student card tokens.
"""
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
import uuid
from datetime import datetime, timezone
from urllib.parse import parse_qs

import platform_store as store

RATE = {}
RATE_LOCK = threading.Lock()
MAX_ROWS = 50
SESSION_SECONDS = 8 * 3600


def clock():
    return int(time.time())


def sql(query, params=(), many=False):
    return store.query(query, params, many)


def initialize():
    commands = [
        """CREATE TABLE IF NOT EXISTS admin_users(
          id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
          password_hash TEXT NOT NULL, salt TEXT NOT NULL, totp_cipher TEXT NOT NULL,
          active INTEGER NOT NULL DEFAULT 0, failed_attempts INTEGER NOT NULL DEFAULT 0,
          locked_until BIGINT NOT NULL DEFAULT 0, last_login BIGINT NOT NULL DEFAULT 0,
          created_at BIGINT NOT NULL)""",
        """CREATE TABLE IF NOT EXISTS admin_sessions(
          token_hash TEXT PRIMARY KEY, admin_id TEXT NOT NULL,
          csrf_hash TEXT NOT NULL, expires_at BIGINT NOT NULL, created_at BIGINT NOT NULL)""",
        """CREATE TABLE IF NOT EXISTS admin_audit(
          id TEXT PRIMARY KEY, admin_id TEXT NOT NULL, action TEXT NOT NULL,
          target_type TEXT NOT NULL, target_id TEXT NOT NULL,
          note TEXT NOT NULL, created_at BIGINT NOT NULL)""",
        "CREATE INDEX IF NOT EXISTS idx_admin_session_exp ON admin_sessions(expires_at)",
        "CREATE INDEX IF NOT EXISTS idx_admin_audit_time ON admin_audit(created_at)",
    ]
    for statement in commands:
        store.exec_sql(statement)
    if store.DATABASE_KIND == 'postgres':
        exists = sql("""SELECT 1 AS ok FROM information_schema.columns
                       WHERE table_schema='public' AND table_name='teachers'
                       AND column_name='admin_disabled'""")
        if not exists:
            store.exec_sql('ALTER TABLE teachers ADD COLUMN admin_disabled INTEGER NOT NULL DEFAULT 0')
    else:
        with store.db_connection() as con:
            columns = [r[1] for r in con.execute('PRAGMA table_info(teachers)').fetchall()]
        if 'admin_disabled' not in columns:
            store.exec_sql('ALTER TABLE teachers ADD COLUMN admin_disabled INTEGER NOT NULL DEFAULT 0')


def _hash_password(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf8'), bytes.fromhex(salt), 650_000).hex()


def _fernet():
    from cryptography.fernet import Fernet
    key = os.getenv('BOOYAH_ADMIN_TOTP_KEY', '')
    if not key:
        raise RuntimeError('admin_encryption_key_missing')
    return Fernet(key.encode('ascii'))


def encrypt_secret(value):
    return _fernet().encrypt(value.encode('ascii')).decode('ascii')


def decrypt_secret(value):
    return _fernet().decrypt(value.encode('ascii')).decode('ascii')


def totp(secret, step=None):
    counter = int(clock() // 30 if step is None else step)
    raw = base64.b32decode(secret + '=' * ((8 - len(secret) % 8) % 8), casefold=True)
    digest = hmac.new(raw, counter.to_bytes(8, 'big'), hashlib.sha1).digest()
    offset = digest[-1] & 15
    num = int.from_bytes(digest[offset:offset + 4], 'big') & 0x7fffffff
    return f'{num % 1_000_000:06d}'


def check_totp(secret, code):
    if not re.fullmatch(r'[0-9]{6}', str(code or '')):
        return False
    period = clock() // 30
    return any(hmac.compare_digest(str(code), totp(secret, period + shift)) for shift in (-1, 0, 1))


def require_origin(handler):
    origin = handler.headers.get('Origin')
    if origin:
        from urllib.parse import urlparse
        parsed = urlparse(origin)
        host = handler.headers.get('Host', '')
        # Same-origin request only, independent of proxy/CDN forwarded origin.
        if parsed.netloc != host or parsed.scheme not in ('https', 'http'):
            return False
    return handler.headers.get('X-BOOYAH-Admin') == '1'


def limited(handler, action, identity=''):
    key = (handler.client_address[0], action, hashlib.sha256(str(identity).lower().encode()).hexdigest()[:12])
    now = time.monotonic()
    with RATE_LOCK:
        records = [x for x in RATE.get(key, []) if now - x < 600]
        if len(records) >= (6 if action == 'login' else 12):
            RATE[key] = records
            return True
        RATE[key] = records + [now]
        if len(RATE) > 6000:
            RATE.clear()
    return False


def _cookie(handler, name):
    from http.cookies import SimpleCookie
    cookie = SimpleCookie()
    try:
        cookie.load(handler.headers.get('Cookie', ''))
        return cookie[name].value if name in cookie else ''
    except Exception:
        return ''


def _admin_cookie(handler, key, value, max_age=SESSION_SECONDS, http_only=True):
    # Localhost is a secure context in browsers; local HTTP tests may omit Secure.
    secure = '; Secure' if os.getenv('RENDER') or os.getenv('RENDER_EXTERNAL_URL') else ''
    return f'{key}={value}; Path={"/api/admin" if http_only else "/"}; Max-Age={max_age}; SameSite=Strict{secure}' + ('; HttpOnly' if http_only else '')


def _reply(handler, data, code=200, cookies=()):
    raw = json.dumps(data, ensure_ascii=False).encode('utf-8')
    handler.send_response(code)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Content-Length', str(len(raw)))
    handler.send_header('Cache-Control', 'no-store, private')
    for cookie in cookies:
        handler.send_header('Set-Cookie', cookie)
    handler.end_headers()
    handler.wfile.write(raw)


def _safe_account(admin):
    return {'name': admin['name'], 'email': admin['email'], 'role': 'owner', 'lastLogin': admin['last_login']}


def admin_for_request(handler, needs_csrf=False):
    token = _cookie(handler, 'bjadmin')
    if len(token) < 42 or len(token) > 160:
        return None
    user = sql("""SELECT a.id,a.email,a.name,a.active,a.last_login,s.csrf_hash
                  FROM admin_sessions s JOIN admin_users a ON a.id=s.admin_id
                  WHERE s.token_hash=? AND s.expires_at>?""",
               (hashlib.sha256(token.encode()).hexdigest(), clock()))
    if not user or not user['active']:
        return None
    if needs_csrf:
        csrf = handler.headers.get('X-Admin-CSRF', '')
        cookie = _cookie(handler, 'bjcsrf')
        if not csrf or not cookie or not hmac.compare_digest(csrf, cookie):
            return None
        if not hmac.compare_digest(hashlib.sha256(csrf.encode()).hexdigest(), user['csrf_hash']):
            return None
    return user


def audit(admin_id, action, target_type='system', target_id='', note=''):
    store.exec_sql('INSERT INTO admin_audit(id,admin_id,action,target_type,target_id,note,created_at) VALUES(?,?,?,?,?,?,?)',
                   (uuid.uuid4().hex, admin_id, action, target_type, target_id, str(note or '')[:240], clock()))


def setup_ready():
    # No owner email or password is baked into source or user data.
    return bool(os.getenv('BOOYAH_ADMIN_SETUP_KEY') and os.getenv('BOOYAH_ADMIN_TOTP_KEY')) and (
        sql('SELECT COUNT(*) AS n FROM admin_users')['n'] == 0)


def _setup(h, data):
    if not setup_ready():
        return _reply(h, {'ok': False, 'error': 'setup_disabled'}, 403)
    key = str(data.get('setupKey') or '')
    expected = os.getenv('BOOYAH_ADMIN_SETUP_KEY', '')
    if len(key) < 24 or not hmac.compare_digest(key, expected):
        return _reply(h, {'ok': False, 'error': 'invalid_setup_key'}, 403)
    email = str(data.get('email') or '').strip().lower()
    name = str(data.get('name') or '').strip()
    password = str(data.get('password') or '')
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email) or len(email) > 160:
        return _reply(h, {'ok': False, 'error': 'invalid_email'}, 400)
    if not 2 <= len(name) <= 100 or len(password) < 14 or len(password) > 180:
        return _reply(h, {'ok': False, 'error': 'password_min_14'}, 400)
    try:
        secret = base64.b32encode(secrets.token_bytes(20)).decode('ascii').rstrip('=')
        salt = secrets.token_hex(16)
        uid = uuid.uuid4().hex
        with store.DB_LOCK:
            with store.db_connection() as con:
                cur = con.cursor()
                cur.execute(store.sql('SELECT COUNT(*) FROM admin_users'))
                if cur.fetchone()[0] != 0:
                    return _reply(h, {'ok': False, 'error': 'setup_disabled'}, 403)
                cur.execute(store.sql("""INSERT INTO admin_users(
                  id,email,name,password_hash,salt,totp_cipher,active,created_at)
                  VALUES(?,?,?,?,?,?,0,?)"""),
                  (uid,email,name,_hash_password(password,salt),salt,encrypt_secret(secret),clock()))
        return _reply(h, {'ok': True, 'pending2fa': True, 'secret': secret,
                          'message': 'Add this code to an authenticator app and confirm a one-time code.'})
    except Exception:
        return _reply(h, {'ok': False, 'error': 'setup_error'}, 500)


def _activate(h, data):
    expected = os.getenv('BOOYAH_ADMIN_SETUP_KEY', '')
    if not expected or not hmac.compare_digest(str(data.get('setupKey') or ''), expected):
        return _reply(h, {'ok': False, 'error': 'invalid_setup_key'}, 403)
    email = str(data.get('email') or '').strip().lower()
    row = sql('SELECT id,active,totp_cipher FROM admin_users WHERE email=?', (email,))
    if not row or row['active']:
        return _reply(h, {'ok': False, 'error': 'setup_disabled'}, 403)
    if not check_totp(decrypt_secret(row['totp_cipher']), str(data.get('otp') or '')):
        return _reply(h, {'ok': False, 'error': 'invalid_otp'}, 401)
    store.exec_sql('UPDATE admin_users SET active=1 WHERE id=? AND active=0', (row['id'],))
    audit(row['id'], 'owner_activated')
    return _reply(h, {'ok': True, 'activated': True})


def _login(h, data):
    email = str(data.get('email') or '').strip().lower()[:160]
    row = sql('SELECT * FROM admin_users WHERE email=?', (email,))
    # Equal-work baseline prevents quick user-email enumeration.
    if not row:
        _hash_password(str(data.get('password') or '')[:180], '0' * 32)
        return _reply(h, {'ok': False, 'error': 'invalid_credentials'}, 401)
    if not row['active'] or row['locked_until'] > clock():
        return _reply(h, {'ok': False, 'error': 'invalid_credentials'}, 401)
    password = str(data.get('password') or '')
    match = hmac.compare_digest(row['password_hash'], _hash_password(password[:181], row['salt']))
    code_ok = match and check_totp(decrypt_secret(row['totp_cipher']), str(data.get('otp') or ''))
    if not code_ok:
        failed = int(row['failed_attempts']) + 1
        store.exec_sql('UPDATE admin_users SET failed_attempts=?, locked_until=? WHERE id=?',
                       (failed, clock() + 900 if failed >= 5 else 0, row['id']))
        return _reply(h, {'ok': False, 'error': 'invalid_credentials'}, 401)
    store.exec_sql('UPDATE admin_users SET failed_attempts=0, locked_until=0,last_login=? WHERE id=?',
                   (clock(), row['id']))
    session = secrets.token_urlsafe(48)
    csrf = secrets.token_urlsafe(32)
    store.exec_sql('INSERT INTO admin_sessions(token_hash,admin_id,csrf_hash,expires_at,created_at) VALUES(?,?,?,?,?)',
                   (hashlib.sha256(session.encode()).hexdigest(), row['id'],
                    hashlib.sha256(csrf.encode()).hexdigest(), clock() + SESSION_SECONDS, clock()))
    audit(row['id'], 'admin_login')
    return _reply(h, {'ok': True, 'admin': _safe_account(row)}, cookies=(
        _admin_cookie(h, 'bjadmin', session),
        _admin_cookie(h, 'bjcsrf', csrf, http_only=False)))


def _logout(h, admin):
    token = _cookie(h, 'bjadmin')
    store.exec_sql('DELETE FROM admin_sessions WHERE token_hash=?', (hashlib.sha256(token.encode()).hexdigest(),))
    audit(admin['id'], 'admin_logout')
    return _reply(h, {'ok': True}, cookies=(
        _admin_cookie(h, 'bjadmin', '', max_age=0),
        _admin_cookie(h, 'bjcsrf', '', max_age=0, http_only=False)))


def _count(table):
    return int(sql(f'SELECT COUNT(*) AS n FROM {table}')['n'])


def summary():
    # Numeric aggregations only; never expose student names, QR tokens or passwords.
    counted_quizzes = sql('SELECT quizzes FROM datasets', many=True)
    quizzes = sum(len(q) for row in counted_quizzes
                  for q in [store.jload(row['quizzes'], [])] if isinstance(q, list))
    days = []
    today = clock() // 86400 * 86400
    for i in range(13, -1, -1):
        begin = today - i * 86400
        stat = sql('SELECT COUNT(*) AS n FROM played_sessions WHERE played_at>=? AND played_at<?',
                   (begin, begin + 86400))
        days.append({'day': datetime.fromtimestamp(begin, tz=timezone.utc).strftime('%m-%d'),
                     'sessions': int(stat['n'])})
    return {'teachers': _count('teachers'), 'students': _count('students'),
            'quizzes': quizzes, 'sessions': _count('played_sessions'),
            'attempts': _count('student_attempts'), 'liveRooms': _count('active_rooms'),
            'schools': int(sql("SELECT COUNT(DISTINCT school) AS n FROM teachers")['n']),
            'activeTeachers7d': int(sql("""SELECT COUNT(DISTINCT teacher_id) AS n FROM
              played_sessions WHERE played_at>=?""", (clock() - 7*86400,))['n']),
            'days': days, 'database': store.DATABASE_KIND}


def teacher_rows(page, search):
    term = '%' + str(search or '').strip()[:70].replace('%', '\\%').replace('_', '\\_') + '%'
    where = "(t.name LIKE ? ESCAPE '\\' OR t.email LIKE ? ESCAPE '\\' OR t.school LIKE ? ESCAPE '\\')"
    args = (term, term, term)
    total = sql('SELECT COUNT(*) AS n FROM teachers t WHERE ' + where, args)['n']
    rows = sql("""SELECT t.id,t.name,t.email,t.school,t.subject,t.school_type,
                 t.created_at,t.admin_disabled,
                 (SELECT COUNT(*) FROM students s WHERE s.teacher_id=t.id) AS students,
                 (SELECT COUNT(*) FROM played_sessions p WHERE p.teacher_id=t.id) AS sessions
                 FROM teachers t WHERE """ + where +
               ' ORDER BY t.created_at DESC LIMIT ? OFFSET ?', args + (MAX_ROWS,(page-1)*MAX_ROWS), True)
    return {'total': int(total), 'page': page, 'pageSize': MAX_ROWS,
            'rows': [dict(r) for r in rows]}


def school_rows():
    return sql("""SELECT t.school, COUNT(DISTINCT t.id) AS teachers,
                 COUNT(DISTINCT s.id) AS students,
                 COUNT(DISTINCT p.id) AS sessions
                 FROM teachers t LEFT JOIN students s ON s.teacher_id=t.id
                 LEFT JOIN played_sessions p ON p.teacher_id=t.id
                 GROUP BY t.school ORDER BY teachers DESC,t.school LIMIT 100""", many=True)


def audit_rows():
    return sql("""SELECT a.action,a.target_type,a.target_id,a.note,a.created_at,u.name AS actor
                  FROM admin_audit a JOIN admin_users u ON u.id=a.admin_id
                  ORDER BY a.created_at DESC LIMIT 100""", many=True)



def _page(qs, key='page'):
    try:
        return max(1, min(1000, int(qs.get(key, ['1'])[0])))
    except (ValueError, TypeError, OverflowError):
        return 1


def _safe_search(qs):
    return str(qs.get('search', [''])[0] or '').strip()[:90].replace('%', '\\%').replace('_', '\\_')


def _id(value):
    return bool(re.fullmatch(r'[0-9a-f]{32}', str(value or '')))


def _quiz_count(teacher_id):
    data = sql('SELECT quizzes FROM datasets WHERE teacher_id=?', (teacher_id,))
    if not data:
        return 0
    quizzes = store.jload(data['quizzes'], [])
    return len(quizzes) if isinstance(quizzes, list) else 0


def teacher_detail(teacher_id):
    if not _id(teacher_id):
        return None
    t = sql("""SELECT id,name,email,school,subject,school_type,created_at,
                admin_disabled FROM teachers WHERE id=?""", (teacher_id,))
    if not t:
        return None
    counts = sql("""SELECT
        (SELECT COUNT(*) FROM students WHERE teacher_id=?) students,
        (SELECT COUNT(*) FROM played_sessions WHERE teacher_id=?) sessions,
        (SELECT COUNT(*) FROM student_attempts WHERE teacher_id=?) attempts,
        (SELECT MAX(played_at) FROM played_sessions WHERE teacher_id=?) last_session,
        (SELECT MAX(created_at) FROM student_attempts WHERE teacher_id=?) last_attempt
    """, (teacher_id,)*5)
    attempts = sql("""SELECT AVG(percent) AS average_percent,
                SUM(CASE WHEN percent>=80 THEN 1 ELSE 0 END) AS high_scores
                FROM student_attempts WHERE teacher_id=?""", (teacher_id,))
    classes = sql("""SELECT class_name, COUNT(*) AS students
                     FROM students WHERE teacher_id=?
                     GROUP BY class_name ORDER BY students DESC,class_name LIMIT 25""",
                  (teacher_id,), True)
    sessions = sql("""SELECT id,quiz_title,section,subject,game_mode,played_at
                     FROM played_sessions WHERE teacher_id=?
                     ORDER BY played_at DESC LIMIT 12""", (teacher_id,), True)
    output = dict(t)
    output.update(dict(counts))
    output['quizzes'] = _quiz_count(teacher_id)
    output['averagePercent'] = round(float(attempts['average_percent'] or 0), 1)
    output['highScores'] = int(attempts['high_scores'] or 0)
    output['classes'] = [dict(x) for x in classes]
    output['recentSessions'] = [dict(x) for x in sessions]
    return output



def student_detail(student_id):
    if not _id(student_id):
        return None
    row = sql("""SELECT s.id,s.name,s.class_name,s.avatar,s.xp,
                 s.correct_count,s.played_count,s.created_at,
                 t.name AS teacher_name,t.id AS teacher_id,t.school,t.subject
                 FROM students s JOIN teachers t ON t.id=s.teacher_id
                 WHERE s.id=?""", (student_id,))
    if not row:
        return None
    attempts = sql("""SELECT id,quiz_id,room_code,correct_count,question_total,
                      percent,score,created_at FROM student_attempts
                      WHERE student_id=? ORDER BY created_at DESC LIMIT 25""",
                   (student_id,), True)
    stats = sql("""SELECT COUNT(*) AS attempts,AVG(percent) AS avg_percent,
                   MAX(created_at) AS last_attempt
                   FROM student_attempts WHERE student_id=?""", (student_id,))
    detail = dict(row)
    detail['attempts'] = int(stats['attempts'])
    detail['averagePercent'] = round(float(stats['avg_percent'] or 0),1)
    detail['lastAttempt'] = stats['last_attempt']
    detail['recentAttempts'] = [dict(a) for a in attempts]
    return detail


def student_rows(page, search, teacher_id):
    term = '%' + search + '%'
    where = """(s.name LIKE ? ESCAPE '\\' OR s.class_name LIKE ? ESCAPE '\\'
                OR t.name LIKE ? ESCAPE '\\')"""
    params = [term, term, term]
    if teacher_id:
        if not _id(teacher_id):
            return {'total': 0, 'page': page, 'pageSize': MAX_ROWS, 'rows': []}
        where += ' AND s.teacher_id=?'
        params.append(teacher_id)
    total = sql("""SELECT COUNT(*) AS n FROM students s
                   JOIN teachers t ON t.id=s.teacher_id WHERE """+where, tuple(params))['n']
    rows = sql("""SELECT s.id,s.name,s.class_name,s.xp,s.correct_count,s.played_count,
                 s.created_at,s.teacher_id,t.name AS teacher_name,t.school,
                 (SELECT COUNT(*) FROM student_attempts a WHERE a.student_id=s.id) AS attempts,
                 (SELECT MAX(a.created_at) FROM student_attempts a WHERE a.student_id=s.id) AS last_attempt
                 FROM students s JOIN teachers t ON t.id=s.teacher_id WHERE """+where+
               ' ORDER BY s.created_at DESC LIMIT ? OFFSET ?',
               tuple(params + [MAX_ROWS,(page-1)*MAX_ROWS]), True)
    # No card codes, QR credentials, authentication tokens or answer payloads.
    return {'total': int(total), 'page': page, 'pageSize': MAX_ROWS,
            'rows': [dict(x) for x in rows]}


def session_rows(page, search, teacher_id):
    term = '%' + search + '%'
    where = """(p.quiz_title LIKE ? ESCAPE '\\' OR p.section LIKE ? ESCAPE '\\'
                OR t.name LIKE ? ESCAPE '\\' OR p.code LIKE ? ESCAPE '\\')"""
    params = [term]*4
    if teacher_id:
        if not _id(teacher_id):
            return {'total': 0, 'page': page, 'pageSize': MAX_ROWS, 'rows': []}
        where += ' AND p.teacher_id=?'
        params.append(teacher_id)
    total = sql("""SELECT COUNT(*) AS n FROM played_sessions p
                   JOIN teachers t ON t.id=p.teacher_id WHERE """+where, tuple(params))['n']
    rows = sql("""SELECT p.id,p.code,p.section,p.subject,p.quiz_title,p.game_mode,
                 p.played_at,t.name AS teacher_name,t.school,t.id AS teacher_id,
                 (SELECT COUNT(*) FROM student_attempts a
                  WHERE a.teacher_id=p.teacher_id AND a.room_code=p.code) AS attempts
                 FROM played_sessions p JOIN teachers t ON t.id=p.teacher_id WHERE """+where+
               ' ORDER BY p.played_at DESC LIMIT ? OFFSET ?',
               tuple(params + [MAX_ROWS,(page-1)*MAX_ROWS]), True)
    return {'total': int(total), 'page':page,'pageSize':MAX_ROWS,
            'rows':[dict(x) for x in rows]}


def school_detail(name):
    name = str(name or '').strip()[:150]
    if not name:
        return None
    stats = sql("""SELECT COUNT(DISTINCT t.id) AS teachers,
                COUNT(DISTINCT s.id) AS students,
                COUNT(DISTINCT p.id) AS sessions
                FROM teachers t LEFT JOIN students s ON s.teacher_id=t.id
                LEFT JOIN played_sessions p ON p.teacher_id=t.id WHERE t.school=?""", (name,))
    if not stats or not stats['teachers']:
        return None
    teachers = sql("""SELECT t.id,t.name,t.subject,t.email,t.admin_disabled,
                 (SELECT COUNT(*) FROM students s WHERE s.teacher_id=t.id) students,
                 (SELECT COUNT(*) FROM played_sessions p WHERE p.teacher_id=t.id) sessions
                 FROM teachers t WHERE t.school=? ORDER BY t.created_at DESC LIMIT 100""",
                 (name,), True)
    return {'school':name,**dict(stats),'teachersList':[dict(x) for x in teachers]}


def account_overview():
    return {'summary': summary(), 'recentTeachers': [dict(r) for r in sql(
        """SELECT id,name,school,created_at,admin_disabled FROM teachers
           ORDER BY created_at DESC LIMIT 8""", many=True)],
        'recentSessions': [dict(r) for r in sql(
        """SELECT p.quiz_title,p.played_at,t.name AS teacher_name,p.section
           FROM played_sessions p JOIN teachers t ON t.id=p.teacher_id
           ORDER BY p.played_at DESC LIMIT 8""", many=True)],
        'disabledTeachers': int(sql(
            'SELECT COUNT(*) AS n FROM teachers WHERE admin_disabled=1')['n']),
        'totalSchools': int(sql(
            "SELECT COUNT(DISTINCT NULLIF(TRIM(school),'')) AS n FROM teachers")['n'])}


def handle_get(h,u):
    if u.path not in ('/api/admin/status','/api/admin/me','/api/admin/summary',
                      '/api/admin/teachers','/api/admin/schools','/api/admin/audit',
                      '/api/admin/teacher/detail','/api/admin/student/detail','/api/admin/students',
                      '/api/admin/sessions','/api/admin/school/detail',
                      '/api/admin/insights'):
        return False
    if u.path=='/api/admin/status':
        count=_count('admin_users')
        return _reply(h, {'ok': True, 'setupAvailable': setup_ready(),
                          'hasOwner': bool(count)}) or True
    admin = admin_for_request(h)
    if not admin:
        _reply(h, {'ok': False, 'error': 'admin_login_required'}, 401)
        return True
    args = parse_qs(u.query)
    if u.path == '/api/admin/me':
        _reply(h, {'ok': True, 'admin': _safe_account(admin)})
    elif u.path == '/api/admin/summary':
        _reply(h, {'ok': True, 'summary': summary()})
    elif u.path == '/api/admin/teachers':
        args = parse_qs(u.query)
        page = max(1, min(500, int(args.get('page', ['1'])[0] or 1)))
        _reply(h, {'ok': True, **teacher_rows(page,args.get('search', [''])[0])})
    elif u.path == '/api/admin/schools':
        _reply(h, {'ok': True, 'rows': school_rows()})
    elif u.path == '/api/admin/audit':
        _reply(h, {'ok': True, 'rows': audit_rows()})
    elif u.path == '/api/admin/teacher/detail':
        detail = teacher_detail(args.get('id',[''])[0])
        _reply(h, {'ok': bool(detail), 'teacher': detail} if detail else {'ok':False,'error':'not_found'}, 200 if detail else 404)
    elif u.path == '/api/admin/student/detail':
        detail = student_detail(args.get('id',[''])[0])
        _reply(h, {'ok':True,'student':detail} if detail else {'ok':False,'error':'not_found'}, 200 if detail else 404)
    elif u.path == '/api/admin/students':
        _reply(h, {'ok':True, **student_rows(_page(args),_safe_search(args),args.get('teacherId',[''])[0])})
    elif u.path == '/api/admin/sessions':
        _reply(h, {'ok':True, **session_rows(_page(args),_safe_search(args),args.get('teacherId',[''])[0])})
    elif u.path == '/api/admin/school/detail':
        detail = school_detail(args.get('name',[''])[0])
        _reply(h, {'ok':bool(detail),'school':detail} if detail else {'ok':False,'error':'not_found'}, 200 if detail else 404)
    elif u.path == '/api/admin/insights':
        _reply(h, {'ok':True, **account_overview()})
    return True


def handle_post(h,u,data):
    if u.path not in ('/api/admin/setup','/api/admin/activate','/api/admin/login',
                      '/api/admin/logout','/api/admin/teacher/status'):
        return False
    if not require_origin(h):
        _reply(h, {'ok': False, 'error': 'origin_or_csrf_required'}, 403)
        return True
    if not isinstance(data, dict):
        _reply(h, {'ok': False, 'error': 'bad_request'}, 400)
        return True
    kind = u.path.rsplit('/',1)[-1]
    if kind in ('setup','activate','login') and limited(h,kind,data.get('email','')):
        _reply(h, {'ok': False, 'error': 'rate_limited'}, 429)
        return True
    try:
        if u.path == '/api/admin/setup':
            _setup(h,data)
            return True
        if u.path == '/api/admin/activate':
            _activate(h,data)
            return True
        if u.path == '/api/admin/login':
            _login(h,data)
            return True
        admin = admin_for_request(h,needs_csrf=True)
        if not admin:
            _reply(h, {'ok': False, 'error': 'admin_csrf_or_login_required'}, 403)
            return True
        if u.path == '/api/admin/logout':
            _logout(h,admin)
            return True
        if u.path == '/api/admin/teacher/status':
            tid = str(data.get('teacherId') or '')
            status = data.get('disabled')
            note = str(data.get('reason') or '').strip()
            if not re.fullmatch(r'[0-9a-f]{32}', tid) or type(status) is not bool or len(note)<8:
                _reply(h, {'ok': False, 'error': 'invalid_change'}, 400)
                return True
            row = sql('SELECT id,admin_disabled FROM teachers WHERE id=?',(tid,))
            if not row:
                _reply(h, {'ok': False, 'error': 'not_found'}, 404)
                return True
            value = int(status)
            if int(row['admin_disabled'])!=value:
                store.exec_sql('UPDATE teachers SET admin_disabled=? WHERE id=?',(value,tid))
                if value:
                    store.exec_sql('DELETE FROM auth_sessions WHERE teacher_id=?',(tid,))
                audit(admin['id'], 'teacher_disabled' if value else 'teacher_enabled',
                      'teacher',tid,note)
            _reply(h, {'ok': True, 'disabled': status})
            return True
    except Exception as e:
        h.log_message('admin request failed: %s', type(e).__name__)
        _reply(h, {'ok': False, 'error': 'admin_server_error'}, 500)
    return True
