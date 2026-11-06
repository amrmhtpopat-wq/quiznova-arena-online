"""BOOYAH v12.1: verified student card edits, class isolation, saved images and scene controls."""
import base64
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
TEMP=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(TEMP.name)/'v121.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store
import server

HTTP=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=HTTP.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(HTTP.server_port)
PNG='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+hZ1EAAAAASUVORK5CYII='

def request(path,body=None,token=None):
    headers={'Content-Type':'application/json'}
    if token:headers['Authorization']='Bearer '+token
    req=urllib.request.Request(BASE+path,
        data=json.dumps(body,ensure_ascii=False).encode() if body is not None else None,
        headers=headers)
    try:
        with urllib.request.urlopen(req,timeout=20) as res:return res.status,json.load(res)
    except urllib.error.HTTPError as err:return err.code,json.load(err)

class Release121Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        one=store.create_teacher('v121-a@example.org','TeacherPassword121!','معلم أول',
                                 'مدرسة أولى','المهارات الرقمية','boys')
        two=store.create_teacher('v121-b@example.org','TeacherPassword121!','معلم ثان',
                                 'مدرسة ثانية','المهارات الرقمية','girls')
        cls.one=one;cls.two=two
        cls.student=store.add_students(one['teacher']['id'],[
            {'name':'طالب واحد','className':'التاسع أ','avatar':'n01'}])[0]
        cls.other=store.add_students(two['teacher']['id'],[
            {'name':'طالبة','className':'السابع ب','avatar':'g01'}])[0]

    def test_01_card_edit_preserves_qr_code(self):
        token=self.one['token']
        first=next(s for s in store.list_students(self.one['teacher']['id']) if s['id']==self.student['id'])
        code,data=request('/api/teacher/students/edit',{
            'id':self.student['id'],'name':'طالب معدل','className':'التاسع ب','avatar':'n02'},token)
        self.assertEqual(code,200,data)
        after=next(s for s in store.list_students(self.one['teacher']['id']) if s['id']==self.student['id'])
        self.assertEqual(after['name'],'طالب معدل')
        self.assertEqual(after['className'],'التاسع ب')
        self.assertEqual(after['avatar'],'n02')
        self.assertEqual(after['card'],first['card'])
        self.assertEqual(after['cardCode'],first['cardCode'])
        self.assertEqual(store.student_profile_by_card(first['card'])['name'],'طالب معدل')
        self.assertEqual(store.student_profile_by_card(first['cardCode'])['avatar'],'n02')

    def test_02_teacher_isolation_and_card_archive(self):
        code,data=request('/api/teacher/students/edit',{
            'id':self.student['id'],'name':'محاولة','className':'الأول','avatar':'g01'},self.two['token'])
        self.assertNotEqual(code,200)
        code,data=request('/api/teacher/students/delete',{'id':self.student['id']},self.one['token'])
        self.assertEqual(code,400,data)
        code,data=request('/api/teacher/students/delete',{'id':self.student['id'],'confirm':True},self.two['token'])
        self.assertNotEqual(code,200)
        code,data=request('/api/teacher/students/delete',{'id':self.student['id'],'confirm':True},self.one['token'])
        self.assertEqual(code,200,data)
        self.assertIsNone(store.student_profile_by_card(self.student['card']))
        self.assertIsNone(store.student_profile_by_card(self.student['cardCode']))
        self.assertFalse(any(s['id']==self.student['id'] for s in store.list_students(self.one['teacher']['id'])))
        self.assertIsNotNone(store.query('SELECT id FROM students WHERE id=?',(self.student['id'],)))
        recreated=store.add_students(self.one['teacher']['id'],[
            {'name':'طالب معدل','className':'التاسع ب','avatar':'n01'}])
        self.assertEqual(len(recreated),1)

    def test_03_teacher_media_is_durable_scoped_and_validated(self):
        a=self.one['token'];b=self.two['token']
        code,data=request('/api/teacher/media/save',{'label':'أجزاء الحاسوب','file':PNG})
        self.assertEqual(code,401)
        code,data=request('/api/teacher/media/save',{'label':'أجزاء الحاسوب','file':PNG},a)
        self.assertEqual(code,200,data)
        asset=data['image']
        self.assertEqual(asset['file'],PNG)
        self.assertEqual(store.query('SELECT COUNT(*) AS n FROM teacher_media')['n'],1)
        code,assets=request('/api/teacher/media',token=a)
        self.assertEqual(code,200)
        self.assertTrue(any(x['id']==asset['id'] for x in assets['images']))
        code,other=request('/api/teacher/media',token=b)
        self.assertEqual(code,200)
        self.assertEqual(other['images'],[])
        code,other=request('/api/teacher/media/delete',{'id':asset['id']},b)
        self.assertNotEqual(code,200)
        code,other=request('/api/teacher/media/save',{'label':'إدخال خاطئ',
                        'file':'data:image/svg+xml;base64,PHN2Zy8+'},a)
        self.assertNotEqual(code,200)
        code,deleted=request('/api/teacher/media/delete',{'id':asset['id']},a)
        self.assertEqual(code,200)
        self.assertEqual(store.query('SELECT COUNT(*) AS n FROM teacher_media')['n'],0)

    def test_04_live_scene_change_requires_host_token(self):
        self.assertTrue({'cine-stars','cine-aurora','cine-neon','cine-desert','cine-arena'}<=set(server.SCENES))
        q={'id':'quiz121','title':'اختبار تغيير الخلفية',
           'questions':[{'id':'q1','type':'single','text':'اختبار',
                         'options':['أ','ب'],'correct':[0],'time':20,'points':1000}]}
        code,r=request('/api/room/start',{'quiz':q,'background':'cine-stars'},self.one['token'])
        self.assertEqual(code,200,r)
        pin=r['code'];host=r['hostToken'];stage=r['stageToken']
        code,bad=request('/api/room/control',{'code':pin,'action':'background','background':'cine-neon',
            'hostToken':'forged'})
        self.assertEqual(code,403)
        code,ok=request('/api/room/control',{'code':pin,'action':'background','background':'cine-aurora',
            'hostToken':host})
        self.assertEqual(code,200,ok)
        code,room=request('/api/room/state?code='+pin+'&stage='+urllib.parse.quote(stage))
        self.assertEqual(code,200,room)
        self.assertEqual(room['room']['background'],'cine-aurora')
        code,bad=request('/api/room/control',{'code':pin,'action':'background','background':'url(javascript:evil)',
            'hostToken':host})
        self.assertEqual(code,400)

    def test_05_named_characters_and_launch_assets(self):
        data=(ROOT/'avatar-names-v121.js').read_text()
        self.assertIn("n01:'نشمي'",data)
        self.assertIn('g16:',data)
        self.assertIn('b16:',data)
        count=(ROOT/'booyah-countdown-v121.js').read_text()
        for label in ("'3'","'2'","'1'","'READY'","'GO!'"):
            self.assertIn(label,count)
        portal=(ROOT/'portal.js').read_text()
        self.assertIn('bo-class-folder',portal)
        self.assertIn('/api/teacher/students/edit',portal)
        self.assertIn('/api/teacher/students/delete',portal)
        studio=(ROOT/'studio.html').read_text()
        self.assertIn('cine-desert',studio)
        self.assertIn('qnMediaMigrateLegacy',studio)

if __name__=='__main__':
    unittest.main()
