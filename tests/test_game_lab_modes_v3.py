"""All 24 Game Lab modes: server-authoritative activity, safe text responses and participation."""
import json,os,sys,tempfile,unittest,uuid,threading
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import Request,urlopen
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


class ModeContract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory()
  os.environ.pop('DATABASE_URL',None)
  os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(cls.temp.name)/'modes.sqlite')
  os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
  import platform_store as store,server
  cls.http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
  threading.Thread(target=cls.http.serve_forever,daemon=True).start()
  cls.base='http://127.0.0.1:'+str(cls.http.server_port)
  cls.store=store
  created=store.create_teacher('modes-'+uuid.uuid4().hex+'@example.test','StrongModeTeacherPassword123!',
      'معلم الألعاب','مدرسة الألعاب','المهارات الرقمية')
  cls.tid=created['teacher']['id'];cls.token=created['token']
  cls.student=store.add_students(cls.tid,[{'name':'طالب وضع','className':'التاسع أ','avatar':'m01'}])[0]

 @classmethod
 def tearDownClass(cls):
  cls.http.shutdown();cls.http.server_close();cls.temp.cleanup()

 def api(self,path,data,token=None):
  h={'Content-Type':'application/json'}
  if token:h['Authorization']='Bearer '+token
  req=Request(self.base+path,data=json.dumps(data,ensure_ascii=False).encode(),headers=h)
  try:
   with urlopen(req,timeout=15) as resp:return resp.status,json.load(resp)
  except HTTPError as exc:return exc.code,json.load(exc)

 def test_all_modes(self):
  from game_lab_api import MODES,TEXT_MODES,NON_GRADED_MODES
  self.assertEqual(len(MODES),24)
  source=[{'q':'ما المقصود بالمفهوم '+str(i)+'؟','a':'مفهوم'+str(i),'g':'تصنيف'+str(i%2)} for i in range(4)]
  for mode in sorted(MODES):
   with self.subTest(mode=mode):
    payload={'title':'نشاط '+mode,'subject':'العلوم','grade':'السابع','mode':mode,'rows':source}
    status,created=self.api('/api/game-lab/teacher/save',{'activity':payload},self.token)
    self.assertEqual(status,200,created)
    status,published=self.api('/api/game-lab/teacher/publish',{'id':created['id']},self.token)
    self.assertEqual(status,200,published)
    status,started=self.api('/api/game-lab/student/start',{
       'code':published['publicCode'],'card':self.student['cardCode']})
    self.assertEqual(status,200,started)
    state=started['state']
    self.assertEqual(state['unscored'],mode in NON_GRADED_MODES)
    q=state['question']
    self.assertNotIn('correctAnswer',q)
    if mode in TEXT_MODES:
     self.assertIn('entry',q)
     self.assertEqual(q['choices'],[])
    else:self.assertTrue(q['choices'])
    answer='نص تأملي' if mode in NON_GRADED_MODES else ('تصنيف0' if mode=='sort' else 'مفهوم0')
    if mode=='truth':answer='صح'
    status,replied=self.api('/api/game-lab/student/answer',{
       'token':started['token'],'index':0,'answer':answer})
    self.assertEqual(status,200,replied)
    self.assertIsNone(replied['correct']) if mode in NON_GRADED_MODES else self.assertIsInstance(replied['correct'],bool)
    status,repeat=self.api('/api/game-lab/student/answer',{
       'token':started['token'],'index':0,'answer':answer})
    self.assertEqual(status,409,repeat)
    # Learner can continue in every mode; server advances state.
    self.assertEqual(replied['state']['index'],1)


 def test_bulk_templates_share_one_xp_entitlement(self):
  source={'title':'درس واحد لجميع الألعاب','subject':'المهارات الرقمية','grade':'السابع',
   'mode':'quiz','rows':[{'q':'سؤال'+str(i),'a':'حل'+str(i),'g':'عام'} for i in range(4)]}
  code,created=self.api('/api/game-lab/teacher/save',{'activity':source},self.token)
  self.assertEqual(code,200,created)
  root=created['id']
  code,batch=self.api('/api/game-lab/teacher/generate-all',{'sourceId':root,'confirm':True},self.token)
  self.assertEqual(code,200,batch)
  self.assertEqual(batch['templates'],24)
  self.assertEqual(batch['created'],23)
  code,batch_again=self.api('/api/game-lab/teacher/generate-all',{'sourceId':root,'confirm':True},self.token)
  self.assertEqual(code,200,batch_again)
  self.assertEqual(batch_again['created'],0)
  self.assertEqual(batch_again['updated'],24)
  names=self.store.query('SELECT id,mode,payload FROM game_lab_activities WHERE teacher_id=?',(self.tid,),True)
  siblings=[r for r in names if self.store.jload(r['payload'],{}).get('sourceGroup')==root]
  self.assertEqual(len(siblings),24)
  individual=next(x for x in siblings if x['mode']=='quiz')
  text=next(x for x in siblings if x['mode']=='crossword')
  baseline=self.store.query('SELECT xp FROM students WHERE id=?',(self.student['id'],))['xp']
  gains=[]
  for item in (individual,text):
   code,enabled=self.api('/api/game-lab/teacher/publish',{'id':item['id']},self.token)
   self.assertEqual(code,200,enabled)
   code,running=self.api('/api/game-lab/student/start',{
      'code':enabled['publicCode'],'card':self.student['cardCode']})
   self.assertEqual(code,200,running)
   state=running['state']
   for i in range(4):
    code,reply=self.api('/api/game-lab/student/answer',{
       'token':running['token'],'index':i,'answer':'حل'+str(i)})
    self.assertEqual(code,200,reply)
    state=reply['state']
   gains.append(state['xpGain'])
  self.assertEqual(gains,[50,0])
  self.assertEqual(self.store.query('SELECT xp FROM students WHERE id=?',(self.student['id'],))['xp']-baseline,50)

if __name__=='__main__':unittest.main(verbosity=2)
