# import pytest

# from main import is_anagram

# @pytest.mark.parametrize(
#     "str1, str2, expected",
#     [
#         ("", "", True),
#         ("", " ", False),
#         ("[]", "[]", True),
#         ("aba", "ab", False),
#         ("bab", "bba", True),
#         ("aaaaaba", "aaaaaaa", False),
#         (".,.,.", ".,.,.", True),
#     ],
# )
# def test_is_anagram(str1: str, str2: str, expected: str) -> None:
#     assert is_anagram(str1, str2) == expected
