"""TAG LAB AI: mocked free-only Gemini transport, strict source citations and safe limits."""
import io
import urllib.error
import json
import os
import tempfile
import time
import unittest
import uuid
from unittest.mock import patch

from game_lab_ai_quality import selected_ai_source,verify_ai_rows


class SourceGroundingTests(unittest.TestCase):
    def setUp(self):
        self.pages=[
            {'p':1,'text':'الادخار هو الاحتفاظ بجزء من الدخل لاستخدامه في المستقبل. '
                           'ويساعد الادخار على الاستعداد للنفقات المستقبلية.'},
            {'p':2,'text':'التضخم هو ارتفاع عام ومستمر في أسعار السلع والخدمات بمرور الزمن. '
                           'وقد تؤثر زيادة الأسعار في القوة الشرائية.'}
        ]

    def test_page_balancing_and_bounds(self):
        book={'page_data':json.dumps(self.pages,ensure_ascii=False)}
        source,pages=selected_ai_source(book,1,2,lambda value,default:json.loads(value) if value else default)
        self.assertIn('[صفحة 1]',source)
        self.assertIn('[صفحة 2]',source)
        self.assertEqual(len(pages),2)
        with self.assertRaisesRegex(ValueError,'invalid_pages'):
            selected_ai_source(book,2,3,lambda value,default:json.loads(value) if value else default)
        many={'page_data':json.dumps([{'p':i,'text':'نص تعليمي واضح.'} for i in range(1,28)],ensure_ascii=False)}
        with self.assertRaisesRegex(ValueError,'ai_too_many_pages'):
            selected_ai_source(many,1,27,lambda value,default:json.loads(value) if value else default)

    def test_discard_fabricated_and_wrong_page_quotes(self):
        good='الادخار هو الاحتفاظ بجزء من الدخل لاستخدامه في المستقبل.'
        rows=[
            {'q':'ما المقصود بالادخار؟','a':'الاحتفاظ بجزء من الدخل','g':'التعريف',
             'sourcePage':1,'sourceQuote':good},
            {'q':'ما المقصود بالادخار؟','a':'نفس الإجابة','g':'التعريف',
             'sourcePage':1,'sourceQuote':good},
            {'q':'ما معنى التضخم؟','a':'ارتفاع الأسعار','g':'التعريف',
             'sourcePage':1,'sourceQuote':'التضخم هو ارتفاع عام ومستمر في أسعار السلع والخدمات بمرور الزمن.'},
            {'q':'كيف نحسب فائدة البنك؟','a':'5%','g':'تطبيق',
             'sourcePage':2,'sourceQuote':'معلومات لم ترد في الكتاب بأي شكل.'},
            {'q':'ما معنى التضخم؟','a':'ارتفاع عام في الأسعار','g':'التعريف',
             'sourcePage':2,'sourceQuote':'التضخم هو ارتفاع عام ومستمر في أسعار السلع والخدمات بمرور الزمن.'}
        ]
        result=verify_ai_rows(rows,self.pages,20)
        self.assertEqual(len(result),2,result)
        self.assertEqual([r['sourcePage'] for r in result],[1,2])
        self.assertEqual(result[0]['origin'],'ai')


class MockedAiGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        os.environ.pop('DATABASE_URL',None)
        os.environ['QUIZNOVA_SQLITE_PATH']=cls.tmp.name+'/ai.sqlite'
        os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
        import platform_store
        import server
        import game_lab_pro
        cls.store=platform_store
        cls.pro=game_lab_pro
        t=platform_store.create_teacher('ai-test-'+uuid.uuid4().hex+'@example.test',
            'TestPassword123456!','معلم التجربة','مدرسة اختبار','المالية')
        cls.teacher_id=t['teacher']['id']
        cls.book_id=uuid.uuid4().hex
        cls.pages=[
            {'p':1,'text':'الادخار هو الاحتفاظ بجزء من الدخل لاستخدامه في المستقبل. '
                           'ويساعد الادخار على الاستعداد للنفقات المستقبلية.'},
            {'p':2,'text':'التضخم هو ارتفاع عام ومستمر في أسعار السلع والخدمات بمرور الزمن. '
                           'وقد تؤثر زيادة الأسعار في القوة الشرائية.'}
        ]
        platform_store.exec_sql(
            'INSERT INTO game_lab_books(id,teacher_id,name,kind,page_count,section,'
            'page_data,source_base64,created_at) VALUES(?,?,?,?,?,?,?,?,?)',
            (cls.book_id,cls.teacher_id,'كتاب الثقافة المالية.txt','txt',2,'الوحدة الأولى',
             json.dumps(cls.pages,ensure_ascii=False),'',int(time.time())))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_no_key_or_consent_prevents_call(self):
        data={'bookId':self.book_id,'count':12,'startPage':1,'endPage':2}
        with patch.dict(os.environ,{'GEMINI_API_KEY':''}):
            with self.assertRaisesRegex(ValueError,'ai_not_configured'):
                self.pro.ai_generate(self.teacher_id,data)
        with patch.dict(os.environ,{'GEMINI_API_KEY':'mock-secret'}):
            with self.assertRaisesRegex(ValueError,'ai_consent_required'):
                self.pro.ai_generate(self.teacher_id,data)

    def test_generation_uses_choices_and_filters_unsupported_rows(self):
        source='الادخار هو الاحتفاظ بجزء من الدخل لاستخدامه في المستقبل.'
        rows=[
            {'q':'ما المقصود بالادخار؟','a':'الاحتفاظ بجزء من الدخل','g':'معرفة',
             'sourcePage':1,'sourceQuote':source},
            {'q':'كم يبلغ سعر الفائدة؟','a':'10 بالمئة','g':'تطبيق',
             'sourcePage':2,'sourceQuote':'سعر الفائدة 10 بالمئة.'}
        ]
        response={'candidates':[{'content':{'parts':[{'text':json.dumps({'rows':rows},ensure_ascii=False)}]}}]}
        captured={}
        class FakeResponse(io.BytesIO):
            def __enter__(self):return self
            def __exit__(self,*args):self.close()
        def fake_open(request,timeout):
            captured['request']=json.loads(request.data.decode('utf8'))
            captured['timeout']=timeout
            return FakeResponse(json.dumps(response,ensure_ascii=False).encode('utf8'))
        data={'bookId':self.book_id,'count':12,'startPage':1,'endPage':2,
              'consent':True,'difficulty':'advanced','focus':'application',
              'grade':'التاسع','subject':'الثقافة المالية'}
        with patch.dict(os.environ,{'GEMINI_API_KEY':'mock-secret'}):
            with patch('game_lab_pro.urllib.request.urlopen',side_effect=fake_open):
                result=self.pro.ai_generate(self.teacher_id,data)
        self.assertEqual(result['count'],1,result)
        self.assertEqual(result['rows'][0]['sourcePage'],1)
        self.assertEqual(result['rows'][0]['origin'],'ai')
        body=captured['request']
        prompt=body['contents'][0]['parts'][0]['text']
        self.assertIn('متقدمة',prompt)
        self.assertIn('تطبيق',prompt)
        self.assertIn('[صفحة 2]',prompt)
        self.assertEqual(body['generationConfig']['responseMimeType'],'application/json')
        self.assertEqual(captured['timeout'],38)


    def test_retired_free_model_falls_back_to_other_free_model(self):
        good='الادخار هو الاحتفاظ بجزء من الدخل لاستخدامه في المستقبل.'
        result={'candidates':[{'content':{'parts':[{'text':json.dumps({
            'rows':[{'q':'ما هو الادخار؟','a':'الاحتفاظ بجزء من الدخل',
             'g':'معرفة','sourcePage':1,'sourceQuote':good}]},ensure_ascii=False)}]}}]}
        urls=[]
        def simulated_provider(request,timeout):
            urls.append(request.full_url)
            if len(urls)==1:
                raise urllib.error.HTTPError(request.full_url,404,'Not Found',{},
                    io.BytesIO(b'{"error":{"status":"NOT_FOUND","message":"Model retired"}}'))
            return io.BytesIO(json.dumps(result,ensure_ascii=False).encode('utf8'))
        with patch.dict(os.environ,{'GEMINI_API_KEY':'mock-secret'}):
            with patch('game_lab_pro.urllib.request.urlopen',side_effect=simulated_provider):
                response=self.pro.ai_generate(self.teacher_id,
                    {'bookId':self.book_id,'count':8,'consent':True,
                     'startPage':1,'endPage':2})
        self.assertEqual(response['count'],1,response)
        self.assertEqual(len(urls),2,urls)
        self.assertIn('gemini-3-flash-preview',urls[0])
        self.assertIn('gemini-3.8-flash',urls[1])

    def test_free_tier_denial_shows_distinct_error(self):
        def refused(request,timeout):
            raise urllib.error.HTTPError(request.full_url,400,'Bad Request',{},
                io.BytesIO(b'{"error":{"status":"FAILED_PRECONDITION","message":"Free tier is not available for your country"}}'))
        with patch.dict(os.environ,{'GEMINI_API_KEY':'mock-secret'}):
            with patch('game_lab_pro.urllib.request.urlopen',side_effect=refused):
                with self.assertRaisesRegex(ValueError,'ai_free_tier_unavailable'):
                    self.pro.ai_generate(self.teacher_id,
                       {'bookId':self.book_id,'count':8,'consent':True,
                        'startPage':1,'endPage':2})


if __name__=='__main__':
    unittest.main(verbosity=2)
