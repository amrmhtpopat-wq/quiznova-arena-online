"""Regression: production Handler's X-Frame-Options must permit same-site creator preview.

Unlike older static-file browser checks, this test launches the real server,
using disposable SQLite and synthetic game content (never Render/Neon).
"""
import os,sys,tempfile,threading
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import urlopen
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
folder=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(folder.name)/'iframe-regression.sqlite')
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import server
http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(http.server_port)
MODES='quiz fast pairs flash wheel boxes sort truth crossword wordsearch anagram order maze balloons memory hidden cloze diagram board teams survey exit story bingo'.split()
try:
 for path,want in [('/game-lab-preview.html','SAMEORIGIN'),
                   ('/game-lab-preview.html?creatorPreview=1&mode=wheel','SAMEORIGIN'),
                   ('/game-lab-create.html?mode=wheel','DENY'),
                   ('/game-lab-live.html','DENY'),
                   ('/game-lab-play.html','DENY')]:
  with urlopen(BASE+path,timeout=12) as res:
   assert res.status==200,(path,res.status)
   assert res.headers.get('X-Frame-Options')==want,(path,res.headers)
   if want=='SAMEORIGIN':
    assert "frame-ancestors 'self'" in res.headers.get('Content-Security-Policy',''),path
   else:
    assert 'frame-ancestors' not in res.headers.get('Content-Security-Policy',''),path
 print('PASS preview-only SAMEORIGIN response headers; all other pages stay DENY',flush=True)
 with sync_playwright() as playwright:
  browser=playwright.chromium.launch(headless=True,args=['--no-sandbox'])
  try:
   for width,height,modes in [
     (1366,768,MODES),
     (390,844,['wheel','boxes','quiz','fast','truth','pairs'])
   ]:
    page=browser.new_page(viewport={'width':width,'height':height})
    page_errors=[]
    frame_responses=[]
    page.on('pageerror',lambda e:page_errors.append(str(e)))
    page.on('response',lambda r:frame_responses.append((r.url,r.headers.get('x-frame-options','')))
            if 'game-lab-preview.html?creatorPreview=1' in r.url else None)
    for mode in modes:
     page.goto(BASE+'/game-lab-create.html?mode='+mode,wait_until='domcontentloaded')
     assert page.locator('#modeSelect').input_value()==mode
     page.locator('#sampleQuestions').click()
     page.locator('#goPreview').click()
     assert page.locator('#stepThree').is_visible(),mode
     page.locator('#launchPreview').click()
     frame=page.frame_locator('#gameFrame')
     frame.locator('#playOverlay').wait_for(state='visible',timeout=15000)
     assert frame.locator('#playBody').is_visible(),mode
     assert frame.locator('#playTitle').inner_text().strip(),mode
     src=page.locator('#gameFrame').get_attribute('src')
     assert 'creatorPreview=1' in src and 'mode='+mode in src,(mode,src)
     assert page.locator('#previewNewTab').get_attribute('href')==src,mode
     assert page.locator('#previewNewTab').get_attribute('target')=='_blank'
     assert 'SAMEORIGIN' in [h for u,h in frame_responses if 'mode='+mode in u],mode
     page.locator('#closePreview').click()
     assert page.locator('#previewOverlay').is_hidden(),mode
     print('PASS actual production Handler, embedded creator mode: '+mode+' @'+str(width),flush=True)
    assert not page_errors,(width,page_errors)
    layout=page.evaluate('()=>({width:innerWidth,scroll:document.documentElement.scrollWidth})')
    assert layout['scroll']<=layout['width']+4,(width,layout)
    page.close()
  finally:
   browser.close()
finally:
 http.shutdown();http.server_close();folder.cleanup()
