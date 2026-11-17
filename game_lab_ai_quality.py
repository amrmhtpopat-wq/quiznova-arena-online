"""Source-grounding for TAG LAB AI questions.

No model output is trusted as a citation: the quote must be found on the
claimed page of the teacher's saved book. Pure helpers; no API calls.
"""
from __future__ import annotations
import re
import unicodedata


def _plain(value):
    text=unicodedata.normalize('NFKC',str(value or ''))
    text=re.sub(r'[\u064b-\u065f\u0670\u0640\u200b-\u200d]','',text)
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


def verify_ai_rows(raw_rows,selected_pages,maximum):
    """Only retain questions with a literal quote on the stated source page."""
    sources={int(p['p']):_plain(p['text']) for p in selected_pages}
    found=[]
    seen=set()
    for row in raw_rows[:max(0,int(maximum))*3]:
        if not isinstance(row,dict):
            continue
        q=str(row.get('q') or '').strip()[:200]
        a=str(row.get('a') or '').strip()[:100]
        quote=str(row.get('sourceQuote') or '').strip()[:240]
        try:page=int(row.get('sourcePage'))
        except (ValueError,TypeError,OverflowError):continue
        normalized=_plain(quote)
        if not (8<=len(q)<=200 and 2<=len(a)<=100 and 14<=len(normalized)<=240):
            continue
        if page not in sources or normalized not in sources[page]:
            continue
        signature=_plain(q)
        if signature in seen:
            continue
        seen.add(signature)
        group=str(row.get('g') or '').strip()[:60] or ('صفحة '+str(page))
        found.append({'q':q,'a':a,'g':group,'sourcePage':page,
                      'sourceQuote':quote,'origin':'ai'})
        if len(found)>=maximum:
            break
    # Distribute the retained questions across the pages when possible.
    buckets={}
    for row in found:
        buckets.setdefault(row['sourcePage'],[]).append(row)
    balanced=[]
    while len(balanced)<len(found):
        for page in sorted(buckets):
            if buckets[page]:
                balanced.append(buckets[page].pop(0))
    return balanced
