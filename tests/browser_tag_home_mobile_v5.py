"""TAG Spatial V4 regression: 3D first paint, no legacy flash, direct teacher tools, responsive geometry."""
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
  # V4 replaces the former V5 dashboard with the approved full-width 3D workspace,
  # while retaining the original markup/handlers for a safe failure fallback.
  native=page.locator('#panel-home>.tag-spatial-native-host')
  native.wait_for(state='visible',timeout=15000)
  page.wait_for_function("""() => Boolean(document.querySelector(".tag-spatial-native-host")?.shadowRoot?.getElementById("tag-v3-tools"))""",timeout=10000)
  assert native.locator('.tool[data-tool]').count()==9,(width,'missing teacher instruments')
  assert not page.locator('#panel-home>.hero').is_visible(),(width,'old portal hero flashed')
  assert not page.locator('#workspace>.sidebar').is_visible(),(width,'redundant sidebar on spatial landing')
  assert not page.locator('#workspace>.main>.topbar').is_visible(),(width,'old portal topbar on landing')
  dims=page.evaluate("""() => {
    const host=document.querySelector('.tag-spatial-native-host'),
      header=host.shadowRoot.querySelector('.header').getBoundingClientRect();
    return {width:innerWidth,scroll:document.documentElement.scrollWidth,
      headerY:header.y,headerW:header.width};
  }""")
  assert dims['scroll']<=dims['width']+3,(width,dims)
  assert dims['headerY']<150,(width,'excessive blank space',dims)
  if phone:
   native.locator('[data-tool="cards"]').first.click()
   page.locator('#panel-students.active').wait_for(state='visible',timeout=8000)
  else:
   native.locator('[data-tool="create"]').first.click()
   page.wait_for_url('**/studio.html#builder',timeout=12000)
   page.locator('#view-builder.active').wait_for(state='visible',timeout=12000)
  ctx.close()
 browser.close()
http.shutdown();http.server_close()
print('PASS TAG Spatial V4: consistent native 3D landing, no old hero flash, direct cards and builder routes.')
