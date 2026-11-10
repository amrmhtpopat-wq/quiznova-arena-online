"""V12.8: Card-linked practice only displays and starts quizzes for the student's grade and optional section."""
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import uuid
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
TMP=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(TMP.name)/'scope-v128.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store
import student_quiz_scope_v128 as scope
import server

TEACHER=store.create_teacher('scope-v128@example.org','TeacherScopeSecure2026!',
                             'معلم اختبار الصف','مدرسة مختبر للبنين','المهارات الرقمية','boys')
TID=TEACHER['teacher']['id']
CARDS=store.add_students(TID,[
    {'name':'طالب تاسع أ','className':'التاسع أ','avatar':'m01'},
    {'name':'طالب تاسع ب','className':'الصف التاسع ب','avatar':'m02'},
    {'name':'طالب ثامن ب','className':'الثامن / ب','avatar':'m03'},
    {'name':'طالب صف بلا شعبة','className':'9','avatar':'m04'},
    {'name':'طالب عاشر أ','className':'العاشر أ','avatar':'m05'},
])
OTHER=store.create_teacher('scope-other@example.org','TeacherScopeSecure2026!',
                           'معلم آخر','مدرسة أخرى','المهارات الرقمية','boys')
OTHERCARD=store.add_students(OTHER['teacher']['id'],[
    {'name':'طالب معلم آخر','className':'التاسع ب','avatar':'m01'}])[0]
def quiz(id,grade,section='',published=True):
    return {'id':id,'title':'اختبار '+id,'grade':grade,'section':section,
        'subject':'المهارات الرقمية',
        'settings':{'publishedSolo':published,'randomQuestions':False},
        'questions':[{'id':'t'+id,'type':'tf','text':'ذاكرة RAM مؤقتة',
                      'correct':True,'points':1000,'time':120}]}
QUIZZES=[
    quiz('g9-all','التاسع'),
    quiz('g9-a','9','أ'),
    quiz('g9-b','الصف التاسع','ب'),
    quiz('g8-b','الثامن','ب'),
    quiz('g10-a','العاشر','أ'),
    quiz('g9-unpublished','التاسع','',False),
    quiz('missing-grade','',''),
    quiz('g7','السابع')
]
store.save_snapshot(TID,{'quizzes':QUIZZES})
store.save_snapshot(OTHER['teacher']['id'],{'quizzes':[quiz('other-g9','التاسع')]})
HTTP=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=HTTP.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(HTTP.server_port)

def post(path,data):
    request=urllib.request.Request(BASE+'/api/student/solo/'+path,
        data=json.dumps(data,ensure_ascii=False).encode('utf8'),
        headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(request,timeout=10) as response:
            return response.status,json.load(response)
    except urllib.error.HTTPError as error:
        return error.code,json.load(error)

class ScopeTests(unittest.TestCase):
    def test_01_normalization(self):
        self.assertEqual(scope.class_parts('الصف التاسع ب'),(9,'b'))
        self.assertEqual(scope.class_parts('تاسع / أ'),(9,'a'))
        self.assertEqual(scope.class_parts('G9B'),(9,'b'))
        self.assertEqual(scope.class_parts('۹-ب'),(9,'b'))
        self.assertEqual(scope.class_parts('الثامن / ج'),(8,'c'))
        self.assertEqual(scope.class_parts('الحادي عشر أ'),(11,'a'))
        self.assertEqual(scope.class_parts('الثاني عشر ب'),(12,'b'))
        self.assertEqual(scope.class_parts('العاشر'),(10,''))
        self.assertEqual(scope.section_code('شعبة ب'),'b')
        self.assertEqual(scope.section_code('التاسع/ب'),'b')
        self.assertFalse(scope.allowed(quiz('unknown','',''),{'class_name':'التاسع أ'}))
        self.assertFalse(scope.allowed(quiz('class-b','التاسع','ب'),{'class_name':'التاسع أ'}))
        self.assertTrue(scope.allowed(quiz('all','التاسع'),{'class_name':'التاسع أ'}))

    def test_02_catalog_grade_and_section(self):
        expected=[
            {'g9-all','g9-a'},
            {'g9-all','g9-b'},
            {'g8-b'},
            {'g9-all'},
            {'g10-a'}
        ]
        for student,expected_ids in zip(CARDS,expected):
            status,data=post('catalog',{'card':student['cardCode']})
            self.assertEqual(status,200,data)
            actual={q['id'] for q in data['quizzes']}
            self.assertEqual(actual,expected_ids,(student['name'],data))
            self.assertNotIn('correct',json.dumps(data,ensure_ascii=False))
            self.assertTrue(all(q.get('section','')==next((x['section'] for x in QUIZZES if x['id']==q['id']),None) for q in data['quizzes']))
        status,data=post('catalog',{'card':OTHERCARD['cardCode']})
        self.assertEqual(status,200,data)
        self.assertEqual([q['id'] for q in data['quizzes']],['other-g9'])

    def test_03_start_cannot_bypass_grade_section(self):
        card_a=CARDS[0]['cardCode']
        card_b=CARDS[1]['cardCode']
        card_8=CARDS[2]['cardCode']
        for card,quiz_id in [
            (card_a,'g9-b'),(card_a,'g8-b'),(card_a,'g10-a'),
            (card_b,'g9-a'),(card_b,'g8-b'),
            (card_8,'g9-all'),(card_8,'g9-b'),
            (card_b,'missing-grade'),(card_b,'g9-unpublished'),
            (OTHERCARD['cardCode'],'g9-b')]:
            status,data=post('start',{'card':card,'quizId':quiz_id})
            self.assertEqual(status,404,(quiz_id,status,data))
            self.assertEqual(data['error'],'not_published')
        for card,quiz_id in [(card_a,'g9-a'),(card_b,'g9-b'),(card_8,'g8-b')]:
            status,data=post('start',{'card':card,'quizId':quiz_id})
            self.assertEqual(status,200,(quiz_id,status,data))
            self.assertNotIn('correct',json.dumps(data['state']['question']))
        row=store.query('SELECT COUNT(*) AS n FROM solo_sessions')
        self.assertEqual(int(row['n']),3)

    def test_04_changed_student_class_changes_permissions(self):
        original=CARDS[0]
        store.edit_student_card(TID,original['id'],original['name'],'التاسع ب','m01')
        try:
            status,data=post('catalog',{'card':original['cardCode']})
            self.assertEqual(status,200,data)
            self.assertEqual({q['id'] for q in data['quizzes']},{'g9-all','g9-b'})
            status,r=post('start',{'card':original['cardCode'],'quizId':'g9-a'})
            self.assertEqual(status,404,r)
        finally:
            store.edit_student_card(TID,original['id'],original['name'],'التاسع أ','m01')

if __name__=='__main__':
    unittest.main()
