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

    def test_live_room_request_uses_teacher_token_and_actionable_errors(self):
        source=read('app.js')
        self.assertIn("const teacherToken=window.QN9_TOKEN||localStorage.getItem('qn9_teacher_token')||''",source)
        self.assertIn("'Authorization':'Bearer '+teacherToken",source)
        self.assertIn("if(!r.ok||!d.ok)throw Object.assign",source)
        self.assertIn("e.status===401||e.message==='login_required'",source)
        self.assertNotIn("تعذر إنشاء الغرفة. تحقق من اتصال الخادم بالإنترنت ثم حاول مرة أخرى",source)
        self.assertIn("script.src='/app.js?v=11.2'",read('studio-auth.js'))
        self.assertIn("studio-auth.js?v=11.2",read('studio.html'))

    def test_booyah_classroom_viewport_and_progress_contract(self):
        css=read('booyah-classroom.css')
        self.assertIn('grid-template-columns:repeat(2,minmax(0,1fr))',css)
        self.assertIn('overflow:hidden!important',css)
        self.assertIn('::placeholder',css)
        for page in ('index.html','studio.html','student.html','stage.html'):
            self.assertIn('booyah-classroom.css?v=10.8',read(page))
        self.assertIn('fitQuestionToViewport',read('student.js'))
        self.assertIn('qn-xp-progress',read('student.js'))
        self.assertIn('qn-card-progress',read('portal.js'))
        self.assertIn('xpBreakdown',read('server.py'))

    def test_booyah_final_contrast_layer_loads_last_across_all_pages(self):
        css=read('booyah-contrast-v109.css')
        for selector in ('#view-live','#view-builder','#view-bank','#view-results','#view-play',
                         '.toggle-line','.bank-item','.summary-chip','.insight-card',
                         '.game-card','.answer-btn','.feedback','.leader',
                         'v105-student','v105-stage'):
            self.assertIn(selector,css)
        for name in ('index.html','studio.html','student.html','stage.html'):
            html=read(name)
            self.assertIn('/booyah-contrast-v109.css?v=10.9',html)
            self.assertGreater(html.index('booyah-contrast-v109.css'),html.index('booyah-classroom.css'))
            self.assertEqual(html.count('booyah-contrast-v109.css'),1)
        self.assertIn('body.v105-studio #view-play #gameArea .game-card h3',css)
        self.assertIn('body.v105-studio #view-results .insight-card strong',css)
        self.assertIn('body.v105-studio #view-bank .bank-item h4',css)
        self.assertIn('body.v105-studio :is(#view-live,#view-builder,#view-generator,#view-settings) .toggle-line',css)

    def test_focused_question_builder_has_clear_time_points_and_navigation(self):
        html=read('studio.html')
        css=read('booyah-builder-v110.css')
        script=read('app.js')
        for control in ('boQuestionRail','boRailAddQuestion','boQuestionProperties',
                        'quizTitle','quizSubject','quizGrade','saveQuiz'):
            self.assertIn('id="'+control+'"',html)
        self.assertIn('booyah-builder-v110.css?v=11.0',html)
        self.assertGreater(html.index('booyah-builder-v110.css'),html.index('booyah-contrast-v109.css'))
        self.assertIn('bo-optional-tools',html)
        self.assertIn('bo-question-editor',css)
        self.assertIn('grid-template-columns:repeat(2,minmax(0,1fr))',css)
        self.assertIn('time:20,points:1000',script)
        self.assertIn('id="boPropertyTime"',script)
        self.assertIn('id="boPropertyPoints"',script)
        self.assertIn('window.boSetQuestionTime',script)
        self.assertIn('window.boSetQuestionPoints',script)
        self.assertIn('window.boSelectQuestion',script)
        self.assertIn('boActiveQuestionId=q.id;',script)
        self.assertIn("return toast('السؤال '",script)

    def test_quiz_save_is_cloud_acknowledged_and_library_immediate(self):
        studio=read('studio.html')
        app=read('app.js')
        auth=read('studio-auth.js')
        css=read('booyah-quiz-polish-v111.css')
        self.assertIn('window.QN9_SAVE_NOW=()=>flush()',auth)
        self.assertIn("const stored=typeof window.QN9_SAVE_NOW==='function'&&await window.QN9_SAVE_NOW()",app)
        self.assertIn("$('#librarySearch').value=''",app)
        self.assertIn("go('library');",app)
        self.assertIn("function openNewQuiz(){resetBuilder();go('builder')}",app)
        self.assertIn("window.openLiveQuizById=id=>go('live',{quizId:id})",app)
        self.assertIn('function renderLiveLanding(preferredQuizId=null)',app)
        self.assertIn('function newestQuizzes()',app)
        self.assertIn('bo-saved-chip',app)
        self.assertIn('booyah-quiz-polish-v111.css?v=11.1',studio)
        self.assertIn('booyah-quiz-polish-v111.css?v=11.1',read('student.html'))
        self.assertGreater(studio.index('booyah-quiz-polish-v111.css'),studio.index('booyah-builder-v110.css'))
        for name in ('bo-library-quiz','bo-library-actions','#view-live','#view-play','v105-student'):
            self.assertIn(name,css)

    def test_studio_deep_links_preserved_through_teacher_auth(self):
        studio_auth=read('studio-auth.js')
        portal=read('portal.js')
        app=read('app.js')
        self.assertIn("const loginTarget='/?next='+encodeURIComponent('/studio.html#'+safeView)",studio_auth)
        self.assertIn("lastStatus.every(code=>code===401)",studio_auth)
        self.assertIn("throw Error('temporary_auth_unavailable')",studio_auth)
        self.assertIn("document.querySelector('#qnRetryStudio')",studio_auth)
        self.assertIn("function pendingStudioDestination()",portal)
        self.assertIn("if(resumeStudioAfterLogin())return",portal)
        self.assertIn("history.replaceState(null,'','#'+view)",app)
        self.assertIn("portal.js?v=11.2",read('index.html'))
        self.assertIn("studio-auth.js?v=11.2",read('studio.html'))
        self.assertIn("script.src='/app.js?v=11.2'",studio_auth)

    def test_teacher_photo_is_not_in_profile_card(self):
        dashboard=read('index.html')
        studio=read('studio.html')
        self.assertNotIn('teacher-avatar-pro',dashboard)
        self.assertNotIn('class="teacher-avatar"',studio)
        self.assertIn('id="teacherSideName"',dashboard)
        self.assertIn('id="studioTeacherName"',studio)

if __name__=='__main__':
    unittest.main()
