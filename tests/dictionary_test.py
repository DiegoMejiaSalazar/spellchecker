import math
import unittest

from parameterized import parameterized
from nose.tools import assert_equals

from services.dictionary import EnglishDictionary
from services.namesdictionary import NamesDictionary


class TestMathUnitTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        EnglishDictionary.load()
        NamesDictionary.load()


    @parameterized.expand([
        ("negative", True),
        ("integer", True),
        ("large", True),
        ("driven", True),
        ("design", True),
        ("front", True),
        ("end", True)
    ])
    def test_word_exist_in_english_dictionary(self, word, expected):
        assert_equals(EnglishDictionary.check_if_word_exist(word), expected)

    @parameterized.expand([
        ("Diego", True),
        ("Jose", True),
        ("Daniel", True),
        ("Juan", True),
        ("Hector", True),
        ("Luis", True),
        ("Pepe", True),
        ("Daniela", True),
        ("Ricardo", True),
        ("Erick", True),
    ])
    def test_if_names_exists_in_names_dictionary(self, word, expected):
        assert_equals(EnglishDictionary.check_if_word_exist(word), expected)


if __name__ == '__main__':
    unittest.main()
