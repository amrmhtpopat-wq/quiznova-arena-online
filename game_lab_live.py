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
import platform_store as db
import platform_api as auth
import solo_api
import game_lab_api as games

GET={'/api/game-lab/live/state','/api/game-lab/live/rooms'}
HOST={'/api/game-lab/live/create','/api/game-lab/live/next',
      '/api/game-lab/live/finish','/api/game-lab/live/start'}
STUDENT={'/api/game-lab/live/join','/api/game-lab/live/answer','/api/game-lab/live/state'}
TTL=5*3600


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
    idx=int(s['index'])
    if idx<0 or idx>=len(s['rows']):return None
    row=s['rows'][idx]
    available=[]
    for item in s['rows']:
        if item['a'] not in available and item['a']!=row['a']:
            available.append(item['a'])
    rng=hashlib.sha256((s['seed']+str(idx)).encode()).digest()
    from random import Random
    random=Random(int.from_bytes(rng[:8],'big'))
    random.shuffle(available)
    opts=[row['a']]+available[:3]
    random.shuffle(opts)
    result={'index':idx,'total':len(s['rows']),'text':row['q'],
            'options':opts,'group':row['g'],'duration':s['duration'],
            'imageUrl':s.get('imageUrl') or '',
            'mode':s['mode']}
    if with_answers:result['correctAnswer']=row['a']
    return result


def snapshot(room,players,role='',person=None):
    s=state(room)
    current=phase(room,players)
    idx=int(s.get('index',0))
    mine=db.jload(person['answers'],{}) if person else {}
    responded=bool(person and str(idx) in mine)
    correct=None
    if current=='results' and (s['showFeedback'] or role=='teacher'):
        correct=s['rows'][idx]['a'] if idx<len(s['rows']) else None
    answer_data=None
    if role=='teacher':
        answered=sum(1 for p in players if str(idx) in db.jload(p['answers'],{}))
        answer_data={'answered':answered,'total':len(players)}
    leaderboard=[{'name':x['student_name'],'className':x['class_name'],
                  'team':x['team'],'score':x['score']} for x in players[:10]]
    teams={}
    for p in players:
        if p['team']:teams[p['team']]=teams.get(p['team'],0)+int(p['score'])
    grouped=sorted([{'name':name,'score':score} for name,score in teams.items()],
                   key=lambda x:-x['score'])
    data={'code':room['code'],'title':s['title'],'status':current,
          'index':idx,'total':len(s['rows']),'deadline':s.get('deadline',0),
          'duration':s['duration'],'showFeedback':s['showFeedback'],'teams':s['teams'],
          'leaderboard':leaderboard,'teamLeaderboard':grouped,'participants':len(players),
          'question':question(s,with_answers=role=='teacher') if current in ('question','results') else None,
          'correctAnswer':correct,'roomUpdatedAt':room['updated_at']}
    if role=='teacher':data['answerStats']=answer_data
    if person and person['team']:
        data['teammates']=[p['student_name'] for p in players if p['team']==person['team']][:50]
    if person:data['me']={'name':person['student_name'],'team':person['team'],
             'score':person['score'],'answered':responded,
             'answerCorrect':mine.get(str(idx),{}).get('correct') if current=='results' and s['showFeedback'] else None}
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
    try:duration=int(data.get('duration',payload.get('time',25)))
    except (TypeError,ValueError):duration=25
    duration=max(10,min(120,duration))
    team_mode=data.get('teams') is True
    names=[str(x).strip()[:30] for x in data.get('teamNames',[]) if isinstance(x,str)] if isinstance(data.get('teamNames'),list) else []
    if team_mode and len(names)<2:names=['الصقور','النمور']
    code=code_new()
    settings={'status':'lobby','title':activity['title'],'index':0,'rows':rows[:60],
              'duration':duration,'mode':activity['mode'],'showFeedback':data.get('showFeedback') is not False,
              'teams':team_mode,'teamNames':names[:6],'seed':secrets.token_hex(12),
              'deadline':0,'imageUrl':''}
    if payload.get('imageId') and len(str(payload['imageId']))==32:
        settings['imageUrl']='/api/game-lab/pro/image?id='+payload['imageId']+'&code='+(activity['public_code'] or '')
    db.exec_sql('INSERT INTO game_lab_live_rooms(code,teacher_id,activity_id,state,created_at,updated_at) '
                'VALUES(?,?,?,?,?,?)',(code,tid,aid,db.jdump(settings),stamp(),stamp()))
    return {'code':code,'teacherUrl':'/game-lab-live.html?host='+code,
            'studentUrl':'/game-lab-live.html?code='+code}


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
    name=student['name'] if student else str(data.get('guestName') or '').strip()[:40]
    if len(name)<2:return error(h,'name_required')
    if student:
        old=db.query('SELECT id FROM game_lab_live_players WHERE code=? AND student_id=?',
                     (code,student['id']))
        if old:return error(h,'already_joined',409)
    token=secrets.token_urlsafe(36)
    with db.DB_LOCK:
        with db.db_connection() as conn:
            cur=conn.execute(db.sql('SELECT COUNT(*) FROM game_lab_live_players WHERE code=?'),(code,))
            count=int(cur.fetchone()[0])
            if count>=200:return error(h,'room_full',403)
            team=s['teamNames'][count%len(s['teamNames'])] if s['teams'] else ''
            conn.execute(db.sql('INSERT INTO game_lab_live_players '
              '(id,code,teacher_id,student_id,student_name,class_name,team,token_hash,'
              'answers,joined_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)'),
              (uuid.uuid4().hex,code,room['teacher_id'],student['id'] if student else None,
               name,student['class_name'] if student else 'ضيف',team,sha(token),'{}',stamp(),stamp()))
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
            answers=db.jload(player['answers'],{})
            if str(idx) in answers:return error(h,'already_answered',409)
            expected=s['rows'][idx]['a']
            valid_options=question(s)['options']
            if choice not in valid_options:return error(h,'invalid_answer')
            correct=choice.casefold()==expected.casefold()
            # Deadline score is never reported to clients until the server records it.
            gained=(100+max(0,int(s['deadline'])-stamp())*2) if correct else 0
            answers[str(idx)]={'correct':correct,'answer':choice,'score':gained}
            conn.execute(db.sql('UPDATE game_lab_live_players SET answers=?,score=score+?,updated_at=? '
                     'WHERE id=?'),(db.jdump(answers),gained,stamp(),player['id']))
    h.send_json({'ok':True,'submitted':True})
    return True


def handle_get(h,u):
    if u.path not in GET:return False
    params=parse_qs(u.query);code=(params.get('code') or [''])[0]
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
    if not person:return error(h,'invalid_session',403)
    h.send_json({'ok':True,'state':snapshot(room,roster(room['code']),person=person)})
    return True


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
