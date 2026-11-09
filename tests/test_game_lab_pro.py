"""Game Lab Pro: textbook extraction, media persistence, card permission and live controls."""
import base64
import json
import os
import tempfile
import threading
import unittest
import uuid
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError


class ExtendedGameLabTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        os.environ.pop('DATABASE_URL',None)
        os.environ.pop('OPENAI_API_KEY',None)
        os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(cls.temp.name)/'game_lab_pro.sqlite')
        os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
        import platform_store as store
        import server
        cls.store=store
        cls.http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        threading.Thread(target=cls.http.serve_forever,daemon=True).start()
        cls.base='http://127.0.0.1:'+str(cls.http.server_port)
        a=store.create_teacher('pro-'+uuid.uuid4().hex+'@example.test','TeacherSecurePassword123!',
             'معلم التجربة','مدرسة الاختبار','المهارات الرقمية')
        b=store.create_teacher('other-'+uuid.uuid4().hex+'@example.test','TeacherSecurePassword123!',
             'معلم ثاني','مدرسة ثانية','العلوم')
        cls.token=a['token'];cls.tid=a['teacher']['id'];cls.other=b['token']
        people=store.add_students(cls.tid,[
            {'name':'طالب أ','className':'التاسع أ','avatar':'m01'},
            {'name':'طالب ب','className':'التاسع ب','avatar':'m02'}])
        cls.first,cls.second=people
        cls.bad_student=store.add_students(b['teacher']['id'],[
            {'name':'طالب خارج','className':'التاسع أ','avatar':'m01'}])[0]

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.temp.cleanup()

    def request(self,path,data=None,token=None):
        headers={}
        if token:headers['Authorization']='Bearer '+token
        if data is not None:headers['Content-Type']='application/json'
        raw=json.dumps(data,ensure_ascii=False).encode() if data is not None else None
        request=Request(self.base+path,data=raw,headers=headers)
        try:
            with urlopen(request,timeout=20) as response:
                body=response.read()
                return response.status,json.loads(body),None
        except HTTPError as err:
            body=err.read()
            return err.code,json.loads(body),None

    def make_book(self):
        source='\n'.join(
           'وحدة المعالجة المركزية: تنفذ التعليمات وتعالج البيانات داخل الحاسوب.\n'
           'ذاكرة الوصول العشوائي: تحفظ البيانات المؤقتة المستخدمة أثناء التشغيل.\n'
           'اللوحة الأم: تربط المكونات الداخلية وتسمح بالتواصل بينها.\n'
           'الشاشة: تعرض النصوص والرسومات للمستخدم.\n'
           'لوحة المفاتيح: تتيح للمستخدم إدخال النصوص والأوامر.\n'
           'الفأرة: تحرك المؤشر وتساعد على اختيار العناصر.\n'
           'السماعات: تحول الإشارات الرقمية إلى أصوات مسموعة.\n'
           'وحدة التخزين: تحفظ الملفات والبيانات حتى بعد إطفاء الجهاز.' for _ in range(2))
        return source.encode('utf8')

    def test_books_media_and_cards(self):
        data=base64.b64encode(self.make_book()).decode()
        status,out,_=self.request('/api/game-lab/pro/books/upload',{'filename':'كتاب مهارات رقمية.txt','data':data,'section':'الوحدة الأولى'},self.token)
        self.assertEqual(status,200,out)
        book=out['book'];self.assertGreater(book['pageCount'],0)
        status,out,_=self.request('/api/game-lab/pro/books',token=self.other)
        self.assertEqual(status,200);self.assertFalse(out['books'])
        status,out,_=self.request('/api/game-lab/pro/books/draft',{'bookId':book['id'],'count':8},self.token)
        self.assertEqual(status,200,out);self.assertGreaterEqual(out['count'],4)
        self.assertTrue(all(row['sourcePage']>0 for row in out['rows']))
        status,out,_=self.request('/api/game-lab/pro/books/draft',{'bookId':book['id']},self.other)
        self.assertEqual(status,400);self.assertEqual(out['error'],'book_not_found')
        status,out,_=self.request('/api/game-lab/pro/books/ai',{'bookId':book['id']},self.token)
        self.assertEqual(status,503);self.assertEqual(out['error'],'ai_not_configured')

        # 1x1 PNG: source preserved and protected from cross-teacher access
        png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO3tBB0AAAAASUVORK5CYII=')
        status,out,_=self.request('/api/game-lab/pro/media/upload',{'filename':'لوحة.png','mime':'image/png','data':base64.b64encode(png).decode()},self.token)
        self.assertEqual(status,200,out);media=out['image']['id']
        payload={'title':'نشاط الكتاب','grade':'التاسع','subject':'المهارات الرقمية','mode':'quiz',
                 'imageId':media,'bookId':book['id'],'rows':out.get('rows',[])}

        from game_lab_pro import offline_generate
        rows=offline_generate(self.tid,{'bookId':book['id'],'count':8})['rows']
        payload['rows']=rows
        status,saved,_=self.request('/api/game-lab/teacher/save',{'activity':payload},self.token)
        self.assertEqual(status,200,saved);aid=saved['id']
        status,pub,_=self.request('/api/game-lab/teacher/publish',{'id':aid,'maxAttempts':2},self.token)
        self.assertEqual(status,200,pub);code=pub['publicCode']
        # Assigned to ninth A: ninth B must not see this activity, nor bypass via its URL.
        status,out,_=self.request('/api/game-lab/pro/assignments/save',{
            'activityId':aid,'targets':[{'type':'class','value':'التاسع أ'}]},self.token)
        self.assertEqual(status,200,out)
        status,found,_=self.request('/api/game-lab/pro/card/catalog',{'card':self.first['cardCode']})
        self.assertEqual(status,200,found);self.assertEqual(len(found['activities']),1)
        status,other,_=self.request('/api/game-lab/pro/card/catalog',{'card':self.second['cardCode']})
        self.assertEqual(status,200);self.assertEqual(other['activities'],[])
        status,res,_=self.request('/api/game-lab/student/start',{'code':code,'card':self.second['cardCode']})
        self.assertEqual(status,403,res)
        status,res,_=self.request('/api/game-lab/student/start',{'code':code,'guestName':'طالب ضيف'})
        self.assertEqual(status,403,res)
        status,res,_=self.request('/api/game-lab/student/start',{'code':code,'card':self.first['cardCode']})
        self.assertEqual(status,200,res)
        self.assertIn(media,res['state']['question']['imageUrl'])
        # API must not allow teachers to attach another teacher's image.
        status,res,_=self.request('/api/game-lab/teacher/save',{'activity':payload},self.other)
        self.assertEqual(status,400,res)
        self.assertIn(res['error'],('media_not_found','book_not_found'))

    def test_live_sync_and_teacher_permissions(self):
        payload={'title':'منافسة مباشرة','grade':'التاسع','subject':'المهارات الرقمية',
                 'mode':'quiz','time':45,'rows':[{'q':'ما المكون '+str(i)+'؟',
                 'a':'الجواب '+str(i),'g':'مكونات'} for i in range(4)]}
        status,saved,_=self.request('/api/game-lab/teacher/save',{'activity':payload},self.token)
        self.assertEqual(status,200,saved)
        status,created,_=self.request('/api/game-lab/live/create',{'activityId':saved['id'],'teams':True,'duration':60,'teamNames':['الصقور','النمور']},self.token)
        self.assertEqual(status,200,created);code=created['code']
        status,not_owner,_=self.request('/api/game-lab/live/start',{'code':code},self.other)
        self.assertEqual(status,404,not_owner)
        status,one,_=self.request('/api/game-lab/live/join',{'code':code,'card':self.first['cardCode']})
        self.assertEqual(status,200,one)
        status,two,_=self.request('/api/game-lab/live/join',{'code':code,'card':self.second['cardCode']})
        self.assertEqual(status,200,two)
        self.assertNotEqual(one['state']['me']['team'],two['state']['me']['team'])
        status,started,_=self.request('/api/game-lab/live/start',{'code':code},self.token)
        self.assertEqual(status,200,started)
        status,poll,_=self.request('/api/game-lab/live/state?code='+code+'&token='+one['token'])
        self.assertEqual(status,200,poll)
        self.assertEqual(poll['state']['status'],'question')
        self.assertNotIn('correctAnswer',poll['state']['question'])
        correct=started['state']['question']['correctAnswer']
        status,yes,_=self.request('/api/game-lab/live/answer',{'code':code,'token':one['token'],'index':0,'answer':correct})
        self.assertEqual(status,200,yes)
        status,dup,_=self.request('/api/game-lab/live/answer',{'code':code,'token':one['token'],'index':0,'answer':correct})
        self.assertEqual(status,409,dup)
        status,poll,_=self.request('/api/game-lab/live/state?code='+code+'&token='+one['token'])
        self.assertEqual(poll['state']['me']['answered'],True)
        status,two_answer,_=self.request('/api/game-lab/live/answer',{'code':code,'token':two['token'],'index':0,'answer':correct})
        self.assertEqual(status,200,two_answer)
        status,results,_=self.request('/api/game-lab/live/state?code='+code+'&token='+one['token'])
        self.assertEqual(status,200,results)
        self.assertEqual(results['state']['status'],'results')
        self.assertEqual(results['state']['participants'],2)
        status,advance,_=self.request('/api/game-lab/live/next',{'code':code},self.token)
        self.assertEqual(status,200,advance)
        self.assertEqual(advance['state']['index'],1)
        status,end,_=self.request('/api/game-lab/live/finish',{'code':code},self.token)
        self.assertEqual(status,200,end)
        self.assertEqual(end['state']['status'],'finished')


if __name__=='__main__':unittest.main()
