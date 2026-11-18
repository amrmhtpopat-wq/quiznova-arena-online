"""TAG Mobile V2 — real Chromium QA at 320/390/768 CSS pixels, no real accounts.

Tests mobile layouts for every public HTML route and that TAG LAB leaves
the installed PWA window via a user-triggered external-browser link.
"""
import os
import sys
import tempfile
import threading
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
tmp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(tmp.name)/'tag-mobile-v2-test.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
from playwright.sync_api import sync_playwright
import server

http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(http.server_port)
ART=Path('browser-qa-artifacts');ART.mkdir(exist_ok=True)

routes=[
 '/about.html','/admin.html','/app.html','/champion-board.html',
 '/champion.html','/for-teachers.html','/game-lab-card.html',
 '/game-lab-create.html','/game-lab-live.html','/game-lab-play.html',
 '/game-lab-preview.html','/','/stage.html','/student.html',
 '/studio.html','/tag-lab-books.html','/tag-lab-create.html',
 '/tag-lab-games.html','/tag-lab-home.html','/tag-lab-library.html',
 '/tag-lab-live.html','/tag-lab-mixer.html','/tag-lab-students.html'
]

with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
 ctx=browser.new_context(viewport={'width':390,'height':844},device_scale_factor=2,
                         is_mobile=True,has_touch=True,service_workers='block')
 page=ctx.new_page()
 offenders=[]
 for i,route in enumerate(routes):
  response=page.goto(BASE+route,wait_until='domcontentloaded',timeout=25000)
  assert response and response.status==200,(route,'HTTP unavailable')
  page.locator('link[href*="tag-mobile-v2.css"]').wait_for(state='attached',timeout=5000)
  page.evaluate('document.fonts.ready')
  measure=page.evaluate("""() => {
    let width=Math.max(document.documentElement.scrollWidth,
                       document.body&&document.body.scrollWidth||0);
    return {width,viewport:window.innerWidth,body:document.body.className};
  }""")
  if measure['width']>measure['viewport']+8:
   offenders.append((route,measure))
  if route in ('/app.html','/','/student.html','/studio.html','/champion.html',
               '/admin.html','/tag-lab-home.html','/game-lab-play.html'):
   page.screenshot(path=str(ART/('tag-mobile-390-'+route.strip('/').replace('/','-').replace('?','')+'.png')),
                   full_page=False)
 print('TAG Mobile 390px document width audit:',offenders,flush=True)
 assert not offenders,'Horizontal overflow on phone: '+repr(offenders)
 for width,targets in [
  (320,['/app.html','/','/student.html','/studio.html','/champion.html',
        '/tag-lab-home.html','/game-lab-play.html']),
  (768,['/app.html','/','/studio.html','/admin.html','/tag-lab-home.html'])
 ]:
  page.set_viewport_size({'width':width,'height':740 if width==320 else 1024})
  over=[]
  for route in targets:
   response=page.goto(BASE+route,wait_until='domcontentloaded',timeout=25000)
   assert response and response.status==200,(width,route,'HTTP unavailable')
   data=page.evaluate("""() => [document.documentElement.scrollWidth,innerWidth]""")
   if data[0]>data[1]+8:over.append((route,data))
  print('TAG Mobile '+str(width)+'px overflow:',over,flush=True)
  assert not over,'Overflow at '+str(width)+': '+repr(over)
 ctx.close()

 # Android standalone: TAG LAB opens in a new browser browsing context,
 # while the four main app sections remain in the installed application.
 android=browser.new_context(viewport={'width':393,'height':852},is_mobile=True,has_touch=True,
                             service_workers='block')
 android.add_init_script("Object.defineProperty(navigator,'standalone',{value:true,configurable:true});")
 home=android.new_page()
 home.goto(BASE+'/app.html',wait_until='domcontentloaded')
 lab=home.locator('a.entry.lab')
 lab.wait_for(state='visible')
 home.wait_for_function("document.querySelector('a.entry.lab')?.target==='_blank'")
 assert lab.get_attribute('rel')=='noopener noreferrer external'
 assert not home.locator('a.entry.student').get_attribute('target')
 with android.expect_page(timeout=12000) as spawned:
  lab.click()
 popup=spawned.value
 popup.wait_for_load_state('domcontentloaded')
 assert '/tag-lab-home.html' in popup.url,popup.url
 assert '/app.html' in home.url,'App home was replaced instead of external handoff'
 popup.locator('#tag-lab-browser-handoff').wait_for(state='visible',timeout=10000)
 assert 'المتصفح' in popup.locator('#tag-lab-browser-handoff h1').inner_text()
 popup.close();android.close()

 # Normal Chrome browser: TAG LAB opens in a separate browser tab;
 # normal pages are not blocked by the standalone-only handoff dialog.
 browserCtx=browser.new_context(viewport={'width':390,'height':844},
                                is_mobile=True,has_touch=True,service_workers='block')
 chrome=browserCtx.new_page()
 chrome.goto(BASE+'/app.html',wait_until='domcontentloaded')
 assert chrome.locator('a.entry.lab').get_attribute('target')=='_blank'
 with browserCtx.expect_page(timeout=12000) as new_tab:
  chrome.locator('a.entry.lab').click()
 lab_tab=new_tab.value
 lab_tab.wait_for_url('**/tag-lab-home.html*',timeout=12000)
 assert not lab_tab.locator('#tag-lab-browser-handoff').count()
 assert '/app.html' in chrome.url
 browserCtx.close()
 browser.close()

http.shutdown();http.server_close()
print('PASS: TAG Mobile V2 all 23 pages, 320/390/768 layouts, mobile browser handoff and normal-browser fallback')
