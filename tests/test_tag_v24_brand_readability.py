"""TAG V24 static release contract: Google favicon, new logo, readable scoped pages."""
import re
import json
import struct
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
read=lambda p:(ROOT/p).read_text(encoding='utf-8')
PAGES=['index.html','studio.html','student.html','champion.html','champion-board.html','app.html','about.html','admin.html','for-teachers.html','stage.html','tag-lab-home.html','tag-lab-books.html','tag-lab-create.html','tag-lab-games.html','tag-lab-library.html','tag-lab-live.html','tag-lab-mixer.html','tag-lab-students.html','game-lab-preview.html']

class TagV24BrandAndType(unittest.TestCase):
 def test_search_favicons_square_and_compatible(self):
  for path in ('assets/brand/tag-favicon-v24.png','short-link/assets/brand/tag-favicon-v24.png'):
   p=(ROOT/path).read_bytes()
   self.assertEqual(p[:8],bytes([137,80,78,71,13,10,26,10]),path)
   self.assertEqual(struct.unpack('>II',p[16:24]),(128,128),path)
   self.assertGreater(len(p),2000,path)
  for path in ('assets/brand/tag-share-v24.png','short-link/assets/brand/tag-share-v24.png'):
   p=(ROOT/path).read_bytes()
   self.assertEqual(struct.unpack('>II',p[16:24]),(1200,630))
 def test_public_search_page_is_indexable_and_uses_new_icon(self):
  public=read('short-link/index.html')
  self.assertIn('content="index,follow',public)
  self.assertIn('rel="canonical" href="https://teachgame.onrender.com/"',public)
  self.assertIn('href="/assets/brand/tag-favicon-v24.png"',public)
  self.assertIn('https://teachgame.onrender.com/assets/brand/tag-share-v24.png',public)
  self.assertIn('href="/student/"',public)
  self.assertIn('href="/teacher/"',public)
  self.assertNotIn('tag-logo-v15.png',public)
 def test_all_live_portal_pages_rebrand_without_touching_credentials(self):
  for path in PAGES:
   with self.subTest(path=path):
    html=read(path)
    self.assertNotIn('tag-logo-dark-v21.png',html)
    self.assertNotIn('tag-logo-v15.png',html)
    self.assertNotIn('tag-icon.svg',html)
    self.assertIn('/assets/brand/tag-favicon-v24.png',html)
  studio=read('studio.html')
  self.assertIn('id="tagBookAi"',studio)
  self.assertIn('id="bankSearch"',studio)
  self.assertIn('id="generateQuiz"',studio)
  self.assertIn('tag-studio-bank-ai-v24.css?v=24.0',studio)
  portal=read('portal.js')
  self.assertIn('encodeURIComponent(isSchoolId?quizLink:link)',portal)
  self.assertIn('student.cardCode',portal)
 def test_installed_app_icon_has_same_brand(self):
  manifest=json.loads(read('manifest.webmanifest'))
  self.assertEqual(manifest['short_name'],'TAG')
  paths={item['src'] for item in manifest['icons']}
  self.assertIn('/assets/brand/tag-favicon-v24.png',paths)
  for p,sz in [('assets/pwa/tag-192.png',192),('assets/pwa/tag-512.png',512),
               ('assets/pwa/tag-maskable-512.png',512),('assets/pwa/tag-apple-180.png',180)]:
   png=(ROOT/p).read_bytes()
   self.assertEqual(struct.unpack('>II',png[16:24]),(sz,sz))
 def test_bank_and_generator_scope_and_controls(self):
  html=read('studio.html')
  for id in ('bankSearch','bankDifficulty','bankGrade','bankSemester','bankUnit','bankLesson','bankType'):
   self.assertIn('for="'+id+'"',html)
  self.assertIn('id="tag24GeneratorTitle"',html)
  self.assertIn('id="tag24BankTitle"',html)
  css=read('tag-studio-bank-ai-v24.css')
  self.assertIn('body.v105-studio #view-bank .bank-item h4',css)
  self.assertIn('body.v105-studio #view-generator .tag-book-grid',css)
  self.assertIn('max-width:540px',css)
  self.assertIn('max-width:370px',css)
  self.assertNotIn('#view-live',css)
  self.assertNotIn('game-lab',css)
if __name__=='__main__':unittest.main()
