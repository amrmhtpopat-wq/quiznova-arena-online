"""TAG V23: verify indexed landing, QR preservation, full-site shared assets and routing."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
read = lambda p: (ROOT / p).read_text(encoding="utf-8")


class TagV23ReleaseSafety(unittest.TestCase):
    def test_public_landing_keeps_search_and_legacy_routes(self):
        html = read("short-link/index.html")
        self.assertIn('rel="canonical" href="https://teachgame.onrender.com/"', html)
        self.assertIn('name="robots" content="index,follow', html)
        self.assertIn('href="/teacher/"', html)
        self.assertIn('href="/student/"', html)
        self.assertIn('href="/tag-landing-v23.css?v=23.0"', html)
        self.assertIn('location.replace(to.toString()+location.hash)', html)
        self.assertIn('["teacher","card","code","room","session","join","quiz"]', html)
        self.assertIn('class="tag23-scene"', html)
        self.assertTrue((ROOT / "short-link/tag-landing-v23.css").is_file())

    def test_static_brand_asset_is_bundled(self):
        for path in ("assets/brand/tag-spatial-identity-v3.webp",
                     "short-link/assets/brand/tag-spatial-identity-v3.webp"):
            content = (ROOT / path).read_bytes()
            self.assertTrue(content.startswith(b"RIFF") and content[8:12] == b"WEBP", path)

    def test_student_qr_unchanged_and_logo_natively_updated(self):
        js = read("portal.js")
        css = read("tag-responsive-brand-v23.css")
        self.assertIn('tag-card-logo" src="/assets/brand/tag-spatial-identity-v3.webp', js)
        self.assertIn("includes('tag-spatial-identity-v3.webp')", js)
        self.assertIn("const schoolQrCode=String(student.cardCode||'').trim().toUpperCase()", js)
        self.assertIn('encodeURIComponent(isSchoolId?quizLink:link)', js)
        self.assertIn("image-rendering:pixelated", css)
        self.assertIn("24.5mm", css)
        self.assertIn("height:62mm", css)
        self.assertIn("grid-template-columns:repeat(2,minmax(0,1fr))", css)
        self.assertNotIn("data-pin", js)

    def test_original_pages_have_back_and_style_without_changing_lab(self):
        for path in ("index.html", "student.html", "studio.html", "champion.html",
                     "about.html", "for-teachers.html", "admin.html", "stage.html",
                     "champion-board.html", "app.html"):
            with self.subTest(path=path):
                html = read(path)
                self.assertIn('tag-responsive-brand-v23.css?v=23.0', html)
                self.assertIn('tag-responsive-brand-v23.js?v=23.0', html)
        js = read("tag-responsive-brand-v23.js")
        self.assertIn("tag-lab|game-lab|tag-independent", js)
        self.assertIn("history.back()", js)
        self.assertIn("MutationObserver", js)

if __name__ == "__main__":
    unittest.main()
