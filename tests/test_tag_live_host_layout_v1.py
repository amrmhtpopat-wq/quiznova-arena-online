"""TAG LIVE: selected classroom backdrop must paint large host room, not the picker sidebar.
This is a design-only regression: no player, score, timer or room-control JS changes.
"""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCENES=('cartoon','anime','cinematic','cine-stars','cine-aurora','cine-neon',
        'cine-desert','cine-arena','tag-daylight','tag-finals','tag-royal',
        'tag-celebration','tag-hall','tag-neon','tag-trophy','tag-elegant')

class TagLiveHostLayoutV1(unittest.TestCase):
    def test_host_background_uses_same_room_scene_as_dropdown(self):
        css=(ROOT/'tag-live-host-layout-v1.css').read_text(encoding='utf-8')
        app=(ROOT/'app.js').read_text(encoding='utf-8')
        for name in SCENES:
            self.assertIn('data-live-scene="'+name+'"',css)
        self.assertIn('var(--tag-host-scene)',css)
        self.assertIn('.room-shell>.room-code-card',css)
        self.assertIn('background-image:linear-gradient(105deg',css)
        self.assertIn("$('#liveHost').dataset.liveScene=room.background||'cartoon'",app)
        self.assertIn("$('#changeLiveScene').onclick=()=>liveControl('background')",app)

    def test_picker_is_full_width_and_room_has_no_implicit_third_column(self):
        css=(ROOT/'tag-live-host-layout-v1.css').read_text(encoding='utf-8')
        self.assertIn('grid-template-columns:minmax(0,1.65fr) minmax(260px,.83fr)',css)
        self.assertIn('grid-column:1/-1!important;grid-row:1!important',css)
        self.assertIn('grid-column:1!important;grid-row:2!important',css)
        self.assertIn('grid-column:2!important;grid-row:2!important',css)
        self.assertIn('@media(max-width:1050px)',css)
        self.assertIn('@media(max-width:650px)',css)
        html=(ROOT/'studio.html').read_text(encoding='utf-8')
        self.assertIn('tag-live-host-layout-v1.css?v=1.0',html)
        self.assertLess(html.index('tag-live-visual-v1.css?v=1.0'),
                        html.index('tag-live-host-layout-v1.css?v=1.0'))

if __name__=='__main__':
    unittest.main()
