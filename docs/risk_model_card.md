# NEO Risk Scoring Model — Model Card

**Version:** 1.0  
**Last updated:** 2026-07-10  
**Dataset window:** 2024-01-01 to 2026-12-31  
**Scorable asteroids:** 4,084  
**Technical reference:** [docs/risk_model_design.md](risk_model_design.md)

---

## Model Overview

### Purpose

The NEO Risk Scoring Model ranks near-Earth asteroids by their composite threat potential. It is designed to answer a single operational question:

> **Of the asteroids making close approaches to Earth, which merit the most attention?**

The model produces a ranked list — updated whenever the underlying NeoWs dataset is refreshed — that supports three use cases:

| Use case | Audience | Output used |
|---|---|---|
| Observational prioritization | Researchers and mission planners | Top-N ranked list |
| Public threat awareness | Dashboard end users | Top-100 risk list with human-readable scores |
| Model validation and audit | Data engineers | Full ranked dataset with normalized feature columns |

The model is a **risk prioritization tool**, not a collision predictor. It does not estimate impact probability, impact energy, or any form of trajectory propagation. It scores relative threat potential based on four observable physical and orbital characteristics as of the current dataset snapshot.

### Approach

The scoring pipeline consists of four sequential stages:

**1. Feature extraction**  
Four features are computed from raw asteroid and close-approach records retrieved from the NASA NeoWs API:

- **Diameter** — maximum estimated diameter in km, taken from the closest NeoWs size estimate for each asteroid.
- **Miss distance** — minimum close-approach distance to Earth (km) across all recorded approaches in the dataset window. Inverted so that closer = higher score.
- **Velocity** — maximum relative approach velocity (km/s) across all recorded approaches.
- **Encounter frequency** — number of distinct close approaches recorded in the dataset window, normalized against the maximum observed count.

**2. Normalization**  
Each feature is scaled to [0, 1] using min-max normalization across the full scorable population. Normalization ranges are computed once per scoring run from the complete set of scorable asteroids, ensuring all features contribute on a common scale. An asteroid is scorable if all four raw features are non-null.

**3. Weighted linear scoring**  
A single composite risk score is computed as a weighted sum of the four normalized features:

```
Risk = 0.40 × diameter_norm
     + 0.30 × miss_distance_norm
     + 0.20 × velocity_norm
     + 0.10 × encounter_frequency_norm
```

Weights sum to 1.0, placing Risk ∈ [0, 1] for all scorable asteroids.

**4. Ranking**  
All scorable asteroids are ranked in descending order by Risk score. Asteroids with missing feature data are assigned rank `null` and excluded from the ordered list.

### Limitations

The following limitations apply to all outputs produced by this model. The Known Limitations section below expands each limitation with detail and recommended mitigations.

| # | Limitation | Scope |
|---|---|---|
| L1 | Not a collision predictor | The model does not compute impact probability or trajectory. |
| L2 | Proximity-dominated scoring | 70.7% of the average risk score for the top-100 asteroids is driven by miss distance alone, reflecting NeoWs dataset selection bias. |
| L3 | Dataset window dependency | Scores reflect approaches recorded in the configured date range only. Asteroids with approaches outside the window are unscored. |
| L4 | Observation-completeness sensitivity | Small and newly-discovered asteroids may lack diameter estimates; these are excluded from scoring (`is_scorable = False`). |
| L5 | Static weights | Weights are fixed constants derived from a physical threat hierarchy and validated by sensitivity analysis. They are not learned from outcome data. |
| L6 | Non-probabilistic output | Risk scores are relative ranks on a continuous scale, not probability estimates. A score of 0.45 does not mean "45% chance of impact." |
| L7 | No temporal dynamics | The model scores each asteroid as a snapshot; it does not model how threat potential changes as new observations refine orbital elements. |

---

## Feature Definitions

Every variable that appears in model inputs, intermediate computations, or outputs is defined below. Variables are grouped by pipeline stage.

### Input Variables (raw)

These are extracted directly from the NeoWs API and stored in the `asteroids` and `close_approaches` tables.

| Variable | Type | Source field | Definition |
|---|---|---|---|
| `asteroid_id` | integer | `id` | NeoWs integer identifier. Prefix `2` = permanently numbered asteroid; prefix `3` = provisionally designated. |
| `name` | string | `name` | Human-readable name or provisional designation assigned by the Minor Planet Center. |
| `diameter_km` | float | `estimated_diameter.kilometers.estimated_diameter_max` | **Maximum** estimated diameter in kilometres, taken from the NeoWs size estimate for the asteroid. The maximum (not mean) is used as a conservative worst-case size. NULL if NeoWs does not report a diameter estimate for the asteroid. |
| `velocity_kps` | float | `relative_velocity.kilometers_per_second` | **Maximum** relative approach velocity in km/s across all close approaches recorded in the dataset window. Relative velocity is measured at closest approach. Higher velocity = greater kinetic energy on impact. |
| `miss_distance_km` | float | `miss_distance.kilometers` | **Minimum** miss distance to Earth in kilometres across all close approaches recorded in the dataset window. The closest approach is used because it represents the highest proximity event. |
| `encounter_frequency` | integer | (counted) | Number of distinct close-approach dates recorded for the asteroid in the dataset window. Computed from the count of rows in `close_approaches` for each asteroid after deduplication on approach date. Minimum value for any scorable asteroid is 1. |
| `is_potentially_hazardous` | boolean | `is_potentially_hazardous_asteroid` | NASA classification flag. True if the asteroid has an absolute magnitude H ≤ 22 (diameter ≳ 140 m) **and** a minimum orbital intersection distance (MOID) with Earth ≤ 0.05 AU. Set by NeoWs; not used in scoring. |

### Intermediate Variables (normalized)

Normalization maps each raw feature to [0, 1] using the min-max ranges of the **full scorable population** for that scoring run. Ranges are computed once and held constant across all asteroids in a run.

| Variable | Derivation | Direction | Definition |
|---|---|---|---|
| `diameter_norm` | `(diameter_km − min_d) / (max_d − min_d)` | Higher = larger = higher risk | Normalized diameter. 0 = smallest diameter in scorable population; 1 = largest (433 Eros in the current dataset). |
| `miss_distance_norm` | `1 − (miss_distance_km − min_m) / (max_m − min_m)` | Higher = closer = higher risk | Inverted normalized miss distance. 1 = closest recorded approach in the scorable population; 0 = most distant. The inversion ensures that proximity (closeness) increases the score. |
| `velocity_norm` | `(velocity_kps − min_v) / (max_v − min_v)` | Higher = faster = higher risk | Normalized approach velocity. 0 = slowest recorded approach speed; 1 = fastest in the scorable population. |
| `encounter_frequency_norm` | `(encounter_frequency − min_f) / (max_f − min_f)` | Higher = more approaches = higher risk | Normalized encounter count. 0 = fewest recorded approaches (1 in the current dataset); 1 = most (8 in the current dataset, (2025 US6)). |

### Classification Variable

| Variable | Type | Definition |
|---|---|---|
| `is_scorable` | boolean | True if `diameter_km`, `velocity_kps`, and `miss_distance_km` are all non-NULL. Encounter frequency is always non-NULL (a minimum of 1 close approach must exist for the asteroid to appear in the dataset). Non-scorable asteroids are excluded from ranking and receive `risk_score = NULL`, `rank = NULL`. In the current dataset, 4,084 of the total asteroid population are scorable. |

### Output Variables

| Variable | Type | Range | Definition |
|---|---|---|---|
| `risk_score` | float | [0, 1] for scorable asteroids; NULL otherwise | Composite risk score. Computed as the weighted sum of the four normalized features (see Scoring Formula and Methodology). Higher score = higher relative risk. Scores are comparable within a single scoring run; they are not comparable across runs with different dataset windows or normalization ranges. |
| `rank` | integer | 1 … N for scorable asteroids; NULL otherwise | Ordinal rank by descending `risk_score`. Rank 1 = highest composite risk in the current dataset. Ties in `risk_score` are broken by `asteroid_id` (ascending) for deterministic ordering. |

---

## Scoring Formula and Methodology

### Step 1 — Normalization

Before scoring, each raw feature is scaled to [0, 1] so that features measured in different units (km, km/s, counts) can be combined on a common scale. Min-max normalization is used:

```
norm(x) = (x − x_min) / (x_max − x_min)
```

where `x_min` and `x_max` are the minimum and maximum values of that feature across the **full scorable population** for the current run. Ranges are computed once before any scoring begins and held fixed for all 4,084 asteroids.

**Miss distance is inverted** after normalization because smaller distances represent greater threat:

```
miss_distance_norm = 1 − (miss_distance_km − min_dist) / (max_dist − min_dist)
```

This inversion means an asteroid at the closest recorded distance receives `miss_distance_norm = 1.0`; the most distant receives `miss_distance_norm = 0.0`. All other features are normalized in the natural direction (larger raw value → higher normalized score).

### Step 2 — Scoring

The composite risk score is a weighted linear combination of the four normalized features:

```
Risk(a) = 0.40 × diameter_norm(a)
        + 0.30 × miss_distance_norm(a)
        + 0.20 × velocity_norm(a)
        + 0.10 × encounter_frequency_norm(a)
```

Because all four normalized values lie in [0, 1] and the weights sum to 1.0, `Risk(a)` lies in [0, 1] for all scorable asteroids. A score of 1.0 would require an asteroid that simultaneously holds the maximum value on every feature — no such asteroid exists in the current dataset.

### Weight Rationale

Weights reflect a physical threat hierarchy derived from planetary defense principles and validated by sensitivity analysis:

| Feature | Weight | Rationale |
|---|---|---|
| Diameter | **0.40** | Kinetic energy scales as mass × v², and mass scales approximately as diameter³. A larger asteroid is categorically more destructive regardless of other factors, so it receives the highest weight to ensure physically large objects are elevated above the many small close-passers in the dataset. |
| Miss distance | **0.30** | Orbital proximity is the primary filter for close-approach datasets. Among the scorable population, miss distance is the strongest predictor of which asteroids merit observational attention. |
| Velocity | **0.20** | Kinetic energy scales as v²; higher approach speed multiplies impact destructiveness. Provides secondary differentiation within groups of similarly-sized, similarly-close objects. |
| Encounter frequency | **0.10** | Repeated close approaches indicate a persistently Earth-crossing orbit and increase the cumulative probability of a future threat window. Treated as a tie-breaker rather than a primary signal. |

### Step 3 — Ranking

All scorable asteroids are ranked by descending `risk_score`. The rank is an ordinal position (1 = most threatening) within the current dataset snapshot. Rank values are not stable across scoring runs with different dataset windows: an asteroid at rank 50 in one run may be rank 65 in the next run if new asteroids enter the scorable population.

### Worked Examples

The two examples below illustrate how the formula handles contrasting feature profiles.

**Example A — 433 Eros (rank 1, baseline dataset)**

Eros is the largest near-Earth asteroid in the current dataset. Its risk score is driven almost entirely by its exceptional diameter.

| Feature | Raw value | Normalized | Weight | Contribution |
|---|---|---|---|---|
| Diameter | ~16.8 km (max est.) | **1.000** | 0.40 | 0.400 |
| Miss distance | ~26.5 M km | 0.205 | 0.30 | 0.062 |
| Velocity | ~3.8 km/s | 0.067 | 0.20 | 0.013 |
| Encounter frequency | 1 approach | 0.000 | 0.10 | 0.000 |
| **Risk score** | | | | **0.475** |

Eros ranks #1 despite moderate proximity and low velocity because no other scorable asteroid comes close to its diameter. Under any weight scenario that preserves a non-trivial size weight, Eros remains in the top 5. However, its risk score collapses to near-zero under a proximity-dominant configuration, confirming that its ranking is fully attributable to size alone.

**Example B — (2019 PJ) (rank 3, baseline dataset)**

(2019 PJ) is a small asteroid with no recorded name, but it scores high on proximity and moderately on velocity and frequency — a balanced multi-feature profile.

| Feature | Raw value | Normalized | Weight | Contribution |
|---|---|---|---|---|
| Diameter | very small | 0.002 | 0.40 | 0.001 |
| Miss distance | very close | 0.952 | 0.30 | 0.286 |
| Velocity | moderate | 0.549 | 0.20 | 0.110 |
| Encounter frequency | 2 approaches | 0.143 | 0.10 | 0.014 |
| **Risk score** | | | | **0.411** |

Despite a trivial size contribution (0.001 out of a possible 0.400), (2019 PJ) reaches rank 3 because proximity alone contributes 0.286. This illustrates the practical dominance of miss distance in the scoring formula for the typical NeoWs asteroid: most scorable asteroids are small, so proximity and velocity — not size — determine their relative ranking.

### Score Interpretation

| Score range | Interpretation |
|---|---|
| 0.45 – 1.00 | Exceptional risk profile. In the current dataset only 433 Eros exceeds 0.45; this range flags asteroids with an extreme value on at least one feature. |
| 0.38 – 0.45 | High risk. Baseline top-100 asteroids fall in this range. Multiple features contributing meaningfully. |
| 0.20 – 0.38 | Moderate risk. Single strong feature (usually proximity) with weak contributions elsewhere. |
| 0.00 – 0.20 | Low risk relative to the scorable population. Distant, slow, and/or infrequently encountered. |

Risk scores should be interpreted **comparatively within a single run**. Absolute score values shift between runs as normalization ranges change with the dataset.

---

## Known Limitations

The seven limitations introduced in the Model Overview are expanded here with their practical impact and recommended mitigations.

---

### L1 — Not a Collision Predictor

**What it means.** The model computes a composite score from current observable characteristics — size, proximity, velocity, encounter frequency. It does not integrate orbital elements forward in time, does not simulate trajectory uncertainty, and produces no probability of impact (PI) estimate.

**Practical impact.** An asteroid at rank 1 may have zero modelled chance of Earth impact within the next century. Conversely, an asteroid not in the top 100 may be on a trajectory that will be revised to show a meaningful impact probability as observations accumulate. The ranked list answers "which asteroid has the most concerning observable profile right now," not "which asteroid will hit Earth."

**Mitigation.** For collision probability, cross-reference NASA's Sentry system or CNEOS close-approach tables, both of which use full trajectory propagation. This model is intended as a fast-cadence triage tool, not a replacement for those analyses.

---

### L2 — Proximity-Dominated Scoring

**What it means.** The NeoWs API returns asteroids specifically because they make close approaches to Earth. Every asteroid in the scorable population satisfies a proximity criterion by construction. As a result, `miss_distance_norm` is systematically high across the entire dataset — averaging 0.885 for the baseline top-100 — and contributes approximately 70.7% of the average risk score despite carrying only the second-highest weight (0.30).

**Practical impact.** The ranked list is effectively a ranking of *close-approaching asteroids by their additional threat characteristics*, not a ranking of all near-Earth asteroids by absolute danger. Large, distant asteroids that do not make close approaches in the dataset window are entirely absent. The model should not be interpreted as a survey of the most dangerous objects in the solar system.

**Mitigation.** Communicate the list explicitly as a close-approach risk ranking. Avoid statements that imply the #1-ranked asteroid is the most dangerous asteroid known; it is the most concerning *among those making close approaches in the dataset window*.

---

### L3 — Dataset Window Dependency

**What it means.** Scoring covers only asteroid close approaches recorded in the configured date range (currently 2024-01-01 to 2026-12-31). An asteroid making its closest Earth approach in 2028 will not appear in the current dataset and will receive no score.

**Practical impact.** Absence of a rank is not evidence of absence of threat. The risk list is a snapshot of the specified window, not a complete catalogue. An asteroid may drop off the list between runs not because it became safer, but because its closest approach shifted outside the window as new orbital data were incorporated.

**Mitigation.** Re-run scoring periodically with an updated or extended date window. When communicating results, always include the dataset window dates prominently so consumers understand the temporal scope.

---

### L4 — Observation-Completeness Sensitivity

**What it means.** Asteroids without a diameter estimate in NeoWs are flagged `is_scorable = False` and excluded from all rankings. The absence of a diameter estimate is not random: it correlates with the asteroid being small, newly discovered, or poorly characterised. The model therefore systematically under-represents the most recently detected and least-characterised objects.

**Practical impact.** The risk list is biased toward well-observed asteroids. A freshly-discovered 200 m asteroid making a very close approach may be excluded from the ranking entirely because no diameter estimate exists yet — precisely when it might most warrant attention.

**Mitigation.** Track the non-scorable fraction each run (currently: total asteroids minus 4,084). A rising non-scorable fraction signals either expanding dataset coverage (more new discoveries) or degrading data completeness. Consider flagging newly-appeared close-approach asteroids without diameter estimates in a separate watch list.

---

### L5 — Static Weights

**What it means.** The four feature weights (0.40 / 0.30 / 0.20 / 0.10) are fixed constants derived from a physical threat hierarchy and validated by sensitivity analysis. They are not learned from historical outcome data, not adjusted by expert feedback over time, and not conditional on asteroid type or orbital class.

**Practical impact.** The model cannot adapt if domain knowledge shifts — for example, if new research suggests impact velocity is a more important discriminator than size for a specific asteroid size range. Sensitivity analysis confirms the current weights produce a stable and defensible ranking, but "defensible" is not the same as "optimal."

**Mitigation.** Re-run the sensitivity analysis after any major dataset extension or domain-knowledge update. Document all weight changes with explicit rationale. The current weights and their justification are recorded in `src/models/weights.json` and `docs/risk_model_design.md`.

---

### L6 — Non-Probabilistic Output

**What it means.** `risk_score` is a dimensionless number in [0, 1] produced by a weighted sum of normalized features. It is not a probability. A score of 0.45 does not mean "45% chance of impact" — it means the asteroid's normalized feature profile produces a weighted sum of 0.45 under the current formula.

**Practical impact.** Fine-grained rank differences are not meaningful. Two asteroids with scores 0.400 and 0.399 differ by less than the uncertainty in any individual feature estimate (particularly diameter, which is itself an estimated range). Treating adjacent ranks as ordered by genuine threat difference overstates the model's resolution.

**Mitigation.** Use the score to identify tiers — top 20, top 100 — rather than to rank adjacent entries as meaningfully distinct. When presenting results to non-technical audiences, describe the output as a relative risk ranking, not a probability or certainty.

---

### L7 — No Temporal Dynamics

**What it means.** The model scores each asteroid as a static snapshot using the best available data at the time of the run. It does not propagate orbital elements forward, does not model how observational refinements affect future close-approach predictions, and does not account for non-gravitational forces such as the Yarkovsky effect or radiation pressure.

**Practical impact.** An asteroid's true threat level may change substantially as its orbit is refined. A highly-ranked asteroid may have its close-approach distance revised upward (reducing true threat) with additional observations — but its score will not update until the next scoring run. Conversely, a lower-ranked asteroid may be on a trajectory that later observations will confirm as more threatening than current data suggest.

**Mitigation.** Re-run scoring regularly and compare rank-change patterns between runs as a proxy for the effect of orbital refinements. Significant rank movement between runs — particularly for asteroids in the top 20 — should trigger manual review of the underlying orbital data.
