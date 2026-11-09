"""BOOYAHJO Game Lab: authenticated authoring and card-based classroom activities.

Isolated tables; additive, backward-compatible schema. Never stores raw student
card tokens in games or results. Grade/XP awards are server-authoritative and
the award for each student+activity is limited to its first completion.
"""
import hashlib
import json
import random
import secrets
import time
import uuid
import re
from urllib.parse import parse_qs
import platform_store as db
import platform_api as auth
import solo_api

MAX_ROWS=80
TEXT_MODES={'anagram','crossword','wordsearch','cloze','exit'}
NON_GRADED_MODES={'survey','exit','board'}
MODES={'quiz','fast','pairs','flash','wheel','boxes','sort','truth','crossword',
       'wordsearch','anagram','order','maze','balloons','memory','hidden',
       'cloze','diagram','board','teams','survey','exit','story','bingo'}
TEACHER_PATHS={'/api/game-lab/teacher/save','/api/game-lab/teacher/delete',
               '/api/game-lab/teacher/publish','/api/game-lab/teacher/unpublish'}
STUDENT_PATHS={'/api/game-lab/student/start','/api/game-lab/student/state',
               '/api/game-lab/student/answer'}
RUN_TTL=24*3600


def now():return int(time.time())

def ensure_schema():
    for statement in (
      'CREATE TABLE IF NOT EXISTS game_lab_activities (id TEXT PRIMARY KEY,teacher_id TEXT NOT NULL,'
      'title TEXT NOT NULL,subject TEXT NOT NULL,grade TEXT NOT NULL,mode TEXT NOT NULL,'
      'payload TEXT NOT NULL,public_code TEXT UNIQUE,published INTEGER NOT NULL DEFAULT 0,'
      'max_attempts INTEGER NOT NULL DEFAULT 1,archived INTEGER NOT NULL DEFAULT 0,'
      'created_at BIGINT NOT NULL,updated_at BIGINT NOT NULL)',
      'CREATE TABLE IF NOT EXISTS game_lab_runs (token_hash TEXT PRIMARY KEY,activity_id TEXT NOT NULL,'
      'teacher_id TEXT NOT NULL,student_id TEXT,student_name TEXT NOT NULL,class_name TEXT NOT NULL,'
      'state TEXT NOT NULL,created_at BIGINT NOT NULL,updated_at BIGINT NOT NULL,finished_at BIGINT NOT NULL DEFAULT 0)',
      'CREATE INDEX IF NOT EXISTS idx_lab_activities_owner ON game_lab_activities(teacher_id,updated_at)',
      'CREATE INDEX IF NOT EXISTS idx_lab_runs_owner ON game_lab_runs(teacher_id,activity_id,created_at)',
      'CREATE INDEX IF NOT EXISTS idx_lab_runs_student ON game_lab_runs(student_id,activity_id)',
    ):
        db.exec_sql(statement)


def fail(h,error,status=400):
    h.send_json({'ok':False,'error':error},status)
    return True


def validate_payload(raw):
    if not isinstance(raw,dict):raise ValueError('invalid_activity')
    title=str(raw.get('title','')).strip()[:90]
    if not title:raise ValueError('title_required')
    rows=raw.get('rows')
    if not isinstance(rows,list) or not 4<=len(rows)<=MAX_ROWS:raise ValueError('invalid_question_count')
    result=[];seen=set()
    for row in rows:
        if not isinstance(row,dict):raise ValueError('invalid_question')
        q=str(row.get('q','')).strip()[:200]
        a=str(row.get('a','')).strip()[:100]
        g=str(row.get('g','عام')).strip()[:60] or 'عام'
        if not q or not a:raise ValueError('incomplete_question')
        key=(q.casefold(),a.casefold())
        if key in seen:continue
        seen.add(key);result.append({'q':q,'a':a,'g':g})
    if len(result)<4:raise ValueError('too_few_unique_questions')
    mode=str(raw.get('mode') or 'quiz')
    if mode not in MODES:raise ValueError('invalid_game_mode')
    subject=str(raw.get('subject') or 'عام').strip()[:80]
    grade=str(raw.get('grade') or 'عام').strip()[:40]
    raw_time=raw.get('time',25)
    try:seconds=int(raw_time)
    except (ValueError,TypeError):seconds=25
    image_id=str(raw.get('imageId') or '').strip()
    book_id=str(raw.get('bookId') or '').strip()
    if image_id and not re.fullmatch('[a-f0-9]{32}',image_id):raise ValueError('invalid_image_id')
    if book_id and not re.fullmatch('[a-f0-9]{32}',book_id):raise ValueError('invalid_book_id')
    return {'title':title,'subject':subject,'grade':grade,'mode':mode,
            'time':max(10,min(90,seconds)),'rows':result,
            'imageId':image_id,'bookId':book_id}


def public_view(row):
    return {'id':row['id'],'title':row['title'],'subject':row['subject'],
            'grade':row['grade'],'mode':row['mode'],
            'published':bool(row['published']),'publicCode':row['public_code'] if row['published'] else None,
            'maxAttempts':row['max_attempts'],
            'imageId':db.jload(row['payload'],{}).get('imageId') or '',
            'bookId':db.jload(row['payload'],{}).get('bookId') or '',
            'createdAt':row['created_at'],
            'updatedAt':row['updated_at'],'questionCount':len(db.jload(row['payload'],{}).get('rows',[]))}


def owner_row(tid,aid):
    return db.query('SELECT * FROM game_lab_activities WHERE id=? AND teacher_id=? AND archived=0',
                    (aid,tid))


def list_activities(tid):
    rows=db.query('SELECT * FROM game_lab_activities WHERE teacher_id=? AND archived=0 '
                  'ORDER BY updated_at DESC LIMIT 150',(tid,),True)
    return [{**public_view(row),'activity':db.jload(row['payload'],{})} for row in rows]


def save(tid,data):
    activity=validate_payload(data.get('activity'))
    if activity.get('imageId') and not db.query(
        'SELECT id FROM game_lab_media WHERE id=? AND teacher_id=? AND archived=0',
        (activity['imageId'],tid)):raise ValueError('media_not_found')
    if activity.get('bookId') and not db.query(
        'SELECT id FROM game_lab_books WHERE id=? AND teacher_id=? AND archived=0',
        (activity['bookId'],tid)):raise ValueError('book_not_found')
    aid=str(data.get('id') or '')
    timestamp=now()
    if aid:
        row=owner_row(tid,aid)
        if not row:raise ValueError('activity_not_found')
        db.exec_sql('UPDATE game_lab_activities SET title=?,subject=?,grade=?,mode=?,payload=?,updated_at=? '
                    'WHERE id=? AND teacher_id=?',
                    (activity['title'],activity['subject'],activity['grade'],activity['mode'],
                     db.jdump(activity),timestamp,aid,tid))
    else:
        aid=uuid.uuid4().hex
        db.exec_sql('INSERT INTO game_lab_activities '
                    '(id,teacher_id,title,subject,grade,mode,payload,created_at,updated_at) '
                    'VALUES(?,?,?,?,?,?,?,?,?)',
                    (aid,tid,activity['title'],activity['subject'],activity['grade'],activity['mode'],
                     db.jdump(activity),timestamp,timestamp))
    return {**public_view(owner_row(tid,aid)),'activity':activity}


def publish(tid,data,enabled):
    aid=str(data.get('id') or '')
    row=owner_row(tid,aid)
    if not row:raise ValueError('activity_not_found')
    try:maximum=int(data.get('maxAttempts',row['max_attempts']))
    except (TypeError,ValueError):raise ValueError('invalid_attempt_limit')
    if not 1<=maximum<=10:raise ValueError('invalid_attempt_limit')
    code=row['public_code'] or secrets.token_urlsafe(18)
    db.exec_sql('UPDATE game_lab_activities SET published=?,public_code=?,max_attempts=?,updated_at=? '
                'WHERE id=? AND teacher_id=?',(int(enabled),code,maximum,now(),aid,tid))
    return public_view(owner_row(tid,aid))


def remove(tid,data):
    row=owner_row(tid,str(data.get('id') or ''))
    if not row:raise ValueError('activity_not_found')
    if data.get('confirm') is not True:raise ValueError('confirmation_required')
    db.exec_sql('UPDATE game_lab_activities SET archived=1,published=0,updated_at=? '
                'WHERE id=? AND teacher_id=?',(now(),row['id'],tid))
    return {'id':row['id'],'archived':True}


def public_activity(code):
    code=str(code or '').strip()
    if not 12<=len(code)<=90:return None
    return db.query('SELECT * FROM game_lab_activities WHERE public_code=? AND published=1 '
                    'AND archived=0',(code,))


def participant_view(a):
    return {'title':a['title'],'subject':a['subject'],'grade':a['grade'],
            'mode':a['mode'],'questions':len(db.jload(a['payload'],{}).get('rows',[])),
            'maxAttempts':a['max_attempts'],
            'imageUrl':('/api/game-lab/pro/image?id='+str(db.jload(a['payload'],{}).get('imageId'))+
              '&code='+str(a['public_code'])) if db.jload(a['payload'],{}).get('imageId') else ''}


def hashed(token):return hashlib.sha256(token.encode()).hexdigest()


def normalize(value):return str(value or '').strip().casefold()


def question_state(state,token_hash):
    rows=state['rows'];idx=state['index'];answered=idx>=len(rows)
    if answered:return None
    item=rows[idx];mode=state['mode']
    rng=random.Random(int(hashlib.sha256((token_hash+':'+str(idx)).encode()).hexdigest()[:12],16))
    if mode in TEXT_MODES:
        can_shuffle=mode in ('anagram','wordsearch') and len(item['a'].replace(' ',''))<=40
        letters=list(item['a'].replace(' ','')) if can_shuffle else []
        rng.shuffle(letters)
        return {'index':idx,'question':item['q'],'choices':[],
                'entry':'letters' if can_shuffle else 'text',
                'scrambled':letters,'answerLength':len(item['a'][:40]),
                'total':len(rows),'mode':mode,'duration':state['duration'],
                'score':state['score']}
    if mode=='sort':
        choices=list(dict.fromkeys(r['g'] for r in rows))
        correct=item['g']
    elif mode=='truth':
        wrongs=[r['a'] for r in rows if r['a']!=item['a']]
        actual=bool(rng.randrange(2))
        candidate=item['a'] if actual or not wrongs else rng.choice(wrongs)
        correct='صح' if candidate==item['a'] else 'خطأ'
        return {'index':idx,'question':item['q'],'candidate':candidate,
                'choices':['صح','خطأ'],'total':len(rows),'mode':mode,
                'duration':state['duration'],'score':state['score']}
    else:
        choices=list(dict.fromkeys(r['a'] for r in rows if r['a']!=item['a']))
        rng.shuffle(choices);choices=choices[:3]+[item['a']]
        correct=item['a']
    rng.shuffle(choices)
    return {'index':idx,'question':item['q'],'group':item['g'] if mode=='sort' else '',
            'choices':choices,'total':len(rows),'mode':mode,
            'duration':state['duration'],'score':state['score']}


def expected_answer(state,token_hash):
    row=state['rows'][state['index']]
    mode=state['mode']
    if mode=='sort':return row['g']
    if mode=='truth':
        rng=random.Random(int(hashlib.sha256((token_hash+':'+str(state['index'])).encode()).hexdigest()[:12],16))
        wrongs=[r['a'] for r in state['rows'] if r['a']!=row['a']]
        actual=bool(rng.randrange(2))
        candidate=row['a'] if actual or not wrongs else rng.choice(wrongs)
        return 'صح' if candidate==row['a'] else 'خطأ'
    return row['a']


def state_view(state,digest):
    completed=state['finished']
    data={'finished':completed,'studentName':state['studentName'],
          'className':state['className'],'score':state['score'],
          'correct':state['correct'],'index':state['index'],'total':len(state['rows']),
          'xpGain':state.get('xpGain',0),'guest':state.get('guest',False),
          'activityTitle':state['title'],'mode':state['mode'],
          'unscored':state['mode'] in NON_GRADED_MODES}
    if not completed:
        data['question']=question_state(state,digest)
        if state.get('imageUrl'):data['question']['imageUrl']=state['imageUrl']
    return data


def start(data,h):
    a=public_activity(data.get('code'))
    if not a:return fail(h,'not_published',404)
    card=str(data.get('card') or '').strip()
    if solo_api.limited(h,card or data.get('code')):return fail(h,'rate_limited',429)
    student=solo_api.find_student(card) if card else None
    if card and not student:return fail(h,'invalid_card',403)
    if student and student['teacher_id']!=a['teacher_id']:return fail(h,'card_other_teacher',403)
    guest=not bool(student)
    name=str(data.get('guestName') or 'ضيف').strip()[:40]
    if guest and len(name)<2:return fail(h,'name_required')
    payload=db.jload(a['payload'],{})
    rows=payload.get('rows',[])
    if not rows:return fail(h,'empty_activity',409)
    assigned=db.query('SELECT target_type,target_value FROM game_lab_assignments '
       'WHERE activity_id=? AND teacher_id=?',(a['id'],a['teacher_id']),True)
    if assigned:
        if not student:return fail(h,'card_required_for_assignment',403)
        if not any(t['target_type']=='all' or
             (t['target_type']=='student' and t['target_value']==student['id']) or
             (t['target_type']=='class' and t['target_value']==student['class_name'])
             for t in assigned):
            return fail(h,'not_assigned_to_card',403)
    token=secrets.token_urlsafe(36)
    state={'rows':rows,'title':a['title'],'mode':a['mode'],'duration':payload.get('time',25),
           'index':0,'score':0,'correct':0,'finished':False,'xpGain':0,
           'guest':guest,'studentName':student['name'] if student else name,
           'className':student['class_name'] if student else 'زائر',
           'imageUrl':('/api/game-lab/pro/image?id='+str(payload.get('imageId'))+
              '&code='+str(a['public_code'])) if payload.get('imageId') else ''}
    key=hashed(token);timestamp=now()
    # Atomic start quota for a student card: lock that student record first.
    with db.DB_LOCK:
        with db.db_connection() as con:
            cur=con.cursor()
            if student:
                lock='SELECT id FROM students WHERE id=? AND teacher_id=?'+(' FOR UPDATE' if db.DATABASE_URL else '')
                cur.execute(db.sql(lock),(student['id'],a['teacher_id']))
                if not cur.fetchone():return fail(h,'invalid_card',403)
                cur.execute(db.sql('SELECT COUNT(*) FROM game_lab_runs WHERE activity_id=? '
                                   'AND student_id=?'),(a['id'],student['id']))
                if int(cur.fetchone()[0])>=int(a['max_attempts']):
                    return fail(h,'attempt_limit',403)
            cur.execute(db.sql('INSERT INTO game_lab_runs '
               '(token_hash,activity_id,teacher_id,student_id,student_name,class_name,state,created_at,updated_at) '
               'VALUES(?,?,?,?,?,?,?,?,?)'),
               (key,a['id'],a['teacher_id'],student['id'] if student else None,
                state['studentName'],state['className'],db.jdump(state),timestamp,timestamp))
    h.send_json({'ok':True,'token':token,'state':state_view(state,key)})
    return True


def read_state(data,h):
    token=str(data.get('token') or '')
    if len(token)<25 or len(token)>150:return fail(h,'invalid_session',403)
    row=db.query('SELECT * FROM game_lab_runs WHERE token_hash=?',(hashed(token),))
    if not row or now()-int(row['updated_at'])>RUN_TTL:return fail(h,'expired_session',403)
    state=db.jload(row['state'],{})
    h.send_json({'ok':True,'state':state_view(state,hashed(token))})
    return True


def answer(data,h):
    token=str(data.get('token') or '')
    if len(token)<25 or len(token)>150:return fail(h,'invalid_session',403)
    idx=data.get('index')
    if type(idx)!=int:return fail(h,'invalid_index')
    raw=data.get('answer')
    if not isinstance(raw,str) or len(raw)>120:return fail(h,'invalid_answer')
    key=hashed(token)
    with db.DB_LOCK:
        with db.db_connection() as con:
            cur=con.cursor()
            lock='SELECT * FROM game_lab_runs WHERE token_hash=?'+(' FOR UPDATE' if db.DATABASE_URL else '')
            cur.execute(db.sql(lock),(key,))
            row=cur.fetchone()
            if not row:return fail(h,'invalid_session',403)
            col=[x[0] for x in cur.description];session=dict(zip(col,row))
            if now()-int(session['updated_at'])>RUN_TTL:return fail(h,'expired_session',403)
            state=db.jload(session['state'],{})
            if state['finished'] or state['index']!=idx:return fail(h,'question_changed',409)
            right=expected_answer(state,key)
            graded=state['mode'] not in NON_GRADED_MODES
            correct=normalize(raw)==normalize(right) if graded else None
            if correct:
                state['correct']+=1;state['score']+=100
            state['index']+=1
            finished=state['index']>=len(state['rows'])
            state['finished']=finished
            timestamp=now()
            if finished and session['student_id']:
                student_id=session['student_id'];tid=session['teacher_id'];aid=session['activity_id']
                # Serialize XP for all runs by this student in Postgres, too.
                owner_lock='SELECT xp FROM students WHERE id=? AND teacher_id=?'+(' FOR UPDATE' if db.DATABASE_URL else '')
                cur.execute(db.sql(owner_lock),(student_id,tid))
                owner=cur.fetchone()
                if not owner:return fail(h,'invalid_card',403)
                cur.execute(db.sql('SELECT id FROM student_attempts WHERE teacher_id=? AND student_id=? '
                                   'AND quiz_id=? LIMIT 1'),(tid,student_id,'LAB-'+aid))
                awarded=cur.fetchone() is not None
                gain=0 if awarded or not graded else (state['correct']*10+10)
                state['xpGain']=gain
                if gain:
                    cur.execute(db.sql('UPDATE students SET xp=xp+?,correct_count=correct_count+?,'
                                       'played_count=played_count+1 WHERE id=? AND teacher_id=?'),
                                (gain,state['correct'],student_id,tid))
                attempt_id=uuid.uuid4().hex
                cur.execute(db.sql('INSERT INTO student_attempts (id,teacher_id,student_id,quiz_id,room_code,'
                                   'student_name,class_name,avatar,correct_count,question_total,percent,'
                                   'score,answers,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)'),
                            (attempt_id,tid,student_id,'LAB-'+aid,'LAB-'+aid,
                             session['student_name'],session['class_name'],'b01',state['correct'],
                             len(state['rows']),round(state['correct']*100/max(1,len(state['rows']))),
                             state['score'],db.jdump({'source':'game_lab','run':key[:12]}),timestamp))
            cur.execute(db.sql('UPDATE game_lab_runs SET state=?,updated_at=?,finished_at=? WHERE token_hash=?'),
                        (db.jdump(state),timestamp,timestamp if finished else 0,key))
    h.send_json({'ok':True,'correct':correct,'correctAnswer':right if graded else None,
                 'state':state_view(state,key)})
    return True


def teacher_reports(tid,aid):
    if not owner_row(tid,aid):raise ValueError('activity_not_found')
    records=db.query('SELECT student_name,class_name,student_id,state,finished_at,created_at '
             'FROM game_lab_runs WHERE teacher_id=? AND activity_id=? AND finished_at>0 '
             'ORDER BY finished_at DESC LIMIT 500',(tid,aid),True)
    output=[]
    for rec in records:
        state=db.jload(rec['state'],{})
        output.append({'name':rec['student_name'],'className':rec['class_name'],
            'correct':state.get('correct',0),'questions':len(state.get('rows',[])),
            'score':state.get('score',0),'xpGain':state.get('xpGain',0),
            'guest':not bool(rec['student_id']),'finishedAt':rec['finished_at']})
    return {'results':output,'total':len(output),
            'averagePercent':round(sum(100*x['correct']/max(x['questions'],1) for x in output)/len(output),1) if output else 0}


def handle_get(h,u):
    if u.path=='/api/game-lab/public':
        params=parse_qs(u.query);a=public_activity((params.get('code') or [''])[0])
        if not a:return fail(h,'not_published',404)
        h.send_json({'ok':True,'activity':participant_view(a)});return True
    if u.path not in ('/api/game-lab/teacher/list','/api/game-lab/teacher/reports'):return False
    teacher=auth.authorized(h)
    if not teacher:return True
    tid=teacher['id']
    try:
        if u.path.endswith('/list'):
            h.send_json({'ok':True,'activities':list_activities(tid)})
        else:
            params=parse_qs(u.query);aid=(params.get('id') or [''])[0]
            h.send_json({'ok':True,**teacher_reports(tid,aid)})
    except ValueError as err:return fail(h,str(err),404)
    except Exception as err:
        h.log_message('Game Lab GET error: %s',str(err))
        return fail(h,'server_error',500)
    return True


def handle_post(h,u,data):
    if u.path in STUDENT_PATHS:
        try:
            if u.path.endswith('/start'):return start(data,h)
            if u.path.endswith('/state'):return read_state(data,h)
            return answer(data,h)
        except ValueError as err:return fail(h,str(err),400)
        except Exception as err:
            h.log_message('Game Lab student route: %s',str(err))
            return fail(h,'server_error',500)
    if u.path not in TEACHER_PATHS:return False
    teacher=auth.authorized(h)
    if not teacher:return True
    tid=teacher['id']
    try:
        if u.path.endswith('/save'):result=save(tid,data)
        elif u.path.endswith('/delete'):result=remove(tid,data)
        elif u.path.endswith('/publish'):result=publish(tid,data,True)
        else:result=publish(tid,data,False)
        h.send_json({'ok':True,**result})
    except ValueError as err:
        return fail(h,str(err),404 if str(err)=='activity_not_found' else 400)
    except Exception as err:
        h.log_message('Game Lab teacher route: %s',str(err))
        return fail(h,'server_error',500)
    return True
