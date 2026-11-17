"""Offline-only tests. No real cards, no live database and no network."""
import os
import unittest
from unittest.mock import patch
import tag_card_provider as provider

class Handler:
    headers={}
    client_address=("198.51.100.33",1234)
    response=None
    def send_json(self,value,status=200):
        self.response=(status,value)

class Url:
    path="/api/tag-independent/card/resolve"

class ProviderTests(unittest.TestCase):
    def test_disabled_without_secret(self):
        h=Handler()
        with patch.dict(os.environ, {"TAG_CARD_BRIDGE_SECRET":""}):
            self.assertTrue(provider.handle_post(h,Url(),{"card":"ABCD-1234"}))
        self.assertEqual(h.response[0],503)
    def test_rejects_unauthorized(self):
        h=Handler()
        h.headers={"Authorization":"Bearer wrong"}
        with patch.dict(os.environ, {"TAG_CARD_BRIDGE_SECRET":"x"*40}):
            self.assertTrue(provider.handle_post(h,Url(),{"card":"ABCD-1234"}))
        self.assertEqual(h.response[0],401)
    def test_minimal_pseudonymous_response(self):
        h=Handler()
        h.headers={"Authorization":"Bearer "+"x"*40}
        with patch.dict(os.environ, {"TAG_CARD_BRIDGE_SECRET":"x"*40}):
            with patch.object(provider.store,"student_profile_by_card",return_value={"id":"student-1","name":"DO_NOT_DISCLOSE","xp":50}):
                provider.handle_post(h,Url(),{"card":"ABCD-1234"})
        status, payload = h.response
        self.assertEqual(status,200)
        self.assertEqual(set(payload),{"ok","version","cardRef"})
        self.assertTrue(payload["cardRef"].startswith("tg1_"))
        self.assertNotIn("DO_NOT_DISCLOSE",str(payload))
        self.assertEqual(payload["cardRef"],provider._identity("x"*40,"student-1"))
    def test_invalid_card_is_not_disclosed(self):
        h=Handler()
        h.headers={"Authorization":"Bearer "+"x"*40}
        with patch.dict(os.environ, {"TAG_CARD_BRIDGE_SECRET":"x"*40}):
            provider.handle_post(h,Url(),{"card":"untrusted card with spaces"})
        self.assertEqual(h.response[0],403)

if __name__=="__main__":
    unittest.main()
