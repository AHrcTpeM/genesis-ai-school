# B2C Product Decision & Market Validation Guide

This guide outlines heuristics for founders and AI agents to transform Wikipedia analytics into sound product investment decisions.

---

## 1. Intent Mapping: Wikipedia vs. Commercial Demand

Wikipedia data measures **Aggregate Informational Curiosity**. It is one of the earliest leading indicators in the customer discovery funnel:

```
[Unconscious Need] 
       │
       ▼
[Wikipedia Lookup] ◄── WHAT THIS SKILL MEASURES
       │                (Broad awareness, cultural interest, curiosity)
       ▼
[Commercial Search] ◄── Google Trends, Amazon / App Store queries
       │                (Evaluating specific solutions, apps, courses)
       ▼
[Transaction / Purchase] ◄── Willingness to pay (Credit card conversion)
```

### When Wikipedia Interest Strongly Correlates with Commercial Success:
1. **New Consumer Habits & Lifestyle shifts**: e.g., Intermittent fasting, Pilates, Air fryers, EV charging.
2. **Language & Regional Education**: Languages where people actively seek self-improvement (e.g. English learning in Ukraine).
3. **Emerging Tech & Professional Skills**: Python, Prompt engineering, Data analysis.

### When Wikipedia Interest Diverges from Commercial Success (False Signals):
1. **Academic School Curricula**: Astronomy, World War II history, Cell biology. High peaks in September/May are driven by high school students looking up homework answers with zero budget or willingness to pay.
2. **Ephemeral Celebrity/Tragedy News**: A news spike when a prominent scientist or actor passes away causes massive 48-hour pageviews that quickly decay to zero.
3. **General Reference Topics**: Concepts that people research out of curiosity without intending to purchase any service.

---

## 2. Decision Heuristics for B2C Founders

### Matrix: Demand Intensity vs. Trust Score

| Normalized Mindshare (VPM) | Trust Score $\ge 80$ | Trust Score $< 60$ |
| :--- | :--- | :--- |
| **High ($> 50$ vpm)** | **Tier 1: High Priority**<br>Strong organic demand. Build MVP, launch localized ads, prioritize roadmap. | **Tier 3: Investigate Further**<br>High traffic but seasonal or spike-heavy. Run pre-order landing page first. |
| **Low ($< 15$ vpm)** | **Tier 2: Niche / Specialized**<br>Steady loyal audience. Good for targeted premium courses; avoid mass-market B2C spend. | **Tier 4: Deprioritize / Avoid**<br>Low interest combined with low reliability. Do not invest development budget. |

---

## 3. Triangulation Strategy (Recommended Next Steps)

When this skill identifies an attractive market opportunity:

1. **Google Trends / Search Volume**: Verify whether transactional keywords (e.g. "kurs angielskiego", "appka do postu przerywanego") are also trending.
2. **Fake Door / Landing Page Test**: Create a 1-page pre-launch landing page with a waitlist or pre-order button to test conversion before writing production code.
3. **App Store Competitive Intelligence**: Check top-grossing apps in the localized App Store category to measure competitor revenue.

---

## 4. Iterative Exploration Strategies

When users or founders ask follow-up questions:
* *"What about Germany?"* $\rightarrow$ Run `scripts/wiki_insights.py analyze --topic ... --langs de` to pull comparative metrics. Cached project traffic ensures instant execution.
* *"Can we check daily data around the peak?"* $\rightarrow$ Run with `--granularity daily --period 6m` to dissect whether a spike happened over 1 single day or sustained over months.
* *"What related topics should we test?"* $\rightarrow$ Query candidate topics suggested in `closest_candidates` (e.g., `Głodówka lecznicza`, `Ketoza`).
