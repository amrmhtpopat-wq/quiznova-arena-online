"""TAG AI Book Engine V2: pure planning, independent audit and bounded orchestration.

These tests never use external Gemini calls, real students or production data.
"""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# The existing platform security module requires initialized teacher tables.
# Isolate this contract test from production and initialize the local schema.
_test_db=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(_test_db.name)/'ai-v2.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store
store.init()
from game_lab_ai_v2 import (
 page_segments,plan_batches,is_near_duplicate,review_verified_rows,
 distribute_by_pages,choose_repair_pages,report_coverage
)
import game_lab_pro as pro

PAGES=[{'p':i,'text':(
 'الدرس في الصفحة '+str(i)+': يشرح هذا النص المفاهيم الأساسية في الدراسة '
 'ويقدم تطبيقات مناسبة للطلبة ويعطي أمثلة مختلفة على استخدامها. ')*8}
 for i in range(1,26)]
BOOK={'id':'teacher-book-1','name':'كتاب تدريب.pdf','kind':'pdf','page_count':25,
      'section':'دروس التجربة','created_at':1,'page_data':'[]'}

def sample(i, page):
 return {'q':f'كيف نفهم مفهوم القيمة رقم {page} في المثال {i} من الدرس؟',
         'a':f'القيمة الصحيحة رقم {page}-{i}',
         'g':'درس القيم','sourcePage':page,'sourceQuote':PAGES[page-1]['text'][:110],
         'questionType':'mcq','difficulty':'medium','origin':'ai',
         'choices':['الخيار الأول','الخيار الثاني',f'القيمة الصحيحة رقم {page}-{i}','الخيار الرابع']}

class BookEngineV2Test(unittest.TestCase):
 def test_section_planning_covers_pages_without_extra_requests(self):
  sections=page_segments(PAGES)
  self.assertEqual(len(sections),7)
  self.assertEqual([p for block in sections for p in block['pages']],list(range(1,26)))
  batches=plan_batches(PAGES,20)
  self.assertEqual(len(batches),2)
  self.assertEqual([p for block in batches for p in block['pages']],list(range(1,26)))
  self.assertEqual(batches[0]['startPage'],1)
  self.assertEqual(batches[1]['endPage'],25)
  self.assertTrue(all(b['target']<=25 for b in batches))
  self.assertEqual(len(plan_batches(PAGES[:5],6)),1)
 def test_quality_rejects_repeats_and_weak_answer_choices(self):
  valid=sample(1,1)
  duplicate=dict(valid)
  invalid={**sample(2,2),'choices':['الخيار الأول','كل ما سبق','الخيار الثالث','القيمة الصحيحة رقم 2-2']}
  rows,reasons=review_verified_rows([valid,duplicate,invalid],limit=10)
  self.assertEqual(len(rows),1)
  self.assertGreaterEqual(reasons['duplicate'],1)
  self.assertGreaterEqual(reasons['options'],1)
  self.assertTrue(rows[0]['sourceQuoteVerified'])
  self.assertEqual(rows[0]['reviewStatus'],'teacher_review_required')
  self.assertTrue(is_near_duplicate(valid['q'],duplicate['q']))
 def test_coverage_and_page_balance(self):
  rows=[sample(i,1) for i in range(4)]+[sample(9,5),sample(8,8)]
  result=distribute_by_pages(rows,4)
  self.assertEqual([x['sourcePage'] for x in result],[1,5,8,1])
  coverage=report_coverage(result,PAGES[:10])
  self.assertEqual(coverage['coveredPages'],3)
  self.assertEqual(coverage['extractablePages'],10)
 def test_retry_page_selection_prioritizes_uncovered(self):
  repair=choose_repair_pages(PAGES[:12],[sample(1,1),sample(2,2)])
  self.assertIsNotNone(repair)
  self.assertGreaterEqual(repair[0],3)
  self.assertLessEqual(repair[1]-repair[0],5)
 def test_orchestration_respects_call_budget_and_returns_provenance(self):
  seen=[]
  def fake_generate(_tid,settings):
   page=int(settings['startPage'])
   seen.append((page,settings['endPage'],settings['count']))
   results=[sample(i,page) for i in range(1,9)]
   return {'rows':results,'count':len(results),'proposedCount':len(results),'discardedCount':0}
  source=[p for p in PAGES[:18]]
  with (patch.object(pro,'require_book',return_value=BOOK),
        patch.object(pro,'selected_ai_source',return_value=('text',source)),
        patch.dict(os.environ,{'GEMINI_API_KEY':'mock-key'}),
        patch.object(pro,'ai_generate',side_effect=fake_generate)):
   result=pro.ai_generate_v2('teacher1',{
    'bookId':BOOK['id'],'startPage':1,'endPage':18,'count':12,'consent':True})
  self.assertLessEqual(len(seen),3)
  self.assertEqual(len(seen),2)
  self.assertLessEqual(result['count'],12)
  self.assertTrue(all(row['reviewStatus']=='teacher_review_required' for row in result['rows']))
  self.assertEqual(result['generationStats']['providerCalls'],2)
  self.assertEqual(result['generationStats']['sections'],6)
  self.assertTrue(result['generationStats']['coverage']['coveredPages']>=1)
 def test_one_question_retry_is_bound_to_source_and_excludes_previous(self):
  seen=[]
  def fake_generate(_tid,settings):
   seen.append(settings)
   return {'rows':[sample(17,3)],'count':1,'proposedCount':1,'discardedCount':0}
  with (patch.object(pro,'require_book',return_value=BOOK),
        patch.object(pro,'selected_ai_source',return_value=('text',PAGES[:8])),
        patch.dict(os.environ,{'GEMINI_API_KEY':'mock-key'}),
        patch.object(pro,'ai_generate',side_effect=fake_generate)):
   out=pro.ai_generate_v2('t',{'bookId':BOOK['id'],'consent':True,
       'startPage':1,'endPage':8,'count':12,'retryPage':3,
       'retryQuestion':'ما معنى أحد المصطلحات السابقة؟'})
  self.assertEqual(len(seen),1)
  self.assertEqual(seen[0]['startPage'],3)
  self.assertEqual(seen[0]['endPage'],3)
  self.assertIn('ما معنى أحد المصطلحات السابقة؟',seen[0]['excludeQuestions'])
  self.assertEqual(out['count'],1)
  self.assertEqual(out['rows'][0]['sourcePage'],3)
 def test_consent_and_provider_checks_happen_before_generation(self):
  with (patch.object(pro,'require_book',return_value=BOOK),
        patch.dict(os.environ,{'GEMINI_API_KEY':'mock-key'}),
        patch.object(pro,'ai_generate') as mock):
   with self.assertRaisesRegex(ValueError,'ai_consent_required'):
    pro.ai_generate_v2('t',{'bookId':BOOK['id'],'consent':False})
   mock.assert_not_called()
  with (patch.object(pro,'require_book',return_value=BOOK),
        patch.dict(os.environ,{'GEMINI_API_KEY':''}),
        patch.object(pro,'ai_generate') as mock):
   with self.assertRaisesRegex(ValueError,'ai_not_configured'):
    pro.ai_generate_v2('t',{'bookId':BOOK['id'],'consent':True})
   mock.assert_not_called()
 def test_browser_contract_and_pwa_cache_versions(self):
  html=Path('studio.html').read_text(encoding='utf-8')
  script=Path('tag-studio-book-ai-v1.js').read_text(encoding='utf-8')
  server=Path('game_lab_pro.py').read_text(encoding='utf-8')
  self.assertIn('id="tagBookQuestionMix"',html)
  self.assertIn('id="tagBookEngineStats"',html)
  self.assertIn('studio-auth.js?v=13.4',html)
  self.assertIn('/api/game-lab/pro/books/ai/retry',server)
  self.assertIn('ai_generate_v2(tid,data)',server)
  self.assertIn('tag-book-retry',script)
  self.assertIn('generationStats',script)
  self.assertIn('tagBookQuestionMix',script)
  self.assertNotIn('/api/room/start',script)

if __name__=='__main__':unittest.main()
