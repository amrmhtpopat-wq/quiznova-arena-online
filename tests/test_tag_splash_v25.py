"""V25: branded wake redirect without manual Render bypass and no unstyled 3D mount."""
import re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
read=lambda p:(ROOT/p).read_text(encoding="utf-8")
SPLASH=["teacher/index.html","student/index.html","studio/index.html","card/index.html",
"champion/index.html","play/index.html","solo/index.html","stage/index.html",
"admin/index.html","about/index.html","for-teachers/index.html",
"about.html","admin.html","for-teachers.html","student.html","studio.html","app/index.html"]
class TagV25Safety(unittest.TestCase):
 def test_branded_wake_pages_are_automatic_only(self):
  for route in SPLASH:
   with self.subTest(route=route):
    html=read("short-link/"+route)
    self.assertIn('class="splash-logo" src="/assets/brand/tag-favicon-v24.png"',html)
    self.assertIn('class="wake-wordmark"',html)
    self.assertIn('wake-loader.js?v=25',html)
    self.assertIn('wake-loader.css?v=25',html)
    self.assertIn('id="wakeRetry" hidden',html)
    self.assertIn('window.TAG_ENTRY_GO=function(){location.replace(window.TAG_ENTRY_URL())}',html)
    self.assertIn('noindex,nofollow,noarchive',html)
    self.assertNotIn('wakeDirect',html)
    self.assertNotIn('فتح الصفحة مباشرة',html)
 def test_retry_only_after_timeout_and_modern_probe(self):
  js=read("short-link/wake-loader.js")
  self.assertNotIn('wakeDirect',js)
  self.assertNotIn('tag-logo-v15.png',js)
  self.assertIn('tag-favicon-v24.png?wake=',js)
  self.assertIn('setTimeout(go,280)',js)
  self.assertIn('retry.hidden=false',js)
  self.assertIn('maxWindow=95000',js)
  css=read("short-link/wake-loader.css")
  self.assertIn('.wake-wordmark',css)
 def test_static_home_routes_to_wake_pages(self):
  html=read("short-link/index.html")
  for route in ['/student/','/teacher/','/app/']:
   self.assertIn('href="'+route+'"',html)
  self.assertNotIn('href="https://quiznova-arena-online.onrender.com/app.html"',html)
  self.assertIn('rel="canonical" href="https://teachgame.onrender.com/"',html)
 def test_dashboard_stylesheet_is_required_before_reveal(self):
  html=read('index.html')
  self.assertIn('rel="preload" href="/tag-spatial-native-v3.css?v=25.1" as="style"',html)
  self.assertIn('tag-spatial-site-v3.js?v=25',html)
  js=read('tag-spatial-site-v3.js')
  self.assertIn("host.style.visibility='hidden'",js)
  self.assertIn("sheet.addEventListener('load',reveal",js)
  self.assertIn("sheet.addEventListener('error',()=>fallback",js)
  self.assertIn("host.style.visibility='visible'",js)
  self.assertIn("page.classList.add('tag-spatial-v4-fallback')",js)
  self.assertLess(js.index("host.style.visibility='hidden'"),js.index("shadow.appendChild(sheet)"))
  self.assertNotIn('window.location.reload()',js)
if __name__=="__main__":unittest.main()
