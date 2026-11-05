"""Card-authenticated solo practice: public catalog, server-only answer keys, persistent XP."""
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import uuid
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TEMP = tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL', None)
os.environ['QUIZNOVA_SQLITE_PATH'] = str(Path(TEMP.name) / 'solo-v120.sqlite')
os.environ['QUIZNOVA_CLOUD'] = '1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL'] = 'yes'

import platform_store as store
import server

server_instance = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
threading.Thread(target=server_instance.serve_forever, daemon=True).start()
BASE = 'http://127.0.0.1:' + str(server_instance.server_port)


def post(action, payload):
    request = urllib.request.Request(
        BASE + '/api/student/solo/' + action,
        data=json.dumps(payload, ensure_ascii=False).encode('utf8'),
        headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, json.load(exc)


class StudentSoloContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.teacher = store.create_teacher(
            'solo-teacher-' + uuid.uuid4().hex + '@school.example', 'SuperSecurePassword123!',
            'Teacher Solo', 'مدرسة تجريبية للبنين', 'المهارات الرقمية', 'boys')
        cls.tid = cls.teacher['teacher']['id']
        created = store.add_students(cls.tid, [
            {'name': 'طالب التدريب', 'className': 'التاسع أ', 'avatar': 'm01'}])
        cls.card = created[0]['cardCode']
        cls.student_id = created[0]['id']
        cls.questions = [
            {'id': 's1', 'type': 'single', 'text': 'ما وظيفة CPU؟', 'time': 120,
             'points': 1000, 'options': ['حفظ مؤقت', 'تنفيذ التعليمات', 'طباعة المستندات', 'تشغيل الصوت'],
             'correct': [1]},
            {'id': 's2', 'type': 'tf', 'text': 'RAM ذاكرة مؤقتة', 'time': 120,
             'points': 1500, 'correct': True}]
        cls.quiz = {'id': 'published-practice', 'title': 'مهارات الحاسوب',
                    'grade': 'التاسع', 'subject': 'مهارات رقمية',
                    'settings': {'randomQuestions': False, 'publishedSolo': False},
                    'questions': cls.questions}
        store.save_snapshot(cls.tid, {'quizzes': [cls.quiz]})

    def test_unpublished_is_private_and_only_own_card_can_access(self):
        status, data = post('catalog', {'card': self.card})
        self.assertEqual(status, 200)
        self.assertEqual(data['quizzes'], [])
        self.assertEqual(data['student']['name'], 'طالب التدريب')
        status, data = post('start', {'card': self.card, 'quizId': self.quiz['id']})
        self.assertEqual(status, 404)
        self.assertEqual(data['error'], 'not_published')
        status, data = post('catalog', {'card': 'NOT-A-REAL-CARD'})
        self.assertEqual(status, 403)
        self.assertEqual(data['error'], 'invalid_card')

    def test_solo_published_answers_never_exposed_and_xp_idempotent(self):
        q = json.loads(json.dumps(self.quiz, ensure_ascii=False))
        q['settings']['publishedSolo'] = True
        store.save_snapshot(self.tid, {'quizzes': [q]})
        status, catalog = post('catalog', {'card': self.card})
        self.assertEqual(status, 200)
        self.assertEqual(len(catalog['quizzes']), 1)
        self.assertNotIn('correct', catalog['quizzes'][0])
        status, started = post('start', {'card': self.card, 'quizId': q['id']})
        self.assertEqual(status, 200)
        token = started['token']
        self.assertGreater(len(token), 40)
        first = started['state']['question']
        self.assertEqual(first['type'], 'single')
        self.assertNotIn('correct', first)
        self.assertNotIn('answers', first)
        self.assertNotIn('quiz', started['state'])
        selected = first['options'].index('تنفيذ التعليمات')
        status, a1 = post('answer', {'token': token, 'index': 0, 'answer': selected})
        self.assertEqual(status, 200)
        self.assertTrue(a1['correct'])
        self.assertEqual(a1['earned'], 1000)
        status, stale = post('answer', {'token': token, 'index': 0, 'answer': selected})
        self.assertEqual(status, 409)
        self.assertEqual(stale['error'], 'question_changed')
        status, resumed = post('state', {'token': token})
        self.assertEqual(status, 200)
        self.assertEqual(resumed['state']['index'], 1)
        self.assertNotIn('correct', resumed['state']['question'])
        status, a2 = post('answer', {'token': token, 'index': 1, 'answer': True})
        self.assertEqual(status, 200)
        self.assertTrue(a2['state']['finished'])
        self.assertEqual(a2['state']['score'], 2500)
        self.assertEqual(a2['state']['xpGain'], 30)
        status, repeat = post('answer', {'token': token, 'index': 1, 'answer': True})
        self.assertEqual(status, 200)
        self.assertTrue(repeat['duplicate'])
        record = store.query('SELECT xp,played_count,correct_count FROM students WHERE id=?', (self.student_id,))
        self.assertEqual(record['xp'], 30)
        self.assertEqual(record['played_count'], 1)
        self.assertEqual(record['correct_count'], 2)
        attempts = store.query('SELECT COUNT(*) AS n FROM student_attempts WHERE student_id=? AND quiz_id=?',
                               (self.student_id, q['id']))
        self.assertEqual(attempts['n'], 1)
        status, resumed = post('state', {'token': token})
        self.assertEqual(resumed['state']['xp'], 30)
        self.assertTrue(resumed['state']['finished'])


if __name__ == '__main__':
    unittest.main()
