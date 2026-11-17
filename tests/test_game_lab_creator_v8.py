"""V8 secure authored choices API: explicit distractors and legacy compatibility."""
import unittest,ast,hashlib,random,re
from pathlib import Path
# Use actual server validation and shuffle functions without initializing
# unrelated platform tables at module import.
source=Path(__file__).resolve().parents[1]/'game_lab_api.py'
tree=ast.parse(source.read_text(encoding='utf-8'))
names={'validate_payload','question_state','expected_answer'}
consts={'MAX_ROWS','MODES','TEXT_MODES'}
symbols={'hashlib':hashlib,'random':random,'re':re}
for node in tree.body:
 if isinstance(node,ast.Assign):
  for target in node.targets:
   if isinstance(target,ast.Name) and target.id in consts:
    symbols[target.id]=ast.literal_eval(node.value)
functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
exec(compile(ast.Module(body=functions,type_ignores=[]),str(source),'exec'),symbols)
class Target:
 validate_payload=staticmethod(symbols['validate_payload'])
 question_state=staticmethod(symbols['question_state'])
 expected_answer=staticmethod(symbols['expected_answer'])
 MODES=symbols['MODES']
m=Target

class AuthoredChoices(unittest.TestCase):
 def sample(self,mode='quiz'):
  return {'title':'تجربة خيارات المعلم','subject':'المهارات الرقمية','grade':'السابع','mode':mode,'rows':[
   {'q':'السؤال '+str(i),'a':'الإجابة '+str(i),'g':'عام'} for i in range(4)]}
 def test_custom_options_are_saved_and_shuffled_without_leaking_key(self):
  data=self.sample()
  data['rows'][0]['choices']=['بديل غير صحيح أ','الإجابة 0','بديل غير صحيح ب','بديل غير صحيح ج']
  p=m.validate_payload(data)
  self.assertEqual(len(p['rows'][0]['choices']),4)
  state={'rows':p['rows'],'index':0,'mode':'quiz','duration':25,'score':0}
  q=m.question_state(state,'stable-test-hash')
  self.assertCountEqual(q['choices'],data['rows'][0]['choices'])
  self.assertNotIn('correctAnswer',q)
  self.assertEqual(m.expected_answer(state,'stable-test-hash'),'الإجابة 0')
 def test_legacy_options_still_derive_from_other_answers(self):
  data=m.validate_payload(self.sample())
  q=m.question_state({'rows':data['rows'],'index':1,'mode':'quiz','duration':25,'score':0},'stable-hash')
  self.assertEqual(set(q['choices']),{'الإجابة 0','الإجابة 1','الإجابة 2','الإجابة 3'})
 def test_rejects_duplicate_and_missing_correct(self):
  for choices in (
   ['الإجابة 0','الإجابة 0'],
   ['بديل','بديل آخر'],
   ['الإجابة 0',''],
   ['الإجابة 0']*5,
   'خيار واحد',
  ):
   with self.subTest(choices=choices):
    obj=self.sample()
    obj['rows'][0]['choices']=choices
    with self.assertRaises(ValueError):m.validate_payload(obj)
 def test_all_24_existing_modes_remain_supported(self):
  self.assertEqual(len(m.MODES),24)
  for mode in m.MODES:
   p=m.validate_payload(self.sample(mode))
   self.assertEqual(p['mode'],mode)

if __name__=='__main__':unittest.main(verbosity=2)
