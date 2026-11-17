"""Bridge contract safety checks. No real student cards or network calls used."""
import os
import unittest
from unittest.mock import patch
import tag_card_client as client
import tag_independent_mode as mode

class CardBridgeClientTests(unittest.TestCase):
    def test_absent_secret_is_safe(self):
        with patch.dict(os.environ, {"TAG_CARD_BRIDGE_SECRET":""}):
            self.assertFalse(client.configured())
            with self.assertRaises(client.CardBridgeUnavailable):
                client.verify("ABCD-1234")
    def test_bad_card_never_sent(self):
        with patch.dict(os.environ, {"TAG_CARD_BRIDGE_SECRET":"x"*40}):
            for value in ("", "student name", "http://localhost/admin",
                          "/../private", "x"*200, None):
                with self.assertRaises(client.CardNotFound):
                    client.verify(value)
    def test_parse_original_qr_from_trusted_url_without_following_link(self):
        self.assertEqual(client.normalize_card("G9B-021"),"G9B-021")
        self.assertEqual(client.normalize_card(
            "https://school-qr-attendance.onrender.com/scan?card=G9B-021"),"G9B-021")
        self.assertEqual(client.normalize_card(
            "https://quiznova-arena-online.onrender.com/scan/G9B-021"),"G9B-021")
        self.assertEqual(client.normalize_card(
            "https://school-qr-transfer.onrender.com/?id=G9B-021"),"G9B-021")
        for bad in (
            "http://school-qr-attendance.onrender.com/scan?card=G9B-021",
            "https://school-qr-attendance.onrender.com.evil.net/?card=G9B-021",
            "https://example.org/?card=G9B-021",
            "https://school-qr-attendance.onrender.com/?card=javascript%3Aalert",
            "https://school-qr-attendance.onrender.com/?card=G9B-021#admin",
            "https://school-qr-attendance.onrender.com:8080/?card=G9B-021",
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(client.CardNotFound):
                    client.normalize_card(bad)
    def test_provider_is_pinned_to_https_official_origin(self):
        self.assertEqual(client.OFFICIAL_ENDPOINT,
            "https://quiznova-arena-online.onrender.com/api/tag-independent/card/resolve")
    def test_card_route_is_the_only_shared_api(self):
        with patch.dict(os.environ, {"TAG_LAB_ONLY_MODE":"1"}):
            self.assertFalse(mode.allowed("POST", "/api/tag-independent/card/verify"))
            self.assertTrue(mode.allowed("POST", "/api/tag-independent/student/login"))
            self.assertTrue(mode.allowed("POST", "/api/tag-independent/teacher/cards/enroll"))
            self.assertFalse(mode.allowed("POST", "/api/card/resolve"))
            self.assertFalse(mode.allowed("GET", "/api/teacher/students"))
            self.assertFalse(mode.allowed("POST", "/api/teacher/students/edit"))

if __name__ == "__main__":
    unittest.main()
