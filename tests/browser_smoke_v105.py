"""Headless browser smoke test covering desktop, mobile, student cards and one-tap scoring."""
import json,os,sys,tempfile,threading,time,urllib.request,urllib.error,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright

temp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(temp.name)/'browser.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store
store.init()
import server
site=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
thread=threading.Thread(target=site.serve_forever,daemon=True)
thread.start()
base='http://127.0.0.1:'+str(site.server_port)
account=store.create_teacher('webqa'+uuid.uuid4().hex+'@school.example','SafePassword123!', 'Test Teacher','مدرسة بنين','مهارات رقمية','boys')
token=account['token']
teacher_id=account['teacher']['id']
card=store.add_students(teacher_id,[{'name':'أحمد تجربة','className':'التاسع أ','avatar':'n03'}])[0]
dest=Path('browser-qa-artifacts')
dest.mkdir(exist_ok=True)
def api(path,payload=None,auth=False):
    headers={'Content-Type':'application/json'}
    if auth:headers['Authorization']='Bearer '+token
    request=urllib.request.Request(base+path,headers=headers,method='POST' if payload is not None else 'GET',
        data=json.dumps(payload,ensure_ascii=False).encode() if payload is not None else None)
    with urllib.request.urlopen(request,timeout=15) as response:return json.loads(response.read())

def make_room(show_feedback):
    return api('/api/room/start',{'quiz':{
       'id':uuid.uuid4().hex,'title':'اختبار المتصفح النهائي',
       'subject':'مهارات رقمية','questions':[{'id':'q1','type':'single','text':'ما هو ناتج جمع اثنين واثنين؟',
         'options':['4','5','7','9'],'correct':[0],'time':80,'points':1000}]},
       'gameMode':'speed','variantMode':'same','playType':'individual',
       'showFeedback':show_feedback,'powerups':False},auth=True)

def check_colored_input(page):
    box=page.locator('#quizTitle')
    box.wait_for(state='visible',timeout=30000)
    val=box.evaluate("""el=>{
      const x=getComputedStyle(el);return {color:x.color,background:x.backgroundColor,font:x.fontSize}
    }""")
    assert 'rgb(12, 37, 72)' in val['color'],val
    assert 'rgb(247, 251, 255)' in val['background'],val

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
    # Real browser session, not a static CSS inspection.
    context=browser.new_context(viewport={'width':1366,'height':768},device_scale_factor=1)
    page=context.new_page()
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.add_init_script(f"localStorage.setItem('qn9_teacher_token',{json.dumps(token)});")
    page.goto(base+'/studio.html#builder',wait_until='domcontentloaded',timeout=30000)
    check_colored_input(page)
    page.locator('#quizTitle').fill('تجربة وضوح الخطوط')
    page.screenshot(path=str(dest/'studio-desktop.png'),full_page=True)
    assert not errors,errors
    context.close()

    for width,height,mobile in ((1366,768,False),(390,844,True)):
        context=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1,is_mobile=mobile,has_touch=mobile)
        page=context.new_page()
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(base+'/student.html',wait_until='domcontentloaded',timeout=30000)
        page.locator('#cardCode').fill(card['cardCode'])
        page.locator('#showCardProfile').click()
        page.locator('#cardProfile').wait_for(state='visible',timeout=12000)
        assert 'أحمد تجربة' in page.locator('#cardProfile').inner_text()
        room=make_room(False)
        page.locator('#roomCode').fill(room['code'])
        page.locator('#joinBtn').click()
        page.locator('#gameView .lobby-card').wait_for(state='visible',timeout=12000)
        guest=api('/api/room/join',{'code':room['code'],'name':'زائر اختبار','avatar':'n02'})
        api('/api/room/control',{'code':room['code'],'hostToken':room['hostToken'],'action':'start'})
        page.locator('#gameView .question-card .answer').first.wait_for(state='visible',timeout=12000)
        dims=page.evaluate("""()=>{
          const q=document.querySelector('#gameView .question-card');
          return {height:innerHeight,bottom:q.getBoundingClientRect().bottom,
            overflow:getComputedStyle(document.body).overflow,options:document.querySelectorAll('.answers .answer').length}
        }""")
        assert dims['options']==4,dims
        assert dims['overflow']=='hidden',dims
        assert dims['bottom']<=dims['height']+5,dims
        page.screenshot(path=str(dest/('question-mobile.png' if mobile else 'question-desktop.png')))
        # A transient API failure must not trap the student with disabled options.
        attempts={'count':0}
        def answer_with_one_failure(route):
            attempts['count']+=1
            if attempts['count']==1:
                route.fulfill(status=503,content_type='application/json',body='{"ok":false,"error":"temporary"}')
            else:
                route.continue_()
        page.route('**/api/room/answer',answer_with_one_failure)
        page.locator('#gameView .question-card .answer').first.click()
        page.locator('#feedback .wrong').wait_for(state='visible',timeout=4500)
        assert page.locator('#gameView .question-card .answer').first.is_enabled()
        page.locator('#gameView .question-card .answer').first.click()
        page.locator('#qnAnswerWait').wait_for(state='visible',timeout=4500)
        wait=page.locator('#qnAnswerWait').inner_text()
        assert 'تم تسجيل' in wait and 'إجابة صحيحة' not in wait,wait
        assert 'نقطة' not in wait,wait  # Teacher disabled immediate feedback: keep score hidden
        page.screenshot(path=str(dest/('waiting-mobile.png' if mobile else 'waiting-desktop.png')))
        # Other student can still answer; teacher's countdown is not a blocker.
        api('/api/room/answer',{'code':room['code'],'playerId':guest['playerId'],'index':0,'answer':1})
        api('/api/room/control',{'code':room['code'],'hostToken':room['hostToken'],'action':'next'})
        page.locator('.qn-xp-final').wait_for(state='visible',timeout=12000)
        assert 'XP' in page.locator('.qn-xp-final').inner_text()
        assert not errors,errors
        context.close()

    # The teacher's feedback toggle must really affect the actual student screen.
    context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
    page=context.new_page()
    room=make_room(True)
    page.goto(base+'/student.html?code='+room['code'])
    page.locator('#playerName').fill('زائر جديد')
    page.locator('#joinBtn').click()
    page.locator('.lobby-card').wait_for(state='visible',timeout=12000)
    guest=api('/api/room/join',{'code':room['code'],'name':'زائر ثان','avatar':'n01'})
    api('/api/room/control',{'code':room['code'],'hostToken':room['hostToken'],'action':'start'})
    page.locator('.question-card .answer').first.wait_for(state='visible',timeout=12000)
    page.locator('.question-card .answer').first.click()
    page.locator('#qnAnswerWait').wait_for(state='visible',timeout=4500)
    assert 'إجابة صحيحة' in page.locator('#qnAnswerWait').inner_text()
    context.close()
    browser.close()

site.shutdown();site.server_close()
print('PASS: desktop and mobile, teacher font contrast, card code profile, 4 options fitting screen, instant answer, waiting without correctness, XP and teacher feedback enabled.')
