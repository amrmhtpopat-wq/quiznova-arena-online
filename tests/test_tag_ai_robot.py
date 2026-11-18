"""TAG AI robot display regression: authentic mascot motion and safe assistant behavior."""
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class TagAIRobotTests(unittest.TestCase):
    def test_svg_mascot_and_reduced_motion_version(self):
        animated=ROOT/'assets/brand/tag-ai-robot-slow-v1.svg'
        static=ROOT/'assets/brand/tag-ai-robot-still-v1.svg'
        for path in (animated,static):
            tree=ET.parse(path)
            self.assertTrue(tree.getroot().tag.endswith('svg'))
            self.assertIn('TAG AI',path.read_text('utf-8'))
        a=ET.parse(animated).getroot()
        b=ET.parse(static).getroot()
        ns='{http://www.w3.org/2000/svg}'
        self.assertGreaterEqual(len(list(a.iter(ns+'animateTransform'))),4)
        self.assertEqual(len(list(b.iter(ns+'animateTransform'))),0)

    def test_assistant_button_keeps_dialog_and_gains_robot_image(self):
        script=(ROOT/'tag-ai-assistant-v1.js').read_text(encoding='utf-8')
        style=(ROOT/'tag-ai-assistant-v1.css').read_text(encoding='utf-8')
        shell=(ROOT/'tag-lab-visual-v1.js').read_text(encoding='utf-8')
        self.assertIn("fab.id='tagaiOpen'",script)
        self.assertIn("aria-label','فتح المساعد الذكي TAG AI'",script)
        self.assertIn('tag-ai-robot-slow-v1.svg',script)
        self.assertIn('tag-ai-robot-still-v1.svg',script)
        self.assertIn("fab.addEventListener('click',open)",script)
        self.assertNotIn("fab.append(native('span','tagai-fab-icon'",script)
        self.assertIn('background:transparent!important',style)
        self.assertIn('tagai-robot-art',style)
        self.assertIn('if(!student&&!display)',shell)
        self.assertIn('/tag-ai-assistant-v1.js?v=1.4.0',shell)
        self.assertNotIn("headerDock.append(fab)",script)
        self.assertIn("d.body.append(fab,overlay)",script)
        self.assertIn('width:49px;height:58px',style)
        self.assertIn('position:fixed;left:14px',style)
        self.assertNotIn('position:fixed;bottom:13px;left:19px',style)

if __name__ == '__main__':
    unittest.main()
