"""Card-authenticated, opt-in solo practice for students. No teacher answers are exposed."""
import hashlib
import json
import secrets
import threading
import time
import uuid

import platform_store as store

GUARD = threading.RLock()
RATE_LOCK = threading.Lock()
RATE = {}
MAX_QUIZ_QUESTIONS = 75
SESSION_LIFETIME = 4 * 3600


def now():
    return int(time.time())


def ensure_schema():
    store.exec_sql(
        'CREATE TABLE IF NOT EXISTS solo_sessions '
        '(token_hash TEXT PRIMARY KEY, teacher_id TEXT NOT NULL, student_id TEXT NOT NULL,'
        'quiz_id TEXT NOT NULL, payload TEXT NOT NULL, updated_at BIGINT NOT NULL)'
    )


def limited(handler, identity):
    """Limit anonymous guessing without blocking a whole classroom on one NAT IP."""
    address = handler.client_address[0]
    key = address + ':' + hashlib.sha256(str(identity).upper().encode()).hexdigest()[:12]
    instant = time.monotonic()
    with RATE_LOCK:
        for k in (address, key):
            limit = 500 if k == address else 30
            window = [t for t in RATE.get(k, []) if instant - t < 600]
            if len(window) >= limit:
                RATE[k] = window
                return True
            RATE[k] = window + [instant]
        if len(RATE) > 5000:
            RATE.clear()
    return False


def find_student(card):
    card = str(card or '').strip()
    if not card or len(card) > 90:
        return None
    return store.query(
        'SELECT id,teacher_id,name,class_name,avatar,xp FROM students '
        'WHERE card_token=? OR card_code=? OR id IN '
        '(SELECT student_id FROM student_card_aliases WHERE alias=?)',
        (card, card.upper(), card.upper())
    )


def published_quiz(teacher_id, quiz_id):
    if not isinstance(quiz_id, str) or len(quiz_id) > 100:
        return None
    for quiz in store.snapshot(teacher_id).get('quizzes', []):
        if (quiz.get('id') == quiz_id and quiz.get('settings', {}).get('publishedSolo') is True
                and isinstance(quiz.get('questions'), list) and quiz['questions']):
            return quiz
    return None


def catalog(teacher_id):
    result = []
    for quiz in store.snapshot(teacher_id).get('quizzes', []):
        if (quiz.get('settings', {}).get('publishedSolo') is True
                and isinstance(quiz.get('questions'), list) and quiz['questions']):
            result.append({
                'id': str(quiz.get('id', ''))[:100],
                'title': str(quiz.get('title', 'اختبار'))[:130],
                'subject': str(quiz.get('subject', 'عام'))[:80],
                'grade': str(quiz.get('grade', ''))[:50],
                'questions': min(len(quiz['questions']), MAX_QUIZ_QUESTIONS)
            })
    return result


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def public_state(state):
    """Only public question fields, never answer keys or the source quiz JSON."""
    import server
    qs = state['quiz']['questions']
    idx = state['index']
    output = {
        'quizTitle': str(state['quiz'].get('title') or 'تحدي فردي')[:130],
        'index': idx,
        'total': len(qs),
        'score': state['score'],
        'correct': state['correct'],
        'name': state['name'],
        'finished': state['finished'],
        'xpGain': state.get('xpGain', 0),
        'xp': state.get('xp', 0)
    }
    if state['finished']:
        output['progress'] = store.xp_progress(state.get('xp', 0))
        return output
    q = qs[idx]
    exposed = server.public_question(q)
    if q.get('type') in ('single', 'multi', 'poll'):
        order = state['optionOrders'][idx]
        exposed['options'] = [q['options'][j] for j in order]
    else:
        # A stable, non-leaking presentation of order/match options.
        if q.get('type') == 'order':
            exposed['items'] = state['itemOrders'][idx]
        if q.get('type') == 'match':
            exposed['rights'] = state['rightOrders'][idx]
    output['question'] = exposed
    output['startedAt'] = state['startedAt']
    return output


def get_session(token):
    if not isinstance(token, str) or len(token) < 40 or len(token) > 128:
        return None
    row = store.query('SELECT payload FROM solo_sessions WHERE token_hash=?', (digest(token),))
    if not row:
        return None
    state = store.jload(row['payload'], {})
    if not state or now() - int(state.get('createdAt', 0)) > SESSION_LIFETIME:
        return None
    return state


def make_session(student, quiz):
    import server
    questions = [q for q in quiz['questions'][:MAX_QUIZ_QUESTIONS]
                 if isinstance(q, dict) and str(q.get('type', '')) in
                 ('single', 'multi', 'tf', 'short', 'estimate', 'order', 'match', 'poll')]
    if not questions:
        raise ValueError('empty_quiz')
    clean = server.prepare_quiz({'id': quiz['id'], 'title': quiz.get('title', 'اختبار'), 'questions': questions,
                                  'settings': {'randomQuestions': bool(quiz.get('settings', {}).get('randomQuestions'))}},
                                 'classic', 'options')
    import random
    option_orders = []
    item_orders = []
    right_orders = []
    for q in clean['questions']:
        values = list(range(len(q.get('options') or [])))
        random.shuffle(values)
        option_orders.append(values)
        items = list(q.get('items') or [])
        random.shuffle(items)
        item_orders.append(items)
        rights = [p.get('right', '') for p in (q.get('pairs') or [])]
        random.shuffle(rights)
        right_orders.append(rights)
    return {
        'teacherId': student['teacher_id'], 'studentId': student['id'],
        'name': student['name'], 'className': student['class_name'], 'avatar': student['avatar'],
        'quiz': clean, 'index': 0, 'correct': 0, 'score': 0, 'answers': [],
        'createdAt': now(), 'startedAt': int(time.time() * 1000), 'finished': False,
        'optionOrders': option_orders, 'itemOrders': item_orders, 'rightOrders': right_orders,
        'xp': student['xp'], 'xpGain': 0
    }


def canonical(state, q, submitted):
    t = q.get('type')
    if t in ('single', 'multi'):
        order = state['optionOrders'][state['index']]
        if t == 'single':
            if type(submitted) is not int or not 0 <= submitted < len(order):
                return None
            return order[submitted]
        if not isinstance(submitted, list) or len(submitted) > len(order):
            return []
        if any(type(x) is not int or x < 0 or x >= len(order) for x in submitted):
            return []
        return [order[x] for x in submitted]
    return submitted


def commit_answer(token, state, submitted, submitted_index):
    """An atomic DB transaction prevents double XP/score when a student resends."""
    import server
    if state['finished']:
        return {'ok': True, 'state': public_state(state), 'duplicate': True}
    idx = state['index']
    if type(submitted_index) is not int or submitted_index != idx:
        return {'ok': False, 'error': 'question_changed', 'state': public_state(state)}
    question = state['quiz']['questions'][idx]
    elapsed = int(time.time() * 1000) - int(state['startedAt'])
    allowed_ms = max(5000, min(300000, int(question.get('time') or 20) * 1000))
    answer = canonical(state, question, submitted)
    # The server clock is authoritative. Late answers never count as correct.
    correct = server.evaluate(question, answer) if elapsed <= allowed_ms + 1500 else False
    points = max(0, min(100000, int(question.get('points') or 0)))
    earned = points if correct is True else 0
    state['score'] += earned
    if correct is True:
        state['correct'] += 1
    state['answers'].append({'index': idx, 'correct': correct, 'earned': earned})
    state['index'] += 1
    state['startedAt'] = int(time.time() * 1000)
    completed = state['index'] >= len(state['quiz']['questions'])
    state['finished'] = completed
    xp_gain = int(state['correct'] * 10 + (10 if completed else 0))
    if completed:
        state['xpGain'] = xp_gain
        state['xp'] = int(state.get('xp', 0)) + xp_gain
    key = digest(token)
    with store.DB_LOCK:
        with store.db_connection() as con:
            cur = con.cursor()
            prior = cur.execute(store.sql('SELECT payload FROM solo_sessions WHERE token_hash=?'), (key,)).fetchone()
            if not prior:
                raise ValueError('invalid_session')
            previous = store.jload(prior[0], {})
            if previous.get('index') != idx or previous.get('finished'):
                return {'ok': False, 'error': 'question_changed', 'state': public_state(previous)}
            cur.execute(store.sql('UPDATE solo_sessions SET payload=?,updated_at=? WHERE token_hash=?'),
                        (store.jdump(state), now(), key))
            if completed:
                total = sum(1 for q in state['quiz']['questions'] if q.get('type') != 'poll')
                percent = round(state['correct'] / total * 100) if total else 100
                cur.execute(store.sql(
                    'INSERT INTO student_attempts(id,teacher_id,student_id,quiz_id,room_code,'
                    'student_name,class_name,avatar,correct_count,question_total,percent,score,answers,created_at) '
                    'VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)'), (
                    uuid.uuid4().hex, state['teacherId'], state['studentId'], state['quiz']['id'],
                    'SOLO-' + key[:16], state['name'], state['className'], state['avatar'],
                    state['correct'], total, percent, state['score'], store.jdump(state['answers']), now()
                ))
                cur.execute(store.sql(
                    'UPDATE students SET xp=xp+?,correct_count=correct_count+?,played_count=played_count+1 '
                    'WHERE id=? AND teacher_id=?'), (xp_gain, state['correct'], state['studentId'], state['teacherId']))
    return {'ok': True, 'correct': correct, 'earned': earned, 'state': public_state(state)}


def handle_post(h, u, data):
    if u.path not in ('/api/student/solo/catalog', '/api/student/solo/start',
                      '/api/student/solo/answer', '/api/student/solo/state'):
        return False
    if not isinstance(data, dict):
        h.send_json({'ok': False, 'error': 'bad_request'}, 400)
        return True
    action = u.path.rsplit('/', 1)[-1]
    try:
        if action in ('catalog', 'start'):
            card = str(data.get('card') or '').strip()
            if limited(h, card):
                h.send_json({'ok': False, 'error': 'rate_limited'}, 429)
                return True
            student = find_student(card)
            if not student:
                h.send_json({'ok': False, 'error': 'invalid_card'}, 403)
                return True
            if action == 'catalog':
                h.send_json({'ok': True, 'student': {
                    'name': student['name'], 'className': student['class_name'],
                    'xp': student['xp'], 'progress': store.xp_progress(student['xp'])},
                    'quizzes': catalog(student['teacher_id'])})
                return True
            quiz = published_quiz(student['teacher_id'], data.get('quizId'))
            if not quiz:
                h.send_json({'ok': False, 'error': 'not_published'}, 404)
                return True
            token = secrets.token_urlsafe(40)
            state = make_session(student, quiz)
            store.exec_sql(
                'INSERT INTO solo_sessions(token_hash,teacher_id,student_id,quiz_id,payload,updated_at) '
                'VALUES(?,?,?,?,?,?)',
                (digest(token), state['teacherId'], state['studentId'], quiz['id'],
                 store.jdump(state), now()))
            h.send_json({'ok': True, 'token': token, 'state': public_state(state)})
            return True
        token = data.get('token')
        with GUARD:
            state = get_session(token)
            if not state:
                h.send_json({'ok': False, 'error': 'invalid_session'}, 401)
                return True
            if action == 'state':
                h.send_json({'ok': True, 'state': public_state(state)})
                return True
            result = commit_answer(token, state, data.get('answer'), data.get('index'))
            h.send_json(result, 409 if not result['ok'] else 200)
            return True
    except (ValueError, TypeError, OverflowError, IndexError, KeyError) as error:
        h.send_json({'ok': False, 'error': 'invalid_request'}, 400)
    except Exception as error:
        h.log_message('solo practice error: %s', type(error).__name__)
        h.send_json({'ok': False, 'error': 'server_error'}, 500)
    return True
