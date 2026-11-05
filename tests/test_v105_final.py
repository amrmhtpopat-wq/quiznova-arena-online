"""V10.5 release candidate - functional API, student cards and permanent XP."""
import json,os,tempfile,threading,unittest,urllib.request,urllib.error,uuid,re
from pathlib import Path

tmp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(tmp.name)/'v105-final.sqlite')
import platform_store as store
store.init()
import server

class FinalCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.web=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        cls.thread=threading.Thread(target=cls.web.serve_forever,daemon=True)
        cls.thread.start()
        cls.root='http://127.0.0.1:'+str(cls.web.server_port)
        teachers=[]
        for i in range(2):
            obj=store.create_teacher(uuid.uuid4().hex+'@school.example','TestPass123456!','Teacher '+str(i),'مدرسة بنين','مهارات رقمية','boys')
            teachers.append(obj)
        cls.a=teachers[0]['teacher']['id']
        cls.b=teachers[1]['teacher']['id']
        cls.token_a=teachers[0]['token']
        cls.token_b=teachers[1]['token']
        cls.cards_a=store.add_students(cls.a,[{'name':'أحمد خالد','className':'التاسع أ','avatar':'n03'}])
        cls.cards_b=store.add_students(cls.b,[{'name':'محمد خالد','className':'التاسع أ','avatar':'n05'}])

    @classmethod
    def tearDownClass(cls):
        cls.web.shutdown();cls.web.server_close()
    def api(self,path,data=None,token=None):
        headers={'Content-Type':'application/json'}
        if token:headers['Authorization']='Bearer '+token
        req=urllib.request.Request(self.root+path,headers=headers,
            data=json.dumps(data,ensure_ascii=False).encode() if data is not None else None,
            method='POST' if data is not None else 'GET')
        try:
            with urllib.request.urlopen(req,timeout=12) as response:
                return response.status,json.loads(response.read())
        except urllib.error.HTTPError as ex:
            return ex.code,json.loads(ex.read())

    def room(self,show=False):
        payload={'quiz':{'id':uuid.uuid4().hex,'title':'اختبار نهائي تجريبي',
            'questions':[{'id':'q01','type':'single','text':'ما ناتج 2+2؟',
              'options':['4','3','2','1'],'correct':[0],'time':90,'points':1000}]},
            'playType':'individual','gameMode':'speed','showFeedback':show,'variantMode':'same'}
        status,data=self.api('/api/room/start',payload,self.token_a)
        self.assertEqual(status,200,data)
        return data

    def test_card_code_is_secure_nonsequential_and_qr_compatible(self):
        student=self.cards_a[0]
        self.assertRegex(student['cardCode'],r'^[A-HJ-NP-Z2-9]{4}-[A-HJ-NP-Z2-9]{4}$')
        self.assertGreaterEqual(len(student['card']),28)
        self.assertNotEqual(student['cardCode'],student['card'])
        card=store.student_by_card(student['cardCode'],self.a)
        self.assertEqual(card['id'],student['id'])
        self.assertEqual(store.student_by_card(student['card'],self.a)['id'],student['id'])
        self.assertIsNone(store.student_by_card(student['cardCode'],self.b))
        self.assertIsNone(store.student_by_card('QNA-XXXX-YYYY-ZZZZ',self.a))

    def test_public_card_profile_works_without_joining_room(self):
        import urllib.parse
        code=self.cards_a[0]['cardCode']
        status,res=self.api('/api/card/profile?card='+urllib.parse.quote(code))
        self.assertEqual(status,200,res)
        self.assertEqual(res['name'],'أحمد خالد')
        self.assertEqual(res['level'],1)
        self.assertEqual(res['xp'],0)
        status,invalid=self.api('/api/card/profile?card=invalid')
        self.assertEqual(status,404)
        self.assertEqual(invalid['error'],'invalid_card')

    def test_teacher_feedback_off_immediate_scores_and_atomic_xp(self):
        room=self.room(show=False)
        code=room['code']
        first=self.cards_a[0]
        a,j=self.api('/api/room/join',{'code':code,'card':first['cardCode'],'avatar':'n07'})
        self.assertEqual(a,200,j)
        self.assertEqual(j['name'],'أحمد خالد')
        self.assertEqual(j['level'],1)
        status,again=self.api('/api/room/join',{'code':code,'card':first['cardCode']})
        self.assertEqual(status,409)
        self.assertEqual(again['error'],'card_already_joined')
        status,wrong=self.api('/api/room/join',{'code':code,'card':self.cards_b[0]['cardCode']})
        self.assertEqual(status,403)
        self.assertEqual(wrong['error'],'invalid_card')
        status,visitor=self.api('/api/room/join',{'code':code,'name':'طالب زائر','avatar':'n02'})
        self.assertEqual(status,200,visitor)
        status,started=self.api('/api/room/control',{'code':code,'hostToken':room['hostToken'],'action':'start'})
        self.assertEqual(status,200,started)
        status,answer=self.api('/api/room/answer',{'code':code,'playerId':j['playerId'],'index':0,'answer':0,'elapsedMs':900000})
        self.assertEqual(status,200,answer)
        self.assertTrue(answer['ok'])
        self.assertIsNone(answer['result']['correct']) # private teacher option
        self.assertGreater(answer['result']['earned'],500)
        self.assertGreater(answer['score'],500)
        status,state=self.api('/api/room/state?code='+code+'&player='+j['playerId'])
        self.assertEqual(status,200,state)
        self.assertTrue(state['room']['answeredCurrent'])
        self.assertEqual(state['room']['status'],'question') # other student has yet to answer
        self.assertIsNone(state['room']['lastResult']['correct'])
        status,duplicate=self.api('/api/room/answer',{'code':code,'playerId':j['playerId'],'index':0,'answer':0})
        self.assertEqual(status,200,duplicate)
        self.assertTrue(duplicate['duplicate'])
        self.assertEqual(duplicate['score'],answer['score'])
        status,_=self.api('/api/room/answer',{'code':code,'playerId':visitor['playerId'],'index':0,'answer':1})
        self.assertEqual(status,200)
        status,results=self.api('/api/room/state?code='+code+'&player='+j['playerId'])
        self.assertEqual(status,200,results)
        self.assertEqual(results['room']['status'],'results')
        self.assertIsNone(results['room']['review'])
        status,_=self.api('/api/room/control',{'code':code,'hostToken':room['hostToken'],'action':'next'})
        self.assertEqual(status,200)
        status,finished=self.api('/api/room/state?code='+code+'&player='+j['playerId'])
        self.assertEqual(status,200,finished)
        self.assertEqual(finished['room']['status'],'finished')
        xp=finished['room']['xp']
        self.assertGreater(xp,0)
        self.assertEqual(finished['room']['xpGain'],xp)
        self.assertEqual(store.list_students(self.a)[0]['xp'],xp)
        store.persist_room(server.ROOMS[code],[],[])
        self.assertEqual(store.list_students(self.a)[0]['xp'],xp)

    def test_teacher_feedback_on_shows_correctness_immediately(self):
        room=self.room(show=True)
        status,player=self.api('/api/room/join',{'code':room['code'],'name':'طالب تجريبي','avatar':'n04'})
        self.assertEqual(status,200)
        status,_=self.api('/api/room/control',{'code':room['code'],'hostToken':room['hostToken'],'action':'start'})
        self.assertEqual(status,200)
        status,ans=self.api('/api/room/answer',{'code':room['code'],'playerId':player['playerId'],'index':0,'answer':0})
        self.assertEqual(status,200)
        self.assertTrue(ans['result']['correct'])

if __name__=='__main__':unittest.main()
