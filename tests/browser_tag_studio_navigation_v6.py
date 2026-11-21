"""TAG Studio Navigation V6 — physical phone, tablet and desktop acceptance.

Ensures 4 grouped sections remain fully usable, the off-canvas drawer never
extends outside the viewport, and teacher page routes/quiz state are unchanged.
"""
import os,sys,tempfile,threading,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
tmp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(tmp.name)/'tag-studio-navigation-v6.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store
import server
teacher=store.create_teacher('nav-v6@example.org','TAGStudioNavStrongPass123!',
 'معلم الاختبار','مدرسة تجريبية','المهارات الرقمية','boys')
http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(http.server_port)
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
 for width,height in ((320,640),(390,844),(430,932),(768,1024),(1024,768),(1366,768)):
  phone=width<=430
  ctx=browser.new_context(viewport={'width':width,'height':height},
      is_mobile=phone,has_touch=phone,service_workers='block')
  ctx.add_init_script('localStorage.setItem("qn9_teacher_token",'+json.dumps(teacher['token'])+');')
  page=ctx.new_page();errors=[]
  page.on('pageerror',lambda error:errors.append(str(error)))
  page.goto(BASE+'/studio.html#dashboard',wait_until='domcontentloaded',timeout=25000)
  page.locator('#view-dashboard.active').wait_for(state='visible',timeout=25000)
  page.wait_for_function("document.querySelectorAll('#sidebar .tag-studio-nav-group').length===4 && document.querySelector('#menuBtn').getAttribute('aria-expanded')==='false' && document.querySelector('#sidebar').inert==="+str(width<=1024).lower(),timeout=20000)
  assert page.locator('#sidebar .tag-studio-nav-group').count()==4,(width,'missing groups')
  assert page.locator('#sidebar .nav-item[data-view]').count()==10,(width,'lost teacher pages')
  assert page.locator('#view-dashboard .tag-studio-quickhub-grid>button').count()==4
  assert page.locator('#sidebar .tag-studio-external-link').count()==3
  assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 3'),(width,'horizontal overflow on initial page')
  if width<=1024:
   assert page.locator('#menuBtn').is_visible(),(width,'no mobile nav opener')
   assert page.locator('#tagStudioNavBackdrop').is_hidden(),(width,'backdrop visible before opening')
   assert not page.locator('#sidebar').is_visible(),(width,'closed drawer should not be visible')
   page.locator('#menuBtn').click()
   page.wait_for_function("document.querySelector('#sidebar').classList.contains('open')")
   page.locator('#sidebar').wait_for(state='visible',timeout=7500)
   assert page.locator('#menuBtn').get_attribute('aria-expanded')=='true'
   assert page.locator('#sidebar').is_visible()
   assert page.locator('#tagStudioNavBackdrop').is_visible()
   bbox=page.locator('#sidebar').bounding_box()
   assert bbox['x']>=-2 and bbox['x']+bbox['width']<=width+2,(width,'drawer overflow',bbox)
   assert bbox['height']<=height+2,(width,'drawer exceeds viewport',bbox)
   assert page.locator('#tagStudioGroup-start').is_visible()
   assert not page.locator('#tagStudioGroup-content').is_visible()
   page.locator('[data-tag-studio-group="content"] .tag-studio-group-toggle').click()
   assert page.locator('#tagStudioGroup-content').is_visible()
   assert not page.locator('#tagStudioGroup-start').is_visible()
   page.locator('#tagStudioGroup-content button[data-view="library"]').click()
   page.locator('#view-library.active').wait_for(state='visible',timeout=13000)
   assert page.locator('#menuBtn').get_attribute('aria-expanded')=='false'
   assert page.locator('#sidebar').is_hidden()
   assert page.locator('#tagStudioNavBackdrop').is_hidden()
   assert not page.locator('body').evaluate("el=>el.classList.contains('tag-studio-nav-open')")
   page.locator('#menuBtn').click()
   assert page.locator('[data-tag-studio-group="content"]').get_attribute('class').find('is-expanded')>=0,(width,'active group not remembered')
   assert page.locator('#tagStudioGroup-content').is_visible()
   page.keyboard.press('Escape')
   assert page.locator('#menuBtn').get_attribute('aria-expanded')=='false'
   assert page.locator('#tagStudioNavBackdrop').is_hidden()
   assert page.evaluate("document.activeElement?.id==='menuBtn'"),(width,'keyboard focus not returned')
   page.locator('#menuBtn').click()
   page.locator('#tagStudioNavBackdrop').click(position={'x':4,'y':4},force=True)
   assert page.locator('#sidebar').is_hidden()
  else:
   assert not page.locator('#menuBtn').is_visible(),(width,'desktop drawer button should be hidden')
   assert page.locator('#sidebar').is_visible()
   assert page.locator('#tagStudioNavBackdrop').is_hidden()
   for group in ('start','content','classroom','manage'):
    assert page.locator('#tagStudioGroup-'+group).is_visible(),(width,group)
   page.locator('#tagStudioGroup-content button[data-view="library"]').click()
   page.locator('#view-library.active').wait_for(state='visible',timeout=13000)
  # Existing hash-based navigation and a teacher's saved-quiz view must survive.
  page.evaluate("go('dashboard')")
  page.locator('#view-dashboard.active').wait_for(state='visible')
  page.locator('#view-dashboard .tag-studio-quickhub [data-jump="generator"]').click()
  page.locator('#view-generator.active').wait_for(state='visible')
  assert page.url.endswith('#generator')
  assert not errors,(width,errors)
  ctx.close()
 browser.close()
http.shutdown();http.server_close()
print('PASS TAG Studio Navigation V6: grouped page map, off-canvas phone/tablet drawer, focus, route navigation and desktop visibility at 320/390/430/768/1024/1366.')
