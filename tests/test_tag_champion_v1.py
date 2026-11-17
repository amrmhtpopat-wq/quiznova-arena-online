"""Regression checks for CHAMPION TAG live elimination tournaments.
Run: python -m unittest tests.test_tag_champion_v1 -v
Uses temporary SQLite only; never touches hosted Neon or real students.
"""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import platform_store as store
import tag_champion as champion

ROOT = Path(__file__).resolve().parents[1]


def fixture(players, result1=1100, result2=700, ties=False):
    a,b=players
    return {'code':'548721','teacherId':'','status':'finished','championId':'','championMatchId':'',
            'players':{'p1':{'id':'p1','name':'طالب أ','team':a,'score':result1,'correct':8},
                       'p2':{'id':'p2','name':'طالب ب','team':b,'score':result1 if ties else result2,'correct':8 if ties else 5}}}


class BracketUnitTests(unittest.TestCase):
    def test_balanced_seeding(self):
        self.assertEqual(champion.seed_positions(2),[1,2])
        self.assertEqual(champion.seed_positions(4),[1,4,2,3])
        self.assertEqual(champion.seed_positions(8),[1,8,4,5,2,7,3,6])

    def test_three_to_thirtytwo_bracket_structure(self):
        for n in range(2,33):
            with self.subTest(n=n):
                names=[f'الفريق {i}' for i in range(n)]
                rounds=champion.generate_bracket(names)
                size=2
                while size<n:size*=2
                self.assertEqual(len(rounds),size.bit_length()-1)
                self.assertEqual(sum(len(row['matches']) for row in rounds),size-1)
                self.assertEqual(sum(m['status']=='bye' for m in rounds[0]['matches']),size-n)
                self.assertFalse(any(not m['a'] and not m['b'] for m in rounds[0]['matches']))

    def test_manual_fixtures(self):
        n=['الأول','الثاني','الثالث','الرابع']
        rounds=champion.generate_bracket(n,['الأول','الرابع','الثالث','الثاني'])
        self.assertEqual([(m['a'],m['b']) for m in rounds[0]['matches']],
                         [('الأول','الرابع'),('الثالث','الثاني')])


class StoredTournamentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db_path=str(Path(self.tmp.name)/'champion.db')
        self.patch_url=patch.object(store,'DATABASE_URL','')
        self.patch_db=patch.object(store,'LOCAL_DB',self.db_path)
        self.patch_url.start();self.patch_db.start()
        store.init();champion.ensure_schema()
        user=store.create_teacher('test.champion@example.test','Secret_2026_ABC','معلم الاختبار','المدرسة التجريبية','المهارات الرقمية')
        self.teacher_id=user['teacher']['id']
        quiz={'id':'quiz-001','title':'اختبار مهارات الحاسوب','subject':'المهارات الرقمية',
              'questions':[{'id':'q1','text':'ما الإجابة الصحيحة؟','type':'single',
                            'options':['الأولى','الثانية'],'correct':[0],'time':20,'points':1000}]}
        store.save_snapshot(self.teacher_id,{'quizzes':[quiz]})

    def tearDown(self):
        self.patch_db.stop();self.patch_url.stop();self.tmp.cleanup()

    def create(self, names, mode='random', pairs=None, kind='students'):
        payload={'title':'دوري الفصل الدراسي','kind':kind,'seedMode':mode,
                 'participants':names,'quizId':'quiz-001'}
        if pairs is not None:payload['manualPairs']=pairs
        return champion.create(self.teacher_id,payload)

    def test_persistent_manual_and_isolation(self):
        tournament=self.create(['أحمد','خالد','يوسف','عمر'],mode='manual',
                               pairs=[['أحمد','خالد'],['يوسف','عمر']])
        tid=tournament['id']
        self.assertEqual(champion.detail(self.teacher_id,tid)['rounds'][0]['matches'][0]['a'],'أحمد')
        self.assertEqual(len(champion.list_owned(self.teacher_id)),1)
        with self.assertRaisesRegex(ValueError,'tournament_not_found'):
            champion.detail('another-teacher-id',tid)
        public=champion.public_board(tid)
        self.assertNotIn('hostToken',str(public))
        self.assertNotIn('stageToken',str(public))

    def test_automatic_advancement_and_champion(self):
        tour=self.create(['أحمد','خالد'],mode='manual',pairs=[['أحمد','خالد']])
        tid=tour['id']
        tournament,i,j,m=champion.prepare_match(self.teacher_id,tid,'r1m1')
        room=fixture(['أحمد','خالد'])
        room.update(teacherId=self.teacher_id,championId=tid,championMatchId='r1m1',
                    hostToken='host123',stageToken='stage123')
        champion.attach_match(self.teacher_id,tid,'r1m1',room)
        result=champion.complete_match(self.teacher_id,{'tournamentId':tid,'matchId':'r1m1'},{room['code']:room})
        self.assertEqual(result['champion'],'أحمد')
        self.assertEqual(result['rounds'][0]['matches'][0]['winner'],'أحمد')
        with self.assertRaisesRegex(ValueError,'tournament_not_found'):
            champion.prepare_match('other',tid,'r1m1')

    def test_tie_requires_teacher_resolution(self):
        tour=self.create(['أحمد','خالد'],mode='manual',pairs=[['أحمد','خالد']])
        room=fixture(['أحمد','خالد'],ties=True)
        room.update(teacherId=self.teacher_id,championId=tour['id'],championMatchId='r1m1',
                    hostToken='host',stageToken='stage')
        champion.attach_match(self.teacher_id,tour['id'],'r1m1',room)
        with self.assertRaisesRegex(ValueError,'tie_requires_decision'):
            champion.complete_match(self.teacher_id,{'tournamentId':tour['id'],'matchId':'r1m1'},
                                    {room['code']:room})
        winner=champion.complete_match(self.teacher_id,{'tournamentId':tour['id'],'matchId':'r1m1','tieWinner':'خالد'},
                                       {room['code']:room})
        self.assertEqual(winner['champion'],'خالد')

    def test_manual_pairing_rejects_duplicates(self):
        with self.assertRaisesRegex(ValueError,'invalid_pairings'):
            self.create(['أحمد','خالد','يوسف','عمر'],'manual',
                        [['أحمد','أحمد'],['يوسف','عمر']])
        with self.assertRaisesRegex(ValueError,'duplicate_participants'):
            self.create(['خالد','خالد'],'random')
        with self.assertRaisesRegex(ValueError,'quiz_not_found'):
            champion.create(self.teacher_id,{'title':'بدون اختبار','kind':'students','seedMode':'random',
                'participants':['أحمد','خالد'],'quizId':'missing'})

    def test_valid_forfeit_moves_winner(self):
        tour=self.create(['أحمد','خالد','يوسف','عمر'],'manual',
                         [['أحمد','خالد'],['يوسف','عمر']])
        result=champion.forfeit_match(self.teacher_id,{'tournamentId':tour['id'],
                                                       'matchId':'r1m1','winner':'خالد'})
        self.assertEqual(result['rounds'][1]['matches'][0]['a'],'خالد')
        self.assertEqual(result['rounds'][0]['matches'][0]['status'],'finished')


class StaticIntegrationTests(unittest.TestCase):
    def test_pages_and_entry(self):
        portal=(ROOT/'index.html').read_text(encoding='utf-8')
        studio=(ROOT/'studio.html').read_text(encoding='utf-8')
        self.assertIn('href="/champion.html"',portal)
        self.assertIn('href="/champion.html"',studio)
        self.assertIn('champion-tag.js',(ROOT/'champion.html').read_text(encoding='utf-8'))
        self.assertIn('champion-board.js',(ROOT/'champion-board.html').read_text(encoding='utf-8'))
        self.assertIn('CHAMPION TAG',(ROOT/'champion.html').read_text(encoding='utf-8'))
        server=(ROOT/'server.py').read_text(encoding='utf-8')
        for endpoint in ('/api/champion/public','/api/champion/match/start','/api/champion/match/complete',
                         '/api/champion/match/forfeit'):
            self.assertIn(endpoint,server)
    def test_public_board_has_no_controls(self):
        js=(ROOT/'champion-board.js').read_text(encoding='utf-8')
        self.assertIn('/api/champion/public',js)
        self.assertNotIn('/api/room/control',js)
        self.assertNotIn('hostToken',js)


if __name__=='__main__':unittest.main()
