"""Contract checks for source-grounded textbook -> editable TAG quiz."""
import unittest
from pathlib import Path
from game_lab_ai_quality import verify_ai_rows
ROOT=Path(__file__).resolve().parents[1]
def read(name):return (ROOT/name).read_text(encoding='utf-8')

class BookToQuizContract(unittest.TestCase):
 def test_studio_integrated_without_new_auth_or_auto_publish(self):
  page=read('studio.html')
  auth=read('studio-auth.js')
  builder=read('app.js')
  client=read('tag-studio-book-ai-v1.js')
  for name in ('tagBookFile','tagBookSelect','tagBookGrade','tagBookStart','tagBookEnd',
               'tagBookAi','tagBookExtract','tagBookAiConsent','tagBookResults','tagBookApply'):
   self.assertIn('id="'+name+'"',page,name)
  self.assertIn("'/tag-studio-book-ai-v1.js?v=1'",auth)
  self.assertIn("script.src='/app.js?v=19.1'",auth)
  self.assertIn('window.TAG_ACCEPT_BOOK_ROWS=',builder)
  self.assertIn("q.reviewStatus='teacher_review_required'",builder)
  self.assertIn("q.sourcePage=Number(row.sourcePage)",builder)
  self.assertIn("q.sourceQuote=String(row.sourceQuote",builder)
  self.assertIn("renderQuestions();go('builder')",builder)
  self.assertNotIn('/api/teacher/snapshot',client)
  self.assertNotIn('/api/room/start',client)
  self.assertNotIn('/api/game-lab/teacher/publish',client)
  self.assertIn("'ai_consent_required'",client)
  self.assertIn("aiEnabled=!!data.aiEnabled",client)
  self.assertIn("max=25",page)
  self.assertIn("40_000_000",client)
  self.assertIn("upload/chunk",client)
  self.assertIn("role=\"status\"",page)
 def test_no_unverified_ai_citations_can_reach_ui(self):
  source=[{'p':4,'text':'الادخار هو تخصيص جزء من الدخل للاستخدام المستقبلي وتحقيق أهداف مالية.'}]
  valid={'q':'ما المقصود بالادخار الشخصي؟','a':'تخصيص جزء من الدخل للاستخدام المستقبلي',
         'g':'المفاهيم المالية','sourcePage':4,
         'sourceQuote':'الادخار هو تخصيص جزء من الدخل للاستخدام المستقبلي وتحقيق أهداف مالية.',
         'questionType':'mcq','difficulty':'easy','choices':[
          'شراء جميع السلع','تخصيص جزء من الدخل للاستخدام المستقبلي','الاقتراض فقط','إنفاق جميع المدخرات']}
  wrong={**valid,'q':'سؤال اخترعته المنصة وليس في المصدر؟',
         'sourceQuote':'هذا الاقتباس غير موجود في الكتاب الذي رفعه المعلم'}
  duplicate={**valid}
  approved=verify_ai_rows([wrong,valid,duplicate],source,12)
  self.assertEqual(len(approved),1)
  self.assertEqual(approved[0]['sourcePage'],4)
  self.assertEqual(approved[0]['choices'][1],valid['a'])
 def test_book_upload_is_teacher_owned_and_provider_consent_required(self):
  pro=read('game_lab_pro.py')
  uploads=read('game_lab_uploads.py')
  quality=read('game_lab_ai_quality.py')
  self.assertIn("if data.get('consent') is not True:raise ValueError('ai_consent_required')",pro)
  self.assertIn("if not key:raise ValueError('ai_not_configured')",pro)
  self.assertIn("result=verify_ai_rows(generated,selected_pages,maximum)",pro)
  self.assertIn("MAX_BOOK_BYTES=40_000_000",uploads)
  self.assertIn("if session['teacher_id']!=tid:",uploads)
  self.assertIn("WHERE id=? AND teacher_id=? AND archived=0",pro)
  self.assertIn("if len(chosen)>max_pages:",quality)
if __name__=='__main__':unittest.main()
