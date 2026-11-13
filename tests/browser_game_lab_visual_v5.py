"""QA Game Lab V5: rendered artwork, simple question entry, navigation & contrast."""
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class StaticHandler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kw):super().__init__(*args,directory=str(ROOT),**kw)
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),StaticHandler)
Thread(target=server.serve_forever,daemon=True).start()
URL='http://127.0.0.1:'+str(server.server_port)+'/game-lab-preview.html'
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
  try:
   for w,h in [(1440,900),(390,844)]:
    page=browser.new_page(viewport={'width':w,'height':h},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(URL,wait_until='domcontentloaded')
    page.locator('#gameGrid .game[data-v5-enhanced="1"]').first.wait_for()
    assert page.locator('#gameGrid .game .v5-art').count()==24
    assert page.locator('#gameGrid .game .v4-use-template').count()==24
    assert page.locator('#v5QuickEditor').is_visible()
    assert page.locator('#v5QuestionList .v5-question').count()==8
    assert page.locator('#v5BulkBox').get_attribute('open') is None
    page.locator('#v5Add').click()
    assert page.locator('#v5QuestionList .v5-question').count()==9
    q=page.locator('#v5QuestionList .v5-question').last
    q.locator('input[name=q]').fill('ما وظيفة لوحة المفاتيح؟')
    q.locator('input[name=a]').fill('إدخال النصوص')
    assert 'ما وظيفة لوحة المفاتيح؟ | إدخال النصوص' in page.locator('#activityData').input_value()
    assert 'إدخال النصوص' in page.locator('#activityData').input_value()
    q.locator('button[data-remove]').click()
    assert page.locator('#v5QuestionList .v5-question').count()==8
    page.locator('#gameGrid .game[data-game-mode="wheel"] .v4-use-template').click()
    assert 'عجلة' in page.locator('#v4ChosenTemplate').inner_text()
    page.locator('#v4TrySelected').click()
    page.locator('#playOverlay').wait_for(state='visible')
    # Keep dark text on white surfaces for teachers; a former bug hid the answer.
    colors=page.evaluate("""() => ({
      card:getComputedStyle(document.querySelector('#playOverlay .playcard')).color,
      game:getComputedStyle(document.querySelector('#gameGrid .game h3')).color,
      scroll:document.documentElement.scrollWidth, width:innerWidth
    })""")
    assert colors['scroll']<=colors['width']+3,colors
    assert colors['card']!='rgb(255, 255, 255)',colors
    page.locator('#closePlay').click()
    assert not errors,(w,errors)
    page.close()
    print('PASS V5 '+str(w)+'x'+str(h),flush=True)
  finally:browser.close()
finally:server.shutdown();server.server_close()
