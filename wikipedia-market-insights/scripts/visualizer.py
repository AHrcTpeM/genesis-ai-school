"""Chart Visualizer for Wikipedia Market Insights.

Generates polished, publication-ready multi-language comparative trend charts,
normalized mindshare comparisons, and seasonality diagnostics using Matplotlib.
Proportions are optimized for 1-page PDF reports without distortion.
"""

import os
from typing import Any, Dict, List, Optional
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Elegant color palette
PALETTE = ["#2563EB", "#7C3AED", "#059669", "#D97706", "#DC2626", "#0891B2"]


class ChartVisualizer:
    """Renders high-resolution comparative charts for market reports."""

    def __init__(self, output_dir: str = "."):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_comparison_chart(
        self,
        topic: str,
        series_by_lang: Dict[str, Dict[str, Any]],
        output_filename: str = "market_trend.png",
    ) -> str:
        """Create a coordinated 2-panel comparative chart:

        Panel 1: Absolute Monthly Human Views with rolling average.
        Panel 2: Normalized Mindshare (Views per 1M Total Project Views).
        Dimensions (10 x 5.0 in) ensure natural proportions in 1-page reports.
        """
        output_path = os.path.join(self.output_dir, output_filename)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 5.0), sharex=False, dpi=200)
        fig.patch.set_facecolor("#FFFFFF")

        has_data = False

        for idx, (lang, data) in enumerate(series_by_lang.items()):
            color = PALETTE[idx % len(PALETTE)]
            items = data.get("items", [])
            label = f"{lang.upper()} ({data.get('title') or 'No direct page'})"

            if not items:
                continue

            has_data = True
            # Build DataFrame
            records = []
            for it in items:
                ts = str(it.get("timestamp", ""))[:8]
                if len(ts) == 8:
                    records.append({
                        "date": pd.to_datetime(ts, format="%Y%m%d"),
                        "views": it.get("views", 0),
                    })
            if not records:
                continue

            df = pd.DataFrame(records).sort_values("date")
            df["rolling_3m"] = df["views"].rolling(window=3, min_periods=1).mean()

            x_dates = [d.to_pydatetime() for d in df["date"]]
            y_views = df["views"].to_numpy()
            y_rolling = df["rolling_3m"].to_numpy()

            # Plot 1: Absolute Views
            ax1.plot(
                x_dates,
                y_views,
                label=f"{label} (Monthly)",
                color=color,
                alpha=0.45,
                linewidth=1.2,
                marker="o",
                markersize=3.5,
            )
            ax1.plot(
                x_dates,
                y_rolling,
                label=f"{lang.upper()} (3m Trend)",
                color=color,
                linewidth=2.2,
            )

            # Plot 2: Normalized Mindshare
            norm_items = data.get("normalized_items", [])
            if norm_items:
                norm_records = []
                for nit in norm_items:
                    ts = str(nit.get("timestamp", ""))[:8]
                    if len(ts) == 8:
                        norm_records.append({
                            "date": pd.to_datetime(ts, format="%Y%m%d"),
                            "vpm": nit.get("views_per_million", 0.0),
                        })
                if norm_records:
                    ndf = pd.DataFrame(norm_records).sort_values("date")
                    nx_dates = [d.to_pydatetime() for d in ndf["date"]]
                    ny_vpm = ndf["vpm"].to_numpy()
                    ax2.plot(
                        nx_dates,
                        ny_vpm,
                        label=f"{lang.upper()} (Views / 1M Total Wiki Views)",
                        color=color,
                        linewidth=2.0,
                        marker="s",
                        markersize=3.5,
                    )

        # Style Panel 1
        ax1.set_title(
            f"Wikipedia Search Demand Trend: '{topic}'",
            fontsize=11,
            fontweight="bold",
            pad=6,
            color="#111827",
        )
        ax1.set_ylabel("Monthly Human Views", fontsize=8.5, fontweight="semibold", color="#374151")
        ax1.grid(True, linestyle="--", alpha=0.4, color="#E5E7EB")
        ax1.tick_params(colors="#4B5563", labelsize=8)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
        ax1.legend(loc="upper left", frameon=True, facecolor="#F9FAFB", edgecolor="#E5E7EB", fontsize=8)

        # Style Panel 2
        ax2.set_title(
            "Normalized Market Mindshare (Fair Size Comparison)",
            fontsize=10.5,
            fontweight="bold",
            pad=6,
            color="#111827",
        )
        ax2.set_ylabel("Views / 1M Project Views", fontsize=8.5, fontweight="semibold", color="#374151")
        ax2.set_xlabel("Timeline", fontsize=8.5, fontweight="semibold", color="#374151")
        ax2.grid(True, linestyle="--", alpha=0.4, color="#E5E7EB")
        ax2.tick_params(colors="#4B5563", labelsize=8)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
        ax2.legend(loc="upper left", frameon=True, facecolor="#F9FAFB", edgecolor="#E5E7EB", fontsize=8)

        if not has_data:
            ax1.text(0.5, 0.5, "No pageview data available for selected topics", ha="center", va="center")
            ax2.text(0.5, 0.5, "No normalized data available", ha="center", va="center")

        plt.tight_layout(pad=1.2)
        plt.savefig(output_path, dpi=200, bbox_inches="tight")
        plt.close(fig)

        return output_path

    def generate_single_topic_diagnostics(
        self,
        topic: str,
        lang: str,
        items: List[Dict[str, Any]],
        seasonality: Dict[str, Any],
        traffic_breakdown: Optional[Dict[str, Any]],
        output_filename: str = "topic_diagnostics.png",
    ) -> str:
        """Create diagnostics chart for a single topic:

        Panel 1: Human Traffic vs Spider/Crawler Traffic.
        Panel 2: Seasonality Monthly Index Profile.
        """
        output_path = os.path.join(self.output_dir, output_filename)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2), dpi=200)
        fig.patch.set_facecolor("#FFFFFF")

        # Panel 1: Human vs Spider
        if traffic_breakdown:
            u_views = traffic_breakdown.get("total_user_views", 0)
            s_views = traffic_breakdown.get("total_spider_views", 0)
            labels = ["Human Readers", "Crawlers / Spiders"]
            sizes = [max(1, u_views), max(0, s_views)]
            colors = ["#2563EB", "#F59E0B"]
            ax1.pie(
                sizes,
                labels=labels,
                autopct="%1.1f%%",
                startangle=140,
                colors=colors,
                wedgeprops={"edgecolor": "white", "linewidth": 2},
                textprops={"fontsize": 8.5, "fontweight": "medium"},
            )
            ax1.set_title(f"Traffic Integrity ({lang.upper()})", fontsize=10.5, fontweight="bold", pad=6)
        else:
            ax1.text(0.5, 0.5, "No bot breakdown available", ha="center", va="center")

        # Panel 2: Monthly Seasonality Index
        indices = seasonality.get("monthly_indices", {})
        if indices:
            months = list(indices.keys())
            short_months = [m[:3] for m in months]
            vals = list(indices.values())
            bar_colors = ["#DC2626" if v >= 2.0 else "#2563EB" if v >= 1.0 else "#94A3B8" for v in vals]
            ax2.bar(short_months, vals, color=bar_colors, width=0.6)
            ax2.axhline(1.0, color="#64748B", linestyle="--", linewidth=1.2, label="Yearly Average (1.0x)")
            ax2.set_ylabel("Seasonality Multiplier", fontsize=8.5, fontweight="semibold")
            ax2.set_title(f"Annual Seasonality Profile ({lang.upper()})", fontsize=10.5, fontweight="bold", pad=6)
            ax2.grid(True, axis="y", linestyle="--", alpha=0.4)
            ax2.legend(fontsize=8, loc="upper right")
            ax2.tick_params(labelsize=8)
        else:
            ax2.text(0.5, 0.5, "Insufficient months for seasonality profile", ha="center", va="center")

        plt.tight_layout(pad=1.2)
        plt.savefig(output_path, dpi=200, bbox_inches="tight")
        plt.close(fig)

        return output_path
