"""QA-only V9 complete game experience browser acceptance.
Runs against a disposable localhost static site; never touches Render or real students.
"""
import json
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'browser-qa-artifacts';OUT.mkdir(exist_ok=True)
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
Thread(target=server.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(server.server_port)
TEST_ID='a'*32
exampleReport={'ok':True,'total':2,'averagePercent':62.5,
 'results':[{'name':'Student A','className':'السابع أ','correct':4,'questions':4,'score':400,'finishedAt':1763154000},
            {'name':'Student B','className':'السابع ب','correct':1,'questions':4,'score':100,'finishedAt':1763155000}],
 'skillSummary':[{'group':'المعالج','correct':2,'answers':4,'percent':50.0},
                 {'group':'التخزين','correct':3,'answers':4,'percent':75.0}],
 'questionStats':[{'index':0,'correct':1,'answers':2,'percent':50.0}]}
def mock(r,body):
 r.fulfill(status=200,content_type='application/json',body=json.dumps(body,ensure_ascii=False))
try:
 with sync_playwright() as playwright:
  browser=playwright.chromium.launch(headless=True,args=['--no-sandbox'])
  try:
   for width,height in [(1440,900),(390,844)]:
    page=browser.new_page(viewport={'width':width,'height':height})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.route('**/api/auth/me',lambda r:mock(r,{'ok':True,'teacher':{'name':'معلم التجربة'}}))
    page.route('**/api/game-lab/pro/media',lambda r:mock(r,{'ok':True,'images':[{'id':TEST_ID,'name':'صورة درس'}]}))
    page.route('**/api/game-lab/teacher/list',lambda r:mock(r,{'ok':True,'activities':[{
     'id':TEST_ID,'title':'تحدي المكونات','mode':'quiz','questionCount':4,'published':True}]}))
    page.route('**/api/game-lab/teacher/reports?*',lambda r:mock(r,exampleReport))
    page.goto(BASE+'/game-lab-create.html?mode=diagram',wait_until='domcontentloaded')
    assert page.locator('#modeSelect').input_value()=='diagram'
    assert page.locator('#v9ImageControls').is_visible()
    assert page.locator('#v9TeamsControls').is_hidden()
    assert page.locator('#questionList .question-card [data-field="markerX"]').count()==4
    first=page.locator('#questionList .question-card').first
    first.locator('[data-field="explanation"]').fill('هذا الجزء مسؤول عن المعالجة.')
    first.locator('[data-field="markerX"]').fill('28')
    first.locator('[data-field="markerY"]').fill('40')
    page.locator('#sampleQuestions').click()
    page.locator('#activityTitle').fill('تجربة رسم تفاعلي')
    page.locator('#goPreview').click()
    assert page.locator('#stepThree').is_visible()
    page.locator('#launchPreview').click()
    frame=page.frame_locator('#gameFrame')
    frame.locator('#playOverlay').wait_for(state='visible',timeout=12000)
    assert frame.locator('#playOverlay').get_attribute('data-v9-mode')=='diagram'
    assert frame.locator('.v9-stage').count()==1
    assert frame.locator('.extra-diagram-mark').count()==1
    page.locator('#closePreview').click()
    page.evaluate("localStorage.setItem('qn9_teacher_token','qa-test')")
    page.locator('#myLibrary').click()
    page.locator('.v9-open-report').wait_for(state='visible',timeout=5000)
    page.locator('.v9-open-report').click()
    panel=page.locator('#v9ReportPanel')
    panel.wait_for(state='visible',timeout=6000)
    page.wait_for_function("()=>document.querySelectorAll('#v9ReportRows tr').length===2",timeout=6000)
    assert panel.locator('#v9ReportRows tr').count()==2
    assert '50%' in panel.locator('#v9ReportSkills').inner_text()
    assert 'يحتاج مراجعة' in panel.locator('#v9QuestionAnalysis').inner_text()
    page.screenshot(path=str(OUT/('gamelab-v9-dashboard-'+str(width)+'.png')),animations='disabled')
    layout=page.evaluate('()=>({w:innerWidth,scroll:document.documentElement.scrollWidth})')
    assert layout['scroll']<=layout['w']+4,(width,layout)
    assert not errors,(width,errors)
    print('PASS V9 creator/report '+str(width)+'x'+str(height),flush=True)
    page.close()
   page=browser.new_page(viewport={'width':390,'height':844})
   errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   for mode,expect in [('flash','.flipcard'),('wheel','#spinWheel'),('boxes','#boxesGrid'),
                       ('pairs','.matchgrid'),('memory','.extra-memory'),('wordsearch','.extra-wordsearch'),
                       ('anagram','#letterPool'),('crossword','#crossGrid'),('bingo','#bingoGrid'),
                       ('sort','#sortChoices'),('teams','#teamsOptions'),('truth','#truthActions')]:
    page.goto(BASE+'/game-lab-create.html?mode='+mode,wait_until='domcontentloaded')
    page.locator('#sampleQuestions').click()
    page.locator('#goPreview').click()
    assert page.locator('#stepThree').is_visible(),mode
    page.locator('#launchPreview').click()
    frame=page.frame_locator('#gameFrame')
    frame.locator('#playOverlay').wait_for(state='visible',timeout=12000)
    frame.locator(expect).wait_for(state='visible',timeout=8000)
    assert frame.locator('#playOverlay').get_attribute('data-v9-mode')==mode
    if mode=='flash':
     frame.locator('#flipCard').click()
     assert frame.locator('#flashNav').get_by_text('أتقنت').count()==1
     frame.locator('#flashNav').get_by_text('أتقنت').click()
     assert frame.locator('#playCounter').inner_text().startswith('2 /')
    if mode=='boxes':
     first=frame.locator('#boxesGrid .mystery').first
     first.click();first.click()
     assert 'v6-solved' in first.get_attribute('class')
    if mode=='wheel':
     frame.locator('#wheelArea button').first.click()
     frame.locator('#wheelReveal h3').wait_for(timeout=6500)
     frame.locator('#wheelReveal button').click()
     assert '1 /' in frame.locator('#playCounter').inner_text()
    page.locator('#closePreview').click()
    print('PASS V9 distinct game mode: '+mode,flush=True)
   assert not errors,errors
   page.close()
  finally:browser.close()
finally:server.shutdown();server.server_close()
