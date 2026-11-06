"""Owner Control Center V1 integration: authentication, privacy, isolation and admin actions."""
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import uuid
from http.cookiejar import CookieJar
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cryptography.fernet import Fernet

TMP=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(TMP.name)/'admin-test.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
os.environ['BOOYAH_ADMIN_SETUP_KEY']='admin-test-key-a-long-unpredictable-value'
os.environ['BOOYAH_ADMIN_TOTP_KEY']=Fernet.generate_key().decode('ascii')

import platform_store as store
import admin_api
import server

HTTP=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=HTTP.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(HTTP.server_port)
JAR=CookieJar()
CLIENT=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(JAR))
KEY=os.environ['BOOYAH_ADMIN_SETUP_KEY']


def http(path,body=None,client=CLIENT,headers=None):
    request=urllib.request.Request(BASE+path,
        data=(json.dumps(body).encode('utf-8') if body is not None else None),
        headers={'Content-Type':'application/json','X-BOOYAH-Admin':'1',**(headers or {})})
    try:
        with client.open(request,timeout=15) as r:
            return r.status,json.load(r)
    except urllib.error.HTTPError as e:
        return e.code,json.load(e)


def csrf():
    return next((cookie.value for cookie in JAR if cookie.name=='bjcsrf'),'')


class AdminSecurityIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.teacher=store.create_teacher('admin-qa-'+uuid.uuid4().hex+'@example.org','TeacherPassword12345!',
               'معلم تجريبي','مدرسة تجريبية','المهارات الرقمية','boys')
        cls.teacher_id=cls.teacher['teacher']['id']
        cls.student=store.add_students(cls.teacher_id,[{
            'name':'طالب سري','className':'التاسع ب','avatar':'m01'}])[0]
        cls.admin_email='owner@booyahjo.example'

    def test_01_admin_bootstrap_is_separate_and_2fa_required(self):
        status,response=http('/api/admin/status')
        self.assertEqual(status,200)
        self.assertTrue(response['setupAvailable'])
        status,response=http('/api/admin/summary')
        self.assertEqual(status,401)
        self.assertNotIn('teachers',response)
        status,response=http('/api/admin/setup',{'setupKey':'wrong-setup-key-value-is-very-long','name':'Owner',
              'email':self.admin_email,'password':'SecureAdminPassword!123'})
        self.assertEqual(status,403)
        status,created=http('/api/admin/setup',{'setupKey':KEY,'name':'مالك المنصة',
              'email':self.admin_email,'password':'SecureAdminPassword!123'})
        self.assertEqual(status,200)
        self.assertTrue(created['pending2fa'])
        self.assertRegex(created['secret'],r'^[A-Z2-7]+$')
        self.__class__.otp_secret=created['secret']
        status,r=http('/api/admin/login',{'email':self.admin_email,'password':'SecureAdminPassword!123',
                                         'otp':admin_api.totp(self.otp_secret)})
        self.assertEqual(status,401,'Owner cannot sign in before verifying TOTP')
        status,r=http('/api/admin/activate',{'setupKey':KEY,'email':self.admin_email,'otp':'000000'})
        self.assertEqual(status,401)
        status,r=http('/api/admin/activate',{'setupKey':KEY,'email':self.admin_email,
                                            'otp':admin_api.totp(self.otp_secret)})
        self.assertEqual(status,200)
        self.assertTrue(r['activated'])
        status,r=http('/api/admin/setup',{'setupKey':KEY,'name':'another','email':'two@example.org',
                                         'password':'SecureAdminPassword!123'})
        self.assertEqual(status,403)
        status,r=http('/api/admin/login',{'email':self.admin_email,
                                         'password':'SecureAdminPassword!123','otp':''})
        self.assertEqual(status,401)
        status,r=http('/api/admin/login',{'email':self.admin_email,
                                         'password':'SecureAdminPassword!123',
                                         'otp':admin_api.totp(self.otp_secret)})
        self.assertEqual(status,200)
        self.assertEqual(r['admin']['role'],'owner')
        self.assertNotIn('password_hash',json.dumps(r))
        self.assertNotIn('totp',json.dumps(r))
        self.assertTrue(csrf())

    def test_02_neon_compatible_metrics_and_privacy(self):
        status,r=http('/api/admin/me')
        self.assertEqual(status,200)
        status,r=http('/api/admin/summary')
        self.assertEqual(status,200)
        self.assertGreaterEqual(r['summary']['teachers'],1)
        self.assertGreaterEqual(r['summary']['students'],1)
        self.assertEqual(len(r['summary']['days']),14)
        self.assertEqual(r['summary']['database'],'sqlite')
        status,r=http('/api/admin/teachers')
        self.assertEqual(status,200)
        self.assertGreaterEqual(r['total'],1)
        row=next(x for x in r['rows'] if x['id']==self.teacher_id)
        self.assertEqual(row['students'],1)
        serialized=json.dumps(r,ensure_ascii=False)
        self.assertNotIn(self.student['card'],serialized)
        self.assertNotIn(self.student['cardCode'],serialized)
        self.assertNotIn('password_hash',serialized)
        self.assertNotIn('salt',row)
        status,r=http('/api/admin/schools')
        self.assertEqual(status,200)
        self.assertTrue(any(x['school']=='مدرسة تجريبية' for x in r['rows']))
        status,r=http('/api/admin/audit')
        self.assertEqual(status,200)
        self.assertTrue(any(x['action']=='owner_activated' for x in r['rows']))

    def test_03_tenant_and_csrf_isolation(self):
        other=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
        for path in ('/api/admin/me','/api/admin/summary','/api/admin/teachers','/api/admin/schools','/api/admin/audit'):
            code,data=http(path,client=other)
            self.assertEqual(code,401,(path,data))
        code,data=http('/api/admin/teacher/status',{'teacherId':self.teacher_id,'disabled':True,
                   'reason':'فحص إداري تجريبي'},headers={'X-Admin-CSRF':''})
        self.assertEqual(code,403)
        code,data=http('/api/admin/teacher/status',{'teacherId':self.teacher_id,'disabled':True,
                   'reason':'فحص إداري تجريبي'})
        self.assertEqual(code,403)
        code,data=http('/api/admin/teacher/status',{'teacherId':self.teacher_id,'disabled':True,
                   'reason':'فحص إداري تجريبي'},headers={'X-Admin-CSRF':csrf()})
        self.assertEqual(code,200)
        self.assertTrue(data['disabled'])
        self.assertIsNone(store.teacher_for_token(self.teacher['token']))
        with self.assertRaises(ValueError):
            store.login(self.teacher['teacher']['email'],'TeacherPassword12345!')
        self.assertIsNotNone(store.query('SELECT * FROM students WHERE id=?',(self.student['id'],)))
        code,data=http('/api/admin/teacher/status',{'teacherId':self.teacher_id,'disabled':False,
                   'reason':'إكمال اختبار إعادة التفعيل'},headers={'X-Admin-CSRF':csrf()})
        self.assertEqual(code,200)
        new_session=store.login(self.teacher['teacher']['email'],'TeacherPassword12345!')
        self.assertTrue(store.teacher_for_token(new_session['token']))
        status,r=http('/api/admin/audit')
        self.assertEqual(status,200)
        acts=[x['action'] for x in r['rows']]
        self.assertIn('teacher_disabled',acts)
        self.assertIn('teacher_enabled',acts)
        code,data=http('/api/admin/logout',{},headers={'X-Admin-CSRF':csrf()})
        self.assertEqual(code,200)
        code,data=http('/api/admin/summary')
        self.assertEqual(code,401)


if __name__=='__main__':
    unittest.main()
