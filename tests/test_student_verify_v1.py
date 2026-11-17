"""TAG Student Verify V1 — isolated SQLite + local HTTP integration tests.

No production data, Render deploy, remote network, or real student PINs.
"""
import json
import re
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
tmp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(tmp.name)/'verify-test.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store
import student_verify as verify
import server

runner=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=runner.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(runner.server_port)


def request(method,path,payload=None,token=''):
    headers={'Authorization':'Bearer '+token} if token else {}
    data=None
    if payload is not None:
        data=json.dumps(payload,ensure_ascii=False).encode('utf-8')
        headers['Content-Type']='application/json'
    req=urllib.request.Request(BASE+path,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(req,timeout=10) as response:
            return response.status,json.load(response)
    except urllib.error.HTTPError as ex:
        return ex.code,json.load(ex)


class StudentVerifyContract(unittest.TestCase):
    def setUp(self):
        user='pin-qa-'+uuid.uuid4().hex+'@school.example'
        self.teacher=store.create_teacher(user,'PIN_Test_Pass#12345','QA PIN Teacher','مدرسة تجريبية للبنين','المهارات الرقمية','boys')
        self.teacher_id=self.teacher['teacher']['id']
        self.auth=self.teacher['token']
        self.items=store.add_students(self.teacher_id,[
            {'name':'طالب الصف التاسع التجريبي','className':'التاسع أ','avatar':'m01'},
            {'name':'طالب الصف الثامن التجريبي','className':'الثامن ب','avatar':'m01'}
        ])
        self.student=self.items[0]
        self.card=self.student['cardCode']
        self.quiz={
            'id':'qa-pin-'+uuid.uuid4().hex,'title':'اختبار هوية الطالب',
            'grade':'التاسع','subject':'مهارات رقمية',
            'settings':{'publishedSolo':True,'soloMaxAttempts':3},
            'questions':[{'id':'tf','type':'tf','text':'اختبار آمن','time':120,
                          'points':1000,'correct':True}]
        }
        store.save_snapshot(self.teacher_id,{'quizzes':[self.quiz]})

    def teacher_post(self,op,payload):
        return request('POST','/api/teacher/student-verify/'+op,payload,self.auth)
    def solo_post(self,op,payload):
        return request('POST','/api/student/solo/'+op,payload)

    def activate(self):
        status,issued=self.teacher_post('issue',{})
        self.assertEqual(status,200,issued)
        self.assertEqual(len(issued['pins']),2)
        secrets={x['id']:x['pin'] for x in issued['pins']}
        status,settings=self.teacher_post('toggle',{'enabled':True,'deliveredConfirmed':True})
        self.assertEqual(status,200,settings)
        self.assertTrue(settings['enabled'])
        return secrets[self.student['id']]

    def test_disabled_rollout_preserves_existing_quiz_starts(self):
        code,initial=request('GET','/api/teacher/student-verify',token=self.auth)
        self.assertEqual(code,200)
        self.assertFalse(initial['enabled'])
        self.assertEqual(initial['students'],2)
        self.assertEqual(initial['issued'],0)
        status,data=self.solo_post('start',{'card':self.card,'quizId':self.quiz['id']})
        self.assertEqual(status,200,data)

    def test_no_pin_leak_and_teacher_only_enrollment(self):
        self.assertEqual(request('GET','/api/teacher/student-verify')[0],401)
        self.assertEqual(request('POST','/api/teacher/student-verify/issue',{})[0],401)
        self.assertEqual(self.teacher_post('toggle',{'enabled':True,'deliveredConfirmed':True})[1]['error'],'pin_not_ready')
        status,issued=self.teacher_post('issue',{})
        self.assertEqual(status,200)
        self.assertEqual(len(issued['pins']),2)
        self.assertEqual(len({row['pin'] for row in issued['pins']}),2)
        for row in issued['pins']:
            self.assertRegex(row['pin'],r'^[0-9]{6}$')
            record=store.query('SELECT pin_hash,pin_salt FROM student_verify_pins WHERE student_id=?',(row['id'],))
            self.assertNotEqual(row['pin'],record['pin_hash'])
            self.assertNotIn(row['pin'],json.dumps(record))
        self.assertNotIn('pin',store.list_students(self.teacher_id)[0])
        again=self.teacher_post('issue',{})[1]
        self.assertEqual(again['pins'],[])
        self.assertEqual(self.teacher_post('toggle',{'enabled':True})[1]['error'],'distribution_confirmation_required')
        self.assertEqual(self.teacher_post('toggle',{'enabled':True,'deliveredConfirmed':True})[0],200)
        public=self.solo_post('catalog',{'card':self.card})[1]
        self.assertTrue(public['student']['pinRequired'])
        self.assertNotIn('pin',public['student'])

    def test_pin_required_wrong_and_single_active_cross_quiz(self):
        pin=self.activate()
        req={'card':self.card,'quizId':self.quiz['id']}
        self.assertEqual(self.solo_post('start',req)[1]['error'],'student_pin_required')
        self.assertEqual(self.solo_post('start',{**req,'pin':'abcdef'})[1]['error'],'student_pin_invalid')
        status,started=self.solo_post('start',{**req,'pin':pin})
        self.assertEqual(status,200,started)
        self.assertGreater(len(started['token']),40)
        other={'id':'second-'+uuid.uuid4().hex,'title':'اختبار ثاني',
               'grade':'التاسع','settings':{'publishedSolo':True},'questions':self.quiz['questions']}
        store.save_snapshot(self.teacher_id,{'quizzes':[self.quiz,other]})
        status,blocked=self.solo_post('start',{'card':self.card,'quizId':other['id'],'pin':pin})
        self.assertEqual(status,409,blocked)
        self.assertEqual(blocked['error'],'active_attempt')
        status,complete=self.solo_post('answer',{'token':started['token'],'index':0,'answer':True})
        self.assertEqual(status,200,complete)
        self.assertTrue(complete['state']['finished'])
        self.assertEqual(self.solo_post('start',{'card':self.card,'quizId':other['id'],'pin':pin})[0],200)

    def test_parallel_starts_do_not_bypass_one_attempt(self):
        pin=self.activate()
        payload={'card':self.card,'quizId':self.quiz['id'],'pin':pin}
        with ThreadPoolExecutor(max_workers=5) as pool:
            results=list(pool.map(lambda _:self.solo_post('start',payload),range(5)))
        self.assertEqual(sum(status==200 for status,_ in results),1,results)
        self.assertEqual(sum(status==409 and r.get('error')=='active_attempt'
                             for status,r in results),4,results)
        status,cleared=self.teacher_post('unlock',{'studentId':self.student['id']})
        self.assertEqual(status,200,cleared)
        self.assertEqual(cleared['revoked'],1)
        self.assertEqual(self.solo_post('start',payload)[0],200)

    def test_five_bad_pins_lock_correct_pin_until_teacher_reset(self):
        pin=self.activate()
        wrong='000000' if pin!='000000' else '999999'
        req={'card':self.card,'quizId':self.quiz['id']}
        for i in range(4):
            status,data=self.solo_post('start',{**req,'pin':wrong})
            self.assertEqual(status,403,data)
        status,lock=self.solo_post('start',{**req,'pin':wrong})
        self.assertEqual(status,429,lock)
        self.assertEqual(lock['error'],'student_pin_locked')
        self.assertEqual(self.solo_post('start',{**req,'pin':pin})[0],429)
        status,rotated=self.teacher_post('issue',{'studentId':self.student['id'],'rotate':True})
        self.assertEqual(status,200,rotated)
        new=rotated['pins'][0]['pin']
        self.assertEqual(self.solo_post('start',{**req,'pin':pin})[0],403)
        self.assertEqual(self.solo_post('start',{**req,'pin':new})[0],200)

    def test_live_join_requires_pin_and_prevents_reuse(self):
        pin=self.activate()
        payload={'quiz':self.quiz,'section':'التاسع أ','requireCard':False}
        status,room=request('POST','/api/room/start',payload,self.auth)
        self.assertEqual(status,200,room)
        code=room['code']
        status,config=request('GET','/api/room/config?code='+code)
        self.assertTrue(config['pinRequired'])
        status,blank=request('POST','/api/room/join',{'code':code,'name':'شخص آخر'})
        self.assertEqual(blank['error'],'card_required')
        status,bad=request('POST','/api/room/join',{'code':code,'card':self.card,'pin':'x'})
        self.assertEqual(status,403,bad)
        status,valid=request('POST','/api/room/join',{'code':code,'card':self.card,'pin':pin})
        self.assertEqual(status,200,valid)
        status,duplicate=request('POST','/api/room/join',{'code':code,'card':self.card,'pin':pin})
        self.assertEqual(status,409,duplicate)
        self.assertEqual(duplicate['error'],'card_already_joined')

    def test_rotating_pin_revokes_active_quiz_token(self):
        old=self.activate()
        req={'card':self.card,'quizId':self.quiz['id']}
        status,started=self.solo_post('start',{**req,'pin':old})
        self.assertEqual(status,200,started)
        status,rotation=self.teacher_post('issue',{'studentId':self.student['id'],'rotate':True})
        self.assertEqual(status,200,rotation)
        new=rotation['pins'][0]['pin']
        status,revoked=self.solo_post('state',{'token':started['token']})
        self.assertEqual(status,401,revoked)
        self.assertEqual(revoked['error'],'invalid_session')
        status,again=self.solo_post('start',{**req,'pin':new})
        self.assertEqual(status,200,again)

    def test_archived_cards_cannot_access_catalog_or_start_quiz(self):
        store.archive_student_card(self.teacher_id,self.student['id'])
        status,result=self.solo_post('catalog',{'card':self.card})
        self.assertEqual(status,403,result)
        self.assertEqual(result['error'],'invalid_card')
        status,result=self.solo_post('start',{'card':self.card,'quizId':self.quiz['id']})
        self.assertEqual(status,403,result)
        self.assertEqual(result['error'],'invalid_card')

    def test_live_session_joined_before_activation_cannot_answer_afterwards(self):
        # A live player joined without PIN while protection was disabled.
        payload={'quiz':self.quiz,'section':'التاسع أ'}
        status,room=request('POST','/api/room/start',payload,self.auth)
        self.assertEqual(status,200,room)
        code=room['code']
        status,player=request('POST','/api/room/join',{'code':code,'card':self.card})
        self.assertEqual(status,200,player)
        self.activate()
        status,answer=request('POST','/api/room/answer',{'code':code,'playerId':player['playerId'],
                                  'index':0,'answer':True})
        self.assertEqual(status,403,answer)
        self.assertEqual(answer['error'],'student_pin_required')

    def test_realistic_school_batch_226_pins_keeps_cards_and_qr_unchanged(self):
        # Simulate the actual roster size without using real students or Neon.
        extra=[{'name':'QA Student '+str(i).zfill(3),'className':'التاسع أ','avatar':'m01'}
               for i in range(1,225)]
        self.assertEqual(len(store.add_students(self.teacher_id,extra)),224)
        before={x['id']:(x['cardCode'],x['card']) for x in store.list_students(self.teacher_id)}
        self.assertEqual(len(before),226)
        status,batch=self.teacher_post('issue',{})
        self.assertEqual(status,200,batch if status!=200 else None)
        self.assertEqual(len(batch['pins']),226)
        self.assertEqual(len(set(p['pin'] for p in batch['pins'])),226)
        self.assertTrue(all(len(p['pin'])==6 and p['pin'].isdigit() for p in batch['pins']))
        after={x['id']:(x['cardCode'],x['card']) for x in store.list_students(self.teacher_id)}
        self.assertEqual(before,after)
        self.assertEqual(batch['status']['issued'],226)
        self.assertFalse(batch['status']['enabled'])

    def test_teacher_can_safely_replace_226_lost_pins_after_confirmation(self):
        # Exactly the school's roster size, but entirely synthetic students.
        extra=[{'name':'QA Student '+str(i).zfill(3),'className':'التاسع أ','avatar':'m01'}
               for i in range(1,225)]
        self.assertEqual(len(store.add_students(self.teacher_id,extra)),224)
        before={s['id']:(s['cardCode'],s['card']) for s in store.list_students(self.teacher_id)}
        status,first=self.teacher_post('issue',{})
        self.assertEqual(status,200,first)
        self.assertEqual(len(first['pins']),226)
        self.assertEqual(self.teacher_post('issue',{})[1]['pins'],[])
        old_hash=store.query('SELECT pin_hash FROM student_verify_pins WHERE student_id=?',
                             (self.student['id'],))['pin_hash']
        request_body={'expectedStudents':226,'confirmation':'REISSUE 226'}
        unauth=request('POST','/api/teacher/student-verify/reissue-all',request_body)
        self.assertEqual(unauth[0],401)
        missing=self.teacher_post('reissue-all',{'expectedStudents':226})
        self.assertEqual(missing[0],400,missing)
        self.assertEqual(missing[1]['error'],'pin_rotation_confirmation_required')
        mismatch=self.teacher_post('reissue-all',{'expectedStudents':225,'confirmation':'REISSUE 225'})
        self.assertEqual(mismatch[0],400,mismatch)
        self.assertEqual(mismatch[1]['error'],'student_count_changed')
        self.assertEqual(store.query('SELECT pin_hash FROM student_verify_pins WHERE student_id=?',
                            (self.student['id'],))['pin_hash'],old_hash)
        status,recovered=self.teacher_post('reissue-all',request_body)
        self.assertEqual(status,200,recovered if status!=200 else None)
        self.assertEqual(len(recovered['pins']),226)
        self.assertEqual(len({r['pin'] for r in recovered['pins']}),226)
        self.assertEqual(recovered['status']['issued'],226)
        self.assertFalse(recovered['status']['enabled'])
        self.assertTrue(all(re.fullmatch(r'[0-9]{6}',r['pin']) for r in recovered['pins']))
        after={s['id']:(s['cardCode'],s['card']) for s in store.list_students(self.teacher_id)}
        self.assertEqual(before,after)
        self.assertNotEqual(store.query('SELECT pin_hash FROM student_verify_pins WHERE student_id=?',
                             (self.student['id'],))['pin_hash'],old_hash)
        self.assertEqual(self.teacher_post('issue',{})[1]['pins'],[])

    def test_bulk_recovery_denied_when_protection_enabled(self):
        pin=self.activate()
        status,result=self.teacher_post('reissue-all',
                                       {'expectedStudents':2,'confirmation':'REISSUE 2'})
        self.assertEqual(status,400,result)
        self.assertEqual(result['error'],'pin_protection_must_be_disabled')
        status,bad=self.teacher_post('reissue-all',
                                     {'expectedStudents':True,'confirmation':'REISSUE True'})
        self.assertEqual(status,400,bad)
        self.assertEqual(bad['error'],'invalid_expected_students')

    def test_tag_lab_solo_and_live_require_student_pin(self):
        import game_lab_api as games
        import game_lab_live as lab_live
        pin=self.activate()
        rows=[{'q':'سؤال تجريبي '+str(i),'a':'جواب '+str(i),'g':'عام'}
              for i in range(1,5)]
        activity=games.save(self.teacher_id,{'activity':{
            'title':'TAG LAB QA','subject':'المهارات الرقمية',
            'grade':'التاسع','mode':'quiz','rows':rows}})
        published=games.publish(self.teacher_id,{'id':activity['id'],'maxAttempts':3},True)
        code=published['publicCode']
        path='/api/game-lab/student/start'
        data={'code':code,'card':self.card}
        status,guest=request('POST',path,{'code':code,'guestName':'طالب ضيف'})
        self.assertEqual(status,403,guest)
        self.assertEqual(guest['error'],'card_required')
        status,wrong=request('POST',path,{**data,'pin':'999xyz'})
        self.assertEqual(status,403,wrong)
        self.assertEqual(wrong['error'],'student_pin_invalid')
        status,started=request('POST',path,{**data,'pin':pin})
        self.assertEqual(status,200,started)
        self.assertTrue(started['state'])
        status,busy=request('POST',path,{**data,'pin':pin})
        self.assertEqual(status,409,busy)
        self.assertEqual(busy['error'],'active_attempt')
        live=lab_live.create(self.teacher_id,{'activityId':activity['id']})
        room=live['code']
        path='/api/game-lab/live/join'
        status,guest=request('POST',path,{'code':room,'guestName':'زائر'})
        self.assertEqual(status,403,guest)
        self.assertEqual(guest['error'],'card_required')
        status,wrong=request('POST',path,{'code':room,'card':self.card,'pin':'wrong'})
        self.assertEqual(status,403,wrong)
        self.assertEqual(wrong['error'],'student_pin_invalid')
        status,joined=request('POST',path,{'code':room,'card':self.card,'pin':pin})
        self.assertEqual(status,200,joined)
        status,again=request('POST',path,{'code':room,'card':self.card,'pin':pin})
        self.assertEqual(status,409,again)
        self.assertEqual(again['error'],'already_joined')
        status,st=request('POST','/api/game-lab/live/state',
                          {'code':room,'token':joined['token']})
        self.assertEqual(status,200,st)
        self.assertTrue(st['state'])

    def test_wrong_teacher_cannot_reissue_or_unlock_others(self):
        pin=self.activate()
        other=store.create_teacher('pin-other-'+uuid.uuid4().hex+'@school.example',
            'OtherTeacherPass#123','Other','مدرسة أخرى','عام','mixed')
        other_token=other['token']
        st=request('POST','/api/teacher/student-verify/issue',
                   {'studentId':self.student['id'],'rotate':True},other_token)
        self.assertEqual(st[0],400)
        self.assertEqual(st[1]['error'],'student_not_found')
        status,unlocked=request('POST','/api/teacher/student-verify/unlock',
                                {'studentId':self.student['id']},other_token)
        self.assertEqual(status,400)
        self.assertEqual(unlocked['error'],'student_not_found')


if __name__=='__main__':
    unittest.main()
