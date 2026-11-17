"""CHAMPION TAG V4: eight backgrounds, readability and winner ceremony integration."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class ChampionV4(unittest.TestCase):
    def test_eight_backgrounds_in_both_pickers(self):
        html=(ROOT/'champion.html').read_text(encoding='utf-8')
        for background in ('daylight','finals'):
            self.assertEqual(html.count('data-ct-bg="'+background+'"'),2)
            self.assertTrue((ROOT/'assets/champion'/('bg-'+background+'-v4.svg')).is_file())
        self.assertIn("'daylight', 'finals'",(ROOT/'tag_champion.py').read_text(encoding='utf-8'))
    def test_shared_ceremony_loaded_after_styling(self):
        for page in ('champion.html','champion-board.html'):
            html=(ROOT/page).read_text(encoding='utf-8')
            self.assertIn('champion-experience-v4.css?v=4.0',html)
            self.assertIn('champion-ceremony-v4.js?v=4.0',html)
            self.assertLess(html.index('champion-theme-engine-v3.js?v=5.0'),
                            html.index('champion-ceremony-v4.js?v=4.0'))
    def test_finish_triggers_only_real_winner(self):
        teacher=(ROOT/'champion-tag.js').read_text(encoding='utf-8')
        board=(ROOT/'champion-board.js').read_text(encoding='utf-8')
        self.assertIn('TAGChampionCeremony?.update(active,{autoplay:true})',teacher)
        self.assertIn('TAGChampionCeremony?.update(t,{autoplay:celebrate})',board)
        self.assertIn('initialLoaded=false',board)
    def test_broadcast_labels_and_pitch_are_usable(self):
        css=(ROOT/'champion-experience-v4.css').read_text(encoding='utf-8')
        self.assertIn('data-champion-theme="broadcast"',css)
        self.assertIn('-webkit-text-fill-color:#08233b',css)
        self.assertIn('--ct-field-veil',css)
if __name__=='__main__':
    unittest.main()
