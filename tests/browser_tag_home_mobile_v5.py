"""Phone-only TAG V5 dashboard: Chromium layout and desktop isolation checks."""
import os,sys,tempfile,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
tmp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(tmp.name)/'home-v5.sqlite')
os.environ['QUIZNOVA_CLOUD']='1';os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store
import server
store.create_teacher('test-v5@example.org','TestV5Password123!','معلم تجريبي','مدرسة تجريبية','المهارات الرقمية','boys')
http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(http.server_port)
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
 for width in (320,390,430,650,768,1366):
  phone=width<=650
  ctx=browser.new_context(viewport={'width':width,'height':844},is_mobile=phone,has_touch=phone,service_workers='block')
  page=ctx.new_page()
  page.goto(BASE+'/?teacher=1',wait_until='domcontentloaded')
  page.locator('#email').fill('test-v5@example.org')
  page.locator('#password').fill('TestV5Password123!')
  page.locator('#authSubmit').click()
  page.locator('#workspace').wait_for(state='visible',timeout=15000)
  shortcuts=page.locator('#panel-home>.tag-v5-shortcuts')
  assert shortcuts.is_visible()==phone,('shortcuts',width)
  assert page.locator('#panel-home>.hero h2').is_visible()==(not phone),('desktop hero',width)
  assert page.locator('#panel-home>.grid-two').is_visible()==(not phone),('desktop panels',width)
  assert page.locator('.topbar-actions>a.primary').is_visible()==(not phone),('desktop toolbar',width)
  dims=page.evaluate("""() => ({
    width:innerWidth,scroll:document.documentElement.scrollWidth,
    hero:document.querySelector('#panel-home>.hero').getBoundingClientRect().height,
    metrics:getComputedStyle(document.querySelector('#panel-home>.metric-grid')).gridTemplateColumns.split(' ').length
  })""")
  assert dims['scroll']<=dims['width']+3,(width,dims)
  if phone:
   assert dims['hero']<240,(width,dims)
   assert dims['metrics']==2,(width,dims)
   assert page.locator('#panel-home>.hero .tag-v5-start').is_visible(),width
   assert page.locator('#panel-home>.tag-v5-extra').is_visible(),width
   shortcuts.locator('[data-jump=students]').click()
   assert page.locator('#panel-students.active').is_visible(),width
  else:
   assert not page.locator('#panel-home>.hero .tag-v5-start').is_visible(),width
  ctx.close()
 browser.close()
http.shutdown();http.server_close()
print('PASS TAG V5 compact phone dashboard and unchanged desktop/tablet.')
