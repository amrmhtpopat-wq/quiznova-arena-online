"""Offline-only TAG AI Assistant tests. No API calls or real teacher data."""
import io
import json
import os
import unittest
from unittest.mock import patch
import tag_ai_assistant as assistant

class Handler:
    def __init__(self):self.response=None
    def send_json(self,data,status=200):self.response=(status,data)
    def log_message(self,*args): pass

class Url:
    path='/api/game-lab/ai-assistant/generate'

def row(i,kind='mcq'):
    q='ما المفهوم المناسب للسؤال التعليمي '+str(i)+' في الحاسوب؟'
    answer='وحدة الإدخال' if kind!='true_false' else 'صح'
    choices=['وحدة الإدخال','وحدة الإخراج','الذاكرة','المعالج'] if kind=='mcq' else ['صح','خطأ'] if kind=='true_false' else []
    return {'q':q,'a':answer,'g':'المهارات الرقمية','questionType':kind,
            'difficulty':'easy' if i%2 else 'hard','choices':choices,
            'explanation':'شرح مناسب للمفهوم.'}

class TAGAssistantTests(unittest.TestCase):
    def test_parse_valid_natural_arabic_request(self):
        r=assistant.parse_request({'prompt':'أنشئ 15 سؤالًا للصف السابع من درس وحدات الإدخال.',
            'count':15,'subject':'المهارات الرقمية','grade':'السابع','consent':True})
        self.assertEqual(r['count'],15)
        self.assertEqual(r['grade'],'السابع')

    def test_requires_consent_and_bounds(self):
        data={'prompt':'أنشئ مسابقة للصف السابع من درس الحاسوب','count':15}
        with self.assertRaisesRegex(ValueError,'ai_consent_required'):
            assistant.parse_request(data)
        for bad_count in (0,3,26,100,'abc'):
            with self.subTest(count=bad_count):
                with self.assertRaisesRegex(ValueError,'ai_count_invalid'):
                    assistant.parse_request({**data,'consent':True,'count':bad_count})

    def test_pii_is_not_sent(self):
        base={'prompt':'أنشئ أسئلة عن البريد الإلكتروني للطلاب: teacher@example.com','consent':True}
        with self.assertRaisesRegex(ValueError,'ai_personal_data'):
            assistant.parse_request(base)
        for bad in ('أرسل أسئلة لبطاقة G9B-0049 من الدرس',
                    'أرسلها على الرقم 0791234567 لطفل في الفصل'):
            with self.assertRaisesRegex(ValueError,'ai_personal_data'):
                assistant.parse_request({'prompt':bad,'consent':True})

    def test_validates_options_and_avoids_duplicates(self):
        choices=[row(1),row(2,'true_false'),row(3,'short'),row(4)]
        result=assistant.validate_rows(choices,15)
        self.assertEqual(len(result),4)
        self.assertEqual(result[1]['choices'],['صح','خطأ'])
        self.assertEqual(result[2]['choices'],[])
        self.assertTrue(all(r['origin']=='tag_ai_assistant' for r in result))
        bad=row(5);bad['choices']=['وحدة الإدخال']*4
        self.assertEqual(len(assistant.validate_rows(choices+[bad,choices[0]],15)),4)

    def test_key_not_exposed_and_no_auto_publish(self):
        provider={'candidates':[{'content':{'parts':[{'text':json.dumps({
            'title':'مسابقة الوحدات',
            'rows':[row(1),row(2,'true_false'),row(3,'short'),row(4)]
        },ensure_ascii=False)}]}}]}
        payload=json.dumps(provider,ensure_ascii=False).encode('utf8')
        data={'prompt':'أنشئ لي 4 أسئلة عن أجهزة الإدخال للمستوى السابع.',
              'count':4,'consent':True}
        fake_key='PRIVATE_KEY_NEVER_EXPOSE'
        with patch.dict(os.environ,{'GEMINI_API_KEY':fake_key}):
            with patch.object(assistant,'reserve_quota') as quota:
                with patch.object(assistant.urllib.request,'urlopen',
                    side_effect=lambda request,timeout:io.BytesIO(payload)) as api:
                    result=assistant.generate_for_teacher('teacher_1',data)
        quota.assert_called_once_with('teacher_1')
        self.assertEqual(result['count'],4)
        self.assertIn('راجع',result['warning'])
        self.assertNotIn(fake_key,json.dumps(result,ensure_ascii=False))
        self.assertNotIn('published',result)
        self.assertEqual(api.call_count,1)
        request=api.call_args.args[0]
        self.assertIn('/models/gemini-',request.full_url)
        self.assertEqual(request.get_header('X-goog-api-key'),fake_key)

    def test_explicit_teacher_auth_before_calling_gemini(self):
        h=Handler()
        with patch.dict(os.environ,{'TAG_LAB_ONLY_MODE':'1','GEMINI_API_KEY':'fake'}):
            with patch.object(assistant.auth,'authorized',return_value=None):
                self.assertTrue(assistant.handle_post(h,Url(),{'prompt':'أنشئ أسئلة','consent':True}))
            with patch.object(assistant.auth,'authorized',return_value={'id':'teacher'}):
                self.assertTrue(assistant.handle_post(h,Url(),{'prompt':'أنشئ عشر أسئلة عن الحاسوب',
                                                                   'consent':False}))
                self.assertEqual(h.response[1]['error'],'ai_consent_required')

if __name__=='__main__':unittest.main()
