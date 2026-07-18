# NEO Analytics Dashboard — Architecture & UX Design

**Status:** In progress
**Last updated:** 2026-07-17 (module references corrected for Epic 7 refactoring — see "Resolved (Epic 7/TD-02)" note below)

---

## Target User Personas

**Purpose:** design before coding. The four personas below represent the intended audience for the dashboard and anchor later navigation, workflow, and wireframe decisions.

| Persona | Technical familiarity | Primary question they bring to the dashboard |
|---|---|---|
| Science Enthusiast | Low | "Which asteroids should I be paying attention to, and why?" |
| Analyst | Moderate–High | "How do these asteroids compare, and can I get the numbers out?" |
| Researcher | High (domain expert) | "How was this score computed, and where does the model break down?" |
| Student | Low–Moderate (learning) | "What do these terms mean, and how does the scoring actually work?" |

---

### Science Enthusiast

**Who they are:** A member of the public with a casual interest in astronomy and planetary defense news. No formal science background.

**Goals:**
- Get a quick, plain-language answer to "is anything worth worrying about right now?"
- Browse notable or high-ranked asteroids without needing to understand orbital mechanics.

**Needs from the dashboard:**
- Plain-language summaries and labels (avoid raw feature names like `miss_distance_norm`).
- Visually engaging, high-level charts (top-N lists, simple risk tiers) over dense tables.
- Minimal required navigation — a single landing view should answer their core question.

**Out of scope for this persona:** methodology detail, raw data export, sensitivity analysis.

---

### Analyst

**Who they are:** A data-literate user (e.g., internal stakeholder or hobbyist analyst) who wants to interrogate the data, not just view it.

**Goals:**
- Compare asteroids side by side across features (size, proximity, velocity, frequency).
- Filter, sort, and slice the dataset by custom criteria.
- Export results for use outside the dashboard.

**Needs from the dashboard:**
- Filterable/sortable tables with access to underlying feature values, not just the final score.
- Ability to view per-feature contributions (`explain_score`) for individual asteroids.
- Export or download affordances (e.g., CSV of the current filtered view).

---

### Researcher

**Who they are:** A domain expert (e.g., planetary science or data science background) evaluating the model itself, not just its outputs.

**Goals:**
- Understand exactly how the risk score is derived and validate it against their own judgment.
- Identify where the model's assumptions break down for specific asteroids.

**Needs from the dashboard:**
- Direct visibility into normalization ranges, weights, and per-feature contributions.
- Access to the full scorable/non-scorable population, not just a curated top-N.
- Links or references to the underlying methodology (`docs/risk_model_design.md`, `docs/risk_model_card.md`), including documented limitations (L1–L7).

---

### Student

**Who they are:** Someone learning about NEOs, orbital mechanics, or data science/analytics as a discipline. May be using the dashboard as a guided learning tool.

**Goals:**
- Build an intuitive understanding of what risk scoring means and how it's calculated.
- Explore real data without being blocked by unfamiliar terminology.

**Needs from the dashboard:**
- Inline definitions/glossary support for domain terms (diameter, miss distance, relative velocity, encounter frequency).
- A guided path from "what is this asteroid" to "how did it get this score" (progressive disclosure rather than all detail at once).
- Worked examples (mirroring the model card's Example A/B pattern) that connect raw values to the final score.

---

## Core User Workflows

Three primary workflows cover the full range of user intent across all four personas. Each workflow defines an entry point, a sequence of steps, and an outcome — these anchor the navigation structure and view design that follows.

---

### Workflow 1: Find a Specific Asteroid

**Personas:** Analyst, Researcher, Student

**Entry point:** The user arrives with a specific asteroid in mind — by name (e.g., "433 Eros"), designation (e.g., "2019 PJ"), or because they saw a news item referencing it.

**Steps:**
1. Land on the dashboard. A search field is immediately visible.
2. Type the asteroid name or designation into the search field. Results filter in real time.
3. Select the asteroid from the results. The asteroid detail view opens.
4. View the asteroid's risk score, rank, and plain-language summary.
5. Expand to see per-feature contributions (size, proximity, velocity, frequency) and their normalized values.
6. *(Analyst/Researcher only)* View close-approach records for this asteroid and compare its feature profile against the dataset population.

**Outcome:** The user understands where a specific asteroid sits in the risk ranking and why it received that score.

**Design constraints:**
- Search must be reachable without scrolling from any view.
- The detail view must surface the score explanation without requiring additional navigation steps — the "why" should appear on the same page as the "what."

---

### Workflow 2: Investigate Risk Rankings

**Personas:** Science Enthusiast, Analyst, Researcher

**Entry point:** The user wants to know which asteroids are considered most concerning right now, without having a specific object in mind.

**Steps:**
1. Land on the dashboard. The default view shows the top-ranked asteroids in descending risk order.
2. *(Science Enthusiast)* Scan the top-N list. Plain-language labels (e.g., "Large — very close pass") communicate threat character without requiring domain knowledge.
3. *(Analyst)* Apply filters (e.g., minimum diameter, date range for close approaches, PHO status) and re-sort by any column. Download the filtered list as CSV.
4. Select any asteroid to open its detail view (see Workflow 1 for detail steps).
5. *(Researcher)* Navigate to the full scorable population (not just top-N). Inspect non-scorable asteroids and understand why they were excluded.

**Outcome:** The user has an accurate picture of which asteroids rank highest and the feature profile that drives each ranking.

**Design constraints:**
- The landing view must be useful with zero interaction — the default sort and column set should answer the Science Enthusiast's core question immediately.
- Filters and sort controls must not obscure the default view; they should be accessible but not required.
- The distinction between the curated top-N and the full population must be clearly communicated (scope label, row count).

---

### Workflow 3: Explore Close Approaches

**Personas:** Science Enthusiast, Student, Analyst

**Entry point:** The user wants to browse upcoming or recent close approaches rather than risk ranks — temporal curiosity ("what's coming soon?") rather than threat prioritization.

**Steps:**
1. Navigate to the Close Approaches view (distinct from the risk ranking view).
2. Browse close-approach events sorted by date. Each row shows the asteroid name, approach date, miss distance, and relative velocity.
3. Filter by date range to focus on a specific window (e.g., the next six months).
4. *(Student)* Hover or tap a row to see inline definitions for miss distance and relative velocity.
5. Select a row to navigate to the asteroid's detail view, where the close-approach event is highlighted in the context of the asteroid's full risk profile.

**Outcome:** The user understands what close-approach events are occurring in a given time period and can connect any individual event back to its parent asteroid's risk standing.

**Design constraints:**
- This view is event-centric (one row per close-approach event), not asteroid-centric (one row per asteroid). An asteroid with multiple approaches appears multiple times.
- Date filtering must default to a meaningful window (e.g., current dataset range) rather than showing all records unfiltered.
- The connection between a close-approach event and the asteroid's overall risk rank must be visible without leaving the row (e.g., a rank badge or score chip inline).

---

## Navigation Structure

The dashboard is organized into four top-level sections accessible from a persistent navigation bar. A global search field is always visible in the nav bar regardless of which section is active, providing the entry point for Workflow 1 from anywhere in the application.

### Page layout

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ NEO Analytics  Home  Risk Rankings  Explorer  Analytics  [Search __________] │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                             Page content                                     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

Navigation is flat — no dropdowns or nested menus. All four sections are reachable in a single click from any page. The asteroid detail view is not a top-level nav item; it is reached by selecting any asteroid row or search result and sits within the context of whichever section the user navigated from (preserving back-navigation state).

---

### Home

**Primary personas:** Science Enthusiast, Student

**Purpose:** Answer the dashboard's core question — "which asteroids merit attention right now?" — without requiring any interaction. The landing view must be immediately useful to the least technical user.

**Key components:**
- Dataset summary bar: total scorable asteroids, PHO count, dataset window (2024–2026), and last updated date.
- Top-10 risk list: asteroid name, risk score, a plain-language threat character label (e.g., "Large — close pass," "Fast — very close pass"), and PHO status badge.
- Highest-ranked asteroid spotlight: a single-card callout for rank 1 with its score, a one-sentence plain-language description, and a link to its full detail view.
- Global search prompt: a visible search field with placeholder text ("Search by asteroid name or designation") that routes to Workflow 1.

**Navigation connections:**
- "View full rankings" link routes to Risk Rankings.
- Any asteroid row routes to that asteroid's detail view.
- Search results route to the matching asteroid's detail view.

---

### Risk Rankings

**Primary personas:** Analyst, Researcher, Science Enthusiast (read-only browse)

**Purpose:** Serve Workflow 2 — full ranked list of all scorable asteroids with filtering, sorting, and export.

**Key components:**
- Ranked table: one row per asteroid. Default columns: rank, name, risk score, size (km), closest approach distance (km), max velocity (km/s), encounter count, PHO status. All columns sortable.
- Filter controls: PHO status toggle, diameter range slider, date range for close approaches, minimum/maximum risk score.
- Scope indicator: clearly labels whether the table shows the top-100 curated list or the full scorable population (toggle between the two).
- Row expansion or detail link: selecting a row opens the asteroid detail view.
- Export: "Download CSV" button exports the current filtered/sorted view.

**Navigation connections:**
- Asteroid rows route to the asteroid detail view.
- The asteroid detail view includes a "← Back to Rankings" link preserving the filter/sort state.

---

### Explorer

**Primary personas:** Science Enthusiast, Student, Analyst

**Purpose:** Serve Workflow 3 — event-centric browsing of close-approach records by date, not by risk rank. Each row represents a single close-approach event, not an asteroid.

**Key components:**
- Close-approach event table: one row per event. Default columns: asteroid name, approach date, miss distance (km), relative velocity (km/s), parent asteroid risk rank, PHO status.
- Date range filter: defaults to the full dataset window; user can narrow to a specific period (e.g., next six months).
- Inline glossary: hovering "miss distance" or "relative velocity" column headers (or their values for Student persona) surfaces a short plain-language definition.
- Risk rank chip: each row shows the asteroid's overall risk rank as an inline badge so the event can be immediately contextualized within the broader ranking.

**Navigation connections:**
- Any row's asteroid name links to the asteroid detail view.
- The asteroid detail view reached from Explorer highlights the specific close-approach event that was selected.

---

### Analytics

**Primary personas:** Researcher, Analyst

**Purpose:** Expose the model's internals — scoring methodology, feature contributions, sensitivity analysis results, and documented limitations. This section is the dashboard equivalent of `docs/risk_model_card.md`.

**Key components:**
- Scoring formula display: the weighted linear formula with current weight values (0.40 / 0.30 / 0.20 / 0.10) and a brief rationale for each weight.
- Feature contribution chart: average per-feature contribution across the top-100 baseline (proximity 70.7%, velocity 23.2%, frequency 3.7%, size 2.4%), visualized as a proportional bar or donut.
- Sensitivity analysis summary table: the five weight scenarios, their MARC values, and top-10/top-20 retention rates.
- Known limitations: the seven documented model limitations (L1–L7 from the model card), presented as an expandable list.
- Reference links: links to `docs/risk_model_design.md` and `docs/risk_model_card.md` for full methodology detail.

**Navigation connections:**
- No asteroid-level navigation from this section — it is model-level, not record-level.
- The feature contribution chart may link back to Risk Rankings filtered to specific archetypes (e.g., "View size-extreme asteroids").

---

### Asteroid detail view

**Accessible from:** Home (top-10 list, spotlight card), Risk Rankings (any row), Explorer (any row's asteroid name), global search results.

**Purpose:** The per-asteroid deep-dive, serving all four personas at different levels of depth via progressive disclosure.

**Key components:**
- Header: asteroid name/designation, risk score (large), rank badge, PHO status.
- Plain-language summary: one sentence describing the asteroid's threat character (e.g., "Ranks highly due to an extremely close approach on 2025-03-14 at high velocity").
- Score breakdown: horizontal stacked bar showing each feature's weighted contribution to the total score. Each segment labeled with the feature name, normalized value, weight, and contribution.
- Feature detail table: raw and normalized values for all four features, with the normalization range shown for context.
- Close-approach history: all recorded close-approach events for this asteroid within the dataset window, sorted by date.
- *(Researcher only)* Normalization context: where this asteroid's raw feature values fall relative to the dataset min/max for each feature.

---

## Wireframes

Low-fidelity structural sketches for each page. Layout and content placement only — no color, typography, or visual design implied.

The nav bar is identical across all pages and is abbreviated as `[NAV]` in the wireframes below.

```
[NAV]  NEO Analytics  Home  Risk Rankings  Explorer  Analytics  [Search]
```

---

### Home

```
┌─────────────────────────────────────────────────────────────────────┐
│ [NAV]                                                               │
├─────────────────────────────────────────────────────────────────────┤
│  4,084 asteroids scored  │  527 PHOs (12.9%)  │  2024–2026         │
├───────────────────────────────┬─────────────────────────────────────┤
│                               │                                     │
│  RANK 1 SPOTLIGHT             │  TOP 10 RISK RANKINGS               │
│  ┌─────────────────────────┐  │  ┌───┬──────────────┬───────┬────┐ │
│  │ 433 Eros          #1    │  │  │ # │ Name         │ Score │PHO│ │
│  │ Score: 0.475            │  │  ├───┼──────────────┼───────┼────┤ │
│  │                         │  │  │ 1 │ 433 Eros     │ 0.475 │   │ │
│  │ [Plain-language         │  │  │ 2 │ 66008        │ 0.417 │ ● │ │
│  │  threat summary]        │  │  │ 3 │ (2019 PJ)    │ 0.411 │ ● │ │
│  │                         │  │  │ 4 │ (2014 WF6)   │ 0.407 │ ● │ │
│  │ [View full profile →]   │  │  │ 5 │ (2025 US6)   │ 0.407 │   │ │
│  └─────────────────────────┘  │  │   │ ...          │       │   │ │
│                               │  └───┴──────────────┴───────┴────┘ │
│                               │  [View full rankings →]             │
└───────────────────────────────┴─────────────────────────────────────┘
```

---

### Risk Rankings

```
┌─────────────────────────────────────────────────────────────────────┐
│ [NAV]                                                               │
├─────────────────────────────────────────────────────────────────────┤
│  [PHO only ○]  Diameter: [____] – [____] km  Score: [____] – [____]│
│  Showing: [Top 100 ▾]   4,084 total scorable asteroids              │
├─────────────────────────────────────────────────────────────────────┤
│  Rank ↕ │ Name ↕        │ Score ↕ │ Size ↕ │ Distance ↕ │ Vel ↕  │
├─────────┼───────────────┼─────────┼────────┼────────────┼─────────┤
│    1    │ 433 Eros      │  0.475  │ 16.8km │  18.9M km  │ 5.8kps │
│    2    │ 66008         │  0.417  │ 0.9km  │  3.5M km   │ 7.2kps │
│    3    │ (2019 PJ)     │  0.411  │ 0.1km  │  0.5M km   │ 9.1kps │
│   ...   │ ...           │   ...   │  ...   │    ...     │  ...   │
├─────────┴───────────────┴─────────┴────────┴────────────┴─────────┤
│  [Download CSV ↓]                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Explorer (Close Approaches)

```
┌─────────────────────────────────────────────────────────────────────┐
│ [NAV]                                                               │
├─────────────────────────────────────────────────────────────────────┤
│  Date range: [2024-01-01] to [2026-12-31]     5,551 events          │
├─────────────────────────────────────────────────────────────────────┤
│  Date ↕      │ Asteroid ↕    │ Miss Dist [?] │ Velocity [?] │ Rank │
├──────────────┼───────────────┼───────────────┼──────────────┼──────┤
│  2024-01-14  │ (2014 WF6)    │  4.1M km      │  11.3 kps    │  #4  │
│  2024-02-03  │ 433 Eros      │  18.9M km     │  5.8 kps     │  #1  │
│  2024-02-21  │ (2019 PJ)     │  0.5M km      │  9.1 kps     │  #3  │
│  ...         │ ...           │  ...          │  ...         │ ...  │
└──────────────┴───────────────┴───────────────┴──────────────┴──────┘
  [?] = inline glossary tooltip on hover
```

---

### Asteroid Detail View

```
┌─────────────────────────────────────────────────────────────────────┐
│ [NAV]                                                               │
├─────────────────────────────────────────────────────────────────────┤
│ ← Back                                                              │
│                                                                     │
│  433 Eros                              Score  0.475    Rank  #1     │
│  PHO: No                                                            │
│  "Ranks highest due to exceptional size — the only asteroid in      │
│   this dataset with a diameter above 10 km."                        │
├─────────────────────────────────────────────────────────────────────┤
│  SCORE BREAKDOWN                                                    │
│  [████████████████ Size 40%][███████ Prox 21%][█ Vel 5%][Freq <1%] │
│   0.40 × 1.000 = 0.400     0.30×0.205  0.20×0.067   0.10×0.000    │
├─────────────────────────────────────────────────────────────────────┤
│  FEATURE DETAIL                                                     │
│  Feature       │ Raw value  │ Dataset range      │ Normalized       │
│  ──────────────┼────────────┼────────────────────┼──────────────── │
│  Diameter      │ 16.84 km   │ 0.001 – 16.84 km   │ 1.000           │
│  Miss distance │ 18.9M km   │ 0.04M – 74.8M km   │ 0.205 (inv.)    │
│  Velocity      │ 5.83 kps   │ 2.1 – 33.7 kps     │ 0.118           │
│  Freq.         │ 1 approach │ 1 – 8 approaches    │ 0.000           │
├─────────────────────────────────────────────────────────────────────┤
│  CLOSE APPROACH HISTORY                                             │
│  Date          │ Miss distance   │ Velocity                         │
│  2024-02-03    │ 18.9M km        │ 5.83 kps                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Analytics

```
┌─────────────────────────────────────────────────────────────────────┐
│ [NAV]                                                               │
├─────────────────────────────────────────────────────────────────────┤
│  SCORING FORMULA                                                    │
│  Risk = 0.40×size + 0.30×proximity + 0.20×velocity + 0.10×freq     │
│  [Weight rationale table: feature │ weight │ rationale]             │
├─────────────────────────────────────────────────────────────────────┤
│  FEATURE CONTRIBUTIONS (avg across top-100 baseline)                │
│  Proximity  [████████████████████████████████████████] 70.7%        │
│  Velocity   [█████████████] 23.2%                                   │
│  Frequency  [██] 3.7%                                               │
│  Size       [█] 2.4%                                                │
├─────────────────────────────────────────────────────────────────────┤
│  SENSITIVITY ANALYSIS                                               │
│  Scenario          │ MARC   │ Top-10 retention │ Top-20 retention   │
│  Baseline          │  —     │ —                │ —                  │
│  Size-dominant     │  22.2  │ 50%              │ 65%                │
│  Proximity-dom.    │  66.3  │ 60%              │ 80%                │
│  Equal weights     │  74.0  │ 40%              │ 50%                │
│  Velocity-dom.     │ 166.3  │ 20%              │ 30%                │
├─────────────────────────────────────────────────────────────────────┤
│  KNOWN LIMITATIONS                                                  │
│  ▶ L1 — Not a collision predictor                                   │
│  ▶ L2 — Proximity-dominated output                                  │
│  ▶ L3 — Dataset window: absence ≠ safety                            │
│  ▶ L4 — Non-scorable asteroids excluded                             │
│  ▶ L5 — Weights are not learned                                     │
│  ▶ L6 — Non-probabilistic output                                    │
│  ▶ L7 — No temporal dynamics                                        │
│                                                                     │
│  [risk_model_design.md ↗]   [risk_model_card.md ↗]                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Performance Baseline

**Purpose:** establish a measured baseline before any optimization work (Story 6.9), so later changes can be checked against real numbers rather than guesswork.

**Method:** each `data_service` function is decorated with `@st.cache_data`, so Streamlit caches results in-process across reruns and pages. Timings below measure the underlying data-layer calls directly (cache cleared before the "cold" measurement, immediately re-measured for "warm"), rather than a browser-rendered page load — this isolates the actual cost driver (SQLite queries + `compute_risk_scores`) from browser/network overhead, which varies per machine.

**Dataset size at time of measurement:** 4,084 asteroids, 5,551 close-approach records.

| Page (equivalent data calls) | Cold | Warm (cached) |
|---|---|---|
| Home (`get_high_level_metrics` + `get_top_risk`) | 72.3 ms | — |
| Risk Rankings (`get_rankings` + `get_summary_metrics`) | — | 13.4 ms* |
| Explorer (search + profile + risk breakdown + approach history, 1 match) | — | 22.5 ms* |
| Analytics (`get_all_close_approaches` + `get_feature_matrix`) | 50.6 ms | — |

\* Measured after Home/Analytics had already populated the shared cache — this is the realistic case, since a user visiting Risk Rankings or Explorer almost always lands on Home first in the same session.

| Underlying function | Cold | Warm |
|---|---|---|
| `get_all_scores()` | 45.3 ms | 14.2 ms |
| `get_all_close_approaches()` | 21.0 ms | 2.4 ms |
| `get_feature_matrix()` | 27.8 ms | 3.1 ms |

**Takeaways:**
- All pages load well under 100 ms of data-layer time at the current dataset size — no page is close to feeling sluggish today.
- `get_all_scores()` is the single most expensive call (it drives `compute_risk_scores`, a full join + per-row normalization pass over every asteroid) and is also the most-reused — Home, Risk Rankings, and Explorer all depend on it directly or indirectly.
- Caching is already doing real work: every function shows a 3–7× speedup warm vs. cold.
- These numbers will not hold at a larger dataset size — `compute_risk_scores` and `get_feature_matrix` both do O(n) Python-level work per asteroid (not vectorized), so cost should scale roughly linearly with asteroid/approach count. Story 6.9's remaining subtasks (caching strategy, query optimization, large-dataset validation) should be judged against this baseline.

### 6.9.2 — Query Caching

Added `@st.cache_data` to every remaining `data_service` function that previously re-derived its result from an already-cached call on every rerun (`get_asteroid`, `search_asteroids`, `get_rankings`, `get_top_risk`, `get_summary_metrics`, `get_approach_statistics`, `get_size_distribution`, `get_risk_distribution`, `get_score_explanation`, `get_high_level_metrics`). Measured speedup on repeated (warm) calls: 45×–375× depending on the function, since these previously re-filtered/re-aggregated the full 4,084-row list on every widget interaction even though the underlying data hadn't changed.

### 6.9.3 — Query Optimization

`_fetch_raw_data` (`src/models/risk_score.py`) and `get_feature_matrix` (`data_service.py`) both `GROUP BY`'d on 9–11 columns when `a.asteroid_id` (the `asteroids` primary key) alone is sufficient — every other selected column is already functionally dependent on it. Verified both simplified queries return byte-identical results, ~16–18% faster:

| Query | Before | After |
|---|---|---|
| `_fetch_raw_data` (risk scoring) | 23.1 ms | 18.9 ms |
| `get_feature_matrix` | 21.4 ms | 18.0 ms |

Confirmed no behavior change: `compute_risk_scores` output is unchanged (433 Eros still ranks #1 at 0.475, matching `risk_model_card.md`), and the full test suite (11 tests) passes.

### 6.9.4 — Large Dataset Validation

**Method:** the real dataset (4,084 asteroids / 5,551 close approaches) doesn't stress-test scalability, and pulling a genuinely larger NeoWs dataset would mean re-running the ETL pipeline against a much wider date range. Instead, a scratch copy of the real database was scaled 5×, 10×, and 25× by duplicating every row across all three tables with suffixed IDs (preserving the real ~1.36 close-approaches-per-asteroid ratio). This is synthetic volume, not synthetic *shape* — the join fan-out and value distributions match production. The scratch DB copies were not committed and don't touch `data/database/neows.db`.

| Scale | Asteroids | Approaches | `compute_risk_scores` | `get_feature_matrix` | `get_all_close_approaches` |
|---|---|---|---|---|---|
| 1× (current) | 4,084 | 5,551 | 35.6 ms | 19.1 ms | 14.8 ms |
| 5× | 20,420 | 27,755 | 354.3 ms | 260.3 ms | 132.3 ms |
| 10× | 40,840 | 55,510 | 828.3 ms | 679.9 ms | 402.5 ms |
| 25× | 102,100 | 138,775 | 2,588.5 ms | 1,990.2 ms | 1,346.2 ms |

**This corrects a wrong assumption from the 6.9.1 baseline.** That write-up guessed the Python-level feature-building loop was the scaling risk. Breaking `compute_risk_scores` into its two phases shows the opposite:

| Scale | SQL fetch (`_fetch_raw_data`) | Python build (`_build_features`) |
|---|---|---|
| 1× | 6.23 µs/row | 2.55 µs/row |
| 5× | 14.83 µs/row | 3.11 µs/row |
| 10× | 17.97 µs/row | 2.76 µs/row |
| 25× | 20.92 µs/row | 4.54 µs/row |

The Python loop's per-row cost is flat across every scale tested — it *is* effectively linear, exactly as expected for straight-line per-dict work. The SQL fetch is what degrades super-linearly (~3.4× worse per-row at 25× than at 1×), almost certainly because SQLite's join + `GROUP BY` spills to a temp b-tree on disk once the intermediate result outgrows its page cache. The 6.9.3 query simplification helps at every scale but doesn't change this underlying growth curve.

**Responsiveness assessment:**
- **1×–5× (up to ~20K asteroids):** every query completes in well under 400 ms cold. Fully responsive, including first-load.
- **10× (~41K asteroids):** up to ~830 ms cold per query. Borderline on a genuinely fresh cache, but `@st.cache_data` (6.9.2) means this cost is paid once per cache lifetime, not per interaction — acceptable. This is well beyond what a further date-range extension of this project's ingestion would plausibly produce.
- **25× (~102K asteroids):** up to ~2.6 s cold for a single query; a page needing more than one of these (e.g. Analytics, which calls both `get_feature_matrix` and `get_all_close_approaches`) would exceed 3 s combined on first load. This is the point where "remains responsive" starts to fail for a cold visit — well past any realistic near-term target for this project's date-range-based ingestion.

**Conclusion:** the dashboard remains responsive across every realistic growth scenario for this project (current data through the full known NEO catalog, ~10×). Beyond that, the fix is not the Python code — it's replacing the ad hoc `LEFT JOIN` + `GROUP BY` in `_fetch_raw_data`/`get_feature_matrix` with a pre-aggregated summary table (e.g. a `close_approach_stats` table maintained by the ETL pipeline, keyed by `asteroid_id`) so the dashboard reads a 1:1 join instead of aggregating a growing fan-out join at request time. Flagged here rather than implemented, since it would mean changing the ETL pipeline (Epic 3), outside this story's scope.

---

## System Architecture

**Purpose:** document the as-built implementation — UI, services, and database interactions — as a reference for maintaining or extending the dashboard.

### Layered overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  UI layer            src/dashboard/app.py + pages/*.py               │
│                       (Streamlit pages: rendering, widgets, charts)  │
└──────────────────────────────┬────────────────────────────────────────┘
                                │ calls
┌──────────────────────────────▼────────────────────────────────────────┐
│  Services layer      src/dashboard/data_service.py                    │
│                       (single access point; every function cached     │
│                        with @st.cache_data)                           │
└───────────────┬───────────────────────────────────────┬───────────────┘
                │ calls                                  │ calls
┌───────────────▼───────────────────┐   ┌────────────────▼───────────────┐
│  Risk model    src/models/         │   │  Database access                │
│                risk_score.py       │   │  src/db/connection.py           │
│  (compute_risk_scores,             │   │  (get_connection: sqlite3 +     │
│   explain_score — shared with      │   │   DB_PATH from src.config)      │
│   Epic 5, not dashboard-specific)  │   │  shared with the ETL pipeline   │
└───────────────┬────────────────────┘   └────────────────┬────────────────┘
                │                                          │
                └───────────────────┬──────────────────────┘
                                    ▼
                     data/database/neows.db (SQLite)
                     tables: asteroids, close_approaches,
                             orbital_parameters
```

The dashboard is **read-only** against this database — it never writes. All writes happen upstream, via the ETL pipeline (`src/etl/`, `src/parsing/`, `src/transform/`, `src/db/`) documented in `docs/architecture.md` and `docs/schema_design.md`.

### UI layer

| File | Role |
|---|---|
| `src/dashboard/app.py` | Entry point and the Home page. Runs `st.set_page_config`, renders the summary narrative, headline metrics, rank-1 spotlight, top-10 table, and the size/risk distribution charts. |
| `src/dashboard/pages/1_Risk_Rankings.py` | Filterable, sortable, exportable table of every scorable asteroid. |
| `src/dashboard/pages/2_Explorer.py` | Search by name/ID, then a per-asteroid profile: risk breakdown, orbital data, close-approach history. |
| `src/dashboard/pages/3_Analytics.py` | Dataset-wide analysis: close-approach timeline, distance distribution, hazard population comparisons, correlation matrix, outlier investigation. |
| `src/dashboard/pages/4_Model_Card.py` | Renders `docs/risk_model_card.md` directly — no separate content to maintain. |
| `src/dashboard/layout.py` | Shared chrome used by every page: `configure_page`, `render_page_header`, `render_sidebar`, `render_footer`, and the theme-aware `chart_color` helper used throughout the Altair charts. |
| `src/dashboard/ui_settings.py` | Static display constants — app title/icon/layout, dataset window. (Renamed from `config.py` in Epic 7/TD-10 — the old name collided with `src/config.py`, the actual app configuration module.) |
| `src/dashboard/palette.py` | Shared chart color palette (Epic 7/TD-05) — centralizes hex values that were previously copy-pasted across `app.py` and multiple pages. |

Each page is a standalone Streamlit script (the project uses Streamlit's classic `pages/` multipage convention); none import from each other, only from `layout.py`, `ui_settings.py`, `palette.py`, and `data_service.py`.

### Services layer

`src/dashboard/data_service.py` is the single point every page goes through to get data — no page imports `src.models.risk_score` or `src.dashboard.db` directly (established in Story 6.3, section 6.3.1). Every function is decorated `@st.cache_data` (Story 6.9.2), so repeated calls across pages and reruns hit Streamlit's in-process cache rather than re-querying or re-computing.

| Function | Backed by |
|---|---|
| `get_all_scores()` | `compute_risk_scores()` (risk model) — the base dataset every other function derives from |
| `get_asteroid(id)`, `search_asteroids(query)` | filters over `get_all_scores()` |
| `get_rankings()`, `get_top_risk(n)`, `get_summary_metrics()` | filters/aggregates over `get_all_scores()` |
| `get_size_distribution()`, `get_risk_distribution()` | field extraction over `get_all_scores()` |
| `get_high_level_metrics()`, `get_approach_statistics()` | aggregates over `get_all_scores()` |
| `get_score_explanation(id)` | `explain_score()` (risk model) |
| `get_close_approaches(id)` | direct SQL — event-level data not present in `get_all_scores()` |
| `get_all_close_approaches()` | direct SQL — dataset-wide event-level data, joined with hazard status |
| `get_feature_matrix()` | direct SQL — the Epic 4 correlation feature set (orbital parameters, absolute magnitude) not needed by risk scoring |

### Database interactions

The dashboard imports `get_connection()` directly from `src/db/connection.py` — the same module the ETL pipeline uses — which opens a `sqlite3` connection to `DB_PATH` (resolved in `src/config.py`, see `docs/configuration.md`). Every `data_service` function that queries the database opens its own connection and closes it in a `finally` block — connections are not pooled or held open between calls.

**Resolved (Epic 7/TD-02):** this section previously documented a known inconsistency — the dashboard had its own `src/dashboard/db.py` reading a separately-loaded `DATABASE_PATH` env var, while the ETL pipeline read `DB_PATH` via `src.config`. Both happened to point at the same file, but the two layers didn't share a single source of truth. `src/dashboard/db.py` was deleted and the dashboard was switched to import `src/db/connection.py` directly, eliminating the duplication rather than just documenting around it.
