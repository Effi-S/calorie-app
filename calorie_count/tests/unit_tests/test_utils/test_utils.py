import unittest
from datetime import date

from calorie_count.src.utils.utils import sort_by_similarity, similarity, str2iso


class TestSortBySimilarity(unittest.TestCase):
    def test_empty_list(self):
        self.assertEqual(sort_by_similarity([], 'hello'), [])

    def test_unsorted_list(self):
        self.assertEqual(next(iter(sort_by_similarity(['world', 'bar', 'hello', 'foo'], 'hello'))), 'hello')

    def test_case_insensitivity(self):
        self.assertEqual(next(iter(sort_by_similarity(['Hello', 'world', 'foo', 'bar'], 'hello'))), 'Hello')

    def test_tuple(self):
        tup = ('world', 'Johnny', 'hello', 'foo')
        self.assertEqual(next(iter(sort_by_similarity(tup, 'john'))), 'Johnny')


class TestSimilarity(unittest.TestCase):
    def test_identical_strings(self):
        self.assertEqual(similarity('hello', 'hello'), 1.0)

    def test_completely_different_strings(self):
        result = similarity('hello', 'xyzabc')
        self.assertLess(result, 0.5)

    def test_similar_strings(self):
        result = similarity('hello', 'hell')
        self.assertGreater(result, 0.7)

    def test_empty_strings(self):
        self.assertEqual(similarity('', ''), 1.0)

    def test_one_empty_string(self):
        result = similarity('hello', '')
        self.assertLess(result, 1.0)


class TestStr2Iso(unittest.TestCase):
    def test_valid_date_string(self):
        result = str2iso('2022-12-15')
        self.assertIsInstance(result, date)
        self.assertEqual(result.year, 2022)
        self.assertEqual(result.month, 12)
        self.assertEqual(result.day, 15)

    def test_another_valid_date(self):
        result = str2iso('2023-01-01')
        self.assertEqual(result, date(2023, 1, 1))

    def test_invalid_date_format(self):
        with self.assertRaises(ValueError):
            str2iso('2022/12/15')

    def test_invalid_date(self):
        with self.assertRaises(ValueError):
            str2iso('2022-13-45')


# TODO make mock app for testing this TextField and for components
# class TestRTLMDTextField(unittest.TestCase):
#
#     @patch.object(MDTextField, 'insert_text')
#     def test_insert_rtl_text(self, mock_insert_text):
#         text_field = RTLMDTextField()
#         text_field.insert_text('ش')
#         mock_insert_text.assert_called_once_with('ش', from_undo=False)
#         self.assertEqual(text_field.text, 'ش')


if __name__ == '__main__':
    unittest.main()
