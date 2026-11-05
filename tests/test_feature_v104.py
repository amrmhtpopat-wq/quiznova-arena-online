import json,os,tempfile,threading,unittest,urllib.request,urllib.error,uuid
from pathlib import Path

db=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(db.name)/'v104-test.sqlite')
import platform_store as store
store.init()
import server

class FeatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        cls.thread=threading.Thread(target=cls.site.serve_forever,daemon=True)
        cls.thread.start()
        cls.root='http://127.0.0.1:'+str(cls.site.server_port)
        x=store.create_teacher(uuid.uuid4().hex+'@example.com','AstrongPassword#1','Test Teacher','مدرسة بنين','مهارات','boys')
        cls.token=x['token']
    @classmethod
    def tearDownClass(cls):
        cls.site.shutdown();cls.site.server_close()
    def api(self,path,payload=None,token=None):
        headers={'Content-Type':'application/json'}
        if token:headers['Authorization']='Bearer '+token
        req=urllib.request.Request(self.root+path,headers=headers,data=json.dumps(payload).encode() if payload is not None else None,method='POST' if payload is not None else 'GET')
        try:
            with urllib.request.urlopen(req,timeout=10) as r:return r.status,json.loads(r.read())
        except urllib.error.HTTPError as e:return e.code,json.loads(e.read())

    def create_room(self,assignment):
        data={'quiz':{'id':uuid.uuid4().hex,'title':'اختبار تقدير','questions':[{'id':'q1','type':'estimate','text':'كم عدد ...','estimateAnswer':100,'tolerance':5,'time':120,'points':1000}]},'playType':'teams','teamCount':2,'teamAssignment':assignment}
        code,d=self.api('/api/room/start',data,self.token)
        self.assertEqual(code,200,d)
        return d

    def test_single_tap_answer_scores_before_clock_expires(self):
        """The answer endpoint must score immediately without waiting for the clock."""
        room_data={
            'quiz':{'id':uuid.uuid4().hex,'title':'سباق السرعة','questions':[{
                'id':'speedq','type':'single','text':'كم الناتج؟',
                'options':['4','9','2','1'],'correct':[0],'time':90,'points':1000
            }]},
            'playType':'individual','gameMode':'speed','variantMode':'same'
        }
        code,room=self.api('/api/room/start',room_data,self.token)
        self.assertEqual(code,200,room)
        players=[]
        for name in ('أحمد','محمد'):
            status,p=self.api('/api/room/join',{'code':room['code'],'name':name,'avatar':'m01'})
            self.assertEqual(status,200,p)
            players.append(p)
        status,_=self.api('/api/room/control',{
            'code':room['code'],'hostToken':room['hostToken'],'action':'start'
        })
        self.assertEqual(status,200)
        status,answer=self.api('/api/room/answer',{
            'code':room['code'],'playerId':players[0]['playerId'],
            'index':0,'answer':0,'elapsedMs':200000
        })
        self.assertEqual(status,200,answer)
        self.assertTrue(answer['result']['correct'])
        self.assertGreater(answer['result']['earned'],600)
        status,state=self.api('/api/room/state?code='+room['code']+'&player='+players[0]['playerId'])
        self.assertEqual(status,200,state)
        self.assertTrue(state['room']['answeredCurrent'])
        self.assertEqual(state['room']['status'],'question')
        status,duplicate=self.api('/api/room/answer',{
            'code':room['code'],'playerId':players[0]['playerId'],'index':0,'answer':0
        })
        self.assertEqual(status,200,duplicate)
        self.assertTrue(duplicate['duplicate'])

    def test_numeric_estimation_boundaries(self):
        q={'type':'estimate','estimateAnswer':100,'tolerance':5}
        self.assertTrue(server.evaluate(q,95))
        self.assertTrue(server.evaluate(q,'105'))
        self.assertFalse(server.evaluate(q,'105.1'))
        self.assertFalse(server.evaluate(q,True))
        self.assertFalse(server.evaluate(q,'abc'))
        self.assertFalse(server.evaluate({'type':'estimate','estimateAnswer':100,'tolerance':-2},100))
        public=server.public_question(q)
        self.assertNotIn('estimateAnswer',public)
        self.assertNotIn('tolerance',public)

    def test_mature_portraits_only_boys_mixed(self):
        self.assertEqual(len(store.avatar_pool('boys')),32)
        self.assertEqual(len(store.avatar_pool('girls')),16)
        self.assertEqual(len(store.avatar_pool('mixed')),48)
        self.assertTrue(all(x[0]=='g' for x in store.avatar_pool('girls')))
        self.assertIn('m01',store.avatar_pool('boys'))

    def test_manual_team_assignment_requires_host(self):
        room=self.create_room('manual')
        code=room['code'];host=room['hostToken']
        status,join=self.api('/api/room/join',{'code':code,'name':'محمد','avatar':'m01'})
        self.assertEqual(status,200,join);self.assertEqual(join['team'],'')
        status,denied=self.api('/api/room/team',{'code':code,'playerId':join['playerId'],'team':room['teamNames'][0],'hostToken':'wrong'})
        self.assertEqual(status,403)
        status,notready=self.api('/api/room/control',{'code':code,'hostToken':host,'action':'start'})
        self.assertEqual(status,409);self.assertEqual(notready['error'],'team_missing')
        status,assigned=self.api('/api/room/team',{'code':code,'hostToken':host,'playerId':join['playerId'],'team':room['teamNames'][0]})
        self.assertEqual(status,200,assigned)
        status,started=self.api('/api/room/control',{'code':code,'hostToken':host,'action':'start'})
        self.assertEqual(status,200,started)
        self.assertTrue(started['ok'])
        late,reply=self.api('/api/room/join',{'code':code,'name':'طالب متأخر','avatar':'m02'})
        self.assertEqual(late,409);self.assertEqual(reply['error'],'team_assignment_closed')

    def test_random_teams_balanced(self):
        room=self.create_room('random')
        names=room['teamNames']
        counts={k:0 for k in names}
        for i in range(9):
            status,j=self.api('/api/room/join',{'code':room['code'],'name':'طالب '+str(i),'avatar':'m08'})
            self.assertEqual(status,200,j)
            counts[j['team']]+=1
        self.assertLessEqual(max(counts.values())-min(counts.values()),1)
        status,started=self.api('/api/room/control',{'code':room['code'],'hostToken':room['hostToken'],'action':'start'})
        self.assertEqual(status,200,started)

    def test_shuffle_teams_in_lobby(self):
        room=self.create_room('manual')
        for i in range(5):
            s,r=self.api('/api/room/join',{'code':room['code'],'name':'ج '+str(i),'avatar':'m02'})
            self.assertEqual(s,200)
        status,shuffled=self.api('/api/room/control',{'code':room['code'],'hostToken':room['hostToken'],'action':'shuffle-teams'})
        self.assertEqual(status,200,shuffled)
        status,state=self.api('/api/room/state?code='+room['code']+'&host='+room['hostToken'])
        self.assertEqual(status,200,state)
        teams=[p['team'] for p in state['room']['players']]
        self.assertEqual(len(teams),5)
        self.assertLessEqual(max(teams.count(x) for x in room['teamNames'])-min(teams.count(x) for x in room['teamNames']),1)

if __name__=='__main__':unittest.main()
