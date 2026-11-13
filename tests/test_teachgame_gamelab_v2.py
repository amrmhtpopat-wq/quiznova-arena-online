"""Guard the isolated TeachGame Game Lab V2 experiment from routing and data regressions."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

def read(name):
    return (ROOT/name).read_text(encoding='utf-8')

class GameLabV2(unittest.TestCase):
    def test_teacher_has_a_discoverable_visual_game_lab(self):
        studio=read('studio.html')
        self.assertIn('data-view="gamelab"', studio)
        self.assertIn('id="view-gamelab"', studio)
        self.assertIn('id="tg2Steps"', studio)
        self.assertIn('id="tg2Main"', studio)
        self.assertIn('teachgame-lab-v2.css?v=2.0', studio)
        self.assertIn('data-jump="gamelab"', studio)

    def test_auth_and_navigation_load_after_existing_app(self):
        auth=read('studio-auth.js')
        app=read('app.js')
        self.assertIn("'gamelab'", auth)
        self.assertIn("labScript.src='/teachgame-lab-v2.js?v=2.0'", auth)
        self.assertIn('script.onload=()=>{const labScript=', auth)
        self.assertIn("gamelab:['مختبر الألعاب'", app)
        self.assertIn("if(view==='gamelab'&&window.TG_LAB_V2)", app)

    def test_four_games_are_real_and_reuse_existing_quizzes(self):
        script=read('teachgame-lab-v2.js')
        for key in ('quiz','wheel','boxes','pairs'):
            self.assertIn(key+":{title:", script)
        for action in ("action==='answer'", "action==='spin'", "action==='box'",
                       "action==='flip'", "action==='start'"):
            self.assertIn(action, script)
        self.assertIn('const quizList=()=>typeof DB', script)
        self.assertIn('window.QN9_SAVE_NOW()', script)
        self.assertIn("if(newSource!==state.source)state.quizId=''", script)
        self.assertIn('if(!playable(quiz,state.template))', script)
        self.assertIn('const esc=v=>', script)

    def test_accessible_theme_and_no_student_changes(self):
        css=read('teachgame-lab-v2.css')
        self.assertIn('color:#17334e!important', css)
        self.assertIn('input[type="radio"]', css)
        self.assertIn('prefers-reduced-motion', css)
        self.assertIn('@media(max-width:650px)', css)
        self.assertIn('#view-gamelab', css)
        # This experiment must never ship a new student result pipeline.
        script=read('teachgame-lab-v2.js')
        self.assertNotIn('/api/room/start', script)
        self.assertNotIn('/api/teacher/results', script)

if __name__=='__main__':
    unittest.main()
