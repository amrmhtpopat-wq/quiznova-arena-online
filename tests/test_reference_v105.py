"""Regression checks for reference palette, mature avatars and direct answer UX."""
import base64
import pathlib
import unittest
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
read=lambda name:(ROOT/name).read_text(encoding='utf-8')

class VisualAndDirectAnswerTests(unittest.TestCase):
    def test_page_styles_are_ordered_after_older_themes(self):
        for filename in ('index.html','studio.html','student.html','stage.html'):
            page=read(filename)
            self.assertIn('v105-reference.css?v=10.4.1',page)
            self.assertGreater(page.index('v105-reference.css'),page.index('v104-theme.css'))
            self.assertIn('v105-',page)

    def test_reference_palette_and_responsive_modes(self):
        css=read('v105-reference.css')
        for color in ('#041029','#061735','#7a29e9','#a43cfa','#00cafa','#53e6ff'):
            self.assertIn(color,css)
        for cls in ('v105-studio','v105-portal','v105-student','v105-stage'):
            self.assertIn(cls,css)
        self.assertIn('prefers-reduced-motion',css)
        self.assertIn('max-width:540px',css)

    def test_instant_answers_student_and_local_game(self):
        online=read('student.js')
        local=read('app.js')
        for script in (online,local):
            self.assertIn("['single','tf','poll'].includes(",script)
            self.assertIn('v105-instant-submit',script)
        self.assertIn('submitAnswer(session.currentRoomState)',online)
        self.assertIn('void submitGameAnswer()',local)
        self.assertIn("if(type==='multi')",online)
        self.assertIn("if(q.type==='multi')",local)

    def test_portraits_are_embedded_and_eight_separate_crops(self):
        boxes=set()
        for i in range(1,9):
            path=ROOT/f'assets/avatars3d/m{i:02d}.svg'
            tree=ET.parse(path)
            root=tree.getroot()
            boxes.add(root.get('viewBox'))
            image=root.find('{http://www.w3.org/2000/svg}image')
            self.assertIsNotNone(image)
            embedded=image.get('href')
            self.assertTrue(embedded.startswith('data:image/webp;base64,'))
            raw=base64.b64decode(embedded.split(',',1)[1],validate=True)
            self.assertTrue(raw.startswith(b'RIFF') and b'WEBP' in raw[:16])
        self.assertEqual(len(boxes),8)
        store=read('platform_store.py')
        self.assertIn("AVATAR_3D_IDS = [f'm{i:02}'",store)

    def test_teacher_photo_is_not_in_profile_card(self):
        dashboard=read('index.html')
        studio=read('studio.html')
        self.assertNotIn('teacher-avatar-pro',dashboard)
        self.assertNotIn('class="teacher-avatar"',studio)
        self.assertIn('id="teacherSideName"',dashboard)
        self.assertIn('id="studioTeacherName"',studio)

if __name__=='__main__':
    unittest.main()
