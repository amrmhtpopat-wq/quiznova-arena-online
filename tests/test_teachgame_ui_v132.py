"""TEACH AND GAME V13.2: old public brand does not survive in screens or reprinted cards."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PAGES=['index.html','student.html','studio.html','stage.html','about.html','for-teachers.html','admin.html']
COPY=['portal.js','stage.js','booyah-countdown-v121.js','media_library.js','studio-auth.js']
class UnifiedBrand(unittest.TestCase):
 def test_all_visible_titles_and_labels(self):
  for path in PAGES+COPY:
   with self.subTest(page=path):
    text=(ROOT/path).read_text(encoding='utf-8')
    if path!='studio-auth.js': self.assertIn('TEACH AND GAME',text)
    if path!='index.html':
     self.assertNotIn('QUIZ ARENA',text)
     self.assertNotIn('BOOYAHJO',text)
     self.assertNotIn('بويا جو',text)
  self.assertIn('tag-stage-logo',(ROOT/'stage.js').read_text(encoding='utf-8'))
  self.assertIn('stage.js?v=16.0',(ROOT/'stage.html').read_text(encoding='utf-8'))
  self.assertIn("a.download='TAG_'+liveRoom+'_report.xlsx';",(ROOT/'app.js').read_text(encoding='utf-8'))
 def test_cards_reissued_without_deletion(self):
  text=(ROOT/'portal.js').read_text(encoding='utf-8')
  self.assertIn('class="tag-card-logo"',text)
  self.assertIn('data-card-version="BADJ-TH42"',text)
  self.assertIn('encodeURIComponent(student.card)',text)
  self.assertIn('student.cardCode',text)
  self.assertIn("const base=location.origin+'/student.html?card=';",text)
  self.assertNotIn('https://teachgame.onrender.com/student.html?card=',text)
  self.assertIn('window.print()',text)
  self.assertNotIn('BOOYAHJO',text)
  self.assertNotIn('QUIZ ARENA',text)
  self.assertIn('id="reissueTeachGameCards"',(ROOT/'index.html').read_text(encoding='utf-8'))
 def test_original_site_and_short_alias_unchanged(self):
  content=(ROOT/'index.html').read_text(encoding='utf-8')
  self.assertIn('https://quiznova-arena-online.onrender.com/',content)
  self.assertIn('"name": "TEACH AND GAME"',content)
  self.assertNotIn('BOOYAHJO',content)
  self.assertNotIn('بويا جو',content)
  redirect=(ROOT/'short-link/index.html').read_text(encoding='utf-8')
  self.assertIn('location.replace(target+location.search+location.hash)',redirect)
  self.assertIn('TEACH AND GAME',redirect)
if __name__=='__main__':
 unittest.main()
