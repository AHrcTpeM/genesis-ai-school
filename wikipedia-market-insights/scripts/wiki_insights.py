#!/usr/bin/env python3
"""Wikipedia Market Insights CLI for AI Agents.

Unified tool for resolving multi-lingual topics, fetching Wikimedia analytics data,
running statistical analysis, detecting seasonality/anomalies, calculating trust scores,
generating comparison charts, and creating 1-page executive PDF reports.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from .analytics import AnalyticsEngine
    from .report_generator import ReportGenerator
    from .topic_resolver import TopicResolver
    from .visualizer import ChartVisualizer
    from .wikimedia_client import WikimediaClient
except ImportError:
    from analytics import AnalyticsEngine
    from report_generator import ReportGenerator
    from topic_resolver import TopicResolver
    from visualizer import ChartVisualizer
    from wikimedia_client import WikimediaClient


def compute_date_range(period: str, end_date: Optional[str] = None) -> tuple[str, str]:
    """Compute start and end 'YYYYMMDD' strings given period (e.g. '2y', '1y', '6m')."""
    now = datetime.now()
    if end_date:
        end_dt = datetime.strptime(end_date[:8], "%Y%m%d")
    else:
        # Default end is today
        end_dt = now

    if period == "2y":
        # 730 days
        start_dt = end_dt - timedelta(days=730)
    elif period == "1y":
        start_dt = end_dt - timedelta(days=365)
    elif period == "6m":
        start_dt = end_dt - timedelta(days=182)
    elif period == "3y":
        start_dt = end_dt - timedelta(days=1095)
    else:
        logger.warning(f"Unknown period '{period}', falling back to '2y'. Supported: 2y, 1y, 6m, 3y.")
        # Default to 2y
        start_dt = end_dt - timedelta(days=730)

    # First day of the start month to current end
    start_str = start_dt.strftime("%Y%m01")
    end_str = end_dt.strftime("%Y%m%d")
    return start_str, end_str


def analyze_topic(
    topic: str,
    target_langs: List[str],
    period: str = "2y",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    granularity: str = "monthly",
    output_dir: str = ".",
    make_chart: bool = True,
    make_pdf: bool = True,
) -> Dict[str, Any]:
    """Run end-to-end analysis on a topic across specified languages."""
    os.makedirs(output_dir, exist_ok=True)

    client = WikimediaClient()
    resolver = TopicResolver()
    vis = ChartVisualizer(output_dir=output_dir)
    rep_gen = ReportGenerator(output_dir=output_dir)

    # 1. Resolve topic in target languages
    resolved = resolver.resolve_topic_for_languages(topic, target_langs)

    # 2. Compute date range
    if start_date and end_date:
        start_str = start_date[:8]
        end_str = end_date[:8]
    else:
        start_str, end_str = compute_date_range(period, end_date)

    series_by_lang: Dict[str, Dict[str, Any]] = {}
    analysis_by_lang: Dict[str, Dict[str, Any]] = {}
    total_network_views = 0

    for lang in target_langs:
        info = resolved.get(lang, {})
        title = info.get("title")
        exists = info.get("exists", False)

        if not exists or not title:
            analysis_by_lang[lang] = {
                "exists": False,
                "title": None,
                "resolution_method": info.get("method"),
                "notes": info.get("notes"),
                "closest_candidates": info.get("closest_candidates", []),
                "growth": AnalyticsEngine.calculate_growth_metrics([]),
                "trustworthiness": AnalyticsEngine.compute_trustworthiness_score(None, {}, {}, {}, exact_page_exists=False),
                "seasonality": {},
                "anomalies": {},
                "normalized": {},
            }
            continue

        project = f"{lang}.wikipedia"

        # Fetch human views
        raw_user_items = client.get_article_pageviews(
            project=project,
            article=title,
            start=start_str,
            end=end_str,
            granularity=granularity,
            agent="user",
        )
        user_items = AnalyticsEngine.filter_complete_months(raw_user_items)

        # Fetch project total views for normalization
        proj_items = client.get_project_aggregate_views(
            project=project,
            start=start_str,
            end=end_str,
            granularity=granularity,
            agent="user",
        )
        proj_clean = AnalyticsEngine.filter_complete_months(proj_items)

        # Normalized metrics (views per million)
        norm_items = AnalyticsEngine.calculate_normalized_metrics(user_items, proj_clean)

        # Bot traffic breakdown
        traffic_breakdown = client.get_article_traffic_breakdown(
            project=project,
            article=title,
            start=start_str,
            end=end_str,
            granularity=granularity,
        )

        # Analytics calculations
        growth = AnalyticsEngine.calculate_growth_metrics(user_items)
        anomalies = AnalyticsEngine.detect_spikes_and_anomalies(user_items)
        seasonality = AnalyticsEngine.analyze_seasonality(user_items)
        trust = AnalyticsEngine.compute_trustworthiness_score(
            traffic_breakdown, growth, anomalies, seasonality, exact_page_exists=True
        )

        total_network_views += growth.get("total_views", 0)

        # Compute average normalized views per million
        vpm_vals = [it.get("views_per_million", 0.0) for it in norm_items]
        avg_vpm = round(float(sum(vpm_vals) / len(vpm_vals)), 2) if vpm_vals else 0.0

        series_by_lang[lang] = {
            "title": title,
            "items": user_items,
            "normalized_items": norm_items,
        }

        analysis_by_lang[lang] = {
            "exists": True,
            "title": title,
            "resolution_method": info.get("method"),
            "notes": info.get("notes"),
            "growth": growth,
            "normalized": {
                "avg_views_per_million": avg_vpm,
                "latest_month_vpm": vpm_vals[-1] if vpm_vals else 0.0,
            },
            "anomalies": anomalies,
            "seasonality": seasonality,
            "trustworthiness": trust,
        }

    # 3. Market Comparison & Priority Ranking
    ranked_markets = AnalyticsEngine.rank_markets(analysis_by_lang, target_langs)

    # 4. Generate Strategic Findings & Recommendation
    synthesis = AnalyticsEngine.synthesize_findings_and_recommendations(
        topic, target_langs, analysis_by_lang, ranked_markets
    )

    findings = synthesis["findings"]
    rec = synthesis["recommendation"]
    limitations = synthesis["limitations"]
    overall_yoy = synthesis["overall_yoy"]
    overall_trust = synthesis["overall_trust"]
    top_market = synthesis["top_market"]

    # 5. Generate Visual Artifacts
    chart_path = None
    if make_chart:
        chart_filename = f"{topic.lower().replace(' ', '_')}_{'_'.join(target_langs)}_chart.png"
        chart_path = vis.generate_comparison_chart(
            topic=topic,
            series_by_lang=series_by_lang,
            output_filename=chart_filename,
        )

    pdf_path = None
    if make_pdf:
        pdf_filename = f"{topic.lower().replace(' ', '_')}_{'_'.join(target_langs)}_report.pdf"
        kpis = {
            "total_views": total_network_views,
            "yoy_growth": overall_yoy if overall_yoy is not None else "N/A",
            "trust_score": overall_trust if overall_trust is not None else 0,
            "trust_rating": (
                "HIGH_CONFIDENCE" if (overall_trust or 0) >= 80
                else "MODERATE" if (overall_trust or 0) >= 55
                else "LOW_CONFIDENCE"
            ),
            "top_market": top_market,
        }
        pdf_path = rep_gen.generate_pdf_report(
            topic=topic,
            target_langs=target_langs,
            period_str=f"{period.upper()} ({start_str[:4]}-{end_str[:4]})",
            kpis=kpis,
            chart_image_path=chart_path,
            strategic_findings=findings,
            recommendation=rec,
            limitations=limitations,
            output_filename=pdf_filename,
        )

    # 6. Build structured output for Agent
    result = {
        "status": "success",
        "topic": topic,
        "target_languages": target_langs,
        "period": period,
        "date_range": {"start": start_str, "end": end_str},
        "summary": {
            "total_human_views": total_network_views,
            "overall_yoy_growth_percent": overall_yoy,
            "overall_trust_score": overall_trust,
            "top_market_by_mindshare": top_market,
            "recommendation": rec,
        },
        "ranked_markets": ranked_markets,
        "findings": findings,
        "per_language_analysis": analysis_by_lang,
        "artifacts": {
            "chart_png": chart_path,
            "report_pdf": pdf_path,
        },
    }

    client.close()
    resolver.close()

    return result


def main():
    parser = argparse.ArgumentParser(description="Wikipedia Market Insights Skill CLI")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Command: analyze
    analyze_parser = subparsers.add_parser("analyze", help="Analyze topic across languages")
    analyze_parser.add_argument("--topic", required=True, help="Topic name (e.g. 'Intermittent fasting', 'Astronomy')")
    analyze_parser.add_argument("--langs", required=True, help="Comma-separated language codes (e.g. 'pl,cs' or 'uk')")
    analyze_parser.add_argument("--period", default="2y", help="Time period: '2y', '1y', '6m', '3y' (default: 2y)")
    analyze_parser.add_argument("--start", default=None, help="Explicit start date YYYYMMDD")
    analyze_parser.add_argument("--end", default=None, help="Explicit end date YYYYMMDD")
    analyze_parser.add_argument("--granularity", default="monthly", choices=["monthly", "daily"])
    analyze_parser.add_argument("--output-dir", default="./output", help="Directory to save charts and reports")
    analyze_parser.add_argument("--chart", action="store_true", default=True, help="Generate trend chart (default: True)")
    analyze_parser.add_argument("--no-chart", dest="chart", action="store_false", help="Do not generate chart")
    analyze_parser.add_argument("--pdf", action="store_true", default=True, help="Generate 1-page PDF report (default: True)")
    analyze_parser.add_argument("--no-pdf", dest="pdf", action="store_false", help="Do not generate PDF report")

    # Command: resolve
    resolve_parser = subparsers.add_parser("resolve", help="Resolve topic titles across languages")
    resolve_parser.add_argument("--topic", required=True, help="Topic name")
    resolve_parser.add_argument("--langs", required=True, help="Comma-separated language codes")

    args = parser.parse_args()

    if not args.command or args.command == "analyze":
        if not hasattr(args, "topic") or not args.topic:
            parser.print_help()
            sys.exit(1)
        langs = [l.strip().lower() for l in args.langs.split(",") if l.strip()]
        result = analyze_topic(
            topic=args.topic,
            target_langs=langs,
            period=args.period,
            start_date=args.start,
            end_date=args.end,
            granularity=args.granularity,
            output_dir=args.output_dir,
            make_chart=args.chart,
            make_pdf=args.pdf,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "resolve":
        langs = [l.strip().lower() for l in args.langs.split(",") if l.strip()]
        resolver = TopicResolver()
        res = resolver.resolve_topic_for_languages(args.topic, langs)
        print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
