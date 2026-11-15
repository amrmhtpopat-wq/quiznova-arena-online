"""TAG V18 checks shareable shortcuts, query hygiene, QR and search canonical."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
SHORT='https://teachgame.onrender.com'
class TestTagLinksV18(unittest.TestCase):
 def test_routes(self):
  for slug in ('teacher','student','play','card','solo','studio','admin','about','for-teachers','stage'):
   with self.subTest(slug=slug):
    p=(ROOT/'short-link'/slug/'index.html').read_text(encoding='utf-8')
    self.assertIn('noindex,nofollow,noarchive',p)
    self.assertIn('wake-loader.js?v=18',p)
    self.assertIn('new URL(window.TAG_ENTRY_TARGET)',p)
    self.assertIn('dest.searchParams.set(key,val)',p)
    self.assertIn('location.hash',p)
  self.assertTrue((ROOT/'short-link/links/index.html').is_file())
 def test_referral_cleanup(self):
  src=(ROOT/'tag-clean-links-v18.js').read_text(encoding='utf-8')
  self.assertIn('utm_',src)
  self.assertIn('chatgpt',src)
  self.assertIn('replaceState',src)
  self.assertNotIn('searchParams.delete("code")',src)
  self.assertNotIn('searchParams.delete("card")',src)
 def test_qr_only_official(self):
  p=(ROOT/'portal.js').read_text(encoding='utf-8')
  self.assertIn(SHORT+'/card/?card=',p)
  self.assertIn('student.cardCode',p)
  self.assertIn("location.hostname==='quiznova-arena-online.onrender.com'",p)
  stage=(ROOT/'stage.js').read_text(encoding='utf-8')
  self.assertIn(SHORT+'/play/?code=',stage)
  server=(ROOT/'server.py').read_text(encoding='utf-8')
  self.assertIn(SHORT+'/play/',server)
  self.assertIn("root.rstrip('/')==",server)
  self.assertIn("else root+'/student.html'",server)
 def test_google_not_switched_to_redirect(self):
  for name in ('index.html','about.html','for-teachers.html'):
   page=(ROOT/name).read_text(encoding='utf-8')
   self.assertIn('https://quiznova-arena-online.onrender.com/',page)
  self.assertNotIn(SHORT,(ROOT/'sitemap.xml').read_text(encoding='utf-8'))
 def test_link_scrub_on_page(self):
  for name in ('index.html','student.html','studio.html','admin.html','stage.html','about.html','for-teachers.html'):
   self.assertIn('tag-clean-links-v18.js',(ROOT/name).read_text(encoding='utf-8'))
if __name__=='__main__':unittest.main()
