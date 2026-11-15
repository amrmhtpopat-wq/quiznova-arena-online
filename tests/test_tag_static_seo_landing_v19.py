"""The always-available TAG SEO homepage is indexable and doesn't redirect ordinary visitors."""
import json,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class TestStaticSeoLanding(unittest.TestCase):
 def test_root_is_indexable(self):
  root=(ROOT/'short-link/index.html').read_text(encoding='utf-8')
  self.assertIn('name="robots" content="index,follow',root)
  self.assertIn('rel="canonical" href="https://teachgame.onrender.com/"',root)
  self.assertIn('"@type": "WebSite"',root)
  self.assertIn('TEACH AND GAME',root)
  self.assertIn('href="/teacher/"',root)
  self.assertIn('href="/student/"',root)
  self.assertNotIn('noindex,nofollow,noarchive',root)
  self.assertNotIn('http-equiv="refresh"',root)
 def test_legacy_codes_preserved(self):
  root=(ROOT/'short-link/index.html').read_text(encoding='utf-8')
  self.assertIn('["teacher","card","code","room","session","join","quiz"]',root)
  self.assertIn('location.replace(to.toString()+location.hash)',root)
  self.assertIn('searchParams.set(k,v)',root)
 def test_static_robot_and_sitemap(self):
  robot=(ROOT/'short-link/robots.txt').read_text(encoding='utf-8')
  self.assertIn('Allow: /',robot)
  self.assertNotIn('Disallow: /',robot)
  site=(ROOT/'short-link/sitemap.xml').read_text(encoding='utf-8')
  self.assertIn('<loc>https://teachgame.onrender.com/</loc>',site)
  self.assertEqual(site.count('<url>'),1)
 def test_exclusive_static_public_index(self):
  for route in ('teacher','student','play','card','admin','studio'):
   self.assertIn('noindex,nofollow,noarchive',(ROOT/'short-link'/route/'index.html').read_text(encoding='utf-8'))
if __name__=='__main__':unittest.main()
