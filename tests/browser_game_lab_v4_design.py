"""BOOYAHJO Game Lab V4: classroom-first Wordwall-inspired visual and behavior QA."""
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'browser-qa-artifacts';OUT.mkdir(exist_ok=True)

class StaticHandler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
 def log_message(self,*args):pass

http=ThreadingHTTPServer(('127.0.0.1',0),StaticHandler)
Thread(target=http.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(http.server_port)
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
  try:
   for width,height in ((1440,900),(1280,720),(390,844),(360,740)):
    page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(base+'/game-lab-preview.html',wait_until='domcontentloaded')
    page.locator('#v4QuickStart .v4-quick-card').first.wait_for(state='visible')
    assert page.locator('#v4QuickStart .v4-quick-card').count()==3
    assert page.locator('#gameGrid .game').count()==24
    page.wait_for_function("()=>document.querySelectorAll('#gameGrid .v4-use-template').length===24",timeout=10000)
    assert page.locator('#gameGrid .v4-use-template').count()==24
    assert page.locator('#v4Title').is_visible()
    assert page.locator('#v4ThemeToggle').is_visible() or width<=900
    light=page.evaluate("()=>({scheme:getComputedStyle(document.documentElement).colorScheme,card:getComputedStyle(document.querySelector('.game')).backgroundColor,w:innerWidth,scroll:document.documentElement.scrollWidth})")
    assert light['scheme']=='light',light
    assert light['card']=='rgb(255, 255, 255)',light
    assert light['scroll']<=light['w']+3,(width,light)
    page.locator('#gameGrid .game[data-game-mode="pairs"] .v4-use-template').click()
    assert 'مطابقة' in page.locator('#v4ChosenTemplate').inner_text()
    assert page.locator('#cloudMode').input_value()=='pairs'
    page.locator('#v4TrySelected').click()
    page.locator('#playOverlay').wait_for(state='visible',timeout=5000)
    assert 'توصيل الأزواج' in page.locator('#playTitle').inner_text()
    assert page.locator('#playBody').is_visible()
    page.locator('#closePlay').click()
    page.locator('#playOverlay').wait_for(state='hidden',timeout=4000)
    page.locator('#v4ThemeToggle').click()
    assert page.locator('body').get_attribute('data-lab-theme')=='projector'
    page.locator('#v4ThemeToggle').click()
    assert page.locator('body').get_attribute('data-lab-theme')=='comfort'
    page.evaluate('()=>window.scrollTo(0,0)')
    page.screenshot(path=str(OUT/('game-lab-v4-'+str(width)+'.png')),full_page=False,animations='disabled')
    assert not errors,(width,errors)
    page.close()
    print('PASS GameLab V4 '+str(width)+'x'+str(height)+' visual UI, safe template selection and game launch',flush=True)
   for filename,body in (('game-lab-card.html','lab-v4-card'),('game-lab-play.html','lab-v4-play'),('game-lab-live.html','lab-v4-live')):
    page=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(base+'/'+filename,wait_until='domcontentloaded')
    assert page.locator('body').get_attribute('class')==body
    assert page.locator('.wrap').is_visible()
    sizes=page.evaluate('()=>({screen:innerWidth,scroll:document.documentElement.scrollWidth})')
    assert sizes['scroll']<=sizes['screen']+3,(filename,sizes)
    assert page.locator('link[href="/game-lab-v4-student.css?v=4.0"]').count()==1
    page.screenshot(path=str(OUT/(filename.replace('.html','')+'-v4-mobile.png')),full_page=False,animations='disabled')
    assert not errors,(filename,errors)
    page.close()
    print('PASS V4 '+filename+' responsive student presentation',flush=True)
  finally:browser.close()
finally:http.shutdown();http.server_close()
