"""QA-only V10.2 actual-server UI acceptance (isolated SQLite + Chromium).
Verifies all 24 games, inline feedback, no transparent overlay, light/dark
anagram contrast, win-sector pause, removal, and new mystery emblem.
"""
import os,sys,tempfile,threading
from pathlib import Path
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
FOLDER=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(FOLDER.name)/'v102-qa.sqlite')
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import server
HTTP=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=HTTP.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(HTTP.server_port)
MODES='quiz fast pairs flash wheel boxes sort truth crossword wordsearch anagram order maze balloons memory hidden cloze diagram board teams survey exit story bingo'.split()
ARTIFACT=ROOT/'browser-qa-artifacts';ARTIFACT.mkdir(exist_ok=True)

def open_game(page,mode):
 page.goto(BASE+'/game-lab-create.html?mode='+mode,wait_until='domcontentloaded')
 page.locator('#sampleQuestions').click()
 page.locator('#goPreview').click()
 page.locator('#launchPreview').click()
 frame=page.frame_locator('#gameFrame')
 frame.locator('#playOverlay').wait_for(state='visible',timeout=13000)
 assert frame.locator('#playOverlay').get_attribute('data-v9-mode')==mode,mode
 return frame

def no_floating_status(frame,mode):
 status=frame.locator('#playStatus')
 data=status.evaluate("""el=>({
  position:getComputedStyle(el).position,
  blur:getComputedStyle(el).backdropFilter,
  pointer:getComputedStyle(el).pointerEvents,
  display:getComputedStyle(el).display,
  empty:!el.textContent.trim(),
  width:el.getBoundingClientRect().width,
  parent:el.parentElement?.id
 })""")
 assert data['position']=='static',(mode,data)
 assert data['blur']=='none',(mode,data)
 assert data['pointer']=='none',(mode,data)
 assert data['parent']=='playOverlay',(mode,data)
 if data['empty']:assert data['display']=='none',(mode,data)
 return data

def no_bad_decorations(frame,mode):
 assert frame.locator('#playOverlay .playhead>.v101-buddy').count()==0,mode
 assert frame.locator('#playBody>.v101-scene-token').count()==0,mode
 assert frame.locator('#playOverlay .v101-wheel-dice').count()==0,mode

def anagram_contrast(frame,theme):
 target=frame.locator('#letterAnswer')
 style=target.evaluate("""el=>({
  c:getComputedStyle(el).color,
  bg:getComputedStyle(el).backgroundColor,
  txt:el.textContent.trim()
 })""")
 assert style['c']!=style['bg'],(theme,style)
 assert style['txt'],(theme,style)
 if theme=='light':assert style['c']=='rgb(29, 59, 102)',style
 if theme=='dark':assert style['c']=='rgb(243, 250, 255)',style

def wheel(page,frame,width):
 assert frame.locator('.v102-mystery-emblem').count()==1
 assert frame.locator('.v102-mystery-emblem>span').inner_text().strip()=='؟'
 assert frame.locator('#spinWheel').get_attribute('aria-label')
 assert '🎲' not in frame.locator('#wheelReveal').inner_text()
 assert '🎲' not in frame.locator('#spinWheel').inner_text()
 assert frame.locator('#wheelArea button').is_enabled()
 used=set()
 for turn in range(3):
  labels=frame.locator('#spinWheel g[data-question]')
  before=set(labels.evaluate_all('(els)=>els.map(e=>e.dataset.question)'))
  assert len(before)==8-turn,(turn,before)
  frame.locator('#wheelArea button').click()
  frame.locator('#wheelReveal h3').wait_for(state='visible',timeout=6000)
  heading=frame.locator('#wheelReveal h3').inner_text().strip()
  assert heading and len(heading)>=7,(turn,heading)
  # V10.2 shows a question while still highlighting the winning wedge.
  frame.locator('#spinWheel').wait_for(state='visible')
  selected=frame.locator('#spinWheel g.v102-winning-wedge')
  selected.wait_for(state='visible',timeout=2000)
  chosen=selected.get_attribute('data-question')
  assert chosen not in used and chosen in before,(turn,chosen,used)
  assert frame.locator('#spinWheel').get_attribute('data-v102-holding')=='true'
  assert labels.count()==len(before),(turn,'winning wedge disappeared too soon')
  assert frame.locator('#playStatus').is_visible()
  no_floating_status(frame,'wheel feedback')
  labels.nth(7-turn).wait_for(state='detached',timeout=4000)
  remaining=set(labels.evaluate_all('(els)=>els.map(e=>e.dataset.question)'))
  assert chosen not in remaining,(turn,chosen,remaining)
  assert len(remaining)==len(before)-1
  used.add(chosen)
  frame.locator('#wheelReveal button').click()
  assert 'الإجابة' in frame.locator('#wheelReveal .v101-wheel-answer').inner_text()
  assert frame.locator('#wheelArea button').is_enabled()
  assert frame.locator('#playCounter').inner_text().startswith(str(turn+1)+' /')
  no_floating_status(frame,'wheel revealed')
 # Screenshot with an actual selected question, not an empty placeholder.
 page.screenshot(path=str(ARTIFACT/'gamelab-v102-wheel-'+str(width)+'.png'),animations='disabled')

try:
 with sync_playwright() as playwright:
  browser=playwright.chromium.launch(headless=True,args=['--no-sandbox'])
  try:
   for width,height,modes in [(1366,768,MODES),(390,844,['wheel','quiz','fast','truth','pairs','boxes','anagram','memory'])]:
    context=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce')
    page=context.new_page()
    errors=[];page.on('pageerror',lambda err:errors.append(str(err)))
    for mode in modes:
     frame=open_game(page,mode)
     no_floating_status(frame,mode)
     no_bad_decorations(frame,mode)
     if mode=='wheel':wheel(page,frame,width)
     elif mode=='anagram':
      anagram_contrast(frame,'light')
      frame.locator('#v101ThemeButton').click()
      anagram_contrast(frame,'dark')
      frame.locator('#v101ThemeButton').click()
     elif mode=='quiz':
      frame.locator('#answers .choice').first.click()
      frame.locator('#playStatus').wait_for(state='visible',timeout=4000)
      no_floating_status(frame,mode+' after answer')
      # A status notification must never make the Next button unclickable.
      frame.locator('#nextWrap button').first.click(timeout=4500)
     else:
      assert frame.locator('#playBody').is_visible(),mode
     page.locator('#closePreview').click()
     assert page.locator('#previewOverlay').is_hidden(),mode
     print('PASS V10.2 cleaned preview: '+mode+' '+str(width),flush=True)
    assert not errors,(width,errors)
    layout=page.evaluate("()=>({width:innerWidth,scroll:document.documentElement.scrollWidth})")
    assert layout['scroll']<=layout['width']+5,(width,layout)
    context.close()
  finally:browser.close()
finally:
 HTTP.shutdown();HTTP.server_close();FOLDER.cleanup()
