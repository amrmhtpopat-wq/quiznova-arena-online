"""TAG Smart Math -- server-authoritative Grade 7 equation question engine.

All generated questions are verified arithmetically before being accepted.
Not a full mapping of the official Jordanian mathematics textbook.
"""
import random
from fractions import Fraction

SKILL_NAMES = {
    'one_step': 'العمليات العكسية',
    'two_steps': 'المعادلات من خطوتين',
    'negative': 'التعامل مع الإشارات السالبة',
    'parentheses': 'فك الأقواس',
    'both_sides': 'المتغير في طرفي المعادلة',
    'word_problem': 'المسائل اللفظية',
}
PHASES = ['foundation'] * 10 + ['application'] * 12 + ['reasoning'] * 8
SKILL_SEQUENCES = {
    'foundation': ['one_step','one_step','two_steps','negative','one_step','two_steps','negative','two_steps','one_step','negative'],
    'application': ['two_steps','parentheses','both_sides','negative','parentheses','two_steps','both_sides','word_problem','negative','parentheses','both_sides','word_problem'],
    'reasoning': ['both_sides','parentheses','word_problem','both_sides','word_problem','parentheses','both_sides','word_problem'],
}

def _make(skill, phase, r):
    # Keep integer solutions by constructing RHS from the intended solution.
    x = r.randint(-8, 12) if phase != 'foundation' else r.randint(-5, 10)
    if skill == 'one_step':
        n = r.randint(2, 18)
        if r.random() < .5:
            rhs = x + n
            prompt, eq = 'أوجد قيمة x باستعمال العملية العكسية.', f'x + {n} = {rhs}'
            steps = [f'x = {rhs} − {n}', f'x = {x}']
            check = x + n == rhs
            hint = f'اطرح {n} من الطرفين.'
        else:
            rhs = x - n
            prompt, eq = 'أوجد قيمة x باستعمال العملية العكسية.', f'x − {n} = {rhs}'
            steps = [f'x = {rhs} + {n}', f'x = {x}']
            check = x - n == rhs
            hint = f'أضف {n} إلى الطرفين.'
    elif skill == 'two_steps':
        a, b = r.randint(2, 8), r.randint(2, 16)
        rhs = a*x+b
        prompt, eq = 'حل المعادلة التالية، ثم تحقق بالتعويض.', f'{a}x + {b} = {rhs}'
        steps = [f'{a}x = {rhs} − {b}', f'{a}x = {rhs-b}', f'x = {x}']
        check = a*x+b == rhs
        hint = 'تخلص من العدد الثابت أولًا، ثم اقسم الطرفين على معامل x.'
    elif skill == 'negative':
        a = r.choice([-8,-7,-6,-5,-4,-3,-2]); b = r.randint(-14, 14)
        rhs = a*x+b
        sign = '+' if b >= 0 else '−'
        prompt, eq = 'انتبه إلى الإشارات السالبة، ثم حل المعادلة.', f'{a}x {sign} {abs(b)} = {rhs}'
        steps = [f'{a}x = {rhs-b}', f'x = ({rhs-b}) ÷ ({a})', f'x = {x}']
        check = a*x+b == rhs
        hint = 'عند القسمة على عدد سالب تتغير إشارة الناتج وفق قواعد الإشارات.'
    elif skill == 'parentheses':
        a, b, c = r.randint(2,7), r.randint(-6,7), r.randint(-10,10)
        rhs = a*(x+b)+c
        prompt, eq = 'فك الأقواس أو استعمل العمليات العكسية لحل المعادلة.', f'{a}(x {"+" if b>=0 else "−"} {abs(b)}) {"+" if c>=0 else "−"} {abs(c)} = {rhs}'
        steps = [f'{a}(x {"+" if b>=0 else "−"} {abs(b)}) = {rhs-c}', f'x {"+" if b>=0 else "−"} {abs(b)} = {x+b}', f'x = {x}']
        check = a*(x+b)+c == rhs
        hint = 'ابدأ بإزالة الحد الخارجي، ثم اقسم على العامل خارج القوس.'
    elif skill == 'both_sides':
        a, c = r.sample(range(2,11),2)
        b, d = r.randint(-14,14), r.randint(-14,14)
        d = (a-c)*x+b  # a*x+b = c*x+d
        prompt, eq = 'اجمع الحدود التي تحتوي على x في طرف، والثوابت في طرف آخر.', f'{a}x {"+" if b>=0 else "−"} {abs(b)} = {c}x {"+" if d>=0 else "−"} {abs(d)}'
        steps = [f'{a-c}x = {d-b}', f'x = ({d-b}) ÷ ({a-c})', f'x = {x}']
        check = a*x+b == c*x+d
        hint = 'اطرح الحد الحاوي x من الطرفين، ثم اعزل المجهول.'
    elif skill == 'word_problem':
        x = r.randint(2, 16)
        a, b = r.randint(2, 7), r.randint(3, 15)
        rhs = a*x+b
        prompt = f'اشترى طالب {a} دفاتر متساوية السعر، ودفع {b} دنانير إضافية. إذا كان المجموع {rhs} دينارًا، فما ثمن الدفتر الواحد؟'
        eq = f'{a}x + {b} = {rhs}'
        steps = [f'{a}x = {rhs} − {b}', f'{a}x = {rhs-b}', f'x = {x} دينار']
        check = a*x+b == rhs
        hint = 'مثّل ثمن الدفتر بالمجهول x، ثم كوّن المعادلة.'
    else:
        raise ValueError('Unknown skill')
    if not check or not isinstance(x, int):
        raise AssertionError('Invalid generated question')
    return {'prompt':prompt,'math':eq,'answer':x,'steps':steps,'hint':hint,'skill':skill,'phase':phase,'kind':'number'}

def make_questions(seed, count=30):
    if count not in (5,10,15,30):
        raise ValueError('Unsupported question count')
    r=random.Random(seed)
    full=[]
    for phase in ('foundation','application','reasoning'):
        for skill in SKILL_SEQUENCES[phase]:
            full.append((phase,skill))
    if count < 30:
        # Spread short practices over phases; avoid all-easy questions in shorter sets.
        selected=[full[(i*30)//count] for i in range(count)]
    else:
        selected=full
    questions=[]; seen=set()
    for phase,skill in selected:
        for _ in range(200):
            q=_make(skill,phase,r)
            signature=(q['prompt'],q['math'])
            if signature not in seen:
                seen.add(signature)
                break
        else: raise RuntimeError('Question diversity exhausted')
        # The server decides to send either a numeric entry or four shuffled choices.
        if r.random()<.30:
            answer=q['answer']; distractors=set()
            for offset in [1,-1,2,-2,3,-3,5,-5,7,-7]:
                v=answer+offset
                if v!=answer: distractors.add(v)
                if len(distractors)>=3: break
            opts=[answer]+r.sample(sorted(distractors),3)
            r.shuffle(opts)
            q['kind']='mcq';q['options']=opts
        else: q['options']=[]
        questions.append(q)
    if len(questions)!=count: raise AssertionError('Wrong question count')
    return questions

def parse_answer(value):
    if isinstance(value,bool): return None
    s=str(value).strip().translate(str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹','01234567890123456789')).replace('−','-')
    if len(s)>40: return None
    try:
        f=Fraction(s)
        return int(f) if f.denominator == 1 else None
    except (ValueError,ZeroDivisionError):return None

if __name__=='__main__':
    for j in range(100):
        questions=make_questions(j+100)
        assert len({(x['prompt'],x['math']) for x in questions})==30
        assert [x['phase'] for x in questions].count('foundation') == 10
        assert [x['phase'] for x in questions].count('application') == 12
        assert [x['phase'] for x in questions].count('reasoning') == 8
    print('math engine checks passed')
