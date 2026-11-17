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
    def test_provider_is_pinned_to_https_official_origin(self):
        self.assertEqual(client.OFFICIAL_ENDPOINT,
            "https://quiznova-arena-online.onrender.com/api/tag-independent/card/resolve")
    def test_card_route_is_the_only_shared_api(self):
        with patch.dict(os.environ, {"TAG_LAB_ONLY_MODE":"1"}):
            self.assertTrue(mode.allowed("POST", "/api/tag-independent/card/verify"))
            self.assertFalse(mode.allowed("POST", "/api/card/resolve"))
            self.assertFalse(mode.allowed("GET", "/api/teacher/students"))
            self.assertFalse(mode.allowed("POST", "/api/teacher/students/edit"))

if __name__ == "__main__":
    unittest.main()
