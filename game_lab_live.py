"""BOOYAHJO Game Lab live classroom games over rapid HTTP polling (no sockets).

Teacher-guarded room controls; participant token required for individual state/answers.
All scoring, timing, and correct-answer checks occur server-side. Live participation
does not add XP, to prevent double-counting previous card-assigned solo games.
"""
import hashlib
import json
import secrets
import time
import uuid
from urllib.parse import parse_qs
from random import Random, SystemRandom
import platform_store as db
import platform_api as auth
import solo_api
import student_verify
import game_lab_api as games

GET={'/api/game-lab/live/state','/api/game-lab/live/rooms','/api/game-lab/live/report'}
HOST={'/api/game-lab/live/create','/api/game-lab/live/next',
      '/api/game-lab/live/finish','/api/game-lab/live/start'}
STUDENT={'/api/game-lab/live/join','/api/game-lab/live/answer','/api/game-lab/live/state'}
TTL=5*3600
LIVE_MODES=frozenset({'quiz','fast','truth','pairs','wheel','boxes'})


def stamp():return int(time.time())
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def error(h,s,code=400):return games.fail(h,s,code)


def init():
    for sql in (
      "CREATE TABLE IF NOT EXISTS game_lab_live_rooms (code TEXT PRIMARY KEY,"
      "teacher_id TEXT NOT NULL,activity_id TEXT NOT NULL,"
      "state TEXT NOT NULL,created_at BIGINT NOT NULL,updated_at BIGINT NOT NULL)",
      "CREATE INDEX IF NOT EXISTS ix_gl_live_teacher ON game_lab_live_rooms(teacher_id,updated_at)",
      "CREATE TABLE IF NOT EXISTS game_lab_live_players (id TEXT PRIMARY KEY,"
      "code TEXT NOT NULL,teacher_id TEXT NOT NULL,student_id TEXT,"
      "student_name TEXT NOT NULL,class_name TEXT NOT NULL,team TEXT NOT NULL,"
      "token_hash TEXT UNIQUE NOT NULL,score INTEGER NOT NULL DEFAULT 0,"
      "answers TEXT NOT NULL,joined_at BIGINT NOT NULL,updated_at BIGINT NOT NULL)",
      "CREATE INDEX IF NOT EXISTS ix_gl_live_code ON game_lab_live_players(code,score)"
    ):db.exec_sql(sql)
    if db.DATABASE_URL:
        columns={x['column_name'] for x in db.query(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='game_lab_live_players'",many=True)}
    else:
        with db.db_connection() as con:
            columns={x[1] for x in con.execute(
                "PRAGMA table_info(game_lab_live_players)").fetchall()}
    if 'pin_verified' not in columns:
        db.exec_sql("ALTER TABLE game_lab_live_players ADD COLUMN "
                    "pin_verified INTEGER NOT NULL DEFAULT 0")


def load(code):
    return db.query('SELECT * FROM game_lab_live_rooms WHERE code=?',(str(code or '').strip().upper(),))


def get_player(code,token):
    if not isinstance(token,str) or len(token)<20 or len(token)>160:return None
    return db.query('SELECT * FROM game_lab_live_players WHERE code=? AND token_hash=?',
                    (str(code or '').strip().upper(),sha(token)))


def state(room):
    return db.jload(room['state'],{})


def roster(code):
    return db.query('SELECT id,student_id,student_name,class_name,team,score,answers,joined_at '
                    'FROM game_lab_live_players WHERE code=? ORDER BY score DESC,joined_at ASC LIMIT 200',
                    (code,),True)


def phase(room,players):
    s=state(room)
    if s.get('status')!='question':return s.get('status','lobby')
    idx=int(s.get('index',0))
    joined=len(players)
    answered=sum(1 for p in players if str(idx) in db.jload(p['answers'],{}))
    limit=stamp()>=int(s.get('deadline') or 0)
    return 'results' if limit or (joined and answered==joined) else 'question'


def question(s,with_answers=False):
    """Shared deterministic question; correct key is teacher-only until results."""
    idx=int(s['index'])
    if idx<0 or idx>=len(s['rows']):return None
    row=s['rows'][idx];mode=s['mode']
    rng=Random(int.from_bytes(hashlib.sha256(
        (s['seed']+':'+str(idx)).encode()).digest()[:8],'big'))
    authored=row.get('choices')
    if isinstance(authored,list) and 2<=len(authored)<=4 and row['a'] in authored:
        options=authored[:]
    else:
        options=list(dict.fromkeys(x['a'] for x in s['rows'] if x['a']!=row['a']))
        rng.shuffle(options);options=[row['a']]+options[:3]
    answer=row['a'];candidate=None
    if mode=='truth':
        wrongs=list(dict.fromkeys(x['a'] for x in s['rows'] if x['a']!=row['a']))
        truth=rng.randrange(2)==1 or not wrongs
        candidate=row['a'] if truth else rng.choice(wrongs)
        options=['صح','خطأ'];answer='صح' if candidate==row['a'] else 'خطأ'
    else:rng.shuffle(options)
    result={'index':idx,'total':len(s['rows']),'text':row['q'],
            'options':options,'group':row['g'],'duration':s['duration'],
            'imageUrl':s.get('imageUrl') or '','mode':mode,
            'roundSeed':hashlib.sha256((s['seed']+str(idx)).encode()).hexdigest()[:10]}
    if mode=='truth':result['candidate']=candidate
    if with_answers:result['correctAnswer']=answer
    return result

def snapshot(room,players,role='',person=None):
    s=state(room);current=phase(room,players);idx=int(s.get('index',0))
    mine=db.jload(person['answers'],{}) if person else {}
    responded=bool(person and str(idx) in mine)
    q=question(s,with_answers=role=='teacher') if current in ('question','results') else None
    correct=None
    if current=='results' and (s['showFeedback'] or role=='teacher'):
        correct=question(s,with_answers=True)['correctAnswer']
    answered=sum(1 for p in players if str(idx) in db.jload(p['answers'],{}))
    leaders=[{'name':p['student_name'],'className':p['class_name'],
              'team':p['team'],'score':p['score']} for p in players[:10]]
    totals={}
    for p in players:
        if p['team']:totals[p['team']]=totals.get(p['team'],0)+int(p['score'])
    teams=sorted(({'name':name,'score':score} for name,score in totals.items()),
                 key=lambda x:(-x['score'],x['name']))
    data={'code':room['code'],'title':s['title'],'status':current,
          'index':idx,'total':len(s['rows']),'deadline':s.get('deadline',0),
          'duration':s['duration'],'showFeedback':s['showFeedback'],'teams':s['teams'],
          'mode':s['mode'],'leaderboard':leaders,'teamLeaderboard':teams,
          'participants':len(players),'question':q,'correctAnswer':correct,
          'roomUpdatedAt':room['updated_at'],'targetGrade':s.get('targetGrade','')}
    if role=='teacher':
        data['answerStats']={'answered':answered,'total':len(players)}
        data['activityId']=room['activity_id']
    if person and person['team']:
        data['teammates']=[p['student_name'] for p in players if p['team']==person['team']][:50]
    if person:
        data['me']={'name':person['student_name'],'team':person['team'],
                    'score':person['score'],'answered':responded,
                    'answerCorrect':mine.get(str(idx),{}).get('correct')
                      if current=='results' and s['showFeedback'] and
                         not mine.get(str(idx),{}).get('missed') else None}
    if q and role!='teacher':q.pop('correctAnswer',None)
    if current=='question' and role!='teacher':data['correctAnswer']=None
    return data

def code_new():
    for _ in range(12):
        code=''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(6))
        if not load(code):return code
    raise ValueError('code_unavailable')


def create(tid,data):
    aid=str(data.get('activityId') or '')
    activity=games.owner_row(tid,aid)
    if not activity:raise ValueError('activity_not_found')
    payload=db.jload(activity['payload'],{})
    rows=payload.get('rows',[])
    if not rows:raise ValueError('activity_empty')
    mode=activity['mode']
    if mode not in LIVE_MODES:raise ValueError('live_mode_not_supported')
    try:duration=int(data.get('duration',payload.get('time',25)))
    except (TypeError,ValueError):duration=25
    duration=max(10,min(120,duration))
    group_mode=data.get('teams') is True
    names=[str(x).strip()[:30] for x in data.get('teamNames',[]) if isinstance(x,str)] if isinstance(data.get('teamNames'),list) else []
    if group_mode and len(names)<2:names=['الصقور','النمور']
    code=code_new();rows=rows[:60]
    if mode=='wheel':
        rows=list(rows);SystemRandom().shuffle(rows)
    settings={'status':'lobby','title':activity['title'],'index':0,'rows':rows,
              'duration':duration,'mode':mode,'showFeedback':data.get('showFeedback') is not False,
              'teams':group_mode,'teamNames':names[:6],'seed':secrets.token_hex(12),
              'deadline':0,'imageUrl':'','targetGrade':str(payload.get('grade') or '')[:25],
              'enforceGrade':data.get('enforceGrade') is not False,
              'cardRequired':data.get('cardRequired') is True}
    if payload.get('imageId') and len(str(payload['imageId']))==32:
        settings['imageUrl']='/api/game-lab/pro/image?id='+payload['imageId']+'&code='+(activity['public_code'] or '')
    db.exec_sql('INSERT INTO game_lab_live_rooms(code,teacher_id,activity_id,state,created_at,updated_at) '
                'VALUES(?,?,?,?,?,?)',(code,tid,aid,db.jdump(settings),stamp(),stamp()))
    return {'code':code,'teacherUrl':'/game-lab-live.html?host='+code,
            'studentUrl':'/game-lab-live.html?code='+code,'mode':mode}

def join(h,data):
    code=str(data.get('code') or '').strip().upper()
    room=load(code)
    if not room or stamp()-room['updated_at']>TTL:return error(h,'room_not_found',404)
    s=state(room)
    if s['status']=='finished':return error(h,'room_closed',403)
    card=str(data.get('card') or '').strip()
    if solo_api.limited(h,card or code):return error(h,'rate_limited',429)
    student=solo_api.find_student(card) if card else None
    if card and not student:return error(h,'invalid_card',403)
    if student and student['teacher_id']!=room['teacher_id']:return error(h,'card_other_teacher',403)
    verify_on=student_verify.is_enabled(room['teacher_id'])
    if verify_on and not student:return error(h,'card_required',403)
    if s.get('cardRequired') and not student:return error(h,'card_required',403)
    if student and s.get('enforceGrade') and s.get('targetGrade'):
        grade=s['targetGrade'].strip().casefold()
        numeric={'4':'الرابع','5':'الخامس','6':'السادس','7':'السابع',
                 '8':'الثامن','9':'التاسع','10':'العاشر',
                 '11':'الحادي عشر','12':'الثاني عشر'}
        target=numeric.get(grade,grade)
        student_class=str(student['class_name']).casefold()
        if target not in student_class and grade not in student_class:
            return error(h,'card_wrong_grade',403)
    name=student['name'] if student else str(data.get('guestName') or '').strip()[:40]
    if len(name)<2:return error(h,'name_required')
    token=secrets.token_urlsafe(36)
    with db.DB_LOCK:
        with db.db_connection() as conn:
            cur=conn.execute(db.sql('SELECT COUNT(*) FROM game_lab_live_players WHERE code=?'),(code,))
            count=int(cur.fetchone()[0])
            if student:
                if verify_on:
                    lock='SELECT id FROM students WHERE id=? AND teacher_id=? AND archived=0'+(' FOR UPDATE' if db.DATABASE_URL else '')
                    cur.execute(db.sql(lock),(student['id'],room['teacher_id']))
                    if not cur.fetchone():return error(h,'invalid_card',403)
                    pin_error=student_verify.verify_in_transaction(
                        cur,room['teacher_id'],student['id'],data.get('pin'))
                    if pin_error:return error(h,pin_error,429 if pin_error=='student_pin_locked' else 403)
                cur.execute(db.sql('SELECT id FROM game_lab_live_players WHERE code=? AND student_id=?'),
                            (code,student['id']))
                if cur.fetchone():return error(h,'already_joined',409)
                if verify_on:
                    active=cur.execute(db.sql(
                        'SELECT r.state,r.updated_at FROM game_lab_live_players AS p '
                        'JOIN game_lab_live_rooms AS r ON r.code=p.code '
                        'WHERE p.student_id=? AND r.teacher_id=?'),
                        (student['id'],room['teacher_id'])).fetchall()
                    for raw,updated_at in active:
                        prior=db.jload(raw,{})
                        if prior and prior.get('status')!='finished' and 0<=stamp()-int(updated_at)<TTL:
                            return error(h,'active_attempt',409)
            if count>=200:return error(h,'room_full',403)
            # A late join must not reopen a round whose results have already
            # been decided by all current players (or the server deadline).
            initial_answers={}
            if s.get('status')=='question':
                cur.execute(db.sql('SELECT answers FROM game_lab_live_players WHERE code=?'),(code,))
                earlier=cur.fetchall()
                index=str(s.get('index',0))
                finished_round=(stamp()>=int(s.get('deadline') or 0) or
                                (bool(earlier) and all(index in db.jload(row[0],{})
                                                       for row in earlier)))
                if finished_round:
                    initial_answers[index]={'correct':False,'answer':'','score':0,
                                            'missed':True,'group':str(s['rows'][int(index)].get('g') or 'عام')[:60]}
            team=s['teamNames'][count%len(s['teamNames'])] if s['teams'] else ''
            conn.execute(db.sql('INSERT INTO game_lab_live_players '
              '(id,code,teacher_id,student_id,student_name,class_name,team,token_hash,'
              'pin_verified,answers,joined_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)'),
              (uuid.uuid4().hex,code,room['teacher_id'],student['id'] if student else None,
               name,student['class_name'] if student else 'ضيف',team,sha(token),
               1 if (verify_on and student) else 0,db.jdump(initial_answers),stamp(),stamp()))
    h.send_json({'ok':True,'token':token,'state':read_public_state(code,token)})
    return True


def read_public_state(code,token):
    room=load(code)
    player=get_player(code,token)
    if not room or not player:return None
    return snapshot(room,roster(code),person=player)


def control(h,data,operation):
    t=auth.authorized(h)
    if not t:return True
    code=str(data.get('code') or '').strip().upper()
    room=load(code)
    if not room or room['teacher_id']!=t['id']:return error(h,'room_not_found',404)
    with db.DB_LOCK:
        with db.db_connection() as conn:
            cur=conn.cursor()
            cur.execute(db.sql('SELECT * FROM game_lab_live_rooms WHERE code=?'
                   +(' FOR UPDATE' if db.DATABASE_URL else '')),(code,))
            found=cur.fetchone()
            cols=[x[0] for x in cur.description]
            if not found:return error(h,'room_not_found',404)
            s=db.jload(dict(zip(cols,found))['state'],{})
            if operation=='finish':
                s['status']='finished'
            elif operation=='start':
                if s['status']!='lobby':return error(h,'room_already_started',409)
                s['status']='question';s['index']=0;s['deadline']=stamp()+s['duration']
            else:
                if s['status']=='lobby':return error(h,'room_not_started',409)
                if s['status']=='finished':return error(h,'room_closed',403)
                s['index']+=1
                if s['index']>=len(s['rows']):s['status']='finished'
                else:s['status']='question';s['deadline']=stamp()+s['duration']
            conn.execute(db.sql('UPDATE game_lab_live_rooms SET state=?,updated_at=? WHERE code=?'),
                        (db.jdump(s),stamp(),code))
    h.send_json({'ok':True,'state':snapshot(load(code),roster(code),role='teacher')})
    return True


def answer(h,data):
    code=str(data.get('code') or '').strip().upper()
    token=str(data.get('token') or '')
    if len(token)<20:return error(h,'invalid_session',403)
    idx=data.get('index')
    if type(idx)!=int:return error(h,'invalid_index')
    choice=str(data.get('answer') or '')[:130]
    with db.DB_LOCK:
        with db.db_connection() as conn:
            cur=conn.cursor()
            cur.execute(db.sql('SELECT * FROM game_lab_live_rooms WHERE code=?'
                 +(' FOR UPDATE' if db.DATABASE_URL else '')),(code,))
            found=cur.fetchone()
            if not found:return error(h,'room_not_found',404)
            cols=[x[0] for x in cur.description];room=dict(zip(cols,found));s=state(room)
            if s['status']!='question' or s['index']!=idx or stamp()>int(s.get('deadline',0)):
                return error(h,'question_closed',409)
            cur.execute(db.sql('SELECT * FROM game_lab_live_players WHERE code=? AND token_hash=?'
                 +(' FOR UPDATE' if db.DATABASE_URL else '')),(code,sha(token)))
            found=cur.fetchone()
            if not found:return error(h,'invalid_session',403)
            cols=[x[0] for x in cur.description];player=dict(zip(cols,found))
            if student_verify.is_enabled(room['teacher_id']) and not int(player['pin_verified']):
                return error(h,'student_pin_required',403)
            answers=db.jload(player['answers'],{})
            if str(idx) in answers:return error(h,'already_answered',409)
            q=question(s,with_answers=True)
            expected=q['correctAnswer']
            if choice not in q['options']:return error(h,'invalid_answer')
            correct=choice.casefold()==expected.casefold()
            # Time bonus is for Fast only; all points are server-authoritative.
            gained=(100+max(0,int(s['deadline'])-stamp())*4
                    if s['mode']=='fast' else 100) if correct else 0
            answers[str(idx)]={'correct':correct,'answer':choice,'score':gained,
                               'group':str(s['rows'][idx].get('g') or 'عام')[:60],
                               'at':stamp()}
            conn.execute(db.sql('UPDATE game_lab_live_players SET answers=?,score=score+?,updated_at=? '
                     'WHERE id=?'),(db.jdump(answers),gained,stamp(),player['id']))
    h.send_json({'ok':True,'submitted':True})
    return True


def room_report(room,players):
    """Completed/in-progress room report, available to the owning teacher only."""
    s=state(room);rows=s.get('rows',[])
    skills={}
    questions=[{'index':i,'question':r['q'],'group':r.get('g','عام'),
                'answered':0,'correct':0,'accuracy':0} for i,r in enumerate(rows)]
    output=[]
    for player in players:
        answers=db.jload(player['answers'],{})
        right=0
        for index,record in answers.items():
            try:i=int(index)
            except (TypeError,ValueError):continue
            if not 0<=i<len(rows):continue
            yes=record.get('correct') is True
            right+=int(yes)
            questions[i]['answered']+=1;questions[i]['correct']+=int(yes)
            group=str(rows[i].get('g') or 'عام')[:60]
            skill=skills.setdefault(group,{'name':group,'answered':0,'correct':0})
            skill['answered']+=1;skill['correct']+=int(yes)
        output.append({'name':player['student_name'],'className':player['class_name'],
                       'team':player['team'],'score':player['score'],'correct':right,
                       'answered':len(answers),'total':len(rows),
                       'percent':round(100*right/max(1,len(rows)),1),
                       'joinedAt':player['joined_at']})
    for q in questions:q['accuracy']=round(q['correct']*100/max(1,q['answered']),1)
    for skill in skills.values():
        skill['accuracy']=round(skill['correct']*100/max(1,skill['answered']),1)
    return {'code':room['code'],'title':s['title'],'mode':s['mode'],
            'status':phase(room,players),'totalQuestions':len(rows),
            'totalPlayers':len(players),'results':output,
            'skills':sorted(skills.values(),key=lambda x:x['name']),
            'questions':questions,'createdAt':room['created_at']}

def handle_get(h,u):
    if u.path not in GET:return False
    params=parse_qs(u.query);code=(params.get('code') or [''])[0]
    if u.path.endswith('/report'):
        t=auth.authorized(h)
        if not t:return True
        room=load(code)
        if not room or room['teacher_id']!=t['id']:return error(h,'room_not_found',404)
        h.send_json({'ok':True,**room_report(room,roster(code))})
        return True
    if u.path.endswith('/rooms'):
        t=auth.authorized(h)
        if not t:return True
        rs=db.query('SELECT code,state,created_at FROM game_lab_live_rooms WHERE teacher_id=? '
                    'ORDER BY created_at DESC LIMIT 30',(t['id'],),True)
        h.send_json({'ok':True,'rooms':[{'code':r['code'],'title':state(r).get('title'),
               'status':state(r).get('status'),'createdAt':r['created_at']} for r in rs]})
        return True
    room=load(code)
    if not room:return error(h,'room_not_found',404)
    teacher=auth.get_teacher(h)
    if teacher and teacher['id']==room['teacher_id']:
        h.send_json({'ok':True,'state':snapshot(room,roster(room['code']),role='teacher')});return True
    # Participant session tokens must not appear in URLs or access logs.
    return error(h,'use_post_state',405)


def post_state(h,data):
    code=str(data.get('code') or '').strip().upper()
    room=load(code)
    if not room:return error(h,'room_not_found',404)
    t=auth.get_teacher(h)
    if t and t['id']==room['teacher_id']:
        h.send_json({'ok':True,'state':snapshot(room,roster(code),role='teacher')})
        return True
    token=str(data.get('token') or '')
    person=get_player(code,token)
    if not person:return error(h,'invalid_session',403)
    if student_verify.is_enabled(room['teacher_id']) and not int(person['pin_verified']):
        return error(h,'student_pin_required',403)
    h.send_json({'ok':True,'state':snapshot(room,roster(code),person=person)})
    return True


def handle_post(h,u,data):
    if u.path not in HOST|STUDENT:return False
    try:
        if u.path in STUDENT:
            if u.path.endswith('/join'):return join(h,data)
            if u.path.endswith('/state'):return post_state(h,data)
            return answer(h,data)
        t=auth.authorized(h)
        if not t:return True
        if u.path.endswith('/create'):
            out=create(t['id'],data);h.send_json({'ok':True,**out});return True
        return control(h,data,u.path.rsplit('/',1)[-1])
    except ValueError as e:return error(h,str(e),400)
    except Exception as e:
        h.log_message('Game Lab Live error: %s',str(e))
        return error(h,'server_error',500)
