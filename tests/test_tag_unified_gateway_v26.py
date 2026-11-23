"""TAG V26: static router generator and collision-free origin routing contract."""
import os, subprocess, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class GatewayContract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  subprocess.run(['python','tools/build_teachgame_unified.py'],
        cwd=ROOT,check=True,timeout=25)
  cls.out=ROOT/'short-link-unified'
 def test_root_keeps_indexed_landing(self):
  home=(self.out/'index.html').read_text(encoding='utf8')
  self.assertIn('https://teachgame.onrender.com/',home)
  self.assertIn('href="/student/"',home)
  self.assertIn('href="/teacher/"',home)
  self.assertIn('content="index,follow',home)
  self.assertNotIn('quiznova-arena-online.onrender.com',home)
 def test_backend_html_routes_are_not_shadowed(self):
  for name in ('student.html','studio.html','about.html','admin.html',
               'for-teachers.html','stage.html','app.html','tag-lab-home.html'):
   with self.subTest(name=name):
    self.assertFalse((self.out/name).exists(),
                     'Render serves local files before proxy routes: '+name)
 def test_entry_cold_start_redirects_to_public_domain(self):
  for name,dest in [('teacher','/portal.html?teacher=1'),
                    ('student','/student.html'),('app','/app.html')]:
   p=self.out/name/'index.html'
   self.assertTrue(p.is_file(),name)
   s=p.read_text(encoding='utf8')
   self.assertIn('https://teachgame.onrender.com'+dest,s)
   self.assertNotIn('quiznova-arena-online.onrender.com',s)
   self.assertNotIn('فتح الصفحة مباشرة',s)
  js=(self.out/'wake-loader.js').read_text(encoding='utf8')
  self.assertIn('const publicBase="https://teachgame.onrender.com"',js)
  self.assertIn('!target.startsWith(publicBase+"/")',js)
  self.assertIn('const base="https://quiznova-arena-online.onrender.com"',js)
 def test_blueprint_is_targeted_and_same_origin(self):
  data=(ROOT/'deploy/teachgame-unified.render.yaml').read_text(encoding='utf8')
  self.assertIn('name: teachgame',data)
  self.assertIn('staticPublishPath: short-link-unified',data)
  self.assertIn('source: /portal.html',data)
  self.assertIn('source: /api/*',data)
  self.assertIn('source: /*',data)
  self.assertEqual(data.count('type: rewrite'),3)
  self.assertNotIn('type: redirect',data)
  self.assertNotIn('name: quiznova-arena-online',data)
 def test_keep_public_static_icons_robots_and_sitemap(self):
  for p in ('assets/brand/tag-favicon-v24.png','assets/brand/tag-spatial-identity-v3.webp',
            'sitemap.xml','robots.txt'):
   self.assertTrue((self.out/p).exists(),p)
if __name__=='__main__':unittest.main()
