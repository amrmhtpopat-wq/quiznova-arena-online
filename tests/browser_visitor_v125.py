"""Chromium acceptance: live visit tracking and admin-only counts on desktop and phone."""
import os,sys,tempfile,threading,time
from pathlib import Path
from cryptography.fernet import Fernet
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
TEMP=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(TEMP.name)/'v125-browser.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
os.environ['BOOYAH_ADMIN_SETUP_KEY']='v125-visitor-setup-key-long-isolated-example'
os.environ['BOOYAH_ADMIN_TOTP_KEY']=Fernet.generate_key().decode('ascii')
import server,admin_api,visitor_analytics
HTTP=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=HTTP.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(HTTP.server_port)
screens=Path('browser-qa-artifacts');screens.mkdir(exist_ok=True)
email='owner-visitor-browser@example.org';password='OwnerVisitorBrowserStrongPassword2026!'

def poll(predicate,msg):
    until=time.monotonic()+10
    while time.monotonic()<until:
        if predicate():return
        time.sleep(.1)
    raise AssertionError(msg+': '+str(visitor_analytics.summary()))

def check(cond,msg):
    if not cond:raise AssertionError(msg)

with sync_playwright() as playwright:
    browser=playwright.chromium.launch(headless=True,args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
    visit=context.new_page()
    visit.goto(base+'/',wait_until='domcontentloaded')
    poll(lambda:visitor_analytics.summary()['total']==1,'homepage did not count first visitor')
    visit.goto(base+'/student.html?mode=live',wait_until='domcontentloaded')
    poll(lambda:visitor_analytics.summary()['pageviews']>=2,'student page not counted')
    stats=visitor_analytics.summary()
    check(stats['total']==1 and stats['visits']==1,'same browser should stay one visitor/session')
    visit.reload(wait_until='domcontentloaded')
    poll(lambda:visitor_analytics.summary()['pageviews']>=3,'reload was not counted as a pageview')
    check(visitor_analytics.summary()['total']==1,'reload incorrectly creates a new visitor')
    second_context=browser.new_context(viewport={'width':360,'height':760},is_mobile=True,has_touch=True)
    second=second_context.new_page()
    second.goto(base+'/',wait_until='domcontentloaded')
    poll(lambda:visitor_analytics.summary()['total']==2,'second browser did not add visitor')
    second_context.close();context.close()
    for width,height,mobile in [(1366,820,False),(390,844,True)]:
        ctx=browser.new_context(viewport={'width':width,'height':height},
                                is_mobile=mobile,has_touch=mobile)
        page=ctx.new_page()
        page.goto(base+'/admin.html',wait_until='domcontentloaded')
        if not mobile:
            page.locator('#setupForm').wait_for(state='visible',timeout=12000)
            page.locator('#setupKey').fill(os.environ['BOOYAH_ADMIN_SETUP_KEY'])
            page.locator('#setupName').fill('مدير المنصة')
            page.locator('#setupEmail').fill(email)
            page.locator('#setupPassword').fill(password)
            page.locator('#setupForm button').click()
            page.locator('#activateForm').wait_for(state='visible',timeout=12000)
            secret=page.locator('#totpSecret').inner_text()
            page.locator('#activateOtp').fill(admin_api.totp(secret))
            page.locator('#activateForm button').click()
        page.locator('#loginForm').wait_for(state='visible',timeout=12000)
        page.locator('#loginEmail').fill(email)
        page.locator('#loginPassword').fill(password)
        page.locator('#loginOtp').fill(admin_api.totp(secret))
        page.locator('#loginForm button').click()
        page.locator('#adminApp').wait_for(state='visible',timeout=15000)
        page.locator('#visitorMetrics .visitor-tile').first.wait_for(timeout=15000)
        tiles=page.locator('#visitorMetrics .visitor-tile')
        check(tiles.count()==4,'visitor tiles missing '+str(width))
        labels=[x.inner_text() for x in tiles.all()]
        check('إجمالي الزوار' in labels[0] and '2' in labels[0],'all-time visitor total wrong')
        check('زوار اليوم' in labels[1] and '2' in labels[1],'today counter wrong')
        check('عدد الزيارات' in labels[3] and '2' in labels[3],'session counter wrong')
        check(page.locator('.metric').count()==4,'existing admin indicators changed')
        # The administrator visiting admin.html does not increase the public visitor count.
        check(visitor_analytics.summary()['total']==2,'admin panel incorrectly counted as public traffic')
        m=page.locator('#visitorMetrics').evaluate("""el=>{
          const r=el.getBoundingClientRect();
          return {left:r.left,right:r.right,width:r.width,screen:innerWidth,scroll:document.documentElement.scrollWidth}
        }""")
        check(m['left']>=-2 and m['right']<=width+2 and m['scroll']<=width+3,
              'mobile visitors stats clipped: '+str(m))
        page.screenshot(path=str(screens/('admin-visitor-mobile.png' if mobile else 'admin-visitor-desktop.png')),
                        full_page=True)
        ctx.close()
    browser.close()
HTTP.shutdown();HTTP.server_close()
print('PASS: mobile real page views, anonymous browser deduplication, second browser, owner-only Neon-style stats and desktop/mobile admin panel.')
