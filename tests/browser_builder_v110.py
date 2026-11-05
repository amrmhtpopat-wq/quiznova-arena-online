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
        quizzes=[]
        for attempt in range(25):
            quizzes=store.snapshot(account['teacher']['id'])['quizzes']
            if len(quizzes)==1:break
            time.sleep(0.25)
        assert len(quizzes)==1,quizzes
        assert len(quizzes[0]['questions'])==2,quizzes
        assert [q['points'] for q in quizzes[0]['questions']]==[1000,2500]
        assert [q['time'] for q in quizzes[0]['questions']]==[20,45]
        assert not errors,errors
        page.screenshot(path=str(artifacts/('creator-mobile.png' if mobile else 'creator-desktop.png')),full_page=True)
        ctx.close()
    browser.close()
school.shutdown();school.server_close()
print('PASS: focused editor, 2-question navigation, teacher-chosen 45 seconds, 2500 points, and saved 1000-point default at desktop/mobile.')
