"""V10 classroom pilot — true multi-device HTTP contract on disposable SQLite.

No QA production DB, no real teacher account, no real card numbers.
"""
import json,os,tempfile,threading,uuid,unittest,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

MODES=('quiz','fast','truth','pairs','wheel','boxes')
ROWS=[
 {'q':'ما وظيفة وحدة المعالجة؟','a':'تنفيذ التعليمات','g':'المعالج',
  'choices':['تنفيذ التعليمات','إخراج الصوت','تخزين الملفات','عرض الصور']},
 {'q':'ما وظيفة الذاكرة المؤقتة؟','a':'حفظ البيانات أثناء التشغيل','g':'الذاكرة'},
 {'q':'ما وظيفة شاشة العرض؟','a':'إظهار المحتوى','g':'الإخراج'},
 {'q':'ما وظيفة لوحة المفاتيح؟','a':'إدخال النصوص','g':'الإدخال'}
]
class ClassroomV10(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.folder=tempfile.TemporaryDirectory()
  os.environ.pop('DATABASE_URL',None)
  os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(cls.folder.name)/'classroom.sqlite')
  os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
  import platform_store as db,server
  cls.db=db
  cls.http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
  threading.Thread(target=cls.http.serve_forever,daemon=True).start()
  cls.base='http://127.0.0.1:'+str(cls.http.server_port)
  a=db.create_teacher('classroom-'+uuid.uuid4().hex+'@example.test','StrongTestTeacherPass!22',
                      'معلم QA','مدرسة تجريبية','المهارات الرقمية')
  b=db.create_teacher('outsider-'+uuid.uuid4().hex+'@example.test','StrongTestTeacherPass!22',
                      'معلم ثان','مدرسة QA ثانية','الرياضيات')
  cls.teacher=a['token'];cls.teacher2=b['token'];cls.tid=a['teacher']['id']
  cls.good=db.add_students(cls.tid,[
    {'name':'Student A','className':'السابع أ','avatar':'m01'},
    {'name':'Student B','className':'السابع ب','avatar':'m02'},
    {'name':'Student C','className':'السابع أ','avatar':'m03'}])
  cls.wrong_grade=db.add_students(cls.tid,[{'name':'Student D','className':'التاسع أ','avatar':'m04'}])[0]
  cls.outsider=db.add_students(b['teacher']['id'],
     [{'name':'Outsider','className':'السابع أ','avatar':'m05'}])[0]
 @classmethod
 def tearDownClass(cls):
  cls.http.shutdown();cls.http.server_close();cls.folder.cleanup()
 def req(self,path,data=None,token=None):
  headers={}
  if token:headers['Authorization']='Bearer '+token
  if data is not None:headers['Content-Type']='application/json'
  req=Request(self.base+path,data=json.dumps(data,ensure_ascii=False).encode() if data is not None else None,headers=headers)
  try:
   with urlopen(req,timeout=18) as resp:return resp.status,json.load(resp)
  except HTTPError as e:return e.code,json.load(e)
 def room(self,mode,cardRequired=False,teams=False,showFeedback=True):
  status,saved=self.req('/api/game-lab/teacher/save',{'activity':{
   'title':'V10 Test '+mode,'mode':mode,'subject':'المهارات الرقمية','grade':'السابع',
   'time':25,'rows':ROWS}},self.teacher)
  self.assertEqual(status,200,saved)
  status,created=self.req('/api/game-lab/live/create',{'activityId':saved['id'],
   'duration':25,'teams':teams,'showFeedback':showFeedback,
   'cardRequired':cardRequired,'enforceGrade':True},self.teacher)
  self.assertEqual(status,200,created)
  self.assertEqual(created['mode'],mode)
  self.assertTrue(created['studentUrl'].endswith(created['code']))
  return created['code'],saved['id']
 def roomstate(self,code,token=None):
  return self.req('/api/game-lab/live/state',{'code':code},token or self.teacher)
 def test_six_modes_two_players_and_persistent_reports(self):
  for mode in MODES:
   with self.subTest(mode=mode):
    code,aid=self.room(mode,teams=mode in ('pairs','boxes'))
    # The owning teacher can view room state; unrelated teachers cannot access reports.
    self.assertEqual(self.req('/api/game-lab/live/report?code='+code,token=self.teacher2)[0],404)
    players=[]
    for p in self.good[:2]:
     status,joined=self.req('/api/game-lab/live/join',{'code':code,'card':p['cardCode']})
     self.assertEqual(status,200,joined)
     players.append(joined['token'])
    self.assertEqual(self.roomstate(code)[1]['state']['participants'],2)
    self.assertEqual(self.req('/api/game-lab/live/start',{'code':code},self.teacher)[0],200)
    for index in range(4):
     st,teacher=self.roomstate(code)
     self.assertEqual(st,200)
     view=teacher['state'];q=view['question']
     self.assertEqual(q['index'],index)
     self.assertEqual(q['mode'],mode)
     self.assertEqual(len(q['options']),2 if mode=='truth' else 4)
     if mode=='truth':
      self.assertIn(q['candidate'],[row['a'] for row in ROWS])
      self.assertIn(q['correctAnswer'],['صح','خطأ'])
     correct=q['correctAnswer']
     # A participant must not be able to see the key before round results.
     status,student=self.req('/api/game-lab/live/state',{'code':code,'token':players[0]})
     self.assertEqual(status,200)
     self.assertIsNone(student['state']['correctAnswer'])
     self.assertNotIn('correctAnswer',student['state']['question'])
     self.assertEqual(student['state']['question']['options'],q['options'])
     with ThreadPoolExecutor(max_workers=2) as exe:
      requests=list(exe.map(lambda v:self.req('/api/game-lab/live/answer',{
       'code':code,'index':index,'token':v[0],'answer':v[1]}),[(players[0],correct),(players[1],next(x for x in q['options'] if x!=correct))]))
     self.assertEqual([x[0] for x in requests],[200,200])
     st,after=self.roomstate(code)
     self.assertEqual(st,200)
     self.assertEqual(after['state']['status'],'results')
     self.assertEqual(after['state']['answerStats']['answered'],2)
     bad_status,bad=self.req('/api/game-lab/live/answer',{'code':code,'index':index,
      'token':players[0],'answer':correct})
     self.assertEqual(bad_status,409)
     st,revealed=self.req('/api/game-lab/live/state',{'code':code,'token':players[1]})
     self.assertEqual(st,200)
     self.assertEqual(revealed['state']['correctAnswer'],correct)
     self.assertFalse(revealed['state']['me']['answerCorrect'])
     self.assertTrue(after['state']['leaderboard'][0]['score']>=100)
     self.assertEqual(self.req('/api/game-lab/live/next',{'code':code},self.teacher)[0],200)
    self.assertEqual(self.roomstate(code)[1]['state']['status'],'finished')
    status,report=self.req('/api/game-lab/live/report?code='+code,token=self.teacher)
    self.assertEqual(status,200)
    self.assertEqual(report['totalPlayers'],2)
    self.assertEqual(report['totalQuestions'],4)
    self.assertEqual(len(report['results']),2)
    self.assertEqual(sum(x['correct'] for x in report['results']),4)
    self.assertEqual(len(report['questions']),4)
    self.assertEqual(len(report['skills']),4)
    self.assertEqual(report['results'][0]['answered'],4)
    self.assertEqual(report['results'][0]['score']>=400,True)
    self.assertEqual(self.req('/api/game-lab/live/report?code='+code)[0],401)
    self.assertEqual(self.req('/api/game-lab/live/state?code='+code)[0],405)
    print('PASS V10 synchronized '+mode+' with two simultaneous players, four rounds and report',flush=True)
 def test_grade_teacher_and_card_security(self):
  code,aid=self.room('quiz',cardRequired=True)
  self.assertEqual(self.req('/api/game-lab/live/join',{'code':code,'guestName':'Guest Person'})[1]['error'],'card_required')
  status,outside=self.req('/api/game-lab/live/join',{'code':code,'card':self.outsider['cardCode']})
  self.assertEqual(status,403);self.assertEqual(outside['error'],'card_other_teacher')
  status,wrong=self.req('/api/game-lab/live/join',{'code':code,'card':self.wrong_grade['cardCode']})
  self.assertEqual(status,403);self.assertEqual(wrong['error'],'card_wrong_grade')
  status,valid=self.req('/api/game-lab/live/join',{'code':code,'card':self.good[0]['cardCode']})
  self.assertEqual(status,200,valid)
  self.assertEqual(self.req('/api/game-lab/live/join',{'code':code,'card':self.good[0]['cardCode']})[0],409)
  status,st=self.req('/api/game-lab/live/state',{'code':code,'token':valid['token']})
  self.assertEqual(status,200)
  self.assertEqual(st['state']['me']['name'],'Student A')
  status,denied=self.req('/api/game-lab/live/start',{'code':code},self.teacher2)
  self.assertEqual(status,404)
  self.assertEqual(self.req('/api/game-lab/live/finish',{'code':code},self.teacher)[0],200)
  self.assertEqual(self.req('/api/game-lab/live/join',{'code':code,'card':self.good[1]['cardCode']})[0],403)
 def test_room_rejects_unimplemented_modes(self):
  status,saved=self.req('/api/game-lab/teacher/save',{'activity':{
   'title':'Test crossword','mode':'crossword','grade':'السابع','rows':ROWS}},self.teacher)
  self.assertEqual(status,200)
  status,result=self.req('/api/game-lab/live/create',{'activityId':saved['id']},self.teacher)
  self.assertEqual(status,400)
  self.assertEqual(result['error'],'live_mode_not_supported')
if __name__=='__main__':unittest.main(verbosity=2)
