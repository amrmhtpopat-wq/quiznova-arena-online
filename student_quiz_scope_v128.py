"""Strict per-card solo-quiz grade/section visibility (Arabic and numeric grade labels).

Every visible quiz must have an explicit grade matching the registered student's
class.  A blank section means all sections in that grade; an explicit section
limits access further.  Applied by the API, not merely by browser filtering.
"""
import re
import unicodedata

_GRADE_WORDS = {
    12: ('الثاني عشر', 'ثاني عشر', 'الثاني عشر', '12'),
    11: ('الحادي عشر', 'حادي عشر', '11'),
    10: ('العاشر', 'عاشر', '10'),
    9: ('التاسع', 'تاسع', '9'),
    8: ('الثامن', 'ثامن', '8'),
    7: ('السابع', 'سابع', '7'),
    6: ('السادس', 'سادس', '6'),
    5: ('الخامس', 'خامس', '5'),
    4: ('الرابع', 'رابع', '4'),
    3: ('الثالث', 'ثالث', '3'),
    2: ('الثاني', 'ثاني', '2'),
    1: ('الاول', 'اول', '1'),
}
_DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹', '01234567890123456789')
_ARABIC = str.maketrans({'أ':'ا', 'إ':'ا', 'آ':'ا', 'ٱ':'ا', 'ى':'ي', 'ـ':''})
_SECTIONS = {
    'ا':'a', 'أ':'a', 'a':'a', 'الف':'a',
    'ب':'b', 'b':'b', 'باء':'b',
    'ج':'c', 'c':'c', 'جيم':'c',
    'د':'d', 'd':'d', 'دال':'d',
    'ه':'e', 'هـ':'e', 'e':'e'
}
_JUNK = re.compile(r'\b(?:الصف|صف|الشعبه|شعبه|الشعبة|شعبة|المجموعه|مجموعة|المجموعة|القسم|قسم|الفصل|فصل|grade|class|section)\b')


def normalized(value):
    text = unicodedata.normalize('NFKC', str(value or '')).translate(_DIGITS).translate(_ARABIC).lower()
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    return re.sub(r'\s+', ' ', text).strip()


def class_parts(value):
    """Parse e.g. التاسع ب, الصف التاسع/أ, 9B, G9-B, الثامن, 8/ج."""
    source = normalized(value)
    if not source:
        return None, ''
    # Ensure English grade shorthand does not get parsed as a section.
    shorthand = re.search(r'(?<![a-z0-9])g?\s*(1[0-2]|0?[1-9])\s*([a-e])(?=$|\s|[^\w])', source)
    if shorthand:
        grade = int(shorthand.group(1))
        leftover = source[:shorthand.start()] + ' ' + shorthand.group(2) + ' ' + source[shorthand.end():]
    else:
        grade, leftover = None, source
        # Word boundaries matter: match "الثاني عشر" before "الثاني".
        for number, aliases in _GRADE_WORDS.items():
            for alias in aliases:
                if alias.isdigit():
                    continue
                match = re.search(r'(?<!\w)' + re.escape(alias) + r'(?!\w)', source)
                if match:
                    grade = number
                    leftover = source[:match.start()] + ' ' + source[match.end():]
                    break
            if grade is not None:
                break
        if grade is None:
            match = re.search(r'(?<!\d)(1[0-2]|0?[1-9])(?!\d)', source)
            if match:
                grade = int(match.group(1))
                leftover = source[:match.start()] + ' ' + source[match.end():]
    leftover = _JUNK.sub(' ', leftover)
    candidates = re.findall(r'[\w]+', leftover)
    section = ''
    for candidate in candidates:
        if candidate in _SECTIONS:
            section = _SECTIONS[candidate]
            break
    return grade, section


def section_code(value):
    """A teacher can enter just أ/ب or a full class such as التاسع ب."""
    text = normalized(value)
    if not text:
        return ''
    _, section = class_parts(text)
    if section:
        return section
    # "G9B" is handled by class_parts above. Unknown values never match
    # silently; compare their normalized spelling literally.
    return re.sub(r'\W+', '', text)


def allowed(quiz, student):
    grade, student_section = class_parts(student.get('class_name') or student.get('className'))
    quiz_grade, _ = class_parts(quiz.get('grade'))
    if grade is None or quiz_grade is None or grade != quiz_grade:
        return False
    required_section = section_code(quiz.get('section', ''))
    return not required_section or (bool(student_section) and student_section == required_section)
