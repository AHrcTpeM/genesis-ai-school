# AI Product Engineering School — Task 1: Wikipedia Market Insights Skill

This repository contains the complete implementation of **Task 1** for the AI Product Engineering School.

The deliverable is a standalone, specification-compliant [Agent Skill](https://agentskills.io/specification) named **`wikipedia-market-insights`**, located in the `wikipedia-market-insights/` directory.

---

## Quick Navigation

* 📂 **Skill Directory**: [`wikipedia-market-insights/`](wikipedia-market-insights/)
* 📜 **Agent Specification**: [`wikipedia-market-insights/SKILL.md`](wikipedia-market-insights/SKILL.md)
* 🛠️ **CLI Executable**: [`wikipedia-market-insights/scripts/wiki_insights.py`](wikipedia-market-insights/scripts/wiki_insights.py)
* 📊 **Evaluator Harness**: [`wikipedia-market-insights/scripts/eval_openrouter.py`](wikipedia-market-insights/scripts/eval_openrouter.py)
* 📚 **References & Guides**:
  - [API Reference](wikipedia-market-insights/references/API_REFERENCE.md)
  - [Metrics Guide](wikipedia-market-insights/references/METRICS_GUIDE.md)
  - [Interpretation Guide](wikipedia-market-insights/references/INTERPRETATION_GUIDE.md)

---

## Verification & Execution

### 1. Run Unit & Scenario Tests
```bash
python3 -m unittest discover -s wikipedia-market-insights/tests
```

### 2. Run OpenRouter Model Evaluator
```bash
# Evaluates scenarios via OpenRouter using .env credentials
python3 wikipedia-market-insights/scripts/eval_openrouter.py
```

### 3. Run Example Scenarios
```bash
# Scenario 1: Intermittent Fasting (PL vs CS)
python3 wikipedia-market-insights/scripts/wiki_insights.py analyze --topic "Intermittent fasting" --langs pl,cs --period 2y --output-dir ./output/fasting

# Scenario 2: Astronomy Course (UK)
python3 wikipedia-market-insights/scripts/wiki_insights.py analyze --topic "Astronomy" --langs uk --period 2y --output-dir ./output/astronomy

# Scenario 3: Language App Prioritization (UK, PL, ES, DE)
python3 wikipedia-market-insights/scripts/wiki_insights.py analyze --topic "English language" --langs uk,pl,es,de --period 2y --output-dir ./output/english
```

### 4. Generated Deliverables
After executing the scenarios above, the scripts automatically create the `./output/` directory (ignored by Git) and produce:
* **Intermittent Fasting** (`./output/fasting/`):
  * `intermittent_fasting_pl_cs_report.pdf` (1-page executive summary)
  * `intermittent_fasting_pl_cs_chart.png` (2-year normalized trend chart)
* **Astronomy** (`./output/astronomy/`):
  * `astronomy_uk_report.pdf` (1-page executive summary)
  * `astronomy_uk_chart.png` (2-year normalized trend chart)
* **Language App** (`./output/english/`):
  * `english_language_uk_pl_es_de_report.pdf` (1-page executive summary)
  * `english_language_uk_pl_es_de_chart.png` (2-year normalized trend chart)

