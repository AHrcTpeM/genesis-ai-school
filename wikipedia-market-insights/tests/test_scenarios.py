"""End-to-end integration tests for all 3 prompt scenarios."""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from wiki_insights import analyze_topic


class TestPromptScenarios(unittest.TestCase):

    def _verify_single_page_pdf(self, pdf_path: str):
        self.assertTrue(os.path.exists(pdf_path), f"PDF file does not exist: {pdf_path}")
        with open(pdf_path, "rb") as f:
            pages = re.findall(rb"/Type\s*/Page\b", f.read())
        self.assertEqual(len(pages), 1, f"PDF {pdf_path} must be strictly 1 page, found {len(pages)}")

    def test_scenario_1_intermittent_fasting_pl_cs(self):
        """Scenario 1: Intermittent fasting in Polish vs Czech Wikipedia."""
        out_dir = "/tmp/test_scenario_1"
        res = analyze_topic(
            topic="Intermittent fasting",
            target_langs=["pl", "cs"],
            period="2y",
            output_dir=out_dir,
            make_chart=True,
            make_pdf=True,
        )

        self.assertEqual(res["status"], "success")
        self.assertIn("summary", res)
        # Czech must exist, Polish must be missing
        self.assertTrue(res["per_language_analysis"]["cs"]["exists"])
        self.assertFalse(res["per_language_analysis"]["pl"]["exists"])
        self.assertEqual(res["per_language_analysis"]["cs"]["title"], "Přerušovaný půst")

        # Verify artifacts
        self.assertTrue(os.path.exists(res["artifacts"]["chart_png"]))
        self._verify_single_page_pdf(res["artifacts"]["report_pdf"])

    def test_scenario_2_astronomy_uk(self):
        """Scenario 2: Astronomy in Ukrainian Wikipedia (Academic Seasonality)."""
        out_dir = "/tmp/test_scenario_2"
        res = analyze_topic(
            topic="Astronomy",
            target_langs=["uk"],
            period="2y",
            output_dir=out_dir,
            make_chart=True,
            make_pdf=True,
        )

        self.assertEqual(res["status"], "success")
        uk_data = res["per_language_analysis"]["uk"]
        self.assertTrue(uk_data["exists"])
        self.assertEqual(uk_data["title"], "Астрономія")
        # Must detect academic seasonality
        self.assertTrue(uk_data["seasonality"]["is_academic_seasonal"])
        self.assertEqual(uk_data["seasonality"]["peak_month"], "September")
        self.assertGreaterEqual(uk_data["seasonality"]["peak_index"], 2.5)

        # Verify artifacts
        self.assertTrue(os.path.exists(res["artifacts"]["chart_png"]))
        self._verify_single_page_pdf(res["artifacts"]["report_pdf"])

    def test_scenario_3_english_learning(self):
        """Scenario 3: English learning across Ukrainian, Polish, Spanish, and German."""
        out_dir = "/tmp/test_scenario_3"
        res = analyze_topic(
            topic="English language",
            target_langs=["uk", "pl", "es", "de"],
            period="2y",
            output_dir=out_dir,
            make_chart=True,
            make_pdf=True,
        )

        self.assertEqual(res["status"], "success")
        # Ukrainian should lead in normalized mindshare
        ranked = res["ranked_markets"]
        self.assertEqual(ranked[0]["lang"], "uk")
        self.assertGreater(ranked[0]["avg_views_per_million"], 80.0)

        # Verify artifacts
        self.assertTrue(os.path.exists(res["artifacts"]["chart_png"]))
        self._verify_single_page_pdf(res["artifacts"]["report_pdf"])


if __name__ == "__main__":
    unittest.main()
