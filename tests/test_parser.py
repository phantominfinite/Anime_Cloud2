import unittest
from app.services.parser import parse_filename

class TestParser(unittest.TestCase):
    def test_standard_format(self):
        filename = "[SubGroup] One Piece - 1010 [1080p].mkv"
        res = parse_filename(filename)
        self.assertEqual(res["title"], "One Piece")
        self.assertEqual(res["episode"], "1010")
        self.assertEqual(res["quality"], "1080p")

    def test_simple_format(self):
        filename = "Naruto Shippuden - 500.mp4"
        res = parse_filename(filename)
        self.assertEqual(res["title"], "Naruto Shippuden")
        self.assertEqual(res["episode"], "500")
        self.assertEqual(res["quality"], "HD") # Default

    def test_space_format(self):
        filename = "Bleach 366.mkv"
        res = parse_filename(filename)
        self.assertEqual(res["title"], "Bleach")
        self.assertEqual(res["episode"], "366")

    def test_quality_detection(self):
        filename = "Anime - 01 [720p].mkv"
        res = parse_filename(filename)
        self.assertEqual(res["quality"], "720p")

if __name__ == '__main__':
    unittest.main()
