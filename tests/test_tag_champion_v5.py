"""CHAMPION TAG V5 regressions: elegant 8-background picker and legacy preservation."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VISIBLE = ('daylight','finals','royal','celebration','hall','neon','trophy','elegant')
LEGACY = ('stadium','night','lights','arena','grid','minimal')

class ChampionV5(unittest.TestCase):
    def test_exactly_two_stadiums_six_non_stadiums(self):
        html=(ROOT/'champion.html').read_text(encoding='utf-8')
        for grid_id in ('createBackgroundGrid','activeBackgroundGrid'):
            grid=re.search(r'<div class="ct-background-grid" id="'+grid_id+r'"[^>]*>(.*?)</div>',html,re.S)
            self.assertIsNotNone(grid)
            codes=re.findall(r'data-ct-bg="([^"]+)"',grid.group(1))
            self.assertEqual(codes,list(VISIBLE))
        for name in VISIBLE[2:]:
            self.assertTrue((ROOT/'assets/champion'/('bg-'+name+'-v5.svg')).is_file())
            css=(ROOT/'champion-backgrounds-v5.css').read_text(encoding='utf-8')
            self.assertIn('bg-'+name+'-v5.svg',css)

    def test_legacy_compatibility_no_data_loss(self):
        import tag_champion as champion
        self.assertEqual(champion.DEFAULT_BACKGROUND,'daylight')
        self.assertTrue(set(VISIBLE+LEGACY).issubset(champion.BACKGROUNDS))
        theme=(ROOT/'champion-theme-engine-v3.js').read_text(encoding='utf-8')
        script=(ROOT/'champion-tag.js').read_text(encoding='utf-8')
        for name in LEGACY:
            self.assertIn(name+':',theme)
        self.assertIn('visibleBackgrounds',theme)
        self.assertIn('syncLegacyOption(context,state.background)',script)
        self.assertNotIn('state.background=VISUAL.themes[value].defaultBackground',script)

    def test_current_page_and_projector_use_same_css(self):
        for page in ('champion.html','champion-board.html'):
            html=(ROOT/page).read_text(encoding='utf-8')
            self.assertIn('champion-backgrounds-v5.css?v=5.0',html)
            self.assertIn('champion-theme-engine-v3.js?v=5.0',html)
            self.assertIn('champion-ceremony-v4.js?v=4.0',html)

if __name__=='__main__':
    unittest.main()
