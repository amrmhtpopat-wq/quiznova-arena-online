"""Mobile V2 structural regression: all site pages receive responsive styles and PWA lab handoff."""
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
    self.assertIn('tag-app-bridge-v2.js?v=2',text)
    self.assertIn('name="viewport"',text)

 def test_pwa_home_uses_browser_bridge_without_changing_url(self):
  _,page=fetch('/app.html')
  self.assertIn('data-tag-lab-entry="external"',page)
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
  self.assertIn('https://quiznova-arena-online.onrender.com/app.html',landing)
  self.assertNotIn('href="/champion/"',landing)
  self.assertNotIn('href="/links/"',landing)
  self.assertNotIn('href="/tag-lab-games.html"',portal)
  self.assertIn('href="/tag-lab-home.html',portal)
  self.assertIn('تعلّم. تحدَّ.',app)
  self.assertIn('تعلّم • تحدَّ • تفوّق',landing)

 def test_browser_externalization_only_when_standalone(self):
  _,script=fetch('/tag-app-bridge-v2.js?v=2')
  self.assertIn("if(!standalone())return",script)
  self.assertIn("a.target='_blank'",script)
  self.assertIn("a.rel='noopener noreferrer external'",script)
  self.assertIn('directEntryFallback',script)
  self.assertIn("u.origin===location.origin",script)
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
