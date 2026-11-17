"""Design-only integration for CHAMPION V5 illustrations in the existing live classroom game."""
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCENES=('tag-daylight','tag-finals','tag-royal','tag-celebration',
        'tag-hall','tag-neon','tag-trophy','tag-elegant')
ASSETS=('bg-daylight-v4.svg','bg-finals-v4.svg','bg-royal-v5.svg',
        'bg-celebration-v5.svg','bg-hall-v5.svg','bg-neon-v5.svg',
        'bg-trophy-v5.svg','bg-elegant-v5.svg')

class TagLiveVisualV1(unittest.TestCase):
    def test_scene_options_allow_current_live_room_controls(self):
        setup=(ROOT/'studio.html').read_text(encoding='utf-8')
        teacher=(ROOT/'app.js').read_text(encoding='utf-8')
        server=(ROOT/'server.py').read_text(encoding='utf-8')
        for scene in SCENES:
            self.assertIn('value="'+scene+'"',setup)
            self.assertIn("'"+scene+"'",teacher)
            self.assertIn("'"+scene+"'",server)
        self.assertIn("action=='background'",server)
        self.assertIn("room['background']=new_scene",server)

    def test_all_eight_background_assets_exist_and_css_is_safely_scoped(self):
        skin=(ROOT/'tag-live-visual-v1.css').read_text(encoding='utf-8')
        for scene,asset in zip(SCENES,ASSETS):
            self.assertIn('data-scene="'+scene+'"',skin)
            self.assertIn(asset,skin)
            self.assertTrue((ROOT/'assets/champion'/asset).is_file())
        self.assertIn('[data-bo-question="live"]:not([data-champion="true"])',skin)
        self.assertIn('.answers .answer',skin)
        self.assertNotIn('onClick=',skin)
        self.assertNotIn('fetch(',skin)

    def test_pages_load_visual_only_skin_after_existing_styles(self):
        for page in ('student.html','stage.html','studio.html'):
            html=(ROOT/page).read_text(encoding='utf-8')
            self.assertIn('tag-live-visual-v1.css?v=1.0',html)
        student=(ROOT/'student.html').read_text(encoding='utf-8')
        self.assertLess(student.index('booyah-student-fit-v128.css'),
                        student.index('tag-live-visual-v1.css'))
        self.assertIn('champion-live-v2.css?v=2.0',student)

if __name__=='__main__': unittest.main()
