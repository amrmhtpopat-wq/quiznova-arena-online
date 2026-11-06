"""Control Center V2.1 desktop/mobile Chromium acceptance test using an isolated local database."""
import os
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

from cryptography.fernet import Fernet
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
TMP=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(TMP.name)/'admin-v2-browser.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
os.environ['BOOYAH_ADMIN_SETUP_KEY']='test-browsers-owner-setup-key-super-long'
os.environ['BOOYAH_ADMIN_TOTP_KEY']=Fernet.generate_key().decode('ascii')
import platform_store as store
import admin_api
import server

teacher=store.create_teacher('teacher-browser-v2@example.org','SecureTeacherPassword2026!',
    'معلم منصة بويا','مدرسة تجريبية للبويا','المهارات الرقمية','boys')
tid=teacher['teacher']['id']
student=store.add_students(tid,[{'name':'طالب بويا','className':'التاسع ب','avatar':'m01'}])[0]
room='J72491'
store.exec_sql("""INSERT INTO played_sessions
 (id,teacher_id,code,section,subject,quiz_title,game_mode,played_at,report,questions)
 VALUES(?,?,?,?,?,?,?,?,?,?)""",
 (uuid.uuid4().hex,tid,room,'التاسع ب','المهارات الرقمية',
 'تحدي المعلومات','individual',int(time.time()),'{}','[]'))
store.exec_sql("""INSERT INTO student_attempts
 (id,teacher_id,student_id,quiz_id,room_code,student_name,class_name,avatar,
  correct_count,question_total,percent,score,answers,created_at)
 VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
 (uuid.uuid4().hex,tid,student['id'],'quiz-1',room,'طالب بويا','التاسع ب',
  'm01',8,10,80,800,'[]',int(time.time())))
http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(http.server_port)
screens=Path('browser-qa-artifacts')
screens.mkdir(exist_ok=True)
email='owner-v2-browser@example.org'
password='StrongOwnerPassword2026!'

def check(condition,message):
    if not condition:
        raise AssertionError(message)

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
    secret=None
    for width,height,mobile in [(1366,820,False),(390,844,True)]:
        ctx=browser.new_context(viewport={'width':width,'height':height},
            is_mobile=mobile,has_touch=mobile,accept_downloads=True)
        page=ctx.new_page()
        errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(base+'/admin.html',wait_until='domcontentloaded')
        if not mobile:
            page.locator('#setupForm').wait_for(state='visible',timeout=15000)
            page.locator('#setupKey').fill(os.environ['BOOYAH_ADMIN_SETUP_KEY'])
            page.locator('#setupName').fill('مالك المنصة')
            page.locator('#setupEmail').fill(email)
            page.locator('#setupPassword').fill(password)
            page.locator('#setupForm button').click()
            page.locator('#activateForm').wait_for(state='visible',timeout=15000)
            secret=page.locator('#totpSecret').inner_text()
            check(len(secret)>30,'2FA secret missing')
            page.locator('#activateOtp').fill(admin_api.totp(secret))
            page.locator('#activateForm button').click()
        page.locator('#loginForm').wait_for(state='visible',timeout=15000)
        page.locator('#loginEmail').fill(email)
        page.locator('#loginPassword').fill(password)
        page.locator('#loginOtp').fill(admin_api.totp(secret))
        page.locator('#loginForm button').click()
        page.locator('#adminApp').wait_for(state='visible',timeout=20000)
        page.locator('.metric').first.wait_for(state='visible',timeout=15000)
        page.locator('#insightBanner').get_by_text('حسابات موقوفة').wait_for(timeout=15000)
        check(page.locator('.metric').count()==4,'KPI cards missing')
        page.screenshot(path=str(screens/('admin-v2-home-mobile.png' if mobile else 'admin-v2-home-desktop.png')),full_page=True)

        def tab(name):
            if mobile:
                page.locator('#menuToggle').click()
            page.locator('[data-view="'+name+'"]').click()

        tab('teachers')
        page.locator('#teachersBody').get_by_text('معلم منصة بويا').wait_for(timeout=15000)
        page.locator('#teacherActivityFilter').select_option('recent')
        page.locator('#teachersBody [data-profile]').first.wait_for(timeout=15000)
        check('آخر نشاط' in page.locator('#teachersView').inner_text(),'Teacher activity missing')
        with page.expect_download(timeout=15000) as info:
            page.locator('#teachersExport').click()
        check(info.value.suggested_filename.endswith('.csv'),'Teacher CSV missing')
        info.value.save_as(str(screens/('teachers-v2-mobile.csv' if mobile else 'teachers-v2-desktop.csv')))
        page.locator('#teachersBody [data-profile]').first.click()
        page.locator('#detailDrawer').wait_for(state='visible')
        page.locator('#detailContent').get_by_text('خطة الوصول:').wait_for(timeout=10000)
        check('مجانية' in page.locator('#detailContent').inner_text(),'Free plan not displayed')
        check('آخر دخول' in page.locator('#detailContent').inner_text(),'Last sign-in absent')
        page.locator('#detailClose').click()

        tab('students')
        page.locator('#studentsBody').get_by_text('طالب بويا').wait_for(timeout=15000)
        page.locator('#studentSearch').fill('طالب بويا')
        page.locator('#studentsBody [data-student]').first.wait_for(timeout=15000)
        with page.expect_download(timeout=15000) as info:
            page.locator('#studentsExport').click()
        check(info.value.suggested_filename.endswith('.csv'),'Student export missing')
        page.locator('#studentsBody [data-student]').first.click()
        page.locator('#detailDrawer').wait_for(state='visible')
        check('80%' in page.locator('#detailContent').inner_text(),'Student grade not shown')
        page.locator('#detailClose').click()

        tab('sessions')
        page.locator('#sessionsBody').get_by_text('تحدي المعلومات').wait_for(timeout=15000)
        page.locator('#sessionSearch').fill('تحدي المعلومات')
        page.locator('#sessionsBody').get_by_text('تحدي المعلومات').wait_for(timeout=15000)
        with page.expect_download(timeout=15000) as info:
            page.locator('#sessionsExport').click()
        check(info.value.suggested_filename.endswith('.csv'),'Session export missing')

        tab('schools')
        page.locator('#schoolsBody [data-school]').first.wait_for(timeout=15000)
        page.locator('#schoolsBody [data-school]').first.click()
        page.locator('#detailContent').get_by_text('معلم منصة بويا').wait_for(timeout=15000)
        page.locator('#detailClose').click()

        if not mobile:
            tab('teachers')
            # Confirm + reason dialogs are required for any administrative write.
            def confirm_and_reason(dialog):
                if dialog.type=='prompt':
                    dialog.accept('اختبار شاشة إيقاف الحساب من Playwright')
                else:
                    dialog.accept()
            page.on('dialog',confirm_and_reason)
            page.locator('#teachersBody [data-status]').first.click()
            page.locator('#teachersBody').get_by_text('موقوف',exact=True).wait_for(timeout=15000)
            page.locator('#teachersBody [data-status]').first.click()
            page.locator('#teachersBody').get_by_text('نشط 7 أيام').wait_for(timeout=15000)
            page.remove_listener('dialog',confirm_and_reason)

        tab('audit')
        page.locator('#auditBody').get_by_text('admin_login').first.wait_for(timeout=15000)
        check(not errors,'Browser JavaScript errors: '+str(errors))
        page.screenshot(path=str(screens/('admin-v2-audit-mobile.png' if mobile else 'admin-v2-audit-desktop.png')),full_page=True)
        page.reload(wait_until='domcontentloaded')
        page.locator('#adminApp').wait_for(state='visible',timeout=15000)
        page.locator('#logoutBtn').click()
        page.locator('#loginForm').wait_for(state='visible',timeout=15000)
        ctx.close()
    browser.close()

http.shutdown()
http.server_close()
print('PASS: dashboard, teacher activity, student detail, school drilldown, sessions, CSV, owner audit, disable/re-enable, desktop/mobile, logout.')
