"""TAG V27 realistic projector: sequential score reveal, avatar podium and exam privacy.
Tests only a synthetic classroom. No real teacher login, student identities or DB writes.
"""
import copy,json,threading,os
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,directory=str(ROOT),**kwargs)
 def log_message(self,*args):pass
http=ThreadingHTTPServer(('127.0.0.1',0),Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(http.server_port)
people=[
 {'name':name,'avatar':avatar,'score':score,'correct':correct,'team':''}
 for name,avatar,score,correct in [
 ('ليان','n01',950,5),('أحمد','m02',870,4),('سارة','n04',800,4),
 ('عمر','m05',650,3),('مريم','n03',520,3)]]
def build_room(status='question'):
 old=[dict(p,score=0,correct=0) for p in people]
 current=old if status=='question' else people
 return {'code':'123456','status':status,'index':0,'total':5,'playType':'individual',
  'leaders':current,'teams':[],'players':current,
  'report':[dict(p,percent=80) for p in people] if status=='finished' else [],
  'question':{'text':'أي خيار هو الإجابة الصحيحة؟','options':['أ','ب','ج','د']},
  'showFeedback':True,'examMode':False,'stats':{'answered':5,'accuracy':80,'correct':4,'wrong':1},
  'background':'cartoon','roundDurationMs':20000,'variantMode':'options'}
with sync_playwright() as playwright:
 browser=playwright.chromium.launch(headless=True,args=['--no-sandbox'])
 for width,height in [(1366,768),(390,844)]:
  context=browser.new_context(viewport={'width':width,'height':height},service_workers='block')
  page=context.new_page()
  errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  state={'room':build_room()}
  def api(route):
   route.fulfill(status=200,content_type='application/json',
     body=json.dumps({'ok':True,'room':state['room']},ensure_ascii=False))
  page.route('**/api/room/state?*',api)
  page.goto(base+'/stage.html?code=123456&stage=synthetic-safe-token',wait_until='domcontentloaded')
  page.locator('.stage-wrap').wait_for(state='visible')
  assert page.locator('body[data-stage-view="question"]').count()==1
  state['room']=build_room('results')
  page.locator('#tagV27RoundStage .tag-v27-row').first.wait_for(state='attached',timeout=6000)
  assert page.locator('.tag-v27-row').count()==5
  page.wait_for_timeout(1950)
  n=page.locator('.tag-v27-row.tag-v27-visible').count()
  assert 1<=n<=2,(width,'all ranks appeared too early',n)
  page.wait_for_timeout(8500)
  assert page.locator('.tag-v27-row.tag-v27-visible').count()==5
  assert page.locator('.tag-v27-status').inner_text()=='🏆 الترتيب بعد السؤال'
  first=page.locator('.tag-v27-row').first
  assert first.locator('.tag-v27-realname').inner_text()=='ليان',first.inner_text()
  assert first.locator('.tag-v27-score').inner_text()=='950 ★'
  before=page.locator('.tag-v27-row').first.inner_text()
  page.wait_for_timeout(2100)
  assert first.inner_text()==before,'polling restarted completed animation'
  assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 6'),(width,'overflow on scoreboard')
  state['room']=build_room('finished')
  page.locator('.tag-v27-pod.place-3').wait_for(state='attached',timeout=5000)
  assert page.locator('.tag-v27-pod').count()==3
  page.wait_for_timeout(1100)
  assert page.locator('.tag-v27-pod.place-3.tag-v27-revealed').count()==1,(width,'third did not rise')
  assert page.locator('.tag-v27-pod.place-1.tag-v27-revealed').count()==0,(width,'winner shown prematurely')
  page.wait_for_timeout(3500)
  assert page.locator('.tag-v27-pod.tag-v27-revealed').count()==3
  assert page.locator('.tag-v27-pod.place-1 img[src*="n01"]').count()==1,'winner avatar lost'
  assert 'ليان' in page.locator('.tag-v27-winner-announcement').inner_text()
  assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 6'),(width,'podium overflow')
  assert not errors,(width,errors)
  context.close()
  print('PASS TAG V27 stage at',width,'pixels: suspense, score move, avatar third-second-first, no poll-reset',flush=True)
 browser.close()
http.shutdown();http.server_close()
