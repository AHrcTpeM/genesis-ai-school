# Statistical Metrics & Mathematical Formulations Guide

This document explains the statistical foundations implemented in `scripts/analytics.py`.

---

## 1. Growth Metrics

### Year-over-Year (YoY) Growth
Compares the trailing 12 completed months ($V_{\text{last12}}$) against the preceding 12 completed months ($V_{\text{prior12}}$):
$$\text{YoY} = \left( \frac{V_{\text{last12}} - V_{\text{prior12}}}{V_{\text{prior12}}} \right) \times 100\%$$

*Using full 12-month trailing windows eliminates seasonal bias that would distort single-month comparisons.*

### Compound Annual Growth Rate (CAGR)
Measures the annualized growth over a multi-year window of $N$ years:
$$\text{CAGR} = \left( \frac{V_{\text{end}}}{V_{\text{start}}} \right)^{\frac{1}{N}} - 1$$

To avoid endpoint volatility, $V_{\text{start}}$ and $V_{\text{end}}$ are calculated as 6-month smoothed averages.

---

## 2. Market Baseline Normalization

Comparing raw view counts between different Wikipedia language editions produces a heavy distortion because some languages have much larger user bases than others (e.g. Polish Wikipedia has ~3x the traffic of Czech Wikipedia; Spanish has ~7x).

To enable an apples-to-apples comparison, we compute **Views per Million (VPM)**:
$$\text{VPM}_t = \left( \frac{\text{ArticleViews}_t}{\text{TotalProjectViews}_t} \right) \times 1,000,000$$

* **Interpretation**: VPM represents the topic's **relative market mindshare** or the probability that any given Wikipedia session in that language was about this topic.

---

## 3. Anomaly & Outlier Spike Detection

### Interquartile Range (IQR) Rule
Given the first quartile ($Q_1$) and third quartile ($Q_3$):
$$\text{IQR} = Q_3 - Q_1$$
$$\text{Upper Threshold} = Q_3 + 1.5 \times \text{IQR}$$

Any month exceeding the upper threshold is flagged as an outlier.

### Concentration Index
Calculates the proportion of total multi-year traffic concentrated in the top 2 peak months:
$$\text{Spike Concentration} = \left( \frac{V_{\text{top1}} + V_{\text{top2}}}{\sum V} \right) \times 100\%$$

*If the top 2 months account for $> 35\%$ of total 2-year traffic, the trend is classified as **spike-dominated** (driven by viral news, memes, or temporary media coverage rather than sustainable interest).*

---

## 4. Seasonality Profile & Academic Detection

### Monthly Seasonality Index ($S_m$)
For each calendar month $m \in [1..12]$:
$$S_m = \frac{\bar{V}_m}{\bar{V}_{\text{all}}}$$

* $S_m = 1.0$: Traffic is equal to the yearly average.
* $S_m > 1.5$: Strong positive seasonal clustering.

### Academic Curriculum Seasonality Flag
A topic is flagged as `is_academic_seasonal` if:
$$(\text{Peak Month} = \text{September} \land S_9 \ge 2.0) \lor (\text{Peak Month} = \text{May} \land S_5 \ge 2.0)$$
*This identifies topics heavily skewed by student homework assignments (e.g. Astronomy in Ukrainian high schools).*

---

## 5. Trustworthiness Score Formulation

The Trust Score (0 to 100) measures how safely a founder can rely on this data as evidence of genuine commercial B2C market demand.

$$\text{Trust Score} = 100 - \sum \text{Penalties} + \text{Bonus}$$

| Metric | Condition | Deduction / Bonus | Rationale |
| :--- | :--- | :--- | :--- |
| **Bot Traffic** | `spider_ratio > 35%`<br>`spider_ratio > 20%` | -10 to -35 pts<br>-10 pts | Non-human scraper inflation |
| **Spike Concentration** | `top_2_share > 50%`<br>`top_2_share > 35%` | -25 pts<br>-15 pts | One-off viral news spike, not organic intent |
| **Academic Seasonality** | `is_academic_seasonal: True` | -20 pts | Student schoolwork intent, not commercial B2C buyer |
| **Traffic Volatility** | `CV > 1.2`<br>`CV > 0.8` (non-seasonal) | -15 pts<br>-8 pts | Unpredictable, erratic trend |
| **Direct Page Missing** | `exists: False` | Set to 0 pts | No dedicated Wikipedia page in target edition |
| **Stability Bonus** | `5% <= YoY <= 50%` and `CV < 0.6` | +5 pts | Predictable, healthy organic expansion |
