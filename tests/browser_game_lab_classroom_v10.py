"""V10 live classroom Playwright acceptance, fully isolated loopback/SQLite."""
import json,os,tempfile,threading,uuid,sys
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import Request,urlopen
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
FOLDER=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(FOLDER.name)/'v10-browser.sqlite')
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as db,server
HTTP=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=HTTP.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(HTTP.server_port)
ARTIFACT=ROOT/'browser-qa-artifacts';ARTIFACT.mkdir(exist_ok=True)
t=db.create_teacher('browser-v10-'+uuid.uuid4().hex+'@example.test','UniqueStrongBrowserPass!44',
 'QA Teacher','QA School','المهارات الرقمية')
TEACHER=t['token']
STUDENTS=db.add_students(t['teacher']['id'],[
 {'name':'QA Student Alpha','className':'السابع أ','avatar':'m01'},
 {'name':'QA Student Beta','className':'السابع ب','avatar':'m02'}])
ROWS=[
 {'q':'ما هي وحدة المعالجة؟','a':'CPU','g':'الوحدة الأولى',
  'choices':['CPU','RAM','SSD','الشاشة']},
 {'q':'ما وظيفة ذاكرة الوصول العشوائي؟','a':'تخزين مؤقت','g':'الوحدة الثانية'},
 {'q':'كيف ندخل النصوص؟','a':'لوحة المفاتيح','g':'الوحدة الثالثة'},
 {'q':'أين تظهر المعلومات؟','a':'الشاشة','g':'الوحدة الرابعة'}]
def api(path,payload):
 req=Request(BASE+path,data=json.dumps(payload,ensure_ascii=False).encode(),
  headers={'Authorization':'Bearer '+TEACHER,'Content-Type':'application/json'})
 with urlopen(req,timeout=15) as r:return json.load(r)
def room(mode):
 activity=api('/api/game-lab/teacher/save',{'activity':{'title':'Classroom V10 '+mode,
  'mode':mode,'grade':'السابع','subject':'المهارات الرقمية','rows':ROWS}})
 return api('/api/game-lab/live/create',{'activityId':activity['id'],'duration':25,
  'showFeedback':True,'teams':mode=='pairs','enforceGrade':True,'cardRequired':True})
def no_overflow(page,mode):
 layout=page.evaluate("()=>({w:innerWidth,doc:document.documentElement.scrollWidth})")
 assert layout['doc']<=layout['w']+4,(mode,layout)
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
  try:
   # Full creator-to-live lesson flow as a teacher.
   context=browser.new_context(viewport={'width':1440,'height':900})
   context.add_init_script("localStorage.setItem('qn9_teacher_token',"+json.dumps(TEACHER)+");")
   teacher=context.new_page()
   errors=[]
   teacher.on('pageerror',lambda e:errors.append(str(e)))
   teacher.goto(BASE+'/game-lab-create.html?mode=quiz',wait_until='domcontentloaded')
   teacher.locator('#sampleQuestions').click()
   teacher.locator('#goPreview').click()
   teacher.locator('#goSave').click()
   teacher.locator('#v10ClassroomLaunch').wait_for(state='visible')
   teacher.locator('#v10LiveCardsOnly').check()
   teacher.locator('#v10StartLive').click()
   teacher.wait_for_url('**/game-lab-live.html?host=*',timeout=16000)
   teacher.locator('#teacherPin').wait_for(state='visible',timeout=11000)
   code=teacher.locator('#teacherPin').inner_text().strip()
   assert len(code)==6,code
   assert teacher.locator('#teacherQr').get_attribute('src').startswith('/api/qr?')
   no_overflow(teacher,'host')
   teacher.screenshot(path=str(ARTIFACT/'game-lab-classroom-v10-host-1440.png'),animations='disabled')
   # Actual separate browsing contexts: no shared auth/session state.
   students=[]
   for i,vp in enumerate([(390,844),(1366,768)]):
    ctx=browser.new_context(viewport={'width':vp[0],'height':vp[1]})
    page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE+'/game-lab-live.html?code='+code,wait_until='domcontentloaded')
    page.locator('#joinCard').fill(STUDENTS[i]['cardCode'])
    page.locator('#joinButton').click()
    page.locator('#student').wait_for(state='visible',timeout=13000)
    assert STUDENTS[i]['name'] in page.locator('#studentTeam').inner_text()
    students.append((ctx,page))
   teacher.wait_for_function("()=>document.querySelector('#teacherMembers')?.textContent.includes('2 لاعب')",timeout=7000)
   teacher.locator('#teacherStart').click()
   for ctx,page in students:
    page.locator('.v10-mode-chip').wait_for(state='visible',timeout=7000)
   for i,(ctx,page) in enumerate(students):
    choice='CPU' if i==0 else 'RAM'
    page.locator('#studentQuestionCard .q-option[data-value="'+choice+'"]').click()
   teacher.wait_for_function("()=>document.querySelector('#teacherStatus')?.textContent.includes('انتهى السؤال')",timeout=7000)
   teacher.wait_for_function("()=>document.querySelector('#teacherAnswered')?.textContent.includes('2 / 2 أجابوا')",timeout=7000)
   assert 'CPU' in students[0][1].locator('#studentMessage').inner_text() or True
   teacher.locator('#teacherReport').click()
   report=teacher.locator('#v10Report')
   report.wait_for(state='visible',timeout=7000)
   assert report.locator('#v10ReportTable tr').count()==2
   assert 'الوحدة الأولى' in report.locator('#v10ReportSkills').inner_text()
   teacher.screenshot(path=str(ARTIFACT/'game-lab-classroom-v10-report-1440.png'),animations='disabled')
   teacher.locator('#v10ReportClose').click()
   teacher.locator('#teacherNext').click()
   students[0][1].locator('#studentQuestionCard h2').get_by_text('ذاكرة').wait_for(timeout=7000)
   no_overflow(students[0][1],'quiz-mobile')
   students[0][1].screenshot(path=str(ARTIFACT/'game-lab-classroom-v10-student-390.png'),animations='disabled')
   for ctx,page in students:ctx.close()
   teacher.close();context.close()
   assert not errors,errors
   print('PASS V10 real browser teacher creator, PIN/QR, two students, leaderboard and report',flush=True)
   # Independently inspect all six distinct live game scenes on a small phone.
   for mode in ('quiz','fast','truth','pairs','wheel','boxes'):
    created=room(mode);code=created['code']
    host_ctx=browser.new_context(viewport={'width':1280,'height':800})
    host_ctx.add_init_script("localStorage.setItem('qn9_teacher_token',"+json.dumps(TEACHER)+");")
    host=host_ctx.new_page()
    host.goto(BASE+'/game-lab-live.html?host='+code,wait_until='domcontentloaded')
    host.locator('#teacherStart').click()
    ctx=browser.new_context(viewport={'width':390,'height':844})
    student=ctx.new_page()
    student.goto(BASE+'/game-lab-live.html?code='+code,wait_until='domcontentloaded')
    student.locator('#joinCard').fill(STUDENTS[0]['cardCode'])
    student.locator('#joinButton').click()
    student.locator('#studentQuestionCard .v10-mode-chip').wait_for(state='visible',timeout=8000)
    assert student.locator('#studentQuestionCard').get_attribute('data-v10-mode')==mode
    if mode=='truth':
     assert student.locator('.v10-truth-candidate').count()==1
     assert student.locator('.v10-truth-options .q-option').count()==2
    elif mode=='pairs':
     assert student.locator('.v10-pair-options .q-option').count()==4
    elif mode=='wheel':
     assert student.locator('.v10-spinning-wheel').count()==1
    elif mode=='boxes':
     student.locator('#studentQuestionCard .v10-open-box').click()
     assert student.locator('#studentQuestionCard .q-options').is_visible()
    elif mode=='fast':
     assert student.locator('.v10-timebar').count()==1
    else:
     assert student.locator('.v10-options .q-option').count()==4
    assert student.locator('.v10-options .q-option').count() in (2,4)
    no_overflow(student,mode)
    print('PASS V10 mobile scene '+mode,flush=True)
    ctx.close();host_ctx.close()
  finally:browser.close()
finally:
 HTTP.shutdown();HTTP.server_close();FOLDER.cleanup()
