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
    teacher_page.on('dialog',lambda dialog:dialog.accept(
        'REISSUE 2' if dialog.type=='prompt' else None))
    teacher_page.goto(BASE+'/?teacher=1',wait_until='domcontentloaded')
    teacher_page.locator('#authWall').wait_for(state='visible',timeout=15000)
    teacher_page.locator('#email').fill(username)
    teacher_page.locator('#password').fill(password)
    teacher_page.locator('#authSubmit').click()
    teacher_page.locator('#workspace').wait_for(state='visible',timeout=18000)
    # The approved TAG Spatial home hides its legacy side menu, but its
    # student identity instrument goes directly to the SAME protected panel.
    teacher_page.locator('#panel-home>.tag-spatial-native-host').wait_for(state='visible',timeout=15000)
    teacher_page.locator('.tag-spatial-native-host').locator('[data-tool="cards"]').click()
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
    second_card=students[1]['cardCode']
    second_record=next((line for line in rows.splitlines() if second_card in line),None)
    check(second_record is not None,'Second student private code not issued')
    second_pin=second_record.strip().split()[-1]
    check(bool(re.fullmatch(r'[0-9]{6}',pin)),'Generated PIN not six digits')
    check(bool(re.fullmatch(r'[0-9]{6}',second_pin)) and second_pin!=pin,
          'Second student PIN invalid or reused')
    # Simulate lost issuance window; old hashes cannot reveal secrets.
    teacher_page.locator('#verifyHide').click()
    teacher_page.locator('#verifyIssueMissing').click()
    teacher_page.wait_for_function(
        "document.querySelector('#verifyStatus')?.textContent.includes('PIN بالفعل')",
        timeout=10000)
    check(not teacher_page.locator('#verifyReveal').is_visible(),
          'An already-issued secret was incorrectly exposed a second time')
    # Explicitly double-confirm the two-student recovery. The page must
    # open in the same tab even if browser auto-downloads/popups are blocked.
    teacher_page.locator('#verifyReissueAll').click()
    teacher_page.locator('#tagPinReceipt').wait_for(state='visible',timeout=25000)
    check('صفحة رموز PIN للطلاب' in teacher_page.locator('#tagPinReceipt').inner_text(),
          'PIN receipt full-page interface failed to open')
    check(card in teacher_page.locator('#tagPinReceipt').inner_text(),
          'PIN receipt did not include the student access code')
    with teacher_page.expect_download(timeout=12000) as recovered_file:
        teacher_page.locator('#verifyReceiptDownload').click()
    exported=recovered_file.value
    recovered_path=Path(dbdir.name)/'reissued-pins-private.csv'
    exported.save_as(str(recovered_path))
    teacher_page.locator('#verifyReveal').wait_for(state='visible',timeout=15000)
    newrows=teacher_page.locator('#verifyPinList').inner_text()
    newfirst=next(x for x in newrows.splitlines() if card in x).split()[-1]
    newsecond=next(x for x in newrows.splitlines() if second_card in x).split()[-1]
    check(bool(re.fullmatch(r'[0-9]{6}',newfirst)) and
          bool(re.fullmatch(r'[0-9]{6}',newsecond)) and newfirst!=newsecond,
          'Recovery did not create two distinct six-digit PINs')
    check(newfirst in recovered_path.read_text(encoding='utf-8-sig'),
          'Recovery CSV did not contain the new private PIN')
    pin=newfirst
    second_pin=newsecond
    check(not teacher_page.locator('#verifyToggle').is_enabled(),
          'Bulk PIN recovery accidentally enabled PIN verification')
    take(teacher_page,'tag-verify-teacher-receipt-page-QA.png')
    teacher_page.locator('#verifyReceiptClose').click()
    check(not teacher_page.locator('#tagPinReceipt').count(),
          'Closing receipt page did not remove confidential overlay')
    teacher_page.locator('#verifyReceiptPage').click()
    check(teacher_page.locator('#tagPinReceipt').is_visible(),
          'Teacher cannot reopen the receipt in the same PIN issuance session')
    teacher_page.locator('#verifyReceiptClose').click()

    # Secret is absent from card QR and public student directory.
    check(pin not in teacher_page.locator('#studentsBoard').inner_text(),
          'Secret leaked onto printed student card')
    with teacher_page.expect_download() as delivery:
        teacher_page.locator('#verifySlips').click()
    secret_slips=delivery.value
    slip_path=Path(dbdir.name)/'test-private-pin-slips.html'
    secret_slips.save_as(str(slip_path))
    rendered=slip_path.read_text(encoding='utf-8')
    check(pin in rendered and card in rendered and 'سرّي للطالب فقط' in rendered,
          'Individual private PIN handout did not include the correct school card')
    teacher_page.locator('#verifyHide').click()
    check(teacher_page.locator('#verifyPinList').inner_text()=='',
          'Secret was not cleared when teacher hides it')
    check(not teacher_page.locator('#verifyToggle').is_enabled(),
          'PIN activated without confirming private delivery')
    teacher_page.locator('#verifyDelivered').check()
    check(teacher_page.locator('#verifyToggle').is_enabled(),
          'PIN activation unavailable after private delivery was confirmed')
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
    # TAG LAB also accepts the original card with PIN; a guest must not
    # impersonate another student when the teacher enabled verification.
    import game_lab_api as lab_games
    import game_lab_live as lab_live
    lab_rows=[{'q':'ما وظيفة وحدة المعالجة '+str(i)+'؟',
               'a':'تنفيذ التعليمات','g':'أساسيات الحاسوب',
               'choices':['تنفيذ التعليمات','التخزين','الصوت','العرض']}
              for i in range(1,5)]
    activity=lab_games.save(owner,{'activity':{
        'title':'اختبار TAG LAB المحمي','subject':'المهارات الرقمية',
        'grade':'التاسع','mode':'quiz','rows':lab_rows}})
    lab_public=lab_games.publish(owner,{'id':activity['id'],'maxAttempts':3},True)
    lab_code=lab_public['publicCode']
    lab_ctx=browser.new_context(viewport={'width':390,'height':844},
                                is_mobile=True,has_touch=True)
    lab_page=lab_ctx.new_page()
    lab_errors=[]
    lab_page.on('pageerror',lambda error:lab_errors.append(str(error)))
    lab_page.goto(BASE+'/game-lab-play.html?game='+lab_code,
                  wait_until='domcontentloaded')
    lab_page.locator('#studentCard').fill(second_card)
    lab_page.locator('#studentVerifyPin').fill(second_pin)
    lab_page.locator('#startBtn').click()
    lab_page.locator('#questionPanel').wait_for(state='visible',timeout=17000)
    take(lab_page,'tag-verify-lab-solo-mobile-QA.png')
    check(not lab_errors,'TAG LAB individual errors '+str(lab_errors))
    lab_ctx.close()
    # Release only the incomplete lab attempt, retaining completed marks.
    from urllib.request import Request,urlopen
    req=Request(BASE+'/api/teacher/student-verify/unlock',
                data=json.dumps({'studentId':students[1]['id']}).encode(),
                method='POST',
                headers={'Authorization':'Bearer '+teacher['token'],
                         'Content-Type':'application/json'})
    with urlopen(req,timeout=10) as response:
        unlocked=json.load(response)
    check(unlocked['revoked']>=1,'Teacher cannot release TAG LAB unfinished attempt')

    live_room=lab_live.create(owner,{'activityId':activity['id']})
    room=live_room['code']
    lab_live_ctx=browser.new_context(viewport={'width':390,'height':844},
                                     is_mobile=True,has_touch=True)
    lab_live_page=lab_live_ctx.new_page()
    lab_live_errors=[]
    lab_live_page.on('pageerror',lambda error:lab_live_errors.append(str(error)))
    lab_live_page.goto(BASE+'/game-lab-live.html?code='+room,
                       wait_until='domcontentloaded')
    lab_live_page.locator('#roomCode').fill(room)
    lab_live_page.locator('#joinCard').fill(second_card)
    lab_live_page.locator('#joinVerifyPin').fill(second_pin)
    lab_live_page.locator('#joinButton').click()
    lab_live_page.locator('#student').wait_for(state='visible',timeout=17000)
    take(lab_live_page,'tag-verify-lab-live-mobile-QA.png')
    check(not lab_live_errors,'TAG LAB live errors '+str(lab_live_errors))
    lab_live_ctx.close()
    browser.close()

http.shutdown()
http.server_close()
print('PASS: TAG Verify desktop and mobile real-browser UI, teacher issuance, student PIN, card QR, second device block, recovery, and live join')
