"""Verify TAG V17 public identity styling and static cold-start splash without changing SEO/QR links."""
from pathlib import Path
import re, unittest
ROOT=Path(__file__).resolve().parents[1]
BASE='https://quiznova-arena-online.onrender.com/'
class TagWakeSplashChecks(unittest.TestCase):
 def test_glass_mark(self):
  css=(ROOT/'tag-brand-v2.css').read_text(encoding='utf-8')
  self.assertIn('TAG V17',css)
  self.assertIn('rgba(127,198,229,.92)',css)
  self.assertIn('tag-brand-v2.css?v=17.0',(ROOT/'index.html').read_text(encoding='utf-8'))
 def test_all_shortlink_paths(self):
  for name in ('index.html','student.html','studio.html','admin.html','about.html','for-teachers.html'):
   with self.subTest(path=name):
    p=(ROOT/'short-link'/name).read_text(encoding='utf-8')
    self.assertIn('noindex,nofollow,noarchive',p)
    self.assertIn('location.replace(window.TAG_ENTRY_URL())',p)
    self.assertIn('wake-loader.js?v=18',p)
    self.assertIn('id="wakeStatus"',p)
    self.assertIn('src="/assets/brand/tag-logo-dark-v21.png"',p)
  self.assertTrue((ROOT/'short-link/assets/brand/tag-logo-v15.png').is_file())
 def test_loader_avoids_cors_and_user_redirection(self):
  js=(ROOT/'short-link/wake-loader.js').read_text(encoding='utf-8')
  self.assertIn('new Image()',js)
  self.assertIn('probe.naturalWidth>0',js)
  self.assertNotIn('fetch(',js)
  self.assertIn('target+location.search+location.hash',js)
 def test_protected_pages_remain_unindexed(self):
  for name in ('student.html','studio.html','admin.html','stage.html'):
   self.assertIn('noindex',(ROOT/name).read_text(encoding='utf-8'))
  self.assertIn('Disallow: /api/',(ROOT/'robots.txt').read_text(encoding='utf-8'))
if __name__=='__main__':unittest.main()
