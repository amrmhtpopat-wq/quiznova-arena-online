"""Regression checks for the optional TAG LAB surface isolation (stdlib only)."""
import os
import unittest
from unittest.mock import patch
import tag_independent_mode as mode

class HandlerStub:
    def __init__(self):
        self.status = None
        self.headers = {}
        self.payload = None
    def send_response(self, code): self.status = code
    def send_header(self, key, value): self.headers[key] = value
    def end_headers(self): pass
    def send_json(self, data, status=200):
        self.status, self.payload = status, data

class StandaloneLabTests(unittest.TestCase):
    def test_feature_is_opt_in(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(mode.allowed("GET", "/studio.html"))
            self.assertTrue(mode.allowed("POST", "/api/room/start"))
            self.assertFalse(mode.reject(HandlerStub(), "GET", "/"))
    def test_lab_exposes_only_its_ui(self):
        with patch.dict(os.environ, {"TAG_LAB_ONLY_MODE": "1"}):
            for path in ("/tag-lab-home.html", "/tag-lab-games.html",
                         "/tag-lab-books.html", "/game-lab-preview.html",
                         "/assets/brand/tag-icon.svg", "/api/health",
                         "/api/game-lab/public", "/api/auth/me"):
                self.assertTrue(mode.allowed("GET", path), path)
            for path in ("/studio.html", "/index.html", "/student.html",
                         "/champion.html", "/api/teacher/students",
                         "/api/card/profile", "/api/admin/stats"):
                self.assertFalse(mode.allowed("GET", path), path)
    def test_lab_blocks_old_cards_and_official_rooms(self):
        with patch.dict(os.environ, {"TAG_LAB_ONLY_MODE": "1"}):
            self.assertTrue(mode.allowed("POST", "/api/auth/login"))
            self.assertTrue(mode.allowed("POST", "/api/game-lab/teacher/save"))
            self.assertTrue(mode.allowed("GET", "/tag-lab-assign.html"))
            self.assertTrue(mode.allowed("GET", "/tag-lab-student.html"))
            self.assertTrue(mode.allowed("GET", "/api/tag-independent/teacher/cards"))
            self.assertTrue(mode.allowed("POST", "/api/tag-independent/student/login"))
            for path in ("/api/tag-independent/card/verify",
                         "/api/game-lab/pro/card/catalog",
                         "/api/game-lab/pro/assignments/save",
                         "/api/room/start", "/api/teacher/students/edit",
                         "/api/auth/me"):
                self.assertFalse(mode.allowed("POST", path), path)
    def test_root_goes_to_lab(self):
        with patch.dict(os.environ, {"TAG_LAB_ONLY_MODE": "1"}):
            h = HandlerStub()
            self.assertTrue(mode.reject(h, "GET", "/"))
            self.assertEqual(h.status, 302)
            self.assertEqual(h.headers["Location"], "/tag-lab-home.html")
            h = HandlerStub()
            self.assertTrue(mode.reject(h, "GET", "/student.html"))
            self.assertEqual(h.status, 404)

if __name__ == "__main__":
    unittest.main()
