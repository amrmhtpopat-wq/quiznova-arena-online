"""TAG results back button: actual previous page, new-tab opener and direct-link fallback."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=(ROOT/'tag-stage-worldcup-v28.js').read_text(encoding='utf-8')
ORIGIN='https://teachgame.onrender.com'
ROOM={'report':[{'name':'طالب 1','score':1200,'avatar':'b01'}],
      'players':[{'name':'طالب 1','score':1200,'avatar':'b01'}],
      'total':10,'status':'finished','playType':'individual'}
def show(page):
 page.add_script_tag(content='window.TAGStageCinema={reset(){}};'+SCRIPT)
 page.evaluate('''room => window.TAGStageWorldCup.finale(room, {
   head:'<div class="stage-head">TAG</div>',
   avatarPath:(avatar)=>'/assets/avatars3d/'+avatar+'.webp'
 })''',ROOM)
 assert page.locator('#tag28Back').inner_text().find('رجوع')>=0
 assert page.locator('#tag28Home').count()==0

def respond(route):
 path=route.request.url.split('?')[0]
 if path.endswith('/stage.html'):
  body='<html lang="ar" dir="rtl"><body class="v105-stage" data-stage-view="finished"><main id="stage"></main></body></html>'
 else:
  body='<html lang="ar"><body><h1 id="source">صفحة المعلم</h1></body></html>'
 route.fulfill(status=200,content_type='text/html',body=body)

with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
 ctx=browser.new_context()
 ctx.route(ORIGIN+'/**',respond)
 # Same-tab navigation must go to the exact prior teacher page, not the home page.
 p=ctx.new_page()
 p.goto(ORIGIN+'/champion.html')
 p.goto(ORIGIN+'/stage.html?code=123456')
 show(p)
 p.locator('#tag28Back').click()
 p.wait_for_url(ORIGIN+'/champion.html',timeout=6000)
 assert p.locator('#source').is_visible()
 p.close()
 # Open in new tab: no prior history, but the opening teacher page is the referrer.
 teacher=ctx.new_page()
 teacher.goto(ORIGIN+'/studio.html')
 with teacher.expect_popup() as popup:
  teacher.evaluate("window.open('/stage.html?code=123456','_blank')")
 child=popup.value
 child.wait_for_load_state()
 show(child)
 child.locator('#tag28Back').click()
 child.wait_for_url(ORIGIN+'/studio.html',timeout=6000)
 assert child.locator('#source').is_visible()
 teacher.close()
 child.close()
 # A pasted/bookmarked stage URL has no previous page: safe teacher-workspace fallback.
 direct=ctx.new_page()
 direct.goto(ORIGIN+'/stage.html?code=123456')
 show(direct)
 direct.locator('#tag28Back').click()
 direct.wait_for_url(ORIGIN+'/studio.html',timeout=6000)
 assert direct.locator('#source').is_visible()
 direct.close()
 ctx.close()
 browser.close()
print('PASS TAG previous-page button: same tab, new tab/referrer, and direct-link fallback')
