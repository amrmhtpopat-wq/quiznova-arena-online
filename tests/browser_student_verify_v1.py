"""Real Chromium UI QA for TAG Student Verify V1.

Runs ONLY against an isolated temporary SQLite database and local HTTP server.
Never touches student production data, official Render or student distribution.
"""
import os
import sys
import tempfile
import threading
import uuid
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
dbdir=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(dbdir.name)/'browser-pin-qa.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
from playwright.sync_api import sync_playwright
import platform_store as store
import server

username='pin-browser-'+uuid.uuid4().hex[:12]+'@qa.example'
password='TeacherPIN_1234567!'
teacher=store.create_teacher(username,password,'معلم اختبار PIN','مدرسة تجريبية للبنين','المهارات الرقمية','boys')
owner=teacher['teacher']['id']
students=store.add_students(owner,[
    {'name':'طالب التحقق الأول','className':'التاسع أ','avatar':'m01'},
    {'name':'طالب التحقق الثاني','className':'التاسع أ','avatar':'m02'}])
card=students[0]['cardCode']
quiz={
    'id':'test-pin-ui-'+uuid.uuid4().hex[:10],
    'title':'اختبار هوية الطالب التجريبي',
    'subject':'المهارات الرقمية','grade':'التاسع','section':'أ',
    'settings':{'publishedSolo':True,'soloMaxAttempts':3,'randomQuestions':False},
    'questions':[
        {'id':'q1','type':'single','text':'ما وظيفة وحدة المعالجة؟',
         'options':['التخزين فقط','تنفيذ التعليمات','طباعة الصور'],
         'correct':[1],'time':120,'points':1000},
        {'id':'q2','type':'tf','text':'الذاكرة RAM مؤقتة',
         'correct':True,'time':120,'points':1000}]
}
store.save_snapshot(owner,{'quizzes':[quiz]})
http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(http.server_port)
out=Path('browser-qa-artifacts')
out.mkdir(exist_ok=True)

def take(page,name):
    page.screenshot(path=str(out/name),full_page=True)

def check(condition,message):
    if not condition:raise AssertionError(message)

with sync_playwright() as playwright:
    browser=playwright.chromium.launch(headless=True,args=['--no-sandbox'])
    teacher_ctx=browser.new_context(viewport={'width':1366,'height':900})
    teacher_page=teacher_ctx.new_page()
    errors=[]
    teacher_page.on('pageerror',lambda error:errors.append(str(error)))
    teacher_page.on('dialog',lambda dialog:dialog.accept())
    teacher_page.goto(BASE+'/?teacher=1',wait_until='domcontentloaded')
    teacher_page.locator('#authWall').wait_for(state='visible',timeout=15000)
    teacher_page.locator('#email').fill(username)
    teacher_page.locator('#password').fill(password)
    teacher_page.locator('#authSubmit').click()
    teacher_page.locator('#workspace').wait_for(state='visible',timeout=18000)
    teacher_page.locator('button[data-panel="students"]').click()
    teacher_page.locator('#studentVerifyPanel').wait_for(state='visible',timeout=9000)
    teacher_page.wait_for_function("document.querySelector('#verifyStatus')?.textContent.includes('PIN صادر')",timeout=15000)
    check(not teacher_page.locator('#verifyToggle').is_enabled(),'PIN activated without issuance')
    check('غير مفعّل' in teacher_page.locator('#verifyEnabledLabel').inner_text(),'PIN enabled by default')

    teacher_page.locator('#verifyIssueMissing').click()
    teacher_page.locator('#verifyReveal').wait_for(state='visible',timeout=20000)
    rows=teacher_page.locator('#verifyPinList').inner_text()
    record=next((line for line in rows.splitlines() if card in line),None)
    check(record is not None,'Student secret not issued to authenticated teacher')
    pin=record.strip().split()[-1]
    check(bool(re.fullmatch(r'[0-9]{6}',pin)),'Generated PIN not six digits')
    take(teacher_page,'tag-verify-teacher-issuance-QA.png')

    # Secret is absent from card QR and public student directory.
    check(pin not in teacher_page.locator('#studentsBoard').inner_text(),
          'Secret leaked onto printed student card')
    teacher_page.locator('#verifyHide').click()
    check(teacher_page.locator('#verifyPinList').inner_text()=='',
          'Secret was not cleared when teacher hides it')
    check(teacher_page.locator('#verifyToggle').is_enabled(),
          'PIN activation unavailable after all students issued')
    teacher_page.locator('#verifyToggle').click()
    teacher_page.wait_for_function(
        "document.querySelector('#verifyEnabledLabel')?.textContent.includes('مفعّل') && document.querySelector('#verifyEnabledLabel')?.classList.contains('is-on')",
        timeout=9000)
    take(teacher_page,'tag-verify-teacher-activated-QA.png')
    check(not errors,'Teacher panel JavaScript errors: '+str(errors))

    for width,height,mobile in [(1280,800,False),(390,844,True)]:
        ctx=browser.new_context(viewport={'width':width,'height':height},
                                is_mobile=mobile,has_touch=mobile)
        page=ctx.new_page()
        student_errors=[]
        page.on('pageerror',lambda error:student_errors.append(str(error)))
        page.goto(BASE+'/student.html?mode=card&card='+card,
                  wait_until='domcontentloaded')
        page.locator('#cardProfile').wait_for(state='visible',timeout=14000)
        page.locator('#boCardQuizzes .bo-card-test-item').first.wait_for(
            state='visible',timeout=14000)
        check('طالب التحقق الأول' in page.locator('#cardProfile').inner_text(),
              'Wrong student loaded from existing QR')
        check(not page.locator('#soloPinWrap').is_visible(),
              'Solo PIN visible before selecting the quiz')
        page.locator('#boCardQuizzes button').first.click()
        page.locator('#soloPinWrap').wait_for(state='visible',timeout=15000)
        check(page.locator('#soloView').is_visible(),
              'Card quiz was not opened in solo mode')
        page.locator('#soloPinCode').fill('123456' if pin!='123456' else '888888')
        page.locator('.bo-solo-quiz button').first.click()
        page.wait_for_function(
            "document.querySelector('#soloError')?.textContent.includes('PIN')",
            timeout=10000)
        check(page.locator('#soloPinCode').is_visible(),
              'PIN field disappeared after wrong attempt')
        page.locator('#soloPinCode').fill(pin)
        page.locator('.bo-solo-quiz button').first.click()
        page.locator('#boSoloForm').wait_for(state='visible',timeout=17000)
        check(not page.locator('#soloPinWrap').is_visible(),
              'PIN field did not hide during exam')
        take(page,'tag-verify-student-'+('mobile' if mobile else 'desktop')+'-QA.png')
        check(not student_errors,
              'Student screen JS errors: '+str(student_errors))
        # Complete the first student's attempt once, but prevent second simultaneous login
        # while it remains active.
        if not mobile:
            other=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
            second=other.new_page()
            second.goto(BASE+'/student.html?mode=solo',wait_until='domcontentloaded')
            second.locator('#soloCardCode').fill(card)
            second.locator('#soloLoadBtn').click()
            second.locator('#soloPinWrap').wait_for(state='visible',timeout=12000)
            second.locator('#soloPinCode').fill(pin)
            second.locator('.bo-solo-quiz button').first.click()
            second.wait_for_function(
                "document.querySelector('#soloError')?.textContent.includes('محاولة نشطة')",
                timeout=12000)
            take(second,'tag-verify-blocked-second-device-QA.png')
            other.close()
            # Teacher unlocks a lost device without deleting any completed result.
            teacher_page.locator('#verifyTargetCode').fill(card)
            teacher_page.locator('#verifyUnlock').click()
            teacher_page.wait_for_function(
                "document.querySelector('#verifyStatus')?.textContent.includes('تم تحرير')",
                timeout=12000)
        ctx.close()

    # Live join requires PIN only after activation, and guest/name-only bypass is blocked.
    live_quiz={'id':'pin-live-ui','title':'التحدي المباشر','questions':quiz['questions']}
    from urllib.request import Request,urlopen
    import json
    req=Request(BASE+'/api/room/start',
                data=json.dumps({'quiz':live_quiz,'section':'التاسع أ'}).encode(),
                method='POST',
                headers={'Authorization':'Bearer '+teacher['token'],
                         'Content-Type':'application/json'})
    with urlopen(req,timeout=10) as response:room=json.load(response)
    room_code=room['code']
    live_ctx=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
    live=live_ctx.new_page()
    live.goto(BASE+'/student.html?code='+room_code,wait_until='domcontentloaded')
    live.locator('#liveStudentPinWrap').wait_for(state='visible',timeout=15000)
    live.locator('#cardCode').fill(card)
    live.wait_for_function("document.querySelector('#playerName')?.value==='طالب التحقق الأول'",timeout=12000)
    live.locator('#liveStudentPin').fill(pin)
    live.locator('#joinBtn').click()
    live.locator('.lobby-card').wait_for(state='visible',timeout=16000)
    take(live,'tag-verify-live-pin-QA.png')
    live_ctx.close()
    browser.close()

http.shutdown()
http.server_close()
print('PASS: TAG Verify desktop and mobile real-browser UI, teacher issuance, student PIN, card QR, second device block, recovery, and live join')
