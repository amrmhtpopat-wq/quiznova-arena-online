"""BOOYAHJO 12.3 native mobile/tablet acceptance: no clipped pages or desktop regression."""
import json,os,sys,tempfile,threading,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
temp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(temp.name)/'mobile-v123.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store
import server

teacher=store.create_teacher('v123-mobile@example.org','TeacherV123StrongPassword!',
 'المعلم التجريبي','مدرسة البنين','المهارات الرقمية','boys')
token=teacher['token'];tid=teacher['teacher']['id']
store.add_students(tid,[{'name':'طالب اختبار الهواتف','className':'الصف التاسع أ','avatar':'n01'}])
http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(http.server_port)
out=Path('browser-qa-artifacts');out.mkdir(exist_ok=True)
quiz={'id':'mobile-test-123','title':'التحدي المباشر على الهاتف','subject':'المهارات الرقمية',
 'questions':[{'id':'one','type':'single','text':'ما دور ذاكرة RAM في الحاسوب؟',
 'options':['تخزين مؤقت','طباعة','عرض الصورة','تشغيل سماعات'],'correct':[0],'time':35,'points':1000}]}
def post(path,body):
    request=urllib.request.Request(base+path,data=json.dumps(body,ensure_ascii=False).encode(),
        headers={'Content-Type':'application/json','Authorization':'Bearer '+token})
    with urllib.request.urlopen(request,timeout=20) as resp:return json.load(resp)
room=post('/api/room/start',{'quiz':quiz,'background':'cine-stars'})
def check(condition,message):
    if not condition:raise AssertionError(message)
def metrics(page):
    return page.evaluate("""() => ({
       width:innerWidth,
       doc:document.documentElement.scrollWidth,
       body:document.body.scrollWidth,
       boxes:[...document.querySelectorAll('main,.workspace,.topbar,.sidebar,#studentWelcome,.bo-entry-options,.bo-entry-option,.join-card,#avatarPicker,#view-dashboard,.bo-student-modes,#liveHost,.room-code-card,#roomQr')].filter(el=>el.getClientRects().length).map(el=>{
         const r=el.getBoundingClientRect();return {name:el.id||el.className||el.tagName,
         left:Math.round(r.left),right:Math.round(r.right),width:Math.round(r.width)}
       }).filter(x=>x.width>3&&(x.left < -3||x.right > innerWidth+3)).slice(0,12)
    })""")
def no_body_overflow(page,tag):
    m=metrics(page)
    check(m['doc']<=m['width']+3 and m['body']<=m['width']+3,
          'horizontal overflow '+tag+': '+str(m))
def inside(page,selector,tag):
    m=page.locator(selector).first.evaluate("""el=>{
      const r=el.getBoundingClientRect();return {left:r.left,right:r.right,width:r.width,
        viewport:innerWidth,display:getComputedStyle(el).display,visibility:getComputedStyle(el).visibility}
    }""")
    check(m['width']>12 and m['left']>=-3 and m['right']<=m['viewport']+3,
          'clipped '+tag+' '+selector+': '+str(m))
def init_studio(page):
    page.add_init_script("localStorage.setItem('qn9_teacher_token',"+json.dumps(token)+");")
    page.add_init_script("sessionStorage.setItem('qn9_live_"+tid+"',"+json.dumps(json.dumps({
      'code':room['code'],'hostToken':room['hostToken'],'stageToken':room['stageToken'],'quizId':quiz['id']
    })) + ");")
with sync_playwright() as playwright:
    browser=playwright.chromium.launch(headless=True,args=['--no-sandbox'])
    views=[(320,700,True),(360,740,True),(390,844,True),(430,932,True),
           (600,900,True),(768,1024,True),(820,1180,True),(1024,768,False)]
    for width,height,mobile in views:
        context=browser.new_context(viewport={'width':width,'height':height},
            device_scale_factor=1,is_mobile=mobile,has_touch=mobile)
        page=context.new_page()
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        # Public mobile entry must not be a reduced desktop layout.
        page.goto(base+'/',wait_until='domcontentloaded',timeout=25000)
        page.locator('#studentWelcome').wait_for(state='visible',timeout=12000)
        check(page.locator('.bo-entry-option').count()==3,'public choices missing')
        no_body_overflow(page,f'landing {width}')
        for selector in ['#studentWelcome','.bo-entry-option','.bo-entry-head']:
            inside(page,selector,f'landing {width}')
        if width in (320,390,820):page.screenshot(path=str(out/f'v123-home-{width}.png'),full_page=True)
        # Real teacher sign-in and portal with all navigation destinations.
        page.goto(base+'/?teacher=1',wait_until='domcontentloaded')
        page.locator('#authWall').wait_for(state='visible',timeout=12000)
        inside(page,'.auth-card',f'teacher login {width}')
        no_body_overflow(page,f'teacher login {width}')
        page.locator('#email').fill('v123-mobile@example.org')
        page.locator('#password').fill('TeacherV123StrongPassword!')
        page.locator('#authSubmit').click()
        page.locator('#workspace').wait_for(state='visible',timeout=12000)
        no_body_overflow(page,f'teacher portal {width}')
        inside(page,'.workspace .main',f'workspace {width}')
        check(page.locator('#logout').is_visible(),'logout hidden on teacher portal')
        check(page.locator('.sidebar nav .nav').count()>=6,'teacher tabs missing')
        if width<=768:
            check(page.locator('.sidebar nav').evaluate("el=>getComputedStyle(el).overflowX")=='auto',
                  'teacher tabs should be horizontally scrollable on phone')
        page.locator('button.nav[data-panel="students"]').click()
        page.locator('#studentsBoard .bo-class-folder').first.wait_for(timeout=13000)
        no_body_overflow(page,f'student cards {width}')
        inside(page,'#studentsBoard .bo-class-folder',f'cards {width}')
        if width in (320,390):page.screenshot(path=str(out/f'v123-teacher-{width}.png'),full_page=True)
        # Authenticated studio with a touch menu, create quiz and live QR.
        init_studio(page)
        page.goto(base+'/studio.html#dashboard',wait_until='domcontentloaded')
        page.locator('#view-dashboard.active').wait_for(state='visible',timeout=18000)
        no_body_overflow(page,f'studio {width}')
        inside(page,'.main',f'studio main {width}')
        page.locator('#menuBtn').wait_for(state='visible',timeout=6000)
        page.locator('#menuBtn').click()
        page.wait_for_function("""()=>{
          const el=document.querySelector('#sidebar'),box=el.getBoundingClientRect();
          return el.classList.contains('open') && box.left>=-3 && box.right<=innerWidth+3;
        }""",timeout=5000)
        inside(page,'#sidebar',f'mobile menu {width}')
        page.locator('#mobileCloseNav').click()
        check(page.locator('#sidebar').evaluate("el=>!el.classList.contains('open')"),
              'studio menu does not close')
        page.goto(base+'/studio.html#live',wait_until='domcontentloaded')
        page.locator('#roomQr').wait_for(state='visible',timeout=25000)
        page.wait_for_function("()=>document.getElementById('roomQr').naturalWidth>0",timeout=14000)
        no_body_overflow(page,f'live room {width}')
        inside(page,'.room-code-card',f'live room {width}')
        inside(page,'#roomQr',f'QR {width}')
        inside(page,'.room-code',f'PIN {width}')
        check(page.locator('.room-code').first.inner_text().strip()==room['code'],
              f'room PIN changed at {width}')
        if width in (320,390,820):page.screenshot(path=str(out/f'v123-live-{width}.png'),full_page=True)
        # Student choice of all avatars remains visible, every field fits, and solo tab works.
        page.goto(base+'/student.html?mode=live',wait_until='domcontentloaded')
        page.locator('#avatarPicker .avatar-choice').first.wait_for(timeout=12000)
        check(page.locator('#avatarPicker .avatar-choice').count()==31,
              'boys avatar options missing at '+str(width))
        no_body_overflow(page,f'student join {width}')
        inside(page,'.join-card',f'student join {width}')
        inside(page,'#roomCode',f'PIN field {width}')
        inside(page,'#joinBtn',f'join button {width}')
        page.locator('.bo-student-modes button[data-student-mode="solo"]').click()
        page.locator('#soloView').wait_for(state='visible',timeout=9000)
        no_body_overflow(page,f'student solo {width}')
        inside(page,'#soloCardCode',f'solo card input {width}')
        if width in (320,390):page.screenshot(path=str(out/f'v123-student-{width}.png'),full_page=True)
        check(not errors,f'Javascript error on mobile width {width}: {errors}')
        context.close()
    # Verify desktop layout untouched by the new stylesheet.
    desktop=browser.new_context(viewport={'width':1366,'height':820})
    page=desktop.new_page();page.goto(base+'/?teacher=1',wait_until='domcontentloaded')
    page.locator('#authWall').wait_for(state='visible',timeout=10000)
    layout=page.evaluate("""()=>{
       const m=matchMedia('(max-width:1024px)').matches;
       return {mobileRule:m,authColumns:getComputedStyle(document.querySelector('#authWall')).gridTemplateColumns}
    }""")
    check(not layout['mobileRule'] and len(layout['authColumns'].split())>=2,
          'desktop sign-in layout changed: '+str(layout))
    desktop.close();browser.close()
http.shutdown();http.server_close()
print('PASS: mobile phone 320/360/390/430, 600px, tablet 768/820/1024: home, teacher login, nav/logout/cards, studio drawer and live QR, student join/avatars/solo. Desktop 1366 unchanged.')
