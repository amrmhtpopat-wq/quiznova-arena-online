"""Real browser QA for BOOYAHJO owner control center on desktop and phone."""
import os
import sys
import tempfile
import threading
import uuid
from pathlib import Path
from cryptography.fernet import Fernet
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright

TEMP=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(TEMP.name)/'admin-browser.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
os.environ['BOOYAH_ADMIN_SETUP_KEY']='browser-test-unique-long-admin-setup-key'
os.environ['BOOYAH_ADMIN_TOTP_KEY']=Fernet.generate_key().decode('ascii')
import platform_store as store
import admin_api
import server

teacher=store.create_teacher('admin-browser-'+uuid.uuid4().hex+'@example.org',
                             'TeacherSecurePass999!', 'أستاذ تجريبي', 'مدرسة الملك عبدالله',
                             'المهارات الرقمية', 'boys')
store.add_students(teacher['teacher']['id'],[{'name':'طالب تجربة','className':'التاسع ب','avatar':'m01'}])
app=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=app.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(app.server_port)
screens=Path('browser-qa-artifacts')
screens.mkdir(exist_ok=True)
email='admin-browser-owner@example.org'
password='StrongAdminPass2026!'

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
    for width,height,mobile in [(1366,820,False),(390,844,True)]:
        ctx=browser.new_context(viewport={'width':width,'height':height},
                                is_mobile=mobile,has_touch=mobile)
        page=ctx.new_page()
        errors=[]
        page.on('pageerror',lambda err:errors.append(str(err)))
        page.goto(base+'/admin.html',wait_until='domcontentloaded')
        if not mobile:
            page.locator('#setupForm').wait_for(state='visible',timeout=16000)
            page.locator('#setupKey').fill(os.environ['BOOYAH_ADMIN_SETUP_KEY'])
            page.locator('#setupName').fill('مالك المنصة')
            page.locator('#setupEmail').fill(email)
            page.locator('#setupPassword').fill(password)
            page.locator('#setupForm .button-primary').click()
            page.locator('#activateForm').wait_for(state='visible',timeout=16000)
            secret=page.locator('#totpSecret').inner_text()
            assert len(secret)>=30
            page.locator('#activateOtp').fill(admin_api.totp(secret))
            page.locator('#activateForm button').click()
            page.locator('#loginForm').wait_for(state='visible',timeout=13000)
        else:
            page.locator('#loginForm').wait_for(state='visible',timeout=13000)
        page.locator('#loginEmail').fill(email)
        page.locator('#loginPassword').fill(password)
        page.locator('#loginOtp').fill(admin_api.totp(secret))
        page.locator('#loginForm button').click()
        page.locator('#adminApp').wait_for(state='visible',timeout=16000)
        page.locator('.metric').first.wait_for(state='visible',timeout=12000)
        assert page.locator('.metric').count()==4
        assert 'Neon' in page.locator('#databaseBadge').inner_text() or 'SQLite' in page.locator('#databaseBadge').inner_text()
        assert 'TeachGame' in page.locator('.sidebar-brand').inner_text()
        assert 'الطلاب' in page.locator('#metricsGrid').inner_text()
        page.screenshot(path=str(screens/('admin-home-phone.png' if mobile else 'admin-home-desktop.png')),full_page=True)
        if mobile:page.locator('#menuToggle').click()
        page.locator('[data-view="teachers"]').click()
        page.locator('#teachersBody').get_by_text('أستاذ تجريبي').wait_for(state='visible',timeout=12000)
        assert 'أستاذ تجريبي' in page.locator('#teachersBody').inner_text()
        page.locator('#teacherSearch').fill('الملك عبدالله')
        page.locator('#teachersBody tr').first.wait_for(state='visible',timeout=12000)
        assert page.locator('[data-status]').count()==1
        if mobile:page.locator('#menuToggle').click()
        page.locator('[data-view="schools"]').click()
        page.locator('#schoolsBody').get_by_text('مدرسة الملك عبدالله').wait_for(state='visible',timeout=12000)
        assert 'مدرسة الملك عبدالله' in page.locator('#schoolsBody').inner_text()
        if mobile:page.locator('#menuToggle').click()
        page.locator('[data-view="audit"]').click()
        page.locator('#auditBody').get_by_text('admin_login').first.wait_for(state='visible',timeout=12000)
        assert 'admin_login' in page.locator('#auditBody').inner_text()
        assert not errors,errors
        page.reload(wait_until='domcontentloaded')
        page.locator('#adminApp').wait_for(state='visible',timeout=12000)
        page.locator('#logoutBtn').click()
        page.locator('#loginForm').wait_for(state='visible',timeout=12000)
        page.screenshot(path=str(screens/('admin-logout-phone.png' if mobile else 'admin-logout-desktop.png')),full_page=True)
        ctx.close()
    browser.close()
app.shutdown()
app.server_close()
print('PASS: owner setup/TOTP, dashboard KPI, teacher search, school list, audit, reload and logout (desktop/mobile).')
