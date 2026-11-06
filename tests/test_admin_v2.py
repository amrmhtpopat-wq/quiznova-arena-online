"""BOOYAHJO Control Center V2.1: account activity, detailed read models and permission regression."""
import json
import os
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
import uuid
from http.cookiejar import CookieJar
from pathlib import Path

from cryptography.fernet import Fernet

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TEMP = tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL', None)
os.environ['QUIZNOVA_SQLITE_PATH'] = str(Path(TEMP.name) / 'admin-v2.sqlite')
os.environ['QUIZNOVA_CLOUD'] = '1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL'] = 'yes'
os.environ['BOOYAH_ADMIN_SETUP_KEY'] = 'staging-owner-setup-isolated-long-test-key'
os.environ['BOOYAH_ADMIN_TOTP_KEY'] = Fernet.generate_key().decode('ascii')

import platform_store as store
import admin_api
import server

HTTP = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
threading.Thread(target=HTTP.serve_forever, daemon=True).start()
BASE = 'http://127.0.0.1:' + str(HTTP.server_port)
COOKIES = CookieJar()
CLIENT = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(COOKIES))
EMAIL = 'admin-v2-owner@example.org'
PASSWORD = 'DedicatedOwnerPassword2026!'


def request(path, data=None, client=CLIENT, headers=None):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(data).encode('utf8') if data is not None else None,
        headers={'Content-Type': 'application/json', 'X-BOOYAH-Admin': '1', **(headers or {})},
    )
    try:
        with client.open(req, timeout=15) as res:
            return res.status, json.load(res)
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)


def query(path, **params):
    return path + '?' + urllib.parse.urlencode(params)


def csrf():
    return next((cookie.value for cookie in COOKIES if cookie.name == 'bjcsrf'), '')


class AdminV2Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        active = store.create_teacher('teacher-v2@example.org', 'TeacherStrongPassword2026!',
            'معلم نشط','مدرسة وادي الأردن','المهارات الرقمية','boys')
        old = store.create_teacher('teacher-old-v2@example.org', 'TeacherStrongPassword2026!',
            'معلم قديم','مدرسة أخرى','الرياضيات','boys')
        cls.active_id = active['teacher']['id']
        cls.old_id = old['teacher']['id']
        cls.student = store.add_students(cls.active_id, [{
            'name':'طالب اختباري','className':'التاسع ب','avatar':'m01'
        }])[0]
        past=int(time.time())-45*86400
        store.exec_sql('UPDATE teachers SET created_at=?,last_login=0 WHERE id=?',
                       (past, cls.old_id))
        store.exec_sql('UPDATE datasets SET updated_at=? WHERE teacher_id=?',
                       (past,cls.old_id))
        cls.room = 'Q72619'
        store.exec_sql('''INSERT INTO played_sessions
            (id,teacher_id,code,section,subject,quiz_title,game_mode,played_at,report,questions)
            VALUES(?,?,?,?,?,?,?,?,?,?)''',
            (uuid.uuid4().hex,cls.active_id,cls.room,'التاسع ب','المهارات الرقمية',
             'تحدي BOOYAH','individual',int(time.time()),'{}','[]'))
        store.exec_sql('''INSERT INTO student_attempts
            (id,teacher_id,student_id,quiz_id,room_code,student_name,class_name,avatar,
             correct_count,question_total,percent,score,answers,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (uuid.uuid4().hex,cls.active_id,cls.student['id'],'qtest',cls.room,'طالب اختباري',
             'التاسع ب','m01',8,10,80,800,'[]',int(time.time())))

    def test_01_secure_bootstrap(self):
        for path in ['/api/admin/insights','/api/admin/teacher/detail?id='+self.active_id,
                     '/api/admin/student/detail?id='+self.student['id'],
                     '/api/admin/sessions','/api/admin/students','/api/admin/school/detail?name=x']:
            status, result = request(path)
            self.assertEqual(status,401,(path,result))
        status, prepared = request('/api/admin/setup', {
            'setupKey':os.environ['BOOYAH_ADMIN_SETUP_KEY'],
            'name':'مدير الاختبار', 'email':EMAIL, 'password':PASSWORD})
        self.assertEqual(status,200,prepared)
        secret=prepared['secret']
        status,r=request('/api/admin/activate', {
            'setupKey':os.environ['BOOYAH_ADMIN_SETUP_KEY'],'email':EMAIL,
            'otp':admin_api.totp(secret)})
        self.assertEqual(status,200,r)
        status,r=request('/api/admin/login', {
            'email':EMAIL,'password':PASSWORD,'otp':admin_api.totp(secret)})
        self.assertEqual(status,200,r)
        self.assertTrue(csrf())

    def test_02_account_monitoring_and_privacy(self):
        status,r=request('/api/admin/insights')
        self.assertEqual(status,200,r)
        self.assertEqual(r['inactiveTeachers30d'],1)
        self.assertGreaterEqual(r['recentLogins7d'],1)
        status,r=request(query('/api/admin/teachers',status='recent'))
        self.assertEqual(status,200,r)
        self.assertEqual(r['total'],1)
        t=r['rows'][0]
        self.assertEqual(t['id'],self.active_id)
        self.assertGreater(t['last_login'],0)
        self.assertIn(t['activityStatus'],('recent','idle','inactive'))
        self.assertEqual(t['access_plan'],'free')
        status,r=request(query('/api/admin/teachers',status='inactive'))
        self.assertEqual(status,200,r)
        self.assertEqual(r['total'],1)
        self.assertEqual(r['rows'][0]['id'],self.old_id)
        status,r=request(query('/api/admin/teacher/detail',id=self.active_id))
        self.assertEqual(status,200,r)
        self.assertEqual(r['teacher']['students'],1)
        self.assertEqual(r['teacher']['sessions'],1)
        self.assertEqual(r['teacher']['attempts'],1)
        self.assertEqual(r['teacher']['averagePercent'],80.0)
        self.assertGreater(r['teacher']['last_login'],0)
        self.assertEqual(r['teacher']['access_plan'],'free')
        status,r=request(query('/api/admin/students',search='طالب اختباري'))
        self.assertEqual(status,200,r)
        self.assertEqual(r['total'],1)
        status,r=request(query('/api/admin/student/detail',id=self.student['id']))
        self.assertEqual(status,200,r)
        self.assertEqual(r['student']['attempts'],1)
        self.assertEqual(r['student']['averagePercent'],80.0)
        self.assertEqual(len(r['student']['recentAttempts']),1)
        serialized=json.dumps(r,ensure_ascii=False)
        for forbidden in ('card_token','card_code','password_hash','totp_cipher','answers'):
            self.assertNotIn(forbidden,serialized)
        self.assertNotIn(self.student['card'],serialized)
        status,r=request(query('/api/admin/sessions',search='تحدي BOOYAH'))
        self.assertEqual(status,200,r)
        self.assertEqual(r['total'],1)
        self.assertEqual(r['rows'][0]['attempts'],1)
        status,r=request(query('/api/admin/school/detail',name='مدرسة وادي الأردن'))
        self.assertEqual(status,200,r)
        self.assertEqual(r['school']['teachers'],1)
        self.assertEqual(r['school']['students'],1)
        self.assertEqual(r['school']['sessions'],1)

    def test_03_search_filters_and_bad_ids(self):
        for path in ('/api/admin/teacher/detail','/api/admin/student/detail'):
            code,data=request(query(path,id='bad-id-OR-1=1'))
            self.assertEqual(code,404,(path,data))
        code,data=request(query('/api/admin/school/detail',name='missing-school'))
        self.assertEqual(code,404)
        code,data=request(query('/api/admin/students',teacherId='invalid-id'))
        self.assertEqual(code,200)
        self.assertEqual(data['total'],0)
        code,data=request(query('/api/admin/teachers',page='not-a-number'))
        self.assertEqual(code,200)
        self.assertEqual(data['page'],1)
        code,data=request(query('/api/admin/sessions',search='nonexistent'))
        self.assertEqual(code,200)
        self.assertEqual(data['total'],0)

    def test_04_disable_audit_and_session_revocation(self):
        status,r=request('/api/admin/teacher/status',{
            'teacherId':self.active_id,'disabled':True,
            'reason':'اختبار صلاحيات المدير بشكل آمن'})
        self.assertEqual(status,403)
        status,r=request('/api/admin/teacher/status',{
            'teacherId':self.active_id,'disabled':True,
            'reason':'اختبار صلاحيات المدير بشكل آمن'},headers={'X-Admin-CSRF':csrf()})
        self.assertEqual(status,200,r)
        with self.assertRaises(ValueError):
            store.login('teacher-v2@example.org','TeacherStrongPassword2026!')
        code,r=request(query('/api/admin/teachers',status='disabled'))
        self.assertEqual(code,200,r)
        self.assertEqual(r['total'],1)
        code,r=request('/api/admin/teacher/status',{
            'teacherId':self.active_id,'disabled':False,
            'reason':'إعادة التفعيل بعد فحص الصلاحيات'},headers={'X-Admin-CSRF':csrf()})
        self.assertEqual(code,200,r)
        self.assertEqual(r['disabled'],False)
        logged=store.login('teacher-v2@example.org','TeacherStrongPassword2026!')
        self.assertTrue(store.teacher_for_token(logged['token']))
        code,r=request('/api/admin/audit')
        self.assertEqual(code,200,r)
        actions={row['action'] for row in r['rows']}
        self.assertTrue({'teacher_disabled','teacher_enabled'} <= actions)

    def test_05_logout_invalidates_access(self):
        code,r=request('/api/admin/logout',{},headers={'X-Admin-CSRF':csrf()})
        self.assertEqual(code,200,r)
        other=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
        for client in (CLIENT,other):
            code,r=request('/api/admin/insights',client=client)
            self.assertEqual(code,401)


if __name__=='__main__':
    try:
        unittest.main()
    finally:
        HTTP.shutdown()
        HTTP.server_close()
