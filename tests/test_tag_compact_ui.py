"""Regression checks for compact layout, chatbot docking and responsive safety.

Static guardrails only; real browser smoke checks remain separate.
"""
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PAGES=(
 'tag-lab-home.html','tag-lab-books.html','tag-lab-create.html',
 'tag-lab-games.html','tag-lab-library.html','tag-lab-mixer.html',
 'tag-lab-account.html','tag-lab-assign.html','tag-lab-student.html',
 'game-lab-preview.html','tag-lab-live-teacher.html',
 'tag-lab-live-student.html','tag-lab-live-display.html',
 'tag-lab-results.html',
)

class CompactLayoutTests(unittest.TestCase):
 def test_pages_share_the_same_version_of_compact_design(self):
  for page in PAGES:
   html=(ROOT/page).read_text(encoding='utf-8')
   with self.subTest(page=page):
    self.assertIn('tag-lab-visual-v1.css?v=1.4.0',html)
    self.assertIn('tag-lab-visual-v1.js?v=1.4.0',html)

 def test_compact_layout_uses_real_dimensions_not_browser_zoom(self):
  css=(ROOT/'tag-lab-visual-v1.css').read_text(encoding='utf-8')
  self.assertIn('--tagv-sidebar-width:228px',css)
  self.assertIn('--tagv-content-max:1260px',css)
  self.assertIn('--tagv-content-max:1090px',css)
  self.assertIn('--tagv-sidebar-width:clamp(176px,13.55vw,185px)',css)
  self.assertIn('TAG LAB REFERENCE SCALE V1',css)
  self.assertIn('TAG LAB COMPACT UI V1',css)
  self.assertNotRegex(css,r'(?i)(?:^|[;\\s])zoom\\s*:')
  self.assertNotIn('transform:scale(.94)',css)
  self.assertIn('min-height:85px!important',css)
  self.assertIn('@media(max-width:700px)',css)

 def test_robot_docked_outside_content_without_changing_animation(self):
  robot=(ROOT/'tag-ai-assistant-v1.js').read_text(encoding='utf-8')
  css=(ROOT/'tag-ai-assistant-v1.css').read_text(encoding='utf-8')
  shell=(ROOT/'tag-lab-visual-v1.js').read_text(encoding='utf-8')
  self.assertNotIn('headerDock.append(fab)',robot)
  self.assertIn('d.body.append(fab,overlay)',robot)
  self.assertIn("fab.addEventListener('click',open)",robot)
  self.assertIn('tag-ai-robot-slow-v1.svg',robot)
  self.assertIn('tag-ai-robot-still-v1.svg',robot)
  self.assertIn('.tagai-fab{',css)
  self.assertIn('position:fixed;left:14px',css)
  self.assertIn('width:49px;height:58px',css)
  self.assertIn('tagv-compact-root',shell)
  self.assertIn("if(!student&&!display)",shell)
  self.assertIn('/tag-ai-assistant-v1.css?v=1.4.0',shell)
  self.assertIn('/tag-ai-assistant-v1.js?v=1.4.0',shell)

if __name__=='__main__':
 unittest.main()
