"""TAG V28 World Cup finale: isolated browser regression without live student data.
Runs in Chrome/Chromium; does not contact production or modify any room.
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
STYLE=(ROOT/'tag-stage-worldcup-v28.css').read_text(encoding='utf-8')
SCRIPT=(ROOT/'tag-stage-worldcup-v28.js').read_text(encoding='utf-8')
BASE='''html,body{margin:0;padding:0;height:100%;font-family:Tahoma,Arial;background:#091629;color:white}
*{box-sizing:border-box}.stage-head{display:flex;align-items:center;gap:12px}
.pin{margin-inline-start:auto}.bo-fullscreen{padding:5px 10px}'''

DATA=[
 {'name':'أحمد','score':2450,'avatar':'b01'},
 {'name':'محمد','score':2220,'avatar':'b02'},
 {'name':'عمر','score':1980,'avatar':'b03'},
 {'name':'يوسف','score':1850,'avatar':'b04'},
 {'name':'خالد','score':1720,'avatar':'b05'}
]
JS_INIT='''(room) => {
 const parts={head:'<div class="stage-head"><div class="brand">TAG</div><div class="pin">PIN 123456</div></div>',
 avatarPath:()=>'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2298%22 height=%2298%22%3E%3Ccircle cx=%2249%22 cy=%2249%22 r=%2245%22 fill=%22%23aed9e5%22/%3E%3C/svg%3E'};
 window.TAGStageWorldCup.finale(room,parts);
}'''

with sync_playwright() as playwright:
 browser=playwright.chromium.launch(headless=True,
  **({'executable_path':os.environ['CHROME_PATH']} if os.getenv('CHROME_PATH') else {}),
  args=['--no-sandbox'])
 for width,height in [(1366,768),(390,844),(375,667)]:
  page=browser.new_page(viewport={'width':width,'height':height},service_workers='block')
  errors=[]
  page.on('pageerror',lambda err:errors.append(str(err)))
  page.set_content('<html lang="ar" dir="rtl"><body class="v105-stage" data-stage-view="finished"><div id="stage"></div></body></html>')
  page.add_style_tag(content=BASE+'\n'+STYLE)
  page.add_script_tag(content='window.TAGStageCinema={reset(){}};'+SCRIPT)
  room={'playType':'individual','status':'finished','report':DATA,'players':DATA,'total':20}
  page.evaluate(JS_INIT,room)
  assert page.locator('.tag28-finale').count()==1
  assert page.locator('.tag28-winner').count()==3
  assert page.locator('.tag28-sidecard').count()==2
  assert page.locator('.tag28-stat').count()==3
  assert page.locator('.tag28-person-head img').count()==3
  assert page.locator('.tag28-place-1 .tag27-podium-name').inner_text()=='أحمد'
  # Show the podium in third → second → first order on an actual browser timer.
  page.wait_for_function("document.querySelector('.tag28-place-3')?.classList.contains('tag28-visible')",timeout=3000)
  assert not page.locator('.tag28-place-1').evaluate("el=>el.classList.contains('tag28-visible')")
  page.wait_for_function("document.querySelector('.tag28-place-2')?.classList.contains('tag28-visible')",timeout=5000)
  page.wait_for_function("document.querySelector('.tag28-place-1')?.classList.contains('tag28-visible')",timeout=7500)
  page.wait_for_timeout(1100)
  metrics=page.evaluate('''() => {
   const r=e=>{const b=e.getBoundingClientRect();return {top:b.top,bottom:b.bottom,left:b.left,right:b.right}};
   return {w:document.documentElement.scrollWidth,h:document.documentElement.scrollHeight,
    podiums:[...document.querySelectorAll('.tag28-winner')].map(r),footer:r(document.querySelector('.tag28-actions'))};
  }''')
  assert metrics['w']<=width+2 and metrics['h']<=height+2,(width,height,metrics)
  assert all(0<=p['left'] and p['right']<=width+3 for p in metrics['podiums']),(width,metrics)
  assert metrics['footer']['bottom']<=height+3,(width,metrics)
  page.locator('#tag28All').click()
  assert page.locator('#tag28AllPanel').is_visible()
  assert page.locator('.tag28-all-row').count()==5
  assert page.locator('.tag28-all-name').all_text_contents()==[r['name'] for r in DATA]
  page.keyboard.press('Escape')
  assert page.locator('#tag28AllPanel').is_hidden()
  page.locator('#tag27Replay').click()
  page.wait_for_function("document.querySelector('.tag28-place-3')?.classList.contains('tag28-visible')",timeout=3000)
  page.locator('#tag28Skip').click()
  assert all(page.locator(f'.tag28-place-{i}').evaluate("el=>el.classList.contains('tag28-visible')") for i in (1,2,3))
  assert 'بطل TAG' in page.locator('#tag28Announcement').inner_text()
  assert not errors,(width,errors)
  print('PASS TAG V28',width,height,'cinematic order, genuine ranked data, sidebar, modal, replay, skip, viewport')
  page.close()
 browser.close()