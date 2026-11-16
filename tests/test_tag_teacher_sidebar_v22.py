"""TAG V22 teacher sidebar scroll regression: all routes reachable at desktop 100% zoom."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]

class TestTeacherSidebarV22(unittest.TestCase):
 def test_stylesheet_loaded_only_on_portal(self):
  html=(ROOT/'index.html').read_text(encoding='utf-8')
  self.assertIn('tag-sidebar-scroll-v22.css?v=22.0',html)
  self.assertLess(html.index('tag-brand-v2.css?v=20.0'),html.index('tag-sidebar-scroll-v22.css?v=22.0'))
  self.assertIn('aside class="sidebar"',html)
  for section in ('home','classes','mastery','students','history','school'):
   self.assertIn(f'data-panel="{section}"',html)
  self.assertIn('class="sidebar-bottom"',html)
  self.assertIn('href="/studio.html"',html)
 def test_isolated_desktop_scroller(self):
  css=(ROOT/'tag-sidebar-scroll-v22.css').read_text(encoding='utf-8')
  for part in ('@media screen and (min-width: 1025px)',
               'body.v105-portal #workspace:not(.hidden) > aside.sidebar',
               'overflow-y: auto !important',
               'overflow-x: hidden !important',
               'height: 100dvh !important',
               'scrollbar-gutter: stable',
               'flex-shrink: 0 !important'):
   self.assertIn(part,css)
  self.assertNotIn('body.v105-studio',css)
  self.assertNotIn('body.v105-student',css)
 def test_mobile_style_untouched(self):
  text=(ROOT/'booyah-mobile-v123.css').read_text(encoding='utf-8')
  self.assertIn('overflow-x:auto!important',text)
  self.assertIn('body.v105-portal .workspace>.sidebar',text)
if __name__=='__main__':unittest.main()
