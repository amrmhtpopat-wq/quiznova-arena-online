"""TAG LAB V32: template-first gallery, real preview, no-loss template switch and saved game."""
import os,sys,tempfile,threading,uuid
from pathlib import Path
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
temporary=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ.pop('GEMINI_API_KEY',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(temporary.name)/'game-v32.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store,server
email='v32-'+uuid.uuid4().hex+'@example.test'
password='StrongBrowserPassword456!'
account=store.create_teacher(email,password,'معلم V32','مدرسة التدريب','المهارات الرقمية')
http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(http.server_port)
raw='''ما عاصمة الأردن؟ | عمّان | جغرافيا
كم ناتج 5 × 6؟ | 30 | رياضيات
ما الكوكب الأحمر؟ | المريخ | علوم
ما مرادف كلمة سريع؟ | عاجل | لغة عربية'''
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
  try:
   context=browser.new_context(viewport={'width':1440,'height':900})
   page=context.new_page()
   faults=[]
   page.on('pageerror',lambda e:faults.append(str(e)))
   page.goto(base+'/tag-lab-home.html',wait_until='domcontentloaded')
   page.get_by_role('link',name='استكشف القوالب وجربها').first.click()
   page.wait_for_url('**/tag-lab-games.html',timeout=15000)
   cards=page.locator('#catalog .tag-v32-game')
   cards.first.wait_for(state='visible',timeout=14000)
   assert cards.count()==6,cards.count()
   assert not page.locator('#gameGrid .game').first.is_visible()
   chosen=page.locator('#cloudMode').input_value()
   wheel=page.locator('#catalog .tag-v32-game[data-mode="wheel"]')
   wheel.get_by_role('button',name='معاينة لعبة عجلة الحظ بأسئلة تجريبية').click()
   page.locator('#playOverlay').wait_for(state='visible',timeout=12000)
   assert page.locator('#tagV32SampleNotice').is_visible()
   assert page.locator('#playTitle').inner_text().strip().endswith('عجلة الحظ')
   assert not page.locator('#activityData').input_value(), 'Preview must not insert sample text in the teacher editor'
   page.locator('#closePlay').click()
   assert page.locator('#cloudMode').input_value()==chosen,'Preview must not change selected mode'
   wheel.get_by_role('button',name='استخدم هذا القالب').click()
   page.wait_for_url('**/tag-lab-create.html',timeout=16000)
   assert page.locator('#cloudMode').input_value()=='wheel','Choice must persist between separate pages'
   assert 'عجلة الحظ' in page.locator('.tag-v32-current').inner_text()
   page.locator('#activityTitle').fill('مراجعة الصف التاسع')
   # Teachers use the easy structured question editor, not the hidden bulk textarea.
   for i,line in enumerate(raw.split('\n')):
    fields=line.split(' | ')
    page.locator('#v5Add').click()
    card=page.locator('#v5QuestionList .v5-question').nth(i)
    card.locator('input[name="q"]').fill(fields[0])
    card.locator('input[name="a"]').fill(fields[1])
    card.locator('input[name="g"]').fill(fields[2])
   page.locator('#builder .tag-v32-mini[data-mode="quiz"]').click()
   assert page.locator('#cloudMode').input_value()=='quiz'
   assert page.locator('#activityData').input_value()==raw,'Switching must never rewrite questions'
   page.locator('.tag-v32-modebar button').filter(has_text='تغيير القالب').click()
   dialog=page.locator('#tagV32AllModes')
   dialog.wait_for(state='visible')
   assert dialog.locator('.tag-v32-option').count()==24
   dialog.locator('.tag-v32-option[data-mode="pairs"]').click()
   dialog.locator('#tagV32ModalPick').click()
   assert page.locator('#cloudMode').input_value()=='pairs'
   assert page.locator('#activityData').input_value()==raw
   page.locator('.tag-v32-modebar button').filter(has_text='تجربة بأسئلتي').click()
   page.locator('#playOverlay').wait_for(state='visible',timeout=12000)
   assert not page.locator('#tagV32SampleNotice').is_visible(),'Full draft should preview with own questions'
   assert page.locator('#playOverlay').get_attribute('data-v9-mode')=='pairs',page.locator('#playTitle').inner_text()
   page.locator('#closePlay').click()
   assert page.locator('#activityData').input_value()==raw
   page.locator('#cloudEmail').fill(email);page.locator('#cloudPassword').fill(password)
   page.locator('#cloudSignIn').click()
   page.wait_for_function("()=>document.querySelector('#cloudWorkspace')&&!document.querySelector('#cloudWorkspace').classList.contains('hide')",timeout=15000)
   page.locator('.tag-simple-savebar button').filter(has_text='حفظ في مكتبتي').click()
   page.wait_for_function("()=>document.querySelector('#cloudMessage').textContent.includes('حُفظ')",timeout=12000)
   page.goto(base+'/tag-lab-library.html',wait_until='domcontentloaded')
   page.locator('#cloudList .cloud-activity').first.wait_for(state='visible',timeout=13000)
   saved=page.evaluate("""async () => {
     const r=await fetch('/api/game-lab/teacher/list',{
       headers:{Authorization:'Bearer '+localStorage.getItem('qn9_teacher_token')}});
     return (await r.json()).activities;
   }""")
   assert len(saved)==1,saved
   assert saved[0]['mode']=='pairs',saved
   assert [r['q'] for r in saved[0]['activity']['rows']]==[x.split(' | ')[0] for x in raw.split('\n')],saved
   phone=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True).new_page()
   phone.on('pageerror',lambda e:faults.append('mobile:'+str(e)))
   phone.goto(base+'/tag-lab-games.html',wait_until='domcontentloaded')
   phone.locator('#catalog .tag-v32-game').first.wait_for(state='visible',timeout=14000)
   assert phone.locator('#catalog .tag-v32-game').count()==6
   assert phone.locator('#catalog .tag-v32-game[data-mode="wheel"] button.pick').is_visible()
   assert not faults,faults
   print('PASS V32: six visual templates, real safe preview, saved mode, no-loss switch, 24 modes, cloud persistence and mobile.',flush=True)
  finally:browser.close()
finally:http.shutdown();http.server_close();temporary.cleanup()
