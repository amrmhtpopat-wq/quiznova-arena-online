"""BOOYAHJO Game Lab end-to-end contract: authorization, attempts, XP and reports."""
import json,os,tempfile,threading,unittest,uuid
from http.server import ThreadingHTTPServer
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from pathlib import Path

class LabAPITest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory()
  os.environ.pop('DATABASE_URL',None)
  os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(cls.temp.name)/'game_lab_contract.sqlite')
  os.environ['QUIZNOVA_CLOUD']='1'
  os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
  import platform_store,server
  cls.store=platform_store
  cls.server=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
  threading.Thread(target=cls.server.serve_forever,daemon=True).start()
  cls.url='http://127.0.0.1:'+str(cls.server.server_port)
  a=platform_store.create_teacher('lab1-'+uuid.uuid4().hex+'@example.test','TestTeacherStrong123!',
           'المعلم التجريبي','المدرسة التجريبية','المهارات الرقمية')
  b=platform_store.create_teacher('lab2-'+uuid.uuid4().hex+'@example.test','TestTeacherStrong123!',
           'معلم ثان','مدرسة أخرى','الرياضيات')
  cls.teacher=a['teacher'];cls.token=a['token'];cls.other=b['token']
  cls.student=platform_store.add_students(cls.teacher['id'],[{'name':'الطالب التجريبي','className':'التاسع ب','avatar':'m01'}])[0]
  cls.outsider=platform_store.add_students(b['teacher']['id'],[{'name':'طالب ثاني','className':'التاسع أ','avatar':'m01'}])[0]

 @classmethod
 def tearDownClass(cls):
  cls.server.shutdown();cls.server.server_close();cls.temp.cleanup()

 def request(self,endpoint,data=None,token=None):
  headers={}
  if token:headers['Authorization']='Bearer '+token
  if data is not None:headers['Content-Type']='application/json'
  req=Request(self.url+endpoint,data=json.dumps(data,ensure_ascii=False).encode() if data is not None else None,headers=headers)
  try:
   with urlopen(req,timeout=12) as resp:return resp.status,json.load(resp)
  except HTTPError as err:return err.code,json.load(err)

 def test_game_lab(self):
  payload={'title':'مختبر اختبار شامل','subject':'المهارات الرقمية','grade':'التاسع','mode':'quiz','time':25,
       'rows':[{'q':'س'+str(i),'a':'إجابة'+str(i),'g':'مجموعة'+str(i%2)} for i in range(8)]}
  code,saved=self.request('/api/game-lab/teacher/save',{'activity':payload},self.token)
  self.assertEqual(code,200,saved);aid=saved['id']
  self.assertEqual(saved['questionCount'],8)
  code,result=self.request('/api/game-lab/teacher/list',token=self.other)
  self.assertEqual(code,200);self.assertEqual(len(result['activities']),0)
  code,denied=self.request('/api/game-lab/teacher/publish',{'id':aid,'maxAttempts':2},self.other)
  self.assertEqual(code,404,denied)
  code,published=self.request('/api/game-lab/teacher/publish',{'id':aid,'maxAttempts':2},self.token)
  self.assertEqual(code,200,published);public=published['publicCode']
  code,meta=self.request('/api/game-lab/public?code='+public)
  self.assertEqual(code,200,meta)
  self.assertNotIn('rows',str(meta));self.assertNotIn('إجابة0',str(meta))
  code,bad=self.request('/api/game-lab/student/start',{'code':public,'card':self.outsider['cardCode']})
  self.assertEqual(code,403,bad)
  code,unauth=self.request('/api/game-lab/teacher/list')
  self.assertEqual(code,401,unauth)
  baseline=self.store.query('SELECT xp FROM students WHERE id=?',(self.student['id'],))['xp']
  gains=[]
  for attempt in range(2):
   code,started=self.request('/api/game-lab/student/start',{'code':public,'card':self.student['cardCode']})
   self.assertEqual(code,200,started)
   token=started['token'];state=started['state']
   self.assertNotIn('rows',str(state));self.assertNotIn('correctAnswer',str(state))
   for ix in range(8):
    answer='إجابة'+str(ix)
    self.assertIn(answer,state['question']['choices'])
    code,replied=self.request('/api/game-lab/student/answer',{'token':token,'index':ix,'answer':answer})
    self.assertEqual(code,200,replied)
    self.assertTrue(replied['correct'])
    state=replied['state']
   self.assertTrue(state['finished'])
   gains.append(state['xpGain'])
  self.assertEqual(gains,[90,0])
  self.assertEqual(self.store.query('SELECT xp FROM students WHERE id=?',(self.student['id'],))['xp']-baseline,90)
  code,limited=self.request('/api/game-lab/student/start',{'code':public,'card':self.student['cardCode']})
  self.assertEqual(code,403,limited);self.assertEqual(limited['error'],'attempt_limit')
  code,report=self.request('/api/game-lab/teacher/reports?id='+aid,token=self.token)
  self.assertEqual(code,200,report);self.assertEqual(report['total'],2);self.assertEqual(report['averagePercent'],100)
  code,denied=self.request('/api/game-lab/teacher/reports?id='+aid,token=self.other)
  self.assertEqual(code,404,denied)
  code,res=self.request('/api/game-lab/teacher/unpublish',{'id':aid},self.token)
  self.assertEqual(code,200);self.assertFalse(res['published'])
  code,notfound=self.request('/api/game-lab/public?code='+public)
  self.assertEqual(code,404,notfound)
  code,res=self.request('/api/game-lab/teacher/delete',{'id':aid,'confirm':True},self.token)
  self.assertEqual(code,200,res)
  code,res=self.request('/api/game-lab/teacher/list',token=self.token)
  self.assertEqual(code,200);self.assertFalse(any(x['id']==aid for x in res['activities']))


 def test_structured_question_bank_persists_and_reuses_for_24_templates(self):
  """MCQ + true/false + free response survive save, reopen, conversion and replay."""
  import game_lab_api as games
  bank=[
   {'q':'ما معنى الادخار؟','a':'الاحتفاظ بجزء من الدخل','g':'الادخار',
    'questionType':'mcq','difficulty':'easy',
    'choices':['استثمار الديون','الاحتفاظ بجزء من الدخل','زيادة الإنفاق','شراء الأسهم'],
    'explanation':'الادخار يساعد في الاستعداد للمستقبل.',
    'sourcePage':1,'sourceQuote':'الادخار هو الاحتفاظ بجزء من الدخل لاستخدامه في المستقبل.',
    'origin':'ai'},
   {'q':'التضخم هو ارتفاع عام ومستمر في الأسعار.','a':'صح','g':'التضخم',
    'questionType':'true_false','difficulty':'medium','choices':['صح','خطأ'],
    'sourcePage':2,'sourceQuote':'التضخم هو ارتفاع عام ومستمر في أسعار السلع والخدمات.'},
   {'q':'ما أثر الادخار على المستقبل؟','a':'يساعد على الاستعداد للنفقات','g':'الادخار',
    'questionType':'short','difficulty':'hard','explanation':'فكر في التخطيط المالي.',
    'sourcePage':1,'sourceQuote':'يساعد الادخار على الاستعداد للنفقات المستقبلية.'},
   {'q':'ما هدف الميزانية؟','a':'تنظيم الإيرادات والنفقات','g':'الموازنة',
    'questionType':'mcq','difficulty':'medium',
    'choices':['زيادة الأسعار','تنظيم الإيرادات والنفقات','تقليل التعلم','إيقاف البيع'],
    'sourcePage':3,'sourceQuote':'الموازنة هي خطة مالية تنظم الإيرادات والنفقات.'}
  ]
  data={'title':'بنك الأسئلة الذكي','subject':'الثقافة المالية','grade':'التاسع',
        'mode':'quiz','rows':bank}
  status,saved=self.request('/api/game-lab/teacher/save',{'activity':data},self.token)
  self.assertEqual(status,200,saved)
  self.assertEqual(saved['activity']['rows'][0]['choices'],bank[0]['choices'])
  self.assertEqual(saved['activity']['rows'][0]['difficulty'],'easy')
  self.assertEqual(saved['activity']['rows'][0]['sourceQuote'],bank[0]['sourceQuote'])
  aid=saved['id']
  status,listing=self.request('/api/game-lab/teacher/list',token=self.token)
  self.assertEqual(status,200)
  reopened=next(item for item in listing['activities'] if item['id']==aid)
  self.assertEqual(reopened['activity']['rows'][1]['questionType'],'true_false')
  self.assertEqual(reopened['activity']['rows'][2]['explanation'],'فكر في التخطيط المالي.')
  status,all_games=self.request('/api/game-lab/teacher/generate-all',
                                {'sourceId':aid,'confirm':True},self.token)
  self.assertEqual(status,200,all_games)
  self.assertEqual(all_games['templates'],24)
  status,listing=self.request('/api/game-lab/teacher/list',token=self.token)
  self.assertEqual(status,200)
  variants=[item for item in listing['activities'] if item.get('sourceGroup')==aid]
  self.assertEqual(len(variants),24)
  self.assertTrue(all(item['activity']['rows'][0]['choices']==bank[0]['choices']
                      for item in variants))
  tf_state={'rows':bank,'index':1,'mode':'truth','duration':25,'score':0}
  self.assertEqual(games.expected_answer(tf_state,'test-digest'),'صح')
  question=games.question_state(tf_state,'test-digest')
  self.assertEqual(question['candidate'],bank[1]['q'])
  self.assertEqual(question['choices'],['صح','خطأ'])
  bad={**data,'title':'معيبة','rows':[{**bank[0],'choices':['جواب واحد','جواب ثان']}]+bank[1:]}
  status,out=self.request('/api/game-lab/teacher/save',{'activity':bad},self.token)
  self.assertEqual(status,400,out)
  self.assertEqual(out['error'],'correct_answer_missing_from_choices')

if __name__=='__main__':unittest.main(verbosity=2)
