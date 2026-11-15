"""TAG V20: official transparent logo appears without a visual box anywhere. """
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class TransparentLogoV20(unittest.TestCase):
 def test_site_branding_rules(self):
  css=(ROOT/'tag-brand-v2.css').read_text(encoding='utf-8')
  self.assertIn('TAG V20',css)
  self.assertNotIn('TAG V17 —',css)
  self.assertNotIn('background:linear-gradient(160deg,#fff',css)
  self.assertIn('background:transparent!important',css)
  self.assertIn('padding:0!important',css)
  self.assertIn('border:0!important',css)
  self.assertIn('@media print',css)
 def test_all_app_pages_have_fresh_stylesheet(self):
  for path in ('index.html','student.html','studio.html','admin.html','stage.html','about.html','for-teachers.html'):
   with self.subTest(path=path):
    html=(ROOT/path).read_text(encoding='utf-8')
    self.assertIn('tag-brand-v2.css?v=20.0',html)
 def test_png_remains_transparent(self):
  for path in ('assets/brand/tag-logo-v15.png','short-link/assets/brand/tag-logo-v15.png'):
   data=(ROOT/path).read_bytes()
   self.assertEqual(data[:8],b'\x89PNG\r\n\x1a\n')
   self.assertIn(b'tRNS',data)
 def test_static_splash_has_no_logo_box(self):
  css=(ROOT/'short-link/wake-loader.css').read_text(encoding='utf-8')
  start=css.index('.splash-logo{')
  end=css.index('}',start)
  declaration=css[start:end]
  self.assertIn('background:transparent',declaration)
  self.assertIn('border:0',declaration)
  self.assertIn('padding:0',declaration)
  self.assertIn('box-shadow:none',declaration)
if __name__=='__main__': unittest.main()
