"""Existing printed school identity QR codes are preserved on imported TAG cards."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class SchoolQrImport(unittest.TestCase):
    def test_teacher_badge_qr_encodes_original_school_code(self):
        portal=(ROOT/'portal.js').read_text(encoding='utf-8')
        self.assertIn("const schoolQrCode=String(student.cardCode||'').trim().toUpperCase()",portal)
        self.assertIn('const isSchoolId=/^G[789][ABC]-\\d{3}$/.test(schoolQrCode)',portal)
        self.assertIn("encodeURIComponent(isSchoolId?schoolQrCode:link)",portal)
        self.assertIn("const qrCaption=isSchoolId?'رمز الهوية المدرسية الأصلي':'امسح للانضمام'",portal)
        self.assertIn('const link=base+encodeURIComponent(student.card)',portal)
    def test_student_room_accepts_short_school_code_as_card(self):
        student=(ROOT/'student.js').read_text(encoding='utf-8')
        self.assertIn("selectedCard.length>=9||/^G[789][ABC]-\\d{3}$/.test(selectedCard)",student)
        self.assertIn("/api/card/profile?card=",student)
        self.assertIn("/api/card/resolve?code=",student)
if __name__=='__main__': unittest.main()
