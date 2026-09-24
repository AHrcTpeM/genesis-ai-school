"""Statistical Analytics Engine for Wikipedia Pageviews.

Calculates growth rates (YoY, CAGR, MoM), market normalization (views per million),
anomaly/spike detection, seasonality decomposition, and a comprehensive Trustworthiness Score.
"""

import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


class AnalyticsEngine:
    """Analyzes time series of Wikipedia pageviews for market insight."""

    @staticmethod
    def filter_complete_months(
        items: List[Dict[str, Any]],
        current_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Filter out the currently incomplete month from monthly items.

        If current date is Sept 23, 2026, the item for 2026090100 is partial.
        """
        if not items:
            return []

        now = current_date or datetime.now()
        current_ym = now.strftime("%Y%m")

        clean_items = []
        for it in items:
            ts = str(it.get("timestamp", ""))[:6]
            # If item matches ongoing current month, skip it for monthly calculations
            if ts == current_ym:
                continue
            clean_items.append(it)
        return sorted(clean_items, key=lambda x: str(x.get("timestamp", "")))

    @classmethod
    def calculate_growth_metrics(cls, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate total views, YoY growth, recent momentum, and CAGR."""
        if not items:
            return {
                "total_views": 0,
                "avg_monthly_views": 0.0,
                "median_monthly_views": 0.0,
                "yoy_growth_percent": None,
                "recent_momentum_percent": None,
                "cagr_percent": None,
                "num_months": 0,
            }

        views = [it.get("views", 0) for it in items]
        n = len(views)
        total_views = sum(views)
        avg_views = float(np.mean(views))
        median_views = float(np.median(views))

        # Year-over-Year (YoY): compare last 12 months vs previous 12 months
        yoy_growth = None
        if n >= 24:
            recent_12 = sum(views[-12:])
            prior_12 = sum(views[-24:-12])
            if prior_12 > 0:
                yoy_growth = round(((recent_12 - prior_12) / prior_12) * 100, 2)
        elif n >= 13:
            # Compare same month a year ago
            recent_m = views[-1]
            prior_m = views[-13]
            if prior_m > 0:
                yoy_growth = round(((recent_m - prior_m) / prior_m) * 100, 2)

        # Recent 3-month momentum vs prior 3-month period
        momentum = None
        if n >= 6:
            recent_3 = sum(views[-3:])
            prior_3 = sum(views[-6:-3])
            if prior_3 > 0:
                momentum = round(((recent_3 - prior_3) / prior_3) * 100, 2)

        # CAGR over full multi-year span
        cagr = None
        if n >= 24:
            years = n / 12.0
            start_val = max(1, np.mean(views[:6]))
            end_val = max(1, np.mean(views[-6:]))
            if start_val > 0 and end_val > 0:
                cagr_val = ((end_val / start_val) ** (1.0 / years)) - 1.0
                cagr = round(cagr_val * 100, 2)

        return {
            "total_views": total_views,
            "avg_monthly_views": round(avg_views, 1),
            "median_monthly_views": round(median_views, 1),
            "yoy_growth_percent": yoy_growth,
            "recent_momentum_percent": momentum,
            "cagr_percent": cagr,
            "num_months": n,
        }

    @classmethod
    def calculate_normalized_metrics(
        cls,
        article_items: List[Dict[str, Any]],
        project_items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Compute normalized views per million total wiki project views."""
        project_map = {str(it.get("timestamp", ""))[:6]: it.get("views", 1) for it in project_items}

        normalized = []
        for it in article_items:
            ts = str(it.get("timestamp", ""))[:6]
            art_views = it.get("views", 0)
            proj_views = project_map.get(ts, 0)
            views_per_million = (art_views / proj_views * 1_000_000) if proj_views > 0 else 0.0

            normalized.append({
                "timestamp": it.get("timestamp"),
                "month": ts,
                "views": art_views,
                "project_views": proj_views,
                "views_per_million": round(views_per_million, 3),
            })
        return normalized

    @classmethod
    def detect_spikes_and_anomalies(cls, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect outliers using IQR and Z-score and compute concentration ratio."""
        if not items or len(items) < 4:
            return {
                "outliers": [],
                "top_2_months_share_percent": 0.0,
                "is_spike_dominated": False,
                "coefficient_of_variation": 0.0,
            }

        views = [it.get("views", 0) for it in items]
        total_views = sum(views) if sum(views) > 0 else 1
        q75, q25 = np.percentile(views, [75, 25])
        iqr = q75 - q25
        upper_threshold = q75 + (1.5 * iqr)

        mean_val = np.mean(views)
        std_val = np.std(views)
        cv = (std_val / mean_val) if mean_val > 0 else 0.0

        outliers = []
        for it in items:
            v = it.get("views", 0)
            z_score = ((v - mean_val) / std_val) if std_val > 0 else 0.0
            if v > upper_threshold or z_score > 2.5:
                outliers.append({
                    "timestamp": it.get("timestamp"),
                    "month": str(it.get("timestamp", ""))[:6],
                    "views": v,
                    "z_score": round(z_score, 2),
                    "ratio_to_median": round(v / max(1, np.median(views)), 2),
                })

        sorted_views = sorted(views, reverse=True)
        top_2_sum = sum(sorted_views[:2])
        top_2_share = round((top_2_sum / total_views) * 100, 2)
        is_spike_dominated = top_2_share > 35.0

        return {
            "outliers": outliers,
            "top_2_months_share_percent": top_2_share,
            "is_spike_dominated": is_spike_dominated,
            "coefficient_of_variation": round(cv, 2),
        }

    @classmethod
    def analyze_seasonality(cls, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute monthly seasonality index and detect academic/calendar peaks."""
        if not items or len(items) < 12:
            return {
                "has_strong_seasonality": False,
                "peak_month": None,
                "peak_index": 1.0,
                "monthly_indices": {},
                "is_academic_seasonal": False,
            }

        month_views: Dict[int, List[int]] = {m: [] for m in range(1, 13)}
        for it in items:
            ts = str(it.get("timestamp", ""))
            if len(ts) >= 6:
                m = int(ts[4:6])
                month_views[m].append(it.get("views", 0))

        overall_mean = np.mean([it.get("views", 0) for it in items])
        if overall_mean <= 0:
            return {
                "has_strong_seasonality": False,
                "peak_month": None,
                "peak_index": 1.0,
                "monthly_indices": {},
                "is_academic_seasonal": False,
            }

        monthly_indices: Dict[int, float] = {}
        for m, vals in month_views.items():
            if vals:
                monthly_indices[m] = round(float(np.mean(vals) / overall_mean), 2)
            else:
                monthly_indices[m] = 1.0

        peak_m = max(monthly_indices, key=lambda m: monthly_indices[m])
        peak_idx = monthly_indices[peak_m]

        # Academic seasonality: September (m=9) or May (m=5) peak index >= 2.0
        # typical of school curriculum subjects like Astronomy in Ukraine
        is_academic = (peak_m == 9 and peak_idx >= 2.0) or (peak_m == 5 and peak_idx >= 2.0)
        has_strong_seasonality = peak_idx >= 1.6

        month_names = {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August",
            9: "September", 10: "October", 11: "November", 12: "December"
        }

        return {
            "has_strong_seasonality": has_strong_seasonality,
            "peak_month_num": peak_m,
            "peak_month": month_names.get(peak_m, str(peak_m)),
            "peak_index": peak_idx,
            "monthly_indices": {month_names[k]: v for k, v in monthly_indices.items()},
            "is_academic_seasonal": is_academic,
        }

    @classmethod
    def compute_trustworthiness_score(
        cls,
        traffic_breakdown: Optional[Dict[str, Any]],
        growth_metrics: Dict[str, Any],
        anomalies: Dict[str, Any],
        seasonality: Dict[str, Any],
        exact_page_exists: bool = True,
    ) -> Dict[str, Any]:
        """Calculate Trustworthiness Score (0 to 100) and commercial conversion rating."""
        if not exact_page_exists:
            return {
                "trust_score": 0,
                "rating": "NO_DIRECT_PAGE",
                "explanation": "No direct Wikipedia article exists for this topic in this language edition.",
                "bot_ratio_percent": 0.0,
                "deductions": ["Direct article missing (-100)"],
            }

        score = 100.0
        deductions = []

        # 1. Bot / Spider Traffic Penalty
        spider_ratio = 0.0
        if traffic_breakdown:
            spider_ratio = traffic_breakdown.get("spider_ratio", 0.0)
            spider_pct = round(spider_ratio * 100, 1)
            if spider_ratio > 0.35:
                penalty = min(35.0, (spider_ratio - 0.20) * 100)
                score -= penalty
                deductions.append(f"High crawler/bot traffic ({spider_pct}%, penalty -{penalty:.0f})")
            elif spider_ratio > 0.20:
                penalty = 10.0
                score -= penalty
                deductions.append(f"Moderate bot traffic ({spider_pct}%, penalty -10)")

        # 2. Outlier Spike Penalty (Viral news vs organic interest)
        spike_share = anomalies.get("top_2_months_share_percent", 0.0)
        if spike_share > 50.0:
            score -= 25.0
            deductions.append(f"Extreme spike concentration (top 2 months = {spike_share}% of all views, -25)")
        elif spike_share > 35.0:
            score -= 15.0
            deductions.append(f"Notable spike concentration ({spike_share}% in top 2 months, -15)")

        # 3. Academic Seasonality Penalty (Commercial B2C Intent Caveat)
        if seasonality.get("is_academic_seasonal", False):
            score -= 20.0
            peak_m = seasonality.get("peak_month", "September")
            idx = seasonality.get("peak_index", 2.0)
            deductions.append(
                f"Academic curriculum seasonality detected ({peak_m} index = {idx}x baseline, student homework skew, -20)"
            )

        # 4. Volatility Penalty
        cv = anomalies.get("coefficient_of_variation", 0.0)
        if cv > 1.2:
            score -= 15.0
            deductions.append(f"Erratic traffic volume (CV = {cv}, -15)")
        elif cv > 0.8 and not seasonality.get("has_strong_seasonality", False):
            score -= 8.0
            deductions.append(f"High volatility without seasonal pattern (CV = {cv}, -8)")

        # 5. Stability Reward
        yoy = growth_metrics.get("yoy_growth_percent")
        if yoy is not None and 5.0 <= yoy <= 50.0 and cv < 0.6:
            score = min(100.0, score + 5.0)

        final_score = int(max(0, min(100, round(score))))

        if final_score >= 80:
            rating = "HIGH_CONFIDENCE"
            explanation = "Steady, human-driven traffic with reliable sustained audience interest."
        elif final_score >= 55:
            rating = "MODERATE_CONFIDENCE"
            explanation = "Interest is genuine but subject to seasonal fluctuations, media spikes, or curriculum patterns."
        else:
            rating = "LOW_CONFIDENCE"
            explanation = "High risk of false signal: traffic is distorted by school homework cycles, bots, or ephemeral spikes."

        return {
            "trust_score": final_score,
            "rating": rating,
            "explanation": explanation,
            "bot_ratio_percent": round(spider_ratio * 100, 1),
            "deductions": deductions,
        }
