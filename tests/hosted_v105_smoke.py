"""Live HTTP smoke test on the isolated ephemeral Render V10.5 preview.

Creates ONLY synthetic teacher/students. Must never run against real staging DB.
"""
import json, os, secrets, time, urllib.request, urllib.error, urllib.parse
BASE=os.getenv('QUIZNOVA_QA_URL','https://quiznova-arena-v105-qa.onrender.com').rstrip('/')
assert BASE=='https://quiznova-arena-v105-qa.onrender.com','Refusing to test any non-QA service'
def req(path,data=None,token=None,method=None):
    hd={'Accept':'application/json'}
    if data is not None:hd['Content-Type']='application/json'
    if token:hd['Authorization']='Bearer '+token
    request=urllib.request.Request(BASE+path,headers=hd,data=json.dumps(data,ensure_ascii=False).encode() if data is not None else None,method=method or ('POST' if data is not None else 'GET'))
    try:
        with urllib.request.urlopen(request,timeout=60) as response:
            raw=response.read(3000000);return response.status,json.loads(raw) if raw and response.headers.get('Content-Type','').startswith('application/json') else {'bytes':len(raw)}
    except urllib.error.HTTPError as e:
        raw=e.read(500000)
        try:payload=json.loads(raw)
        except Exception:payload={'message':str(e)}
        return e.code,payload
for attempt in range(15):
    try:
        status,h=req('/api/health')
        if status==200 and h.get('ok'):break
    except Exception:pass
    time.sleep(5)
else:raise AssertionError('QA website did not become healthy')
assert h.get('version','').startswith('10.5'),h
print('Health:',h.get('version'),h.get('storage'),h.get('database'))

for path in ('/','/student.html','/studio.html','/v107-prelaunch.css','/assets/avatars3d/n01.webp','/assets/backgrounds/quiznova-learning.webp'):
    status,body=req(path)
    assert status==200,(path,status)
    assert body['bytes']>1000,(path,body)
print('Homepage, student, studio, styles and image files: HTTP 200')

identity=secrets.token_hex(8)
teacher='qa'+identity+'@example.org'
password='TeacherTest#'+identity
status,auth=req('/api/auth/register',{'email':teacher,'password':password,'name':'Release QA Teacher','school':'QA school for boys','subject':'Digital Skills','schoolType':'boys'})
assert status==200 and auth.get('ok'),(status,auth)
token=auth['token']
names=['QA Student A '+identity,'QA Student B '+identity]
status,created=req('/api/teacher/students',{'students':[{'name':n,'className':'QA-9','avatar':'n01'} for n in names]},token)
assert status==200 and created.get('ok'),(status,created)
status,listed=req('/api/teacher/students',token=token)
assert status==200 and len(listed.get('students',[]))>=2
students=[next(x for x in listed['students'] if x['name']==name) for name in names]
assert all(s.get('cardCode','').startswith('QNA-') for s in students)
assert students[0]['cardCode']!=students[1]['cardCode']
print('Teacher account, two student cards, card code uniqueness: OK')

q={'id':'qa-q'+identity,'title':'QA Instant Choice','questions':[{'id':'q1','type':'single','text':'2 + 2','options':['4','7','5','8'],'correct':[0],'time':60,'points':1000}]}
status,room=req('/api/room/start',{'quiz':q,'gameMode':'speed','playType':'individual','variantMode':'same','showFeedback':False,'requireCard':True},token)
assert status==200 and room.get('ok'),(status,room)
code=room['code']
ids=[]
for student in students:
    st,res=req('/api/card/resolve?code='+code+'&card='+urllib.parse.quote(student['cardCode']))
    assert st==200 and res.get('name')==student['name'],(st,res)
    st,joined=req('/api/room/join',{'code':code,'name':'','avatar':'n01','card':student['cardCode']})
    assert st==200 and joined.get('ok'),(st,joined)
    ids.append(joined['playerId'])
st,invalid=req('/api/room/join',{'code':code,'name':'Fake Student','card':'QNA-INVALID-CODE'})
assert st==403 and invalid.get('error')=='invalid_card'
st,started=req('/api/room/control',{'code':code,'hostToken':room['hostToken'],'action':'start'})
assert st==200 and started.get('ok')
st,answer=req('/api/room/answer',{'code':code,'playerId':ids[0],'index':0,'answer':0})
assert st==200 and answer['result']['correct'] is None,(st,answer)
st,state=req('/api/room/state?code='+code+'&player='+ids[0])
assert st==200 and state['room']['status']=='question' and state['room']['answeredCurrent']
st,answer2=req('/api/room/answer',{'code':code,'playerId':ids[1],'index':0,'answer':2})
assert st==200 and answer2.get('ok'),(st,answer2)
st,state=req('/api/room/state?code='+code+'&player='+ids[0])
assert state['room']['status']=='results'
assert state['room']['review'] is None
print('Card code login, instant answer without reveal, all-answered finish: OK')

st,_=req('/api/room/control',{'code':code,'hostToken':room['hostToken'],'action':'next'})
assert st==200
st,record=req('/api/teacher/students',token=token)
updated=next(x for x in record['students'] if x['name']==names[0])
assert updated['xp']>0 and updated['played']==1,updated
st,finished=req('/api/room/state?code='+code+'&player='+ids[0])
assert finished['room']['status']=='finished'
assert finished['room']['xpGain']>0 and finished['room']['level']==updated['level']
st,record2=req('/api/teacher/students',token=token)
after=next(x for x in record2['students'] if x['name']==names[0])
assert after['xp']==updated['xp'] and after['played']==1
print('Durable XP, level and double-award prevention: OK')

st,room2=req('/api/room/start',{'quiz':q,'gameMode':'speed','playType':'individual','variantMode':'same','showFeedback':True},token)
assert st==200 and room2.get('ok'),(st,room2)
joined=[]
for name in ('QA One '+identity,'QA Two '+identity):
    st,j=req('/api/room/join',{'code':room2['code'],'name':name,'avatar':'n01'})
    assert st==200 and j.get('ok');joined.append(j)
st,_=req('/api/room/control',{'code':room2['code'],'hostToken':room2['hostToken'],'action':'start'})
assert st==200
st,answer=req('/api/room/answer',{'code':room2['code'],'playerId':joined[0]['playerId'],'index':0,'answer':0})
assert st==200 and answer['result']['correct'] is True and answer['result']['earned']>0,(st,answer)
print('Teacher-enabled correctness and instant scoring: OK')
print('PASS — V10.5 hosted QA smoke test succeeded.')
