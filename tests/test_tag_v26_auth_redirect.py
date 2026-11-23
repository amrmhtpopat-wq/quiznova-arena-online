"""Protect teacher login redirects after migrating the TAG public origin."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class UnifiedAuthRedirectV26(unittest.TestCase):
    def test_studio_login_redirects_to_official_portal_and_legacy_still_works(self):
        src=(ROOT/'studio-auth.js').read_text(encoding='utf-8')
        self.assertIn("location.hostname==='teachgame.onrender.com'?'/portal.html':'/'",src)
        self.assertIn("loginTarget=teacherEntry+'?next='+encodeURIComponent('/studio.html#'+safeView)",src)
        self.assertIn('location.replace(loginTarget)',src)
        self.assertIn('main.querySelector(\'a[href*="next="]\')',src)
    def test_champion_login_same_origin(self):
        src=(ROOT/'champion-tag.js').read_text(encoding='utf-8')
        self.assertEqual(src.count("location.hostname==='teachgame.onrender.com'?'/portal.html?next=':'/?next='"),2)
        self.assertIn("encodeURIComponent('/champion.html')",src)
    def test_portal_resumes_requested_view_after_login(self):
        src=(ROOT/'portal.js').read_text(encoding='utf-8')
        self.assertIn("new URLSearchParams(location.search).get('next')",src)
        self.assertIn("url.origin===location.origin",src)
        self.assertIn("?'/studio.html#'+target:''",src)
        self.assertIn("return '/champion.html'",src)
    def test_public_origin_root_remains_indexed_while_portal_is_login(self):
        gateway=(ROOT/'deploy/teachgame-unified.render.yaml').read_text(encoding='utf-8')
        self.assertIn('source: /portal.html',gateway)
        self.assertIn('source: /api/*',gateway)
        self.assertIn('source: /*',gateway)
        self.assertIn('type: rewrite',gateway)
        home=(ROOT/'short-link/index.html').read_text(encoding='utf-8')
        self.assertIn('https://teachgame.onrender.com/',home)
        self.assertIn('content="index,follow',home)
if __name__=='__main__':unittest.main()
