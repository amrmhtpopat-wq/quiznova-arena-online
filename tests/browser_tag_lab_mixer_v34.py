"""TAG LAB V34 browser + API integration: mixer, same card, live room and separate pages."""
import os,sys,tempfile,threading,uuid
from pathlib import Path
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
tmp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ.pop('GEMINI_API_KEY',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(tmp.name)/'v34.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as db,server
email='tag-v34-'+uuid.uuid4().hex+'@example.test'
password='StrongTestV34Password!'
teacher=db.create_teacher(email,password,'معلم V34','مدرسة الاختبار','المهارات الرقمية')
tid=teacher['teacher']['id']
student=db.add_students(tid,[{'name':'طالب تجربة','className':'التاسع ب'}])[0]
http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(http.server_port)
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
  try:
   context=browser.new_context(viewport={'width':1366,'height':850})
   page=context.new_page()
   faults=[]
   page.on('pageerror',lambda e:faults.append(str(e)))
   page.goto(base+'/tag-lab-home.html',wait_until='domcontentloaded')
   assert page.locator('a[href="/tag-lab-mixer.html"]').count()>0
   page.goto(base+'/tag-lab-mixer.html',wait_until='domcontentloaded')
   page.locator('#mixer').wait_for(state='visible',timeout=12000)
   page.locator('#tagMixerLibrary').wait_for(state='visible')
   assert page.locator('.tag-simple-nav a[href="/tag-lab-mixer.html"][aria-current="page"]').count()==1
   assert page.locator('#mixerStart').is_disabled()
   page.locator('#cloudEmail').fill(email)
   page.locator('#cloudPassword').fill(password)
   page.locator('#cloudSignIn').click()
   page.wait_for_function("()=>!!localStorage.getItem('qn9_teacher_token')",timeout=15000)
   sample=[{'q':q,'a':a,'g':'المهارات الرقمية'} for q,a in [
     ('ما وظيفة الفأرة؟','التحكم بالمؤشر'),('ما وظيفة لوحة المفاتيح؟','إدخال البيانات'),
     ('ما وظيفة الشاشة؟','عرض المعلومات'),('ما وظيفة السماعة؟','إخراج الصوت')]]
   created=page.evaluate("""async activity=>{
    const headers={Authorization:'Bearer '+localStorage.getItem('qn9_teacher_token'),'Content-Type':'application/json'};
    const response=await fetch('/api/game-lab/teacher/save',{method:'POST',headers,body:JSON.stringify({activity})});
    return {status:response.status,data:await response.json()};
   }""",{'title':'حصة V34 التفاعلية','mode':'quiz','subject':'المهارات الرقمية','grade':'التاسع','rows':sample})
   assert created['status']==200,created
   activity_id=created['data']['id']
   page.locator('#tagMixerLibrary button').filter(has_text='تحديث').click()
   page.wait_for_function("()=>document.querySelector('#tagMixerActivity').options.length>1",timeout=14000)
   page.locator('#tagMixerActivity').select_option(activity_id)
   assert page.locator('#mixerStart').is_enabled()
   assert 'حصة V34' in page.locator('#tagMixerStatus').inner_text()
   page.locator('#mixerStart').click()
   page.locator('#playOverlay').wait_for(state='visible',timeout=13000)
   assert page.locator('#playOverlay').get_attribute('data-v9-mode')=='flash'
   page.locator('#closePlay').click()
   # Publish the same teacher-owned game for the existing official student card.
   outcome=page.evaluate("""async ({id,card})=>{
    const headers={Authorization:'Bearer '+localStorage.getItem('qn9_teacher_token'),'Content-Type':'application/json'};
    async function send(url,body){const r=await fetch(url,{method:'POST',headers,body:JSON.stringify(body)});return {status:r.status,data:await r.json()}}
    const published=await send('/api/game-lab/teacher/publish',{id,maxAttempts:2});
    const assigned=await send('/api/game-lab/pro/assignments/save',{activityId:id,targets:[{type:'all',value:'*'}]});
    const response=await fetch('/api/game-lab/pro/card/catalog',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({card})});
    return {published,assigned,catalog:{status:response.status,data:await response.json()}};
   }""",{'id':activity_id,'card':student['cardCode']})
   assert outcome['published']['status']==200,outcome
   assert outcome['assigned']['status']==200,outcome
   assert outcome['catalog']['status']==200,outcome
   assert outcome['catalog']['data']['student']['name']=='طالب تجربة',outcome
   assert any(a['id']==activity_id for a in outcome['catalog']['data']['activities']),outcome
   page.goto(base+'/student.html?mode=card',wait_until='domcontentloaded')
   link=page.locator('#tagLabStudentGames')
   link.wait_for(state='visible',timeout=12000)
   page.locator('#cardCode').fill(student['cardCode'])
   link.click()
   page.wait_for_url('**/game-lab-card.html?open=1',timeout=10000)
   assert page.locator('#cardCode').input_value()==student['cardCode']
   page.wait_for_function("()=>document.querySelector('#studentName')?.textContent.includes('طالب تجربة')",timeout=15000)
   assert page.locator('#gameList').inner_text().find('حصة V34')>=0
   page.goto(base+'/tag-lab-live.html',wait_until='domcontentloaded')
   page.locator('#liveLab').wait_for(state='visible',timeout=12000)
   page.wait_for_function("()=>document.querySelector('#labLiveActivity').options.length>1",timeout=14000)
   page.locator('#labLiveActivity').select_option(activity_id)
   page.locator('#labLiveCreate').click()
   page.wait_for_function("()=>document.querySelector('#labLiveCreated')&&!document.querySelector('#labLiveCreated').classList.contains('hide')",timeout=14000)
   assert len(page.locator('#labLiveCode').inner_text().strip())>=5
   assert not faults,faults
   print('PASS TAG LAB V34: interactive mixer, saved lesson, official student card, assignment, live competition and all buttons.',flush=True)
  finally:browser.close()
finally:http.shutdown();http.server_close();tmp.cleanup()
