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


class TagLogoOnlyV16(unittest.TestCase):
 def test_visible_brand_is_logo_only(self):
  checks={
   'index.html':['bo-entry-logo tag-brand-only','sidebar-brand tag-brand-only','auth-brand tag-brand-only'],
   'about.html':['<a class="brand" href="/"><img'],
   'for-teachers.html':['<a class="logo" href="/"','<a class="footer-logo" href="/"><img'],
   'studio.html':['class="tag-brand-copy" aria-hidden="true"'],
   'student.html':['class="logo tag-student-logo"'],
   'admin.html':['sidebar-brand tag-brand-only'],
   'stage.html':['stage.js?v=16.0'],
  }
  for path,needles in checks.items():
   text=(ROOT/path).read_text(encoding='utf-8')
   for word in needles:
    with self.subTest(page=path,word=word):
     self.assertIn(word,text)
  home=(ROOT/'index.html').read_text(encoding='utf-8')
  start=home.index('<div class="bo-entry-logo tag-brand-only"')
  end=home.index('</div>',start)
  self.assertNotIn('<strong>',home[start:end])
  self.assertNotIn('<span>',home[start:end])
  self.assertIn('tag-logo-v15.png',home[start:end])
  js=(ROOT/'stage.js').read_text(encoding='utf-8')
  head=js[js.index('function head(){'):js.index('let stageLobbySignature')]
  self.assertIn('tag-stage-logo',head)
  self.assertNotIn('<small>',head)
  cards=(ROOT/'portal.js').read_text(encoding='utf-8')
  start=cards.index('<header class="bo-badge-header tag-brand-only"')
  end=cards.index('</header>',start)
  self.assertNotIn('<strong>',cards[start:end])
  self.assertNotIn('<small>',cards[start:end])
  self.assertIn('tag-card-logo',cards[start:end])
  self.assertIn("encodeURIComponent(student.card)",cards)
  self.assertIn('student.cardCode',cards)
