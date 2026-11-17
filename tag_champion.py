"""TAG CHAMPION: teacher-owned single-elimination classroom tournaments.
No changes to existing assessments, student cards, or login schemas.
"""
import copy
import random
import secrets
import time
import uuid

import platform_store as store

MAX_ENTRANTS = 32
MAX_TOURNAMENTS = 80


def ensure_schema():
    with store.DB_LOCK:
        with store.db_connection() as con:
            con.execute("""CREATE TABLE IF NOT EXISTS tag_championships (
                id TEXT PRIMARY KEY, teacher_id TEXT NOT NULL, title TEXT NOT NULL,
                kind TEXT NOT NULL, seed_mode TEXT NOT NULL, quiz_id TEXT NOT NULL,
                quiz_json TEXT NOT NULL, bracket_json TEXT NOT NULL,
                champion TEXT NOT NULL DEFAULT '', created_at BIGINT NOT NULL,
                updated_at BIGINT NOT NULL
            )""")
            con.execute("CREATE INDEX IF NOT EXISTS idx_tag_champion_teacher ON tag_championships (teacher_id,updated_at)")


def seed_positions(size):
    """Balanced FIFA-style seeding so each bye belongs to an occupied branch."""
    positions = [1, 2]
    while len(positions) < size:
        value = 2 * len(positions) + 1
        positions = [item for seed in positions for item in (seed, value-seed)]
    return positions


def generate_bracket(participants, manual_seats=None):
    n = len(participants)
    size = 2
    while size < n:
        size *= 2
    seats = (manual_seats if manual_seats is not None
             else [participants[i - 1] if i <= n else None for i in seed_positions(size)])
    if len(seats) != size:
        raise ValueError('invalid_pairings')
    rounds = []
    match_count = size // 2
    for round_index in range(size.bit_length()-1):
        row = []
        for i in range(match_count):
            a, b = ((seats[i*2], seats[i*2+1]) if round_index == 0 else (None, None))
            row.append({'id': f'r{round_index+1}m{i+1}', 'a': a, 'b': b,
                        'winner': None, 'status': ('ready' if a and b else 'pending'),
                        'code': '', 'hostToken': '', 'stageToken': '',
                        'scores': None, 'startedAt': 0, 'finishedAt': 0})
        rounds.append({'index': round_index, 'matches': row})
        match_count //= 2
    for i, match in enumerate(rounds[0]['matches']):
        if bool(match['a']) != bool(match['b']):
            name = match['a'] or match['b']
            match.update(status='bye', winner=name)
            _advance(rounds, 0, i, name)
    return rounds


def _advance(rounds, round_index, match_index, winner):
    if round_index+1 >= len(rounds):
        return
    next_match = rounds[round_index+1]['matches'][match_index//2]
    field = 'a' if match_index % 2 == 0 else 'b'
    if next_match[field] and next_match[field] != winner:
        raise ValueError('already_advanced')
    next_match[field] = winner
    if next_match['a'] and next_match['b']:
        next_match['status'] = 'ready'


def _owned(teacher_id, tournament_id):
    row=store.query('SELECT * FROM tag_championships WHERE id=? AND teacher_id=?',
                    (str(tournament_id), str(teacher_id)))
    if row is None:
        raise ValueError('tournament_not_found')
    return row


def _read(row, include_quiz=False):
    rounds = store.jload(row['bracket_json'], [])
    item = {'id': row['id'], 'title': row['title'], 'kind': row['kind'],
            'seedMode': row['seed_mode'], 'quizId': row['quiz_id'],
            'quizTitle': store.jload(row['quiz_json'], {}).get('title', ''),
            'rounds': rounds, 'champion': row['champion'],
            'createdAt': row['created_at'], 'updatedAt': row['updated_at']}
    if include_quiz:
        item['quiz'] = store.jload(row['quiz_json'], {})
    return item


def list_owned(teacher_id):
    rows = store.query('SELECT * FROM tag_championships WHERE teacher_id=? ORDER BY updated_at DESC LIMIT 80',
                       (teacher_id,), True)
    return [_read(row) for row in rows]


def detail(teacher_id, tournament_id):
    return _read(_owned(teacher_id, tournament_id))


def create(teacher_id, data):
    title = str(data.get('title') or 'بطولة TAG').strip()[:100]
    kind = data.get('kind')
    mode = data.get('seedMode')
    names = data.get('participants')
    if kind not in ('students', 'classes', 'teams') or mode not in ('random', 'manual'):
        raise ValueError('invalid_tournament_type')
    if not isinstance(names, list) or not 2 <= len(names) <= MAX_ENTRANTS:
        raise ValueError('participants_2_to_32')
    if any(not isinstance(name, str) or not 1 <= len(name.strip()) <= 55 for name in names):
        raise ValueError('invalid_participants')
    names = [name.strip() for name in names]
    if len({name.casefold() for name in names}) != len(names):
        raise ValueError('duplicate_participants')
    quizzes = store.snapshot(teacher_id).get('quizzes') or []
    quiz_id = str(data.get('quizId') or '')
    quiz = next((q for q in quizzes if isinstance(q, dict) and str(q.get('id')) == quiz_id), None)
    if not quiz or not isinstance(quiz.get('questions'), list) or not quiz['questions']:
        raise ValueError('quiz_not_found')
    serialized_quiz = store.jdump(quiz)
    if len(serialized_quiz) > 900000:
        raise ValueError('quiz_too_large')
    if mode == 'random':
        random.SystemRandom().shuffle(names)
        bracket = generate_bracket(names)
    else:
        size=2
        while size<len(names):
            size*=2
        pairs=data.get('manualPairs')
        if not isinstance(pairs,list) or len(pairs)!=size//2:
            raise ValueError('manual_pairings_required')
        seats=[]
        for pair in pairs:
            if not isinstance(pair,list) or len(pair)!=2:
                raise ValueError('invalid_pairings')
            a,b=(str(pair[0] or '').strip(),str(pair[1] or '').strip())
            if not a and not b:
                raise ValueError('empty_fixture')
            seats.extend((a or None,b or None))
        assigned=[name for name in seats if name]
        if len(assigned)!=len(names) or {name.casefold() for name in assigned}!={name.casefold() for name in names}:
            raise ValueError('invalid_pairings')
        bracket=generate_bracket(names, seats)
    now=store.epoch()
    with store.DB_LOCK:
        existing=store.query('SELECT COUNT(*) AS count FROM tag_championships WHERE teacher_id=?',(teacher_id,))
        if existing and existing['count'] >= MAX_TOURNAMENTS:
            raise ValueError('tournament_limit')
        row_id=uuid.uuid4().hex
        store.exec_sql('INSERT INTO tag_championships(id,teacher_id,title,kind,seed_mode,quiz_id,quiz_json,bracket_json,champion,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                       (row_id,teacher_id,title,kind,mode,quiz_id,serialized_quiz,store.jdump(bracket),'',now,now))
    return detail(teacher_id,row_id)


def _match(item, match_id):
    for index,row in enumerate(item['rounds']):
        for pos,match in enumerate(row['matches']):
            if match['id'] == match_id:
                return index,pos,match
    raise ValueError('match_not_found')


def prepare_match(teacher_id, tournament_id, match_id):
    item = _read(_owned(teacher_id,tournament_id), True)
    i,j,match = _match(item, str(match_id))
    if match['status'] != 'ready' or not match['a'] or not match['b']:
        raise ValueError('match_not_ready')
    return item, i, j, match


def attach_match(teacher_id, tournament_id, match_id, room):
    with store.DB_LOCK:
        row=_owned(teacher_id,tournament_id)
        item=_read(row)
        _,_,match=_match(item, match_id)
        if match['status'] != 'ready':
            raise ValueError('match_not_ready')
        match.update(status='live', code=room['code'], hostToken=room['hostToken'],
                     stageToken=room['stageToken'],startedAt=store.epoch())
        store.exec_sql('UPDATE tag_championships SET bracket_json=?,updated_at=? WHERE id=? AND teacher_id=?',
                       (store.jdump(item['rounds']),store.epoch(),tournament_id,teacher_id))
    return item


def complete_match(teacher_id, data, rooms):
    tournament_id=str(data.get('tournamentId') or '')
    match_id=str(data.get('matchId') or '')
    chosen=str(data.get('tieWinner') or '')
    with store.DB_LOCK:
        item=_read(_owned(teacher_id,tournament_id))
        index,pos,match=_match(item,match_id)
        if match['status'] == 'finished':
            return item
        if match['status'] != 'live':
            raise ValueError('match_not_started')
        room=rooms.get(match['code'])
        if not room or room.get('teacherId') != teacher_id or room.get('status') != 'finished' or room.get('championId') != tournament_id or room.get('championMatchId') != match_id:
            raise ValueError('room_not_finished')
        sides=[match['a'], match['b']]
        results=[]
        for side in sides:
            members=[p for p in room['players'].values() if p.get('team') == side]
            if not members:
                raise ValueError('both_teams_required')
            total=sum(int(p.get('score',0)) for p in members)
            correct=sum(int(p.get('correct',0)) for p in members)
            results.append({'name':side,'members':len(members),'points':total,
                            'average':round(total/len(members),2),
                            'correctAverage':round(correct/len(members),3)})
        x,y=results
        left=(x['average'],x['correctAverage'])
        right=(y['average'],y['correctAverage'])
        if left == right:
            if chosen not in sides:
                raise ValueError('tie_requires_decision')
            winner=chosen
        else:
            if chosen:
                raise ValueError('tie_break_not_allowed')
            winner=sides[0] if left>right else sides[1]
        match.update(status='finished',winner=winner,scores=results,
                     finishedAt=store.epoch())
        _advance(item['rounds'],index,pos,winner)
        champion=winner if index == len(item['rounds'])-1 else ''
        store.exec_sql('UPDATE tag_championships SET bracket_json=?,champion=?,updated_at=? WHERE id=? AND teacher_id=?',
                       (store.jdump(item['rounds']),champion,store.epoch(),tournament_id,teacher_id))
    return detail(teacher_id,tournament_id)


def forfeit_match(teacher_id,data):
    tournament_id=str(data.get('tournamentId') or '')
    match_id=str(data.get('matchId') or '')
    winner=str(data.get('winner') or '')
    with store.DB_LOCK:
        item=_read(_owned(teacher_id,tournament_id))
        index,pos,match=_match(item,match_id)
        if match['status']!='ready' or winner not in (match['a'],match['b']):
            raise ValueError('forfeit_not_allowed')
        match.update(status='finished',winner=winner,finishedAt=store.epoch(),
                     scores=None)
        _advance(item['rounds'],index,pos,winner)
        champion=winner if index==len(item['rounds'])-1 else ''
        store.exec_sql('UPDATE tag_championships SET bracket_json=?,champion=?,updated_at=? WHERE id=? AND teacher_id=?',
                       (store.jdump(item['rounds']),champion,store.epoch(),tournament_id,teacher_id))
    return detail(teacher_id,tournament_id)

def public_board(tournament_id):
    """Unlisted view for projection; never expose room tokens or other teacher data."""
    if not isinstance(tournament_id,str) or len(tournament_id)!=32 or any(x not in '0123456789abcdef' for x in tournament_id):
        raise ValueError('tournament_not_found')
    row=store.query('SELECT id,title,kind,bracket_json,champion,created_at,updated_at FROM tag_championships WHERE id=?',
                    (tournament_id,))
    if row is None:
        raise ValueError('tournament_not_found')
    rounds=[]
    for r in store.jload(row['bracket_json'],[]):
        rounds.append({'index':r['index'],
                       'matches':[{'id':m['id'],'a':m['a'],'b':m['b'],'status':m['status'],
                                   'winner':m['winner'],'scores':m.get('scores')}
                                  for m in r['matches']]})
    return {'id':row['id'],'title':row['title'],'kind':row['kind'],
            'champion':row['champion'],'rounds':rounds,'updatedAt':row['updated_at']}
