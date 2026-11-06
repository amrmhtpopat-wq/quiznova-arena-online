"""QuizNova V9 authenticated teacher storage and progress analytics.
SQLite for local testing; PostgreSQL for hosted persistent deployment.
"""
import os, json, sqlite3, secrets, hashlib, hmac, re, time, threading, uuid
from pathlib import Path

DATABASE_URL = os.getenv('DATABASE_URL','').strip()
LOCAL_DB = os.getenv('QUIZNOVA_SQLITE_PATH',str(Path(__file__).resolve().parent/'quiznova_local.db'))
DATABASE_KIND = 'postgres' if DATABASE_URL else 'sqlite'
SCHOOL_TYPES = ('boys','girls','mixed')
AVATAR_3D_IDS = [f'n{i:02}' for i in range(1,9)] + [f'm{i:02}' for i in range(1,9)] + [f'b{i:02}' for i in range(1,17)] + [f'g{i:02}' for i in range(1,17)]
def avatar_pool(school_type):
    return [a for a in AVATAR_3D_IDS if school_type=='mixed' or (a[0] in ('b','m','n') if school_type=='boys' else a[0]=='g')]
def inferred_school_type(school):
    school=str(school or '')
    if any(x in school for x in ('للبنين','بنين','boys')):return 'boys'
    if any(x in school for x in ('للبنات','بنات','girls')):return 'girls'
    return 'mixed'

DB_LOCK=threading.RLock()
CARD_ALPHABET='ABCDEFGHJKLMNPQRSTUVWXYZ23456789'

def new_card_code():
    """Easy-to-type 40-bit random school card code, 4+4 characters.
    Existing QNA-... codes remain valid; full QR tokens are unchanged.
    """
    raw=''.join(secrets.choice(CARD_ALPHABET) for _ in range(8))
    return raw[:4]+'-'+raw[4:]

LEVEL_TITLES=('مبتدئ','متقدم','منافس','بطل الصف','نجم الشعبة','أسطورة بويا')

def xp_progress(xp):
    """Return the exact level bounds so every client uses one XP scale."""
    xp=max(0,int(xp))
    bounds=[0,100,250,450,700,1000]
    while xp>=bounds[-1]:
        bounds.append(bounds[-1]+350+50*(len(bounds)-6))
    level=next((i for i in range(1,len(bounds)) if xp<bounds[i]),len(bounds)-1)
    floor=bounds[level-1]
    ceiling=bounds[level]
    return {'level':level,'title':LEVEL_TITLES[min(level-1,len(LEVEL_TITLES)-1)],
            'startXp':floor,'nextXp':ceiling,'xpToNext':ceiling-xp,
            'percent':round((xp-floor)*100/(ceiling-floor))}

def level_for_xp(xp):
    return xp_progress(xp)['level']

def xp_gain_for_attempt(score,correct):
    """Base XP for correct answers; completion/rank/speed are added at room finish."""
    return max(0,int(correct))*10

def room_xp_awards(room):
    """Deterministic per-player XP; fastest 3 for the same question earn +5."""
    players=list(room.get('players',{}).values())
    fastest={}
    for player in players:
        for answer in player.get('answers',{}).values():
            if answer.get('correct') is True:
                qid=answer.get('questionIndex')
                fastest.setdefault(qid,[]).append((int(answer.get('elapsedMs',0)),player['id']))
    speed_bonus={p['id']:0 for p in players}
    for answers in fastest.values():
        for _,pid in sorted(answers,key=lambda item:(item[0],item[1]))[:3]:
            speed_bonus[pid]+=5
    ranking=sorted(players,key=lambda p:(-int(p.get('score',0)),-int(p.get('correct',0)),p['id']))
    first=ranking[0]['id'] if ranking else None
    total=len(room.get('quiz',{}).get('questions',[]))
    awards={}
    for p in players:
        base=xp_gain_for_attempt(p.get('score',0),p.get('correct',0))
        complete=10 if total and len(p.get('answers',{}))>=total else 0
        winner=20 if p['id']==first else 0
        fast=speed_bonus[p['id']]
        awards[p['id']]={'correct':base,'fastest':fast,'completion':complete,'firstPlace':winner,
                         'total':base+fast+complete+winner}
    return awards


def epoch(): return int(time.time())
def jdump(value): return json.dumps(value,ensure_ascii=False,separators=(',',':'))
def jload(raw,default):
    try:return json.loads(raw)
    except (TypeError,ValueError):return default

def db_connection():
    if DATABASE_URL:
        import psycopg
        conn=psycopg.connect(DATABASE_URL, connect_timeout=7)
        return conn
    conn=sqlite3.connect(LOCAL_DB,timeout=15)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA busy_timeout=15000')
    return conn

def sql(query):
    return query.replace('?', '%s') if DATABASE_URL else query

def query(query,args=(),many=False):
    with DB_LOCK:
        with db_connection() as con:
            cur=con.cursor()
            cur.execute(sql(query),args)
            if not cur.description:return None
            columns=[x[0] for x in cur.description]
            rows=[dict(zip(columns,row)) for row in cur.fetchall()]
            return rows if many else (rows[0] if rows else None)

def exec_sql(query_s,args=()): return query(query_s,args)

def init():
    commands=[
      'CREATE TABLE IF NOT EXISTS teachers (id TEXT PRIMARY KEY,email TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,salt TEXT NOT NULL,name TEXT NOT NULL,school TEXT NOT NULL,subject TEXT NOT NULL,created_at BIGINT NOT NULL)',
      'CREATE TABLE IF NOT EXISTS auth_sessions (token_hash TEXT PRIMARY KEY,teacher_id TEXT NOT NULL,expires_at BIGINT NOT NULL)',
      'CREATE TABLE IF NOT EXISTS datasets (teacher_id TEXT PRIMARY KEY,quizzes TEXT NOT NULL,bank TEXT NOT NULL,settings TEXT NOT NULL,results TEXT NOT NULL,updated_at BIGINT NOT NULL)',
      'CREATE TABLE IF NOT EXISTS students (id TEXT PRIMARY KEY,teacher_id TEXT NOT NULL,name TEXT NOT NULL,class_name TEXT NOT NULL,avatar TEXT NOT NULL,card_token TEXT UNIQUE NOT NULL,xp INTEGER NOT NULL DEFAULT 0,correct_count INTEGER NOT NULL DEFAULT 0,played_count INTEGER NOT NULL DEFAULT 0,created_at BIGINT NOT NULL)',
      'CREATE TABLE IF NOT EXISTS played_sessions (id TEXT PRIMARY KEY,teacher_id TEXT NOT NULL,code TEXT UNIQUE NOT NULL,section TEXT NOT NULL,subject TEXT NOT NULL,quiz_title TEXT NOT NULL,game_mode TEXT NOT NULL,played_at BIGINT NOT NULL,report TEXT NOT NULL,questions TEXT NOT NULL)',
      'CREATE TABLE IF NOT EXISTS student_attempts (id TEXT PRIMARY KEY,teacher_id TEXT NOT NULL,student_id TEXT,quiz_id TEXT NOT NULL,room_code TEXT NOT NULL,student_name TEXT NOT NULL,class_name TEXT NOT NULL,avatar TEXT NOT NULL,correct_count INTEGER NOT NULL,question_total INTEGER NOT NULL,percent INTEGER NOT NULL,score INTEGER NOT NULL,answers TEXT NOT NULL,created_at BIGINT NOT NULL)',
      'CREATE TABLE IF NOT EXISTS active_rooms (code TEXT PRIMARY KEY, snapshot TEXT NOT NULL, updated_at BIGINT NOT NULL)',
      'CREATE TABLE IF NOT EXISTS student_card_aliases (alias TEXT PRIMARY KEY, student_id TEXT NOT NULL, teacher_id TEXT NOT NULL, created_at BIGINT NOT NULL)',
      'CREATE INDEX IF NOT EXISTS idx_active_rooms_updated ON active_rooms (updated_at)',
      'CREATE INDEX IF NOT EXISTS idx_students_teacher ON students (teacher_id)',
      'CREATE INDEX IF NOT EXISTS idx_rooms_teacher ON played_sessions (teacher_id)',
      'CREATE INDEX IF NOT EXISTS idx_attempts_student ON student_attempts (student_id,quiz_id)',
    ]
    with DB_LOCK:
        with db_connection() as con:
            for stmt in commands:con.execute(stmt)
            if DATABASE_URL:
                cur=con.execute("SELECT column_name FROM information_schema.columns WHERE table_name='teachers' AND column_name='school_type'")
                has_school_type=bool(cur.fetchone())
            else:
                cols=[r[1] for r in con.execute('PRAGMA table_info(teachers)').fetchall()]
                has_school_type='school_type' in cols
            if not has_school_type:
                con.execute("ALTER TABLE teachers ADD COLUMN school_type TEXT NOT NULL DEFAULT 'mixed'")
                con.execute("UPDATE teachers SET school_type='boys' WHERE school LIKE '%بنين%'")
                con.execute("UPDATE teachers SET school_type='girls' WHERE school LIKE '%بنات%'")
            # Additive account-activity and access-plan fields; legacy data stays unchanged.
            if DATABASE_URL:
                teacher_columns={x[0] for x in con.execute(
                    "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='teachers'").fetchall()}
            else:
                teacher_columns={x[1] for x in con.execute('PRAGMA table_info(teachers)').fetchall()}
            if 'last_login' not in teacher_columns:
                con.execute('ALTER TABLE teachers ADD COLUMN last_login BIGINT NOT NULL DEFAULT 0')
            if 'access_plan' not in teacher_columns:
                con.execute("ALTER TABLE teachers ADD COLUMN access_plan TEXT NOT NULL DEFAULT 'free'")
            if DATABASE_URL:
                present=bool(con.execute("SELECT 1 FROM information_schema.columns WHERE table_name='students' AND column_name='card_code'").fetchone())
            else:
                present='card_code' in [x[1] for x in con.execute('PRAGMA table_info(students)').fetchall()]
            if not present:
                con.execute('ALTER TABLE students ADD COLUMN card_code TEXT')
            if DATABASE_URL:
                student_columns={x[0] for x in con.execute(
                    "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='students'").fetchall()}
            else:
                student_columns={x[1] for x in con.execute('PRAGMA table_info(students)').fetchall()}
            if 'archived' not in student_columns:
                con.execute('ALTER TABLE students ADD COLUMN archived INTEGER NOT NULL DEFAULT 0')
            con.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_students_card_code ON students (card_code)')
            # Backfill legacy cards without changing their existing QR bearer tokens.
            old=con.execute("SELECT id FROM students WHERE card_code IS NULL OR card_code=''").fetchall()
            for (sid,) in old:
                for _ in range(12):
                    candidate=new_card_code()
                    if not con.execute(sql('SELECT id FROM students WHERE card_code=?'),(candidate,)).fetchone():break
                else:raise RuntimeError('card_code_collision')
                con.execute(sql('UPDATE students SET card_code=? WHERE id=?'),(candidate,sid))


def password_hash(password,salt):return hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),300000).hex()
def token_hash(token):return hashlib.sha256(token.encode()).hexdigest()

def teacher_public(row):return {k:row[k] for k in ('id','name','email','school','subject','school_type','created_at')}

def create_teacher(email,password,name,school,subject,school_type='mixed'):
    email=email.strip().lower()[:160];name=name.strip()[:120];school=school.strip()[:180];subject=subject.strip()[:100]
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',email):raise ValueError('invalid_email')
    if len(password)<10 or len(password)>160:raise ValueError('weak_password')
    if len(name)<2:raise ValueError('name_required')
    if school_type not in SCHOOL_TYPES: school_type=inferred_school_type(school)
    existing=query('SELECT id FROM teachers WHERE email=?',(email,))
    if existing:raise ValueError('email_taken')
    tid=uuid.uuid4().hex; salt=secrets.token_hex(16)
    exec_sql('INSERT INTO teachers(id,email,password_hash,salt,name,school,subject,school_type,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(tid,email,password_hash(password,salt),salt,name,school,subject,school_type,epoch()))
    exec_sql('INSERT INTO datasets (teacher_id,quizzes,bank,settings,results,updated_at) VALUES(?,?,?,?,?,?)',(tid,'[]','[]',jdump({'teacherName':name,'schoolName':school,'platformName':'BOOYAHJO','scene':'cartoon'}),'[]',epoch()))
    return login(email,password)

def login(email,password):
    row=query('SELECT * FROM teachers WHERE email=?',(email.strip().lower(),))
    if not row:
        # minimize account discovery timing disparity
        password_hash(password,'0'*32)
        raise ValueError('wrong_credentials')
    good=hmac.compare_digest(password_hash(password,row['salt']),row['password_hash'])
    if not good or int(row.get('admin_disabled', 0)) == 1: raise ValueError('wrong_credentials')
    token=secrets.token_urlsafe(40)
    exec_sql('INSERT INTO auth_sessions(token_hash,teacher_id,expires_at) VALUES(?,?,?)',(token_hash(token),row['id'],epoch()+14*86400))
    exec_sql('UPDATE teachers SET last_login=? WHERE id=?',(epoch(),row['id']))
    return {'token':token,'teacher':teacher_public(row)}

def teacher_for_token(token):
    if not token or len(token)>200:return None
    row=query('SELECT t.* FROM auth_sessions a JOIN teachers t ON t.id=a.teacher_id WHERE a.token_hash=? AND a.expires_at>?',(token_hash(token),epoch()))
    return teacher_public(row) if row and int(row.get('admin_disabled',0)) == 0 else None

def signout(token):
    if token:exec_sql('DELETE FROM auth_sessions WHERE token_hash=?',(token_hash(token),))

def snapshot(teacher_id):
    row=query('SELECT * FROM datasets WHERE teacher_id=?',(teacher_id,))
    if not row: return {'quizzes':[],'bank':[],'settings':{},'results':[]}
    return {k:jload(row[k], [] if k!='settings' else {}) for k in ('quizzes','bank','settings','results')}

def save_snapshot(teacher_id,data):
    row=snapshot(teacher_id)
    for field in ('quizzes','bank','settings','results'):
        if field in data:
            val=data[field]
            if not isinstance(val,dict if field=='settings' else list):raise ValueError('invalid_'+field)
            if len(jdump(val))>9_000_000:raise ValueError('too_large')
            row[field]=val
    exec_sql('UPDATE datasets SET quizzes=?,bank=?,settings=?,results=?,updated_at=? WHERE teacher_id=?',(jdump(row['quizzes']),jdump(row['bank']),jdump(row['settings']),jdump(row['results']),epoch(),teacher_id))
    return {'ok':True}

def add_students(teacher_id,students):
    created=[]
    if len(students)>450:raise ValueError('too_many_students')
    for item in students:
        name=str(item.get('name','')).strip()[:90]; cls=str(item.get('className','')).strip()[:65]
        allowed=avatar_pool(teacher_school_type(teacher_id))
        avatar=str(item.get('avatar','b01')).strip()
        if avatar not in allowed:avatar=allowed[0]
        if not name or not cls:continue
        duplicate=query('SELECT id FROM students WHERE teacher_id=? AND archived=0 AND name=? AND class_name=?',(teacher_id,name,cls))
        if duplicate:continue
        sid=uuid.uuid4().hex;card=secrets.token_urlsafe(24)
        code=new_card_code()
        for _ in range(12):
            if not query('SELECT id FROM students WHERE card_code=?',(code,)):break
            code=new_card_code()
        else:raise RuntimeError('card_code_collision')
        exec_sql('INSERT INTO students (id,teacher_id,name,class_name,avatar,card_token,card_code,created_at) VALUES (?,?,?,?,?,?,?,?)',(sid,teacher_id,name,cls,avatar,card,code,epoch()))
        created.append({'id':sid,'name':name,'className':cls,'avatar':avatar,'card':card,'cardCode':code})
    return created


def edit_student_card(teacher_id,student_id,name,class_name,avatar):
    """Edits the visible student card without regenerating any QR or access code."""
    if not re.fullmatch(r'[0-9a-f]{32}',str(student_id or '')):
        raise ValueError('invalid_student')
    name=str(name or '').strip()[:90]
    class_name=str(class_name or '').strip()[:65]
    if len(name)<2 or not class_name:
        raise ValueError('student_name_class_required')
    allowed=avatar_pool(teacher_school_type(teacher_id))
    if avatar not in allowed:raise ValueError('invalid_avatar')
    row=query('SELECT id FROM students WHERE id=? AND teacher_id=? AND archived=0',(student_id,teacher_id))
    if not row:raise ValueError('student_not_found')
    other=query('SELECT id FROM students WHERE teacher_id=? AND archived=0 AND name=? AND class_name=? AND id<>?',
               (teacher_id,name,class_name,student_id))
    if other:raise ValueError('student_duplicate')
    exec_sql('UPDATE students SET name=?,class_name=?,avatar=? WHERE id=? AND teacher_id=? AND archived=0',
             (name,class_name,avatar,student_id,teacher_id))
    return {'id':student_id,'name':name,'className':class_name,'avatar':avatar}


def archive_student_card(teacher_id,student_id):
    """Revoke a student card but retain existing results/XP for historical reporting."""
    if not re.fullmatch(r'[0-9a-f]{32}',str(student_id or '')):
        raise ValueError('invalid_student')
    row=query('SELECT id FROM students WHERE id=? AND teacher_id=? AND archived=0',(student_id,teacher_id))
    if not row:raise ValueError('student_not_found')
    exec_sql('UPDATE students SET archived=1 WHERE id=? AND teacher_id=? AND archived=0',
             (student_id,teacher_id))
    return {'id':student_id,'archived':True}

def shorten_student_codes(teacher_id):
    """Opt-in only: issue memorable short codes while old printed codes remain valid."""
    updated=0
    with DB_LOCK:
        with db_connection() as con:
            rows=con.execute(sql('SELECT id,card_code FROM students WHERE teacher_id=? AND card_code LIKE ?'),(teacher_id,'QNA-%')).fetchall()
            for sid,old_code in rows:
                for _ in range(30):
                    candidate=new_card_code()
                    exists=con.execute(sql('SELECT id FROM students WHERE card_code=?'),(candidate,)).fetchone()
                    alias=con.execute(sql('SELECT student_id FROM student_card_aliases WHERE alias=?'),(candidate,)).fetchone()
                    if not exists and not alias:break
                else:raise RuntimeError('card_code_collision')
                con.execute(sql('INSERT INTO student_card_aliases(alias,student_id,teacher_id,created_at) VALUES(?,?,?,?)'),
                            (old_code,sid,teacher_id,epoch()))
                con.execute(sql('UPDATE students SET card_code=? WHERE id=? AND teacher_id=?'),(candidate,sid,teacher_id))
                updated+=1
    return updated

def list_students(teacher_id):
    rows=query('SELECT id,name,class_name,avatar,card_token,card_code,xp,correct_count,played_count FROM students WHERE teacher_id=? AND archived=0 ORDER BY class_name,name',(teacher_id,),True)
    return [{'id':r['id'],'name':r['name'],'className':r['class_name'],'avatar':r['avatar'],'card':r['card_token'],'cardCode':r['card_code'],'xp':r['xp'],'level':level_for_xp(r['xp']),'progress':xp_progress(r['xp']),'correct':r['correct_count'],'played':r['played_count']} for r in rows]

def student_profile_by_card(token):
    """A physical student card permits access to a limited student profile."""
    value=str(token or '').strip()
    if not value or len(value)>90:return None
    return query('SELECT id,name,class_name,avatar,xp,correct_count,played_count FROM students WHERE archived=0 AND (card_token=? OR card_code=? OR id IN (SELECT student_id FROM student_card_aliases WHERE alias=?))',(value,value.upper(),value.upper()))

def student_by_card(token,teacher_id):
    token=str(token or '').strip()
    if not token or len(token)>90 or not teacher_id:return None
    # Accept the original QR token or the new printed card code.
    return query('SELECT * FROM students WHERE archived=0 AND (card_token=? OR card_code=? OR id IN (SELECT student_id FROM student_card_aliases WHERE alias=? AND teacher_id=?)) AND teacher_id=?',(token,token.upper(),token.upper(),teacher_id,teacher_id))

def attempt_count(sid,quiz_id):
    row=query('SELECT COUNT(*) AS c FROM student_attempts WHERE student_id=? AND quiz_id=?',(sid,quiz_id))
    return int(row['c'] or 0)

def persist_room(room,report,questions):
    """Atomically record results and award durable XP exactly once per finished room."""
    if not room.get('teacherId'):return
    tid=room['teacherId'];code=room['code']
    total=sum(1 for q in room['quiz']['questions'] if q.get('type')!='poll')
    awards=room_xp_awards(room)
    with DB_LOCK:
        with db_connection() as con:
            existing=con.execute(sql('SELECT id FROM played_sessions WHERE code=?'),(code,)).fetchone()
            if existing:return
            con.execute(sql('INSERT INTO played_sessions(id,teacher_id,code,section,subject,quiz_title,game_mode,played_at,report,questions) VALUES (?,?,?,?,?,?,?,?,?,?)'),(
                uuid.uuid4().hex,tid,code,room.get('section',''),room.get('quiz',{}).get('subject','عام'),
                room['quiz'].get('title',''),room.get('gameMode',''),epoch(),jdump(report),jdump(questions)))
            for p in room['players'].values():
                correct=int(p.get('correct',0));pct=round(correct/total*100) if total else 100
                student_id=p.get('studentId')
                con.execute(sql('INSERT INTO student_attempts(id,teacher_id,student_id,quiz_id,room_code,student_name,class_name,avatar,correct_count,question_total,percent,score,answers,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)'),(
                    uuid.uuid4().hex,tid,student_id,room['quiz'].get('id',''),code,p['name'],
                    room.get('section',''),p.get('avatar','01'),correct,total,pct,p.get('score',0),jdump(p.get('answers',{})),epoch()))
                if student_id:
                    breakdown=awards.get(p['id'],{})
                    gain=breakdown.get('total',0)
                    con.execute(sql('UPDATE students SET xp=xp+?,correct_count=correct_count+?,played_count=played_count+1 WHERE id=? AND teacher_id=?'),
                        (gain,correct,student_id,tid))
                    progress=con.execute(sql('SELECT xp,played_count FROM students WHERE id=? AND teacher_id=?'),(student_id,tid)).fetchone()
                    if progress:
                        p['xpGain']=gain
                        p['xpBreakdown']=breakdown
                        p['xp']=int(progress[0])
                        p['level']=level_for_xp(p['xp'])
                        p['levelUp']=level_for_xp(max(0,p['xp']-gain))<p['level']
    try:
        from platform_security import auto_backup
        auto_backup(tid)
    except Exception as exc:
        print('[QuizNova backup] automatic backup failed:',type(exc).__name__)

def history(teacher_id,limit=100):
    rows=query('SELECT code,section,subject,quiz_title,game_mode,played_at,report,questions FROM played_sessions WHERE teacher_id=? ORDER BY played_at DESC LIMIT ?',(teacher_id,limit),True)
    return [{**{k:r[k] for k in ('code','section','subject','quiz_title','game_mode','played_at')},'report':jload(r['report'],[]),'questions':jload(r['questions'],[])} for r in rows]

def class_wars(teacher_id):
    rooms=history(teacher_id,300); classes={}
    for room in rooms:
        section=room.get('section') or 'غير محددة';sub=room.get('subject') or 'عام'
        key=(section,sub);slot=classes.setdefault(key,{'section':section,'subject':sub,'scores':[],'sessions':0,'participants':0})
        rows=room['report'];slot['scores'] += [int(r.get('percent',0)) for r in rows]
        slot['participants']+=len(rows);slot['sessions']+=1
    return sorted([{**{k:v for k,v in cls.items() if k!='scores'},'rating':round(sum(cls['scores'])/len(cls['scores']),1) if cls['scores'] else 0} for cls in classes.values()],key=lambda r:(r['rating'],r['participants']),reverse=True)

def mastery(teacher_id):
    rooms=history(teacher_id,300);stats={}
    for room in rooms:
        for q in room.get('questions',[]):
            skill=(q.get('skill') or q.get('unit') or 'مهارات عامة').strip()
            key=(room.get('subject','عام'),room.get('section','غير محددة'),skill)
            x=stats.setdefault(key,{'subject':key[0],'section':key[1],'skill':key[2],'correct':0,'total':0,'questions':0})
            x['correct']+=len(q.get('correctStudents',[]));x['total']+=len(q.get('correctStudents',[]))+len(q.get('wrongStudents',[]))+len(q.get('skippedStudents',[]));x['questions']+=1
    return [{**r,'rate':round(r['correct']*100/r['total']) if r['total'] else 0,'needsReview':(r['correct']*100/r['total']<70) if r['total'] else True} for r in stats.values()]

def dashboard(teacher_id):
    hist=history(teacher_id,80); students=list_students(teacher_id)
    percents=[r.get('percent',0) for ses in hist for r in ses.get('report',[])]
    return {'sessions':len(hist),'students':len(students),'attempts':len(percents),'average':round(sum(percents)/len(percents)) if percents else 0,
            'recent':[{k:v for k,v in ses.items() if k not in ('report','questions')} for ses in hist[:6]],'classes':class_wars(teacher_id)[:12],
            'mastery':mastery(teacher_id)[:60], 'dbKind':DATABASE_KIND}

# V10: school-specific avatar policy and recoverable live-room snapshots.
def teacher_school_type(teacher_id):
    row=query('SELECT school_type FROM teachers WHERE id=?',(teacher_id,))
    return (row or {}).get('school_type') or 'mixed'

def update_school_type(teacher_id,school_type):
    if school_type not in SCHOOL_TYPES:raise ValueError('invalid_school_type')
    exec_sql('UPDATE teachers SET school_type=? WHERE id=?',(school_type,teacher_id))
    return teacher_school_type(teacher_id)

def save_active_room(room):
    raw=jdump(room)
    if len(raw)>30_000_000:raise ValueError('room_too_large')
    code=room['code']
    exec_sql('DELETE FROM active_rooms WHERE code=?',(code,))
    exec_sql('INSERT INTO active_rooms(code,snapshot,updated_at) VALUES(?,?,?)',(code,raw,epoch()))

def recover_active_rooms(max_age_hours=72):
    cutoff=epoch()-max_age_hours*3600
    rows=query('SELECT code,snapshot FROM active_rooms WHERE updated_at>?',(cutoff,),True)
    result={}
    for row in rows:
        room=jload(row['snapshot'],{})
        if isinstance(room,dict) and room.get('code')==row['code']:
            result[row['code']]=room
    exec_sql('DELETE FROM active_rooms WHERE updated_at<?',(cutoff,))
    return result

def delete_active_room(code):
    exec_sql('DELETE FROM active_rooms WHERE code=?',(code,))
