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


def selected_ai_source(book,start,end,decode_pages,max_chars=26000,max_pages=25):
    pages=decode_pages(book['page_data'],[])
    try:
        a=int(start or 1)
        b=int(end or len(pages))
    except (TypeError,ValueError,OverflowError):
        raise ValueError('invalid_pages')
    if a<1 or b<a or b>len(pages):
        raise ValueError('invalid_pages')
    chosen=[p for p in pages if a<=int(p['p'])<=b and str(p.get('text') or '').strip()]
    if not chosen:
        raise ValueError('empty_pages')
    if len(chosen)>max_pages:
        raise ValueError('ai_too_many_pages')
    per_page=max(300,(max_chars-24*len(chosen))//len(chosen))
    fragments=['[صفحة '+str(p['p'])+']\n'+str(p['text'])[:per_page] for p in chosen]
    return '\n\n'.join(fragments)[:max_chars],chosen


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


def verify_ai_rows(raw_rows,selected_pages,maximum,include_stats=False):
    """Keep source-grounded questions, repairing only verifiable formatting.

    An MCQ whose choices are malformed becomes a short-answer suggestion for
    the teacher to edit, rather than losing an otherwise valid question.
    """
    source_text={int(p['p']):str(p.get('text') or '') for p in selected_pages}
    source_plain={p:_plain(t) for p,t in source_text.items()}
    stats={'missing_quote':0,'invalid_fields':0,'duplicate':0,
           'invalid_true_false':0,'corrected_page':0,'corrected_quote':0,
           'repaired_choices':0,'accepted':0}
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
