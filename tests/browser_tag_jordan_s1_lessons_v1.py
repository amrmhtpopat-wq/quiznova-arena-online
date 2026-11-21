"""Teacher-authenticated TAG Jordan S1 30-question unit/lesson end-to-end QA."""
import os,sys,tempfile,threading,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
tmp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(tmp.name)/'tag-s1-lesson-exams.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store
import server
math=store.create_teacher('s1-math@example.org','TAGMathS1Strong123!',
 'معلم الرياضيات','مدرسة تجريبية','الرياضيات','mixed')
digital=store.create_teacher('s1-digital@example.org','TAGDigitalS1Strong123!',
 'معلم المهارات الرقمية','مدرسة تجريبية','المهارات الرقمية','mixed')
http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(http.server_port)
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
 for teacher,sub,grade,unit,lesson in [
  (math,'الرياضيات','السابع','math-7-u3','math-7-u3-l4'),
  (digital,'المهارات الرقمية','السابع','digital-7-u1','digital-7-u1-l1')]:
  for width in (390,1366):
   ctx=browser.new_context(viewport={'width':width,'height':844},is_mobile=width==390,
       has_touch=width==390,service_workers='block')
   ctx.add_init_script('localStorage.setItem("qn9_teacher_token",'+json.dumps(teacher['token'])+');')
   page=ctx.new_page();errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(base+'/studio.html#library',wait_until='domcontentloaded',timeout=30000)
   page.locator('#tagS1Grade').wait_for(state='visible',timeout=25000)
   page.wait_for_function("window.TAG_JORDAN_S1_TESTS_V1 && typeof window.TAG_OPEN_S1_LESSON_EXAM==='function'",timeout=16000)
   assert page.locator('#tagS1TeacherSubject').inner_text().endswith(sub)
   assert page.locator('#tagS1Grade option').count()==6
   grades=page.locator('#tagS1Grade option').all_text_contents()
   assert 'السادس' in grades if sub=='الرياضيات' else 'الحادي عشر' in grades
   assert page.locator('#tagS1Unit').is_disabled()
   page.locator('#tagS1Grade').select_option(label=grade)
   page.locator('#tagS1Unit').select_option(unit)
   page.locator('#tagS1Lesson').select_option(lesson)
   page.locator('#tagS1ExamPreview').wait_for(state='visible',timeout=10000)
   assert page.locator('#tagS1ExamCount').inner_text()=='30'
   assert page.locator('#tagS1ExamSamples .tag-s1-sample').count()==3
   assert page.locator('#tagS1OpenExam').is_enabled()
   assert page.evaluate("TAG_JORDAN_S1_TESTS_V1.questionsFor('digital-7-u1-l1','الرياضيات').length") == 0
   assert page.evaluate("TAG_JORDAN_S1_TESTS_V1.questionsFor('math-7-u3-l4','المهارات الرقمية').length") == 0
   before=page.evaluate('DB.quizzes.length')
   page.locator('#tagS1OpenExam').click()
   page.locator('#view-builder.active').wait_for(state='visible',timeout=12000)
   assert page.evaluate('builderQuestions.length')==30
   assert page.evaluate("builderQuestions.every(q=>q.reviewStatus==='teacher_review_required')")
   assert page.locator('#quizSubject').input_value()==sub
   assert page.locator('#quizGrade').input_value()==grade
   assert page.evaluate('DB.quizzes.length')==before,'The lesson preview must not automatically save'
   assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 3'),(sub,width,'horizontal scroll')
   if sub=='الرياضيات':
    assert page.evaluate("builderQuestions.some(q=>q.text.includes('f(x)'))")
   if width==390:
    page.locator('#saveQuiz').click()
    page.locator('#view-library.active').wait_for(state='visible',timeout=18000)
    assert page.evaluate('DB.quizzes.length')==before+1
    assert page.evaluate('DB.quizzes[DB.quizzes.length-1].questions.length')==30
   assert not errors,(sub,width,errors)
   ctx.close()
 browser.close()
http.shutdown();http.server_close()
print('PASS TAG S1 graded math/digital teacher isolation, 30-question editor and optional explicit save on phone and desktop.')
