"""QuizNova V10.3: password recovery, versioned sync, and per-teacher recoverable backups.

All data operations are scoped by authenticated teacher_id. No credentials or
reset tokens ever appear in backups or URLs returned to other users.
"""
import base64, hashlib, hmac, json, os, secrets, smtplib, ssl, time, uuid
from email.message import EmailMessage
import platform_store as store

FIELDS=('quizzes','bank','settings','results')
TABLES=('students','played_sessions','student_attempts')
BACKUP_RETENTION=14

def initialize():
    with store.DB_LOCK:
        with store.db_connection() as conn:
            if store.DATABASE_KIND=='postgres':
                cur=conn.execute("SELECT column_name FROM information_schema.columns WHERE table_name='datasets' AND column_name='revision'")
                exists=cur.fetchone() is not None
            else:
                exists='revision' in [r[1] for r in conn.execute('PRAGMA table_info(datasets)').fetchall()]
            if not exists:conn.execute('ALTER TABLE datasets ADD COLUMN revision INTEGER NOT NULL DEFAULT 0')
            conn.execute('CREATE TABLE IF NOT EXISTS password_resets (token_hash TEXT PRIMARY KEY, teacher_id TEXT NOT NULL, expires_at BIGINT NOT NULL, used_at BIGINT NOT NULL DEFAULT 0)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_password_resets_teacher ON password_resets (teacher_id)')
            conn.execute('CREATE TABLE IF NOT EXISTS teacher_backups (id TEXT PRIMARY KEY, teacher_id TEXT NOT NULL,created_at BIGINT NOT NULL,reason TEXT NOT NULL,payload TEXT NOT NULL)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_teacher_backups ON teacher_backups (teacher_id,created_at)')

def token_hash(token):return hashlib.sha256(str(token).encode()).hexdigest()

def smtp_ready():
    return all(os.getenv(k,'').strip() for k in ('SMTP_HOST','SMTP_USER','SMTP_PASSWORD','SMTP_FROM'))

def _mail_reset(recipient,token):
    base=(os.getenv('QUIZNOVA_PUBLIC_URL') or os.getenv('RENDER_EXTERNAL_URL') or '').strip().rstrip('/')
    if not base:raise RuntimeError('public_url_not_configured')
    from urllib.parse import quote
    link=f'{base}/?reset={quote(token,safe="")}'
    message=EmailMessage()
    message['Subject']='QuizNova Arena - إعادة تعيين كلمة المرور'
    message['From']=os.environ['SMTP_FROM'];message['To']=recipient
    message.set_content('تم طلب إعادة تعيين كلمة مرور حسابك في QuizNova.\n\n'+link+'\n\nينتهي الرابط خلال 20 دقيقة ويُستخدم مرة واحدة. إذا لم تطلب ذلك فتجاهل الرسالة.')
    host=os.environ['SMTP_HOST'];port=int(os.getenv('SMTP_PORT','587'))
    context=ssl.create_default_context()
    if port==465:
        with smtplib.SMTP_SSL(host,port,timeout=12,context=context) as smtp:
            smtp.login(os.environ['SMTP_USER'],os.environ['SMTP_PASSWORD']);smtp.send_message(message)
    else:
        with smtplib.SMTP(host,port,timeout=12) as smtp:
            smtp.starttls(context=context);smtp.login(os.environ['SMTP_USER'],os.environ['SMTP_PASSWORD']);smtp.send_message(message)

def request_password_reset(email):
    """Give identical generic result for unknown and known accounts, if mail configured."""
    if not smtp_ready() or not (os.getenv('QUIZNOVA_PUBLIC_URL') or os.getenv('RENDER_EXTERNAL_URL')):
        raise ValueError('email_not_configured')
    email=str(email or '').strip().lower()[:160]
    row=store.query('SELECT id FROM teachers WHERE email=?',(email,))
    if row:
        token=secrets.token_urlsafe(38)
        with store.DB_LOCK:
            with store.db_connection() as conn:
                conn.execute(store.sql('DELETE FROM password_resets WHERE teacher_id=?'),(row['id'],))
                conn.execute(store.sql('INSERT INTO password_resets(token_hash,teacher_id,expires_at,used_at) VALUES (?,?,?,0)'),(token_hash(token),row['id'],store.epoch()+20*60))
        try:_mail_reset(email,token)
        except Exception:
            # Do not leak SMTP failures or account existence to anonymous callers.
            pass
    return {'ok':True,'message':'If this account exists, instructions were sent.'}

def reset_password(token,password):
    if not isinstance(password,str) or not 10<=len(password)<=160:raise ValueError('weak_password')
    if not isinstance(token,str) or not 15<=len(token)<=256:raise ValueError('reset_invalid')
    h=token_hash(token)
    with store.DB_LOCK:
        with store.db_connection() as conn:
            row=conn.execute(store.sql('SELECT teacher_id FROM password_resets WHERE token_hash=? AND expires_at>? AND used_at=0'),(h,store.epoch())).fetchone()
            if not row:raise ValueError('reset_invalid')
            teacher=row[0];salt=secrets.token_hex(16)
            conn.execute(store.sql('UPDATE teachers SET password_hash=?,salt=? WHERE id=?'),(store.password_hash(password,salt),teacher))
            conn.execute(store.sql('UPDATE password_resets SET used_at=? WHERE token_hash=? AND used_at=0'),(store.epoch(),h))
            conn.execute(store.sql('DELETE FROM auth_sessions WHERE teacher_id=?'),(teacher,))
    return {'ok':True}

def change_password(teacher_id,old,new):
    if not isinstance(new,str) or not 10<=len(new)<=160:raise ValueError('weak_password')
    row=store.query('SELECT salt,password_hash FROM teachers WHERE id=?',(teacher_id,))
    if not row or not isinstance(old,str) or not hmac.compare_digest(store.password_hash(old,row['salt']),row['password_hash']):
        raise ValueError('wrong_credentials')
    salt=secrets.token_hex(16)
    with store.DB_LOCK:
        with store.db_connection() as con:
            con.execute(store.sql('UPDATE teachers SET salt=?,password_hash=? WHERE id=?'),(salt,store.password_hash(new,salt),teacher_id))
            con.execute(store.sql('DELETE FROM auth_sessions WHERE teacher_id=?'),(teacher_id,))
    return {'ok':True,'relogin':True}

def snapshot_with_revision(teacher_id):
    row=store.query('SELECT quizzes,bank,settings,results,revision FROM datasets WHERE teacher_id=?',(teacher_id,))
    if not row:return {'data':{'quizzes':[],'bank':[],'settings':{},'results':[]},'revision':0}
    return {'data':{k:store.jload(row[k],{} if k=='settings' else []) for k in FIELDS},'revision':int(row['revision'] or 0)}

def save_patch(teacher_id,patch,revision):
    """Atomic optimistic locking; only dirty fields are changed. Never silently override edits."""
    if type(revision)!=int or revision<0:raise ValueError('revision_required')
    keys=[k for k in FIELDS if k in patch]
    if not keys:raise ValueError('empty_patch')
    if any(not isinstance(patch[k],dict if k=='settings' else list) for k in keys):raise ValueError('invalid_snapshot')
    if any(len(store.jdump(patch[k]))>8_000_000 for k in keys):raise ValueError('too_large')
    with store.DB_LOCK:
        with store.db_connection() as con:
            columns=', '.join(k+'=?' for k in keys)
            args=[store.jdump(patch[k]) for k in keys]+[store.epoch(),teacher_id,revision]
            cur=con.execute(store.sql('UPDATE datasets SET '+columns+',updated_at=?,revision=revision+1 WHERE teacher_id=? AND revision=?'),args)
            if cur.rowcount!=1:raise ValueError('revision_conflict')
    # Make one automatic recovery checkpoint every 12 hours of teacher edits.
    try:auto_backup(teacher_id)
    except Exception as e:print('[QuizNova backup] snapshot checkpoint failed:',type(e).__name__)
    return {'ok':True,'revision':revision+1}

def _rows(conn,table,teacher_id):
    cur=conn.execute(store.sql('SELECT * FROM '+table+' WHERE teacher_id=?'),(teacher_id,))
    cols=[x[0] for x in cur.description]
    return [dict(zip(cols,r)) for r in cur.fetchall()]

def backup_payload(teacher_id):
    with store.DB_LOCK:
        with store.db_connection() as con:
            ds=_rows(con,'datasets',teacher_id)
            tables={table:_rows(con,table,teacher_id) for table in TABLES}
    return {'schema':103,'teacherId':teacher_id,'createdAt':store.epoch(),'datasets':ds,'tables':tables}

def create_backup(teacher_id,reason='manual'):
    if reason not in ('manual','automatic','before_restore'):raise ValueError('invalid_reason')
    payload=store.jdump(backup_payload(teacher_id))
    if len(payload)>22_000_000:raise ValueError('backup_too_large')
    ident=uuid.uuid4().hex;now=store.epoch()
    with store.DB_LOCK:
        with store.db_connection() as con:
            con.execute(store.sql('INSERT INTO teacher_backups(id,teacher_id,created_at,reason,payload) VALUES(?,?,?,?,?)'),(ident,teacher_id,now,reason,payload))
            # Portable retention cleanup (remove oldest entries beyond BACKUP_RETENTION)
            old=con.execute(store.sql('SELECT id FROM teacher_backups WHERE teacher_id=? ORDER BY created_at DESC,id DESC'),(teacher_id,)).fetchall()[BACKUP_RETENTION:]
            for (k,) in old:con.execute(store.sql('DELETE FROM teacher_backups WHERE id=? AND teacher_id=?'),(k,teacher_id))
    return {'id':ident,'created_at':now,'reason':reason}

def auto_backup(teacher_id):
    if not teacher_id:return
    last=store.query('SELECT MAX(created_at) AS t FROM teacher_backups WHERE teacher_id=? AND reason=?',(teacher_id,'automatic'))
    if last and int(last['t'] or 0)>store.epoch()-12*3600:return
    create_backup(teacher_id,'automatic')

def list_backups(teacher_id):
    return store.query('SELECT id,created_at,reason,LENGTH(payload) AS size FROM teacher_backups WHERE teacher_id=? ORDER BY created_at DESC LIMIT 14',(teacher_id,),True)

def download_backup(teacher_id,id):
    row=store.query('SELECT payload FROM teacher_backups WHERE teacher_id=? AND id=?',(teacher_id,id))
    if not row:raise ValueError('backup_not_found')
    return store.jload(row['payload'],{})

def restore_backup(teacher_id,id,password):
    row=store.query('SELECT password_hash,salt FROM teachers WHERE id=?',(teacher_id,))
    if not row or not isinstance(password,str) or not hmac.compare_digest(store.password_hash(password,row['salt']),row['password_hash']):raise ValueError('wrong_credentials')
    source=download_backup(teacher_id,id)
    if source.get('teacherId')!=teacher_id or source.get('schema')!=103 or len(source.get('datasets',[]))!=1:raise ValueError('backup_invalid')
    data=source['datasets'][0];tables=source['tables']
    if not all(isinstance(tables.get(table),list) for table in TABLES):raise ValueError('backup_invalid')
    if not all(all(row.get('teacher_id')==teacher_id for row in tables[table]) for table in TABLES):raise ValueError('backup_invalid')
    # Create a recovery point before making any destructive change.
    safe=create_backup(teacher_id,'before_restore')
    with store.DB_LOCK:
        with store.db_connection() as con:
            for table in ('student_attempts','played_sessions','students'):
                con.execute(store.sql('DELETE FROM '+table+' WHERE teacher_id=?'),(teacher_id,))
            for table in ('students','played_sessions','student_attempts'):
                for r in tables[table]:
                    keys=list(r);vals=[r[k] for k in keys]
                    con.execute(store.sql('INSERT INTO '+table+' ('+','.join(keys)+') VALUES ('+','.join('?' for _ in keys)+')'),vals)
            con.execute(store.sql('UPDATE datasets SET quizzes=?,bank=?,settings=?,results=?,updated_at=?,revision=revision+1 WHERE teacher_id=?'),(data['quizzes'],data['bank'],data['settings'],data['results'],store.epoch(),teacher_id))
    return {'ok':True,'recovery_backup_id':safe['id'],'revision':snapshot_with_revision(teacher_id)['revision']}

initialize()
