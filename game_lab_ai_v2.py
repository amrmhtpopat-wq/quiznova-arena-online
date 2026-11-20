"""TAG AI Book Engine V2 — bounded textbook segmentation and evidence quality.

All content is untrusted teacher-uploaded data. This module has no external
network calls, no database writes, and makes no claims of curriculum approval.
Model outputs MUST pass the pre-existing literal source-quote verifier first.
"""
from __future__ import annotations
import math
import re
from collections import Counter
from game_lab_ai_quality import _plain

# One teacher action uses at most 2 generation calls, plus one optional repair
# when provider time allows. Each call consumes an existing per-teacher quota.
MAX_GENERATION_BATCHES = 2
MAX_TOTAL_CALLS = 3
PAGES_PER_SECTION = 4

_STOP = {'ما','هو','هي','من','في','على','الى','إلى','عن','هل','لماذا',
         'كيف','متى','اختر','أي','اي','الذي','التي','الآتي','التالية',
         'يأتي','مما','يلي','من','خلال','يكون','تكون','مع','يمكن',
         'السؤال','الصحيحة','الصحيح','منها','هناك','هذا','هذه'}


def page_segments(pages, section_size=PAGES_PER_SECTION):
    """Consecutive nonempty source pages, independently inspectable in UI."""
    selected = [p for p in pages if str(p.get('text') or '').strip()]
    section_size = max(1, min(5, int(section_size)))
    segments = []
    for offset in range(0, len(selected), section_size):
        block = selected[offset:offset + section_size]
        text = '\n'.join(str(p.get('text') or '')[:6500] for p in block)
        segments.append({
            'first': int(block[0]['p']),
            'last': int(block[-1]['p']),
            'pages': [int(p['p']) for p in block],
            'chars': len(text),
        })
    return segments


def plan_batches(pages, requested):
    """Split a book selection into up to two bounded, contiguous model calls.

    Each call also receives 3-5-page segment instructions. It never requests
    pages outside those selected by the authenticated teacher.
    """
    available = [p for p in pages if str(p.get('text') or '').strip()]
    if not available:
        return []
    count = min(25, max(1, int(requested)))
    calls = 2 if len(available) >= 7 and count >= 8 else 1
    midpoint = math.ceil(len(available) / calls)
    batches = []
    for offset in range(0, len(available), midpoint):
        group = available[offset:offset + midpoint]
        if not group:
            continue
        proportion = len(group) / len(available)
        # Slight oversampling compensates for factual/format verification
        # rejection without uncontrolled provider requests.
        target = min(25, max(4, int(math.ceil(count * proportion * 1.18))))
        batches.append({
            'startPage': int(group[0]['p']),
            'endPage': int(group[-1]['p']),
            'target': target,
            'sections': page_segments(group),
            'pages': [int(p['p']) for p in group],
        })
    return batches[:MAX_GENERATION_BATCHES]


def _keywords(text):
    return {t for t in _plain(text).split() if len(t) > 2 and t not in _STOP}


def is_near_duplicate(first, second):
    """Conservative semantic-overlap guard beyond exact string duplicates."""
    if _plain(first) == _plain(second):
        return True
    left, right = _keywords(first), _keywords(second)
    if len(left) < 4 or len(right) < 4:
        return False
    common = len(left & right)
    return common >= 4 and common / max(1, len(left | right)) >= 0.82


_BAD_OPTIONS = ('كل ما سبق','جميع ما سبق','ليس مما سبق','لا شيء مما سبق',
                'جميع الخيارات','لا توجد اجابة','لا توجد إجابة')


def review_verified_rows(rows, existing=None, limit=25, excluded=None):
    """Additional independent *structural* review AFTER literal quote check.

    Does NOT replace fact checking by a human teacher. Distractor truthfulness
    cannot be established by string matching; no score implies official proof.
    """
    existing = list(existing or [])
    excluded = list(excluded or [])
    kept = []
    reasons = Counter()
    for row in rows:
        if len(kept) >= int(limit):
            break
        if not isinstance(row, dict):
            reasons['invalid'] += 1
            continue
        question = str(row.get('q') or '').strip()
        answer = str(row.get('a') or '').strip()
        quote = str(row.get('sourceQuote') or '').strip()
        if len(question) < 9 or len(answer) < 2 or not quote:
            reasons['unclear'] += 1
            continue
        if any(is_near_duplicate(question, previous.get('q') or '')
               for previous in existing + kept):
            reasons['duplicate'] += 1
            continue
        if any(is_near_duplicate(question, item) for item in excluded):
            reasons['duplicate'] += 1
            continue
        kind = str(row.get('questionType') or '')
        if kind == 'mcq':
            options = row.get('choices') or []
            if (len(options) != 4
                    or any(_plain(o) in {_plain(x) for x in _BAD_OPTIONS}
                           for o in options)
                    or len({_plain(o) for o in options}) != 4
                    or sum(_plain(o) == _plain(answer) for o in options) != 1):
                reasons['options'] += 1
                continue
        if kind == 'true_false' and answer not in ('صح', 'خطأ'):
            reasons['answer'] += 1
            continue
        approved = dict(row)
        approved['reviewStatus'] = 'teacher_review_required'
        approved['sourceQuoteVerified'] = True
        approved['qualityLabel'] = 'دليل نصي مطابق — بانتظار مراجعة المعلم'
        kept.append(approved)
    return kept, dict(reasons)


def distribute_by_pages(rows, maximum):
    """Page-balanced selection without mixing different books."""
    buckets = {}
    for row in rows:
        buckets.setdefault(int(row['sourcePage']), []).append(row)
    spread = []
    while len(spread) < min(int(maximum), len(rows)):
        changed = False
        for page in sorted(buckets):
            if buckets[page] and len(spread) < int(maximum):
                spread.append(buckets[page].pop(0))
                changed = True
        if not changed:
            break
    return spread


def choose_repair_pages(selected_pages, accepted, max_pages=6):
    """Prefer under-represented pages with enough source text for correction."""
    counts = Counter(int(row['sourcePage']) for row in accepted)
    candidates = [
        p for p in selected_pages
        if len(str(p.get('text') or '').strip()) >= 90
    ]
    candidates.sort(key=lambda p: (counts.get(int(p['p']), 0), int(p['p'])))
    # A repair request uses one contiguous range; make its bounds explicit.
    if not candidates:
        return None
    page = int(candidates[0]['p'])
    by_page = {int(p['p']): p for p in selected_pages}
    numbers = [n for n in sorted(by_page) if n >= page][:max_pages]
    # Caller may use this as a single-page retry to avoid bringing pages
    # without relevant evidence into the citation check.
    return (page, numbers[-1] if numbers else page)


def report_coverage(rows, selected_pages):
    pages = {int(p['p']) for p in selected_pages if str(p.get('text') or '').strip()}
    covered = {int(row['sourcePage']) for row in rows} & pages
    return {'coveredPages': len(covered), 'extractablePages': len(pages),
            'uncoveredPages': sorted(pages - covered)}
