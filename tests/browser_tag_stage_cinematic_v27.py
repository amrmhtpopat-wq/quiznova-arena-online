"""TAG V27 projector: browser-verified sequential ranking and avatar podium.
Uses synthetic public room state, never touches production teachers or students.
"""
import copy,json,os,threading
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
http=ThreadingHTTPServer(('127.0.0.1',0),Quiet)
threading.Thread(target=http.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(http.server_port)
players=[
 {'name':'ليان','avatar':'b01','score':2000,'correct':5,'team':''},
 {'name':'محمد','avatar':'g02','score':1850,'correct':4,'team':''},
 {'name':'سارة','avatar':'n01','score':1750,'correct':4,'team':''},
 {'name':'عمر','avatar':'01','score':1650,'correct':3,'team':''},
 {'name':'هيا','avatar':'b04','score':1500,'correct':3,'team':''}
]
room={'status':'question','playType':'individual','background':'cartoon',
      'showFeedback':True,'examMode':False,'championMode':False,'index':0,'total':8,
      'variantMode':'same','question':{'text':'ما اسم المكون الأساسي للحاسوب؟','options':['الشاشة','المعالج','الماوس','السماعة']},
      'players':players,'leaders':players,'report':players,
      'stats':{'answered':3,'accuracy':80,'correct':4,'wrong':1}}
outdir=ROOT/'artifacts/tag-v27'
outdir.mkdir(parents=True,exist_ok=True)
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
 for width,height in ((390,844),(1366,800)):
  context=browser.new_context(viewport={'width':width,'height':height},is_mobile=width<600,has_touch=width<600,service_workers='block')
  page=context.new_page()
  errors=[]
  page.on('pageerror',lambda err: errors.append(str(err)))
  state={'room':copy.deepcopy(room)}
  def responder(route):
   route.fulfill(status=200,content_type='application/json; charset=utf-8',
                 body=json.dumps({'ok':True,'room':state['room']},ensure_ascii=False))
  page.route('**/api/room/state?**',responder)
  page.goto(BASE+'/stage.html?code=123456&stage=synthetic-read-only',wait_until='domcontentloaded',timeout=20000)
  page.locator('#tagLiveLeaders .tag27-rank-row').first.wait_for(state='visible',timeout=12000)
  page.wait_for_function("document.querySelectorAll('#tagLiveLeaders .tag27-rank-row').length===5",timeout=11000)
  page.wait_for_timeout(900)
  assert page.locator('#tagLiveLeaders .tag27-rank-row').count()==5
  assert page.locator('#tagLiveLeaders .tag27-player b').all_text_contents()==[p['name'] for p in players]
  page.evaluate("window.__tag27FirstRow=document.querySelector('#tagLiveLeaders .tag27-rank-row')")
  page.wait_for_timeout(1800)
  assert page.evaluate("window.__tag27FirstRow===document.querySelector('#tagLiveLeaders .tag27-rank-row')"),'High-frequency polls destroyed live visual DOM'
  liveOverflow=page.evaluate("document.documentElement.scrollWidth-innerWidth")
  assert liveOverflow<=10,('Question overflow',width,liveOverflow)
  page.screenshot(path=str(outdir/f'live-{width}.png'),full_page=False)
  state['room']={**copy.deepcopy(room),'status':'results','stats':{'answered':5,'accuracy':85,'correct':5,'wrong':0}}
  page.locator('#tag27RoundList').wait_for(state='visible',timeout=7000)
  page.wait_for_function("document.querySelectorAll('#tag27RoundList .tag27-rank-row').length===5",timeout=11000)
  page.wait_for_timeout(1300)
  roundOverflow=page.evaluate("document.documentElement.scrollWidth-innerWidth")
  assert roundOverflow<=10,('Results overflow',width,roundOverflow)
  page.screenshot(path=str(outdir/f'round-{width}.png'),full_page=False)
  state['room']={**copy.deepcopy(room),'status':'finished','report':players,'stats':{'answered':5,'accuracy':85,'correct':5,'wrong':0}}
  page.locator('.tag28-finale').wait_for(state='visible',timeout=7000)
  assert page.locator('.tag27-podium-card').count()==3
  assert page.locator('.tag27-podium-card img').count()==3
  assert [page.locator(f'.tag27-place-{n} img').get_attribute('src') for n in (1,2,3)]==[
     '/assets/avatars3d/b01.webp','/assets/avatars3d/g02.webp','/assets/avatars3d/n01.webp']
  page.wait_for_function("document.querySelector('.tag27-place-3')?.classList.contains('tag27-entered')",timeout=3000)
  page.wait_for_function("document.querySelector('.tag27-place-2')?.classList.contains('tag27-entered')",timeout=5000)
  page.wait_for_function("document.querySelector('.tag27-place-1')?.classList.contains('tag27-entered')",timeout=7500)
  # Wait for the entrance to visibly finish before checking the actual
  # character/avatar and taking screenshots. Log bounds for a real 390px
  # phone and 1366px classroom projector — not just a CSS class.
  page.wait_for_timeout(1600)
  geo=page.evaluate("""() => {
    const nodes=['.tag27-place-1','.tag27-place-1 .tag28-person',
      '.tag27-place-1 .tag27-podium-name','.tag27-place-1 .tag28-stand',
      '.tag28-actions'];
    const geom=s=>{const n=document.querySelector(s);
      if(!n)return null;const r=n.getBoundingClientRect();
      return {top:r.top,bottom:r.bottom,left:r.left,right:r.right,
              opacity:getComputedStyle(n).opacity,visible:r.bottom>0&&r.top<innerHeight}};
    return {h:innerHeight,w:innerWidth,parts:Object.fromEntries(nodes.map(x=>[x,geom(x)]))};
  }""")
  print('TAG27_VISIBLE_FINAL_PODIUM',width,json.dumps(geo,ensure_ascii=False),flush=True)
  page.screenshot(path=str(outdir/f'podium-{width}.png'),full_page=False)
  gold=geo['parts']['.tag27-place-1']
  figure=geo['parts']['.tag27-place-1 .tag28-person']
  assert float(gold['opacity'])>0.98,('Gold card did not enter',width,geo)
  assert figure['visible'] and figure['top']>=0 and figure['bottom']<=height+3,('Gold character clipped',width,geo)
  stand=geo['parts']['.tag27-place-1 .tag28-stand']
  footer=geo['parts']['.tag28-actions']
  assert stand['bottom']<=footer['top']+2,('Podium/replay controls overlap',width,geo)
  assert footer['bottom']<=height+3,('Replay controls leave screen',width,geo)
  assert page.locator('.tag27-place-1 .tag27-podium-name').inner_text()=='ليان'
  assert page.locator('.tag27-place-1 img').evaluate("(el)=>el.complete && el.naturalWidth>0")
  assert page.locator('#tag28Announcement').inner_text().find('بطل TAG')>=0
  finalOverflow=page.evaluate("document.documentElement.scrollWidth-innerWidth")
  assert finalOverflow<=10,('Final podium overflow',width,finalOverflow)
  page.screenshot(path=str(outdir/f'podium-{width}.png'),full_page=False)
  page.locator('#tag27Replay').click()
  page.wait_for_function("document.querySelector('.tag27-place-1')?.classList.contains('tag27-entered')",timeout=8500)
  state['room']={**copy.deepcopy(room),'examMode':True,'showFeedback':False,'status':'question','index':1}
  page.wait_for_function("document.querySelector('body')?.dataset.stageView==='question' && document.querySelector('.question')",timeout=8000)
  assert page.locator('#tagLiveLeaders').count()==0,'Private exam score was disclosed'
  state['room']['status']='results'
  page.wait_for_function("document.querySelector('body')?.dataset.stageView==='results' && document.querySelector('.round-stage')",timeout=8000)
  assert page.locator('#tag27RoundList').count()==0,'Hidden exam ranks were disclosed'
  assert not errors,('Page JS exceptions',width,errors)
  print('PASS TAG V27:',width,'sequential top-five, no poll reset, podium 3→2→1, avatars, private exam, replay, responsive',flush=True)
  context.close()
 browser.close()
http.shutdown();http.server_close()
