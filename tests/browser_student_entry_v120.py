"""Real Chromium QA: official landing, teacher entry, card login and solo quiz on mobile/desktop."""
import os
import sys
import tempfile
import threading
import uuid
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright

tmp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(tmp.name)/'v120.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store
store.init()
import server
account=store.create_teacher('entry-'+uuid.uuid4().hex+'@example.org',
    'SecureTeacherPassword123!','Teacher Entry','مدرسة تجريبية للبنين','المهارات الرقمية','boys')
tid=account['teacher']['id']
student=store.add_students(tid,[{'name':'طالب التجربة','className':'التاسع ب','avatar':'m01'}])[0]
quiz={'id':'v120-published','title':'مهارات رقمية — تدريب فردي',
      'subject':'المهارات الرقمية','grade':'التاسع',
      'settings':{'publishedSolo':True,'randomQuestions':False},
      'questions':[
       {'id':'one','type':'single','text':'ما وظيفة المعالج CPU؟','options':['تشغيل الصوت','تنفيذ التعليمات','طباعة الورق','حفظ الملفات'],
        'correct':[1],'time':120,'points':1000},
       {'id':'two','type':'tf','text':'RAM ذاكرة مؤقتة','correct':True,'time':120,'points':1000}
      ]}
hidden={'id':'unpublished','title':'اختبار المعلم الخاص','subject':'المهارات الرقمية','grade':'التاسع',
        'settings':{'publishedSolo':False},'questions':[quiz['questions'][0]]}
store.save_snapshot(tid,{'quizzes':[quiz,hidden]})
http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(http.server_port)
out=Path('browser-qa-artifacts');out.mkdir(exist_ok=True)

with sync_playwright() as playwright:
    browser=playwright.chromium.launch(headless=True,args=['--no-sandbox'])
    for width,height,mobile in ((1280,800,False),(390,844,True)):
        ctx=browser.new_context(viewport={'width':width,'height':height},is_mobile=mobile,has_touch=mobile)
        page=ctx.new_page()
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(base+'/',wait_until='domcontentloaded')
        page.locator('#studentWelcome').wait_for(state='visible',timeout=15000)
        assert page.locator('title').text_content().startswith('BOOYAH!')
        assert page.locator('#studentWelcome a.bo-entry-option').count()==3
        assert page.locator('#authWall').is_hidden()
        page.screenshot(path=str(out/('home-student-mobile.png' if mobile else 'home-student-desktop.png')),full_page=True)

        page.locator('a.bo-entry-option[href*="mode=solo"]').click()
        page.wait_for_url('**/student.html?mode=solo')
        page.locator('#soloView').wait_for(state='visible')
        assert page.locator('#joinView').is_hidden()
        page.locator('#soloCardCode').fill(student['cardCode'])
        page.locator('#soloLoadBtn').click()
        page.locator('.bo-solo-quiz').first.wait_for(state='visible')
        assert page.locator('.bo-solo-quiz').count()==1
        assert 'اختبار المعلم الخاص' not in page.locator('#soloQuizList').inner_text()
        page.locator('.bo-solo-quiz button').click()
        page.locator('#boSoloForm').wait_for(state='visible',timeout=13000)
        assert page.locator('#boSoloForm h2').inner_text()=='ما وظيفة المعالج CPU؟'
        assert not page.locator('#boSoloForm').inner_text().find('correct:')>=0
        page.locator('.bo-solo-choice').filter(has_text='تنفيذ التعليمات').click()
        page.locator('#boSoloSubmit').click()
        page.locator('.bo-solo-feedback').wait_for(state='visible',timeout=13000)
        page.locator('#boSoloForm h2').wait_for(state='visible',timeout=13000)
        assert page.locator('#boSoloForm h2').inner_text()=='RAM ذاكرة مؤقتة'
        # Verify persistence of the solo session after browser refresh.
        page.reload(wait_until='domcontentloaded')
        page.locator('#boSoloForm h2').wait_for(state='visible',timeout=13000)
        assert page.locator('#boSoloForm h2').inner_text()=='RAM ذاكرة مؤقتة'
        page.locator('.bo-solo-choice').filter(has_text='صح').click()
        page.locator('#boSoloSubmit').click()
        page.locator('.bo-solo-finish').wait_for(state='visible',timeout=15000)
        assert '+30 XP' in page.locator('.bo-solo-finish').inner_text()
        assert '2000' in page.locator('.bo-solo-finish').inner_text()
        page.screenshot(path=str(out/('student-solo-mobile.png' if mobile else 'student-solo-desktop.png')),full_page=True)
        assert not errors,errors
        ctx.close()

        # Separate no-token visitor can still access the teacher's own login.
        teacher_ctx=browser.new_context(viewport={'width':width,'height':height},is_mobile=mobile,has_touch=mobile)
        teacher_page=teacher_ctx.new_page()
        teacher_page.goto(base+'/?teacher=1',wait_until='domcontentloaded')
        teacher_page.locator('#authWall').wait_for(state='visible',timeout=12000)
        teacher_page.locator('#email').fill(account['teacher']['email'])
        teacher_page.locator('#password').fill('SecureTeacherPassword123!')
        teacher_page.locator('#authSubmit').click()
        teacher_page.locator('#workspace').wait_for(state='visible',timeout=15000)
        assert teacher_page.locator('#studentWelcome').is_hidden()
        teacher_ctx.close()

        card_ctx=browser.new_context(viewport={'width':width,'height':height},is_mobile=mobile,has_touch=mobile)
        card_page=card_ctx.new_page()
        card_page.goto(base+'/student.html?mode=card',wait_until='domcontentloaded')
        card_page.locator('#joinView').wait_for(state='visible')
        card_page.locator('#cardCode').fill(student['cardCode'])
        card_page.locator('#showCardProfile').click()
        card_page.locator('#cardProfile').wait_for(state='visible',timeout=15000)
        assert 'طالب التجربة' in card_page.locator('#cardProfile').inner_text()
        assert card_page.locator('#joinBtn').is_visible()
        card_ctx.close()
    browser.close()
http.shutdown();http.server_close()
assert store.query('SELECT COUNT(*) AS c FROM student_attempts WHERE quiz_id=?',(quiz['id'],))['c']==2
print('PASS: student-first entry, secure card solo, hidden unpublished quizzes, two complete attempts, session resume and teacher login.')
