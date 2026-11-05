"""Browser-level WCAG contrast regression for the teacher's screenshots (v10.9)."""
import os,sys,json,threading,tempfile,uuid,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright

tmp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(tmp.name)/'contrast.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store
store.init()
import server
account=store.create_teacher('contrast-'+uuid.uuid4().hex+'@example.org','TeacherPassword123!','Teacher Contrast','مدرسة بنين','المهارات الرقمية','boys')
token=account['token']; tid=account['teacher']['id']
q={'id':'contrast-q1','type':'single','text':'لماذا يعد المعالج أهم جزء في تنفيذ التعليمات داخل الحاسوب؟',
   'options':['لأنه ينفذ التعليمات','لأنه يطبع الأوراق','لأنه يرسل الصوت','لأنه يخزن الملفات دائمًا'],
   'correct':[0],'time':60,'points':1000,'grade':'السابع','unit':'أنظمة الحوسبة',
   'subject':'المهارات الرقمية','difficulty':'easy','tags':['اختبار'],'skill':'معالجة البيانات'}
quiz={'id':'contrast-demo','title':'اختبار وضوح الخطوط','subject':'المهارات الرقمية','grade':'السابع',
      'questions':[q], 'settings':{'randomQuestions':False,'randomOptions':False,'showFeedback':True}}
store.save_snapshot(tid,{'quizzes':[quiz],'bank':[q],'results':[{
    'student':'طالب تجربة','quizTitle':'اختبار وضوح الخطوط','team':'','score':1000,
    'maxScore':1000,'percent':100,'seconds':12,'date':'2026-11-05T12:00:00Z','answers':[]}]})
site=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
thread=threading.Thread(target=site.serve_forever,daemon=True);thread.start()
base='http://127.0.0.1:'+str(site.server_port)
dest=Path('browser-qa-artifacts');dest.mkdir(exist_ok=True)

def as_rgb(value):
    n=[float(x) for x in re.findall(r'[\d.]+',value)[:3]]
    assert len(n)==3, value
    return n

def brightness(color):
    return sum(as_rgb(color))/3

def relative_luminance(color):
    channels=[]
    for n in as_rgb(color):
        v=n/255
        channels.append(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4)
    return sum(x*y for x,y in zip(channels,[.2126,.7152,.0722]))

def contrast(foreground,background):
    a,b=sorted([relative_luminance(foreground),relative_luminance(background)])
    return (b+.05)/(a+.05)

def check_ratio(page,text_selector,surface_selector,threshold=4.5):
    metrics=page.evaluate("""([textSel,bgSel])=>{
        let fg=getComputedStyle(document.querySelector(textSel));
        let bg=getComputedStyle(document.querySelector(bgSel));
        return {foreground:fg.color,background:bg.backgroundColor,
                visible:!!document.querySelector(textSel).getClientRects().length};
    }""",[text_selector,surface_selector])
    assert metrics['visible'],(text_selector,metrics)
    ratio=contrast(metrics['foreground'],metrics['background'])
    assert ratio>=threshold,(text_selector,surface_selector,round(ratio,2),metrics)
    return round(ratio,2)

def screenshot(page,name):
    page.screenshot(path=str(dest/name),full_page=True)

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
    for width,height,mobile in [(1366,768,False),(390,844,True)]:
        context=browser.new_context(viewport={'width':width,'height':height},is_mobile=mobile,has_touch=mobile)
        page=context.new_page()
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.add_init_script('localStorage.setItem("qn9_teacher_token", '+json.dumps(token)+');')
        page.goto(base+'/studio.html#builder',wait_until='domcontentloaded',timeout=30000)
        page.locator('#quizTitle').wait_for(state='visible',timeout=20000)
        assert page.locator('link[href*="booyah-contrast-v109"]').count()==1
        check_ratio(page,'#view-builder .settings-row .toggle-line span','#view-builder .settings-row .toggle-line')
        screenshot(page,'contrast-builder-'+('mobile' if mobile else 'desktop')+'.png')

        page.evaluate("go('live')")
        page.locator('#liveSetup').wait_for(state='visible',timeout=15000)
        check_ratio(page,'#view-live .live-switches .toggle-line span','#view-live .live-switches .toggle-line')
        check_ratio(page,'#view-live .v9-live-settings .toggle-line span','#view-live .v9-live-settings .toggle-line')
        screenshot(page,'contrast-live-'+('mobile' if mobile else 'desktop')+'.png')

        page.evaluate("go('bank')")
        page.locator('#questionBank .bank-item h4').wait_for(state='visible',timeout=10000)
        check_ratio(page,'#bankSummary .summary-chip','#bankSummary .summary-chip')
        assert brightness(page.locator('#questionBank .bank-item h4').evaluate('e=>getComputedStyle(e).color'))<135
        screenshot(page,'contrast-bank-'+('mobile' if mobile else 'desktop')+'.png')

        page.evaluate("go('results')")
        page.locator('#view-results .insight-card strong').first.wait_for(state='visible',timeout=10000)
        check_ratio(page,'#view-results .insight-card strong','#view-results .insight-card')
        check_ratio(page,'#view-results .insight-card small','#view-results .insight-card')
        screenshot(page,'contrast-results-'+('mobile' if mobile else 'desktop')+'.png')

        page.evaluate("go('library')")
        page.locator('#quizLibrary .quiz-card h4').wait_for(state='visible',timeout=10000)
        assert brightness(page.locator('#quizLibrary .quiz-card h4').evaluate('e=>getComputedStyle(e).color'))<135

        page.evaluate("go('play')")
        page.locator('#playQuizSelect').select_option('contrast-demo')
        page.locator('#studentName').fill('طالب اختبار')
        page.locator('#startQuiz').click()
        page.locator('#gameArea .game-card h3').wait_for(state='visible',timeout=10000)
        check_ratio(page,'#gameArea .game-card h3','#gameArea .game-card')
        for i in range(4):
            check_ratio(page,f'#gameArea .answer-btn:nth-child({i+1})',f'#gameArea .answer-btn:nth-child({i+1})')
        screenshot(page,'contrast-solo-'+('mobile' if mobile else 'desktop')+'.png')
        assert not errors,errors
        context.close()
    browser.close()
site.shutdown();site.server_close()
print('PASS: WCAG 4.5:1 for live checkbox labels, builder chips, bank summary, insights and all four solo answer colors on desktop/mobile.')
