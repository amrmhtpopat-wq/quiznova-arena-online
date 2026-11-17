"""CHAMPION TAG V3: four backend-persisted themes, six independent stadium backdrops.
Runs locally against a disposable SQLite database, never production Neon.
"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import platform_store as store
import tag_champion as champion

ROOT=Path(__file__).resolve().parents[1]

class ChampionV3Persistence(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.path=str(Path(self.folder.name)/'tag_v3.sqlite')
        self.db_patch=patch.object(store,'LOCAL_DB',self.path)
        self.url_patch=patch.object(store,'DATABASE_URL','')
        self.db_patch.start()
        self.url_patch.start()
        store.init()
        champion.ensure_schema()
        # Migration is idempotent even when tables already exist.
        champion.ensure_schema()
        teacher=store.create_teacher('champion.v3@example.test','Secret_2026_ABC','معلم البطولة','مدرسة تجريبية','المهارات الرقمية')
        self.teacher_id=teacher['teacher']['id']
        quiz={'id':'quiz-v3','title':'أسئلة البطولة',
              'questions':[{'id':'q1','text':'اختر الصحيح','type':'single',
                            'options':['أ','ب','ج','د'],'correct':[0],'time':20,'points':1000}]}
        store.save_snapshot(self.teacher_id,{'quizzes':[quiz]})

    def tearDown(self):
        self.db_patch.stop()
        self.url_patch.stop()
        self.folder.cleanup()

    def new(self,theme='gold',background='stadium'):
        return champion.create(self.teacher_id,{
            'title':'دوري TAG','kind':'classes','seedMode':'random',
            'participants':['السابع أ','السابع ب','الثامن أ','الثامن ب'],
            'quizId':'quiz-v3','theme':theme,'background':background
        })

    def test_default_skin_and_theme_background_independence(self):
        t=self.new()
        self.assertEqual(t['theme'],'gold')
        self.assertEqual(t['background'],'stadium')
        for theme in champion.THEMES:
            for background in champion.BACKGROUNDS:
                updated=champion.update_appearance(self.teacher_id,{
                    'tournamentId':t['id'],'theme':theme,'background':background
                })
                self.assertEqual((updated['theme'],updated['background']),(theme,background))
                board=champion.public_board(t['id'])
                self.assertEqual((board['theme'],board['background']),(theme,background))
                self.assertNotIn('hostToken',str(board))
                self.assertNotIn('stageToken',str(board))
        # Reload from a fresh database query: not just client-side state.
        self.assertEqual(champion.detail(self.teacher_id,t['id'])['background'],champion.BACKGROUNDS[-1])

    def test_creation_can_use_any_official_theme(self):
        for theme,background in [('gold','stadium'),('neon','arena'),('esports','grid'),('broadcast','lights')]:
            t=self.new(theme,background)
            self.assertEqual((t['theme'],t['background']),(theme,background))
            self.assertEqual(len(t['rounds']),2)

    def test_invalid_appearance_cannot_change_saved_bracket(self):
        t=self.new()
        for payload in [{'theme':'../../other','background':'stadium'},
                        {'theme':'gold','background':'https://unsafe.test/image.svg'},
                        {'theme':'<script>','background':'arena'}]:
            with self.assertRaisesRegex(ValueError,'invalid_appearance'):
                champion.update_appearance(self.teacher_id,{'tournamentId':t['id'],**payload})
        self.assertEqual(champion.detail(self.teacher_id,t['id'])['theme'],'gold')

    def test_teachers_cannot_modify_others_tournaments(self):
        t=self.new()
        with self.assertRaisesRegex(ValueError,'tournament_not_found'):
            champion.update_appearance('not-the-teacher',{
                'tournamentId':t['id'],'theme':'neon','background':'arena'
            })
        self.assertEqual(champion.detail(self.teacher_id,t['id'])['theme'],'gold')

    def test_schema_additive_migration_from_v2(self):
        # The active V3 database already migrated above; verify columns exist.
        with store.db_connection() as con:
            names={row[1] for row in con.execute('PRAGMA table_info(tag_championships)').fetchall()}
        self.assertTrue({'theme','background'}.issubset(names))

class ChampionV3UI(unittest.TestCase):
    def test_four_previews_and_six_backdrops(self):
        html=(ROOT/'champion.html').read_text(encoding='utf-8')
        for theme in champion.THEMES:
            self.assertIn('data-ct-theme="'+theme+'"',html)
        for background in champion.BACKGROUNDS:
            self.assertIn('data-ct-bg="'+background+'"',html)
            asset=('bg-'+background+'-v4.svg') if background in ('daylight','finals') else ('bg-'+background+'.svg')
            self.assertTrue((ROOT/'assets/champion'/asset).is_file())
        self.assertIn('champion-themes-v3.css?v=3.0',html)
        self.assertIn('saveChampionAppearance',html)
        self.assertIn('champion-theme-engine-v3.js?v=4.0',html)

    def test_teacher_persists_and_projector_replays(self):
        script=(ROOT/'champion-tag.js').read_text(encoding='utf-8')
        board=(ROOT/'champion-board.js').read_text(encoding='utf-8')
        self.assertIn("request('/api/champion/appearance','POST'",script)
        self.assertIn('theme:draftAppearance.theme',script)
        self.assertIn('background:draftAppearance.background',script)
        self.assertIn('window.TAGChampionTheme.apply(t.theme,t.background)',board)
        self.assertIn('window.TAGChampionBracket.afterRender',board)
        self.assertTrue((ROOT/'assets/champion/trophy.svg').is_file())

    def test_bracket_rebuilds_real_connectors(self):
        code=(ROOT/'champion-bracket.js').read_text(encoding='utf-8')
        self.assertIn('drawConnectors(root)',code)
        self.assertIn('createElementNS',code)
        self.assertIn('bracket-connector-layer',code)
        self.assertIn('pointer-events:none',(ROOT/'champion-themes-v3.css').read_text(encoding='utf-8'))
        self.assertIn('/assets/champion/trophy.svg',code)
        self.assertNotIn('svg onclick=',code)

if __name__=='__main__':unittest.main()
