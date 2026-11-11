#!/usr/bin/env python3
# QuizNova Arena - local classroom server (standard library + vendored QR generator)
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import json, random, string, time, threading, socket, webbrowser, os, sys, io, zlib, struct, re, math
from datetime import datetime, timezone, timedelta
from xlsx_report import generate_report
import platform_store
platform_store.init()
import platform_api
import solo_api
solo_api.ensure_schema()
import admin_api
admin_api.initialize()
import visitor_analytics
visitor_analytics.initialize()

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT / 'vendor'))
try:
    import qrcode  # available from requirements.txt in cloud; vendored fallback locally
except Exception:
    qrcode = None

ROOMS = {}
LOCK = threading.RLock()
PORT = int(os.environ.get('PORT', '8765'))
IS_CLOUD = bool(os.environ.get('RENDER') or os.environ.get('RENDER_EXTERNAL_URL') or os.environ.get('QUIZNOVA_CLOUD'))
TEAM_NAMES = ['البرق ⚡','الصقور 🦅','النجوم ⭐','الفرسان 🛡️','الرواد 🚀','الأبطال 🏆']
AVATARS = platform_store.AVATAR_3D_IDS + [f'{i:02}' for i in range(1, 21)]
SCENES = ['cartoon','anime','cinematic','cine-stars','cine-aurora','cine-neon','cine-desert','cine-arena']


def qr_png(text, scale=9, border=4):
    """Render an actual black-white QR as PNG (pure stdlib output, no Pillow required)."""
    if qrcode is None:
        raise RuntimeError('QR encoder unavailable')
    qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=0)
    qr.add_data(text);qr.make(fit=True)
    matrix=qr.get_matrix();side=len(matrix);n=side+border*2;width=n*scale
    white=bytes([255,255,255]);black=bytes([8,37,72]);rows=[]
    for y in range(n):
        j=y-border
        bits=[(0 <= j < side and 0 <= x-border < side and matrix[j][x-border]) for x in range(n)]
        row=b'\x00'+b''.join(black if v else white for v in bits for _ in range(scale))
        rows.extend([row]*scale)
    def chunk(name,data): return struct.pack('!I',len(data))+name+data+struct.pack('!I',zlib.crc32(name+data)&0xffffffff)
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',width,width,8,2,0,0,0))+
            chunk(b'IDAT',zlib.compress(b''.join(rows),8))+chunk(b'IEND',b''))

def qr_svg(text):
    if qrcode is None: raise RuntimeError('QR encoder unavailable')
    qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=1,border=0)
    qr.add_data(text);qr.make(fit=True)
    matrix=qr.get_matrix();border=4;size=len(matrix)+border*2
    # Horizontal run-length rectangles keep the image compact, portable and crisp on every browser.
    rects=[]
    for y,row in enumerate(matrix):
        i=0
        while i<len(row):
            if not row[i]: i+=1;continue
            j=i+1
            while j<len(row) and row[j]:j+=1
            rects.append(f'<rect x="{i+border}" y="{y+border}" width="{j-i}" height="1"/>');i=j
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="300" height="300" shape-rendering="crispEdges"><rect width="{size}" height="{size}" fill="white"/><g fill="#082548">'+''.join(rects)+'</g></svg>'
    return svg.encode('utf-8')

def now_ms(): return int(time.time()*1000)
def rid(n=18): return ''.join(random.choice(string.ascii_letters+string.digits) for _ in range(n))
def code6():
    with LOCK:
        while True:
            c=''.join(random.choice(string.digits) for _ in range(6))
            if c not in ROOMS: return c

def shuffle(a):
    b=list(a); random.shuffle(b); return b

def safe_image_path(value):
    if not isinstance(value,str):return ''
    value=value.strip()
    if re.fullmatch(r'/assets/[a-zA-Z0-9_./-]{1,180}\.(?:png|jpg|jpeg|webp|svg)',value):
        return value if '..' not in value else ''
    if len(value)<8_000_000 and re.fullmatch(r'data:image/(?:png|jpeg|webp);base64,[A-Za-z0-9+/=]+',value):
        return value
    return ''

def prepare_quiz(quiz, game_mode, variant_mode='options'):
    q=json.loads(json.dumps(quiz, ensure_ascii=False))
    questions=q.get('questions',[])
    if len(questions)>250:questions=questions[:250]
    for x in questions:
        x['image']=safe_image_path(x.get('image',''))
        x['text']=str(x.get('text',''))[:2500]
        x['explanation']=str(x.get('explanation',''))[:1500]
        x['skill']=str(x.get('skill') or x.get('topic') or x.get('unit') or 'مهارات عامة')[:150]
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
    if t=='estimate':
        try:
            if isinstance(ans,bool):return False
            number=float(str(ans).strip().replace('٫','.').replace('،','.'))
            expected=float(q.get('estimateAnswer'))
            tolerance=float(q.get('tolerance',0))
            return all(math.isfinite(v) for v in (number,expected,tolerance)) and tolerance>=0 and abs(number-expected)<=tolerance
        except (ValueError,TypeError,OverflowError):return False
    if t=='order': return list(ans or []) == list(q.get('items',[]))
    if t=='match':
        pairs=q.get('pairs',[])
        return all(str((ans or {}).get(str(i),(ans or {}).get(i,'')))==str(p.get('right','')) for i,p in enumerate(pairs))
    if t=='poll': return None
    return False

def public_question(q):
    t=q.get('type')
    out={k:q.get(k) for k in ('id','type','text','time','points','image','difficulty','_boss','source','sourcePage','unit','skill') if k in q}
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
    out={k:q.get(k) for k in ('id','type','text','time','points','image','difficulty','_boss','source','sourcePage','unit','skill') if k in q}
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
    if t=='estimate': return f"{q.get('estimateAnswer','')} ± {q.get('tolerance',0)}"
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
    if host:
        if not IS_CLOUD and (host.startswith('localhost:') or host.startswith('127.0.0.1:') or host in ('localhost','127.0.0.1')):
            return f"http://{local_ip()}:{handler.server.server_port}"
        return f'{proto}://{host}'
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
    if not teams:return ''
    minimum=min(counts.values())
    return random.choice([t for t in teams if counts[t]==minimum])

def team_leaders(room):
    totals={t:{'name':t,'score':0,'correct':0,'members':0} for t in room.get('teamNames',[])}
    for p in room['players'].values():
        t=p.get('team') or 'بدون فريق'
        totals.setdefault(t,{'name':t,'score':0,'correct':0,'members':0})
        totals[t]['score']+=p['score']; totals[t]['correct']+=p['correct']; totals[t]['members']+=1
    return sorted(totals.values(),key=lambda x:(x['score'],x['correct']),reverse=True)

def individual_leaders(room):
    return sorted([{'name':p['name'],'team':p.get('team',''),'avatar':p.get('avatar','01'),'model':p.get('model',''),'avatar':p.get('avatar','01'),'score':p['score'],'correct':p['correct'],'wrong':p['wrong'],'streak':p['streak']} for p in room['players'].values()],key=lambda x:(x['score'],x['correct']),reverse=True)

def round_duration_ms(room):
    idx=room['index']
    if idx<0 or idx>=len(room['quiz']['questions']): return 20000
    # In A/B/C/D mode, allow the maximum of the different question durations.
    if room.get('variantMode')=='models4':
        qidxs={player_question_index(room,p,idx) for p in room['players'].values()}
        if not qidxs: qidxs=set(range(len(room['quiz']['questions'])))
        return max(5000, max(int(room['quiz']['questions'][i].get('time',20) or 20) for i in qidxs)*1000)
    return max(5000,int(room['quiz']['questions'][idx].get('time',20) or 20)*1000)

def snapshot_room(room):
    try:platform_store.save_active_room(room)
    except Exception as exc:print('[QuizNova] room snapshot error:',repr(exc),flush=True)

def maybe_end_round(room):
    if room['status']!='question': return False
    players=list(room['players'].values())
    index=str(room['index'])
    time_up=now_ms() >= room.get('startedAt',0)+room.get('roundDurationMs',20000)
    everyone=bool(players) and all(index in p['answers'] for p in players)
    if time_up or everyone:
        finish_round(room,'timeout' if time_up else 'all_answered')
        return True
    return False

def persist_finished_room(room):
    if room.get('_persisted') or not room.get('teacherId'):return
    room['_persisted']=True
    try:
        platform_store.persist_room(room, final_report(room), question_report(room))
    except Exception as exc:
        room['_persisted']=False
        print('[QuizNova] persistence error:',repr(exc),flush=True)

def finish_round(room,reason='manual'):
    if room['status']!='question':return
    if room.get('cooperative') and room['playType']=='teams':
        idx=str(room['index'])
        for team in room.get('teamNames',[]):
            members=[p for p in room['players'].values() if p.get('team')==team]
            if not members:continue
            votes=[p.get('answers',{}).get(idx) for p in members]
            full=bool(votes) and all(a is not None and a.get('correct') is True for a in votes)
            # Team consensus means every member chose the same canonical correct answer.
            if full:
                votes_json=[json.dumps(a.get('answer'),sort_keys=True,ensure_ascii=False) for a in votes]
                full=len(set(votes_json))==1
            for p,a in zip(members,votes):
                if not a or a.get('consensusResolved'):continue
                bonus=int(a.get('pendingTeamBonus',0)) if full else 0
                p['score']+=bonus
                a['earned']+=bonus;a['consensusResolved']=True
                a['teamConsensus']=full
                if p.get('lastResult',{}).get('index')==room['index']:
                    p['lastResult']['earned']+=bonus
                    p['lastResult']['teamConsensus']=full
    room['status']='results'
    room['roundEndedAt']=now_ms()
    room['roundEndReason']=reason
    snapshot_room(room)

def next_round(room):
    if room['status']=='question':finish_round(room,'skip')
    room['index']+=1
    if room['index']>=len(room['quiz']['questions']):
        room['status']='finished'
        room['finishedAt']=now_ms()
        room['index']=len(room['quiz']['questions'])
        persist_finished_room(room)
    else:
        room['status']='question'
        room['startedAt']=now_ms()
        room['roundDurationMs']=round_duration_ms(room)
        room['roundEndReason']=''
    snapshot_room(room)

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
        rows.append({**p,'percent':percent,'unanswered':max(0,total_q-p['correct']-p['wrong'])})
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
        rows.append({'index':qidx,'text':q.get('text',''),'type':q.get('type',''),'correctAnswer':correct_display(q),'correctStudents':correct,'wrongStudents':wrong,'skippedStudents':skipped,'accuracy':acc,'source':q.get('source',''),'sourcePage':q.get('sourcePage',''),'skill':q.get('skill') or q.get('unit') or 'مهارات عامة','unit':q.get('unit',''),'explanation':q.get('explanation','')})
    return rows

class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Revalidate HTML after each release; student cards and teacher screens
        # must not remain on an old cached brand or bundled script references.
        requested=urlparse(self.path).path
        if requested=='/' or requested.lower().endswith('.html'):
            self.send_header('Cache-Control','no-cache, max-age=0, must-revalidate')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Referrer-Policy','same-origin')
        self.send_header('Permissions-Policy','camera=(), microphone=(), geolocation=()')
        if IS_CLOUD:self.send_header('Strict-Transport-Security','max-age=15552000')
        return super().end_headers()
    def translate_path(self,path):
        parsed=urlparse(path).path
        rel=parsed.lstrip('/') or 'index.html'
        safe=(ROOT/rel).resolve()
        if ROOT not in safe.parents and safe!=ROOT:return str(ROOT/'__not_found__')
        # Never expose database credentials, Python sources or other private server files.
        if safe.is_dir():return str(ROOT/'__not_found__')
        # Serve only the two public SEO resources; do not expose arbitrary .txt/.xml files.
        if rel in ('robots.txt', 'sitemap.xml'):return str(safe)
        allowed={'.html','.js','.css','.svg','.png','.jpg','.jpeg','.webp','.ico','.woff','.woff2'}
        if safe.suffix.lower() not in allowed:return str(ROOT/'__not_found__')
        return str(safe)
    def log_message(self, fmt, *args):
        sys.stdout.write('[QuizNova] '+fmt%args+'\n')
    def send_bytes(self,data,ctype,status=200):
        self.send_response(status); self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(data))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(data)
    def send_json(self,obj,status=200):
        data=json.dumps(obj,ensure_ascii=False).encode('utf-8'); self.send_bytes(data,'application/json; charset=utf-8',status)
    def read_json(self):
        n=min(int(self.headers.get('Content-Length','0') or 0),13_000_000)
        raw=self.rfile.read(n) if n else b'{}'
        return json.loads(raw.decode('utf-8') or '{}')
    def do_GET(self):
        u=urlparse(self.path)
        if admin_api.handle_get(self,u):return
        if platform_api.handle_get(self,u):return
        if u.path=='/api/health':
            try:
                result=platform_store.query('SELECT 1 AS ok')
                if not result or int(result['ok'])!=1:raise RuntimeError('db_not_ready')
            except Exception:
                return self.send_json({'ok':False,'service':'quiznova-arena','version':'10.5-beta','database':'unavailable'},503)
            return self.send_json({'ok':True,'service':'quiznova-arena','version':'10.5-beta','storage':platform_store.DATABASE_KIND,'database':'ready','rooms':len(ROOMS)})
        if u.path=='/api/status':
            base=public_base(self); return self.send_json({'ok':True,'mode':('cloud' if IS_CLOUD else 'local'),'student_url':base+'/student.html','teacher_url':base+'/', 'features':['qr','pin','teams','live-analytics','powerups','reactions','internet','auth','student-cards','solo-practice','exams','classwars','mastery','persistent-reports']})
        if u.path=='/api/qr':
            qs=parse_qs(u.query);text=(qs.get('text') or [''])[0]
            if not text or len(text)>2000: return self.send_json({'ok':False,'error':'invalid_qr_content'},400)
            try:
                if (qs.get('format') or ['png'])[0].lower()=='svg':
                    return self.send_bytes(qr_svg(text),'image/svg+xml; charset=utf-8')
                return self.send_bytes(qr_png(text),'image/png')
            except Exception as e:
                self.log_message('QR generation failure: %s',str(e))
                return self.send_json({'ok':False,'error':'qr_unavailable'},503)
        if u.path=='/api/card/profile':
            qs=parse_qs(u.query);value=(qs.get('card') or [''])[0]
            student=platform_store.student_profile_by_card(value)
            if not student:return self.send_json({'ok':False,'error':'invalid_card'},404)
            return self.send_json({'ok':True,'name':student['name'],'className':student['class_name'],
                'avatar':student['avatar'],'xp':student['xp'],
                'level':platform_store.level_for_xp(student['xp']),
                'progress':platform_store.xp_progress(student['xp']),
                'correct':student['correct_count'],'played':student['played_count']})
        if u.path=='/api/room/config':
            qs=parse_qs(u.query); code=(qs.get('code') or [''])[0]
            with LOCK:
                room=ROOMS.get(code)
                if not room:return self.send_json({'ok':False,'error':'room_not_found'},404)
                school_type=room.get('schoolType','mixed')
                return self.send_json({'ok':True,'schoolType':school_type,'avatars':platform_store.avatar_pool(school_type),
                                      'section':room.get('section',''),'subject':room['quiz'].get('subject','عام'),
                                      'examMode':bool(room.get('examMode')),'requireCard':bool(room.get('requireCard'))})
        if u.path=='/api/card/resolve':
            qs=parse_qs(u.query);card=(qs.get('card') or [''])[0];code=(qs.get('code') or [''])[0]
            with LOCK:
                room=ROOMS.get(code)
                if not room:return self.send_json({'ok':False,'error':'room_not_found'},404)
                s=platform_store.student_by_card(card,room.get('teacherId',''))
                if not s:return self.send_json({'ok':False,'error':'invalid_card'},403)
                return self.send_json({'ok':True,'name':s['name'],'avatar':s['avatar'],'className':s['class_name'],'level':platform_store.level_for_xp(s['xp']),'xp':s['xp'],'progress':platform_store.xp_progress(s['xp'])})
        if u.path=='/api/room/export.xlsx':
            qs=parse_qs(u.query); code=(qs.get('code') or [''])[0]; token=(qs.get('host') or [''])[0]
            with LOCK:
                room=ROOMS.get(code)
                if not room: return self.send_json({'ok':False,'error':'room_not_found'},404)
                if not token or token != room.get('hostToken'): return self.send_json({'ok':False,'error':'host_auth_required'},403)
                if room['status']!='finished': return self.send_json({'ok':False,'error':'not_finished'},409)
                report=generate_report(room,final_report(room),question_report(room))
            self.send_response(200)
            self.send_header('Content-Type','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            self.send_header('Content-Disposition',f'attachment; filename="TeachGame_{code}_report.xlsx"')
            self.send_header('Cache-Control','no-store')
            self.send_header('Content-Length',str(len(report)))
            self.end_headers();self.wfile.write(report);return
        if u.path=='/api/room/state':
            qs=parse_qs(u.query); code=(qs.get('code') or [''])[0]; player=(qs.get('player') or [''])[0]; host=(qs.get('host') or [''])[0]; stage=(qs.get('stage') or [''])[0]
            with LOCK:
                room=ROOMS.get(code)
                if not room: return self.send_json({'ok':False,'error':'room_not_found'},404)
                maybe_end_round(room)
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
                        'question':q,'review':({'explanation':room['quiz']['questions'][player_question_index(room,p,idx)].get('explanation',''),'image':room['quiz']['questions'][player_question_index(room,p,idx)].get('image',''),'correctAnswer':correct_display(room['quiz']['questions'][player_question_index(room,p,idx)])} if room['status']=='results' and room.get('showFeedback',True) and not room.get('examMode') and 0<=idx<total else None),'startedAt':room.get('startedAt',0),'answeredCurrent':str(idx) in p['answers'],'lastResult':((dict(result,correct=None) if result and not room.get('showFeedback',True) else result) if not room.get('examMode') else ({'index':idx,'correct':None,'earned':0} if result else None)),
                        'playerScore':(p['score'] if not room.get('examMode') or room['status']=='finished' else 0),'playerCorrect':(p['correct'] if not room.get('examMode') or room['status']=='finished' else 0),'playerStreak':(p['streak'] if not room.get('examMode') else 0),'team':p.get('team',''),
                        'teamMembers':([{'name':other['name'],'avatar':other.get('avatar','b01')} for other in room['players'].values() if other.get('team')==p.get('team')] if room['playType']=='teams' and p.get('team') else []),
                        'teamScore':(sum(int(other.get('score',0)) for other in room['players'].values() if other.get('team')==p.get('team')) if room['playType']=='teams' and p.get('team') and not room.get('examMode') else 0),
                        'powerups':p.get('powerups',{}),'leaders':(leaders if not room.get('examMode') or room['status']=='finished' else []),'examMode':bool(room.get('examMode')),'level':p.get('level',1),'xp':p.get('xp',0),'xpGain':p.get('xpGain',0),'xpBreakdown':p.get('xpBreakdown',{}),'levelUp':bool(p.get('levelUp',False)),'progress':platform_store.xp_progress(p.get('xp',0)),'quizTitle':room['quiz'].get('title',''),
                        'showFeedback':(room['showFeedback'] and not room.get('examMode')),'powerupsEnabled':(room['powerupsEnabled'] and not room.get('examMode')),'background':room.get('background','cartoon'),'cooperative':bool(room.get('cooperative')),'roundDurationMs':room.get('roundDurationMs',20000),'avatar':p.get('avatar','01')
                    }})
                is_host = bool(host) and host == room.get('hostToken')
                is_stage = bool(stage) and stage == room.get('stageToken')
                if not (is_host or is_stage): return self.send_json({'ok':False,'error':'host_auth_required'},403)
                # Only the authenticated host sees private per-student marks during an active exam.
                exam_private=room.get('examMode') and room['status']!='finished' and not is_host
                players=[{'id':(p['id'] if is_host else ''),'name':p['name'],'level':p.get('level',1),'team':p.get('team',''),'model':p.get('model',''),'avatar':p.get('avatar','01'),'score':0 if exam_private else p['score'],'correct':0 if exam_private else p['correct'],'wrong':0 if exam_private else p['wrong'],'streak':0 if exam_private else p['streak']} for p in room['players'].values()]
                qobj=room['quiz']['questions'][idx] if 0<=idx<total else None
                stats=current_stats(room)
                if (room.get('examMode') and room['status']!='finished') or (is_stage and room['status']=='question'):
                    stats={'answered':stats['answered'],'pending':stats['pending'],'correct':0,'wrong':0,'accuracy':0,'distribution':[], 'correctStudents':[], 'wrongStudents':[], 'reactions':{},'mixed':False,'models':[]}
                return self.send_json({'ok':True,'room':{
                    'code':code,'status':room['status'],'index':idx,'total':total,'players':players,'section':room.get('section',''),'quizTitle':room['quiz'].get('title',''),'createdAt':room.get('createdAt',0),'roundDurationMs':room.get('roundDurationMs',20000),'startedAt':room.get('startedAt',0),'roundEndReason':room.get('roundEndReason',''),'background':room.get('background','cartoon'),'requireCard':bool(room.get('requireCard')),'playType':room['playType'],'gameMode':room['gameMode'],
                    'question':(public_question(qobj) if qobj and room.get('variantMode')!='models4' else None),'question_text':(qobj.get('text','') if qobj and room.get('variantMode')!='models4' else ''),
                    'correctAnswer':(correct_display(qobj) if qobj and room.get('variantMode')!='models4' and (not room.get('examMode') or room['status']=='finished') and (not is_stage or room['status']!='question') else ''),'explanation':(qobj.get('explanation','') if qobj and room['status']!='question' and not room.get('examMode') else ''),'examMode':bool(room.get('examMode')),'showFeedback':bool(room.get('showFeedback',True)),'cooperative':bool(room.get('cooperative')),'stats':stats,'variantMode':room.get('variantMode','options'),
                    'leaders':(individual_leaders(room) if not room.get('examMode') or room['status']=='finished' else []),'teams':(team_leaders(room) if not room.get('examMode') or room['status']=='finished' else []),'teamNames':room.get('teamNames',[]),'teamAssignment':room.get('teamAssignment','random'),
                    'report':final_report(room) if room['status']=='finished' else [],
                    'questionReport':question_report(room) if room['status']=='finished' else []
                }})
        return super().do_GET()
    def do_POST(self):
        u=urlparse(self.path)
        if u.path=='/api/visitors/track':
            try: body_length=int(self.headers.get('Content-Length','0') or 0)
            except ValueError: return self.send_json({'ok':False,'error':'bad_length'},400)
            if body_length<1 or body_length>512:
                return self.send_json({'ok':False,'error':'payload_too_large'},413)
            try: tracking=self.read_json()
            except Exception: return self.send_json({'ok':False,'error':'bad_json'},400)
            return visitor_analytics.handle_post(self,tracking)
        try: data=self.read_json()
        except Exception: return self.send_json({'ok':False,'error':'bad_json'},400)
        if admin_api.handle_post(self,u,data):return
        if platform_api.handle_post(self,u,data):return
        if solo_api.handle_post(self,u,data):return
        if u.path=='/api/room/start':
            teacher=platform_api.authorized(self)
            if not teacher:return
            quiz=data.get('quiz'); play_type=data.get('playType','individual'); game_mode=data.get('gameMode','classic'); variant_mode=data.get('variantMode','options')
            if not isinstance(quiz,dict) or not isinstance(quiz.get('questions'),list) or not quiz['questions']: return self.send_json({'ok':False,'error':'invalid_quiz'},400)
            if play_type not in ('individual','teams'): play_type='individual'
            team_assignment='manual' if data.get('teamAssignment')=='manual' and play_type=='teams' else 'random'
            team_count=max(2,min(6,int(data.get('teamCount',4) or 4)))
            if variant_mode not in ('same','options','models4'): variant_mode='options'
            exam=bool(data.get('examMode'))
            if exam: variant_mode='models4' if variant_mode=='models4' else 'options'
            if bool(data.get('cooperative')) and play_type=='teams':variant_mode='options'
            c=code6(); q=prepare_quiz(quiz,game_mode,variant_mode)
            section=str(data.get('section') or quiz.get('section') or '').strip()[:75]
            background=str(data.get('background') or 'cartoon')
            if background not in SCENES: background='cartoon'
            with LOCK:
                host_token=rid(36); stage_token=rid(30)
                ROOMS[c]={'code':c,'quiz':q,'playType':play_type,'gameMode':game_mode,'status':'lobby','index':-1,'players':{},'createdAt':now_ms(),'startedAt':0,
                          'showFeedback':(bool(data.get('showFeedback',True)) and not exam),'powerupsEnabled':(bool(data.get('powerups',True)) and not exam),'examMode':exam,'maxAttempts':max(1,min(5,int(data.get('maxAttempts',1) or 1))),'requireCard':bool(data.get('requireCard',False)),'cooperative':(bool(data.get('cooperative')) and play_type=='teams' and not exam),'teacherId':teacher['id'],'schoolType':teacher.get('school_type','mixed'),'_persisted':False,'variantMode':variant_mode,'bossFinal':bool(variant_mode=='models4' and (game_mode=='boss' or quiz.get('settings',{}).get('bossEnabled'))),
                          'teamNames':TEAM_NAMES[:team_count] if play_type=='teams' else [],'teamAssignment':team_assignment,'reactions':{},'hostToken':host_token,'stageToken':stage_token,'section':section,'background':background,'roundDurationMs':20000,'roundEndReason':''}
            snapshot_room(ROOMS[c])
            root=public_base(self); base=root+'/student.html'; join=f'{base}?code={c}'
            return self.send_json({'ok':True,'code':c,'student_url':base,'join_url':join,'playType':play_type,'teamNames':ROOMS[c]['teamNames'],'teamAssignment':team_assignment,'variantMode':variant_mode,'hostToken':host_token,'stageToken':stage_token})
        if u.path=='/api/room/team':
            code=str(data.get('code','')).strip()
            host_token=str(data.get('hostToken',''))
            player_id=str(data.get('playerId',''))
            team=str(data.get('team','')).strip()
            with LOCK:
                room=ROOMS.get(code)
                if not room:return self.send_json({'ok':False,'error':'room_not_found'},404)
                if not host_token or host_token!=room.get('hostToken'):return self.send_json({'ok':False,'error':'host_auth_required'},403)
                if room['status']!='lobby' or room['playType']!='teams':return self.send_json({'ok':False,'error':'not_in_lobby'},409)
                if team not in room['teamNames']:return self.send_json({'ok':False,'error':'invalid_team'},400)
                player=room['players'].get(player_id)
                if not player:return self.send_json({'ok':False,'error':'player_not_found'},404)
                player['team']=team
                snapshot_room(room)
            return self.send_json({'ok':True,'team':team})
        if u.path=='/api/room/join':
            code=str(data.get('code','')).strip(); name=str(data.get('name','')).strip()[:60]
            avatar=str(data.get('avatar','01')).strip()
            if avatar not in AVATARS: avatar='b01'
            card=str(data.get('card','')).strip()
            with LOCK:
                room=ROOMS.get(code)
                if not room: return self.send_json({'ok':False,'error':'room_not_found'},404)
                if room['status']=='finished': return self.send_json({'ok':False,'error':'finished'},400)
                if room['playType']=='teams' and room.get('teamAssignment')=='manual' and room['status']!='lobby':return self.send_json({'ok':False,'error':'team_assignment_closed'},409)
                if room.get('examMode') and room['status']!='lobby':return self.send_json({'ok':False,'error':'exam_started'},409)
                student=platform_store.student_by_card(card,room.get('teacherId','')) if card else None
                if card and not student:return self.send_json({'ok':False,'error':'invalid_card'},403)
                if student:
                    name=student['name'];avatar=student['avatar']
                    if room.get('examMode') and room.get('section') and room['section']!=student['class_name']:
                        return self.send_json({'ok':False,'error':'wrong_class'},403)
                    if room.get('examMode') and platform_store.attempt_count(student['id'],room['quiz'].get('id',''))>=room['maxAttempts']:
                        return self.send_json({'ok':False,'error':'attempt_limit'},403)
                elif room.get('requireCard'):
                    return self.send_json({'ok':False,'error':'card_required'},403)
                allowed=platform_store.avatar_pool(room.get('schoolType','mixed'))
                if avatar not in allowed: avatar=allowed[0]
                if not name:return self.send_json({'ok':False,'error':'name_required'},400)
                # prevent duplicate exact nickname in same room, but allow explicit suffix by student
                if student and any(x.get('studentId')==student['id'] for x in room['players'].values()):return self.send_json({'ok':False,'error':'card_already_joined'},409)
                if any(norm(x['name'])==norm(name) for x in room['players'].values()): return self.send_json({'ok':False,'error':'name_taken'},409)
                team=choose_team(room) if room['playType']=='teams' and room.get('teamAssignment')!='manual' else ''
                pid=rid(); model=''
                total=len(room['quiz']['questions']); order=list(range(total))
                if room.get('variantMode')=='models4':
                    model=['A','B','C','D'][len(room['players'])%4]; order=model_order(code,model,total)
                room['players'][pid]={'id':pid,'name':name,'studentId':student['id'] if student else None,'level':platform_store.level_for_xp(student['xp']) if student else 1,'xp':int(student['xp']) if student else 0,'xpGain':0,'avatar':avatar,'team':team,'model':model,'questionOrder':order,'optionMaps':{},'score':0,'correct':0,'wrong':0,'streak':0,'answers':{},'lastResult':{},'powerups':{'double':True}}
            snapshot_room(room)
            return self.send_json({'ok':True,'playerId':pid,'name':name,'quizTitle':room['quiz'].get('title',''),'team':team,'playType':room['playType'],'model':model,'variantMode':room.get('variantMode','options'),'avatar':avatar,'background':room.get('background','cartoon'),'examMode':room.get('examMode',False),'level':room['players'][pid]['level'],'xp':room['players'][pid]['xp'],'progress':platform_store.xp_progress(room['players'][pid]['xp'])})
        if u.path=='/api/room/control':
            code=str(data.get('code','')); action=data.get('action'); host_token=str(data.get('hostToken',''))
            with LOCK:
                room=ROOMS.get(code)
                if not room: return self.send_json({'ok':False,'error':'room_not_found'},404)
                if not host_token or host_token != room.get('hostToken'): return self.send_json({'ok':False,'error':'host_auth_required'},403)
                if action=='background':
                    new_scene=str(data.get('background') or '')
                    if new_scene not in SCENES:
                        return self.send_json({'ok':False,'error':'invalid_background'},400)
                    room['background']=new_scene
                elif action=='start':
                    if room['status']!='lobby': return self.send_json({'ok':False,'error':'already_started'},409)
                    if room['playType']=='teams' and any(not p.get('team') for p in room['players'].values()):return self.send_json({'ok':False,'error':'team_missing'},409)
                    room['status']='question'; room['index']=0; room['startedAt']=now_ms();room['roundDurationMs']=round_duration_ms(room)
                elif action=='shuffle-teams':
                    if room['status']!='lobby' or room['playType']!='teams':return self.send_json({'ok':False,'error':'not_in_lobby'},409)
                    players=list(room['players'].values());random.shuffle(players)
                    names=list(room['teamNames']);random.shuffle(names)
                    for i,player in enumerate(players):player['team']=names[i%len(names)]
                elif action=='reveal':
                    if room['status']=='question': finish_round(room,'manual')
                elif action=='next':
                    if room['status']=='lobby':
                        if room['playType']=='teams' and any(not p.get('team') for p in room['players'].values()):return self.send_json({'ok':False,'error':'team_missing'},409)
                        room['status']='question';room['index']=0;room['startedAt']=now_ms();room['roundDurationMs']=round_duration_ms(room)
                    elif room['status']=='question':
                        finish_round(room,'manual')
                    elif room['status']=='results':next_round(room)
                elif action=='skip':
                    # Immediately advance, without waiting for the timer or any student.
                    if room['status'] in ('question','results'): next_round(room)
                    else:return self.send_json({'ok':False,'error':'not_playing'},409)
                elif action=='end':
                    if room['status']=='question':finish_round(room,'ended')
                    room['status']='finished'; room['index']=len(room['quiz']['questions']);room['finishedAt']=now_ms()
                    persist_finished_room(room)
                else: return self.send_json({'ok':False,'error':'bad_action'},400)
                snapshot_room(room)
            return self.send_json({'ok':True})
        if u.path=='/api/room/answer':
            code=str(data.get('code','')); pid=str(data.get('playerId','')); idx=int(data.get('index',-1)); ans=data.get('answer'); elapsed=max(0,int(data.get('elapsedMs',0))); power=data.get('power','')
            with LOCK:
                room=ROOMS.get(code); p=room and room['players'].get(pid)
                if not room or not p: return self.send_json({'ok':False,'error':'not_found'},404)
                maybe_end_round(room)
                if room['status']!='question' or room['index']!=idx: return self.send_json({'ok':False,'error':'question_changed'},409)
                key=str(idx)
                if key in p['answers']:
                    result=({'index':idx,'correct':None,'earned':0,'streak':0} if room.get('examMode') else (dict(p['lastResult'],correct=None) if not room.get('showFeedback',True) else p['lastResult']))
                    return self.send_json({'ok':True,'duplicate':True,'result':result,'score':0 if room.get('examMode') else p['score']})
                # The server clock is authoritative; the client-provided elapsedMs can be forged.
                elapsed=max(0,now_ms()-room.get('startedAt',now_ms()))
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
                    earned=round(points*mult); p['correct']+=1
                elif correct is False:
                    p['wrong']+=1; p['streak']=0
                bonus=0
                if room.get('cooperative') and room['playType']=='teams' and correct is True:
                    bonus=max(0,earned-round(earned*0.4));earned-=bonus
                p['score']+=earned
                p['answers'][key]={'correct':correct,'earned':earned,'pendingTeamBonus':bonus,'answer':ans,'elapsedMs':elapsed,'power':used_power,'questionIndex':qidx}
                p['lastResult']={'index':idx,'correct':correct,'earned':earned,'streak':p['streak'],'power':used_power}
                maybe_end_round(room)
                shown=({'index':idx,'correct':None,'earned':0,'streak':0} if room.get('examMode') else (dict(p['lastResult'],correct=None) if not room.get('showFeedback',True) else p['lastResult']))
                score=p['score'] if not room.get('examMode') else 0
                snapshot_room(room)
            return self.send_json({'ok':True,'result':shown,'score':score,'powerups':p['powerups']})
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
    if IS_CLOUD and not platform_store.DATABASE_URL and os.getenv('QUIZNOVA_ALLOW_EPHEMERAL')!='yes':
        print('QuizNova V10: DATABASE_URL is required for cloud mode. Refusing ephemeral account storage.',flush=True)
        sys.exit(78)
    os.chdir(ROOT)
    ip=local_ip()
    ROOMS.update(platform_store.recover_active_rooms())
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
