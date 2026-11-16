"""Integration regression: 7MB textbook upload, private staging, limits and book persistence."""
import base64
import json
import os
import tempfile
import threading
import unittest
import uuid
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError


class ChunkedBookUploadTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        os.environ.pop('DATABASE_URL',None)
        os.environ.pop('OPENAI_API_KEY',None)
        os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(cls.temp.name)/'books.sqlite')
        os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
        import platform_store as store
        import server
        cls.store=store
        cls.http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        threading.Thread(target=cls.http.serve_forever,daemon=True).start()
        cls.url='http://127.0.0.1:'+str(cls.http.server_port)
        a=store.create_teacher('largebook-'+uuid.uuid4().hex+'@example.test',
            'SafeTeacherPassword123!','معلم العلوم','مدرسة اختبار','العلوم')
        b=store.create_teacher('otherbook-'+uuid.uuid4().hex+'@example.test',
            'SafeTeacherPassword123!','معلم آخر','مدرسة ثانية','اللغة العربية')
        cls.token=a['token']
        cls.other=b['token']
        cls.teacher_id=a['teacher']['id']

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.temp.cleanup()

    def post(self,path,payload,token=None):
        body=json.dumps(payload,ensure_ascii=False).encode('utf8')
        headers={'Content-Type':'application/json'}
        if token:headers['Authorization']='Bearer '+token
        request=Request(self.url+path,data=body,headers=headers,method='POST')
        try:
            with urlopen(request,timeout=50) as response:
                return response.status,json.load(response)
        except HTTPError as response:
            return response.code,json.loads(response.read())

    def get(self,path,token=None):
        headers={'Authorization':'Bearer '+token} if token else {}
        request=Request(self.url+path,headers=headers)
        try:
            with urlopen(request,timeout=30) as response:
                return response.status,json.load(response)
        except HTTPError as response:
            return response.code,json.loads(response.read())

    def test_chunked_large_txt_and_permissions(self):
        prefix=('الدرس الأول: ما عاصمة الأردن؟\n'
                'الإجابة: عمّان عاصمة المملكة الأردنية الهاشمية.\n').encode('utf8')
        raw=(prefix*((6_500_000//len(prefix))+1))[:6_500_000]
        self.assertGreater(len(raw),6_000_000)
        start={'filename':'كتاب العلوم.txt','fileSize':len(raw),'section':'الفصل الأول'}
        status,denied=self.post('/api/game-lab/pro/books/upload/start',start)
        self.assertEqual(status,401,denied)
        status,started=self.post('/api/game-lab/pro/books/upload/start',start,self.token)
        self.assertEqual(status,200,started)
        self.assertTrue(started['uploadId'])
        self.assertEqual(started['chunkBytes'],1_000_000)
        uid=started['uploadId']
        chunk_path='/api/game-lab/pro/books/upload/chunk'
        status,denied=self.post(chunk_path,{'uploadId':uid,'index':0,'data':'AA=='},self.other)
        self.assertEqual(status,400,denied)
        status,invalid=self.post(chunk_path,{'uploadId':uid,'index':2,'data':'AA=='},self.token)
        self.assertEqual(status,400,invalid)
        self.assertEqual(invalid['error'],'upload_chunk_order')
        size=started['chunkBytes']
        for index,offset in enumerate(range(0,len(raw),size)):
            content=base64.b64encode(raw[offset:offset+size]).decode('ascii')
            status,reply=self.post(chunk_path,{'uploadId':uid,'index':index,'data':content},self.token)
            self.assertEqual(status,200,reply)
            self.assertEqual(reply['uploaded'],min(offset+size,len(raw)))
        status,result=self.post('/api/game-lab/pro/books/upload/finish',{'uploadId':uid},self.token)
        self.assertEqual(status,200,result)
        self.assertGreater(result['book']['pageCount'],1)
        self.assertFalse(result['book']['sourceRetained'])
        book=result['book']
        row=self.store.query('SELECT source_base64,page_data FROM game_lab_books WHERE id=?',
            (book['id'],))
        self.assertEqual(row['source_base64'],'')
        self.assertTrue(row['page_data'])
        status,listed=self.get('/api/game-lab/pro/books',self.token)
        self.assertEqual(status,200)
        self.assertTrue(any(x['id']==book['id'] for x in listed['books']))
        status,private=self.get('/api/game-lab/pro/books',self.other)
        self.assertEqual(status,200)
        self.assertFalse(any(x['id']==book['id'] for x in private['books']))
        status,reused=self.post('/api/game-lab/pro/books/upload/finish',{'uploadId':uid},self.token)
        self.assertEqual(status,400)
        self.assertEqual(reused['error'],'upload_not_found')

    def test_limit_cancel_and_incomplete(self):
        start={'filename':'علوم.txt','fileSize':40_000_001,'section':'الفصل الأول'}
        status,oversized=self.post('/api/game-lab/pro/books/upload/start',start,self.token)
        self.assertEqual(status,400)
        self.assertEqual(oversized['error'],'file_too_large')
        start['fileSize']=1000
        status,session=self.post('/api/game-lab/pro/books/upload/start',start,self.token)
        self.assertEqual(status,200,session)
        uid=session['uploadId']
        status,unfinished=self.post('/api/game-lab/pro/books/upload/finish',
                                    {'uploadId':uid},self.token)
        self.assertEqual(status,400)
        self.assertEqual(unfinished['error'],'upload_incomplete')
        status,cancel=self.post('/api/game-lab/pro/books/upload/cancel',
                                {'uploadId':uid},self.token)
        self.assertEqual(status,200,cancel)
        self.assertTrue(cancel['cancelled'])


if __name__=='__main__':
    unittest.main(verbosity=2)
