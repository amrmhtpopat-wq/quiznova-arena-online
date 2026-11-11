"""V12.9 user-visible branding regression: identity only; never change routes or existing cards."""
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NEW='عندس'
PUBLIC=['index.html','about.html','for-teachers.html','student.html',
        'studio.html','stage.html','admin.html']
RUNTIME=['app.js','portal.js','stage.js']

class BrandRegression(unittest.TestCase):
    def test_public_pages_show_new_name(self):
        for name in PUBLIC:
            with self.subTest(name=name):
                content=(ROOT/name).read_text(encoding='utf-8')
                self.assertIn(NEW,content)
                self.assertNotIn('بويا جو',content) if name!='index.html' else None
                self.assertIn('https://quiznova-arena-online.onrender.com/',content) if name in ('index.html','about.html','for-teachers.html') else None

    def test_home_seo_renamed_and_old_name_kept_as_search_alias_only(self):
        content=(ROOT/'index.html').read_text(encoding='utf-8')
        self.assertIn('<title>عندس |',content)
        self.assertIn('<meta property="og:site_name" content="عندس',content)
        match=re.search(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>',content,re.S)
        self.assertIsNotNone(match)
        data=json.loads(match.group(1))
        self.assertEqual(data['name'],NEW)
        self.assertIn('BOOYAHJO',data['alternateName'])
        self.assertIn('بويا جو',data['alternateName'])

    def test_live_teacher_student_admin_still_connected(self):
        for path in RUNTIME:
            self.assertIn(NEW,(ROOT/path).read_text(encoding='utf-8'))
        app=(ROOT/'app.js').read_text(encoding='utf-8')
        self.assertIn("'BOOYAHJO'",app)  # legacy saved account value migration
        self.assertIn("?'عندس':",app)
        self.assertIn("andas-quiz-backup.json",app)
        html=(ROOT/'student.html').read_text(encoding='utf-8')
        self.assertIn('student.js?v=',html)
        self.assertIn('solo-student-v120.js?v=',html)
        self.assertIn('booyah-card-quizzes-v128.js?v=',html)
        self.assertIn('booyah-student-fit-v128.js?v=',html)
        self.assertIn('id="cardProfile"',html)
        self.assertIn('id="boCardQuizzes"',html)
        self.assertIn('sitemap.xml',(ROOT/'robots.txt').read_text(encoding='utf-8'))
        self.assertEqual((ROOT/'sitemap.xml').read_text(encoding='utf-8').count('<url>'),3)
        self.assertIn("'platformName':'عندس'",(ROOT/'platform_store.py').read_text(encoding='utf-8'))

if __name__=='__main__':
    unittest.main()
