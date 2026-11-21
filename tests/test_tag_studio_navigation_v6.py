"""Static regression contract: grouped studio page map and accessible drawer."""
import re
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def source(name):return (ROOT/name).read_text(encoding='utf-8')

class StudioNavigationV6Contract(unittest.TestCase):
 def test_original_pages_preserved_and_grouped(self):
  html=source('studio.html')
  keys=re.findall(r'<button class="nav-item[^"]*" data-view="([^"]+)"',html)
  self.assertEqual(sorted(keys),sorted(['dashboard','generator','builder','bank','library',
                                         'media','live','play','results','settings']))
  for group in ('start','content','classroom','manage'):
   self.assertIn('data-tag-studio-group="'+group+'"',html)
   self.assertIn('id="tagStudioGroup-'+group+'"',html)
  self.assertIn('id="tagStudioNavBackdrop"',html)
  self.assertIn('aria-controls="sidebar"',html)
  self.assertIn('data-jump="generator"',html)
  self.assertIn('data-jump="builder"',html)
  self.assertIn('data-jump="live"',html)
  self.assertIn('data-jump="library"',html)
  for link in ('/champion.html','/tag-lab-home.html?v=34','href="/"'):
   self.assertIn(link,html)
  self.assertIn('tag-studio-navigation-v6.css?v=6',html)
  self.assertIn('studio-auth.js?v=13.7',html)
 def test_navigation_loaded_after_teacher_auth_and_does_not_write_student_data(self):
  auth=source('studio-auth.js')
  nav=source('tag-studio-navigation-v6.js')
  self.assertIn("studioNavigation.src='/tag-studio-navigation-v6.js?v=6'",auth)
  for text in ("(max-width:1024px)","tag-studio-nav-open","aria-expanded",
               "Escape","backdrop.addEventListener","sidebar.inert",
               "tag-studio-group-toggle","data-view"):
   self.assertIn(text,nav)
  for forbidden in ('/api/student/','/api/room/','localStorage.setItem','/api/teacher/snapshot','fetch('):
   self.assertNotIn(forbidden,nav)
 def test_css_keeps_desktop_and_print_separate(self):
  css=source('tag-studio-navigation-v6.css')
  self.assertIn('@media (max-width:1024px)',css)
  self.assertIn('@media (min-width:1025px)',css)
  self.assertIn('width:min(344px,calc(100vw - 20px))',css)
  self.assertIn('overflow-y:auto!important',css)
  self.assertIn('tag-studio-nav-group.is-expanded',css)
  self.assertIn('tag-studio-quickhub-grid',css)
  self.assertIn('@media print',css)
  self.assertIn('body.v105-studio',css)

if __name__=='__main__':unittest.main()
