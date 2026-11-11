"""TeachGame global branding + backwards-compatible free short-address redirects."""
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
                self.assertIn('TeachGame',html)
                self.assertNotIn('BOOYAHJO',html) if path!='index.html' else None
                self.assertNotIn('بويا جو',html) if path!='index.html' else None
        self.assertIn('value="TeachGame"',(ROOT/'studio.html').read_text(encoding='utf-8'))
        self.assertIn('TeachGame',(ROOT/'portal.js').read_text(encoding='utf-8'))
        self.assertIn('TeachGame',(ROOT/'stage.js').read_text(encoding='utf-8'))

    def test_google_metadata_uses_new_brand_and_preserves_old_alias(self):
        text=(ROOT/'index.html').read_text(encoding='utf-8')
        self.assertIn('<title>TeachGame | تيتش جيم',text)
        self.assertIn('og:site_name" content="TeachGame | تيتش جيم"',text)
        data_match=re.search(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>',text,re.S)
        self.assertIsNotNone(data_match)
        data=json.loads(data_match.group(1))
        self.assertEqual(data['name'],'TeachGame')
        self.assertIn('تيتش جيم',data['alternateName'])
        self.assertIn('BOOYAHJO',data['alternateName'])
        self.assertIn('https://quiznova-arena-online.onrender.com/',text)

    def test_badges_exports_progress_and_new_defaults(self):
        self.assertIn('أسطورة تيتش جيم',(ROOT/'platform_store.py').read_text(encoding='utf-8'))
        self.assertIn("'platformName':'TeachGame'",(ROOT/'platform_store.py').read_text(encoding='utf-8'))
        js=(ROOT/'app.js').read_text(encoding='utf-8')
        self.assertIn('teachgame-results.csv',js)
        self.assertIn('teachgame-backup.json',js)
        self.assertIn("'BOOYAHJO'",js) # old saved teacher settings still load
        self.assertIn('بويا جو',js)  # old Arabic teacher value also migrates
        self.assertIn('TeachGame',(ROOT/'portal.js').read_text(encoding='utf-8'))
        self.assertIn('TeachGame_{code}_report.xlsx',(ROOT/'server.py').read_text(encoding='utf-8'))

    def test_redirect_alias_pages_are_static_safe_and_preserve_query(self):
        for path in ['index.html','student.html','studio.html','admin.html','about.html','for-teachers.html']:
            with self.subTest(path=path):
                html=(ROOT/'short-link'/path).read_text(encoding='utf-8')
                dest='https://quiznova-arena-online.onrender.com/'+('' if path=='index.html' else path)
                self.assertIn('content="noindex,nofollow,noarchive"',html)
                self.assertIn('location.replace(target+location.search+location.hash)',html)
                self.assertIn(dest,html)
                self.assertIn('TeachGame | تيتش جيم',html)
        sitemap=(ROOT/'sitemap.xml').read_text(encoding='utf-8')
        self.assertEqual(sitemap.count('<url>'),3)
        self.assertNotIn('teachgame.onrender.com',sitemap)

    def test_student_card_grade_and_fullscreen_changes_remain(self):
        html=(ROOT/'student.html').read_text(encoding='utf-8')
        for part in ['boCardQuizzes','booyah-card-quizzes-v128.js',
                     'booyah-student-fit-v128.css','booyah-student-fit-v128.js',
                     'solo-student-v120.js']:
            self.assertIn(part,html)

if __name__=='__main__':
    unittest.main()
