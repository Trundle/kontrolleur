import unittest

from kontrolleur import parse_entries


class TestParseEntries(unittest.TestCase):
    def test_empty(self):
        entries = list(parse_entries([]))
        self.assertEqual(entries, [])

    def test_escaped_linebreak(self):
        entries = list(parse_entries(["foo \\\n", "bar\x00", "spam\x00"]))
        self.assertEqual(entries, ["foo \\\nbar", "spam"])

    def test_string(self):
        entries = list(parse_entries(["'some\n", "string' foobar\x00",
                                      "this 'string\n", "is \\' escaped\n", "!'\x00"]))
        self.assertEqual(entries, ["'some\nstring' foobar",
                                   "this 'string\nis \\' escaped\n!'"])


if __name__ == '__main__':
    unittest.main()
