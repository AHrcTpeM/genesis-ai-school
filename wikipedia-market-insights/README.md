# Wikipedia Market Insights — Agent Skill

A production-grade, standalone Agent Skill adhering to the [Agent Skills specification](https://agentskills.io/specification). It enables AI agents to analyze Wikimedia page views data, evaluate B2C product demand, detect seasonality and bot anomalies, and produce publication-ready comparative charts and 1-page executive PDF reports.

---

## 🌟 Core Highlights

* **100% Deterministic Execution**: All data fetching, caching, statistical anomaly detection, chart plotting, and PDF generation are executed by modular Python scripts. The LLM agent receives structured, compact JSON (< 500–1500 tokens) to reason and communicate without hallucinating numbers.
* **Language & Population Normalization**: Normalizes raw views against total project traffic (Views per Million total wiki views) so that a smaller market (e.g. Czechia with 10M population) is fairly compared to larger ones (Poland, Germany).
* **Bot & Crawler Isolation**: Queries real human readers (`agent=user`) while calculating the crawler ratio (`agent=spider`) to penalize artificial bot surges.
* **Academic Seasonality Trap Detection**: Automatically flags school curriculum spikes (e.g. high school astronomy in Ukraine spiking in September) and discounts them from commercial B2C intent.
* **Concept & Missing Page Resolution**: Uses Wikidata sitelinks and MediaWiki `langlinks` to map topics across languages, cleanly flagging when a language lacks a dedicated article (e.g. Polish Wikipedia lacking a standalone article for intermittent fasting).
* **Strictly 1-Page Executive PDF Report**: Generates an A4 portrait PDF with KPI scorecards, embedded chart, bulleted findings, and founder recommendations with full Cyrillic and Latin Unicode support.
* **Engineered for Fast/Cheap Models**: Operates efficiently on models like Claude 3.5 Haiku, Llama 3.2 3B, or free OpenRouter models.

---

## 📁 Repository Structure

```
wikipedia-market-insights/
├── SKILL.md                          # Agent Skill specification (YAML frontmatter + prompt guide)
├── README.md                         # Project documentation and quickstart
├── requirements.txt                  # Python dependencies
├── scripts/
│   ├── __init__.py
│   ├── wiki_insights.py              # Unified CLI entrypoint for agents
│   ├── wikimedia_client.py           # Wikimedia Pageviews client with local caching & bot breakdown
│   ├── topic_resolver.py             # Multi-language concept resolver (MediaWiki + Wikidata)
│   ├── analytics.py                  # Statistical engine: YoY, CAGR, normalization, anomaly & trust scoring
│   ├── visualizer.py                 # Matplotlib charts (time series, rolling trends, normalized mindshare)
│   ├── report_generator.py           # ReportLab 1-page executive PDF generator (Unicode DejaVu font)
│   └── eval_openrouter.py            # Evaluation harness for testing on cheap/free LLM models
├── references/
│   ├── API_REFERENCE.md              # Wikimedia Analytics API endpoints & schemas
│   ├── METRICS_GUIDE.md              # Mathematical formulas (YoY, CAGR, Z-score, Trust Score)
│   └── INTERPRETATION_GUIDE.md       # B2C product decision heuristics & triangulation guide
├── assets/
│   └── fonts/                        # Bundled DejaVuSans TrueType fonts for reproducible Unicode PDF rendering
├── tests/
│   ├── test_analytics.py             # Unit tests for analytics & trust scoring
│   ├── test_resolver.py              # Unit tests for multi-language topic resolution
│   └── test_scenarios.py             # Integration tests for all 3 prompt scenarios
└── .cache/                           # Local disk cache for fast repeated queries
```

---

## 🚀 Quickstart

### 1. Environment Setup
```bash
# Optional: create virtual environment
python3 -m venv venv && source venv/bin/activate

# Install dependencies
pip install -r wikipedia-market-insights/requirements.txt
```

### 2. Run Example Scenarios

#### Scenario 1: Intermittent Fasting (Polish vs. Czech Wikipedia)
```bash
python3 wikipedia-market-insights/scripts/wiki_insights.py analyze \
  --topic "Intermittent fasting" \
  --langs pl,cs \
  --period 2y \
  --output-dir ./output/fasting
```
*Identifies that Polish Wikipedia lacks a dedicated standalone article (`missing_no_page`), while Czech has `Přerušovaný půst` with 6.9k views and a 100/100 trust score.*

#### Scenario 2: Astronomy Course Demand & Trust (Ukrainian Wikipedia)
```bash
python3 wikipedia-market-insights/scripts/wiki_insights.py analyze \
  --topic "Astronomy" \
  --langs uk \
  --period 2y \
  --output-dir ./output/astronomy
```
*Identifies `Астрономія`, detects the massive September academic curriculum spike (3.26x baseline), penalizes commercial trust to 70/100, and warns about the summer drop.*

#### Scenario 3: Language Learning App Prioritization
```bash
python3 wikipedia-market-insights/scripts/wiki_insights.py analyze \
  --topic "English language" \
  --langs uk,pl,es,de \
  --period 2y \
  --output-dir ./output/english
```
*Ranks target markets: Ukrainian leads in normalized urgency (127 views/1M wiki views, ~3x higher than Western Europe), while Spanish leads in total addressable scale (751k views).*

---

## 🧪 Running Automated Tests

Run the complete test suite:
```bash
python3 -m unittest discover -s wikipedia-market-insights/tests
```

Run the OpenRouter model evaluation harness:
```bash
# Automatic mode (reads OPENROUTER_API_KEY and OPENROUTER_MODEL from .env file)
python3 wikipedia-market-insights/scripts/eval_openrouter.py

# Live mode with specific model override
python3 wikipedia-market-insights/scripts/eval_openrouter.py --model "openrouter/free"
```

---

## 📈 Iterative Scaling Roadmap

To expand the skill for larger datasets and deeper research:

1. **Category & Topic Hierarchy Expansion**:
   - Use the MediaWiki `categorymembers` API or Wikidata SPARQL queries (`wdt:P31` instance of, `wdt:P279` subclass of) to analyze an entire thematic domain (e.g., all 50 articles in the "Astronomy" or "Fitness diets" category) and generate aggregate domain market indices.
2. **Geographic Breakdown via Country Endpoint**:
   - Integrate the Wikimedia `/pageviews/top-by-country/{project}/{access}/{year}/{month}` endpoint to differentiate which countries read a given language edition (e.g. analyzing Spanish traffic from Spain vs. Mexico vs. Colombia).
3. **Batch Processing & Wikimedia Data Dumps**:
   - For queries spanning 1,000+ keywords, migrate from REST API to Wikimedia Pageviews hourly/daily public dumps on AWS S3/Google Cloud BigQuery (`bigquery-public-data.wikimedia_pageviews`).
4. **Multi-Source Triangulation**:
   - Integrate Google Trends (Pytrends) and Reddit/App Store review volume side-by-side to correlate Wikipedia awareness with commercial search and intent to pay.
