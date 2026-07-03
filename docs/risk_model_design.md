# Risk Model Design

## 5.1.1 Definition of "Risk" for This Project

### What Risk Means Here

In this project, **risk** is a relative, explainable score that quantifies how concerning a Near-Earth Object is based on its measurable physical and orbital characteristics.

Risk does **not** represent:

- the probability that an asteroid will impact Earth
- an official planetary defense threat assessment
- a replacement for NASA's Torino or Palermo scale ratings

Risk **does** represent:

- a composite ranking of how much potential harm an asteroid could cause, based on the data available in this platform
- a tool for prioritizing which objects deserve closer attention
- a transparent, formula-driven score that can be explained and defended

---

### Risk Dimensions

Risk is evaluated across four measurable dimensions drawn from the NeoWs dataset:

| Dimension | Field(s) Used | Rationale |
|---|---|---|
| **Size** | `estimated_diameter_min_km`, `estimated_diameter_max_km` | Larger objects carry greater destructive potential on impact |
| **Velocity** | `relative_velocity_kps` | Faster objects deliver more kinetic energy and leave less warning time |
| **Proximity** | `miss_distance_km` | Closer approaches represent a higher potential for danger; contribution is inverse of distance |
| **Frequency** | count of `close_approach` records | Objects that approach Earth more often present more recurring exposure opportunities |

---

### Core Formula

```
Risk = w1(Size) + w2(Velocity) + w3(1 / Distance) + w4(Frequency)
```

Each dimension is normalized before weighting so that no single factor dominates due to scale differences. Weights are defined and justified in section 5.4.

---

### Assumptions

- All four dimensions contribute positively to risk — there is no protective factor in this model.
- Risk scores are computed relative to the current dataset. A score of 90 means high risk *among observed asteroids*, not in absolute terms.
- The `is_potentially_hazardous` NASA flag is available but treated as a supplementary signal, not a primary input, to keep the scoring model independently derived.

---

### What This Definition Rules Out

The following variables are **excluded from the risk definition** and are documented in section 5.1.4:

- Orbital parameters (eccentricity, inclination, semi-major axis, etc.) — scientifically relevant but require domain expertise to weight correctly
- Absolute magnitude — correlated with size but redundant given diameter estimates
- Orbiting body — all records in scope orbit Earth; this field adds no discriminating power

---

## 5.1.2 Evidence Summary from Epic 4 EDA

Source: `notebooks/eda.ipynb`

### Dataset Snapshot

| Metric | Value |
|---|---|
| Total NEOs in database | 4,084 |
| NEOs with close approaches | 828 |
| Potentially Hazardous Objects (PHOs) | 90 (10.9% of those with approaches) |
| Non-hazardous | 738 (89.1% of those with approaches) |
| Total close approach records | 5,551 |
| Date range covered | 2024-01-01 – 2026-12-31 |

---

### Finding 1 — Size Is the Strongest Differentiator

PHOs are substantially larger than non-hazardous asteroids on every central measure:

| Statistic | PHOs (n=90) | Non-Hazardous (n=738) | Ratio |
|---|---|---|---|
| Median diameter (max est.) | ~429 m | ~104 m | ~4.1× |
| Mean diameter (max est.) | ~2.2× larger | — | — |

The 128 diameter outliers (3× IQR fence at 1.251 km) flagged in the EDA are disproportionately PHOs, consistent with the size gap. Note: this ratio is partially structural — NASA's PHO definition requires H ≤ 22 (absolute magnitude), which enforces a minimum diameter of roughly 140 m. Small objects cannot be classified as hazardous regardless of orbit.

**Model implication:** Size is the highest-signal feature and should carry the most weight.

---

### Finding 2 — Velocity Shows Meaningful but Weaker Differentiation

PHOs approach Earth roughly 30% faster than non-hazardous asteroids:

| Statistic | PHOs | Non-Hazardous |
|---|---|---|
| Median velocity | ~16.5 km/s | ~12.6 km/s |
| Dataset mean | 15.1 km/s | — |

However, the velocity distributions overlap substantially (both groups span similar ranges with ~7 km/s standard deviations). The fastest recorded approach — 51.70 km/s by 504181 (2006 TC) on 2025-10-12 — belongs to a non-hazardous asteroid. Velocity alone is a weak discriminator, but it carries real information when combined with other features.

The eccentricity–velocity relationship (r = 0.53) and perihelion distance–velocity relationship (r = −0.55) explain the PHO speed advantage: eccentric orbits that dip close to the Sun produce faster Earth encounters.

**Model implication:** Include velocity as a feature but do not overweight it. Its value is in combination with size and proximity, not in isolation.

---

### Finding 3 — Proximity Is Independent of Size and Velocity

The closest approaches are not the fastest ones. The EDA confirmed that proximity and velocity are effectively independent:

- The closest approach in the dataset ((2025 US6), ~136,611 km — inside the Moon's orbit) travelled at only ~2.1 km/s.
- No PHOs appear in the very closest approaches — the closest recorded PHO approach was ~2.21 million km.
- Miss distance and diameter show very weak negative correlation (r = −0.012), driven by the MOID orbital criterion rather than a physical causal link.

This independence means proximity adds genuinely new information that size and velocity do not capture.

**Model implication:** Proximity should be included as a distinct, non-redundant feature. Using inverse miss distance (1/Distance) is appropriate since smaller distance = higher concern.

---

### Finding 4 — Encounter Frequency Is Not a Useful Per-Asteroid Feature

Monthly approach frequency across the dataset is approximately stable at ~154 approaches/month with no detectable seasonal trend.

> "Approach frequency is a dataset-level characteristic, not a per-asteroid property. It does not vary meaningfully across individual objects in this dataset and should not be included as a model feature."
> — EDA section 4.4.4

The dataset covers 36 months (January 2024–December 2026). Year-over-year variation is observable (~171/month in 2024, ~138/month in 2025, ~153/month in 2026), but no strong directional trend is visible across the full window.

**Model implication:** The Frequency term in the core formula (`w4(Frequency)`) requires careful definition. Using raw close approach count from the current dataset is not a reliable signal. Options for story 5.3 include: using `data_arc_in_days` as a proxy for observational history, or setting `w4 = 0` with documentation of why.

---

### Finding 5 — No Single Feature Is Sufficient

From section 4.5.5:

> "No single feature achieves |r| > 0.40 with hazard status, confirming that a multi-feature model is necessary."

This validates the composite scoring approach defined in 5.1.1. The combination of size, velocity, and proximity covers three physically independent risk dimensions, and together they provide more discriminating power than any individual feature.

---

### Summary Table for Risk Model Design

| Dimension | EDA Support | Model Confidence |
|---|---|---|
| Size (diameter) | PHOs are 4.1× larger; 128 outliers are PHO-heavy | High |
| Velocity | PHOs ~30% faster; high overlap; not sufficient alone | Medium |
| Proximity (1/Distance) | Independent of size and velocity; sub-lunar encounters exist | High |
| Frequency (encounter count) | Dataset-level metric; weak per-asteroid signal | Low — requires further design decision |

---

## 5.1.3 Initial Risk Factor Selection

### Selected Features

The following four variables are recommended as the initial feature set for the risk scoring model.

---

#### Feature 1 — Diameter (Size)

| Property | Value |
|---|---|
| Source table | `asteroids` |
| Raw fields | `estimated_diameter_min_km`, `estimated_diameter_max_km` |
| Derived value | `(estimated_diameter_min_km + estimated_diameter_max_km) / 2.0` |
| Aggregation | Per-asteroid (one value per object) |
| Direction | Higher = more risk |

**Justification:** PHOs are 4.1× larger than non-hazardous asteroids by median diameter (~429 m vs ~104 m). Size is the strongest single differentiator in the dataset and represents the potential destructive energy of an impact. 128 extreme outlier values (3× IQR fence at 1.251 km) are disproportionately PHOs — extreme sizes are a genuine signal, not noise.

---

#### Feature 2 — Miss Distance (Proximity)

| Property | Value |
|---|---|
| Source table | `close_approaches` |
| Raw field | `miss_distance_km` |
| Derived value | `MIN(miss_distance_km)` across all recorded approaches |
| Aggregation | Per-asteroid minimum (worst-case proximity) |
| Direction | Lower = more risk (enters formula as `1/Distance`) |

**Justification:** Proximity is independent of both size and velocity, making it a non-redundant contributor. The dataset contains encounters inside the Moon's orbit (closest: ~136,611 km). Using the minimum (closest recorded approach) captures the worst-case proximity each asteroid has demonstrated.

---

#### Feature 3 — Relative Velocity

| Property | Value |
|---|---|
| Source table | `close_approaches` |
| Raw field | `relative_velocity_kps` |
| Derived value | `MAX(relative_velocity_kps)` across all recorded approaches |
| Aggregation | Per-asteroid maximum (worst-case speed) |
| Direction | Higher = more risk |

**Justification:** PHOs approach ~31% faster than non-hazardous asteroids (medians: 16.5 vs 12.6 km/s). Higher velocity means greater kinetic energy at impact and less warning time. The maximum is used to capture peak threat level rather than average behavior. The velocity–eccentricity relationship (r = 0.53) indicates this feature also partially encodes orbital shape information.

---

#### Feature 4 — Approach Count (Encounter Frequency)

| Property | Value |
|---|---|
| Source table | `close_approaches` |
| Raw field | `close_approach_id` |
| Derived value | `COUNT(close_approach_id)` per asteroid |
| Aggregation | Per-asteroid total |
| Direction | Higher = more risk |

**Justification (with caveat):** An asteroid that approaches Earth more frequently represents a recurring exposure opportunity. However, the EDA noted that approach count is weakly discriminating across individual objects — monthly totals are stable at ~154/month across the 3-year dataset with limited per-asteroid variation (median = 1 approach, max = 8). This feature is included in the initial set because it appears in the Epic formula (`w4(Frequency)`) and may become more informative as the dataset grows over time. Its weight will be set conservatively (see section 5.4).

---

### Feature Summary Table

| # | Feature | DB Field(s) | Aggregation | Direction | EDA Confidence |
|---|---|---|---|---|---|
| 1 | Diameter | `estimated_diameter_min_km`, `estimated_diameter_max_km` | Average (per asteroid) | ↑ Higher = more risk | High |
| 2 | Miss Distance | `miss_distance_km` | MIN (per asteroid) | ↓ Lower = more risk | High |
| 3 | Relative Velocity | `relative_velocity_kps` | MAX (per asteroid) | ↑ Higher = more risk | Medium |
| 4 | Approach Count | `close_approach_id` | COUNT (per asteroid) | ↑ Higher = more risk | Low |

All four features are available in the current schema with no new data collection required.

---

## 5.1.4 Excluded Variables

The following fields exist in the database schema but are intentionally omitted from the initial risk model. Each exclusion is justified below.

---

### Absolute Magnitude (`absolute_magnitude_h`)

**Excluded — redundant with diameter.**

Absolute magnitude H is used by NASA to derive `estimated_diameter_min_km` and `estimated_diameter_max_km`. Including both H and diameter in the same model would double-count the same underlying physical property. Diameter is preferred because it is more interpretable (kilometers vs. a logarithmic brightness scale) and directly represents the size dimension the model is meant to capture.

---

### Orbital Parameters (`eccentricity`, `inclination`, `semi_major_axis`, `orbital_period`, `perihelion_distance`, `aphelion_distance`, etc.)

**Excluded — scientifically meaningful but require domain expertise to weight defensibly.**

The EDA found that eccentricity correlates with velocity (r = 0.53) and perihelion distance correlates with velocity (r = −0.55). These relationships mean orbital parameters are already partially represented through the velocity feature — including them separately would introduce collinearity without clear added value.

Weighting orbital parameters correctly requires assumptions about orbital mechanics that go beyond what this dataset can validate in isolation. Incorporating them is a logical enhancement for a future model iteration once a domain-informed weighting rationale exists.

---

### `is_potentially_hazardous` (NASA Hazard Flag)

**Excluded — target-adjacent label, not an independent input.**

The `is_potentially_hazardous` flag is determined by NASA using criteria that overlap significantly with the features already in the model (minimum orbit intersection distance and absolute magnitude). Including it as a model input would partially encode the output in the input, making the score circular and less interpretable.

Its role in this platform is as a validation signal: if the model assigns high risk scores to objects that NASA also flags as hazardous, that is evidence the model is tracking the right dimensions.

---

### `orbiting_body`

**Excluded — no discriminating power in this dataset.**

Every close approach record in scope has `orbiting_body = 'Earth'`. This field carries no information for ranking or differentiating asteroids.

---

### `orbit_class_type`

**Excluded — categorical, not straightforwardly quantifiable.**

Orbit class (Aten, Apollo, Amor, etc.) describes the shape and location of an orbit but is a nominal category with no natural numeric ordering for risk. Encoding it would require assumptions about which orbital class is more dangerous that are not supported by the current dataset. This variable is better suited to filtering or segmentation in the dashboard (Epic 6) than as a scoring input.

---

### `data_arc_in_days`, `observations_used`, `orbit_uncertainty`

**Excluded — observational quality metrics, not risk signals.**

These fields describe how well an asteroid has been tracked, not how dangerous it is. A newly discovered object with a short data arc may have a high `orbit_uncertainty` simply because it has not been observed long enough — this does not make it more or less risky than a well-characterized object. Mixing data quality with risk magnitude would produce scores that reflect our knowledge gap rather than the object's characteristics.

---

### Summary of Excluded Variables

| Field | Reason for Exclusion |
|---|---|
| `absolute_magnitude_h` | Redundant — diameter is derived from it |
| `eccentricity`, `inclination`, `semi_major_axis`, etc. | Partially captured by velocity; requires domain expertise to weight |
| `is_potentially_hazardous` | Target-adjacent label; would make scoring circular |
| `orbiting_body` | Constant value across all records |
| `orbit_class_type` | Nominal category with no defensible numeric ordering |
| `data_arc_in_days`, `observations_used`, `orbit_uncertainty` | Data quality metrics, not risk signals |

---

## 5.2 Feature Engineering Decisions

### 5.2.3 Velocity Feature Strategy

Three aggregation strategies were evaluated for `relative_velocity_kps`:

| Strategy | Description | Decision |
|---|---|---|
| **Maximum** | `MAX(relative_velocity_kps)` across all recorded approaches | **Selected** |
| Average | `AVG(relative_velocity_kps)` across all recorded approaches | Rejected |
| Latest | velocity from the most recent `close_approach_date` | Rejected |

**Rationale for maximum:**

Risk scoring is a worst-case exercise. An asteroid that has demonstrated one very fast approach carries more concern than one that has only ever approached slowly, regardless of its average behavior. The maximum captures the ceiling of what the object is capable of — which is the relevant signal for prioritization.

Average was rejected because it dilutes genuine high-speed events. An asteroid with nine slow approaches and one extreme pass at 40 km/s would score nearly the same as one that has only ever been slow, which is not the intended behavior.

Latest was rejected because recency has no physical meaning in this context. The most recent recorded approach is an artifact of the dataset window, not a property of the asteroid.

**Implementation:** `velocity_kps = MAX(relative_velocity_kps)` computed in the SQL join, mapped to a clean feature name in Python.

---

### 5.2.4 Miss Distance Feature Strategy

The representative distance for each asteroid is its **minimum** recorded miss distance across all close approaches.

| Strategy | Description | Decision |
|---|---|---|
| **Minimum** | `MIN(miss_distance_km)` across all recorded approaches | **Selected** |
| Average | `AVG(miss_distance_km)` across all recorded approaches | Rejected |
| Latest | distance from the most recent `close_approach_date` | Rejected |

**Rationale for minimum:** Consistent with the worst-case philosophy applied to velocity. The closest an asteroid has ever come to Earth is the strongest proximity signal — an asteroid that has passed inside the Moon's orbit once is more concerning than one that has only ever passed at 50 million km, regardless of its typical behavior.

**Implementation:** `miss_distance_km = MIN(miss_distance_km)` computed in the SQL join, mapped to a clean feature name in Python.

---

### 5.2.5 Encounter Frequency Feature

`encounter_frequency = COUNT(close_approach_id)` per asteroid, computed in the SQL join.

This feature counts how many close approach records exist for each asteroid in the database. Unlike the other three features, it returns `0` (not NULL) for asteroids with no approach records, because SQL `COUNT` on an unmatched LEFT JOIN returns zero.

**Caveat carried forward from 5.1.2:** This is the weakest feature in the set. Monthly totals are stable at ~154/month across the 3-year dataset, and most asteroids have only a single recorded approach (median = 1, max = 8). Per-asteroid variation exists but remains limited. The feature is included because it is defined in the Epic formula (`w4(Frequency)`) and will become more meaningful as the dataset grows. Its weight in section 5.4 will reflect this limitation.

---

### 5.2.6 Missing Data Treatment Strategy

#### NULL inventory by feature

| Feature | Source | Can be NULL? | Cause |
|---|---|---|---|
| `diameter_km` | `estimated_diameter_min/max_km` | Yes (rare) | Asteroid record missing size data |
| `velocity_kps` | `max_relative_velocity_kps` | Yes | No close approach records for this asteroid |
| `miss_distance_km` | `min_miss_distance_km` | Yes | No close approach records for this asteroid |
| `encounter_frequency` | `approach_count` (COUNT) | No — always ≥ 0 | SQL COUNT returns 0 for unmatched LEFT JOIN rows |

#### Treatment: exclusion, not imputation

Asteroids missing any continuous scoring feature receive `is_scorable = False` and are excluded from composite score calculation. They remain in the dataset with NULL component scores.

**Why not impute?** Imputing velocity or miss distance for an asteroid with no close approach records would require inventing data — there is no recorded encounter to draw from. A score built on imputed proximity or speed would misrepresent actual risk. Exclusion is more honest: the model declines to score what it cannot measure.

**Why not use a worst-case fill?** Filling NULL velocity with the dataset maximum would rank unobserved asteroids as highly dangerous by assumption. That inflates risk for objects we simply haven't seen approach yet, which is not a defensible scoring decision.

#### Implementation

Each row receives an `is_scorable` boolean:

```python
is_scorable = (
    diameter_km is not None
    and velocity_kps is not None
    and miss_distance_km is not None
)
```

The normalization step (5.3) and formula step (5.4) only process rows where `is_scorable = True`.

---

## 5.3 Feature Normalization

### 5.3.1 Feature Range Analysis

Computed from 4,084 scorable asteroids (dataset: 2024-01-01 – 2026-12-31).

#### Diameter (km)

| Metric | Value |
|---|---|
| Min | 0.001500 km |
| Max | 35.772000 km |
| Spread | 35.770500 km |
| Median | 0.098500 km |
| Mean | 0.215000 km |

**Observation:** Heavily right-skewed — mean is more than 2× the median. Most asteroids are small (sub-100 m), while a small number of large PHOs pull the tail significantly. The full 3-year dataset extends the maximum from 3.2 km (partial dataset) to 35.8 km, a ~11× increase that substantially widens the spread. Min-max normalization will compress most asteroids toward 0, with large objects scoring distinctly higher. This is the intended behavior.

---

#### Velocity (km/s)

| Metric | Value |
|---|---|
| Min | 0.292900 km/s |
| Max | 51.704400 km/s |
| Spread | 51.411600 km/s |
| Median | 14.530900 km/s |
| Mean | 15.083600 km/s |

**Observation:** Well-behaved — mean and median remain close (~14.5–15.1 km/s). The distribution is roughly symmetric. The maximum extends slightly from 45.5 km/s (partial dataset) to 51.7 km/s with the full 3-year window. Min-max normalization will spread scores evenly across the range without distortion.

---

#### Miss Distance (km)

| Metric | Value |
|---|---|
| Min | 136,611 km |
| Max | 74,791,691 km |
| Spread | 74,655,080 km |
| Median | 33,062,564 km |
| Mean | 36,080,388 km |

**Observation:** Enormous absolute range (~547× from min to max). The minimum drops sharply from 260,528 km (partial dataset) to 136,611 km — nearly inside the Moon's orbit (~384,400 km) — indicating the 3-year window captured a significantly closer approach than the original 6-month slice. Mean and median are relatively close (~33–36M km), indicating a roughly symmetric core distribution despite the extreme minimum. Note: this feature is **inverted** in the formula — closer = higher risk — so normalization will be `1 − (value − min) / (max − min)`.

---

#### Encounter Frequency

| Metric | Value |
|---|---|
| Min | 1 |
| Max | 8 |
| Spread | 7 |
| Median | 1 |
| Mean | 1.3592 |

**Observation:** A notable improvement over the partial dataset, where spread was exactly 1 (max=2, mean=1.020). The 3-year window reveals asteroids with up to 8 recorded approaches, and the mean rises to 1.36. However, the feature remains heavily right-skewed — median is still 1, meaning the majority of asteroids have only a single recorded approach. After min-max normalization the range is 0–1, but the distribution is very sparse at the high end. The concern from 5.1.2 and 5.2.5 is reduced but not eliminated: this feature now has real discriminating power for multi-approach objects, but most asteroids will still normalize to 0. The weight assigned in section 5.4 should remain conservative.

---

### 5.3.1 Summary

| Feature | Min | Max | Spread | Skew | Normalization note |
|---|---|---|---|---|---|
| `diameter_km` | 0.002 km | 35.772 km | 35.771 km | High right-skew | Most scores cluster near 0; large objects separate clearly |
| `velocity_kps` | 0.293 km/s | 51.704 km/s | 51.412 km/s | Roughly symmetric | Clean min-max |
| `miss_distance_km` | 136,611 km | 74,791,691 km | 74,655,080 km | Roughly symmetric | Inverted: `1 − normalized` |
| `encounter_frequency` | 1 | 8 | 7 | Heavy right-skew | Sparse high end; conservative weight warranted |

---

### 5.3.4 Scaling Methodology

#### Method Selected: Min-Max Normalization

Each feature is scaled to `[0, 1]` using:

```
normalized = (value − min) / (max − min)
```

Where `min` and `max` are computed from scorable asteroids only. The degenerate case (`max == min`, meaning all asteroids have the same value) returns `0.0`.

Miss distance is **inverted** after normalization because the feature's risk direction is reversed — closer = more dangerous:

```
miss_distance_norm = 1 − normalized
```

Non-scorable asteroids receive `None` for all normalized fields and are excluded from the weighted sum in section 5.4.

---

#### Why Min-Max?

**Formula compatibility.** The risk formula is a weighted sum of feature contributions. For that sum to be meaningful, every feature must operate on the same scale. Min-max produces identical bounds `[0, 1]` for all four inputs, so no feature can dominate simply because of its unit of measurement.

**Interpretability.** A normalized score of `0.0` means the least extreme value in the dataset; `1.0` means the most extreme. This is intuitive and easy to explain: "this asteroid's diameter normalizes to 0.82" means it is among the largest 18% of observed objects. Z-score produces no such natural reading — a value of +2.3 is only interpretable if the reader understands standard deviations.

**No distributional assumptions.** Z-score standardization assumes a roughly normal distribution. Diameter and encounter frequency are both heavily right-skewed; standardizing them would still place most asteroids near 0 but with different semantics, and extreme outliers would produce z-scores well above 3 with no natural ceiling.

---

#### Alternatives Considered and Rejected

| Method | Reason Rejected |
|---|---|
| **Z-score (mean/std)** | Produces unbounded output; the composite score loses its fixed range. Also assumes normality, which diameter and frequency clearly violate. |
| **Log transform + min-max** | Would compress the diameter scale logarithmically. An asteroid 10× larger than another would contribute less than 10× more to the score — inconsistent with the goal of reflecting proportional physical size differences. |
| **Robust scaling (median/IQR)** | Designed to dampen the influence of outliers. In a risk model, extreme values (a 35 km asteroid, a 136,611 km miss) are the most important signals — dampening them is the wrong behavior. |
| **Percentile rank** | Monotonic and outlier-resistant, but loses magnitude information entirely. A jump from the 50th to the 51st percentile is treated identically to a jump from the 98th to the 99th percentile, regardless of the underlying values. |

---

#### Dataset-Relative Scoring

Normalization bounds are computed fresh from the live dataset each time `_build_features` is called. Scores are therefore **relative to the current dataset**, not fixed to an absolute scale. This has two implications:

1. Adding new asteroid records may shift normalization bounds, which will change individual scores without any change to the underlying data or formula.
2. A score of `1.0` on diameter means "the largest asteroid currently in the database," not "the largest possible asteroid."

This is an accepted trade-off for a relative ranking system. If absolute, stable scores are needed in the future, the bounds can be fixed constants derived from physical limits (e.g., the largest known NEO diameter).

---

## 5.4 Risk Formula Design

### 5.4.1 Initial Weighting Strategy

#### Formula

```
Risk = 0.40 × diameter_norm
     + 0.30 × miss_distance_norm
     + 0.20 × velocity_norm
     + 0.10 × encounter_frequency_norm
```

All four normalized inputs are in `[0, 1]`. The weights sum to `1.0`, so the composite risk score is also bounded to `[0, 1]`.

---

#### Weight Justification

| Feature | Weight | EDA Confidence |
|---|---|---|
| `diameter_norm` | **0.40** | High |
| `miss_distance_norm` | **0.30** | High |
| `velocity_norm` | **0.20** | Medium |
| `encounter_frequency_norm` | **0.10** | Low |

---

##### Size — 0.40

Size receives the highest weight because it is the strongest single differentiator between hazardous and non-hazardous asteroids in the dataset. Across 4,084 asteroids, PHOs have a median diameter of 0.310 km compared to 0.075 km for non-hazardous asteroids — approximately 4.1× larger — and a mean diameter of 0.415 km versus 0.185 km (~2.2× larger). Of the 128 diameter outliers identified at the 3× IQR threshold, 36 (28.1%) are PHOs, despite PHOs representing only 12.9% of the overall dataset. This 2.2× overrepresentation confirms that extreme sizes are genuine signal rather than noise. No single feature achieves |r| > 0.5 with hazard status, but size comes closest and carries the strongest physical interpretation: a larger asteroid delivers more kinetic energy on impact.

This weight is also supported by structural constraints in NASA's PHO classification: the H ≤ 22 magnitude criterion enforces a minimum diameter of approximately 140 m, meaning small asteroids are definitionally excluded from the hazardous category regardless of orbit. Size is not merely correlated with hazard — it partially defines it.

---

##### Proximity — 0.30

Proximity receives the second-highest weight because it is statistically independent of both size and velocity, meaning it adds information that neither of the other two high-confidence features captures. The closest recorded approach in the dataset is 136,611 km (asteroid 2025 US6) — well inside the Moon's orbit at ~384,400 km — at a velocity of only 2.08 km/s. This illustrates that the closest approaches are not the fastest. Miss distance and diameter show only a weak negative correlation, driven by the minimum orbital intersection distance (MOID) criterion used in PHO classification rather than any direct physical link.

Notably, none of the 20 closest approaches in the dataset belong to a PHO, which demonstrates that proximity and hazard classification are measuring different things — proximity contributes genuinely new discriminating information to the composite score that the other features do not replicate.

---

##### Velocity — 0.20

Velocity receives a medium weight reflecting its genuine but limited discriminating power. Across 4,084 asteroids, PHOs have a median maximum velocity of 17.18 km/s compared to 14.25 km/s for non-hazardous asteroids — approximately 21% faster. However, the distributions overlap substantially: both groups have a standard deviation of approximately 7.1 km/s, and the fastest recorded approach in the dataset (51.70 km/s, asteroid 504181 (2006 TC)) belongs to a non-hazardous object. Velocity alone is a weak discriminator; it adds value as a component of a multi-feature model, not in isolation.

The eccentricity–velocity correlation (r = 0.56) and perihelion distance–velocity correlation (r = −0.51) found in the EDA suggest that velocity partially encodes orbital shape information. This is useful, but it also means velocity is not a fully independent dimension — it carries some of the same signal as orbital parameters already excluded from the model (section 5.1.4). A weight of 0.20 reflects these constraints.

---

##### Encounter Frequency — 0.10

Encounter frequency receives the minimum weight because it is the weakest feature in the model. Across 5,551 close approach records spanning 36 months (2024–2026), the dataset averages approximately 154 approaches per month with no detectable per-asteroid trend, consistent with the EDA conclusion that "approach frequency is a dataset-level characteristic, not a per-asteroid property." The per-asteroid distribution is heavily right-skewed: median = 1, mean = 1.36, and 73.4% of asteroids (2,998 of 4,084) have exactly one recorded approach.

The feature is retained because it is defined in the core formula and does add signal for multi-approach objects (up to 8 recorded approaches). The 0.10 weight is the minimum that keeps it as an active contributor while ensuring it cannot meaningfully override the three higher-confidence features.

---

#### Why Weights Sum to 1.0

Requiring `w1 + w2 + w3 + w4 = 1.0` keeps the composite score bounded to `[0, 1]` without any additional scaling step. This makes the score directly interpretable as a weighted average of normalized feature contributions: a score of `0.75` means the asteroid scores, on average, in the 75th percentile of the observed range across its contributing dimensions.

---

#### Sensitivity and Revision

These weights are an initial, evidence-informed starting point. They are not derived from a statistical fitting procedure — there is no labeled "true risk" outcome to optimize against. The rationale above documents the reasoning so that future weight revisions can be made deliberately rather than arbitrarily.

---

### 5.4.3 Scoring Formula

#### Mathematical Model

For a scorable asteroid *a*, the composite risk score is:

```
Risk(a) = 0.40 · S(a) + 0.30 · P(a) + 0.20 · V(a) + 0.10 · F(a)
```

Where each term is a min-max normalized feature derived from the modeling dataset:

```
S(a) = ( diameter_km(a) − min_d ) / ( max_d − min_d )

P(a) = 1 − ( miss_distance_km(a) − min_p ) / ( max_p − min_p )

V(a) = ( velocity_kps(a) − min_v ) / ( max_v − min_v )

F(a) = ( encounter_frequency(a) − min_f ) / ( max_f − min_f )
```

`P(a)` is inverted so that closer approaches produce higher scores. All four normalized terms are in `[0, 1]`, and the weights sum to 1.0, so `Risk(a) ∈ [0, 1]` for all scorable asteroids.

For non-scorable asteroids (those missing diameter, velocity, or miss distance), `Risk(a) = NULL`. These asteroids are excluded from ranking.

---

#### Variable Definitions

| Symbol | Feature | Source field(s) | Aggregation |
|---|---|---|---|
| `diameter_km(a)` | Average diameter | `estimated_diameter_min_km`, `estimated_diameter_max_km` | `(min + max) / 2` per asteroid |
| `miss_distance_km(a)` | Closest recorded approach | `miss_distance_km` | `MIN` per asteroid |
| `velocity_kps(a)` | Fastest recorded approach | `relative_velocity_kps` | `MAX` per asteroid |
| `encounter_frequency(a)` | Total recorded approaches | `close_approach_id` | `COUNT` per asteroid |
| `min_x`, `max_x` | Normalization bounds | Computed from scorable rows | `MIN` / `MAX` across dataset |

---

#### Output Interpretation

| Score range | Interpretation |
|---|---|
| 0.00 – 0.20 | Low concern — small, slow, distant, infrequent |
| 0.20 – 0.40 | Below average — no single feature stands out |
| 0.40 – 0.60 | Moderate — notable on one or more dimensions |
| 0.60 – 0.80 | High — large, fast, or close by dataset standards |
| 0.80 – 1.00 | Very high — extreme on multiple dimensions |

A score of `1.0` is only achievable by an asteroid that simultaneously holds the dataset maximum for size, velocity, and encounter frequency, and the dataset minimum for miss distance. In practice, top scores will fall below 1.0 because no single asteroid is extreme on all four dimensions at once.

---

#### Edge Cases

See section 5.4.4 for full evaluation. Summary:

| Condition | Behaviour |
|---|---|
| `max == min` for a feature | `_minmax` returns `0.0`; feature contributes nothing to any score |
| Asteroid missing diameter, velocity, or miss distance | `is_scorable = False`; `risk_score = NULL` |
| Miss distance at or near zero | Handled by `_minmax`; a true zero would be below the dataset minimum and could produce a score marginally above 1.0 — this is a theoretical case that cannot occur in practice |
| Asteroid outside current dataset bounds | Scores may exceed `[0, 1]`; bounds are recomputed on each pipeline run, so this only occurs in incremental-load scenarios between runs |
| `encounter_frequency = 0` | Not possible — `COUNT` on a LEFT JOIN returns 0, but such an asteroid would have `NULL` velocity and miss distance and be excluded as non-scorable |

---

### 5.4.4 Edge Case Review

#### Zero Distance

A miss distance of 0 km would represent an actual impact event. NASA's NeoWs API does not record impacts, so this value cannot appear in the database. However, the formula's behaviour under this condition is still worth evaluating.

`_minmax` does not clamp its output. If `miss_distance_km = 0` and the dataset minimum is 136,611 km, the normalized value before inversion would be:

```
(0 − 136,611) / (74,791,691 − 136,611) ≈ −0.00183
```

After inversion: `1 − (−0.00183) ≈ 1.00183` — marginally above 1.0. The composite score would then also marginally exceed 1.0.

**Verdict:** No code change is needed. The data source (NASA NeoWs) structurally prevents this input. If the platform were ever extended to ingest impact records from a different source, a clamp to `[0, 1]` should be added to `_minmax`.

---

#### Extreme Values

The dataset minimum and maximum for each feature normalize to exactly `0.0` and `1.0` by construction, since `_minmax` is anchored to those bounds. This means:

- The asteroid with the smallest recorded diameter always scores `0.0` on the size dimension.
- The asteroid with the largest recorded diameter always scores `1.0` on the size dimension.
- The same holds for velocity, encounter frequency, and (after inversion) miss distance.

This is the intended behaviour — scores express position within the observed range, not absolute magnitude. The only risk is that a genuine outlier (e.g., a newly ingested 100 km asteroid) would compress all other diameter scores toward 0 once the bounds update on the next pipeline run. This is an accepted property of dataset-relative normalization, documented in section 5.3.4.

---

#### Missing Values

Three missing-data scenarios are possible:

**1 — Missing diameter.** `estimated_diameter_min_km` or `estimated_diameter_max_km` is NULL in the `asteroids` table. `_add_diameter_feature` sets `diameter_km = None`. `_handle_missing_data` sets `is_scorable = False`. `_compute_risk_scores` sets `risk_score = None`. The asteroid is excluded from all ranking.

**2 — Missing velocity or miss distance.** The asteroid has no records in `close_approaches` (LEFT JOIN returns no match). `MAX(relative_velocity_kps)` and `MIN(miss_distance_km)` both return NULL from the aggregation. `is_scorable = False`, `risk_score = None`.

**3 — Missing encounter frequency.** Not possible. SQL `COUNT` on an unmatched LEFT JOIN always returns 0. An asteroid with no approach records receives `encounter_frequency = 0`, but it also falls into case 2 above and is excluded as non-scorable before normalization.

In the current dataset all 4,084 asteroids are scorable, confirming that the 3-year pipeline window provided sufficient coverage to produce at least one close approach record for every ingested asteroid.
