"""TAG Jordan curriculum browser acceptance: teacher subject isolation and safe quiz creation."""
import os,sys,tempfile,threading,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
tmp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(tmp.name)/'tag-jordan-library-v1.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store
import server
math=store.create_teacher('jordan-math@example.org','JordanMathTestPass123!',
 'معلم الرياضيات','مدرسة تجريبية','الرياضيات','mixed')
english=store.create_teacher('jordan-english@example.org','JordanEnglishTestPass123!',
 'معلم اللغة الإنجليزية','مدرسة تجريبية','اللغة الإنجليزية','mixed')
http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(http.server_port)
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
 for teacher,view in ((math,'library'),(english,'bank')):
  for width in (390,1366):
   ctx=browser.new_context(viewport={'width':width,'height':844},
       is_mobile=width==390,has_touch=width==390,service_workers='block')
   ctx.add_init_script('localStorage.setItem("qn9_teacher_token",'+json.dumps(teacher['token'])+');')
   page=ctx.new_page();errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(BASE+'/studio.html#'+view,wait_until='domcontentloaded')
   page.locator('#jordanLibrarySubject').wait_for(state='attached',timeout=25000)
   page.wait_for_function('window.TAG_JORDAN_CURRICULUM_V1 && window.go && document.querySelector("#jordanLibraryCount")',timeout=20000)
   assert page.evaluate('TAG_JORDAN_CURRICULUM_V1.grades.length')==12
   assert page.locator('#jordanLibrary .jordan-grade-card').count()==12
   subject='الرياضيات' if teacher is math else 'اللغة الإنجليزية'
   assert subject in page.locator('#jordanLibrarySubject').inner_text()
   count=page.evaluate('TAG_JORDAN_CURRICULUM_V1.questionsForTeacher(window.QN9_TEACHER.subject).length')
   assert count>100,(subject,count)
   other='اللغة الإنجليزية' if teacher is math else 'الرياضيات'
   assert all(q['subject']==subject for q in page.evaluate('TAG_JORDAN_CURRICULUM_V1.questionsForTeacher(window.QN9_TEACHER.subject).slice(0,200)'))
   assert page.evaluate('window.allAvailableBank().length')>=count
   stored_before=page.evaluate('DB.bank.length')
   assert stored_before<=20,('Shared library improperly copied into teacher storage',subject,stored_before)
   page.evaluate("go('generator')")
   assert page.locator('#genSubject').input_value()==subject
   page.locator('#genGrade').select_option(label='السابع')
   page.wait_for_function('Number(document.querySelector("#poolCount").textContent)>0')
   assert page.locator('#genLesson option').count()>1
   if teacher is math:
    page.locator('#genCount').fill('20')
    page.locator('#genTitle').fill('تحدي الرياضيات — السابع')
    page.locator('#generateQuiz').click()
    page.locator('#view-builder.active').wait_for(state='visible',timeout=10000)
    assert page.evaluate('builderQuestions.length')==20
    assert page.locator('#quizGrade').input_value()=='السابع'
    assert page.evaluate('DB.bank.length')==stored_before,'Shared source unexpectedly synced before quiz save'
    if width==390:
     page.locator('#saveQuiz').click()
     page.locator('#view-library.active').wait_for(state='visible',timeout=18000)
     assert page.locator('#quizLibrary .bo-library-quiz').count()==1
     assert page.evaluate('DB.bank.length')<=20,'Cloud snapshot should only contain explicitly selected questions'
   else:
    page.evaluate("go('bank')")
    page.locator('#bankGrade').select_option(label='السابع')
    page.wait_for_function('document.querySelector("#questionBank .jordan-bank-item")!==null')
    assert page.locator('#questionBank .jordan-bank-item').count()<=72
    assert page.locator('#jordanTeacherSubject').inner_text().endswith(subject)
    assert page.locator('#questionBank .jordan-bank-item').first.inner_text().find('اللغة الإنجليزية')>=0
    assert 'الرياضيات' not in page.locator('#bankSummary').inner_text()
   assert not errors,(subject,width,errors)
   ctx.close()
 browser.close()
http.shutdown();http.server_close()
print('PASS teacher-scoped Jordan curriculum, grade/lesson filters, quiz creation, and no auto-sync of shared bank.')
