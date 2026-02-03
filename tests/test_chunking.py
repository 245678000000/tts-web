import unittest

from tts_service import split_text_into_chunks


class TestChunking(unittest.TestCase):
    def test_empty_text(self):
        self.assertEqual(split_text_into_chunks("", max_chars=10), [])

    def test_punctuation_boundary_chunking(self):
        text = "第一句。第二句！第三句？第四句；第五句。"
        chunks = split_text_into_chunks(text, max_chars=8)
        self.assertTrue(all(len(chunk) <= 8 for chunk in chunks))
        self.assertEqual("".join(chunks), text)

    def test_hard_split_for_long_sentence(self):
        text = "a" * 25
        chunks = split_text_into_chunks(text, max_chars=10)
        self.assertEqual(chunks, ["a" * 10, "a" * 10, "a" * 5])

    def test_newline_and_mixed_symbols(self):
        text = "第一段第一句。\n第一段第二句！\n第二段。"
        chunks = split_text_into_chunks(text, max_chars=12)
        self.assertTrue(all(len(chunk) <= 12 for chunk in chunks))
        self.assertEqual("".join(chunks), text.replace("\r\n", "\n"))


if __name__ == "__main__":
    unittest.main()
