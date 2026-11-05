"""BOOYAH progression contract: short unique cards, explicit XP tiers and fair bonuses."""
import re
import unittest
import platform_store as store


class BooyahProgressTests(unittest.TestCase):
    def test_short_card_code_is_random_and_easy_to_enter(self):
        codes=[store.new_card_code() for _ in range(600)]
        self.assertEqual(len(codes),len(set(codes)))
        self.assertTrue(all(re.fullmatch(r'[A-HJ-NP-Z2-9]{4}-[A-HJ-NP-Z2-9]{4}', c) for c in codes))

    def test_level_boundaries_and_progress(self):
        cases=[(0,1,100),(99,1,1),(100,2,150),(249,2,1),
               (250,3,200),(449,3,1),(450,4,250),
               (699,4,1),(700,5,300),(999,5,1),(1000,6,350)]
        for xp,level,remaining in cases:
            with self.subTest(xp=xp):
                result=store.xp_progress(xp)
                self.assertEqual(result['level'],level)
                self.assertEqual(result['xpToNext'],remaining)
                self.assertGreaterEqual(result['percent'],0)
                self.assertLessEqual(result['percent'],100)
        self.assertEqual(store.xp_progress(0)['title'],'مبتدئ')
        self.assertEqual(store.xp_progress(700)['title'],'نجم الشعبة')
        self.assertEqual(store.xp_progress(1000)['title'],'أسطورة بويا')

    def test_correct_fast_completion_and_first_place_xp(self):
        def answer(correct,elapsed,index):
            return {'correct':correct,'elapsedMs':elapsed,'questionIndex':index}
        room={'quiz':{'questions':[{'id':'a'},{'id':'b'}]},'players':{
            'a':{'id':'a','score':2000,'correct':2,'answers':{
                '0':answer(True,200,0),'1':answer(True,400,1)}},
            'b':{'id':'b','score':1000,'correct':1,'answers':{
                '0':answer(True,300,0),'1':answer(False,600,1)}},
            'c':{'id':'c','score':0,'correct':0,'answers':{
                '0':answer(False,100,0),'1':answer(False,100,1)}}
        }}
        awards=store.room_xp_awards(room)
        self.assertEqual(awards['a'],{'correct':20,'fastest':10,'completion':10,'firstPlace':20,'total':60})
        self.assertEqual(awards['b'],{'correct':10,'fastest':5,'completion':10,'firstPlace':0,'total':25})
        self.assertEqual(awards['c']['total'],10)
        self.assertEqual(store.xp_gain_for_attempt(1000,3),30)


if __name__=='__main__':
    unittest.main()
