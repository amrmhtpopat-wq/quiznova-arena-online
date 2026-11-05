"""Regression checks for reference palette, mature avatars and direct answer UX."""
import pathlib
import unittest

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

    def test_portraits_are_independent_rendered_webp_assets(self):
        for i in range(1,9):
            path=ROOT/f'assets/avatars3d/m{i:02d}.webp'
            self.assertTrue(path.is_file(),str(path))
            raw=path.read_bytes()
            self.assertGreater(len(raw),8000)
            self.assertLess(len(raw),260000)
            self.assertTrue(raw.startswith(b'RIFF') and raw[8:12]==b'WEBP')
        for name in ('app.js','student.js','stage.js','portal.js'):
            self.assertIn("id+'.webp'",read(name))
        store=read('platform_store.py')
        self.assertIn("AVATAR_3D_IDS = [f'n{i:02}'",store)

    def test_high_contrast_inputs_and_fresh_client_assets(self):
        css=read('v106-contrast.css')
        self.assertIn('--qn-field-color:#0c2548',css)
        self.assertIn('--qn-field-bg:#f7fbff',css)
        self.assertIn('color:var(--qn-field-color)!important',css)
        self.assertIn('-webkit-text-fill-color:var(--qn-field-color)!important',css)
        for page in ('index.html','studio.html','student.html','stage.html'):
            html=read(page)
            self.assertIn('v106-contrast.css?v=10.4.2',html)
            self.assertGreater(html.index('v106-contrast.css'),html.index('v105-reference.css'))
        online=read('student.js')
        offline=read('app.js')
        self.assertIn("$('.answer').forEach(b=>b.disabled=true)",online)
        self.assertIn("$('.answer-btn').forEach(b=>b.disabled=true)",offline)
        self.assertIn('void submitAnswer(session.currentRoomState)',online)
        self.assertIn('void submitGameAnswer()',offline)
        studio=read('studio.html')
        self.assertIn('<option value="speed" selected>',studio)

    def test_original_career_and_jordanian_avatars_and_educational_hero(self):
        for i in range(1,9):
            asset=ROOT/f'assets/avatars3d/n{i:02d}.webp'
            self.assertTrue(asset.is_file(),str(asset))
            raw=asset.read_bytes()
            self.assertGreater(len(raw),5000)
            self.assertTrue(raw[:4]==b'RIFF' and raw[8:12]==b'WEBP')
        hero=ROOT/'assets/backgrounds/quiznova-learning.webp'
        self.assertTrue(hero.is_file())
        self.assertGreater(hero.stat().st_size,40000)
        for page in ('index.html','studio.html'):
            self.assertIn('/assets/backgrounds/quiznova-learning.webp',read(page))
        self.assertIn('v107-prelaunch.css?v=10.5',read('student.html'))
        self.assertIn('100dvh',read('v107-prelaunch.css'))
        self.assertIn('grid-template-columns:repeat(2,minmax(0,1fr))',read('v107-prelaunch.css'))
        self.assertIn('id="cardCode"',read('student.html'))
        self.assertIn('id="cardProfile"',read('student.html'))

    def test_multiple_choice_uses_all_button_selector(self):
        student=read('student.js')
        self.assertGreaterEqual(student.count("$$('.answer').forEach"),2)
        self.assertIn("$$('.answer').forEach(b=>b.disabled=true)",student)
        self.assertIn("$$('.answer').forEach(b=>b.disabled=false)",student)

    def test_teacher_photo_is_not_in_profile_card(self):
        dashboard=read('index.html')
        studio=read('studio.html')
        self.assertNotIn('teacher-avatar-pro',dashboard)
        self.assertNotIn('class="teacher-avatar"',studio)
        self.assertIn('id="teacherSideName"',dashboard)
        self.assertIn('id="studioTeacherName"',studio)

if __name__=='__main__':
    unittest.main()
