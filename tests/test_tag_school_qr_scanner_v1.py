"""TAG school QR integration regressions.

The original ministry school-attendance QR stays a plain G7/G8/G9 school ID.
Students open TAG through the browser scanner or the *separate* new TAG quiz QR.
"""
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]

class OriginalSchoolQrToPublishedQuizzes(unittest.TestCase):
    def test_scanner_accepts_original_school_ids(self):
        script=(ROOT/'tag-school-qr-scanner-v1.js').read_text(encoding='utf-8')
        self.assertIn(r'const schoolId=/^G[789][ABC]-\d{3}$/',script)
        self.assertIn("getUserMedia",script)
        self.assertIn("window.jsQR(",script)
        self.assertIn("decodeFile(",script)
        self.assertIn("/api/student/solo/catalog",script)
        self.assertIn("sessionStorage.setItem('tag_school_card_pending',card)",script)
        self.assertIn("location.assign('/student.html?mode=card')",script)
        self.assertNotIn("teacher/students/delete",script)

    def test_student_card_loaded_and_published_quizzes_visible(self):
        student=(ROOT/'student.js').read_text(encoding='utf-8')
        html=(ROOT/'student.html').read_text(encoding='utf-8')
        published=(ROOT/'booyah-card-quizzes-v128.js').read_text(encoding='utf-8')
        self.assertIn("sessionStorage.getItem('tag_school_card_pending')",student)
        self.assertIn("window.BOOYAH_SHOW_CARD_TESTS?.(code)",student)
        self.assertIn("mode=card",student)
        self.assertIn('href="/scan-card.html"',html)
        self.assertIn('student.js?v=25.0',html)
        self.assertIn("/api/student/solo/catalog",published)
        self.assertIn("data-card-quiz",published)

    def test_original_attendance_qr_unchanged_plus_secondary_tag_url_qr(self):
        portal=(ROOT/'portal.js').read_text(encoding='utf-8')
        self.assertIn("encodeURIComponent(isSchoolId?schoolQrCode:link)",portal)
        self.assertIn("const qrCaption=isSchoolId?'رمز الهوية المدرسية الأصلي'",portal)
        self.assertIn('bo-tag-quiz-qr',portal)
        self.assertIn('/student.html?mode=card&card=',portal)
        self.assertIn("isSchoolId?'https://quiznova-arena-online.onrender.com/student.html",portal)
        badge=(ROOT/'tag-dual-school-qr-v1.css').read_text(encoding='utf-8')
        self.assertIn('grid-template-columns:minmax(0,1fr) 20.5mm 20.5mm',badge)

    def test_self_hosted_decoder_and_student_entry_pages(self):
        scan=(ROOT/'scan-card.html').read_text(encoding='utf-8')
        homepage=(ROOT/'index.html').read_text(encoding='utf-8')
        self.assertIn('/vendor/jsqr-1.4.0.js',scan)
        self.assertIn('/tag-school-qr-scanner-v1.js',scan)
        self.assertIn('capture="environment"',scan)
        self.assertIn('href="/scan-card.html"',homepage)
        self.assertTrue((ROOT/'vendor/jsqr-1.4.0.js').is_file())
        self.assertTrue((ROOT/'vendor/jsqr-LICENSE').is_file())

if __name__=='__main__':
    unittest.main()
