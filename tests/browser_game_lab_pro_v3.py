"""Chromium E2E: upload a book, generate editor draft, publish to class card and play live."""
import os,sys,uuid,tempfile,threading
from pathlib import Path
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
TEMP=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ.pop('OPENAI_API_KEY',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(TEMP.name)/'lab-e2e.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store
import server
email='pro-browser-'+uuid.uuid4().hex+'@example.test'
password='StrongBrowserPassword456!'
created=store.create_teacher(email,password,'معلم المتصفح','مدرسة الصفوف','المهارات الرقمية')
student=store.add_students(created['teacher']['id'],[
 {'name':'الطالب المتصفح','className':'التاسع ب','avatar':'m01'}])[0]
http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(http.server_port)
text='''CPU: وحدة معالجة تنفذ العمليات الحسابية والمنطقية للحاسوب.
RAM: ذاكرة تحفظ البيانات المؤقتة خلال تشغيل البرامج.
اللوحة الأم: لوحة تربط كل مكونات الحاسوب الداخلية معًا.
لوحة المفاتيح: جهاز لإدخال النصوص والأوامر إلى الحاسوب.
الشاشة: جهاز إخراج يعرض النصوص والصور والرسومات.
الفأرة: جهاز إدخال يستخدم لتوجيه المؤشر واختيار الملفات.
السماعات: أجهزة إخراج تستخدم لسماع الصوت في الحاسوب.
وحدة التخزين: جهاز يحتفظ بالبيانات والملفات بصورة دائمة.
'''
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
  try:
   context=browser.new_context(viewport={'width':1440,'height':900})
   page=context.new_page()
   errors=[]
   page.on('pageerror',lambda e:errors.append('teacher: '+str(e)))
   page.goto(base+'/game-lab-preview.html',wait_until='domcontentloaded')
   page.locator('#cloudEmail').fill(email)
   page.locator('#cloudPassword').fill(password)
   page.locator('#cloudSignIn').click()
   page.locator('#cloudWorkspace').wait_for(state='visible',timeout=15000)
   page.locator('#labBookFile').set_input_files({'name':'lesson.txt','mimeType':'text/plain','buffer':text.encode()})
   page.locator('#labBookUpload').click()
   page.wait_for_function("()=>document.querySelector('#labBookSelect').options.length>1",timeout=13000)
   page.locator('#labBookMode').select_option('extract')
   page.locator('#labBookGenerate').click()
   page.wait_for_function("()=>document.querySelector('#labBookPreview').querySelectorAll('.lab-bookrow').length>=4",timeout=13000)
   assert 'RAM' in page.locator('#activityData').input_value()
   # Confirm persistent textbook-linked activity and card assignment to ninth B.
   page.locator('#cloudMode').select_option('quiz')
   page.locator('#cloudSave').click()
   page.wait_for_function("()=>document.querySelectorAll('#cloudList .cloud-activity').length===1",timeout=13000)
   page.locator('#cloudList .cloud-activity button').filter(has_text='نشر').click()
   page.locator('#cloudShare').wait_for(state='visible',timeout=13000)
   page.wait_for_function("()=>document.querySelector('#labAssignActivity').options.length>1")
   page.locator('#labAssignActivity').select_option(index=1)
   page.locator('#labAssignType').select_option('class')
   page.locator('#labAssignTargets input').first.check()
   page.locator('#labAssignSave').click()
   page.wait_for_function("()=>document.querySelector('#labAssignStatus').textContent.includes('تم جلب')",timeout=12000)
   student_page=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True).new_page()
   student_page.on('pageerror',lambda e:errors.append('student: '+str(e)))
   student_page.goto(base+'/game-lab-card.html',wait_until='domcontentloaded')
   student_page.locator('#cardCode').fill(student['cardCode'])
   student_page.locator('#loadButton').click()
   student_page.locator('#gameList .game').first.wait_for(state='visible',timeout=12000)
   assert 'مكونات' in student_page.locator('#gameList').inner_text() or 'lesson' in student_page.locator('#gameList').inner_text()
   student_page.locator('#gameList .game .btn').first.click()
   student_page.locator('#studentCard').wait_for(state='visible',timeout=12000)
   assert student_page.locator('#studentCard').input_value()==student['cardCode']
   student_page.locator('#startBtn').click()
   student_page.locator('#questionText').wait_for(state='visible',timeout=12000)
   assert student_page.locator('#choices .choice').count()>0
   # Start a synchronized classroom competition from the same saved activity.
   page.locator('#labLiveActivity').select_option(index=1)
   page.locator('#labLiveMode').select_option('teams')
   page.locator('#labLiveCreate').click()
   page.locator('#labLiveCreated').wait_for(state='visible',timeout=13000)
   host_page=context.new_page()
   host_page.goto(page.locator('#labLiveTeacherLink').get_attribute('href'),wait_until='domcontentloaded')
   host_page.locator('#teacherPin').wait_for(timeout=12000)
   live_player=browser.new_context(viewport={'width':1280,'height':720}).new_page()
   live_player.goto(page.locator('#labLiveStudentLink').get_attribute('href'),wait_until='domcontentloaded')
   live_player.locator('#joinName').fill('مشارك ضيف')
   live_player.locator('#joinButton').click()
   live_player.locator('#studentTitle').wait_for(state='visible',timeout=13000)
   host_page.locator('#teacherStart').click()
   live_player.locator('#studentQuestionCard .q-option').first.wait_for(state='visible',timeout=14000)
   live_player.locator('#studentQuestionCard .q-option').first.click()
   host_page.wait_for_function("()=>document.querySelector('#teacherAnswered').textContent.includes('1 / 1')",timeout=14000)
   host_page.wait_for_function("()=>document.querySelector('#teacherStatus').textContent.includes('انتهى')",timeout=14000)
   assert not errors,errors
   print('PASS Game Lab V3: upload book, draft, teacher save, card assignment, student game and synchronized live teams.',flush=True)
  finally:
   browser.close()
finally:
 http.shutdown();http.server_close();TEMP.cleanup()
