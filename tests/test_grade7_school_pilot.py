"""Grade 7 pilot: five synthetic students, lesson -> 24 modes -> cards -> teams.

All records are created in an isolated throwaway SQLite database, never Neon.
The 20 authored questions cite the grade-7 Jordanian Digital Skills textbook
(pp. 11-23). Neither the teacher nor students are real people.
"""
import json,os,sys,tempfile,threading,unittest,uuid
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import Request,urlopen
from urllib.error import HTTPError

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

class Grade7Pilot(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory()
  os.environ.pop('DATABASE_URL',None)
  os.environ.pop('OPENAI_API_KEY',None)
  os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(cls.temp.name)/'grade7-pilot.sqlite')
  os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
  os.environ['QUIZNOVA_CLOUD']='1'
  import platform_store as store,server
  cls.store=store
  cls.http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
  threading.Thread(target=cls.http.serve_forever,daemon=True).start()
  cls.base='http://127.0.0.1:'+str(cls.http.server_port)
  teacher=store.create_teacher(
      'grade7-pilot-'+uuid.uuid4().hex+'@example.test','Grade7PilotSecurePass123!',
      'معلم تجريبي','مدرسة تجريبية','المهارات الرقمية')
  other=store.create_teacher(
      'grade7-other-'+uuid.uuid4().hex+'@example.test','Grade7PilotSecurePass123!',
      'معلم آخر','مدرسة تجريبية ثانية','العلوم')
  cls.tid=teacher['teacher']['id'];cls.token=teacher['token'];cls.other=other['token']
  cls.students=store.add_students(cls.tid,[
      {'name':'تجريبي ألف','className':'السابع أ','avatar':'m01'},
      {'name':'تجريبي باء','className':'السابع أ','avatar':'m01'},
      {'name':'تجريبي جيم','className':'السابع أ','avatar':'m01'},
      {'name':'تجريبي دال','className':'السابع ب','avatar':'m01'},
      {'name':'تجريبي هاء','className':'السابع ب','avatar':'m01'}])
  cls.pilot=json.loads((ROOT/'pilot'/'grade7_computing_reviewed.json').read_text('utf8'))

 @classmethod
 def tearDownClass(cls):
  cls.http.shutdown();cls.http.server_close();cls.temp.cleanup()

 def req(self,path,data=None,token=None):
  headers={}
  if token:headers['Authorization']='Bearer '+token
  if data is not None:headers['Content-Type']='application/json'
  req=Request(self.base+path,data=json.dumps(data,ensure_ascii=False).encode('utf8') if data is not None else None,headers=headers)
  try:
   with urlopen(req,timeout=20) as r:return r.status,json.load(r)
  except HTTPError as e:return e.code,json.load(e)

 def test_complete_school_pilot(self):
  # The teacher-facing reviewed lesson has 20 different answers with page refs.
  self.assertEqual(len(self.students),5)
  self.assertEqual(len(self.pilot['rows']),20)
  self.assertEqual(len({row['a'] for row in self.pilot['rows']}),20)
  self.assertTrue(all(11<=row['sourcePage']<=23 for row in self.pilot['rows']))
  code,pilot=self.req('/api/game-lab/pilot/grade7')
  self.assertEqual(code,200,pilot)
  self.assertEqual(len(pilot['pilot']['rows']),20)
  draft={key:self.pilot[key] for key in ('title','subject','grade','mode','time','rows')}
  code,saved=self.req('/api/game-lab/teacher/save',{'activity':draft},self.token)
  self.assertEqual(code,200,saved)
  self.assertEqual(saved['activity']['rows'][0]['sourcePage'],self.pilot['rows'][0]['sourcePage'])
  aid=saved['id']
  code,unauthorized=self.req('/api/game-lab/teacher/generate-all',{'sourceId':aid,'confirm':True},self.other)
  self.assertEqual(code,404,unauthorized)
  code,converted=self.req('/api/game-lab/teacher/generate-all',{'sourceId':aid,'confirm':True},self.token)
  self.assertEqual(code,200,converted)
  self.assertEqual(converted['templates'],24)
  self.assertEqual(converted['created'],23)
  code,convertedAgain=self.req('/api/game-lab/teacher/generate-all',{'sourceId':aid,'confirm':True},self.token)
  self.assertEqual(code,200,convertedAgain)
  self.assertEqual(convertedAgain['created'],0)
  code,shelf=self.req('/api/game-lab/teacher/list',token=self.token)
  self.assertEqual(code,200,shelf)
  templates=[a for a in shelf['activities'] if a['activity'].get('sourceGroup')==aid]
  self.assertEqual(len(templates),24)
  self.assertTrue(all(len(a['activity']['rows'])==20 for a in templates))
  self.assertTrue(all(a['activity']['rows'][0]['sourcePage']==11 for a in templates))
  byMode={a['mode']:a for a in templates}
  self.assertEqual(len(byMode),24)

  # Only class A is assigned to a quiz and its sibling flash game.
  codes={}
  for mode in ('quiz','flash'):
   activity=byMode[mode]
   code,published=self.req('/api/game-lab/teacher/publish',{
       'id':activity['id'],'maxAttempts':2},self.token)
   self.assertEqual(code,200,published)
   codes[mode]=published['publicCode']
   code,assigned=self.req('/api/game-lab/pro/assignments/save',{
       'activityId':activity['id'],'targets':[{'type':'class','value':'السابع أ'}]},self.token)
   self.assertEqual(code,200,assigned)
  for number,student in enumerate(self.students):
   code,assigned=self.req('/api/game-lab/pro/card/catalog',{'card':student['cardCode']})
   self.assertEqual(code,200,assigned)
   self.assertEqual(len(assigned['activities']),2 if number<3 else 0)
  code,denied=self.req('/api/game-lab/student/start',{
      'code':codes['quiz'],'card':self.students[4]['cardCode']})
  self.assertEqual(code,403,denied)
  code,guest=self.req('/api/game-lab/student/start',{
      'code':codes['quiz'],'guestName':'ضيف عابر'})
  self.assertEqual(code,403,guest)

  # One student can complete two modalities, but earn XP only once per source.
  student=self.students[0]
  baseline=self.store.query('SELECT xp FROM students WHERE id=?',(student['id'],))['xp']
  gain=[]
  for mode in ('quiz','flash'):
   code,start=self.req('/api/game-lab/student/start',{
     'code':codes[mode],'card':student['cardCode']})
   self.assertEqual(code,200,start)
   self.assertEqual(start['state']['total'],20)
   self.assertNotIn('correctAnswer',start['state']['question'])
   for index,row in enumerate(self.pilot['rows']):
    code,res=self.req('/api/game-lab/student/answer',{
       'token':start['token'],'index':index,'answer':row['a']})
    self.assertEqual(code,200,res)
    self.assertTrue(res['correct'])
   gain.append(res['state']['xpGain'])
  self.assertEqual(gain,[210,0])
  self.assertEqual(
      self.store.query('SELECT xp FROM students WHERE id=?',(student['id'],))['xp']-baseline,210)

  # A separate live session includes all five synthetic student cards,
  # with five distinct score updates and two groups.
  code,live=self.req('/api/game-lab/live/create',{'activityId':aid,
      'teams':True,'teamNames':['الصقور','النمور'],'duration':60},self.token)
  self.assertEqual(code,200,live)
  room=live['code']
  players=[]
  for student in self.students:
   code,joined=self.req('/api/game-lab/live/join',{'code':room,'card':student['cardCode']})
   self.assertEqual(code,200,joined)
   players.append(joined['token'])
  code,denied=self.req('/api/game-lab/live/start',{'code':room},self.other)
  self.assertEqual(code,404,denied)
  code,started=self.req('/api/game-lab/live/start',{'code':room},self.token)
  self.assertEqual(code,200,started)
  self.assertEqual(started['state']['participants'],5)
  correct=started['state']['question']['correctAnswer']
  self.assertEqual(correct,self.pilot['rows'][0]['a'])
  for token in players:
   code,response=self.req('/api/game-lab/live/answer',{
      'code':room,'token':token,'index':0,'answer':correct})
   self.assertEqual(code,200,response)
  code,board=self.req('/api/game-lab/live/state',{'code':room},self.token)
  self.assertEqual(code,200,board)
  state=board['state']
  self.assertEqual(state['status'],'results')
  self.assertEqual(state['participants'],5)
  self.assertEqual(state['answerStats']['answered'],5)
  self.assertEqual(len(state['leaderboard']),5)
  self.assertEqual(len(state['teamLeaderboard']),2)
  self.assertTrue(all(x['score']>=100 for x in state['leaderboard']))
  code,view=self.req('/api/game-lab/live/state',{'code':room,'token':players[0]})
  self.assertEqual(code,200,view)
  self.assertGreaterEqual(len(view['state'].get('teammates',[])),2)
  code,repeated=self.req('/api/game-lab/live/answer',{
       'code':room,'token':players[0],'index':0,'answer':correct})
  self.assertEqual(code,409,repeated)
  code,done=self.req('/api/game-lab/live/finish',{'code':room},self.token)
  self.assertEqual(code,200,done)
  self.assertEqual(done['state']['status'],'finished')
  print('PASS Grade 7: 20 page-linked questions, 24 modes, class card assignment, 5 students, one XP source, and synchronized 2-team room.')

if __name__=='__main__':unittest.main(verbosity=2)
