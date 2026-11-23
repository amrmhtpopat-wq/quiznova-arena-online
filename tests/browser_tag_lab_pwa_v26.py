"""TAG V26: installed iOS/Android PWA keeps TAG LAB navigation in-app."""
import sys, tempfile, os, threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
temp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(temp.name)/'qa.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import server
srv=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=srv.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(srv.server_port)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
 for device in ('iphone-standalone','android-standalone','desktop'):
  mobile=device!='desktop'
  ctx=browser.new_context(viewport={'width':390 if mobile else 1280,'height':844 if mobile else 800},
    is_mobile=mobile,has_touch=mobile,service_workers='block')
  if device=='iphone-standalone':
   ctx.add_init_script("Object.defineProperty(navigator,'standalone',{configurable:true,value:true})")
  if device=='android-standalone':
   ctx.add_init_script("""(()=>{
    const original=window.matchMedia.bind(window);
    window.matchMedia=(q)=>q.includes('display-mode: standalone')?
      {matches:true,media:q,addListener(){},removeListener(){},
       addEventListener(){},removeEventListener(){}}:original(q);
   })()""")
  page=ctx.new_page();errors=[];popups=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('popup',lambda popup:popups.append(popup.url))
  page.goto(base+'/app.html',wait_until='domcontentloaded')
  lab=page.locator('a.entry.lab')
  lab.wait_for(state='visible',timeout=10000)
  assert lab.get_attribute('target') is None,('external target',device)
  assert lab.get_attribute('data-tag-lab-entry')=='internal',device
  lab.click()
  page.wait_for_url('**/tag-lab-home.html?v=34',timeout=15000)
  assert not popups,('unexpected popup',device,popups)
  assert page.locator('h1').first.is_visible(),device
  assert page.locator('#tag-lab-browser-handoff').count()==0,device
  assert page.locator('a[href="/tag-lab-create.html"]').count()>0,device
  page.go_back()
  page.wait_for_url('**/app.html',timeout=12000)
  assert not errors,(device,errors)
  print('PASS',device,'in-app TAG LAB and history back',flush=True)
  ctx.close()
 browser.close()
srv.shutdown();srv.server_close()
