"""TAG LAB V33: template-first gallery, private question banks, previews and saved editing."""
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
   wheel.get_by_role('button',name='✏️ اكتب أسئلة هذا القالب').click()
   page.wait_for_url('**/tag-lab-create.html',timeout=16000)
   page.locator('#tagV33Editor').wait_for(state='visible',timeout=15000)
   assert page.locator('#cloudMode').input_value()=='wheel'
   assert 'عجلة الحظ' in page.locator('#tagV33Heading').inner_text()
   wheelQuestions=[('ما عاصمة الأردن؟','عمّان'),('كم ناتج 5 × 6؟','30'),
                   ('ما الكوكب الأحمر؟','المريخ'),('ما مرادف سريع؟','عاجل')]
   def add_rows(items):
    for i,(question,answer) in enumerate(items):
     if i:page.locator('#tagV33Add').click()
     card=page.locator('#tagV33List .tag-v33-card').nth(i)
     card.locator('.tag-v33-fields textarea').fill(question)
     card.locator('.tag-v33-fields input').fill(answer)
   page.locator('#activityTitle').fill('تحدي العجلة')
   add_rows(wheelQuestions)
   wheelRaw=page.locator('#activityData').input_value()
   assert wheelRaw.count('\n')==3,wheelRaw
   # Changing the mode opens a distinct empty bank — wheel questions must stay saved.
   page.locator('#builder .tag-v32-mini[data-mode="quiz"]').click()
   assert page.locator('#cloudMode').input_value()=='quiz'
   assert not page.locator('#activityData').input_value()
   assert page.locator('#tagV33List .tag-v33-card').count()==1
   page.locator('#activityTitle').fill('أسئلة الاختبار')
   add_rows([('ما وظيفة RAM؟','ذاكرة مؤقتة'),('أين تقع عمّان؟','الأردن'),
             ('كم يساوي 4 + 4؟','8'),('ما لون السماء؟','أزرق')])
   first=page.locator('#tagV33List .tag-v33-card').first
   for i,text in enumerate(['قرص صلب','شاشة','طابعة']):
    first.locator('.tag-v33-three input').nth(i).fill(text)
   assert page.locator('#activityData').input_value()!=wheelRaw
   assert page.locator('#tagV33Heading').inner_text().find('الاختبار')>=0
   page.locator('#builder .tag-v32-mini[data-mode="wheel"]').click()
   assert page.locator('#activityData').input_value()==wheelRaw,'wheel draft must survive returning to mode'
   assert page.locator('#activityTitle').input_value()=='تحدي العجلة'
   page.locator('.tag-v32-modebar button').filter(has_text='فتح قالب آخر').click()
   dialog=page.locator('#tagV32AllModes')
   dialog.wait_for(state='visible')
   assert dialog.locator('.tag-v32-option').count()==24
   dialog.locator('.tag-v32-option[data-mode="pairs"]').click()
   # Closing a selection dialog without confirming must not change the template.
   dialog.locator('.tag-v32-close').click()
   assert page.locator('#cloudMode').input_value()=='wheel'
   page.locator('.tag-v32-modebar button').filter(has_text='فتح قالب آخر').click()
   dialog.locator('.tag-v32-option[data-mode="pairs"]').click()
   dialog.locator('#tagV32ModalPick').click()
   assert page.locator('#cloudMode').input_value()=='pairs'
   assert not page.locator('#activityData').input_value(),'pairs must not silently receive wheel questions'
   page.locator('#activityTitle').fill('أزواج الحاسوب')
   pairsQuestions=[('الشاشة','عرض المعلومات'),('الفأرة','التحكم بالمؤشر'),
                   ('لوحة المفاتيح','إدخال البيانات'),('السماعات','إخراج الصوت')]
   add_rows(pairsQuestions)
   pairRaw=page.locator('#activityData').input_value()
   page.locator('#tagV33Preview').click()
   page.locator('#playOverlay').wait_for(state='visible',timeout=12000)
   assert not page.locator('#tagV32SampleNotice').is_visible(),'own questions, not demo'
   assert page.locator('#playOverlay').get_attribute('data-v9-mode')=='pairs'
   page.locator('#closePlay').click()
   assert page.locator('#activityData').input_value()==pairRaw
   page.locator('#cloudEmail').fill(email)
   page.locator('#cloudPassword').fill(password)
   page.locator('#cloudSignIn').click()
   page.wait_for_function("()=>document.querySelector('#cloudWorkspace')&&!document.querySelector('#cloudWorkspace').classList.contains('hide')",timeout=16000)
   page.locator('.tag-simple-savebar button').filter(has_text='حفظ في مكتبتي').click()
   page.wait_for_function("()=>document.querySelector('#cloudMessage').textContent.includes('حُفظ')",timeout=13000)
   page.goto(base+'/tag-lab-library.html',wait_until='domcontentloaded')
   page.locator('#cloudList .cloud-activity').first.wait_for(state='visible',timeout=15000)
   def owned():
    return page.evaluate("""async()=> {
     const r=await fetch('/api/game-lab/teacher/list',{
      headers:{Authorization:'Bearer '+localStorage.getItem('qn9_teacher_token')}});
     return (await r.json()).activities;
    }""")
   saved=owned()
   assert len(saved)==1,saved
   assert saved[0]['mode']=='pairs',saved
   assert [r['q'] for r in saved[0]['activity']['rows']]==[q for q,a in pairsQuestions],saved
   oldId=saved[0]['id']
   # Edit the saved pairs activity itself, then ensure it updates in place.
   page.locator('#cloudList .cloud-activity button').filter(has_text='✏️ تعديل').click()
   page.wait_for_url('**/tag-lab-create.html?edit=*',timeout=14000)
   page.wait_for_function("()=>document.querySelector('#tagV33List textarea')?.value.includes('الشاشة')",timeout=15000)
   assert page.locator('#cloudMode').input_value()=='pairs'
   page.locator('#tagV33List .tag-v33-card').first.locator('textarea').first.fill('شاشة الحاسوب')
   page.locator('.tag-simple-savebar button').filter(has_text='حفظ في مكتبتي').click()
   page.wait_for_function("()=>document.querySelector('#cloudMessage').textContent.includes('حُفظ')",timeout=13000)
   page.goto(base+'/tag-lab-library.html',wait_until='domcontentloaded')
   page.locator('#cloudList .cloud-activity').first.wait_for(state='visible',timeout=12000)
   updated=owned()
   assert len(updated)==1,updated
   assert updated[0]['id']==oldId,updated
   assert updated[0]['activity']['rows'][0]['q']=='شاشة الحاسوب',updated
   # Return to creator from this tab: wheel bank must still be isolated and available.
   page.goto(base+'/tag-lab-create.html',wait_until='domcontentloaded')
   page.locator('#tagV33Editor').wait_for(state='visible',timeout=10000)
   page.locator('#builder .tag-v32-mini[data-mode="wheel"]').click()
   assert page.locator('#activityData').input_value()==wheelRaw
   assert page.locator('#activityTitle').input_value()=='تحدي العجلة'
   assert page.locator('#tagV33List .tag-v33-card').count()==4
   phone=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True).new_page()
   phone.on('pageerror',lambda e:faults.append('mobile:'+str(e)))
   phone.goto(base+'/tag-lab-games.html',wait_until='domcontentloaded')
   phone.locator('#catalog .tag-v32-game').first.wait_for(state='visible',timeout=14000)
   assert phone.locator('#catalog .tag-v32-game').count()==6
   assert phone.locator('#catalog .tag-v32-game[data-mode="wheel"] button.pick').is_visible()
   assert not faults,faults
   print('PASS V33: six visual templates, private quiz/wheel/pairs drafts, editable owned activity, cloud persistence and mobile.',flush=True)
  finally:browser.close()
finally:http.shutdown();http.server_close();temporary.cleanup()
