"""TAG official identity and Search SEO V2 checks."""
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='https://quiznova-arena-online.onrender.com'
class TagSeoChecks(unittest.TestCase):
 def test_logo_files(self):
  image=(ROOT/'assets/brand/tag-logo-v15.png').read_bytes()
  self.assertTrue(image.startswith(b'\x89PNG'))
  self.assertGreater(len(image),1000)
  self.assertIn('<svg',(ROOT/'assets/brand/tag-icon.svg').read_text(encoding='utf-8'))
 def test_pages(self):
  for name in ('index.html','about.html','for-teachers.html'):
   with self.subTest(name=name):
    html=(ROOT/name).read_text(encoding='utf-8')
    self.assertIn('TEACH AND GAME',html)
    self.assertIn('tag-brand-v2.css',html)
    self.assertIn('tag-logo-v15.png',html)
    dest=BASE+('/' if name=='index.html' else '/'+name)
    self.assertIn('<link rel="canonical" href="'+dest+'">',html)
    self.assertIn('og:image',html)
    self.assertIn('twitter:image',html)
 def test_schema(self):
  html=(ROOT/'index.html').read_text(encoding='utf-8')
  start=html.index('<script type="application/ld+json">')+len('<script type="application/ld+json">')
  end=html.index('</script>',start)
  graph=json.loads(html[start:end])['@graph']
  site=next(v for v in graph if v.get('@type')=='WebSite')
  self.assertEqual(site['name'],'TEACH AND GAME')
  self.assertIn('TAG',site['alternateName'])
 def test_privacy(self):
  for name in ('student.html','studio.html','stage.html','admin.html'):
   self.assertIn('noindex',(ROOT/name).read_text(encoding='utf-8'))
  self.assertIn('Disallow: /api/',(ROOT/'robots.txt').read_text(encoding='utf-8'))
  self.assertEqual((ROOT/'sitemap.xml').read_text(encoding='utf-8').count('<url>'),3)
if __name__=='__main__':
 unittest.main()
