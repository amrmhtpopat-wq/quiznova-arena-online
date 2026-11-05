"""BOOYAH BADJ-TH42: regression safety for seven named avatars and printed student IDs."""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
read=lambda name:(ROOT/name).read_text(encoding='utf-8')
NAMES=['شرارة','روبوك','فوكسو','نينزو','درعو','بيكسو','زومي']


class MascotsAndBadgeTests(unittest.TestCase):
    def test_seven_original_valid_svg_mascots(self):
        distinct=set()
        for index,name in enumerate(NAMES,1):
            path=ROOT/'assets'/'avatars-game'/f'm{index:02}.svg'
            self.assertTrue(path.is_file(),str(path))
            source=path.read_text(encoding='utf-8')
            root=ET.fromstring(source)
            self.assertEqual(root.tag,'{http://www.w3.org/2000/svg}svg')
            self.assertIn('viewBox="0 0 256 256"',source)
            self.assertNotIn('<script',source.lower())
            self.assertNotIn('http:',source.replace('xmlns="http://www.w3.org/2000/svg"',''))
            self.assertGreater(len(source),1800)
            distinct.add(source)
        self.assertEqual(len(distinct),7)

    def test_avatar_names_and_legacy_compatibility(self):
        portal=read('portal.js')
        student=read('student.js')
        for i,name in enumerate(NAMES,1):
            avatar=f'm{i:02}'
            self.assertIn(f"{avatar}:'{name}'",portal)
            self.assertIn(f"{avatar}:'{name}'",student)
            self.assertIn(f'/assets/avatars-game/',portal)
        self.assertIn("'m08'?'m07'",portal)
        self.assertIn("'m08'?'m07'",student)
        self.assertIn("length:7",portal)
        self.assertIn("id!=='m08'",student)
        self.assertIn('bo-avatar-name',student)
        self.assertIn('bo-mascot-option',portal)
        for js in ('app.js','portal.js','student.js','stage.js'):
            self.assertIn('avatars-game',read(js))
        # Existing server-side legacy avatar m08 stays valid for old student cards.
        self.assertIn("[f'm{i:02}' for i in range(1,9)]",read('platform_store.py'))

    def test_secure_qr_and_human_readable_codes_are_unmodified(self):
        portal=read('portal.js')
        self.assertIn("encodeURIComponent(student.card)",portal)
        self.assertIn("'/api/qr?text='+encodeURIComponent(link)",portal)
        self.assertIn('student.cardCode',portal)
        self.assertIn('BADJ-TH42',portal)
        self.assertIn('aria-label="بطاقة الطالب',portal)
        self.assertIn('bo-badge-student-name',portal)
        self.assertIn('bo-badge-access-id',portal)
        self.assertIn('bo-badge-meter',portal)
        self.assertIn('bo-badge-qr',portal)
        self.assertIn("img.loading='eager'",portal)
        self.assertIn("await Promise.all(images.map(img=>",portal)
        self.assertIn('window.print()',portal)
        # BADJ-TH42 is design version, NOT a shared student login credential.
        self.assertIn('title="إصدار تصميم البطاقة"',portal)
        self.assertIn("code=new_card_code()",read('platform_store.py'))

    def test_print_and_mobile_styles_are_loaded(self):
        index=read('index.html')
        student=read('student.html')
        css=read('booyah-badge-v112.css')
        mascot_css=read('booyah-mascots-v112.css')
        self.assertIn('booyah-badge-v112.css?v=11.3',index)
        self.assertIn('booyah-mascots-v112.css?v=11.3',student)
        self.assertGreater(index.index('booyah-badge-v112.css'),index.index('portal.css'))
        self.assertIn('@page{size:A4 portrait;margin:8mm}',css)
        self.assertIn('grid-template-columns:repeat(2,minmax(0,1fr))',css)
        self.assertIn('height:62mm!important',css)
        self.assertIn('print-color-adjust:exact',css)
        self.assertIn('#avatarPicker .bo-avatar-name',mascot_css)
        self.assertIn('@media(max-width:600px)',mascot_css)


if __name__=='__main__':
    unittest.main()
