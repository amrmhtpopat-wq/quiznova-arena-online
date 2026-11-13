"""Interaction Redesign V6: real browser QA for six teacher-led Game Lab games."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**k):super().__init__(*a,directory=str(ROOT),**k)
 def log_message(self,*a):pass

http=ThreadingHTTPServer(('127.0.0.1',0),Handler)
Thread(target=http.serve_forever,daemon=True).start()
url='http://127.0.0.1:'+str(http.server_port)+'/game-lab-preview.html?v=6'
modes=('quiz','fast','truth','pairs','wheel','boxes')
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
  try:
   for width,height in ((1440,900),(390,844)):
    page=browser.new_page(viewport={'width':width,'height':height})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(url,wait_until='domcontentloaded')
    page.locator('#gameGrid .v4-use-template').first.wait_for()
    assert page.locator('#gameGrid .game').count()==24
    assert page.locator('#gameGrid .game .v5-art').count()==24
    for mode in modes:
     launch=page.locator('#gameGrid .game[data-game-mode="'+mode+'"] .button:not(.v4-use-template)').first
     launch.click()
     overlay=page.locator('#playOverlay')
     overlay.wait_for(state='visible')
     page.wait_for_function("(m)=>document.querySelector('#playOverlay')?.dataset.v6Mode===m",mode,timeout=5000)
     body=page.locator('#playBody')
     if mode in ('quiz','fast'):
      assert body.locator('#answers button.choice').count()==4
      assert body.locator('.v6-choice-index').count()==4
      assert body.locator('.v6-question-label').count()>=1
      assert body.locator('.v6-progress').count()==1
      if mode=='fast':
       timer=body.locator('.v6-timer')
       assert timer.count()==1
       assert timer.inner_text().strip().isdigit()
       assert int(timer.inner_text())<=25
       page.wait_for_timeout(1100)
       assert int(timer.inner_text())<=24
      body.locator('#answers button[data-answer="CPU"]').click()
      page.locator('#playStatus[data-v6-result="correct"]').wait_for()
      assert body.locator('#answers .choice.correct').count()==1
      body.locator('#nextWrap .button').click()
      assert body.locator('.playinfo').is_visible()
     elif mode=='truth':
      assert body.locator('#truthActions .choice').count()==2
      assert body.locator('.v6-question-label').count()>=1
      assert body.locator('.v6-choice-index').count()==2
      body.locator('#truthActions .choice').first.click()
      page.wait_for_function("()=>!!document.querySelector('#playStatus').dataset.v6Result")
      assert body.locator('#truthNext .button').count()==1
     elif mode=='pairs':
      assert body.locator('.v6-column-heading').count()==2
      assert body.locator('.matchitem').count()==12
      body.locator('#matchLeft .matchitem').first.click()
      assert body.locator('.matchitem.active').count()==1
      body.locator('#matchRight .matchitem',has_text='CPU').click()
      assert body.locator('.matchitem.done').count()==2
      assert '1 /' in page.locator('#playCounter').inner_text()
     elif mode=='wheel':
      assert body.locator('#spinWheel').count()==1
      assert body.locator('.v6-question-label').count()>=1
      body.locator('#wheelArea button').click()
      body.locator('#wheelReveal h3').wait_for(timeout=6500)
      assert body.locator('#wheelReveal .v6-question-label').count()==1
      body.locator('#wheelReveal button').click()
      page.locator('#playStatus[data-v6-result="reveal"]').wait_for()
     elif mode=='boxes':
      assert body.locator('.mystery').count()==8
      first=body.locator('.mystery').first
      first.click()
      assert first.get_attribute('class').find('open')!=-1
      assert '0 /' not in page.locator('#playCounter').inner_text()
      first.click()
      assert 'v6-solved' in first.get_attribute('class')
     # No horizontal scrolling, even when the question text grows.
     sizes=page.evaluate("()=>({w:innerWidth,scroll:document.documentElement.scrollWidth,overlay:document.querySelector('#playOverlay').scrollWidth,viewport:document.querySelector('#playOverlay').clientWidth})")
     assert sizes['scroll']<=sizes['w']+4,(mode,width,sizes)
     assert sizes['overlay']<=sizes['viewport']+5,(mode,width,sizes)
     page.locator('#closePlay').click()
     overlay.wait_for(state='hidden')
    assert not errors,(width,errors)
    print('PASS V6 six games '+str(width)+'×'+str(height),flush=True)
    page.close()
  finally:browser.close()
finally:http.shutdown();http.server_close()
