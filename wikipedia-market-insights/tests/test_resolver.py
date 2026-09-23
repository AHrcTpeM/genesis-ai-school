"""Unit tests for TopicResolver."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from topic_resolver import TopicResolver


class TestTopicResolver(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.resolver = TopicResolver()

    def test_direct_match(self):
        res = self.resolver.verify_article_exists("uk", "Астрономія")
        self.assertTrue(res["exists"])
        self.assertEqual(res["canonical_title"], "Астрономія")

    def test_missing_article(self):
        res = self.resolver.verify_article_exists("pl", "NonExistentArticleXYZ12345")
        self.assertFalse(res["exists"])

    def test_intermittent_fasting_resolution(self):
        # Czech should resolve to Přerušovaný půst via Wikidata
        # Polish should be detected as missing_no_page with related candidates
        res = self.resolver.resolve_topic_for_languages("Intermittent fasting", ["pl", "cs"])

        self.assertIn("cs", res)
        self.assertTrue(res["cs"]["exists"])
        self.assertEqual(res["cs"]["title"], "Přerušovaný půst")

        self.assertIn("pl", res)
        self.assertFalse(res["pl"]["exists"])
        self.assertEqual(res["pl"]["method"], "missing_no_page")
        self.assertGreater(len(res["pl"]["closest_candidates"]), 0)


if __name__ == "__main__":
    unittest.main()
