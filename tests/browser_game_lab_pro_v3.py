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
text='''الادخار هو الاحتفاظ بجزء من الدخل لاستخدامه في المستقبل.
التضخم هو ارتفاع عام ومستمر في أسعار السلع والخدمات بمرور الزمن.
الموازنة هي خطة مالية تبين الإيرادات والنفقات خلال فترة زمنية محددة.
وحدة المعالجة المركزية: تنفذ التعليمات وتعالج البيانات داخل الحاسوب.
ذاكرة الوصول العشوائي: تحفظ البيانات المؤقتة المستخدمة أثناء التشغيل.
اللوحة الأم: تربط المكونات الداخلية وتسمح بالتواصل بينها.
الشاشة: تعرض النصوص والرسومات للمستخدم.
لوحة المفاتيح: تتيح للمستخدم إدخال النصوص والأوامر.
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
   page.wait_for_function("()=>document.querySelector('#labBookPreview').querySelectorAll('.tag-book-review-card').length>=4",timeout=13000)
   assert not page.locator('#activityData').input_value(), 'Book suggestions must not silently publish to editor'
   assert page.locator('#labBookPreview .tag-book-evidence').count()>=4
   first=page.locator('#labBookPreview .tag-book-review-card').first
   first.locator('textarea.tag-book-question').fill('ما تعريف الادخار؟')
   correct=first.locator('.tag-book-answer').input_value()
   first.locator('.tag-book-type').select_option('mcq')
   first.locator('.tag-book-difficulty').select_option('hard')
   for i,value in enumerate([correct,'زيادة الديون','استنزاف الرصيد','إلغاء الميزانية']):
    first.locator('.tag-book-choice').nth(i).fill(value)
   first.locator('.tag-book-explanation').fill('الادخار يعني تخصيص جزء من الدخل للمستقبل.')
   second=page.locator('#labBookPreview .tag-book-review-card').nth(1)
   second.locator('.tag-book-type').select_option('true_false')
   second.locator('.tag-book-question').fill('التضخم هو ارتفاع عام ومستمر في الأسعار.')
   second.locator('.tag-book-answer').fill('صح')
   page.locator('#labBookApprove').click()
   page.wait_for_function("()=>document.querySelector('#activityData').value.includes('ما تعريف الادخار؟')",timeout=13000)
   assert 'صفحة' in page.locator('#activityData').input_value()
   # Confirm persistent textbook-linked activity and card assignment to ninth B.
   page.locator('#cloudMode').select_option('quiz')
   page.locator('#cloudSave').click()
   page.wait_for_function("()=>document.querySelectorAll('#cloudList .cloud-activity').length===1",timeout=13000)
   rows=page.evaluate("""async () => {
    const response=await fetch('/api/game-lab/teacher/list',{
      headers:{Authorization:'Bearer '+localStorage.getItem('qn9_teacher_token')}});
    const data=await response.json();
    return data.activities[0].activity.rows;
   }""")
   assert rows[0]['questionType']=='mcq',rows
   assert rows[0]['difficulty']=='hard',rows
   assert rows[0]['choices']==[correct,'زيادة الديون','استنزاف الرصيد','إلغاء الميزانية'],rows
   assert rows[0]['sourceQuote'],rows
   assert rows[1]['questionType']=='true_false' and rows[1]['a']=='صح',rows
   assert rows[1]['choices']==['صح','خطأ'],rows
   # Edit this saved question bank without another AI request or losing its activity ID.
   page.locator('#cloudList .cloud-activity button').filter(has_text='تعديل أنواع الأسئلة').click()
   editable=page.locator('#labBookPreview .tag-book-review-card').first
   assert editable.locator('.tag-book-choice').nth(0).input_value()==correct
   editable.locator('.tag-book-choice').nth(3).fill('إيقاف الإنفاق')
   page.locator('#labBookApprove').click()
   page.locator('#cloudSave').click()
   page.wait_for_function("()=>document.querySelector('#cloudMessage').textContent.includes('حُفظ')",timeout=13000)
   updated=page.evaluate("""async () => {
    const response=await fetch('/api/game-lab/teacher/list',{
      headers:{Authorization:'Bearer '+localStorage.getItem('qn9_teacher_token')}});
    return (await response.json()).activities[0].activity.rows;
   }""")
   assert updated[0]['choices'][3]=='إيقاف الإنفاق',updated
   assert updated[0]['questionType']=='mcq' and updated[1]['questionType']=='true_false',updated
   assert page.locator('#cloudList .cloud-activity').count()==1
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
   print('PASS Game Lab V30: review MCQ/TF evidence and preserve persistent choices, approve draft, teacher save, card assignment, student game and synchronized live teams.',flush=True)
  finally:
   browser.close()
finally:
 http.shutdown();http.server_close();TEMP.cleanup()
