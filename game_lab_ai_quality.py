"""Validate TAG LAB AI proposals against pages of the teacher's uploaded book.

Citations are accepted only when the source exists in the selected book.
Minor OCR/Arabic spelling differences and wrong page labels can be corrected
without trusting the model to invent supporting evidence.
"""
from __future__ import annotations
from difflib import SequenceMatcher
import re
import unicodedata


def _plain(value):
    text=unicodedata.normalize('NFKC',str(value or ''))
    text=re.sub(r'[\u064b-\u065f\u0670\u0640\u200b-\u200f]','',text)
    text=text.translate(str.maketrans({'أ':'ا','إ':'ا','آ':'ا','ٱ':'ا','ى':'ي','ی':'ي','ک':'ك'}))
    return re.sub(r'[^\w\u0621-\u064a]+',' ',text,flags=re.UNICODE).strip().casefold()


def suspicious_book_text(value):
    """Conservatively reject recognizable exam furniture and damaged PDF text.

    Quoting the book proves provenance, not that the extracted words form a
    meaningful educational statement. Apply to AI and local book candidates.
    Normal curriculum paragraphs, numbers, mathematics and English are allowed.
    """
    raw=unicodedata.normalize('NFKC',str(value or ''))
    normalized=_plain(raw)
    if not normalized:return True
    # Common exam instructions, headers, pagination and answer-sheet boilerplate.
    if re.search(r'(?:اجب|أجب)\s+(?:عن|على)\s+(?:جميع\s+)?(?:الاسئله|الاسئلة|الأسئلة|السوال|السؤال)',raw):
        return True
    if re.search(r'(?:السؤال\s+(?:الاول|الثاني|الثالث)|اسم\s+الطالب|رقم\s+الجلوس|علامة\s+الامتحان)',normalized):
        return True
    if re.search(r'(?:ضع\s+دائرة|اختر\s+الاجابة\s+الصحيحة|الاسئلة\s+جميعها|مده\s+الامتحان)',normalized):
        return True
    # Very common forms of accidentally glued examination-header words.
    if re.search(r'(?:منالمتحان|المةصفحة|الصفحاتادد|السئلةجميع|الاسئلةجميع|ازلزي|واددها|المتحان)',normalized):
        return True
    words=normalized.split()
    arabic_words=[w for w in words if re.fullmatch(r'[\u0621-\u064a]+',w)]
    if arabic_words and any(len(w)>25 for w in arabic_words):
        return True
    # Several numbered fields + examination terms usually indicate a header,
    # rather than a lesson paragraph. Do not reject real mathematical numerals.
    exam_terms=sum(bool(re.search(r'\b'+w+r'\b',normalized))
                   for w in ('الامتحان','الاسئلة','الطالب','الصفحة','الصفحات',
                             'ملاحظة','العلامة','الاسم','اجب','المدرسة'))
    if exam_terms>=3 and len(re.findall(r'\d+',raw))>=2:
        return True
    if len(words)>=8 and sum(1 for w in words if re.fullmatch(r'\d+',w))>len(words)*.45:
        return True
    return False


def _usable_source_lines(text):
    """Strip clearly corrupt PDF text before it reaches the external model.

    This is an intentionally conservative text filter. It never repairs
    damaged words by guessing. Teachers can inspect the unmodified text.
    """
    accepted=[]
    removed=0
    for raw_line in str(text or '').splitlines():
        line=unicodedata.normalize('NFKC',raw_line).strip()
        if not line:continue
        # Long PDF text lines can contain several statements: segment them
        # so one damaged header does not discard an entire clean paragraph.
        segments=(re.split(r'(?<=[.؟!؛])\s+',line)
                  if len(line)>800 else [line])
        for part in segments:
            candidate=re.sub(r'\s+',' ',part).strip()
            tokens=_plain(candidate).split()
            if (len(candidate)<25 or len(tokens)<4 or
                    suspicious_book_text(candidate) or
                    re.fullmatch(r'[\d\s\-()\[\].،:]+',candidate)):
                removed+=1
                continue
            accepted.append(candidate)
    return accepted,removed


def audit_ai_source(book,start,end,decode_pages,max_chars=26000,max_pages=25):
    """Readiness report without an AI call or external upload."""
    pages=decode_pages(book['page_data'],[])
    try:
        a=int(start or 1)
        b=int(end or len(pages))
    except (TypeError,ValueError,OverflowError):
        raise ValueError('invalid_pages')
    if a<1 or b<a or b>len(pages):
        raise ValueError('invalid_pages')
    selected=[p for p in pages if a<=int(p.get('p') or 0)<=b]
    if not selected:
        raise ValueError('empty_pages')
    if len(selected)>max_pages:
        raise ValueError('ai_too_many_pages')
    summary=[]
    good=[]
    for page in selected:
        number=int(page['p'])
        lines,removed=_usable_source_lines(page.get('text',''))
        extracted='\n'.join(lines)
        word_count=len(_plain(extracted).split())
        usable=(len(extracted)>=65 and word_count>=10)
        if usable:good.append({'p':number,'text':extracted})
        summary.append({'page':number,'readable':usable,'words':word_count,
                        'excludedFragments':removed})
    selected_count=len(selected)
    report={'selectedPages':selected_count,'readablePages':len(good),
            'excludedPages':selected_count-len(good),
            'excludedFragments':sum(p['excludedFragments'] for p in summary),
            'pages':summary,'ready':bool(good)}
    if not good:
        report['message']=('النص المستخرج من الصفحات المحددة غير موثوق أو لا يحتوي على درس مقروء. '
                           'اختر صفحات شرح واضحة أو ارفع PDF نصيًا سليمًا أو DOCX؛ '
                           'لن نرسل نصًا مشوّهًا إلى TAG AI.')
        return '',[],report
    per_page=max(350,(max_chars-24*len(good))//len(good))
    fragments=[]
    for page in good:
        snippet=page['text'][:per_page]
        # Avoid truncating Arabic words if the page exceeds its text budget.
        if len(page['text'])>per_page and ' ' in snippet:
            snippet=snippet.rsplit(' ',1)[0]
        fragments.append('[صفحة '+str(page['p'])+']\n'+snippet)
    source='\n\n'.join(fragments)[:max_chars]
    report['message']=('تم العثور على '+str(len(good))+' صفحات صالحة من '+
                       str(selected_count)+'؛ استُبعدت المقاطع المشوهة قبل إرسال النص. '
                       'راجع الصفحات والإجابات قبل اعتماد المقترحات.')
    return source,good,report


def selected_ai_source(book,start,end,decode_pages,max_chars=26000,max_pages=25):
    source,pages,report=audit_ai_source(book,start,end,decode_pages,
                                       max_chars=max_chars,max_pages=max_pages)
    if not report['ready']:
        raise ValueError('ai_source_quality_low')
    return source,pages


def _near_literal_quote(quote,original):
    """Return a real contiguous book excerpt only for very-close OCR variants.

    Six-plus words and 93% token agreement prevent a loose semantic match
    from ever becoming a fabricated citation.
    """
    words=_plain(quote).split()
    if len(words)<6 or len(words)>45:
        return None
    original=str(original or '')
    spans=[]
    for item in re.finditer(r'\w+',original,flags=re.UNICODE):
        normalized=_plain(item.group())
        if normalized:
            for token in normalized.split():
                spans.append((token,item.start(),item.end()))
    n=len(words)
    if len(spans)<n-1:
        return None
    first=words[0]
    for i in range(len(spans)):
        if spans[i][0]!=first:
            continue
        for width in (n,n-1,n+1):
            if width<6 or i+width>len(spans):
                continue
            excerpt=' '.join(x[0] for x in spans[i:i+width])
            if SequenceMatcher(None,' '.join(words),excerpt,autojunk=False).ratio()<0.94:
                continue
            literal=original[spans[i][1]:spans[i+width-1][2]].strip()
            if 14<=len(_plain(literal))<=240 and len(literal)<=240:
                return literal
    return None


_ANSWER_STOP_WORDS={'في','من','على','الى','إلى','عن','التي','الذي','هذا',
                    'هذه','انه','بانه','لها','لهم','عند','لأن','بعض','وهي',
                    'ذلك','تلك','تكون','يكون','هي','هو','مع','بين'}


def answer_evidence_strength(answer,quote):
    """High/low confidence of literal source support, not semantic truth."""
    a=_plain(answer)
    evidence=_plain(quote)
    if not a or not evidence:return 'needs_review'
    if a in evidence:return 'direct'
    significant=[w for w in a.split()
                 if len(w)>=3 and w not in _ANSWER_STOP_WORDS]
    if len(significant)>=2:
        supported=sum(any(w==token or
                          (len(w)>=5 and len(token)>=5 and
                           (w in token or token in w))
                          for token in evidence.split())
                      for w in significant)
        if supported>=2 and supported/len(significant)>=0.75:
            return 'partial'
    return 'needs_review'


def verify_ai_rows(raw_rows,selected_pages,maximum,include_stats=False):
    """Keep source-grounded questions, repairing only verifiable formatting.

    An MCQ whose choices are malformed becomes a short-answer suggestion for
    the teacher to edit, rather than losing an otherwise valid question.
    """
    source_text={int(p['p']):str(p.get('text') or '') for p in selected_pages}
    source_plain={p:_plain(t) for p,t in source_text.items()}
    stats={'missing_quote':0,'invalid_fields':0,'duplicate':0,
           'invalid_true_false':0,'corrected_page':0,'corrected_quote':0,
           'repaired_choices':0,'accepted':0,'needs_review':0}
    found=[]
    seen=set()
    for row in (raw_rows if isinstance(raw_rows,list) else [])[:max(0,int(maximum))*3]:
        if not isinstance(row,dict):
            stats['invalid_fields']+=1
            continue
        q=str(row.get('q') or '').strip()[:200]
        a=str(row.get('a') or '').strip()[:100]
        quote=str(row.get('sourceQuote') or '').strip()[:240]
        try:
            page=int(row.get('sourcePage'))
        except (ValueError,TypeError,OverflowError):
            page=None
        normalized=_plain(quote)
        if any(suspicious_book_text(part) for part in (q,a,quote)):
            stats['invalid_fields']+=1
            continue
        if not (8<=len(q)<=200 and 2<=len(a)<=100 and 14<=len(normalized)<=240):
            stats['invalid_fields']+=1
            continue
        matched=None
        if page in source_plain and normalized in source_plain[page]:
            matched=page
        else:
            # Models sometimes copy the right passage but label the wrong page.
            for candidate,body in source_plain.items():
                if normalized in body:
                    matched=candidate
                    break
        if matched is None and page in source_text:
            corrected=_near_literal_quote(quote,source_text[page])
            if corrected:
                quote=corrected
                matched=page
                stats['corrected_quote']+=1
        if matched is None:
            stats['missing_quote']+=1
            continue
        if page!=matched:
            stats['corrected_page']+=1
        signature=_plain(q)
        if signature in seen:
            stats['duplicate']+=1
            continue
        group=str(row.get('g') or '').strip()[:60] or ('صفحة '+str(matched))
        question_type=str(row.get('questionType') or 'short').strip()
        if question_type not in ('mcq','true_false','short'):
            question_type='short'
        level=str(row.get('difficulty') or 'medium').strip()
        if level not in ('easy','medium','hard'):
            level='medium'
        explanation=str(row.get('explanation') or '').strip()[:240]
        choices=[]
        if question_type=='mcq':
            raw_choices=row.get('choices')
            if isinstance(raw_choices,list) and len(raw_choices)==4:
                choices=[str(v).strip()[:100] for v in raw_choices]
            canonical=[_plain(c) for c in choices]
            if (len(choices)!=4 or any(not c for c in canonical)
                    or len(set(canonical))!=4 or canonical.count(_plain(a))!=1):
                # Do not silently invent distractors: retain the teacher's
                # verifiable question as a short-answer question instead.
                question_type='short'
                stats['repaired_choices']+=1
                explanation=(explanation+' | راجع خيارات الاختيار من متعدد.').strip(' |')[:240]
            else:
                a=choices[canonical.index(_plain(a))]
        elif question_type=='true_false':
            mapped={'صح':'صح','صحيح':'صح','صحيحة':'صح',
                    'خطأ':'خطأ','خاطئ':'خطأ','خاطئة':'خطأ','غير صحيح':'خطأ'}
            converted=mapped.get(_plain(a))
            if not converted:
                stats['invalid_true_false']+=1
                continue
            a=converted
            choices=['صح','خطأ']
        question={'q':q,'a':a,'g':group,'sourcePage':matched,
                  'sourceQuote':quote,'origin':'ai','questionType':question_type,
                  'difficulty':level}
        if choices and question_type in ('mcq','true_false'):
            question['choices']=choices
        if explanation:
            question['explanation']=explanation
        # Literal proof for MCQ/short answers. A false T/F answer requires
        # semantic review, so it is never automatically marked verified.
        strength=('needs_review' if question_type=='true_false' and a=='خطأ'
                  else answer_evidence_strength(a,quote)
                  if question_type in ('short','mcq') else 'direct')
        if question_type=='short' and 'راجع خيارات' in explanation:
            strength='needs_review'
        question['evidenceStatus']=strength
        if strength=='needs_review':
            question['requiresReview']=True
            question['reviewReason']=('قارن الإجابة مع اقتباس الكتاب؛ لا توجد مطابقة نصية كافية.'
                                      if question_type!='true_false' else
                                      'تأكد من صحة الحكم على العبارة بالرجوع إلى صفحة الدرس.')
            stats['needs_review']+=1
        found.append(question)
        seen.add(signature)
        if len(found)>=maximum:
            break
    buckets={}
    for row in found:
        buckets.setdefault(row['sourcePage'],[]).append(row)
    balanced=[]
    while len(balanced)<len(found):
        for page in sorted(buckets):
            if buckets[page]:
                balanced.append(buckets[page].pop(0))
    stats['accepted']=len(balanced)
    return (balanced,stats) if include_stats else balanced
