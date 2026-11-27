"""Standalone school pilot for TAG Smart Math. Python standard library only.

Run: python server.py --demo
Production: configure independent persistent DATA_DIR, HTTPS, accounts, and backups.
Never mount this service within the official TAG application.
"""
import argparse
import csv
import hashlib
import hmac
import io
import json
import os
import secrets
import sqlite3
import sys
import time
import urllib.parse
from contextlib import contextmanager
from datetime import datetime, timezone
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from math_engine import SKILL_NAMES, make_questions, parse_answer

BASE=Path(__file__).resolve().parent
PUBLIC=BASE/'public'
DB_FILE=Path(os.environ.get('DATA_DIR',BASE/'private_data'))/'tag_school.sqlite3'
SESSION_SECONDS=60*60*12
LOGINS={}
LOGIN_LOCK=Lock()
DEMO_MODE=False
FORCE_SECURE_COOKIE=os.environ.get('SECURE_COOKIE','0')=='1'

class ApiError(Exception):
    def __init__(self,status,message,code='error',extra=None):
        self.status,self.message,self.code,self.extra=status,message,code,extra or {}

def db_connect():
    c=sqlite3.connect(DB_FILE,timeout=12, isolation_level=None,check_same_thread=True)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA foreign_keys = ON')
    c.execute('PRAGMA busy_timeout = 12000')
    return c

@contextmanager
def tx(conn):
    conn.execute('BEGIN IMMEDIATE')
    try:
        yield conn
        conn.commit()
    except:
        conn.rollback()
        raise

@contextmanager
def db_session():
    conn=db_connect()
    try:yield conn
    finally:conn.close()

def utcnow():return datetime.now(timezone.utc).isoformat()
def password_hash(password,salt=None):
    salt=salt or secrets.token_bytes(20)
    h=hashlib.pbkdf2_hmac('sha256',password.encode('utf-8'),salt,260_000)
    return salt.hex(),h.hex()
def verify_password(password,salt,h):
    computed=password_hash(password,bytes.fromhex(salt))[1]
    return hmac.compare_digest(computed,h)

def init_database(demo=False):
    DB_FILE.parent.mkdir(parents=True,exist_ok=True)
    with db_session() as c:
        c.execute('PRAGMA journal_mode = WAL')
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(
          id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE, display_name TEXT NOT NULL,
          role TEXT NOT NULL CHECK(role IN ('student','teacher')),
          classroom TEXT NOT NULL, salt TEXT NOT NULL, password_digest TEXT NOT NULL,
          created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(
          token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          csrf TEXT NOT NULL, expires INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS assignments(
          id TEXT PRIMARY KEY, teacher_id TEXT NOT NULL REFERENCES users(id), classroom TEXT NOT NULL,
          title TEXT NOT NULL, lesson_id TEXT NOT NULL DEFAULT 'u3l1', question_count INTEGER NOT NULL,
          mode TEXT NOT NULL CHECK(mode IN ('practice','exam')),
          max_attempts INTEGER NOT NULL, due_at TEXT, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS attempts(
          id TEXT PRIMARY KEY, assignment_id TEXT NOT NULL REFERENCES assignments(id),
          student_id TEXT NOT NULL REFERENCES users(id), seed INTEGER NOT NULL,
          status TEXT NOT NULL CHECK(status IN ('active','finished','abandoned')),
          next_index INTEGER NOT NULL DEFAULT 0, correct_count INTEGER NOT NULL DEFAULT 0,
          started_at TEXT NOT NULL, finished_at TEXT);
        CREATE INDEX IF NOT EXISTS ix_attempt_student ON attempts(student_id,assignment_id);
        CREATE TABLE IF NOT EXISTS questions(
          attempt_id TEXT NOT NULL REFERENCES attempts(id) ON DELETE CASCADE, idx INTEGER NOT NULL,
          prompt TEXT NOT NULL, math TEXT NOT NULL, skill TEXT NOT NULL, phase TEXT NOT NULL,
          answer INTEGER NOT NULL, kind TEXT NOT NULL, options_json TEXT NOT NULL,
          hint TEXT NOT NULL, steps_json TEXT NOT NULL,
          PRIMARY KEY(attempt_id,idx));
        CREATE TABLE IF NOT EXISTS responses(
          attempt_id TEXT NOT NULL, idx INTEGER NOT NULL, answer_text TEXT NOT NULL,
          is_correct INTEGER NOT NULL, submitted_at TEXT NOT NULL,
          PRIMARY KEY(attempt_id,idx),
          FOREIGN KEY(attempt_id,idx) REFERENCES questions(attempt_id,idx));
        ''')
        if demo and not c.execute('SELECT 1 FROM users LIMIT 1').fetchone():
            pw=os.environ.get('PILOT_PASSWORD','TagMath!Demo2026')
            for id,name,role,cl,display in [
                ('t01','teacher','teacher','السابع أ','معلم الرياضيات التجريبي'),
                ('s01','student01','student','السابع أ','طالب تجريبي 1'),
                ('s02','student02','student','السابع أ','طالب تجريبي 2'),
                ('s03','student03','student','السابع أ','طالب تجريبي 3'),
                ('s04','student04','student','السابع أ','طالب تجريبي 4'),
                ('s05','student05','student','السابع أ','طالب تجريبي 5'),
                ('s06','student06','student','السابع ب','طالب تجريبي - شعبة ب'),
            ]:
                salt,digest=password_hash(pw)
                c.execute('INSERT INTO users VALUES(?,?,?,?,?,?,?,?)',(id,name,display,role,cl,salt,digest,utcnow()))
            c.execute('INSERT INTO assignments VALUES(?,?,?,?,?,?,?,?,?,?)',('demo-equations-30','t01','السابع أ','تدريب حل المعادلات — 30 سؤالًا','u3l1',30,'practice',5,None,utcnow()))

def sanitize_text(s,maxlen=100):
    s=str(s).strip()
    if len(s)>maxlen:raise ApiError(400,'النص أطول من المسموح')
    return s

def public_question(row):
    if row is None:return None
    return {'index':row['idx'],'prompt':row['prompt'],'math':row['math'],
            'skill':row['skill'],'skill_name':SKILL_NAMES.get(row['skill'],row['skill']),
            'phase':row['phase'],'kind':row['kind'],'options':json.loads(row['options_json'])}

def get_user_from_token(conn, token):
    if not token: return None
    token_hash=hashlib.sha256(token.encode()).hexdigest()
    row=conn.execute('SELECT u.*,s.csrf,s.expires FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=?',(token_hash,)).fetchone()
    return row if row and row['expires']>int(time.time()) else None

def login_limit(ip,user):
    key=(ip,user)
    with LOGIN_LOCK:
        now=time.monotonic()
        vals=[t for t in LOGINS.get(key,[]) if now-t<600]
        if len(vals)>=8:raise ApiError(429,'محاولات كثيرة، أعد المحاولة لاحقًا')
        vals.append(now); LOGINS[key]=vals

def safe_csv_cell(value):
    s=str(value or '')
    return "'"+s if s.lstrip().startswith(('=','+','-','@')) else s

class Handler(BaseHTTPRequestHandler):
    server_version='TAGSchoolPilot/1.0'
    def log_message(self,fmt,*args):
        # Avoid logging session tokens, passwords, paths with identifiers.
        sys.stderr.write('[school] %s %s\n'%(self.address_string(),fmt%args if not ('/api/' in fmt%args) else 'API request'))
    def _headers(self,status,content_type='application/json; charset=utf-8',extra=None):
        self.send_response(status)
        self.send_header('Content-Type',content_type)
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Permissions-Policy','camera=(), microphone=(), geolocation=()')
        if content_type.startswith('text/html') and self.path.startswith('/school'):
            self.send_header('Content-Security-Policy',"default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
        if extra:
            for k,v in extra.items():self.send_header(k,str(v))
        self.end_headers()
    def out_json(self,obj,status=200,extra=None):
        data=json.dumps(obj,ensure_ascii=False).encode('utf-8')
        self._headers(status,extra=extra)
        self.wfile.write(data)
    def out_text(self,data,ctype,status=200,extra=None):
        self._headers(status,ctype,extra)
        self.wfile.write(data)
    def parse_json(self):
        try:size=int(self.headers.get('Content-Length','0'))
        except ValueError:raise ApiError(400,'بيانات الطلب غير صالحة')
        if size<1 or size>16_000:raise ApiError(413,'الطلب كبير أو فارغ')
        try:
            value=json.loads(self.rfile.read(size).decode('utf-8'))
            if not isinstance(value,dict):raise ValueError()
            return value
        except (ValueError,UnicodeDecodeError):raise ApiError(400,'JSON غير صالح')
    def token(self):
        try:
            cookie=SimpleCookie();cookie.load(self.headers.get('Cookie',''))
            return cookie['tag_math_session'].value if 'tag_math_session' in cookie else ''
        except Exception:return ''
    def user(self,conn,require_role=None):
        row=get_user_from_token(conn,self.token())
        if row is None:raise ApiError(401,'سجّل الدخول أولًا','not_authenticated')
        if require_role and row['role']!=require_role:raise ApiError(403,'لا تملك صلاحية لهذا الإجراء','forbidden')
        return row
    def csrf(self,user):
        if not hmac.compare_digest(self.headers.get('X-CSRF-Token',''),user['csrf']):
            raise ApiError(403,'رمز حماية الطلب غير صحيح','csrf')
    def check_origin(self):
        origin=self.headers.get('Origin')
        if origin:
            proto='https' if FORCE_SECURE_COOKIE or self.headers.get('X-Forwarded-Proto')=='https' else 'http'
            allowed=f'{proto}://{self.headers.get("Host","")}'
            if origin!=allowed:raise ApiError(403,'مصدر الطلب غير مصرح به','origin')
    def handle_request(self,method):
        path=urllib.parse.urlparse(self.path).path
        try:
            if method=='GET' and not path.startswith('/api/'):
                routes={'/':'index.html','/school':'school.html','/school.html':'school.html','/school.css':'school.css','/school.js':'school.js','/favicon.ico':None}
                if path not in routes:raise ApiError(404,'الصفحة غير موجودة')
                fname=routes[path]
                if fname is None:return self.out_text(b'','image/x-icon',204)
                typ='text/html; charset=utf-8' if fname.endswith('.html') else 'text/css; charset=utf-8' if fname.endswith('.css') else 'text/javascript; charset=utf-8'
                return self.out_text((PUBLIC/fname).read_bytes(),typ)
            if method=='GET' and path=='/api/health':return self.out_json({'ok':True,'service':'independent-school-pilot'})
            self.check_origin()
            with db_session() as c:
                if method=='POST' and path=='/api/login':
                    data=self.parse_json()
                    username=sanitize_text(data.get('username',''),80).lower()
                    password=data.get('password','')
                    if not isinstance(password,str) or len(password)>128:raise ApiError(400,'بيانات الدخول غير صالحة')
                    login_limit(self.client_address[0],username)
                    row=c.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
                    # Perform PBKDF2 even for unknown usernames.
                    if row:
                        valid=verify_password(password,row['salt'],row['password_digest'])
                    else:
                        verify_password(password,'00'*20,'00'*32)
                        valid=False
                    if not valid:raise ApiError(401,'اسم المستخدم أو كلمة المرور غير صحيحة','bad_login')
                    token=secrets.token_urlsafe(40);csrf=secrets.token_urlsafe(32)
                    with tx(c):
                        c.execute('DELETE FROM sessions WHERE expires<?',(int(time.time()),))
                        c.execute('INSERT INTO sessions VALUES(?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),row['id'],csrf,int(time.time())+SESSION_SECONDS))
                    cookie=f'tag_math_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={SESSION_SECONDS}'
                    if FORCE_SECURE_COOKIE:cookie+='; Secure'
                    return self.out_json({'ok':True,'role':row['role']},extra={'Set-Cookie':cookie})
                user=self.user(c)
                if method=='GET' and path=='/api/me':
                    return self.out_json({'id':user['id'],'display_name':user['display_name'],
                        'classroom':user['classroom'],'role':user['role'],'csrf':user['csrf'],
                        'demo':DEMO_MODE})
                if method=='POST':self.csrf(user)
                if method=='POST' and path=='/api/logout':
                    with tx(c):c.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(self.token().encode()).hexdigest(),))
                    ck='tag_math_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'
                    if FORCE_SECURE_COOKIE:ck+='; Secure'
                    return self.out_json({'ok':True},extra={'Set-Cookie':ck})
                if method=='GET' and path=='/api/assignments':
                    if user['role']=='student':
                        rows=c.execute("SELECT a.*, (SELECT COUNT(*) FROM attempts t WHERE t.assignment_id=a.id AND t.student_id=? AND t.status='finished') AS finished, (SELECT id FROM attempts t WHERE t.assignment_id=a.id AND t.student_id=? AND t.status='active' ORDER BY started_at DESC LIMIT 1) AS active_id FROM assignments a WHERE classroom=? ORDER BY created_at DESC",(user['id'],user['id'],user['classroom'])).fetchall()
                    else:
                        rows=c.execute('SELECT a.* FROM assignments a WHERE teacher_id=? ORDER BY created_at DESC',(user['id'],)).fetchall()
                    return self.out_json({'items':[dict(r) for r in rows]})
                if method=='POST' and path=='/api/assignments':
                    self.user(c,'teacher');data=self.parse_json()
                    title=sanitize_text(data.get('title','تدريب المعادلات'),90)
                    classroom=data.get('classroom','السابع أ')
                    if classroom!=user['classroom']:raise ApiError(403,'لا يجوز إنشاء تكليف لشعبة أخرى')
                    count=data.get('count',30)
                    if type(count)!=int or count not in (5,10,15,30):raise ApiError(400,'عدد الأسئلة غير مسموح')
                    mode=data.get('mode','practice')
                    if mode not in ('practice','exam'):raise ApiError(400,'نمط التدريب غير مدعوم')
                    max_attempts=data.get('max_attempts',2)
                    if type(max_attempts)!=int or not 1<=max_attempts<=10:raise ApiError(400,'عدد المحاولات خارج النطاق')
                    due=data.get('due_at') or None
                    if due:
                        try:
                            dt=datetime.fromisoformat(due.replace('Z','+00:00'))
                            if dt.tzinfo is None:raise ValueError('Timezone required')
                        except (ValueError,AttributeError):raise ApiError(400,'الموعد يجب أن يتضمن المنطقة الزمنية')
                    aid=secrets.token_urlsafe(16)
                    with tx(c):c.execute('INSERT INTO assignments VALUES(?,?,?,?,?,?,?,?,?,?)',(aid,user['id'],classroom,title,'u3l1',count,mode,max_attempts,due,utcnow()))
                    return self.out_json({'ok':True,'assignment_id':aid},201)
                if method=='GET' and path=='/api/student/progress':
                    self.user(c,'student')
                    attempts=[dict(r) for r in c.execute('''SELECT t.id,t.assignment_id,t.started_at,t.finished_at,t.status,
                      t.correct_count,a.question_count,a.title FROM attempts t
                      JOIN assignments a ON a.id=t.assignment_id
                      WHERE t.student_id=? ORDER BY t.started_at DESC LIMIT 100''',(user['id'],)).fetchall()]
                    rows=c.execute('''SELECT q.skill,r.is_correct FROM responses r
                      JOIN attempts t ON t.id=r.attempt_id JOIN questions q ON q.attempt_id=r.attempt_id AND q.idx=r.idx
                      WHERE t.student_id=? AND t.status='finished' ''',(user['id'],)).fetchall()
                    for t in attempts:t['percent']=round(100*t['correct_count']/t['question_count']) if t['status']=='finished' else None
                    return self.out_json({'attempts':attempts,'skills':self._skill_stats(rows)})
                if method=='POST' and path=='/api/attempts/start':
                    self.user(c,'student');data=self.parse_json()
                    aid=sanitize_text(data.get('assignment_id',''),60)
                    reset=data.get('new',False)
                    if type(reset)!=bool:raise ApiError(400,'حالة المحاولة غير صحيحة')
                    with tx(c):
                        ass=c.execute('SELECT * FROM assignments WHERE id=? AND classroom=?',(aid,user['classroom'])).fetchone()
                        if not ass:raise ApiError(404,'التكليف غير موجود في شعبتك')
                        if ass['due_at'] and datetime.fromisoformat(ass['due_at'].replace('Z','+00:00')) < datetime.now(timezone.utc):raise ApiError(403,'انتهى موعد التكليف')
                        active=c.execute("SELECT id FROM attempts WHERE assignment_id=? AND student_id=? AND status='active' ORDER BY started_at DESC LIMIT 1",(aid,user['id'])).fetchone()
                        if active and not reset:raise ApiError(409,'هناك تدريب غير منتهٍ، اختر الاستكمال أو البدء من جديد','active_attempt',{'attempt_id':active['id']})
                        completed=c.execute("SELECT COUNT(*) AS n FROM attempts WHERE assignment_id=? AND student_id=? AND status='finished'",(aid,user['id'])).fetchone()['n']
                        if completed>=ass['max_attempts']:raise ApiError(403,'استنفدت محاولات التكليف')
                        if active and reset:c.execute("UPDATE attempts SET status='abandoned',finished_at=? WHERE id=?",(utcnow(),active['id']))
                        attempt_id=secrets.token_urlsafe(18);seed=secrets.randbits(62)
                        qs=make_questions(seed,ass['question_count'])
                        c.execute('INSERT INTO attempts VALUES(?,?,?,?,?,?,?,?,?)',(attempt_id,aid,user['id'],seed,'active',0,0,utcnow(),None))
                        for i,q in enumerate(qs):
                            c.execute('INSERT INTO questions VALUES(?,?,?,?,?,?,?,?,?,?,?)',(attempt_id,i,q['prompt'],q['math'],q['skill'],q['phase'],q['answer'],q['kind'],json.dumps(q['options'],ensure_ascii=False),q['hint'],json.dumps(q['steps'],ensure_ascii=False)))
                    return self.out_json({'attempt_id':attempt_id,'ok':True},201)
                if method=='GET' and path=='/api/attempts/incomplete':
                    self.user(c,'student')
                    rows=c.execute("SELECT t.id,t.assignment_id,t.next_index,t.started_at,a.title,a.question_count FROM attempts t JOIN assignments a ON a.id=t.assignment_id WHERE t.student_id=? AND t.status='active' ORDER BY t.started_at DESC",(user['id'],)).fetchall()
                    return self.out_json({'items':[dict(r) for r in rows]})
                parts=path.strip('/').split('/')
                if len(parts)>=3 and parts[0]=='api' and parts[1]=='attempts':
                    attempt_id=parts[2]
                    if len(attempt_id)>120:raise ApiError(400,'المعرف غير صالح')
                    ar=c.execute('SELECT t.*,a.title,a.question_count,a.mode,a.teacher_id,a.classroom FROM attempts t JOIN assignments a ON a.id=t.assignment_id WHERE t.id=?',(attempt_id,)).fetchone()
                    if not ar:raise ApiError(404,'المحاولة غير موجودة')
                    owner=user['role']=='student' and ar['student_id']==user['id']
                    teacher=user['role']=='teacher' and ar['teacher_id']==user['id']
                    if not (owner or teacher):raise ApiError(403,'لا يمكن الوصول إلى محاولة مستخدم آخر')
                    if method=='GET' and len(parts)==3:
                        if not owner:raise ApiError(403,'عرض السؤال الحالي للطالب فقط')
                        question=c.execute('SELECT * FROM questions WHERE attempt_id=? AND idx=?',(attempt_id,ar['next_index'])).fetchone() if ar['status']=='active' else None
                        return self.out_json({'id':ar['id'],'status':ar['status'],'title':ar['title'],
                            'count':ar['question_count'],'index':ar['next_index'],'correct':ar['correct_count'],'mode':ar['mode'],
                            'question':public_question(question)})
                    if method=='POST' and len(parts)==4 and parts[3]=='answer':
                        if not owner:raise ApiError(403,'إجابة الطالب فقط')
                        data=self.parse_json()
                        idx=data.get('index');value=data.get('answer')
                        if type(idx)!=int or not 0<=idx<ar['question_count']:raise ApiError(400,'رقم السؤال غير صحيح')
                        parsed=parse_answer(value)
                        if parsed is None:raise ApiError(400,'اكتب عددًا صحيحًا أو كسرًا يساويه')
                        with tx(c):
                            ar=c.execute('SELECT * FROM attempts WHERE id=?',(attempt_id,)).fetchone()
                            prior=c.execute('SELECT * FROM responses WHERE attempt_id=? AND idx=?',(attempt_id,idx)).fetchone()
                            if prior:
                                if prior['answer_text']==str(parsed):
                                    return self._answer_result(c,attempt_id,idx,ar,True)
                                raise ApiError(409,'تم تسجيل إجابة مختلفة سابقًا؛ لا يمكن تغييرها','already_answered')
                            if ar['status']!='active':raise ApiError(409,'المحاولة مغلقة')
                            if idx!=ar['next_index']:raise ApiError(409,'يجب حل السؤال الحالي أولًا','out_of_order')
                            q=c.execute('SELECT * FROM questions WHERE attempt_id=? AND idx=?',(attempt_id,idx)).fetchone()
                            is_correct=int(parsed==q['answer'])
                            c.execute('INSERT INTO responses VALUES(?,?,?,?,?)',(attempt_id,idx,str(parsed),is_correct,utcnow()))
                            next_idx=idx+1; finished=next_idx>=int(c.execute('SELECT COUNT(*) n FROM questions WHERE attempt_id=?',(attempt_id,)).fetchone()['n'])
                            c.execute('UPDATE attempts SET next_index=?,correct_count=correct_count+?,status=?,finished_at=? WHERE id=?',(next_idx,is_correct,'finished' if finished else 'active',utcnow() if finished else None,attempt_id))
                            ar=c.execute('SELECT * FROM attempts WHERE id=?',(attempt_id,)).fetchone()
                            return self._answer_result(c,attempt_id,idx,ar,False)
                    if method=='POST' and len(parts)==4 and parts[3]=='abandon':
                        if not owner:raise ApiError(403,'محاولة الطالب فقط')
                        with tx(c):c.execute("UPDATE attempts SET status='abandoned',finished_at=? WHERE id=? AND student_id=? AND status='active'",(utcnow(),attempt_id,user['id']))
                        return self.out_json({'ok':True})
                    if method=='GET' and len(parts)==4 and parts[3]=='result':
                        if ar['status']!='finished' and not teacher:raise ApiError(409,'النتائج النهائية بعد التسليم فقط')
                        rows=c.execute('''SELECT q.idx,q.skill,q.phase,q.math,q.prompt,q.answer,r.answer_text,r.is_correct
                        FROM questions q LEFT JOIN responses r ON r.attempt_id=q.attempt_id AND r.idx=q.idx
                        WHERE q.attempt_id=? ORDER BY q.idx''',(attempt_id,)).fetchall()
                        return self.out_json({'status':ar['status'],'count':ar['question_count'],'correct':ar['correct_count'],
                            'percent':round(ar['correct_count']/ar['question_count']*100),
                            'skills':self._skill_stats(rows),'review':[dict(q) for q in rows]})
                if method=='GET' and path.startswith('/api/teacher/report'):
                    self.user(c,'teacher')
                    query=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                    aid=query.get('assignment_id',[''])[0]
                    filters=['a.teacher_id=?'];params=[user['id']]
                    if aid:filters.append('a.id=?');params.append(aid)
                    rows=c.execute('''SELECT t.id,t.status,t.started_at,t.finished_at,t.correct_count,t.next_index,
                      a.title,a.question_count,a.classroom,u.display_name,u.id student_id
                      FROM attempts t JOIN assignments a ON a.id=t.assignment_id JOIN users u ON t.student_id=u.id
                      WHERE '''+' AND '.join(filters)+' ORDER BY t.started_at DESC',params).fetchall()
                    result=[]
                    for row in rows:
                        d=dict(row)
                        rr=c.execute('''SELECT q.skill,r.is_correct FROM responses r JOIN questions q ON q.attempt_id=r.attempt_id AND q.idx=r.idx WHERE r.attempt_id=?''',(row['id'],)).fetchall()
                        d['skills']=self._skill_stats(rr)
                        d['percent']=round(row['correct_count']*100/row['question_count']) if row['status']=='finished' else None
                        result.append(d)
                    if path.endswith('.csv'):
                        out=io.StringIO();w=csv.writer(out)
                        w.writerow(['الطالب','الشعبة','التكليف','الحالة','الأسئلة','الصحيحة','النسبة','التاريخ'])
                        for r in result:w.writerow([safe_csv_cell(r['display_name']),safe_csv_cell(r['classroom']),safe_csv_cell(r['title']),r['status'],r['question_count'],r['correct_count'],r['percent'] if r['percent'] is not None else '',r['started_at']])
                        return self.out_text(('\ufeff'+out.getvalue()).encode('utf-8'),'text/csv; charset=utf-8',extra={'Content-Disposition':'attachment; filename="tag-math-report.csv"'})
                    roster=[dict(x) for x in c.execute("SELECT id,display_name,classroom FROM users WHERE role='student' AND classroom IN (SELECT DISTINCT classroom FROM assignments WHERE teacher_id=?) ORDER BY display_name",(user['id'],))]
                    return self.out_json({'attempts':result,'students':roster,'skills':SKILL_NAMES})
            raise ApiError(404,'العنوان غير موجود')
        except ApiError as e:self.out_json({'error':e.message,'code':e.code,**e.extra},e.status)
        except (sqlite3.Error,ValueError) as e:
            sys.stderr.write(f'[school] request failure: {type(e).__name__}\n')
            self.out_json({'error':'خطأ داخلي، أعد المحاولة'},500)
        except Exception as e:
            sys.stderr.write(f'[school] unexpected error type: {type(e).__name__}\n')
            self.out_json({'error':'خطأ داخلي، أعد المحاولة'},500)
    def _skill_stats(self,rows):
        skills={}
        for q in rows:
            v=skills.setdefault(q['skill'],{'name':SKILL_NAMES.get(q['skill'],q['skill']),'total':0,'correct':0})
            if q['is_correct'] is not None:
                v['total']+=1;v['correct']+=q['is_correct']
        for v in skills.values():
            v['rate']=round(100*v['correct']/v['total']) if v['total'] else 0
            v['level']=('بيانات أولية' if v['total']<5 else 'يحتاج دعم' if v['rate']<55 else 'في مرحلة التقدم' if v['rate']<75 else 'جيد')
        return skills
    def _answer_result(self,conn,aid,idx,attempt,replay):
        q=conn.execute('SELECT * FROM questions WHERE attempt_id=? AND idx=?',(aid,idx)).fetchone()
        resp=conn.execute('SELECT * FROM responses WHERE attempt_id=? AND idx=?',(aid,idx)).fetchone()
        mode=conn.execute('SELECT a.mode FROM assignments a JOIN attempts t ON t.assignment_id=a.id WHERE t.id=?',(aid,)).fetchone()['mode']
        payload={'ok':True,'replay':replay,'index':idx,'next_index':attempt['next_index'],
                 'finished':attempt['status']=='finished','correct_count':attempt['correct_count']}
        if mode=='practice' or attempt['status']=='finished':
            payload['feedback']={'correct':bool(resp['is_correct']),'expected':q['answer'],
                                 'hint':q['hint'],'steps':json.loads(q['steps_json'])}
        return self.out_json(payload)
    def do_GET(self):self.handle_request('GET')
    def do_POST(self):self.handle_request('POST')
    def do_OPTIONS(self):self._headers(405)

def main():
    global DB_FILE,DEMO_MODE,FORCE_SECURE_COOKIE
    a=argparse.ArgumentParser()
    a.add_argument('--host',default='127.0.0.1')
    a.add_argument('--port',type=int,default=int(os.environ.get('PORT','8765')))
    a.add_argument('--demo',action='store_true')
    a.add_argument('--allow-lan-demo',action='store_true')
    a.add_argument('--data-dir',default=None)
    args=a.parse_args()
    if args.data_dir:DB_FILE=Path(args.data_dir)/'tag_school.sqlite3'
    if args.demo and args.host not in ('127.0.0.1','localhost','::1') and not args.allow_lan_demo:
        sys.exit('Demo accounts require local-only binding. Use --allow-lan-demo explicitly for trusted private networks.')
    if not args.demo and not FORCE_SECURE_COOKIE and args.host not in ('127.0.0.1','localhost','::1'):
        sys.exit('Public binding requires SECURE_COOKIE=1 and an HTTPS reverse proxy.')
    if args.demo and args.host not in ('127.0.0.1','localhost','::1') and FORCE_SECURE_COOKIE:
        demo_pw=os.environ.get('PILOT_PASSWORD','')
        if len(demo_pw)<18 or demo_pw=='TagMath!Demo2026':
            sys.exit('Public pilot requires a strong unique PILOT_PASSWORD environment secret.')
    DEMO_MODE=args.demo
    init_database(demo=DEMO_MODE)
    server=ThreadingHTTPServer((args.host,args.port),Handler)
    server.daemon_threads=True
    print(f'TAG SMART MATH independent school pilot: http://{args.host}:{args.port}/school',flush=True)
    if DEMO_MODE:print('DEMO TEST ACCOUNTS ONLY. Password configured privately.',flush=True)
    server.serve_forever()
if __name__=='__main__':main()
