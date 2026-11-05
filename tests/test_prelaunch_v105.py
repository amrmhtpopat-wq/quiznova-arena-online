"""QuizNova V10.5 release-candidate smoke/regression coverage (SQLite only)."""
import json, os, tempfile, threading, unittest, urllib.request, urllib.error, uuid
from pathlib import Path
tmp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(tmp.name)/'v105.db')
import platform_store as store
store.init()
import server

class ReleaseCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        cls.runner=threading.Thread(target=cls.site.serve_forever,daemon=True)
        cls.runner.start()
        cls.base='http://127.0.0.1:'+str(cls.site.server_port)
        acc=store.create_teacher(uuid.uuid4().hex+'@example.org','StrongTeacher#123','Test Teacher','مدرسة اختبار للبنين','المهارات الرقمية','boys')
        cls.teacher=acc['teacher']['id']
        cls.token=acc['token']

    @classmethod
    def tearDownClass(cls):
        cls.site.shutdown()
        cls.site.server_close()

    def api(self,path,data=None,teacher=False):
        headers={'Content-Type':'application/json'}
        if teacher:headers['Authorization']='Bearer '+self.token
        req=urllib.request.Request(self.base+path,data=json.dumps(data,ensure_ascii=False).encode() if data is not None else None,headers=headers,method='POST' if data is not None else 'GET')
        try:
            with urllib.request.urlopen(req,timeout=15) as resp:return resp.status,json.loads(resp.read())
        except urllib.error.HTTPError as err:return err.code,json.loads(err.read())

    def room(self,feedback=False,require_card=True):
        quiz={'id':uuid.uuid4().hex,'title':'تمرين سرعة','questions':[{'id':'q1','type':'single','text':'كم ٢ + ٢؟','options':['4','5','6','7'],'correct':[0],'time':60,'points':1000}]}
        code,obj=self.api('/api/room/start',{'quiz':quiz,'gameMode':'speed','showFeedback':feedback,'playType':'individual','variantMode':'same','requireCard':require_card},teacher=True)
        self.assertEqual(code,200,obj);return obj

    def test_card_code_qr_and_unique_identity(self):
        students=store.add_students(self.teacher,[{'name':'طالب اختبار أ','className':'9A','avatar':'n01'},{'name':'طالب اختبار ب','className':'9A','avatar':'n02'}])
        self.assertEqual(len(students),2)
        self.assertTrue(all(s['cardCode'].startswith('QNA-') for s in students))
        self.assertNotEqual(students[0]['cardCode'],students[1]['cardCode'])
        self.assertEqual(store.student_by_card(students[0]['cardCode'],self.teacher)['id'],students[0]['id'])
        self.assertEqual(store.student_by_card(students[0]['card'],self.teacher)['id'],students[0]['id'])
        other=store.create_teacher(uuid.uuid4().hex+'@example.org','StrongTeacher#123','Other Teacher','Boys','subject','boys')['teacher']['id']
        self.assertIsNone(store.student_by_card(students[0]['cardCode'],other))
        self.assertIn('n01',store.avatar_pool('boys'))
        self.assertNotIn('n01',store.avatar_pool('girls'))

    def test_answer_privacy_instant_scoring_and_durable_xp(self):
        students=store.add_students(self.teacher,[{'name':'أول مشارك','className':'9A','avatar':'n03'},{'name':'ثاني مشارك','className':'9A','avatar':'n04'}])
        room=self.room(False,True)
        joined=[]
        for item in students:
            status,data=self.api('/api/room/join',{'code':room['code'],'card':item['cardCode'],'name':'','avatar':'n01'})
            self.assertEqual(status,200,data)
            self.assertEqual(data['name'],item['name'])
            joined.append(data['playerId'])
        fail,dup=self.api('/api/room/join',{'code':room['code'],'card':students[0]['cardCode'],'name':''})
        self.assertEqual(fail,409);self.assertEqual(dup['error'],'card_already_joined')
        fail,invalid=self.api('/api/room/join',{'code':room['code'],'card':'QNA-FAKE-FAKE-FAKE','name':'طالب وهمي'})
        self.assertEqual(fail,403);self.assertEqual(invalid['error'],'invalid_card')
        status,_=self.api('/api/room/control',{'code':room['code'],'hostToken':room['hostToken'],'action':'start'})
        self.assertEqual(status,200)
        status,answer=self.api('/api/room/answer',{'code':room['code'],'playerId':joined[0],'index':0,'answer':0})
        self.assertEqual(status,200,answer)
        self.assertIsNone(answer['result']['correct'],'Teacher disabled correctness feedback')
        self.assertGreater(server.ROOMS[room['code']]['players'][joined[0]]['score'],0)
        status,state=self.api('/api/room/state?code='+room['code']+'&player='+joined[0])
        self.assertTrue(state['room']['answeredCurrent'])
        self.assertIsNone(state['room']['lastResult']['correct'])
        self.assertEqual(state['room']['status'],'question')
        status,_=self.api('/api/room/answer',{'code':room['code'],'playerId':joined[1],'index':0,'answer':1})
        self.assertEqual(status,200)
        status,state=self.api('/api/room/state?code='+room['code']+'&player='+joined[0])
        self.assertEqual(state['room']['status'],'results','The question ends when all players answer')
        self.assertIsNone(state['room']['review'])
        status,_=self.api('/api/room/control',{'code':room['code'],'hostToken':room['hostToken'],'action':'next'})
        self.assertEqual(status,200)
        saved=store.student_by_card(students[0]['cardCode'],self.teacher)
        self.assertGreater(saved['xp'],0)
        self.assertEqual(store.level_for_xp(500),2)
        before=saved['xp']
        server.persist_finished_room(server.ROOMS[room['code']])
        self.assertEqual(store.student_by_card(students[0]['cardCode'],self.teacher)['xp'],before,'No duplicate XP on repeated persistence')
        status,finished=self.api('/api/room/state?code='+room['code']+'&player='+joined[0])
        self.assertEqual(finished['room']['level'],store.level_for_xp(saved['xp']))
        self.assertGreater(finished['room']['xpGain'],0)

    def test_teacher_feedback_optin_is_respected(self):
        room=self.room(True,False)
        for name in ('One','Two'):
            status,joined=self.api('/api/room/join',{'code':room['code'],'name':name,'avatar':'n05'})
            self.assertEqual(status,200,joined)
            if name=='One':first=joined['playerId']
        self.api('/api/room/control',{'code':room['code'],'hostToken':room['hostToken'],'action':'start'})
        status,answer=self.api('/api/room/answer',{'code':room['code'],'playerId':first,'index':0,'answer':0})
        self.assertEqual(status,200,answer)
        self.assertTrue(answer['result']['correct'])
        self.assertGreater(answer['result']['earned'],0)

    def test_visual_assets_and_student_viewport(self):
        root=Path(__file__).resolve().parents[1]
        for i in range(1,9):
            pic=root/f'assets/avatars3d/n{i:02d}.webp'
            self.assertTrue(pic.is_file(),str(pic))
            raw=pic.read_bytes()
            self.assertTrue(raw[:4]==b'RIFF' and raw[8:12]==b'WEBP')
            self.assertGreater(len(raw),7000)
        hero=root/'assets/backgrounds/quiznova-learning.webp'
        self.assertTrue(hero.is_file())
        self.assertGreater(hero.stat().st_size,10000)
        css=(root/'v107-prelaunch.css').read_text()
        self.assertIn('100dvh',css)
        self.assertIn('question-card',css)
        self.assertIn('qn-answer-wait',css)
        html=(root/'student.html').read_text()
        self.assertIn('id="cardCode"',html)
        self.assertIn('v107-prelaunch.css',html)
        self.assertIn('v107-educational-hero',(root/'index.html').read_text())
if __name__=='__main__':unittest.main()
