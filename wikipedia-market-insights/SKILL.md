---
name: wikipedia-market-insights
description: Analyze Wikipedia page views data to evaluate B2C product demand across topics and languages, detect seasonal and academic spikes, assess trend reliability (trust score), and generate comparative charts and 1-page PDF executive reports. Use when founders or product teams need to validate course demand, prioritize localization languages, or verify organic interest trends using Wikimedia analytics.
license: MIT
compatibility: Requires Python 3.9+ with requests, matplotlib, pandas, numpy, reportlab
metadata:
  version: "1.0.0"
  category: "market-research"
  author: "Product Engineering Team"
---

# Wikipedia Market Insights Agent Skill

This skill empowers AI agents to validate B2C product ideas, evaluate educational course demand, and prioritize language localization by analyzing historical Wikimedia page views.

> 🚨 **STRICT OPERATING RULE**: Follow skill instructions strictly. **NO OVER-ENGINEERING**. Do NOT write custom Python scripts, ad-hoc API callers, or manual scrapers. Rely solely on the provided self-contained CLI executable (`scripts/wiki_insights.py`) and follow the 5-step Agent Decision Workflow.

It addresses common analytical traps:

1. **Language & Population Disparity**: Normalizes raw views against total project traffic (views per million total wiki visits) so a smaller market like Czechia is fairly compared to a larger market like Poland or Germany.
2. **Academic & School Seasonality**: Automatically detects September/May school curriculum spikes (e.g., high school astronomy in Ukraine) and discounts them from commercial B2C intent.
3. **Bot & Crawler Traffic**: Queries real humans (`agent=user`) while tracking crawler proportions (`agent=spider`) to penalize artificial bot surges.
4. **Missing Concept Handling**: Uses Wikidata sitelinks and MediaWiki `langlinks` to resolve cross-language titles and explicitly detects when a direct concept does not exist (e.g. Polish Wikipedia lacking a standalone article for intermittent fasting).

---

## Quick Execution Commands

The skill provides a self-contained CLI executable at `scripts/wiki_insights.py`. Agents should execute this script using Bash or terminal tools.

### 0. Environment & Dependency Check (Pre-Flight)

Before first execution, verify Python 3 and required libraries:

```bash
python3 -c "import requests, matplotlib, pandas, numpy, reportlab" 2>/dev/null || pip install -r requirements.txt
```

### 1. Stage 1: Topic Resolution Pre-Check (Mandatory First Step)

```bash
python3 scripts/wiki_insights.py resolve \
  --topic "Intermittent fasting" \
  --langs pl,cs
```

### 2. Stage 2: Deep Analytics Execution

#### Scenario A: Direct/Sitelink Match Exists for All Languages

```bash
python3 scripts/wiki_insights.py analyze \
  --topic "Intermittent fasting" \
  --langs pl,cs \
  --period 2y \
  --output-dir ./output/fasting
```

> **Token budget tip**: Add `--compact` to strip raw monthly arrays from JSON output (~1-2k tokens vs ~8-12k). Recommended when using small-context models (Llama 3B, Gemini Flash free tier):
>
> ```bash
> python3 scripts/wiki_insights.py analyze --topic "..." --langs pl,cs --period 2y --compact
> ```

#### Scenario B: Missing Direct Article for a Language (Smart Proxy Fallback)

If `resolve` shows `exists: false` for a language (e.g., `pl`), analyze direct-match languages first, then evaluate `closest_candidates`, select the most relevant proxy concept (e.g. `Głodówka lecznicza`), and run `analyze` for that proxy concept:

```bash
# 1. Analyze exact match language(s)
python3 scripts/wiki_insights.py analyze \
  --topic "Intermittent fasting" \
  --langs cs \
  --period 2y \
  --output-dir ./output/fasting_cs \
  --chart \
  --pdf

# 2. Analyze selected proxy concept for missing language(s)
python3 scripts/wiki_insights.py analyze \
  --topic "Głodówka lecznicza" \
  --langs pl \
  --period 2y \
  --output-dir ./output/fasting_pl_proxy \
  --chart \
  --pdf
```

---

## Agent Decision Workflow

Follow this 5-step workflow when answering founder questions:

```
[User Request]
      │
      ▼
0. Environment Pre-Flight Check:
   ├── Verify dependencies: python3 -c "import requests, matplotlib, pandas, numpy, reportlab"
   └── If missing: propose running 'pip install -r requirements.txt' to user
      │
      ▼
1. Extract Topic & Languages (e.g., 'astronomy', 'uk')
      │
      ▼
2. Resolve Topic Across Target Languages (`scripts/wiki_insights.py resolve ...`)
   ├── If `exists: true` for all → proceed with original topic.
   └── If `exists: false` for any lang → select best candidate from `closest_candidates` as proxy.
      │
      ▼
3. Run CLI Analytics (`scripts/wiki_insights.py analyze ...`)
   ├── Run for exact topic on direct-match languages.
   └── Run for proxy concept on missing-page language(s).
      │
      ▼
4. Parse JSON Output:
   ├── Check `per_language_analysis[lang].exists`: Is there a direct page?
   ├── Check `summary.overall_trust_score`: Is the score >= 75?
   ├── Check `seasonality.is_academic_seasonal`: Is growth driven by school homework?
   └── Check `ranked_markets`: Which market has highest normalized mindshare?
      │
      ▼
5. Formulate Founder Response:
   ├── Direct Answer (Yes / No / Proceed with Caution)
   ├── Key Numbers (Human Views, YoY %, Mindshare VPM, Trust Score)
   ├── Critical Caveats (Seasonality, Bot Ratio, Proxy Disclaimer if applicable)
   └── Deliver Artifacts (Clickable links to generated PNG chart and 1-page PDF report)
```

---

## Interpreting Output Metrics

### 1. Normalized Market Mindshare (`avg_views_per_million`)

- **What it is**: `(article_views / total_project_views) * 1,000,000`
- **Why it matters**: Absolute pageviews favor giant languages (Spanish, German). Normalized mindshare reflects **intensity of interest** relative to the total internet population in that language.
- **Benchmark**:
  - `> 100 vpm`: Massive core interest (e.g. English language in Ukraine ~127 vpm).
  - `20 - 100 vpm`: Solid mainstream topic (e.g. English in Spain ~50 vpm).
  - `< 10 vpm`: Specialized niche or emerging interest.

### 2. Trustworthiness Score (0 to 100)

- **80 - 100 (HIGH_CONFIDENCE)**: Steady, human-driven traffic with consistent demand. Reliable for B2C product validation.
- **55 - 79 (MODERATE_CONFIDENCE)**: Real interest exists, but seasonal swings, media spikes, or curriculum patterns are present. Verify willingness to pay before large investments.
- **0 - 54 (LOW_CONFIDENCE)**: Significant risk of false signal (e.g. bot-inflated, one-off viral spike, or missing direct article).

### 3. Seasonality & The "School Homework" Trap

- If `is_academic_seasonal: true` (huge September or May peak):
  - In educational topics, September spikes mean **students looking up school subjects**, NOT adults ready to buy an online course.
  - Advise the founder to either:
    1. Pivot the product to high-school exam prep (e.g. ZNO/NMT prep in Ukraine).
    2. Discount the September spike and evaluate the base volume during winter/spring months.

### 4. Missing Direct Page (`exists: false`) & Smart Proxy Fallback

- If an article does not exist on a target Wikipedia (e.g. Polish `Intermittent fasting`):
  - Do NOT give up or leave the founder with 0 views.
  - **NO OVER-ENGINEERING RULE**: Do NOT write custom Python scripts, curl/API requests, or extra code to evaluate candidates. The `resolve` command has ALREADY fetched `closest_candidates`.
  - Select the single most semantically relevant candidate title **directly from the `closest_candidates` array** in the JSON output (e.g. from `["Stres oksydacyjny", "Głodówka lecznicza", "Paleolityczny styl życia"]`, select `"Głodówka lecznicza"`).
  - Immediately execute `python3 scripts/wiki_insights.py analyze --topic "<selected_candidate>" --langs <lang>` for that proxy concept.
  - In the response, explicitly state:
    > ⚠️ **Proxy Topic Disclaimer**: Direct article for '[Topic]' does not exist on [lang].wikipedia. Analyzed closest proxy concept '[Proxy Title]' to estimate regional demand in the broader category.

---

## Handling Follow-up & Iterative Queries

Users often refine their questions after an initial answer (e.g. "Now compare that for German", "What about over 3 years?"). Follow these rules:

1. **New language added** → Run `analyze` again with the extended `--langs` list. Cache ensures previously fetched data is reused from disk; only the new language incurs network cost.
2. **Different period requested** → Re-run `analyze` with the new `--period` value. Pass `--no-chart --no-pdf` if the user only wants updated numbers without new artifacts.
3. **Proxy topic comparison** → If user asks "compare that proxy concept too", run a second `analyze` call with `--topic "<proxy>" --langs <lang>` and present both results side by side.
4. **"What if I filter out the September spike?"** → Advise the founder to look at `monthly_indices` in the full output (rerun without `--compact`) and manually compare summer/winter months vs. the September peak month.
5. **Do NOT re-run if**: The user is only asking for a reinterpretation of already-provided data. In that case, reason directly from the JSON you already have in context.

---

## Generated Artifacts

Each analysis run creates two persistent files in `--output-dir`:

1. **`<topic>_<langs>_chart.png`**: High-resolution 2-panel chart showing absolute views with 3-month rolling trendline, and normalized mindshare comparison. Filename uses lowercase with underscores, e.g. `intermittent_fasting_pl_cs_chart.png`.
2. **`<topic>_<langs>_report.pdf`**: Publication-ready, strictly **1-page executive PDF report** featuring KPI scorecards, embedded chart, bulleted findings, founder takeaway, and methodology caveats. E.g. `intermittent_fasting_pl_cs_report.pdf`.

---

## Reference Documentation

For deeper details, consult the reference guides in `references/`:

- [API Reference](references/API_REFERENCE.md): Wikimedia Analytics API endpoints, parameters, and rate-limiting.
- [Metrics Guide](references/METRICS_GUIDE.md): Mathematical definitions for CAGR, YoY, Z-Score outlier detection, and Trust Score.
- [Interpretation Guide](references/INTERPRETATION_GUIDE.md): B2C go-to-market heuristics, interview tips, and triangulation strategies.
