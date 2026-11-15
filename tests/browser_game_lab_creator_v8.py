"""Game Lab V8: real 24-template authoring, preview, cloud-save and publishing UX."""
import json
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**k):super().__init__(*a,directory=str(ROOT),**k)
 def log_message(self,*args):pass
http=ThreadingHTTPServer(('127.0.0.1',0),Handler)
Thread(target=http.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(http.server_port)
MODES='quiz fast pairs flash wheel boxes sort truth crossword wordsearch anagram order maze balloons memory hidden cloze diagram board teams survey exit story bingo'.split()
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
  try:
   for width,height in [(1440,900),(390,844)]:
    page=browser.new_page(viewport={'width':width,'height':height})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    captured=[]
    page.route('**/api/auth/me',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps({'ok':True,'teacher':{'name':'معلم تجريبي'}})))
    def saved(route):
     captured.append(route.request.post_data_json)
     route.fulfill(status=200,content_type='application/json',body=json.dumps({'ok':True,'id':'test_saved_activity'}))
    page.route('**/api/game-lab/teacher/save',saved)
    page.route('**/api/game-lab/teacher/publish',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps({'ok':True,'publicCode':'V8-DEMO'})))
    page.goto(BASE+'/game-lab-preview.html',wait_until='domcontentloaded')
    page.locator('#gameGrid .game[data-game-mode="quiz"] .v4-use-template').click()
    page.wait_for_url('**/game-lab-create.html?mode=quiz')
    assert page.locator('#modeSelect').input_value()=='quiz'
    assert page.locator('#stepTwo').is_visible()
    assert page.locator('#questionList .question-card').count()==4
    page.locator('#sampleQuestions').click()
    assert page.locator('#questionList .question-card').count()==8
    page.locator('#activityTitle').fill('مسابقة تجريبية للصف السابع')
    first=page.locator('#questionList .question-card').first
    assert first.locator('[data-field=q]').input_value().startswith('ما الجزء')
    first.locator('[data-wrong="0"]').fill('المعالج الرسومي')
    page.locator('#goPreview').click()
    assert page.locator('#stepThree').is_visible()
    page.locator('#launchPreview').click()
    frame=page.frame_locator('#gameFrame')
    frame.locator('#playOverlay').wait_for(state='visible',timeout=12000)
    assert frame.locator('#answers .choice').count()==4
    answer_text=' '.join(frame.locator('#answers .choice').all_inner_texts())
    for text in ['CPU','المعالج الرسومي','SSD','الشاشة']:assert text in answer_text,(width,answer_text)
    frame.locator('#answers button[data-answer="CPU"]').click()
    frame.locator('#playStatus[data-v6-result="correct"]').wait_for(timeout=4000)
    page.locator('#closePreview').click()
    assert page.locator('#previewOverlay').is_hidden()
    page.evaluate("localStorage.setItem('qn9_teacher_token','test-token')")
    page.locator('#goSave').click()
    page.locator('#saveBox').wait_for(state='visible',timeout=6000)
    page.locator('#publishCloud').click()
    page.locator('#shareBox').wait_for(state='visible',timeout=6000)
    assert len(captured)==1,captured
    assert captured[0]['activity']['mode']=='quiz'
    assert captured[0]['activity']['rows'][0]['choices']==['CPU','المعالج الرسومي','SSD','الشاشة'],captured[0]
    assert 'V8-DEMO' in page.locator('#shareUrl').input_value()
    assert page.locator('#shareQr').get_attribute('src').startswith('/api/qr?format=svg')
    layout=page.evaluate("()=>({width:innerWidth,doc:document.documentElement.scrollWidth})")
    assert layout['doc']<=layout['width']+4,(width,layout)
    assert not errors,(width,errors)
    print('PASS full V8 creator flow '+str(width)+'x'+str(height),flush=True)
    page.close()
   # Every one of the 24 modes has a distinct dedicated creator route and a
   # working connection to the existing real in-browser game engine.
   page=browser.new_page(viewport={'width':1280,'height':800})
   errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   for mode in MODES:
    page.goto(BASE+'/game-lab-create.html?mode='+mode,wait_until='domcontentloaded')
    assert page.locator('#modeSelect').input_value()==mode
    page.locator('#sampleQuestions').click()
    page.locator('#goPreview').click()
    assert page.locator('#stepThree').is_visible(),mode
    page.locator('#launchPreview').click()
    frame=page.frame_locator('#gameFrame')
    frame.locator('#playOverlay').wait_for(state='visible',timeout=12000)
    assert frame.locator('#playBody').is_visible(),mode
    assert frame.locator('#playTitle').inner_text().strip(),mode
    page.locator('#closePreview').click()
    page.wait_for_timeout(90)
    print('PASS template '+mode,flush=True)
   assert not errors,errors
   page.close()
  finally:browser.close()
finally:http.shutdown();http.server_close()
