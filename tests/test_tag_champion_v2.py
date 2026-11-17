"""CHAMPION TAG V2: same question, different stable options and full-height UI.
No hosted database or login accounts required.
"""
import ast
import random
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def question_helpers():
    tree=ast.parse((ROOT/'server.py').read_text(encoding='utf-8'))
    selected=[node for node in tree.body
              if isinstance(node,ast.FunctionDef) and
              node.name in ('player_question_index','public_question_for_player','canonical_answer')]
    assert len(selected)==3, 'The existing question contract changed unexpectedly.'
    scope={'random':random}
    exec(compile(ast.Module(body=selected,type_ignores=[]),'server.py','exec'),scope)
    return scope


class ChampionQuestionContract(unittest.TestCase):
    def setUp(self):
        self.logic=question_helpers()
        self.room={
            'code':'682314',
            'variantMode':'options',
            'championId':'tournament-1',
            'quiz':{'questions':[{
                'id':'q1','text':'ما المقصود بتقنيات المعلومات؟',
                'type':'single','time':20,'points':1000,
                'image':'/assets/backgrounds/sample.svg',
                'options':['خيار أول','خيار ثان','خيار ثالث','خيار رابع'],
                'correct':[2]
            }]}
        }
        self.first={'id':'p1','championSeat':0,'optionMaps':{}}
        self.second={'id':'p2','championSeat':1,'optionMaps':{}}

    def test_same_question_and_different_option_order(self):
        get=self.logic['public_question_for_player']
        q1=get(self.room,self.first,0)
        q2=get(self.room,self.second,0)
        self.assertEqual(q1['text'],q2['text'])
        self.assertEqual(q1['image'],q2['image'])
        self.assertEqual(q1['_questionIndex'],q2['_questionIndex'])
        self.assertNotEqual(q1['options'],q2['options'])
        self.assertEqual(q1['options'],get(self.room,self.first,0)['options'])
        self.assertEqual(q2['options'],get(self.room,self.second,0)['options'])
        self.assertCountEqual(q1['options'],self.room['quiz']['questions'][0]['options'])

    def test_correct_answers_survive_permutations(self):
        get=self.logic['public_question_for_player']
        canonical=self.logic['canonical_answer']
        for competitor in (self.first,self.second):
            with self.subTest(competitor=competitor['id']):
                q=get(self.room,competitor,0)
                correct_visible=q['options'].index('خيار ثالث')
                question_index,original,index=canonical(self.room,competitor,0,correct_visible)
                self.assertEqual(question_index,0)
                self.assertEqual(index,2)
                self.assertEqual(original['correct'],[2])

    def test_multiple_correct_options_remap(self):
        q=self.room['quiz']['questions'][0]
        q.update(type='multi',correct=[0,2])
        get=self.logic['public_question_for_player']
        canonical=self.logic['canonical_answer']
        for competitor in (self.first,self.second):
            opts=get(self.room,competitor,0)['options']
            selected=[opts.index('خيار أول'),opts.index('خيار ثالث')]
            _,_,answers=canonical(self.room,competitor,0,selected)
            self.assertEqual(sorted(answers),[0,2])

    def test_other_game_rooms_not_given_special_seating(self):
        regular=dict(self.room)
        regular.pop('championId')
        player={'id':'ordinary','optionMaps':{}}
        q=self.logic['public_question_for_player'](regular,player,0)
        self.assertEqual(q['text'],self.room['quiz']['questions'][0]['text'])
        self.assertEqual(set(player['optionMaps']),{'0'})


class ChampionResponsiveUI(unittest.TestCase):
    def test_worldcup_hero_and_real_metrics(self):
        html=(ROOT/'champion.html').read_text(encoding='utf-8')
        app=(ROOT/'champion-tag.js').read_text(encoding='utf-8')
        self.assertIn('champion-worldcup-v2.css?v=2.0',html)
        self.assertIn('wc-worldcup-hero',html)
        for metric in ('wcParticipants','wcFixtures','wcProgress','wcChampion'):
            self.assertIn('id="'+metric+'"',html)
            self.assertIn("'"+metric+"'",app)
        for action in ('create','archive','bracket'):
            self.assertIn('data-champion-jump="'+action+'"',html)
        self.assertEqual(app.count('const entrants='),1)

    def test_student_and_stage_only_scoped_to_championships(self):
        css=(ROOT/'champion-live-v2.css').read_text(encoding='utf-8')
        for token in ('data-champion="true"','data-bo-question="live"',
                      'data-stage-view="question"',
                      'height:100dvh','grid-template-columns:repeat(2,minmax(0,1fr))'):
            self.assertIn(token,css)
        for file in ('student.html','stage.html'):
            self.assertIn('champion-live-v2.css?v=2.0',
                          (ROOT/file).read_text(encoding='utf-8'))
        student=(ROOT/'student.js').read_text(encoding='utf-8')
        stage=(ROOT/'stage.js').read_text(encoding='utf-8')
        for text in (student,stage):
            self.assertIn('dataset.champion',text)
            self.assertIn('championMode',text)
        self.assertIn('wc-stage-versus',stage)
        self.assertIn('wc-question-stage-label',student)

    def test_backend_status_flags_without_secrets(self):
        server=(ROOT/'server.py').read_text(encoding='utf-8')
        self.assertIn("'championSeat':(len(room['players'])",server)
        self.assertIn("'championMode':bool(room.get('championId'))",server)
        self.assertIn("variantMode='options'",server)
        self.assertIn("shift=int(p.get('championSeat',0))%len(order)",server)
        self.assertIn('maps[key]=order',server)


if __name__=='__main__':unittest.main()
