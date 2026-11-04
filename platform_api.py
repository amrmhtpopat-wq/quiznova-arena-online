"""Authenticated teacher APIs, purposefully separate from public student routes."""
from urllib.parse import parse_qs
import time,threading
import platform_security as sec
RATES={}
RATE_LOCK=threading.Lock()
def check_rate(handler,route):
    client=handler.client_address[0]
    key=client+':'+route
    now=time.monotonic()
    with RATE_LOCK:
        records=[t for t in RATES.get(key,[]) if now-t<600]
        if len(records)>8:
            RATES[key]=records;return False
        records.append(now);RATES[key]=records
        if len(RATES)>2000:RATES.clear()
    return True
from platform_store import (DATABASE_KIND,create_teacher,login,teacher_for_token,signout,snapshot,save_snapshot,
                             add_students,list_students,history,dashboard,class_wars,mastery,update_school_type,avatar_pool)

MAX_POST=1_850_000

def bearer(handler):
    raw=handler.headers.get('Authorization','')
    return raw.split(' ',1)[1].strip() if raw.lower().startswith('bearer ') else ''

def get_teacher(handler):return teacher_for_token(bearer(handler))

def authorized(handler):
    teacher=get_teacher(handler)
    if not teacher:
        handler.send_json({'ok':False,'error':'login_required'},401)
    return teacher

def handle_get(h,u):
    if u.path=='/api/auth/reset-status':
        h.send_json({'ok':True,'enabled':sec.smtp_ready()});return True
    if u.path not in ('/api/auth/me','/api/teacher/snapshot','/api/teacher/students','/api/teacher/history','/api/teacher/dashboard','/api/teacher/classwars','/api/teacher/mastery','/api/teacher/backup','/api/teacher/backups'):return False
    t=authorized(h)
    if not t:return True
    tid=t['id']
    if u.path=='/api/auth/me':h.send_json({'ok':True,'teacher':t,'storage':DATABASE_KIND})
    elif u.path=='/api/teacher/snapshot':h.send_json({'ok':True,**sec.snapshot_with_revision(tid)})
    elif u.path=='/api/teacher/students':h.send_json({'ok':True,'students':list_students(tid)})
    elif u.path=='/api/teacher/history':h.send_json({'ok':True,'sessions':history(tid,150)})
    elif u.path=='/api/teacher/dashboard':h.send_json({'ok':True,'dashboard':dashboard(tid),'teacher':t})
    elif u.path=='/api/teacher/classwars':h.send_json({'ok':True,'classes':class_wars(tid)})
    elif u.path=='/api/teacher/mastery':h.send_json({'ok':True,'skills':mastery(tid)})
    elif u.path=='/api/teacher/backup':h.send_json({'ok':True,'version':'10.3','teacher':t,'data':sec.backup_payload(tid)})
    elif u.path=='/api/teacher/backups':h.send_json({'ok':True,'backups':sec.list_backups(tid)})
    return True

def handle_post(h,u,data):
    if u.path not in ('/api/auth/register','/api/auth/login','/api/auth/forgot','/api/auth/reset','/api/auth/logout','/api/auth/password','/api/teacher/snapshot','/api/teacher/students','/api/teacher/school-type','/api/teacher/backups/create','/api/teacher/backups/restore'):return False
    try:
        if u.path in ('/api/auth/register','/api/auth/login','/api/auth/forgot','/api/auth/reset') and not check_rate(h,u.path):
            h.send_json({'ok':False,'error':'rate_limited'},429);return True
        if u.path=='/api/auth/register':
            d=create_teacher(str(data.get('email','')),str(data.get('password','')),str(data.get('name','')),str(data.get('school','')),str(data.get('subject','عام')),str(data.get('schoolType','mixed')))
            return h.send_json({'ok':True,**d}) or True
        if u.path=='/api/auth/login':
            d=login(str(data.get('email','')),str(data.get('password','')))
            return h.send_json({'ok':True,**d}) or True
        if u.path=='/api/auth/forgot':
            h.send_json(sec.request_password_reset(str(data.get('email',''))));return True
        if u.path=='/api/auth/reset':
            h.send_json(sec.reset_password(data.get('token'),data.get('password')));return True
        t=authorized(h)
        if not t:return True
        if u.path=='/api/auth/logout':
            signout(bearer(h));h.send_json({'ok':True});return True
        if u.path=='/api/auth/password':
            h.send_json(sec.change_password(t['id'],data.get('oldPassword'),data.get('newPassword')));return True
        if u.path=='/api/teacher/snapshot':
            h.send_json(sec.save_patch(t['id'],data.get('patch',{}),data.get('revision')));return True
        if u.path=='/api/teacher/backups/create':
            h.send_json({'ok':True,'backup':sec.create_backup(t['id'])});return True
        if u.path=='/api/teacher/backups/restore':
            h.send_json(sec.restore_backup(t['id'],str(data.get('backupId','')),data.get('password')));return True
        if u.path=='/api/teacher/school-type':
            typ=update_school_type(t['id'],str(data.get('schoolType','mixed')))
            h.send_json({'ok':True,'schoolType':typ,'avatars':avatar_pool(typ)});return True
        if u.path=='/api/teacher/students':
            items=data.get('students',[])
            if not isinstance(items,list):return h.send_json({'ok':False,'error':'invalid_students'},400) or True
            rows=add_students(t['id'],items)
            return h.send_json({'ok':True,'created':rows,'count':len(rows)}) or True
    except ValueError as e:
        h.send_json({'ok':False,'error':str(e)},409 if str(e) in ('email_taken','revision_conflict') else (503 if str(e)=='email_not_configured' else 400));return True
    except Exception as e:
        h.log_message('teacher route error: %s',str(e));h.send_json({'ok':False,'error':'server_error'},500);return True
    return True
