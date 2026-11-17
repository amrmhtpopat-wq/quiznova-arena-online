"""Full synthetic end-to-end card and game test on disposable SQLite.

No connection to Neon, Render, official cards, or user accounts.
"""
import os
import tempfile
import unittest
from unittest.mock import patch

import platform_store as db
import game_lab_api as games
import tag_lab_cards as cards
import tag_card_client as bridge

class Handler:
    def __init__(self):
        self.client_address=("192.0.2.11",3322)
        self.status=None
        self.data=None
    def send_json(self,body,status=200):
        self.status,self.data=status,body
    def log_message(self,*args): pass

class CardLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.old_path=db.LOCAL_DB
        cls.old_url=db.DATABASE_URL
        db.LOCAL_DB=os.path.join(cls.tmp.name,"taglab-tests.sqlite")
        db.DATABASE_URL=""
        cls.mode=patch.dict(os.environ,{"TAG_LAB_ONLY_MODE":"1"})
        cls.mode.start()
        db.init();games.ensure_schema();cards.init()
        created=db.create_teacher("qa@example.test","securePassphrase1234",
                                  "Synthetic Teacher","Demo School","Digital Skills")
        cls.tid=created["teacher"]["id"]
        cls.student_ref="tg1_"+"a"*40
    @classmethod
    def tearDownClass(cls):
        cls.mode.stop()
        db.LOCAL_DB=cls.old_path
        db.DATABASE_URL=cls.old_url
        cls.tmp.cleanup()
    def test_1_enrollment_is_private_and_pin_is_slow_hashed(self):
        with patch.object(bridge,"verify",return_value=self.student_ref):
            result=cards.enroll(self.tid,{"card":"SYNTHETIC-QRCODE",
                "label":"Demo Student","className":"Grade 7 A"})
        self.__class__.rid=result["card"]["id"]
        self.__class__.pin=result["pin"]
        self.assertRegex(result["pin"],r"^[0-9]{6}$")
        row=cards.roster_row(self.tid,self.rid)
        self.assertTrue(cards.check_pin(self.pin,row))
        self.assertFalse(cards.check_pin("123456" if self.pin!="123456" else "111111",row))
        self.assertNotIn("SYNTHETIC-QRCODE",repr(row))
        self.assertNotIn(self.pin,repr(row))
        with patch.object(bridge,"verify",return_value=self.student_ref):
            with self.assertRaisesRegex(ValueError,"card_already_enrolled"):
                cards.enroll(self.tid,{"card":"SYNTHETIC-QRCODE",
                   "label":"Demo Student","className":"Grade 7 A"})
    def test_2_assignments_sessions_and_game_play(self):
        aid="a"*32
        source="aPublishedCodeWithEnoughCharacters"
        rows=[{"q":"Test "+str(i),"a":"Answer "+str(i),"g":"Math"}
              for i in range(4)]
        db.exec_sql("INSERT INTO game_lab_activities "
         "(id,teacher_id,title,subject,grade,mode,payload,public_code,published,"
         "max_attempts,archived,created_at,updated_at) "
         "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
         (aid,self.tid,"Demo Quiz","Math","7","quiz",
          db.jdump({"rows":rows}),source,1,2,0,cards.now(),cards.now()))
        saved=cards.assign(self.tid,{"activityId":aid,"targets":[{"type":"student",
                      "value":self.rid}]})
        self.assertEqual(saved["targets"][0]["type"],"student")
        self.assertEqual(len(cards.assignments(self.tid,aid)),1)
        with patch.object(bridge,"verify",return_value=self.student_ref):
            with patch.object(cards.solo_api,"limited",return_value=False):
                h=Handler();cards.card_login(h,{"card":"SYNTHETIC-QRCODE","pin":"000000" if self.pin!="000000" else "999999"})
                self.assertEqual(h.status,403)
                h=Handler();cards.card_login(h,{"card":"SYNTHETIC-QRCODE","pin":self.pin})
                self.assertEqual(h.status,200)
                token=h.data["session"]
                self.assertEqual(len(h.data["activities"]),1)
                h=Handler();cards.card_login(h,{"card":"SYNTHETIC-QRCODE","pin":self.pin})
                self.assertEqual(h.status,409)
        h=Handler();games.start({"code":source,"cardSession":token},h)
        self.assertEqual(h.status,200)
        run=h.data["token"]
        h=Handler();games.start({"code":source,"cardSession":token},h)
        self.assertEqual(h.status,409)
        for i in range(4):
            h=Handler()
            games.answer({"token":run,"index":i,"answer":"Answer "+str(i)},h)
            self.assertEqual(h.status,200)
        self.assertTrue(h.data["state"]["finished"])
        self.assertEqual(h.data["state"]["xpGain"],0)
        self.assertEqual(db.query("SELECT COUNT(*) AS n FROM student_attempts")["n"],0)
        report=games.teacher_reports(self.tid,aid)
        self.assertEqual(report["total"],1)
        h=Handler();games.start({"code":source,"cardSession":token},h)
        self.assertEqual(h.status,200)
        h=Handler();games.start({"code":source},h)
        self.assertEqual(h.status,403)
        h=Handler();cards.student_logout(h,{"session":token})
        self.assertEqual(h.status,200)
        self.assertIsNone(cards.session(token))

if __name__=="__main__":
    unittest.main()
