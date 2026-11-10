"""V12.8 real Chromium acceptance: filtered card tests and fullscreen live/solo questions."""
import json,os,sys,tempfile,threading,urllib.request,uuid,time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
TMP=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(TMP.name)/'v128-browser.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store
import server

teacher=store.create_teacher('v128-browser@example.org','TeacherV128SecurePassword!',
 'معلم المهارات الرقمية','مدرسة تجريبية للبنين','المهارات الرقمية','boys')
tid=teacher['teacher']['id']
students=store.add_students(tid,[
 {'name':'طالب تاسع أ','className':'التاسع أ','avatar':'m01'},
 {'name':'طالب تاسع ب','className':'التاسع ب','avatar':'m02'}
])
question={'id':'long-but-readable','type':'single',
 'text':'أي من المكونات التالية يستخدم لتخزين البيانات والتعليمات بشكل مؤقت أثناء تشغيل البرامج على الحاسوب؟',
 'options':['ذاكرة الوصول العشوائي RAM','وحدة المعالجة المركزية CPU',
            'وحدة التخزين الداخلية SSD','شاشة العرض ولوحة المفاتيح'],
 'correct':[0],'time':120,'points':1000}
quizzes=[
 {'id':'all-ninth','title':'اختبار التاسع لجميع الشعب','subject':'المهارات الرقمية','grade':'التاسع',
  'section':'','settings':{'publishedSolo':True,'soloMaxAttempts':10},'questions':[question]},
 {'id':'ninth-a','title':'تحدي التاسع أ','subject':'المهارات الرقمية','grade':'التاسع',
  'section':'أ','settings':{'publishedSolo':True,'soloMaxAttempts':10},'questions':[question]},
 {'id':'ninth-b','title':'تحدي التاسع ب','subject':'المهارات الرقمية','grade':'التاسع',
  'section':'ب','settings':{'publishedSolo':True,'soloMaxAttempts':10},'questions':[question]},
 {'id':'eighth','title':'اختبار الصف الثامن','subject':'المهارات الرقمية','grade':'الثامن',
  'section':'','settings':{'publishedSolo':True,'soloMaxAttempts':10},'questions':[question]},
 {'id':'secret','title':'اختبار غير منشور','subject':'المهارات الرقمية','grade':'التاسع',
  'section':'','settings':{'publishedSolo':False},'questions':[question]}
]
store.save_snapshot(tid,{'quizzes':quizzes})
http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(http.server_port)
screens=Path('browser-qa-artifacts');screens.mkdir(exist_ok=True)

def request(path,data,token=None):
 headers={'Content-Type':'application/json'}
 if token:headers['Authorization']='Bearer '+token
 req=urllib.request.Request(base+path,
  data=json.dumps(data,ensure_ascii=False).encode('utf8'),headers=headers)
 with urllib.request.urlopen(req,timeout=18) as r:return json.load(r)

def check(condition,message):
 if not condition:raise AssertionError(message)

def fit(page,width,height,kind):
 page.locator('body[data-bo-question="'+kind+'"]').wait_for(timeout=16000)
 if kind=='live':
  card=page.locator('#gameView .question-card')
  options=page.locator('#gameView .answer')
  header=page.locator('#gameView .game-top')
 else:
  card=page.locator('#soloView .bo-solo-question')
  options=page.locator('#soloView .bo-solo-choice')
  header=page.locator('#soloView .bo-solo-progress-header')
 check(card.is_visible(),'Question not visible: '+kind)
 check(options.count()==4,'Not all four answers visible '+kind)
 check(header.is_visible(),'Question HUD hidden '+kind)
 geometry=page.evaluate("""kind=>{
  let card=document.querySelector(kind==='live'?'#gameView .question-card':'#soloView .bo-solo-question');
  let items=[card,card.querySelector('h2'),...(kind==='live'?card.querySelectorAll('.answer'):card.querySelectorAll('.bo-solo-choice'))];
  return {viewport:[innerWidth,innerHeight],y:scrollY,root:document.documentElement.scrollWidth,
   items:items.map(e=>{const r=e.getBoundingClientRect();return [r.left,r.top,r.right,r.bottom,e.scrollHeight,e.clientHeight]})}
 }""",kind)
 check(geometry['y']==0,'Question needs page scroll '+str(geometry))
 check(geometry['root']<=width+3,'Horizontal overflow '+str(geometry))
 for index,item in enumerate(geometry['items']):
  left,top,right,bottom=item[:4]
  check(left>=-3 and top>=-3 and right<=width+3 and bottom<=height+3,
        'Question or option outside screen '+str((width,height,kind,index,item)))
  check((right-left)>16 and (bottom-top)>16,
        'Option or question collapsed '+str((width,height,kind,index,item)))
 # Option labels must also fit normally within each button.
 for index,item in enumerate(geometry['items'][2:],start=2):
  if height>=700:
   check(item[4]<=item[5]+3,'Option text clipped at '+str((width,height,kind,index,item)))
 return geometry

try:
 with sync_playwright() as playwright:
  browser=playwright.chromium.launch(headless=True,args=['--no-sandbox'])
  for width,height in [(320,568),(360,740),(390,844),(430,932),
                       (600,800),(768,1024),(1024,768),(1366,820)]:
   mobile=width<=600
   student=students[0] if width%2==0 else students[1]
   expected='تحدي التاسع أ' if student==students[0] else 'تحدي التاسع ب'
   unwanted='تحدي التاسع ب' if student==students[0] else 'تحدي التاسع أ'
   ctx=browser.new_context(viewport={'width':width,'height':height},
                           is_mobile=mobile,has_touch=mobile)
   page=ctx.new_page();errors=[]
   page.on('pageerror',lambda error:errors.append(str(error)))
   page.goto(base+'/student.html?mode=card',wait_until='domcontentloaded')
   page.locator('#cardCode').fill(student['cardCode'])
   page.locator('#showCardProfile').click()
   page.locator('#boCardQuizzes .bo-card-test-item').first.wait_for(timeout=18000)
   titles=page.locator('#boCardQuizzes').inner_text()
   check(expected in titles,(width,'own section not visible',titles))
   check('اختبار التاسع لجميع الشعب' in titles,(width,'grade-wide quiz absent',titles))
   check(unwanted not in titles,(width,'other section disclosed',titles))
   check('اختبار الصف الثامن' not in titles,(width,'other grade disclosed',titles))
   check('اختبار غير منشور' not in titles,(width,'private quiz disclosed',titles))
   check(page.locator('#boCardQuizzes .bo-card-test-item').count()==2,'Card must show only two quizzes')
   page.locator('#boCardQuizzes button').first.click()
   page.locator('#boSoloForm').wait_for(state='visible',timeout=18000)
   check(page.locator('#soloView').is_visible(),'Card button did not switch to solo mode')
   fit(page,width,height,'solo')
   if width in (320,390,768,1366):
    page.screenshot(path=str(screens/('v128-solo-'+str(width)+'.png')),full_page=True)
   page.locator('.bo-solo-choice').filter(has_text='ذاكرة الوصول').click()
   page.locator('#boSoloSubmit').click()
   page.locator('.bo-solo-finish').wait_for(timeout=17000)
   check(page.locator('body').get_attribute('data-bo-question')!='solo',
         'One-screen mode must clear after completion')
   check(not errors,'Solo JS errors '+str((width,errors)))
   ctx.close()
   # A separate real-time room validates the live classroom question UI.
   room=request('/api/room/start',{'quiz':{
      'id':'fit-room-'+str(width),'title':'درس المهارات الرقمية',
      'questions':[question]},'section':'التاسع أ','powerups':False},teacher['token'])
   live_ctx=browser.new_context(viewport={'width':width,'height':height},
                                 is_mobile=mobile,has_touch=mobile)
   live=live_ctx.new_page();live_errors=[]
   live.on('pageerror',lambda error:live_errors.append(str(error)))
   live.goto(base+'/student.html?code='+room['code'],wait_until='domcontentloaded')
   live.locator('#playerName').fill('زائر ملء الشاشة '+str(width))
   live.locator('#joinBtn').click()
   live.locator('.lobby-card').wait_for(state='visible',timeout=15000)
   request('/api/room/control',{'code':room['code'],'hostToken':room['hostToken'],'action':'start'})
   live.locator('#gameView .question-card .answer').first.wait_for(timeout=17000)
   fit(live,width,height,'live')
   if width in (320,390,768,1366):
    live.screenshot(path=str(screens/('v128-live-'+str(width)+'.png')),full_page=True)
   live.locator('.answer').first.click()
   live.locator('.qn-answer-wait').wait_for(state='visible',timeout=17000)
   live.wait_for_function("document.body.dataset.boQuestion!=='live'",timeout=3500)
   check(live.locator('body').get_attribute('data-bo-question')!='live',
         'One-screen layout must reset after sending answer')
   check(not live_errors,'Live JS errors '+str((width,live_errors)))
   live_ctx.close()
  browser.close()
 print('PASS: grade+section-restricted card quiz lists, one-tap solo start, no other grade leaks; fullscreen live and solo question/2x2 answers at 8 responsive sizes with no page scrolling.')
finally:
 http.shutdown();http.server_close();TMP.cleanup()
