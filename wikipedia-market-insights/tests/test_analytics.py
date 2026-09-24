"""Unit tests for AnalyticsEngine."""

import unittest
from datetime import datetime
import numpy as np

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from analytics import AnalyticsEngine


class TestAnalyticsEngine(unittest.TestCase):

    def test_filter_complete_months(self):
        items = [
            {"timestamp": "2026070100", "views": 1000},
            {"timestamp": "2026080100", "views": 1100},
            {"timestamp": "2026090100", "views": 200},  # current ongoing month
        ]
        # Simulate current date in Sept 2026
        now = datetime(2026, 9, 23)
        filtered = AnalyticsEngine.filter_complete_months(items, current_date=now)
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[-1]["timestamp"], "2026080100")

    def test_growth_metrics_calculation(self):
        # 24 months of steady 10% annual growth
        items = []
        for i in range(24):
            # year 1: 1000 views/mo, year 2: 1200 views/mo
            views = 1000 if i < 12 else 1200
            items.append({"timestamp": f"202{4 + i//12}{(i%12)+1:02d}0100", "views": views})

        res = AnalyticsEngine.calculate_growth_metrics(items)
        self.assertEqual(res["total_views"], (1000 * 12) + (1200 * 12))
        self.assertAlmostEqual(res["yoy_growth_percent"], 20.0, places=1)
        self.assertIsNotNone(res["cagr_percent"])

    def test_normalized_metrics(self):
        article_items = [
            {"timestamp": "2024010100", "views": 1000},
            {"timestamp": "2024020100", "views": 2000},
        ]
        project_items = [
            {"timestamp": "2024010100", "views": 100_000_000},
            {"timestamp": "2024020100", "views": 200_000_000},
        ]
        norm = AnalyticsEngine.calculate_normalized_metrics(article_items, project_items)
        self.assertEqual(len(norm), 2)
        # 1000 / 100M * 1M = 10.0 views per million
        self.assertAlmostEqual(norm[0]["views_per_million"], 10.0, places=2)
        # 2000 / 200M * 1M = 10.0 views per million
        self.assertAlmostEqual(norm[1]["views_per_million"], 10.0, places=2)

    def test_academic_seasonality_detection(self):
        # Create items with a massive September spike
        items = []
        for year in [2023, 2024]:
            for m in range(1, 13):
                views = 10000 if m == 9 else 1000
                items.append({"timestamp": f"{year}{m:02d}0100", "views": views})

        res = AnalyticsEngine.analyze_seasonality(items)
        self.assertTrue(res["has_strong_seasonality"])
        self.assertEqual(res["peak_month"], "September")
        self.assertTrue(res["is_academic_seasonal"])
        self.assertGreater(res["peak_index"], 2.0)

    def test_spike_concentration_and_anomalies(self):
        # 22 months at 100 views, 2 months at 10,000 views
        items = [{"timestamp": f"2024{i+1:02d}0100", "views": 100} for i in range(22)]
        items.append({"timestamp": "2025110100", "views": 10000})
        items.append({"timestamp": "2025120100", "views": 10000})

        anom = AnalyticsEngine.detect_spikes_and_anomalies(items)
        self.assertTrue(anom["is_spike_dominated"])
        self.assertGreater(anom["top_2_months_share_percent"], 50.0)
        self.assertTrue(len(anom["outliers"]) >= 2)

    def test_trustworthiness_scoring(self):
        growth = {"total_views": 50000, "yoy_growth_percent": 12.0}
        anomalies = {"top_2_months_share_percent": 15.0, "coefficient_of_variation": 0.3}
        seasonality = {"is_academic_seasonal": False, "has_strong_seasonality": False}
        breakdown = {"spider_ratio": 0.10}  # healthy 10% bot traffic

        # Normal healthy topic
        trust = AnalyticsEngine.compute_trustworthiness_score(
            breakdown, growth, anomalies, seasonality, exact_page_exists=True
        )
        self.assertGreaterEqual(trust["trust_score"], 80)
        self.assertEqual(trust["rating"], "HIGH_CONFIDENCE")

        # Academic seasonal topic with high bots
        academic_seasonality = {"is_academic_seasonal": True, "peak_month": "September", "peak_index": 3.0}
        high_bot_breakdown = {"spider_ratio": 0.40}
        trust_academic = AnalyticsEngine.compute_trustworthiness_score(
            high_bot_breakdown, growth, anomalies, academic_seasonality, exact_page_exists=True
        )
        self.assertLess(trust_academic["trust_score"], 75)
        self.assertIn("Academic curriculum seasonality detected", trust_academic["deductions"][1])

        # Missing page
        missing_trust = AnalyticsEngine.compute_trustworthiness_score(
            None, {}, {}, {}, exact_page_exists=False
        )
        self.assertEqual(missing_trust["trust_score"], 0)
        self.assertEqual(missing_trust["rating"], "NO_DIRECT_PAGE")


if __name__ == "__main__":
    unittest.main()
