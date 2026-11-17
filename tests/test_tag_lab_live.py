"""Synthetic independent-LAB live game test, no official students or network."""
import os
import tempfile
import unittest
from unittest.mock import patch
import platform_store as db

class Handler:
    def __init__(self):
        self.client_address=('192.0.2.19',12345)
        self.data=None
        self.status=None
        self.headers={}
    def send_json(self,data,status=200):
        self.data,self.status=data,status
    def log_message(self,*args): pass

class LiveIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.old_path=db.LOCAL_DB
        cls.old_url=db.DATABASE_URL
        db.LOCAL_DB=os.path.join(cls.tmp.name,'taglab-live.sqlite')
        db.DATABASE_URL=''
        cls.mode=patch.dict(os.environ,{'TAG_LAB_ONLY_MODE':'1'})
        cls.mode.start()
        db.init()
        global games,live,cards
        import game_lab_api as games
        import game_lab_live as live
        import tag_lab_cards as cards
        games.ensure_schema();live.init();cards.init()
        t=db.create_teacher('live@example.test','SecurePass1234567',
                            'Live Teacher','Sample School','Digital Skills')
        cls.tid=t['teacher']['id']
        cls.activity='1'*32
        source='PublicLiveCodeWithEnoughLength'
        rows=[{'q':'Question '+str(i),'a':'Correct '+str(i),'g':'Digital Skills',
               'choices':['Correct '+str(i),'Wrong '+str(i)]} for i in range(4)]
        db.exec_sql('INSERT INTO game_lab_activities '
           '(id,teacher_id,title,subject,grade,mode,payload,public_code,published,'
           'max_attempts,archived,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
           (cls.activity,cls.tid,'Synthetic live','Digital Skills','7','quiz',
            db.jdump({'rows':rows}),source,1,2,0,live.stamp(),live.stamp()))
    @classmethod
    def tearDownClass(cls):
        cls.mode.stop()
        db.LOCAL_DB=cls.old_path;db.DATABASE_URL=cls.old_url
        cls.tmp.cleanup()
    def test_guest_room_does_not_query_shared_students(self):
        room=live.create(self.tid,{'activityId':self.activity,'duration':25})
        self.assertIn('/tag-lab-live-student.html',room['studentUrl'])
        code=room['code']
        with patch.object(live.solo_api,'limited',return_value=False):
            with patch.object(live.solo_api,'find_student',
                              side_effect=AssertionError('legacy student lookup forbidden')):
                h=Handler();live.join(h,{'code':code,'guestName':'Demo Guest'})
                self.assertEqual(h.status,200)
        session=h.data['token']
        self.assertEqual(h.data['state']['status'],'lobby')
        with patch.object(live.auth,'authorized',return_value={'id':self.tid}):
            h=Handler();live.control(h,{'code':code},'start')
            self.assertEqual(h.status,200)
        public=live.read_public_state(code,session)
        self.assertEqual(public['status'],'question')
        self.assertNotIn('correctAnswer',public['question'])
        q=public['question'];self.assertEqual(q['total'],4)
        h=Handler();live.answer(h,{'code':code,'token':session,'index':0,'answer':q['options'][0]})
        self.assertEqual(h.status,200)
        h=Handler();live.answer(h,{'code':code,'token':session,'index':0,'answer':q['options'][0]})
        self.assertEqual(h.status,409)
        report=live.room_report(live.load(code),live.roster(code))
        self.assertEqual(report['totalPlayers'],1)
        self.assertEqual(report['results'][0]['answered'],1)
    def test_three_simulated_clients_submit_independent_answers(self):
        """Three concurrent virtual browser sessions share one room, no real students."""
        import concurrent.futures
        room=live.create(self.tid,{'activityId':self.activity,'duration':25})
        code=room['code']
        tokens=[]
        with patch.object(live.solo_api,'limited',return_value=False):
            for student in ('Simulated Device A','Simulated Device B','Simulated Device C'):
                h=Handler();live.join(h,{'code':code,'guestName':student})
                self.assertEqual(h.status,200)
                tokens.append(h.data['token'])
        self.assertEqual(len(set(tokens)),3)
        with patch.object(live.auth,'authorized',return_value={'id':self.tid}):
            h=Handler();live.control(h,{'code':code},'start')
            self.assertEqual(h.status,200)
        states=[live.read_public_state(code,t) for t in tokens]
        self.assertTrue(all(x['participants']==3 for x in states))
        self.assertTrue(all(x['question']['options']==states[0]['question']['options']
                            for x in states))
        self.assertTrue(all(x['correctAnswer'] is None for x in states))
        options=states[0]['question']['options']
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future=[executor.submit(self._submit,code,t,0,options[i%len(options)])
                    for i,t in enumerate(tokens)]
            answered=[f.result(timeout=5) for f in future]
        self.assertEqual(answered,[200,200,200])
        self.assertEqual(live.phase(live.load(code),live.roster(code)),'results')
        results=live.room_report(live.load(code),live.roster(code))
        self.assertEqual(results['totalPlayers'],3)
        self.assertEqual(len(results['results']),3)
        self.assertTrue(all(x['answered']==1 for x in results['results']))
        for token in tokens:
            row=live.read_public_state(code,token)
            self.assertEqual(row['status'],'results')
        with patch.object(live.auth,'authorized',return_value={'id':self.tid}):
            h=Handler();live.control(h,{'code':code},'next')
            self.assertEqual(h.status,200)
        self.assertEqual(live.read_public_state(code,tokens[0])['index'],1)

    @staticmethod
    def _submit(code,token,index,answer):
        h=Handler()
        live.answer(h,{'code':code,'token':token,'index':index,'answer':answer})
        return h.status

    def test_card_room_rejects_unverified_guests_and_duplicate_joins(self):
        room=live.create(self.tid,{'activityId':self.activity,'cardRequired':True})
        code=room['code']
        with patch.object(live.solo_api,'limited',return_value=False):
            h=Handler();live.join(h,{'code':code,'guestName':'Unverified Guest'})
            self.assertEqual(h.status,403)
            fake={'roster_id':'synthetic-1','teacher_id':self.tid,
                  'label':'Verified Student','class_name':'السابع أ'}
            with patch.object(cards,'session',return_value=fake):
                h=Handler();live.join(h,{'code':code,'cardSession':'synthetic-valid-token'})
                self.assertEqual(h.status,200)
                h=Handler();live.join(h,{'code':code,'cardSession':'synthetic-valid-token'})
                self.assertEqual(h.status,409)
            h=Handler();live.join(h,{'code':code,'card':'UNTRUSTED-RAW-CARD'})
            self.assertEqual(h.status,403)

if __name__=='__main__':
    unittest.main()
