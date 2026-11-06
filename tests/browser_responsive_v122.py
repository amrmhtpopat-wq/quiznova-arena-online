"""BOOYAHJO 12.2: verify live host QR/PIN at browser 100% zoom and full school avatar lists."""
import json, os, sys, tempfile, threading, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
TMP=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(TMP.name)/'v122-browser.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store
import server
boy=store.create_teacher('v122-boys@example.org','TestTeacherPasswordV122!',
 'معلم تجريبي','مدرسة بنين','المهارات الرقمية','boys')
girl=store.create_teacher('v122-girls@example.org','TestTeacherPasswordV122!',
 'معلمة تجريبية','مدرسة بنات','المهارات الرقمية','girls')
http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(http.server_port)
screens=Path('browser-qa-artifacts')
screens.mkdir(exist_ok=True)
quiz={'id':'fit-v122','title':'اختبار ضبط العرض',
      'questions':[{'id':'question1','type':'single','text':'ما اسم منصة الألعاب؟',
        'options':['بويا','الاختيار الثاني'],'correct':[0],'time':30,'points':1000}]}

def start_room(user):
    b=json.dumps({'quiz':quiz,'background':'cine-stars'}).encode()
    req=urllib.request.Request(base+'/api/room/start',data=b,headers={
        'Authorization':'Bearer '+user['token'],'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=15) as r:return json.load(r)

def check(value,description):
    if not value:raise AssertionError(description)

room=start_room(boy)
girls_room=start_room(girl)
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
    # Desktop 100% zoom, old 80%-style range, narrow notebook and mobile.
    for width,height,is_mobile in [(1024,768,False),(1280,720,False),(1366,768,False),
                                    (1440,900,False),(1920,1080,False),(390,844,True)]:
        context=browser.new_context(viewport={'width':width,'height':height},
            is_mobile=is_mobile,has_touch=is_mobile,device_scale_factor=1)
        page=context.new_page()
        errors=[]
        page.on('pageerror',lambda err:errors.append(str(err)))
        credentials=json.dumps({'teacherToken':boy['token'],'teacherId':boy['teacher']['id'],'room':room})
        page.add_init_script("""(() => {
          const data = """+credentials+""";
          if (location.pathname === '/studio.html') {
            localStorage.setItem('qn9_teacher_token',data.teacherToken);
            sessionStorage.setItem('qn9_live_'+data.teacherId,
              JSON.stringify({code:data.room.code,hostToken:data.room.hostToken,
                stageToken:data.room.stageToken,quizId:'fit-v122'}));
          }
        })();""")
        page.goto(base+'/studio.html#live',wait_until='domcontentloaded',timeout=30000)
        page.locator('#roomQr').wait_for(state='visible',timeout=25000)
        page.wait_for_function("()=>{let e=document.querySelector('#roomQr');return e&&e.complete&&e.naturalWidth>0;}",timeout=15000)
        page.locator('#liveRoomBackground').wait_for(state='visible',timeout=5000)
        metrics=page.evaluate("""() => {
           const box=selector=>{const e=document.querySelector(selector),r=e.getBoundingClientRect();
             return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height}};
           const card=box('.room-code-card'),qr=box('#roomQr'),pin=box('#liveHost .room-code');
           const code=document.querySelector('#liveHost .room-code');
           return {viewport:innerWidth,scroll:document.documentElement.scrollWidth,
             card,qr,pin,pinText:code.textContent.trim(),
             pinSize:parseFloat(getComputedStyle(code).fontSize),
             qrNatural:document.querySelector('#roomQr').naturalWidth,
             liveColumns:getComputedStyle(document.querySelector('#liveHost .room-shell')).gridTemplateColumns,
             controls:box('.bo-live-scene-control')};
        }""")
        check(metrics['pinText']==room['code'],f'Wrong visible room PIN at {width}: {metrics}')
        check(metrics['qrNatural']>100,f'QR is not rendered at {width}: {metrics}')
        check(metrics['card']['width']>=320,f'Live room card crushed at {width}: {metrics}')
        check(metrics['pinSize']>=32,f'PIN font unreadable at {width}: {metrics}')
        check(metrics['scroll']<=width+3,f'Horizontal overflow at 100% {width}: {metrics}')
        for key in ('qr','pin'):
            x=metrics[key]
            check(x['left']>=metrics['card']['left']-2 and x['right']<=metrics['card']['right']+2,
                f'{key} clipped inside room code panel at {width}: {metrics}')
            check(x['left']>=-2 and x['right']<=width+2,
                f'{key} is outside 100% zoom viewport {width}: {metrics}')
        check(metrics['qr']['width']>=120,f'QR too small at {width}: {metrics}')
        check(metrics['card']['top']<height, f'Room code not initially in viewport at {width}: {metrics}')
        check(not errors,f'Browser JS errors at {width}: {errors}')
        page.screenshot(path=str(screens/f'booyah-v122-100-percent-{width}.png'),full_page=True)
        context.close()
    # Public student entry should show 31 unique boys' characters without inner scroll/clipping.
    context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
    page=context.new_page()
    page.goto(base+'/student.html?mode=live',wait_until='domcontentloaded')
    page.locator('#avatarPicker .avatar-choice').first.wait_for(timeout=12000)
    def avatar_state():
        return page.evaluate("""()=>({ids:[...document.querySelectorAll('#avatarPicker [data-avatar]')].map(x=>x.dataset.avatar),
            overflow:getComputedStyle(document.querySelector('#avatarPicker')).overflowY,
            maxHeight:getComputedStyle(document.querySelector('#avatarPicker')).maxHeight,
            hint:document.querySelector('#avatarPickerCount').textContent})""")
    state=avatar_state()
    check(len(state['ids'])==31,f'Only {len(state["ids"])} of 31 boys characters on entry: {state}')
    check(not any(x.startswith('g') for x in state['ids']),f'Girls unexpectedly shown at boys entry: {state}')
    check(len(state['ids'])==len(set(state['ids'])),f'Duplicate boys character: {state}')
    check(state['overflow']=='visible' and state['maxHeight']=='none',f'Avatar gallery clips content: {state}')
    check('31' in state['hint'],'No visible avatar count')
    check(page.locator('[data-avatar="n01"] .bo-avatar-name').inner_text()=='نشمي','Jordanian mascot renamed')
    expected={'b05':'دومو','b14':'تربو','n03':'مسمارو','b12':'دبدوب'}
    for cid,name in expected.items():
        check(page.locator('[data-avatar="'+cid+'"] .bo-avatar-name').inner_text()==name,
              f'Human-style avatar name was not replaced for {cid}')
    page.locator('#roomCode').fill(room['code'])
    page.wait_for_function("()=>document.querySelector('#avatarPickerCount').textContent.includes('31')",timeout=10000)
    page.wait_for_function("()=>document.querySelector('#joinHint').textContent.includes('مدرسة بنين')",timeout=10000)
    state=avatar_state()
    check(len(state['ids'])==31 and not any(x.startswith('g') for x in state['ids']),
          'Boys room must show all 31 boys characters')
    page.locator('#roomCode').fill(girls_room['code'])
    page.wait_for_function("()=>document.querySelector('#joinHint').textContent.includes('مدرسة بنات')",timeout=10000)
    state=avatar_state()
    check(len(state['ids'])==16 and all(x.startswith('g') for x in state['ids']),
          f'Girls room must preserve separate 16-girl policy: {state}')
    page.screenshot(path=str(screens/'booyah-v122-student-avatars.png'),full_page=True)
    context.close()
    browser.close()
http.shutdown();http.server_close()
print('PASS: QR, PIN and fonts visible at 100% zoom (1024/1280/1366/1440/1920/mobile), all 31 boys avatars, independent girls policy and cartoon names.')
