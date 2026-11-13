"""TEACH AND GAME global branding + backwards-compatible free short-address redirects."""
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PAGES=['index.html','about.html','for-teachers.html','student.html','studio.html','stage.html','admin.html']

class TeachGameBrandChecks(unittest.TestCase):
    def test_all_public_app_pages_are_consistently_named(self):
        for path in PAGES:
            with self.subTest(path=path):
                html=(ROOT/path).read_text(encoding='utf-8')
                self.assertIn('TEACH AND GAME',html)
                self.assertNotIn('BOOYAHJO',html) if path!='index.html' else None
                self.assertNotIn('بويا جو',html) if path!='index.html' else None
        self.assertIn('value="TEACH AND GAME"',(ROOT/'studio.html').read_text(encoding='utf-8'))
        self.assertIn('TEACH AND GAME',(ROOT/'portal.js').read_text(encoding='utf-8'))
        self.assertIn('TEACH AND GAME',(ROOT/'stage.js').read_text(encoding='utf-8'))

    def test_google_metadata_uses_new_brand_and_preserves_old_alias(self):
        text=(ROOT/'index.html').read_text(encoding='utf-8')
        self.assertIn('<title>TEACH AND GAME | TAG',text)
        self.assertIn('og:site_name" content="TEACH AND GAME | TAG"',text)
        data_match=re.search(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>',text,re.S)
        self.assertIsNotNone(data_match)
        data=json.loads(data_match.group(1))
        self.assertEqual(next(item for item in data['@graph'] if item.get('@type')=='WebSite')['name'],'TEACH AND GAME')
        self.assertIn('تيتش آند جيم',next(item for item in data['@graph'] if item.get('@type')=='WebSite')['alternateName'])
        self.assertIn('TAG',next(item for item in data['@graph'] if item.get('@type')=='WebSite')['alternateName'])
        self.assertIn('https://quiznova-arena-online.onrender.com/',text)

    def test_badges_exports_progress_and_new_defaults(self):
        self.assertIn('أسطورة تيتش آند جيم',(ROOT/'platform_store.py').read_text(encoding='utf-8'))
        self.assertIn("'platformName':'TEACH AND GAME'",(ROOT/'platform_store.py').read_text(encoding='utf-8'))
        js=(ROOT/'app.js').read_text(encoding='utf-8')
        self.assertIn('tag-results.csv',js)
        self.assertIn('tag-backup.json',js)
        self.assertIn("platform='TEACH AND GAME'",js) # global public identity is not overridden by historical teacher settings
        self.assertIn('value="TEACH AND GAME" readonly',(ROOT/'studio.html').read_text(encoding='utf-8'))
        self.assertIn('TEACH AND GAME',(ROOT/'portal.js').read_text(encoding='utf-8'))
        self.assertIn('TAG_{code}_report.xlsx',(ROOT/'server.py').read_text(encoding='utf-8'))

    def test_redirect_alias_pages_are_static_safe_and_preserve_query(self):
        for path in ['index.html','student.html','studio.html','admin.html','about.html','for-teachers.html']:
            with self.subTest(path=path):
                html=(ROOT/'short-link'/path).read_text(encoding='utf-8')
                dest='https://quiznova-arena-online.onrender.com/'+('' if path=='index.html' else path)
                self.assertIn('content="noindex,nofollow,noarchive"',html)
                self.assertIn('location.replace(target+location.search+location.hash)',html)
                self.assertIn(dest,html)
                self.assertIn('TEACH AND GAME | تيتش آند جيم',html)
        sitemap=(ROOT/'sitemap.xml').read_text(encoding='utf-8')
        self.assertEqual(sitemap.count('<url>'),3)
        self.assertNotIn('teachgame.onrender.com',sitemap)

    def test_student_card_grade_and_fullscreen_changes_remain(self):
        html=(ROOT/'student.html').read_text(encoding='utf-8')
        for part in ['boCardQuizzes','booyah-card-quizzes-v128.js',
                     'booyah-student-fit-v128.css','booyah-student-fit-v128.js',
                     'solo-student-v120.js']:
            self.assertIn(part,html)


    def test_remaining_public_modules_do_not_display_old_brand(self):
        targets={
            'booyah-countdown-v121.js':['TEACH AND GAME • استعد للانطلاق'],
            'media_library.js':['مكتبة TEACH AND GAME'],
            'portal.js':['tag-card-logo','reissueTeachGameCards',"const base=location.origin+'/student.html?card=';"],
            'studio-auth.js':['TAG_unsynced_changes.json',"/app.js?v=13.1"],
            'platform_security.py':['TEACH AND GAME | تيتش آند جيم — إعادة تعيين كلمة المرور','حسابك في TEACH AND GAME'],
        }
        for name,phrases in targets.items():
            content=(ROOT/name).read_text(encoding='utf-8')
            for phrase in phrases:
                with self.subTest(file=name,phrase=phrase):
                    self.assertIn(phrase,content)
        self.assertNotIn('BOOYAHJO • استعد',(ROOT/'booyah-countdown-v121.js').read_text(encoding='utf-8'))
        self.assertNotIn('مكتبة BOOYAHJO',(ROOT/'media_library.js').read_text(encoding='utf-8'))
        self.assertNotIn('QuizNova Arena - إعادة تعيين',(ROOT/'platform_security.py').read_text(encoding='utf-8'))
        self.assertIn('id="reissueTeachGameCards"',(ROOT/'index.html').read_text(encoding='utf-8'))
        self.assertIn("window.print()",(ROOT/'portal.js').read_text(encoding='utf-8'))
        for n in range(1,8):
            asset=(ROOT/f'assets/avatars-game/m{n:02}.svg').read_text(encoding='utf-8')
            self.assertIn('TeachGame game mascot',asset)
            self.assertNotIn('BOOYAH game mascot',asset)

    def test_updated_assets_and_cache_control(self):
        refs={
          'index.html':['portal.js?v=16.0','booyah-badge-v112.css?v=13.1'],
          'studio.html':['media_library.js?v=13.1','studio-auth.js?v=13.1','booyah-countdown-v121.js?v=13.1'],
          'student.html':['booyah-countdown-v121.js?v=13.1'],
          'stage.html':['booyah-countdown-v121.js?v=13.1']
        }
        for path,assets in refs.items():
            html=(ROOT/path).read_text(encoding='utf-8')
            for asset in assets:
                with self.subTest(file=path,asset=asset):self.assertIn(asset,html)
        code=(ROOT/'server.py').read_text(encoding='utf-8')
        self.assertIn("'Cache-Control','no-cache, max-age=0, must-revalidate'",code)
        self.assertIn("requested.lower().endswith('.html')",code)

    def test_no_student_records_rotated_for_visual_reprint(self):
        js=(ROOT/'portal.js').read_text(encoding='utf-8')
        start=js.index("$('#reissueTeachGameCards').onclick")
        end=js.index("$('#printCards').onclick",start)
        refresh=js[start:end]
        self.assertIn('await loadAll()',refresh)
        self.assertIn("$('#printCards').click()",refresh)
        self.assertNotIn('/api/teacher/students/delete',refresh)
        self.assertNotIn('/api/teacher/students/shorten-codes',refresh)
        self.assertIn('student.cardCode',js)
        self.assertIn('encodeURIComponent(student.card)',js)

if __name__=='__main__':
    unittest.main()
