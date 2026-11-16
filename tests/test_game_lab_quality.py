"""TAG LAB: do not turn headings or PDF fragments into false questions."""
import os
import tempfile
import unittest


class BookQuestionQuality(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        os.environ.pop('DATABASE_URL',None)
        os.environ['QUIZNOVA_SQLITE_PATH']=cls.temp.name+'/quality.sqlite'
        os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
        import platform_store
        platform_store.init()
        from game_lab_pro import deterministic_draft, source_selection
        cls.extract=staticmethod(deterministic_draft)
        cls.select=staticmethod(source_selection)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_reject_financial_textbook_headings(self):
        source='''[صفحة 1]
الشاعر: الإعداد والتطوير بالتعاون مع الجهات الأخرى في الوزارة.
الثقافة المالية: الفصل الدراسي الأول من كتاب الثقافة المالية للصف التاسع.
يتألف هذا الكتاب من وحدتين رئيسيتين، هما: الاستثمار والادخار.
الآتي: يمكنك قراءة النصوص المرافقة للأسئلة قبل تنفيذ النشاط.
[صفحة 7]
وتذكر أن الأصول قد تكون ملموسة، مثل: مبانٍ ومعدات وأجهزة كثيرة.
وتذكر أن الأصول قد تكون غير ملموسة، مثل: حقوق النشر وبراءات الاختراع.
أفكر: كيف يمكن استثمار الأموال في مختلف المشروعات؟
النمو المالي: هل يساعد الادخار على تحقيق النمو؟
'''
        self.assertEqual(self.extract(source,20),[])

    def test_explicit_definitions_and_functions_only(self):
        source='''[صفحة 3]
الادخار هو الاحتفاظ بجزء من الدخل لاستخدامه في المستقبل.
التضخم هو ارتفاع عام ومستمر في أسعار السلع والخدمات بمرور الزمن.
[صفحة 4]
وحدة المعالجة المركزية: تنفذ التعليمات وتعالج البيانات داخل الحاسوب.
ذاكرة الوصول العشوائي: تحفظ البيانات المؤقتة المستخدمة أثناء التشغيل.
اللوحة الأم: تربط المكونات الداخلية وتسمح بالتواصل بينها.
الشاشة: تعرض النصوص والرسومات للمستخدم.
لوحة المفاتيح: تتيح للمستخدم إدخال النصوص والأوامر.
الفأرة: تحرك المؤشر وتساعد على اختيار العناصر.
السماعات: تحول الإشارات الرقمية إلى أصوات مسموعة.
وحدة التخزين: تحفظ الملفات والبيانات حتى بعد إطفاء الجهاز.
'''
        rows=self.extract(source,20)
        self.assertEqual(len(rows),10,rows)
        self.assertEqual(rows[0]['q'],'ما المقصود بالادخار؟')
        self.assertEqual(rows[1]['q'],'ما المقصود بالتضخم؟')
        self.assertEqual(rows[2]['q'],'ما وظيفة وحدة المعالجة المركزية؟')
        self.assertEqual(rows[2]['sourcePage'],4)
        self.assertTrue(all(row['sourceQuote'] and row['a'] in row['sourceQuote'] for row in rows))

    def test_explanatory_transition_is_not_mistaken_for_a_concept(self):
        source='''[صفحة 9]
يُعرَفُ الادخارُ بأنَّهُ تخصيصُ جزءٍ من الدخلِ للمستقبل.
بمرور الوقت. وهذا يعني أن الأسر تحفظ جزءًا من مواردها.
'''
        rows=self.extract(source,12)
        self.assertEqual(len(rows),1,rows)
        self.assertEqual(rows[0]['q'],'ما المقصود بالادخار؟')
        self.assertNotIn('مرور الوقت',[row['q'] for row in rows])
        self.assertEqual(rows[0]['sourcePage'],9)

    def test_mixed_question_styles_are_created_from_explicit_evidence(self):
        source='''[صفحة 9]
يُعرَفُ الادخارُ بأنَّهُ تخصيصُ جزءٍ من الدخلِ للمستقبل.
بهدفِ المحافظةِ على المالِ.
الأدوات قد تكون ملموسة، مثل: القلم والكتاب؛ وقد تكون غير ملموسة، مثل: البرامج والتطبيقات.
'''
        rows=self.extract(source,12)
        questions=[row['q'] for row in rows]
        self.assertIn('ما المقصود بالادخار؟',questions)
        self.assertIn('اذكر أمثلة على الأصول الملموسة.',questions)
        self.assertIn('اذكر أمثلة على الأصول غير الملموسة.',questions)
        self.assertTrue(all(row['sourcePage']==9 for row in rows))

    def test_explicit_answers_with_page(self):
        source='''[صفحة 12]
س: ما عاصمة الأردن؟
ج: عمّان
[صفحة 14]
س: كم حاصل ضرب خمسة في ستة؟ ج: ثلاثون
[صفحة 16]
س: ما أسباب التغير المناخي؟
'''
        rows=self.extract(source,20)
        self.assertEqual(len(rows),2,rows)
        self.assertEqual([r['sourcePage'] for r in rows],[12,14])
        self.assertNotIn('ما أسباب التغير المناخي؟',[r['q'] for r in rows])

    def test_selection_covers_last_requested_pages(self):
        pages=[{'p':i,'text':('شرح المادة وتعريفات تعليمية. '*160)} for i in range(1,51)]
        pages[-1]['text']='الادخار هو الاحتفاظ بجزء من الدخل لاستخدامه في المستقبل.'
        text,count=self.select({'page_data':__import__('json').dumps(pages,ensure_ascii=False)},1,50,max_chars=400000)
        self.assertEqual(count,50)
        self.assertIn('[صفحة 50]',text)
        self.assertIn('الادخار هو',text)


if __name__=='__main__':
    unittest.main(verbosity=2)
