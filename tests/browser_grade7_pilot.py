"""Chromium checks: reviewed Grade 7 pilot loads and saves 24 authentic-mode activities."""
import os,sys,tempfile,threading,uuid
from pathlib import Path
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
temp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ.pop('OPENAI_API_KEY',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(temp.name)/'pilot_browser.sqlite')
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
os.environ['QUIZNOVA_CLOUD']='1'
import platform_store as db
import server
email='grade7-browser-'+uuid.uuid4().hex+'@example.test'
password='Grade7SecureBrowserPass123!'
db.create_teacher(email,password,'معلم الصف السابع التجريبي','مدرسة اختبار','المهارات الرقمية')
http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(http.server_port)
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
  try:
   for width,height in ((1440,900),(390,844)):
    context=browser.new_context(viewport={'width':width,'height':height},is_mobile=width<500,has_touch=width<500)
    page=context.new_page()
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(base+'/game-lab-preview.html',wait_until='domcontentloaded')
    page.locator('#loadGrade7Pilot').click()
    page.wait_for_function("()=>document.querySelector('#grade7PilotStatus').textContent.includes('تم تحميل 20')",timeout=11000)
    textarea=page.locator('#activityData').input_value()
    assert len([x for x in textarea.splitlines() if x.strip()])==20
    assert textarea.splitlines()[0].endswith(' | 11')
    assert 'أنظمة الحوسبة' in page.locator('#activityTitle').input_value()
    assert '20' in page.locator('#contentFeedback').inner_text()
    assert page.locator('#gameGrid .game').count()==24
    layout=page.evaluate('() => ({width:innerWidth,scroll:document.documentElement.scrollWidth})')
    assert layout['scroll']<=layout['width']+3,(width,layout)
    if width==1440:
      page.locator('#cloudEmail').fill(email)
      page.locator('#cloudPassword').fill(password)
      page.locator('#cloudSignIn').click()
      page.locator('#cloudWorkspace').wait_for(state='visible',timeout=15000)
      page.locator('#cloudGenerateAll').click()
      page.wait_for_function("()=>document.querySelectorAll('#cloudList .cloud-activity').length===24",timeout=20000)
      assert '24' in page.locator('#cloudMessage').inner_text()
      # Editing a saved variant should preserve its textbook page marker.
      page.locator('#cloudList .cloud-activity').first.locator('button').filter(has_text='تعديل').click()
      assert ' | 11' in page.locator('#activityData').input_value()
    assert not errors,(width,errors)
    context.close()
    print('PASS Grade 7 pilot Chromium '+str(width)+'x'+str(height)+': book-source demo, 20 questions, 24 modes, responsive.')
  finally:
   browser.close()
finally:
 http.shutdown();http.server_close();temp.cleanup()
