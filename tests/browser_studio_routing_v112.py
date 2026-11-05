"""Browser regression: studio deep links must survive login and transient auth failures."""
import os,sys,tempfile,threading,uuid,time
from pathlib import Path
from urllib.parse import urlparse,parse_qs
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright

tmp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(tmp.name)/'routing.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store
store.init()
import server
http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(http.server_port)
email='studio-route-'+uuid.uuid4().hex+'@example.org'
password='SecureTestPass123!'
account=store.create_teacher(email,password,'Teacher Redirect','مدرسة تجريبية للبنين','المهارات الرقمية','boys')

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
    # A copied library link without an existing session returns to that exact
    # section after signing in. It must not strand the user at the dashboard.
    ctx=browser.new_context(viewport={'width':1200,'height':750})
    page=ctx.new_page()
    page.goto(base+'/studio.html#library',wait_until='domcontentloaded')
    page.wait_for_url('**/?next=*')
    pending=parse_qs(urlparse(page.url).query)['next'][0]
    assert pending=='/studio.html#library',pending
    page.locator('#email').fill(email)
    page.locator('#password').fill(password)
    page.locator('#authSubmit').click()
    page.wait_for_url('**/studio.html#library')
    page.locator('#view-library.active').wait_for(state='visible')
    assert page.evaluate('localStorage.getItem("qn9_teacher_token")')
    ctx.close()

    # A transient single 401 from one backend API is retried and not treated
    # as a user logout; preserve the requested builder hash.
    ctx=browser.new_context(viewport={'width':1200,'height':750})
    ctx.add_init_script("localStorage.setItem('qn9_teacher_token',"+repr(account['token'])+");")
    page=ctx.new_page()
    count={'bad':0}
    def maybe_one_401(route):
        count['bad']+=1
        if count['bad']==1:
            route.fulfill(status=401,content_type='application/json',body='{"ok":false,"error":"login_required"}')
        else:route.continue_()
    page.route('**/api/auth/me',maybe_one_401)
    page.goto(base+'/studio.html#builder',wait_until='domcontentloaded')
    page.locator('#view-builder.active #quizTitle').wait_for(state='visible',timeout=20000)
    assert page.url.endswith('#builder'),page.url
    assert count['bad']>=2,count
    assert page.evaluate('localStorage.getItem("qn9_teacher_token")')==account['token']
    page.locator('button[data-view="library"]').click()
    assert page.url.endswith('#library')
    page.reload(wait_until='domcontentloaded')
    page.locator('#view-library.active').wait_for(state='visible',timeout=15000)
    ctx.close()

    # With a permanently missing session, preserve the library destination
    # while asking the user to log in.
    ctx=browser.new_context()
    ctx.add_init_script("localStorage.setItem('qn9_teacher_token','invalid-session');")
    page=ctx.new_page()
    page.goto(base+'/studio.html#live',wait_until='domcontentloaded')
    page.wait_for_url('**/?next=*',timeout=15000)
    assert parse_qs(urlparse(page.url).query)['next'][0]=='/studio.html#live'
    ctx.close()
    browser.close()

http.shutdown();http.server_close()
print('PASS: deep link login, mixed 401 retry, hash restore after reload, and invalid session redirect.')
