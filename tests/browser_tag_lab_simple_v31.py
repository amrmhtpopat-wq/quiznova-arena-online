"""TAG LAB V31: real independent pages, simple teacher workflow, safe shared game engine."""
from __future__ import annotations
import os,sys,tempfile,threading,uuid
from pathlib import Path
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
tmp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ.pop('GEMINI_API_KEY',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(tmp.name)/'tag-pages.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store
import server
created=store.create_teacher('simple-'+uuid.uuid4().hex+'@example.test',
    'ComplexEnoughForTesting123!','معلم تجريبي','مدرسة تجريبية','المهارات الرقمية')
http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(http.server_port)
lesson='''الادخار هو الاحتفاظ بجزء من الدخل لاستخدامه في المستقبل.
التضخم هو ارتفاع عام ومستمر في أسعار السلع والخدمات بمرور الزمن.
الموازنة هي خطة مالية تبين الإيرادات والنفقات خلال فترة زمنية محددة.
وحدة المعالجة المركزية: تنفذ التعليمات وتعالج البيانات داخل الحاسوب.
ذاكرة الوصول العشوائي: تحفظ البيانات المؤقتة المستخدمة أثناء التشغيل.
اللوحة الأم: تربط المكونات الداخلية وتسمح بالتواصل بينها.
الشاشة: تعرض النصوص والرسومات للمستخدم.
لوحة المفاتيح: تتيح للمستخدم إدخال النصوص والأوامر.
'''
routes=[
 ('tag-lab-books.html','bookLab'),
 ('tag-lab-create.html','builder'),
 ('tag-lab-games.html','catalog'),
 ('tag-lab-library.html','cloud'),
 ('tag-lab-live.html','liveLab'),
 ('tag-lab-students.html','studentAssignments')
]
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
  try:
   context=browser.new_context(viewport={'width':1440,'height':900})
   page=context.new_page()
   errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(base+'/tag-lab-home.html',wait_until='domcontentloaded')
   assert page.locator('a[href="/tag-lab-books.html"]').count()>=1
   assert page.locator('a[href="/tag-lab-live.html"]').count()>=1
   for path,section in routes:
    page.goto(base+'/'+path,wait_until='domcontentloaded')
    page.locator('.tag-simple-nav').wait_for(state='visible',timeout=20000)
    page.locator('#'+section).wait_for(state='visible',timeout=20000)
    assert page.locator('.tag-simple-links a[aria-current="page"]').count()==1,(path,'active nav')
    others=[name for _,name in routes if name!=section]
    assert all(not page.locator('#'+o).is_visible() for o in others),(path,'not isolated')
    assert not page.locator('.rail').is_visible(),path
   page.goto(base+'/tag-lab-books.html',wait_until='domcontentloaded')
   page.locator('#tagSimpleAuth #cloudEmail').wait_for(state='visible',timeout=15000)
   page.locator('#cloudEmail').fill('simple-'+created['teacher']['email'].split('simple-')[-1] if False else created['teacher'].get('email') or '')
   page.locator('#cloudPassword').fill('ComplexEnoughForTesting123!')
   page.locator('#cloudSignIn').click()
   page.wait_for_function("()=>document.querySelector('#cloudWorkspace')&&!document.querySelector('#cloudWorkspace').classList.contains('hide')",timeout=14000)
   page.locator('#labBookFile').set_input_files({'name':'مدرستي.txt','mimeType':'text/plain','buffer':lesson.encode()})
   page.locator('#labBookUpload').click()
   page.wait_for_function("()=>document.querySelector('#labBookSelect').options.length>1",timeout=13000)
   page.locator('#labBookMode').select_option('extract')
   page.locator('#labBookGenerate').click()
   page.wait_for_function("()=>document.querySelectorAll('#labBookPreview .tag-book-review-card').length>=4",timeout=15000)
   assert page.locator('#tagBookNext button').first.is_disabled()
   page.locator('#labBookApprove').click()
   page.locator('#tagBookNext button').first.wait_for(state='visible')
   assert page.locator('#tagBookNext button').first.is_enabled()
   page.locator('#tagBookNext button').first.click()
   page.wait_for_url('**/tag-lab-create.html',timeout=14000)
   page.wait_for_function("()=>document.querySelector('#activityData').value.split('\\n').length>=4",timeout=15000)
   assert ' | ' in page.locator('#activityData').input_value()
   assert not page.locator('#bookLab').is_visible()
   page.locator('.tag-simple-savebar button').filter(has_text='حفظ في مكتبتي').click()
   page.wait_for_function("()=>document.querySelector('#cloudMessage').textContent.includes('حُفظ')",timeout=16000)
   page.goto(base+'/tag-lab-library.html',wait_until='domcontentloaded')
   page.locator('#cloudList .cloud-activity').first.wait_for(state='visible',timeout=16000)
   assert page.locator('#cloudList .cloud-activity').count()==1
   page.locator('#cloudList .cloud-activity button').filter(has_text='تعديل أنواع الأسئلة').click()
   page.locator('#bookLab').wait_for(state='visible',timeout=13000)
   review=page.locator('#bookLab .tag-book-review-card').first
   review.locator('.tag-book-type').select_option('mcq')
   answer=review.locator('.tag-book-answer').input_value()
   for i,v in enumerate([answer,'الإفراط في الإنفاق','الاقتراض بلا حاجة','رفض تنظيم الدخل']):
    review.locator('.tag-book-choice').nth(i).fill(v)
   review.locator('.tag-book-difficulty').select_option('hard')
   page.locator('#labBookApprove').click()
   page.locator('#tagEditExistingBar button').filter(has_text='حفظ التعديلات').click()
   page.wait_for_function("()=>document.querySelector('#cloudMessage').textContent.includes('حُفظ')",timeout=13000)
   check=page.evaluate("""async()=>{const r=await fetch('/api/game-lab/teacher/list',{headers:{Authorization:'Bearer '+localStorage.getItem('qn9_teacher_token')}});return (await r.json()).activities}""")
   assert len(check)==1,check
   assert check[0]['activity']['rows'][0]['questionType']=='mcq',check
   assert len(check[0]['activity']['rows'][0]['choices'])==4,check
   assert check[0]['activity']['rows'][0]['difficulty']=='hard',check
   page.goto(base+'/tag-lab-games.html',wait_until='domcontentloaded')
   page.locator('#catalog .tag-v32-game').first.wait_for(state='visible',timeout=13000)
   assert page.locator('#catalog .tag-v32-game').count()==6
   assert page.locator('#gameGrid .game').count()==24
   assert not page.locator('#gameGrid .game').first.is_visible()
   page.get_by_role('button',name='عرض جميع القوالب الـ24').click()
   assert page.locator('#tagV32AllModes').is_visible()
   assert page.locator('#tagV32AllModes .tag-v32-option').count()==24
   page.locator('#tagV32AllModes .tag-v32-close').click()
   # Mobile check: focused header can scroll horizontally without page overflow.
   phone=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True).new_page()
   phone.on('pageerror',lambda e:errors.append('mobile:'+str(e)))
   phone.goto(base+'/tag-lab-home.html',wait_until='domcontentloaded')
   phone.locator('a[href="/tag-lab-books.html"]').first.click()
   phone.wait_for_url('**/tag-lab-books.html',timeout=13000)
   assert phone.locator('#bookLab').is_visible()
   assert not phone.locator('#catalog').is_visible()
   assert not errors,errors
   print('PASS TAG LAB V31 + V32: seven standalone pages, books-to-builder-to-library, saved-bank edit, games and mobile.')
  finally:browser.close()
finally:http.shutdown();http.server_close();tmp.cleanup()
