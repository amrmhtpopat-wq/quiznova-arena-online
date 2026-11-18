"""TAG PWA V1 installability / offline real Chromium QA on desktop & phone sizes.

Mobile emulation checks layout and install guidance only. Real iPhone Safari
Home Screen installation requires a physical-device user acceptance test.
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
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(tmp.name)/'tag-pwa-browser.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
from playwright.sync_api import sync_playwright
import server

http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(http.server_port)
ART=Path('browser-qa-artifacts');ART.mkdir(exist_ok=True)

profiles=[
 {'name':'desktop','viewport':{'width':1366,'height':768},'is_mobile':False,'has_touch':False},
 {'name':'android','viewport':{'width':393,'height':852},'is_mobile':True,'has_touch':True,
  'user_agent':'Mozilla/5.0 (Linux; Android 15; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36'},
 {'name':'iphone','viewport':{'width':390,'height':844},'is_mobile':True,'has_touch':True,
  'user_agent':'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1'},
]

with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
 for profile in profiles:
  name=profile.pop('name')
  ctx=browser.new_context(**profile,service_workers='allow')
  page=ctx.new_page()
  js_errors=[]
  page.on('pageerror',lambda error:js_errors.append(str(error)))
  response=page.goto(BASE+'/app.html',wait_until='domcontentloaded',timeout=25000)
  assert response.status==200,(name,response.status)
  page.locator('.entry.student').wait_for(state='visible',timeout=15000)
  for dest in ('/student.html','/?teacher=1','/tag-lab-home.html?v=34','/champion.html'):
   assert page.locator('a[href="'+dest+'"]').count()==1,(name,dest)
  assert page.locator('link[rel="manifest"]').get_attribute('href')=='/manifest.webmanifest'
  assert page.locator('link[rel="apple-touch-icon"]').count()==1
  assert page.locator('img[src="/assets/pwa/tag-192.png"]').first.evaluate('(img)=>img.complete&&img.naturalWidth===192'),name
  assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth+2'),name+' horizontal overflow'
  assert not js_errors,(name,js_errors)
  if name=='iphone':
   assert 'Safari' in page.locator('#tagInstallStatus').inner_text()
   assert 'إضافة إلى الشاشة الرئيسية' in page.locator('#tagInstallGuide').inner_text()
  if name=='android':
   assert 'Chrome' in page.locator('#tagInstallStatus').inner_text()
  page.screenshot(path=str(ART/('tag-pwa-'+name+'.png')),full_page=True)
  await_ready=page.evaluate("""async () => {
     if(!('serviceWorker' in navigator))return 'unsupported';
     let r=await Promise.race([
       navigator.serviceWorker.ready.then(reg => reg.active && reg.active.scriptURL),
       new Promise(resolve=>setTimeout(()=>resolve('timeout'),12000))
     ]);
     return r;
  }""")
  assert await_ready and await_ready.endswith('/sw.js'),(name,'SW not ready',await_ready)
  if name=='desktop':
   # Entire cache may hold only generic offline instructions and public app icons.
   stored=page.evaluate("""async () => {
      const result=[];
      for(const key of await caches.keys()){
       const cache=await caches.open(key);
       for(const request of await cache.keys())result.push(new URL(request.url).pathname);
      }
      return result;
   }""")
   assert stored,stored
   assert all((url=='/pwa-offline.html'||url.startswith('/assets/pwa/')) for url in stored),stored
   assert not any('/api/' in url or '/student.html' in url or '/index.html' in url for url in stored),stored
   page.wait_for_function("navigator.serviceWorker.controller!==null",timeout=10000)
   ctx.set_offline(True)
   offline=page.goto(BASE+'/student.html',wait_until='domcontentloaded',timeout=15000)
   assert offline.status==200,offline.status
   assert 'الاتصال بالإنترنت غير متاح' in page.locator('h1').inner_text()
   ctx.set_offline(False)
   page.goto(BASE+'/app.html',wait_until='domcontentloaded')
   page.locator('.entry.student').wait_for(state='visible')
  ctx.close()
 browser.close()

http.shutdown()
http.server_close()
print('PASS: TAG PWA install metadata, 3 viewport sizes, iOS/Android guidance, service worker, offline fallback and private-data cache exclusion')
