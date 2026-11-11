"""READ-ONLY post-release health, public assets, and admin isolation smoke for official production.
No user registration, no game sessions, no writes to production data.
"""
import json
import urllib.error
import urllib.request

BASE='https://quiznova-arena-online.onrender.com'
def get(path):
    request=urllib.request.Request(BASE+path,headers={'Accept':'application/json, text/html;q=0.9',
                         'User-Agent':'TeachGame-Release-ReadOnlySmoke/13.1'})
    try:
        with urllib.request.urlopen(request,timeout=60) as response:
            return response.status,response.headers.get('Content-Type',''),response.read(300000)
    except urllib.error.HTTPError as e:
        return e.code,e.headers.get('Content-Type',''),e.read(300000)

for path in ('/','/admin.html','/student.html','/studio.html','/admin-v1.js','/admin-v1.css'):
    code,typ,data=get(path)
    assert code==200,(path,code,data[:160])
    assert len(data)>500,(path,len(data))
    if path=='/admin.html':
        assert b'TeachGame CONTROL CENTER' in data
print('PUBLIC FILES: PASS (home, owner, student, studio, admin JS/CSS)')

status,_,raw=get('/api/health')
assert status==200,(status,raw[:200])
health=json.loads(raw)
assert health.get('ok') is True,health
assert health.get('database') in ('ready','postgres','ok',None),health
print('APP HEALTH: PASS; version:',health.get('version'))

status,_,raw=get('/api/admin/status')
assert status==200,(status,raw[:200])
state=json.loads(raw)
assert state.get('ok') is True,state
assert state.get('hasOwner') in (True,False)
print('OWNER SETUP STATUS: PASS; hasOwner:',state['hasOwner'],'setupAvailable:',state.get('setupAvailable'))

for path in ('/api/admin/me','/api/admin/summary','/api/admin/insights',
             '/api/admin/teachers','/api/admin/students','/api/admin/sessions',
             '/api/admin/schools','/api/admin/audit',
             '/api/admin/teacher/detail?id=bad','/api/admin/student/detail?id=bad'):
    status,_,raw=get(path)
    assert status==401,(path,status,raw[:200])
    payload=json.loads(raw)
    assert payload.get('ok') is False
    assert b'password_hash' not in raw and b'card_token' not in raw
print('ADMIN SECURITY: PASS; all sensitive endpoints deny anonymous HTTP')
print('POST-RELEASE READ-ONLY PRODUCTION SMOKE: PASS')
