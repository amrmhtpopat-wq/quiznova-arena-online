"""V10.1 UX regression: actual production HTTP headers and nested Creator iframe.

Synthetic questions only, temporary SQLite. Verifies 24 game templates, question
readability, wheel labels/removal, contrast themes, and phone/desktop layout.
"""
import os,sys,tempfile,threading
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import urlopen
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
FOLDER=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(FOLDER.name)/'v101-test.sqlite')
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import server
HTTP=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=HTTP.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(HTTP.server_port)
MODES='quiz fast pairs flash wheel boxes sort truth crossword wordsearch anagram order maze balloons memory hidden cloze diagram board teams survey exit story bingo'.split()
OUT=ROOT/'browser-qa-artifacts';OUT.mkdir(exist_ok=True)

def create(page,mode):
 page.goto(BASE+'/game-lab-create.html?mode='+mode,wait_until='domcontentloaded')
 page.locator('#sampleQuestions').click()
 page.locator('#goPreview').click()
 page.locator('#launchPreview').click()
 frame=page.frame_locator('#gameFrame')
 frame.locator('#playOverlay').wait_for(state='visible',timeout=13000)
 return frame

def width_check(page,frame,mode):
 result=frame.locator('#playOverlay').evaluate("""el=>({
  width:el.clientWidth,scroll:el.scrollWidth,
  bodyWidth:document.querySelector('#playBody').clientWidth,
  bodyScroll:document.querySelector('#playBody').scrollWidth,
  headerRect:document.querySelector('.playhead').getBoundingClientRect().toJSON(),
  frameHeight:innerHeight,
  statusRect:document.querySelector('#playStatus').getBoundingClientRect().toJSON(),
  question:document.querySelector('#wheelReveal h3')?.getBoundingClientRect().toJSON()
 })""")
 assert result['scroll']<=result['width']+5,(mode,'overlay',result)
 # V7's positioned mascot/particles may extend beyond the inner 1150px
 # content column while remaining within the actual viewport. The user-facing
 # no-horizontal-scroll contract is the overlay's own scroll width above.
 assert result['bodyScroll']<=result['bodyWidth']+80,(mode,'body decorative extent',result)
 assert result['headerRect']['top']>=-2,(mode,'header above viewport',result)
 assert result['statusRect']['bottom']<=result['frameHeight']+5,(mode,'status clipped',result)
 return result

def theme_test(frame,mode):
 overlay=frame.locator('#playOverlay')
 assert overlay.get_attribute('data-v101-theme') in ('light','dark')
 theme=frame.locator('#v101ThemeButton')
 theme.wait_for(state='visible',timeout=4000)
 assert frame.locator('.v101-buddy svg').count()==1
 assert frame.locator('.v101-scene-token').count()==1
 if overlay.get_attribute('data-v101-theme')=='dark':
  theme.click()
 assert overlay.get_attribute('data-v101-theme')=='light'
 if mode=='wheel':
  frame.locator('#wheelArea button').wait_for(state='visible')
 theme.click()
 assert overlay.get_attribute('data-v101-theme')=='dark'
 theme.click()
 assert overlay.get_attribute('data-v101-theme')=='light'

try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
  try:
   for width,height,modes in [(1366,768,MODES),(390,844,['wheel','quiz','fast','truth','pairs','boxes','crossword','memory'])]:
    ctx=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce')
    page=ctx.new_page();errors=[]
    page.on('pageerror',lambda exc:errors.append(str(exc)))
    for mode in modes:
     frame=create(page,mode)
     overlay=frame.locator('#playOverlay')
     assert overlay.get_attribute('data-v9-mode')==mode,mode
     overlay.evaluate("el=>el.scrollTop=0")
     width_check(page,frame,mode)
     theme_test(frame,mode)
     if mode=='wheel':
      wheel=frame.locator('#spinWheel')
      assert wheel.is_visible()
      labels=wheel.locator('g[data-question]')
      assert labels.count()==8,(width,labels.count())
      first={x for x in labels.evaluate_all("(els)=>els.map(el=>el.dataset.question)")}
      assert len(first)==8
      assert wheel.locator('.v101-slice-label').count()==8
      assert all(len(t.strip())>=4 for t in wheel.locator('.v101-slice-label').all_text_contents())
      frame.locator('#wheelArea button').click()
      question=frame.locator('#wheelReveal h3')
      question.wait_for(state='visible',timeout=5000)
      text=question.inner_text().strip()
      assert len(text)>=8,(width,text)
      remaining=set(labels.evaluate_all("(els)=>els.map(el=>el.dataset.question)"))
      assert len(remaining)==7,(width,remaining)
      assert remaining.issubset(first),(width,first,remaining)
      assert frame.locator('#wheelLeft').inner_text().strip()=='7'
      question_styles=question.evaluate("""el=>({
        color:getComputedStyle(el).color,
        visible:el.getBoundingClientRect().height>30,
        bounds:el.getBoundingClientRect().toJSON()
      })""")
      assert question_styles['color']!='rgb(255, 255, 255)',question_styles
      assert question_styles['visible'],question_styles
      frame.locator('#wheelReveal button').click()
      assert '1 / 8' in frame.locator('#playCounter').inner_text()
      assert 'الإجابة' in frame.locator('#wheelReveal .v101-wheel-answer').inner_text()
      assert frame.locator('#wheelArea button').is_enabled()
      theme=frame.locator('#v101ThemeButton')
      theme.click()
      assert question.evaluate("e=>getComputedStyle(e).color") in ('rgb(241, 247, 255)','rgb(242, 247, 255)')
      theme.click()
      if width>800:
       rect=question.bounding_box()
       assert rect['x']>=-1 and rect['x']+rect['width']<=width+1,(width,rect)
      else:
       assert frame.locator('#wheelReveal').evaluate("el=>getComputedStyle(el).order")=='-1'
      width_check(page,frame,mode+' after-spin')
      page.screenshot(path=str(OUT/('teachgame-ux-v101-wheel-'+str(width)+'.png')),animations='disabled')
     else:
      assert frame.locator('#playBody').is_visible(),mode
      assert frame.locator('#playTitle').inner_text().strip(),mode
     page.locator('#closePreview').click()
     print('PASS actual framed V10.1 game: '+mode+' @'+str(width),flush=True)
    assert not errors,(width,errors)
    ctx.close()
  finally:browser.close()
finally:
 HTTP.shutdown();HTTP.server_close();FOLDER.cleanup()
