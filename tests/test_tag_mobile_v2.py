"""Mobile V2 structural regression: all site pages receive responsive styles and same-window PWA LAB navigation."""
import os
import sys
import json
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
tmp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(tmp.name)/'tag-mobile-check.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import server

http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(http.server_port)

PAGES=[
 'about.html','admin.html','app.html','champion-board.html',
 'champion.html','for-teachers.html','game-lab-card.html',
 'game-lab-create.html','game-lab-live.html','game-lab-play.html',
 'game-lab-preview.html','index.html','stage.html','student.html',
 'studio.html','tag-lab-books.html','tag-lab-create.html',
 'tag-lab-games.html','tag-lab-home.html','tag-lab-library.html',
 'tag-lab-live.html','tag-lab-mixer.html','tag-lab-students.html'
]

def fetch(path):
 with urllib.request.urlopen(BASE+path,timeout=12) as req:
  return req.status,req.read().decode('utf-8')

class AllPagesMobileContract(unittest.TestCase):
 def test_all_23_pages_have_mobile_styles_and_browser_handoff(self):
  for path in PAGES:
   with self.subTest(path=path):
    status,text=fetch('/'+path)
    self.assertEqual(status,200)
    self.assertIn('tag-mobile-v2.css?v=',text)
    self.assertIn('tag-app-bridge-v2.js?v=26.0',text)
    self.assertIn('name="viewport"',text)

 def test_pwa_home_opens_lab_in_same_window(self):
  _,page=fetch('/app.html')
  self.assertIn('data-tag-lab-entry="internal"',page)
  self.assertNotIn('data-tag-external-browser="true"',page)
  self.assertIn('href="/tag-lab-home.html?v=34"',page)
  self.assertIn('href="/student.html"',page)
  self.assertIn('href="/?teacher=1"',page)
  self.assertNotIn('href="/champion.html"',page)
  _,portal=fetch('/')
  self.assertIn('href="/champion.html"',portal)

 def test_one_public_url_and_teacher_templates_shortcut_removed(self):
  landing=(ROOT/'short-link'/'index.html').read_text(encoding='utf-8')
  _,portal=fetch('/')
  _,app=fetch('/app.html')
  self.assertIn('rel="canonical" href="https://teachgame.onrender.com/"',landing)
  self.assertIn('📲 تثبيت تطبيق TAG',landing)
  self.assertIn('href="/app/"',landing)
  self.assertIn('https://quiznova-arena-online.onrender.com/app.html',(ROOT/'short-link'/'app'/'index.html').read_text(encoding='utf-8'))
  self.assertNotIn('href="/champion/"',landing)
  self.assertNotIn('href="/links/"',landing)
  self.assertNotIn('href="/tag-lab-games.html"',portal)
  self.assertIn('href="/tag-lab-home.html',portal)
  self.assertIn('تعلّم. تحدَّ.',app)
  self.assertIn('تعلّم • تحدَّ • تفوّق',landing)

 def test_teacher_phone_dropdown_has_accessible_toggle_and_keeps_desktop_nav(self):
  _,portal=fetch('/')
  self.assertIn('id="tagTeacherMobileToggle"',portal)
  self.assertIn('aria-controls="tagTeacherSections"',portal)
  self.assertIn('aria-expanded="false"',portal)
  self.assertIn('id="tagTeacherSections"',portal)
  self.assertIn('tag-teacher-mobile-menu-v4.js',portal)
  _,script=fetch('/tag-teacher-mobile-menu-v4.js')
  self.assertIn('setOpen(false)',script)
  self.assertIn('event.key === "Escape"',script)
  _,css=fetch('/tag-mobile-v2.css')
  self.assertIn('tag-teacher-menu-open>nav',css)
  self.assertIn('display:none!important',css)

 def test_browser_same_window_lab_navigation(self):
  _,script=fetch('/tag-app-bridge-v2.js?v=26.0')
  self.assertIn("anchor.removeAttribute('target')",script)
  self.assertIn('firstPartyLab',script)
  self.assertNotIn("a.target='_blank'",script)
  self.assertNotIn('directEntryFallback',script)
  self.assertNotIn('localStorage.setItem',script)
  self.assertNotIn('sessionStorage.setItem',script)

 def test_offline_cache_and_protected_assets_unchanged(self):
  _,sw=fetch('/sw.js')
  self.assertIn("req.mode!=='navigate'",sw)
  self.assertNotIn('cache.put(req',sw)
  for path in ('/student.html','/','/tag-lab-home.html'):
   status,page=fetch(path)
   self.assertEqual(status,200)
   self.assertIn('manifest.webmanifest',page)
  status,card=fetch('/student.html')
  self.assertIn('id="liveStudentPin"',card)
  self.assertIn('id="cardCode"',card)

if __name__=='__main__':
 unittest.main()
