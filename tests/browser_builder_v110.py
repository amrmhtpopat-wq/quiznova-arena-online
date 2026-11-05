"""Interactive Chrome regression for BOOYAH question creator v11.0."""
import os,sys,tempfile,threading,uuid,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright

temp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(temp.name)/'creator.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store
store.init()
import server
school=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=school.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(school.server_port)
artifacts=Path('browser-qa-artifacts');artifacts.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
    for width,height,mobile in ((1366,768,False),(390,844,True)):
        account=store.create_teacher('creator-'+uuid.uuid4().hex+'@school.example',
          'LongPassword123!','Teacher','مدرسة تجريبية للبنين','مهارات رقمية','boys')
        ctx=browser.new_context(viewport={'width':width,'height':height},is_mobile=mobile,has_touch=mobile)
        ctx.add_init_script("localStorage.setItem('qn9_teacher_token',"+repr(account['token'])+");")
        page=ctx.new_page()
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(base+'/studio.html#builder',wait_until='domcontentloaded',timeout=30000)
        page.locator('#quizTitle').wait_for(state='visible',timeout=20000)
        assert page.locator('#questionsEditor .bo-question-editor').count()==1
        assert page.locator('#boQuestionRail .bo-rail-question').count()==1
        assert page.locator('#boPropertyPoints').input_value()=='1000'
        assert page.locator('#boPropertyTime').input_value()=='20'
        # Digital Skills accounts start with three demo quizzes. Preserve them.
        page.evaluate("go('library')")
        initial_count=page.locator('#view-library .bo-library-quiz').count()
        page.evaluate("go('builder')")
        page.locator('#quizTitle').fill('اختبار تجريبي بتصميم مبسط')
        page.locator('.bo-question-prompt textarea').fill('ما وظيفة وحدة المعالجة المركزية؟')
        options=page.locator('.bo-question-editor .option-line > input:not([type=checkbox]):not([type=radio])')
        for i,label in enumerate(('تنفيذ التعليمات','تخزين الأوراق','طباعة البيانات','توصيل الطاقة')):
            options.nth(i).fill(label)
        page.locator('#boRailAddQuestion').click()
        assert page.locator('#boQuestionRail .bo-rail-question').count()==2
        assert page.locator('#questionsEditor .bo-question-editor').count()==1
        page.locator('.bo-question-prompt textarea').fill('ما وظيفة الذاكرة RAM؟')
        options=page.locator('.bo-question-editor .option-line > input:not([type=checkbox]):not([type=radio])')
        for i,label in enumerate(('تخزين مؤقت','عرض الصورة','الطباعة','الاتصال بالسماعة')):
            options.nth(i).fill(label)
        page.locator('#boPropertyTime').fill('45')
        page.locator('#boPropertyTime').press('Tab')
        assert page.locator('#boPropertyTime').input_value()=='45'
        page.locator('#boPropertyPoints').fill('2500')
        page.locator('#boPropertyPoints').press('Tab')
        assert page.locator('#boPropertyPoints').input_value()=='2500'
        page.locator('#boQuestionRail .bo-rail-question').first.click()
        assert page.locator('#boPropertyTime').input_value()=='20'
        assert page.locator('#boPropertyPoints').input_value()=='1000'
        assert page.locator('.bo-question-prompt textarea').input_value().startswith('ما وظيفة وحدة')
        page.locator('#boQuestionRail .bo-rail-question').nth(1).click()
        assert page.locator('#boPropertyPoints').input_value()=='2500'
        page.locator('#saveQuiz').click()
        # Save is acknowledged by cloud before navigating to the library.
        page.locator('#view-library.active .bo-library-quiz').first.wait_for(state='visible',timeout=15000)
        assert page.locator('#view-library .bo-library-quiz').count()==initial_count+1
        assert 'اختبار تجريبي بتصميم مبسط' in page.locator('#view-library .bo-library-quiz h4').first.inner_text()
        assert page.locator('#view-library .bo-saved-chip').count()==1
        quizzes=[]
        for attempt in range(25):
            quizzes=store.snapshot(account['teacher']['id'])['quizzes']
            if len(quizzes)==initial_count+1:break
            time.sleep(0.25)
        assert len(quizzes)==initial_count+1,quizzes
        saved=next(q for q in quizzes if q['title']=='اختبار تجريبي بتصميم مبسط')
        assert len(saved['questions'])==2,saved
        assert [q['points'] for q in saved['questions']]==[1000,2500]
        assert [q['time'] for q in saved['questions']]==[20,45]
        # A new quiz must never inherit the previous title/questions.
        page.locator('#view-library [data-jump="builder"]').click()
        assert page.locator('#quizTitle').input_value()==''
        assert page.locator('#boQuestionRail .bo-rail-question').count()==1
        assert page.locator('.bo-question-prompt textarea').input_value()==''
        assert page.locator('#boPropertyPoints').input_value()=='1000'

        # Save a different test and verify both remain, newest first.
        page.locator('#quizTitle').fill('اختبار ثان جديد')
        page.locator('.bo-question-prompt textarea').fill('ما وظيفة الشاشة؟')
        inputs=page.locator('.bo-question-editor .option-line > input:not([type=checkbox]):not([type=radio])')
        for idx,label in enumerate(('عرض النتائج','حفظ الصور','تخزين البيانات','تشغيل الإنترنت')):
            inputs.nth(idx).fill(label)
        page.locator('#saveQuiz').click()
        page.locator('#view-library.active .bo-library-quiz').first.wait_for(state='visible',timeout=15000)
        assert page.locator('#view-library .bo-library-quiz').count()==initial_count+2
        assert page.locator('#view-library .bo-library-quiz h4').first.inner_text()=='اختبار ثان جديد'
        persisted=store.snapshot(account['teacher']['id'])['quizzes']
        assert len(persisted)==initial_count+2,persisted
        newest=next(q for q in persisted if q['title']=='اختبار ثان جديد')
        first=next(q for q in persisted if q['title']=='اختبار تجريبي بتصميم مبسط')
        assert len(newest['questions'])==1 and len(first['questions'])==2

        # Direct launch from the chosen library card selects exactly that quiz.
        page.locator('#view-library .bo-library-quiz').first.locator('.bo-library-actions .btn-primary').click()
        page.locator('#liveSetup').wait_for(state='visible',timeout=15000)
        assert page.locator('#liveQuizSelect').input_value()==newest['id']

        # Return to the library and select solo: it must not use the older test.
        page.evaluate("go('library')")
        page.locator('#view-library .bo-library-quiz').first.locator('.bo-library-actions .btn-secondary').first.click()
        assert page.locator('#playQuizSelect').input_value()==newest['id']
        page.evaluate("go('library')")

        # Explicit Edit loads an existing quiz; + New clears it again.
        page.locator('#view-library .bo-library-quiz').nth(1).locator('.bo-library-actions .btn-secondary').nth(1).click()
        assert page.locator('#quizTitle').input_value()=='اختبار تجريبي بتصميم مبسط'
        page.evaluate("go('library')")
        page.locator('#view-library [data-jump="builder"]').click()
        assert page.locator('#quizTitle').input_value()==''
        assert page.locator('.bo-question-prompt textarea').input_value()==''

        # Reload from cloud, not stale page state.
        page.reload(wait_until='domcontentloaded')
        page.locator('#quizTitle').wait_for(state='visible',timeout=15000)
        page.evaluate("go('library')")
        assert page.locator('#view-library .bo-library-quiz').count()==initial_count+2
        assert not errors,errors
        page.screenshot(path=str(artifacts/('creator-mobile.png' if mobile else 'creator-desktop.png')),full_page=True)
        ctx.close()
    browser.close()
school.shutdown();school.server_close()
print('PASS: focused editor, 2-question navigation, teacher-chosen 45 seconds, 2500 points, and saved 1000-point default at desktop/mobile.')
