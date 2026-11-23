"""Regression tests for corrupted Arabic textbook questions in independent TAG LAB.

Run with: python -m unittest discover -s tests -p 'test_tag_lab_book_question_quality.py'
"""
import unittest

from game_lab_ai_quality import (
    invalid_educational_pair,
    suspicious_book_text,
    verify_ai_rows,
)


BROKEN_QUESTION = "ما المقصود بـ ثم أجب عن الأسئلة التي تليه؟"
BROKEN_ANSWER = '"الموجود داخل مشغل الأقراص'
GOOD_QUOTE = (
    "الأمن الرقمي هو حماية البيانات والمعلومات الشخصية من الوصول "
    "غير المصرح به والمحافظة على الخصوصية."
)


class TagLabQuestionQualityTests(unittest.TestCase):
    def test_reject_exact_book_screenshot(self):
        self.assertTrue(invalid_educational_pair(BROKEN_QUESTION, BROKEN_ANSWER))
        self.assertTrue(suspicious_book_text(BROKEN_QUESTION))

    def test_unmatched_answer_quote_is_rejected(self):
        self.assertTrue(invalid_educational_pair(
            "ما وظيفة مشغل الأقراص؟", BROKEN_ANSWER))

    def test_other_exam_instructions_are_rejected(self):
        self.assertTrue(invalid_educational_pair(
            "اقرأ النص التالي ثم أجب عن الأسئلة", "نص الدرس"))
        self.assertTrue(invalid_educational_pair(
            "ما المقصود بـ ثم اكتب المطلوب؟", "المعلومات"))

    def test_legitimate_educational_question_remains_valid(self):
        self.assertFalse(invalid_educational_pair(
            "ما المقصود بالأمن الرقمي؟",
            "حماية البيانات والمعلومات الشخصية من الوصول غير المصرح به"))
        self.assertFalse(invalid_educational_pair(
            "ما وظيفة جهاز التوجيه؟",
            "توجيه البيانات بين الشبكات المختلفة"))

    def test_balanced_quotes_are_not_automatically_corrupt(self):
        self.assertFalse(invalid_educational_pair(
            "ما المقصود بالتعلم؟", "«اكتساب المعرفة والمهارات»"))

    def test_verification_rejects_instruction_even_if_quoted_from_book(self):
        quote = "اقرأ الفقرة التالية ثم أجب عن الأسئلة التي تليها في النص."
        rows = [{
            "q": BROKEN_QUESTION, "a": BROKEN_ANSWER, "g": "مراجعة",
            "sourcePage": 41, "sourceQuote": quote, "questionType": "short"
        }]
        accepted, stats = verify_ai_rows(
            rows, [{"p": 41, "text": quote}], 12, include_stats=True)
        self.assertEqual(accepted, [])
        self.assertEqual(stats["invalid_fields"], 1)

    def test_good_textbook_answer_still_verifies(self):
        rows = [{
            "q": "ما المقصود بالأمن الرقمي؟",
            "a": "حماية البيانات والمعلومات الشخصية من الوصول غير المصرح به",
            "g": "الأمن الرقمي", "sourcePage": 3, "sourceQuote": GOOD_QUOTE,
            "questionType": "short"
        }]
        accepted, _ = verify_ai_rows(
            rows, [{"p": 3, "text": GOOD_QUOTE}], 12, include_stats=True)
        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0]["sourcePage"], 3)


if __name__ == "__main__":
    unittest.main()
