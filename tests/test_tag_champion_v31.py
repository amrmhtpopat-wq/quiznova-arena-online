"""CHAMPION TAG V3.1: regression checks for broadcaster contrast and pitch visibility."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class ChampionV31Readability(unittest.TestCase):
    def test_fix_is_loaded_last_on_creator_and_screen(self):
        for p in ('champion.html','champion-board.html'):
            content=(ROOT/p).read_text(encoding='utf-8')
            self.assertIn('champion-clarity-v3-1.css?v=3.1', content)
            self.assertLess(content.index('champion-themes-v3.css?v=3.0'),
                            content.index('champion-clarity-v3-1.css?v=3.1'))
    def test_broadcast_ink_and_winner_are_readable(self):
        css=(ROOT/'champion-clarity-v3-1.css').read_text(encoding='utf-8')
        for item in ('data-champion-theme="broadcast"',
                     '--ct-card-text:#092344','color:#092344!important',
                     'color:#086044!important','background:linear-gradient(145deg,#fff',
                     '.fixture-num span','.fixture-team.winner span'):
            self.assertIn(item,css)
    def test_stadium_mask_has_been_lightened(self):
        css=(ROOT/'champion-clarity-v3-1.css').read_text(encoding='utf-8')
        self.assertIn('rgba(2,10,25,.44)',css)
        self.assertIn('rgba(2,12,29,.22)',css)
        self.assertIn('bg-stadium.svg?v=31',css)
        self.assertIn('bg-arena.svg?v=31',css)
        for name in ['stadium','night','lights','arena']:
            svg=(ROOT/f'assets/champion/bg-{name}.svg').read_text(encoding='utf-8')
            self.assertIn('ctv4Grass',svg)
            self.assertIn('ctv4FieldClip',svg)
            self.assertIn('ctv4Flood',svg)
            self.assertIn('cy="795"',svg)
    def test_match_logic_unchanged(self):
        s=(ROOT/'tag_champion.py').read_text(encoding='utf-8')
        self.assertIn('def complete_match',s)
        self.assertIn('def update_appearance',s)
        self.assertIn('THEMES = (',s)

if __name__=='__main__': unittest.main()
