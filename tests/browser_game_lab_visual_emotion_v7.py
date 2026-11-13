"""Visual Emotion V7 QA: verify real game interactions on desktop and mobile."""
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'browser-qa-artifacts';OUT.mkdir(exist_ok=True)

class StaticHandler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
 def log_message(self,*a):pass

http=ThreadingHTTPServer(('127.0.0.1',0),StaticHandler)
Thread(target=http.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(http.server_port)+'/game-lab-preview.html?v=7'

try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
  try:
   for width,height in [(1440,900),(390,844),(360,740)]:
    page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(base,wait_until='domcontentloaded')
    assert page.locator('#gameGrid .game').count()==24
    assert page.locator('#gameGrid .v5-art').count()==24
    for mode in ['quiz','fast','truth']:
     page.locator('#gameGrid .game[data-game-mode="'+mode+'"] .button:not(.v4-use-template)').first.click()
     overlay=page.locator('#playOverlay')
     overlay.wait_for(state='visible')
     page.wait_for_function("(id)=>document.querySelector('#playOverlay')?.dataset.v7Mode===id",arg=mode,timeout=7500)
     assert overlay.evaluate("(node)=>node.classList.contains('v6-game')&&node.classList.contains('v7-game')")
     assert overlay.locator('.v7-ambience').count()==1
     assert overlay.locator('.v7-logo').count()==1
     assert overlay.locator('.v7-victory').count()==1
     hero=page.locator('#playBody > .playcard')
     hero.locator('.v7-mascot svg').wait_for()
     assert hero.locator('.v7-question-content h3').count()==1
     assert hero.locator('.v6-question-label').count()==1
     assert page.locator('#playBody .v6-progress').count()==1
     assert page.locator('#playBody .playchoices .choice').count()==(2 if mode=='truth' else 4)
     assert page.locator('#playBody .playchoices .choice .v7-choice-spark').count()==(2 if mode=='truth' else 4)
     if mode=='truth':
      assert hero.locator('.v7-question-content h2').count()==1
      assert 'صح' in page.locator('#truthActions .choice').first.inner_text()
      assert 'خطأ' in page.locator('#truthActions .choice').last.inner_text()
     else:
      assert hero.locator('.v7-question-content h2').count()==0
     if mode=='fast':
      dial=page.locator('#playBody .v6-timer')
      assert dial.count()==1
      first=int(dial.inner_text())
      page.wait_for_timeout(1050)
      assert int(dial.inner_text())<first,(first,dial.inner_text())
     layout=page.evaluate("""() => {
      const o=document.querySelector('#playOverlay');
      const s=document.querySelector('#playBody .playchoices .choice');
      const q=document.querySelector('#playBody .playcard h3');
      return {
       outer:document.documentElement.scrollWidth,
       width:window.innerWidth,
       ovw:o.scrollWidth,ovclient:o.clientWidth,
       answerColor:getComputedStyle(s).color,
       answerBackground:getComputedStyle(s).backgroundImage,
       questionColor:getComputedStyle(q).color,
       questionText:q.textContent,
       cardWidth:s.getBoundingClientRect().width
      };
     }""")
     assert layout['outer']<=layout['width']+4,(mode,width,layout)
     assert layout['ovw']<=layout['ovclient']+5,(mode,width,layout)
     assert layout['answerColor']=='rgb(255, 255, 255)',(mode,width,layout)
     assert 'gradient' in layout['answerBackground'],layout
     assert layout['questionColor']!='rgb(255, 255, 255)',layout
     assert layout['cardWidth']>95,layout
     page.screenshot(path=str(OUT/('gamelab-v7-'+mode+'-'+str(width)+'.png')),animations='disabled')
     if mode in ('quiz','fast'):
      page.locator('#answers button[data-answer="CPU"]').click()
      page.locator('#playStatus[data-v6-result="correct"]').wait_for()
      page.locator('#answers .choice.correct').wait_for()
      assert page.locator('#playBody .playinfo > b').inner_text().find('100')!=-1
      page.locator('#playBody #nextWrap .button').click()
      page.locator('#playBody .v7-mascot svg').wait_for()
      assert page.locator('#playBody .playchoices .choice').count()==4
      assert page.locator('#playBody .v6-progress').count()==1
     else:
      page.locator('#truthActions .choice').first.click()
      page.locator('#truthNext .button').wait_for()
      assert page.locator('#truthActions .choice.correct').count()==1
      page.locator('#truthNext .button').click()
      page.locator('#playBody .v7-mascot svg').wait_for()
     page.locator('#closePlay').click()
     overlay.wait_for(state='hidden')
     page.wait_for_function("()=>!document.querySelector('#playOverlay').classList.contains('v7-game')",timeout=2500)
    assert not errors,(width,errors)
    print('PASS V7 responsive, scoring, animations and contrast '+str(width)+'x'+str(height),flush=True)
    page.close()
  finally:browser.close()
finally:http.shutdown();http.server_close()
