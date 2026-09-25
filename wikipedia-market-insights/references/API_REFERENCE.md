# Wikimedia Analytics API Reference

This reference documents the primary Wikimedia endpoints utilized by the `wikipedia-market-insights` skill.

Official documentation: [Wikimedia Analytics API Reference](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/reference/page-views.html)

---

## 1. Per-Article Pageviews Endpoint

Retrieves historical pageviews for an individual article in a specific Wikimedia project.

### Endpoint
```http
GET https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{project}/{access}/{agent}/{article}/{granularity}/{start}/{end}
```

### Parameters
* **`project`**: Language domain, e.g. `uk.wikipedia` or `pl.wikipedia`.
* **`access`**: Access method.
  - `all-access` (recommended: desktop + mobile web + mobile app)
  - `desktop`
  - `mobile-app`
  - `mobile-web`
* **`agent`**: Traffic agent filter.
  - `user`: Real human visitors (recommended for demand validation).
  - `spider`: Search engine crawlers and indexing scrapers.
  - `bot`: Known automated bots.
  - `all-agents`: Total unfiltered traffic.
* **`article`**: Article title in URL-encoded UTF-8 format (spaces converted to underscores `_`).
* **`granularity`**: `monthly` or `daily`.
* **`start`**: `YYYYMMDD` (earliest supported date is July 1, 2015: `20150701`).
* **`end`**: `YYYYMMDD` (latest supported date is yesterday or current day).

---

## 2. Project Aggregate Pageviews Endpoint

Retrieves total aggregate pageviews across an entire language edition. Used for market baseline normalization.

### Endpoint
```http
GET https://wikimedia.org/api/rest_v1/metrics/pageviews/aggregate/{project}/{access}/{agent}/{granularity}/{start}/{end}
```

### Response Example
```json
{
  "items": [
    {
      "project": "uk.wikipedia",
      "access": "all-access",
      "agent": "user",
      "granularity": "monthly",
      "timestamp": "2024010100",
      "views": 98450123
    }
  ]
}
```

---

## 3. MediaWiki Langlinks & Wikidata Resolution

Used by `topic_resolver.py` to map concepts across language editions.

### Endpoint 1: Fetch Sitelinks via MediaWiki
```http
GET https://{source_lang}.wikipedia.org/w/api.php?action=query&titles={title}&prop=pageprops|langlinks&lllimit=500&redirects=1&format=json
```

### Endpoint 2: Fetch Wikidata Entity
```http
GET https://www.wikidata.org/w/api.php?action=wbgetentities&ids={QID}&props=sitelinks&format=json
```

---

## 4. Best Practices & Policy Compliance

* **User-Agent Header**: Wikimedia requires a descriptive `User-Agent` containing the tool name, project URL, and contact email.
  ```http
  User-Agent: WikipediaMarketInsightsSkill/1.0 (https://agentskills.io; contact@agentskills.io)
  ```
* **Local Caching**: The skill stores JSON responses in `.cache/` indexed by SHA256 hashes with a 24-hour TTL to prevent redundant network calls and enable rapid iterative analysis.
