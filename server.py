#!/usr/bin/env python3
# QuizNova Arena - local classroom server (standard library + vendored QR generator)
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import json, random, string, time, threading, socket, webbrowser, os, sys, io

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'vendor'))
try:
    import qrcode
    import qrcode.image.svg
except Exception:
    qrcode = None

ROOMS = {}
LOCK = threading.RLock()
PORT = int(os.environ.get('PORT', '8765'))
IS_CLOUD = bool(os.environ.get('RENDER') or os.environ.get('RENDER_EXTERNAL_URL') or os.environ.get('QUIZNOVA_CLOUD'))
TEAM_NAMES = ['البرق ⚡','الصقور 🦅','النجوم ⭐','الفرسان 🛡️','الرواد 🚀','الأبطال 🏆']


def now_ms(): return int(time.time()*1000)
def rid(n=18): return ''.join(random.choice(string.ascii_letters+string.digits) for _ in range(n))
def code6():
    with LOCK:
        while True:
            c=''.join(random.choice(string.digits) for _ in range(6))
            if c not in ROOMS: return c

def shuffle(a):
    b=list(a); random.shuffle(b); return b

def prepare_quiz(quiz, game_mode, variant_mode='options'):
    q=json.loads(json.dumps(quiz, ensure_ascii=False))
    questions=q.get('questions',[])
    settings=q.get('settings',{})
    # In four-model mode each model receives its own question order, so keep the canonical list stable.
    if variant_mode!='models4' and settings.get('randomQuestions'):
        random.shuffle(questions)
    # Answer choices are intentionally kept canonical here. They are shuffled per student/device.
    if questions and variant_mode!='models4' and (game_mode=='boss' or settings.get('bossEnabled')):
        questions[-1]['_boss']=True
        questions[-1]['points']=int(questions[-1].get('points',1000))*2
    q['questions']=questions
    return q

def norm(s):
    s=str(s or '').strip().lower()
    trans=str.maketrans({'أ':'ا','إ':'ا','آ':'ا','ة':'ه','ى':'ي','َ':'','ً':'','ُ':'','ٌ':'','ِ':'','ٍ':'','ْ':'','ّ':''})
    return ' '.join(s.translate(trans).split())

def evaluate(q, ans):
    t=q.get('type')
    if t=='single': return ans == (q.get('correct') or [None])[0]
    if t=='multi': return sorted(ans or []) == sorted(q.get('correct') or [])
    if t=='tf': return ans is q.get('correct')
    if t=='short': return any(norm(x)==norm(ans) for x in q.get('answers',[]))
    if t=='order': return list(ans or []) == list(q.get('items',[]))
    if t=='match':
        pairs=q.get('pairs',[])
        return all(str((ans or {}).get(str(i),(ans or {}).get(i,'')))==str(p.get('right','')) for i,p in enumerate(pairs))
    if t=='poll': return None
    return False

def public_question(q):
    t=q.get('type')
    out={k:q.get(k) for k in ('id','type','text','time','points','image','difficulty','_boss','source','sourcePage') if k in q}
    if t in ('single','multi','poll'): out['options']=q.get('options',[])
    elif t=='order': out['items']=shuffle(q.get('items',[]))
    elif t=='match':
        out['lefts']=[p.get('left','') for p in q.get('pairs',[])]
        out['rights']=shuffle([p.get('right','') for p in q.get('pairs',[])])
    return out

def model_order(code, model, total):
    order=list(range(total))
    rng=random.Random(f'{code}:{model}:QuizNovaArena')
    rng.shuffle(order)
    return order

def player_question_index(room, p, round_idx):
    order=p.get('questionOrder') or list(range(len(room['quiz']['questions'])))
    if 0 <= round_idx < len(order): return order[round_idx]
    return round_idx

def public_question_for_player(room, p, round_idx):
    qidx=player_question_index(room,p,round_idx)
    q=room['quiz']['questions'][qidx]
    # Build a stable view so polling never changes the order on the student's screen.
    out={k:q.get(k) for k in ('id','type','text','time','points','image','difficulty','_boss','source','sourcePage') if k in q}
    seed=f"{room['code']}:{p['id']}:{round_idx}:{q.get('id','q')}"
    rng=random.Random(seed)
    t=q.get('type')
    if t in ('single','multi','poll'):
        key=str(round_idx); maps=p.setdefault('optionMaps',{})
        if room.get('variantMode')=='same':
            order=list(range(len(q.get('options',[]))))
        else:
            if key not in maps:
                order=list(range(len(q.get('options',[])))); rng.shuffle(order); maps[key]=order
            order=maps[key]
        out['options']=[q.get('options',[])[i] for i in order]
    elif t=='order':
        items=list(q.get('items',[])); rng.shuffle(items); out['items']=items
    elif t=='match':
        out['lefts']=[x.get('left','') for x in q.get('pairs',[])]
        rights=[x.get('right','') for x in q.get('pairs',[])]; rng.shuffle(rights); out['rights']=rights
    if room.get('bossFinal') and round_idx==len(room['quiz']['questions'])-1:
        out['_boss']=True; out['points']=int(q.get('points',1000) or 1000)*2
    out['_model']=p.get('model','')
    out['_questionIndex']=qidx
    return out

def canonical_answer(room,p,round_idx,ans):
    qidx=player_question_index(room,p,round_idx)
    q=room['quiz']['questions'][qidx]
    if q.get('type') in ('single','multi','poll'):
        order=p.get('optionMaps',{}).get(str(round_idx),list(range(len(q.get('options',[])))))
        def one(v):
            return order[v] if isinstance(v,int) and 0 <= v < len(order) else v
        if isinstance(ans,list): ans=[one(v) for v in ans]
        else: ans=one(ans)
    return qidx,q,ans

def correct_display(q):
    t=q.get('type')
    if t=='single':
        i=(q.get('correct') or [None])[0]
        return q.get('options',[None])[i] if isinstance(i,int) and i < len(q.get('options',[])) else ''
    if t=='multi':
        return '، '.join(q.get('options',[])[i] for i in q.get('correct',[]) if isinstance(i,int) and i < len(q.get('options',[])))
    if t=='tf': return 'صح' if q.get('correct') else 'خطأ'
    if t=='short': return ' / '.join(q.get('answers',[])[:3])
    if t=='order': return ' ← '.join(q.get('items',[]))
    if t=='match': return ' | '.join(f"{p.get('left','')} ↔ {p.get('right','')}" for p in q.get('pairs',[]))
    return 'استطلاع بلا إجابة صحيحة'

def local_ip():
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect(('8.8.8.8',80)); ip=s.getsockname()[0]; s.close(); return ip
    except Exception:
        try: return socket.gethostbyname(socket.gethostname())
        except Exception: return '127.0.0.1'

def public_base(handler):
    configured=os.environ.get('PUBLIC_BASE_URL','').strip().rstrip('/')
    if configured: return configured
    proto=(handler.headers.get('X-Forwarded-Proto') or ('https' if IS_CLOUD else 'http')).split(',')[0].strip()
    host=(handler.headers.get('X-Forwarded-Host') or handler.headers.get('Host') or '').split(',')[0].strip()
    if host: return f'{proto}://{host}'
    return f'http://{local_ip()}:{PORT}'

def cleanup_rooms():
    cutoff=now_ms()-8*60*60*1000
    with LOCK:
        stale=[c for c,r in ROOMS.items() if r.get('createdAt',0)<cutoff]
        for c in stale: ROOMS.pop(c,None)
    threading.Timer(1800, cleanup_rooms).start()

def choose_team(room):
    teams=room.get('teamNames', TEAM_NAMES[:4])
    counts={t:0 for t in teams}
    for p in room['players'].values():
        if p.get('team') in counts: counts[p['team']]+=1
    return min(teams, key=lambda t:(counts[t], teams.index(t))) if teams else ''

def team_leaders(room):
    totals={t:{'name':t,'score':0,'correct':0,'members':0} for t in room.get('teamNames',[])}
    for p in room['players'].values():
        t=p.get('team') or 'بدون فريق'
        totals.setdefault(t,{'name':t,'score':0,'correct':0,'members':0})
        totals[t]['score']+=p['score']; totals[t]['correct']+=p['correct']; totals[t]['members']+=1
    return sorted(totals.values(),key=lambda x:(x['score'],x['correct']),reverse=True)

def individual_leaders(room):
    return sorted([{'name':p['name'],'team':p.get('team',''),'score':p['score'],'correct':p['correct'],'wrong':p['wrong'],'streak':p['streak']} for p in room['players'].values()],key=lambda x:(x['score'],x['correct']),reverse=True)

def current_stats(room):
    idx=room['index']
    players=list(room['players'].values())
    total=len(players)
    if idx<0 or idx>=len(room['quiz']['questions']):
        return {'answered':0,'correct':0,'wrong':0,'pending':total,'accuracy':0,'distribution':[],'correctStudents':[],'wrongStudents':[],'reactions':{},'mixed':False,'models':[]}
    key=str(idx)
    answered=[p for p in players if key in p['answers']]
    correct=[p for p in answered if p['answers'][key]['correct'] is True]
    wrong=[p for p in answered if p['answers'][key]['correct'] is False]
    mixed=room.get('variantMode')=='models4'
    distribution=[]
    if not mixed:
        q=room['quiz']['questions'][idx]
        if q.get('type') in ('single','multi','poll'):
            opts=q.get('options',[]); counts=[0]*len(opts)
            for p in answered:
                a=p['answers'][key].get('answer')
                vals=a if isinstance(a,list) else [a]
                for v in vals:
                    if isinstance(v,int) and 0<=v<len(counts): counts[v]+=1
            distribution=[{'label':opts[i],'count':counts[i],'correct':i in q.get('correct',[])} for i in range(len(opts))]
        elif q.get('type')=='tf':
            tc=sum(1 for p in answered if p['answers'][key].get('answer') is True)
            fc=sum(1 for p in answered if p['answers'][key].get('answer') is False)
            distribution=[{'label':'صح','count':tc,'correct':q.get('correct') is True},{'label':'خطأ','count':fc,'correct':q.get('correct') is False}]
    models=[]
    if mixed:
        for model in sorted(set(p.get('model','') for p in players if p.get('model'))):
            ps=[p for p in players if p.get('model')==model]
            aq=[p for p in ps if key in p['answers']]
            cq=[p for p in aq if p['answers'][key].get('correct') is True]
            qidx=player_question_index(room,ps[0],idx) if ps else idx
            q=room['quiz']['questions'][qidx] if 0<=qidx<len(room['quiz']['questions']) else {}
            models.append({'model':model,'question':q.get('text',''),'answered':len(aq),'total':len(ps),'correct':len(cq)})
    reacts={}
    for emoji in room.get('reactions',{}).get(key,{}).values(): reacts[emoji]=reacts.get(emoji,0)+1
    return {
        'answered':len(answered),'correct':len(correct),'wrong':len(wrong),'pending':max(0,total-len(answered)),
        'accuracy':round((len(correct)/len(answered))*100) if answered else 0,
        'distribution':distribution,'correctStudents':[p['name'] for p in correct],'wrongStudents':[p['name'] for p in wrong],
        'reactions':reacts,'mixed':mixed,'models':models
    }

def final_report(room):
    total_q=sum(1 for q in room['quiz']['questions'] if q.get('type')!='poll')
    rows=[]
    for p in individual_leaders(room):
        percent=round((p['correct']/total_q)*100) if total_q else 100
        rows.append({**p,'percent':percent})
    return rows

def question_report(room):
    rows=[]; players=list(room['players'].values())
    for qidx,q in enumerate(room['quiz']['questions']):
        hits=[]
        for p in players:
            for round_key,a in p.get('answers',{}).items():
                if a.get('questionIndex', int(round_key) if str(round_key).isdigit() else -1)==qidx:
                    hits.append((p,a)); break
        correct=[p['name'] for p,a in hits if a.get('correct') is True]
        wrong=[p['name'] for p,a in hits if a.get('correct') is False]
        answered_names={p['name'] for p,a in hits}
        skipped=[p['name'] for p in players if p['name'] not in answered_names]
        scored=[a for p,a in hits if a.get('correct') is not None]
        acc=round(len(correct)/len(scored)*100) if scored else 0
        rows.append({'index':qidx,'text':q.get('text',''),'type':q.get('type',''),'correctAnswer':correct_display(q),'correctStudents':correct,'wrongStudents':wrong,'skippedStudents':skipped,'accuracy':acc,'source':q.get('source',''),'sourcePage':q.get('sourcePage','')})
    return rows

class Handler(SimpleHTTPRequestHandler):
    def translate_path(self,path):
        parsed=urlparse(path).path
        rel=parsed.lstrip('/') or 'index.html'
        safe=(ROOT/rel).resolve()
        if ROOT not in safe.parents and safe!=ROOT: return str(ROOT/'index.html')
        return str(safe)
    def log_message(self, fmt, *args):
        sys.stdout.write('[QuizNova] '+fmt%args+'\n')
    def send_bytes(self,data,ctype,status=200):
        self.send_response(status); self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(data))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(data)
    def send_json(self,obj,status=200):
        data=json.dumps(obj,ensure_ascii=False).encode('utf-8'); self.send_bytes(data,'application/json; charset=utf-8',status)
    def read_json(self):
        n=min(int(self.headers.get('Content-Length','0') or 0),5_000_000)
        raw=self.rfile.read(n) if n else b'{}'
        return json.loads(raw.decode('utf-8') or '{}')
    def do_GET(self):
        u=urlparse(self.path)
        if u.path=='/api/health':
            return self.send_json({'ok':True,'service':'quiznova-arena','rooms':len(ROOMS)})
        if u.path=='/api/status':
            base=public_base(self); return self.send_json({'ok':True,'mode':('cloud' if IS_CLOUD else 'local'),'student_url':base+'/student.html','teacher_url':base+'/', 'features':['qr','pin','teams','live-analytics','powerups','reactions','internet']})
        if u.path=='/api/qr':
            text=(parse_qs(u.query).get('text') or [''])[0]
            if not text or qrcode is None: return self.send_json({'ok':False,'error':'qr_unavailable'},404)
            qr=qrcode.QRCode(version=None,error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=8,border=3); qr.add_data(text); qr.make(fit=True)
            img=qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
            buf=io.BytesIO(); img.save(buf); return self.send_bytes(buf.getvalue(),'image/svg+xml; charset=utf-8')
        if u.path=='/api/room/state':
            qs=parse_qs(u.query); code=(qs.get('code') or [''])[0]; player=(qs.get('player') or [''])[0]; host=(qs.get('host') or [''])[0]; stage=(qs.get('stage') or [''])[0]
            with LOCK:
                room=ROOMS.get(code)
                if not room: return self.send_json({'ok':False,'error':'room_not_found'},404)
                idx=room['index']; total=len(room['quiz']['questions'])
                if player:
                    p=room['players'].get(player)
                    if not p: return self.send_json({'ok':False,'error':'player_not_found'},404)
                    q=None
                    if room['status']=='question' and 0<=idx<total: q=public_question_for_player(room,p,idx)
                    result=p.get('lastResult') if p.get('lastResult',{}).get('index')==idx else None
                    leaders=team_leaders(room) if room['playType']=='teams' else individual_leaders(room)[:10]
                    return self.send_json({'ok':True,'room':{
                        'status':room['status'],'index':idx,'total':total,'playType':room['playType'],'gameMode':room['gameMode'],'variantMode':room.get('variantMode','options'),'model':p.get('model',''),
                        'question':q,'startedAt':room.get('startedAt',0),'answeredCurrent':str(idx) in p['answers'],'lastResult':result,
                        'playerScore':p['score'],'playerCorrect':p['correct'],'playerStreak':p['streak'],'team':p.get('team',''),
                        'powerups':p.get('powerups',{}),'leaders':leaders,'quizTitle':room['quiz'].get('title',''),
                        'showFeedback':room['showFeedback'],'powerupsEnabled':room['powerupsEnabled']
                    }})
                is_host = bool(host) and host == room.get('hostToken')
                is_stage = bool(stage) and stage == room.get('stageToken')
                if not (is_host or is_stage): return self.send_json({'ok':False,'error':'host_auth_required'},403)
                players=[{'name':p['name'],'team':p.get('team',''),'model':p.get('model',''),'score':p['score'],'correct':p['correct'],'wrong':p['wrong'],'streak':p['streak']} for p in room['players'].values()]
                qobj=room['quiz']['questions'][idx] if 0<=idx<total else None
                stats=current_stats(room)
                return self.send_json({'ok':True,'room':{
                    'code':code,'status':room['status'],'index':idx,'total':total,'players':players,'playType':room['playType'],'gameMode':room['gameMode'],
                    'question':(public_question(qobj) if qobj and room.get('variantMode')!='models4' else None),'question_text':(qobj.get('text','') if qobj and room.get('variantMode')!='models4' else ''),
                    'correctAnswer':(correct_display(qobj) if qobj and room.get('variantMode')!='models4' else ''), 'stats':stats,'variantMode':room.get('variantMode','options'),
                    'leaders':individual_leaders(room),'teams':team_leaders(room),'teamNames':room.get('teamNames',[]),
                    'report':final_report(room) if room['status']=='finished' else [],
                    'questionReport':question_report(room) if room['status']=='finished' else []
                }})
        return super().do_GET()
    def do_POST(self):
        u=urlparse(self.path)
        try: data=self.read_json()
        except Exception: return self.send_json({'ok':False,'error':'bad_json'},400)
        if u.path=='/api/room/start':
            quiz=data.get('quiz'); play_type=data.get('playType','individual'); game_mode=data.get('gameMode','classic'); variant_mode=data.get('variantMode','options')
            if not isinstance(quiz,dict) or not isinstance(quiz.get('questions'),list) or not quiz['questions']: return self.send_json({'ok':False,'error':'invalid_quiz'},400)
            if play_type not in ('individual','teams'): play_type='individual'
            team_count=max(2,min(6,int(data.get('teamCount',4) or 4)))
            if variant_mode not in ('same','options','models4'): variant_mode='options'
            c=code6(); q=prepare_quiz(quiz,game_mode,variant_mode)
            with LOCK:
                host_token=rid(36); stage_token=rid(30)
                ROOMS[c]={'code':c,'quiz':q,'playType':play_type,'gameMode':game_mode,'status':'lobby','index':-1,'players':{},'createdAt':now_ms(),'startedAt':0,
                          'showFeedback':bool(data.get('showFeedback',True)),'powerupsEnabled':bool(data.get('powerups',True)),'variantMode':variant_mode,'bossFinal':bool(variant_mode=='models4' and (game_mode=='boss' or quiz.get('settings',{}).get('bossEnabled'))),
                          'teamNames':TEAM_NAMES[:team_count] if play_type=='teams' else [],'reactions':{},'hostToken':host_token,'stageToken':stage_token}
            root=public_base(self); base=root+'/student.html'; join=f'{base}?code={c}'
            return self.send_json({'ok':True,'code':c,'student_url':base,'join_url':join,'playType':play_type,'teamNames':ROOMS[c]['teamNames'],'variantMode':variant_mode,'hostToken':host_token,'stageToken':stage_token})
        if u.path=='/api/room/join':
            code=str(data.get('code','')).strip(); name=str(data.get('name','')).strip()[:60]
            if not name: return self.send_json({'ok':False,'error':'name_required'},400)
            with LOCK:
                room=ROOMS.get(code)
                if not room: return self.send_json({'ok':False,'error':'room_not_found'},404)
                if room['status']=='finished': return self.send_json({'ok':False,'error':'finished'},400)
                # prevent duplicate exact nickname in same room, but allow explicit suffix by student
                if any(norm(x['name'])==norm(name) for x in room['players'].values()): return self.send_json({'ok':False,'error':'name_taken'},409)
                team=choose_team(room) if room['playType']=='teams' else ''
                pid=rid(); model=''
                total=len(room['quiz']['questions']); order=list(range(total))
                if room.get('variantMode')=='models4':
                    model=['A','B','C','D'][len(room['players'])%4]; order=model_order(code,model,total)
                room['players'][pid]={'id':pid,'name':name,'team':team,'model':model,'questionOrder':order,'optionMaps':{},'score':0,'correct':0,'wrong':0,'streak':0,'answers':{},'lastResult':{},'powerups':{'double':True}}
            return self.send_json({'ok':True,'playerId':pid,'quizTitle':room['quiz'].get('title',''),'team':team,'playType':room['playType'],'model':model,'variantMode':room.get('variantMode','options')})
        if u.path=='/api/room/control':
            code=str(data.get('code','')); action=data.get('action'); host_token=str(data.get('hostToken',''))
            with LOCK:
                room=ROOMS.get(code)
                if not room: return self.send_json({'ok':False,'error':'room_not_found'},404)
                if not host_token or host_token != room.get('hostToken'): return self.send_json({'ok':False,'error':'host_auth_required'},403)
                if action=='start':
                    room['status']='question'; room['index']=0; room['startedAt']=now_ms()
                elif action=='reveal':
                    if room['status']=='question': room['status']='results'
                elif action=='next':
                    if room['status']=='lobby':
                        room['status']='question'; room['index']=0; room['startedAt']=now_ms()
                    elif room['status']=='question':
                        room['status']='results'
                    elif room['status']=='results':
                        room['index']+=1
                        if room['index']>=len(room['quiz']['questions']): room['status']='finished'; room['index']=len(room['quiz']['questions'])
                        else: room['status']='question'; room['startedAt']=now_ms()
                elif action=='end': room['status']='finished'; room['index']=len(room['quiz']['questions'])
                else: return self.send_json({'ok':False,'error':'bad_action'},400)
            return self.send_json({'ok':True})
        if u.path=='/api/room/answer':
            code=str(data.get('code','')); pid=str(data.get('playerId','')); idx=int(data.get('index',-1)); ans=data.get('answer'); elapsed=max(0,int(data.get('elapsedMs',0))); power=data.get('power','')
            with LOCK:
                room=ROOMS.get(code); p=room and room['players'].get(pid)
                if not room or not p: return self.send_json({'ok':False,'error':'not_found'},404)
                if room['status']!='question' or room['index']!=idx: return self.send_json({'ok':False,'error':'question_changed'},409)
                key=str(idx)
                if key in p['answers']: return self.send_json({'ok':True,'duplicate':True,'result':p['lastResult'],'score':p['score']})
                qidx,q,ans=canonical_answer(room,p,idx,ans); correct=evaluate(q,ans); points=int(q.get('points',1000) or 0);
                if room.get('bossFinal') and idx==len(room['quiz']['questions'])-1: points*=2
                earned=0; used_power=''
                if power=='double' and room['powerupsEnabled'] and p.get('powerups',{}).get('double'):
                    p['powerups']['double']=False; used_power='double'
                if correct is True and room['gameMode']!='zen':
                    t=max(1,int(q.get('time',20)))*1000; ratio=max(0,min(1,1-elapsed/t)); speed=room['gameMode']=='speed' or room['quiz'].get('settings',{}).get('speedBonus',False)
                    mult=(.60+.40*ratio) if speed else 1
                    p['streak']+=1
                    streak_bonus=min(0.25, max(0,p['streak']-1)*0.05)
                    mult*=1+streak_bonus
                    if used_power=='double': mult*=2
                    earned=round(points*mult); p['score']+=earned; p['correct']+=1
                elif correct is False:
                    p['wrong']+=1; p['streak']=0
                p['answers'][key]={'correct':correct,'earned':earned,'answer':ans,'elapsedMs':elapsed,'power':used_power,'questionIndex':qidx}
                p['lastResult']={'index':idx,'correct':correct,'earned':earned,'streak':p['streak'],'power':used_power}
            return self.send_json({'ok':True,'result':p['lastResult'],'score':p['score'],'powerups':p['powerups']})
        if u.path=='/api/room/react':
            code=str(data.get('code','')); pid=str(data.get('playerId','')); idx=str(int(data.get('index',-1))); emoji=str(data.get('emoji',''))[:4]
            if emoji not in ('🔥','🤩','😅','🤔'): return self.send_json({'ok':False,'error':'bad_reaction'},400)
            with LOCK:
                room=ROOMS.get(code); p=room and room['players'].get(pid)
                if not room or not p: return self.send_json({'ok':False,'error':'not_found'},404)
                room.setdefault('reactions',{}).setdefault(idx,{})[pid]=emoji
            return self.send_json({'ok':True})
        return self.send_json({'ok':False,'error':'unknown_endpoint'},404)

if __name__=='__main__':
    os.chdir(ROOT)
    ip=local_ip()
    cleanup_rooms()
    print('\n'+'='*68)
    print(' QuizNova Arena - Online/Local Classroom Server')
    print(' Port    : %d'%PORT)
    if IS_CLOUD:
        print(' Mode    : CLOUD / INTERNET')
    else:
        print(' Teacher : http://localhost:%d/'%PORT)
        print(' Students: http://%s:%d/student.html'%(ip,PORT))
        threading.Timer(1.0, lambda:webbrowser.open(f'http://localhost:{PORT}/')).start()
    print(' QR + PIN + Teams + Live analytics are ready.')
    print('='*68+'\n')
    try: ThreadingHTTPServer(('0.0.0.0',PORT),Handler).serve_forever()
    except KeyboardInterrupt: print('\nQuizNova Arena stopped.')
