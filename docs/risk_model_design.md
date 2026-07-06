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

**1 — Missing diameter.** `estimated_diameter_min_km` or `estimated_diameter_max_km` is NULL in the `asteroids` table. `_add_diameter_feature` sets `diameter_km = None`. `_handle_missing_data` sets `is_scorable = False`. `_apply_formula` sets `risk_score = None`. The asteroid is excluded from all ranking.

**2 — Missing velocity or miss distance.** The asteroid has no records in `close_approaches` (LEFT JOIN returns no match). `MAX(relative_velocity_kps)` and `MIN(miss_distance_km)` both return NULL from the aggregation. `is_scorable = False`, `risk_score = None`.

**3 — Missing encounter frequency.** Not possible. SQL `COUNT` on an unmatched LEFT JOIN always returns 0. An asteroid with no approach records receives `encounter_frequency = 0`, but it also falls into case 2 above and is excluded as non-scorable before normalization.

In the current dataset all 4,084 asteroids are scorable, confirming that the 3-year pipeline window provided sufficient coverage to produce at least one close approach record for every ingested asteroid.

---

## 5.6 Model Validation

### 5.6.1 Top 100 Risk List

Generated from 4,084 scored asteroids (dataset: 2024-01-01 – 2026-12-31).
Output saved to `data/output/top_100_risk.csv`.

| Metric | Value |
|---|---|
| Asteroids scored | 4,084 |
| Score range (full dataset) | 0.0114 – 0.4749 |
| Score range (top 100) | 0.3562 – 0.4749 |
| PHOs in top 100 | 29 / 100 (29%) |
| PHO share of full dataset | 527 / 4,084 (12.9%) |

---

### 5.6.2 Review of Top-Ranked Objects

#### PHO Representation

PHOs make up 12.9% of the total dataset but 29% of the top 100 — a **2.25× overrepresentation**. This is the primary positive validation signal: without any direct use of the `is_potentially_hazardous` flag, the model independently elevates NASA-classified hazardous objects at more than twice their background rate. The composite formula is tracking dimensions that are genuinely correlated with hazard designation.

The highest-ranked PHO is **415029 (2011 UL21)** at rank 7 (score 0.4047), driven by a combination of large diameter (2.80 km, `diameter_norm` = 0.078), high velocity (25.88 km/s), and a relatively close approach (6.6M km).

---

#### Top-Ranked Non-PHO Analysis

Nine of the top 10 are non-PHOs. This is expected and explainable — each of these objects scores high by being extreme on one or two individual dimensions, not because they represent an overall threat profile that NASA would classify as hazardous.

**Rank 1 — 433 Eros (score 0.4749):** Scores almost entirely on size. At 35.77 km diameter it holds the dataset maximum (`diameter_norm = 1.0`), contributing 0.40 of its 0.475 score from the size term alone. Velocity (3.73 km/s) and miss distance (59.5M km) are both low-risk — Eros is large but slow and distant. NASA does not classify it as a PHO because its minimum orbital intersection distance (~0.15 AU) is well above the 0.05 AU threshold.

**Rank 5 — (2025 US6) (score 0.4070):** The inverse of Eros — tiny (0.003 km) but scores high purely on proximity. At 136,611 km it holds the dataset minimum miss distance (`miss_distance_norm = 1.0`), contributing 0.30 from the proximity term. Its velocity (2.08 km/s) is the lowest in the top 10. This object passed exceptionally close but posed little kinetic threat due to its small size and slow speed. Not classified as a PHO because it falls below NASA's minimum size threshold (~140 m).

**Rank 66 — 887 Alinda (score 0.3649):** Scores on size (7.41 km, `diameter_norm` = 0.207) despite a distant miss (12.3M km) and low velocity (8.25 km/s). A well-known large NEO not classified as a PHO due to its MOID exceeding the 0.05 AU cutoff.

---

#### Score Distribution

The score ceiling for the top 100 is **0.4749**, well below the theoretical maximum of 1.0. No asteroid in the dataset is simultaneously extreme across all four dimensions, which is physically expected — the closest approaches are not the fastest (confirmed by 2025 US6 at 2.08 km/s), and the largest objects are not always the closest. The formula is behaving as designed.

The spread across the top 100 is narrow (~0.12 from rank 1 to rank 100), meaning the 101st-ranked asteroid is not dramatically less concerning than the 50th. This is consistent with a dataset where most high-scoring objects are moderately elevated on one or two dimensions rather than extreme on all.

---

#### Data Integrity Flags

Two apparent duplicates appear in the top 100 and warrant investigation:

| Ranks | Name | Asteroid IDs | Score |
|---|---|---|---|
| 29 & 30 | (2013 FW13) | 3633188 and 2837253 | 0.37971 (identical) |
| 93 & 94 | (1998 SH2) | 2875163 and 3014109 | 0.35741 (identical) |

Both pairs share the same name, identical scores, and near-identical feature values. These likely represent the same physical object recorded under two different provisional designations in the NeoWs API. The duplicates do not affect score correctness — each row is independently scored — but they inflate rank counts and should be investigated as part of 5.6.4.

---

#### Summary Assessment

| Finding | Assessment |
|---|---|
| PHOs overrepresented 2.25× in top 100 | Positive — model tracks hazard-correlated dimensions without using the flag directly |
| Top 6 ranks are non-PHOs | Expected — each driven by a single extreme feature value (size or proximity) that NASA's classification does not weight identically |
| Score ceiling ~0.475 | Expected — no asteroid dominates all four dimensions simultaneously |
| Duplicate entries (ranks 29/30, 93/94) | Flag for investigation — likely same objects under alternate designations |

Overall the rankings appear **sensible**. The model is not producing arbitrary outputs: large, fast, or close objects consistently score high; small, slow, and distant objects score low. PHO overrepresentation without direct use of the PHO flag is meaningful convergent validation.

---

### 5.6.3 Comparison Against Hazardous Classification

#### Methodology

The `is_potentially_hazardous` flag is treated as a reference signal rather than a ground truth. NASA's PHO criteria — minimum orbit intersection distance ≤ 0.05 AU and absolute magnitude H ≤ 22 — are independent of the model's four features, but they are physically motivated by the same underlying concerns (size and orbital proximity). Meaningful overlap between model rankings and PHO designation is therefore evidence of construct validity without requiring the two to agree perfectly.

Baseline: 527 of 4,084 scored asteroids are PHOs = **12.9%**. Any tier with a PHO rate above 12.9% indicates positive lift — the model is concentrating PHOs above their background rate.

---

#### PHO Precision at Rank Cutoffs

| Rank cutoff | PHOs found | PHO rate | Baseline | Lift |
|---|---|---|---|---|
| Top 10 | 1 | 10% | 12.9% | 0.78× |
| Top 25 | 8 | 32% | 12.9% | 2.48× |
| Top 50 | 15 | 30% | 12.9% | 2.33× |
| Top 100 | 29 | 29% | 12.9% | 2.25× |

**PHO recall at top 100:** 29 of 527 total PHOs = **5.5%**

---

#### PHO Distribution by Rank Tier

| Tier | PHOs | Slots | PHO rate | Lift |
|---|---|---|---|---|
| Ranks 1–10 | 1 | 10 | 10% | 0.78× |
| Ranks 11–50 | 14 | 40 | 35% | 2.71× |
| Ranks 51–100 | 14 | 50 | 28% | 2.17× |

The first PHO appears at **rank 7** (415029 2011 UL21). The lowest-ranked PHO in the top 100 is **rank 99** (162882 2001 FD58).

---

#### Interpretation

**Top 10 underperformance (lift 0.78×):** Ranks 1–6 are occupied by non-PHOs with single-dimension extremes — 433 Eros dominates on size alone; (2025 US6) dominates on proximity alone. Neither satisfies NASA's combined size–MOID criteria. The model is doing exactly what it was designed to do: score on multiple observed dimensions, not replicate PHO classification. The slight below-baseline PHO rate in the top 10 is a consequence of the formula faithfully scoring extreme-but-narrow cases ahead of more broadly threatening ones.

**Ranks 11–50 concentration (lift 2.71×):** This is the strongest zone of PHO overrepresentation. Objects here tend to be moderately large and fast without holding extreme values on any single feature — the profile most consistent with NASA's combined-criterion classification. The 14 PHOs in this tier include well-characterised objects such as 276033 (2002 AJ129), 439437 (2013 NK4), and 523808 (2007 ML24), which score on multiple dimensions simultaneously.

**Stable overrepresentation through ranks 51–100 (lift 2.17×):** PHO concentration remains above 2× baseline throughout the remainder of the list, indicating the model's moderate scores are also meaningful, not noise.

**Score separation:** The mean score of the 29 PHOs in the top 100 is approximately **0.374**, compared to approximately **0.379** for the 71 non-PHOs. The gap is narrow (~0.005) because the extreme non-PHOs at ranks 1–6 pull the non-PHO average up; within ranks 10–100 the two groups are nearly indistinguishable by score alone. This is expected — the model scores risk dimensions, not hazard classification, and many PHOs and non-PHOs occupy similar positions in the multi-dimensional feature space.

---

#### Summary

| Metric | Value |
|---|---|
| Overall lift at top 100 | 2.25× |
| Peak lift (ranks 11–50) | 2.71× |
| First PHO rank | 7 |
| PHO recall at top 100 | 5.5% (29 / 527) |

The comparison confirms a positive but imperfect relationship between model rankings and PHO designation. The model elevates PHOs at 2.25× their background rate across the full top 100 and at 2.71× in the rank 11–50 tier where multi-feature scoring is strongest. It is not a PHO classifier — nor was it designed to be — but the convergence validates that the four selected features and their weights are measuring dimensions that are genuinely correlated with established hazard criteria.

---

### 5.6.4 Unexpected Rankings Investigation

#### Overview

Two categories of anomaly were identified during review of `data/output/top_100_risk.csv`: (1) unusually high-ranking objects whose scores are driven by a single extreme feature, and (2) data integrity issues where the same physical asteroid appears twice under different NeoWs identifiers.

---

#### Category 1 — Single-Dimension Score Extremes

Two objects hold the dataset maximum for one feature and therefore rank in the top 5 despite not representing an overall threat profile:

| Rank | Name | Driving feature | Feature value | Notes |
|---|---|---|---|---|
| 1 | 433 Eros | Size (`diameter_norm = 1.0`) | 35.77 km | Slow (3.73 km/s), distant (59.5M km); MOID ~0.15 AU above PHO threshold |
| 5 | (2025 US6) | Proximity (`miss_distance_norm = 1.0`) | 136,611 km | Tiny (0.003 km), slow (2.08 km/s); below NASA minimum size for PHO |

These rankings are **expected model behavior**, not defects. The formula scores all four features independently; an asteroid that is maximally extreme on one dimension will always rank high even if the remaining dimensions are low. They are documented here because they would surprise a reader who expects model ranks to approximate hazard classification.

**Finding:** No corrective action is needed. Scores are mathematically correct. The behaviour should be noted in user-facing documentation so that the score is not misread as a PHO likelihood.

---

#### Category 2 — Duplicate Physical Objects Under Multiple Designations

Two physical asteroids each appear twice in the top 100 under separate NeoWs identifiers, consuming two rank slots each.

##### Pair A — (2013 FW13), ranks 29 and 30

| Field | Rank 29 (provisional) | Rank 30 (numbered) |
|---|---|---|
| Asteroid ID | 3633188 | 2837253 |
| Name | (2013 FW13) | 837253 (2013 FW13) |
| `diameter_km` | 0.19932 | 0.19932 |
| `velocity_kps` | 19.7564637 | 19.7564590 |
| `miss_distance_km` | 3,249,430 | 3,249,430 |
| `encounter_frequency` | 2 | 2 |
| `risk_score` | 0.37971 | 0.37971 |

The velocity differs at the 7th decimal place (19.7564**637** vs 19.7564**590**). This is consistent with two separate NASA API fetches of the same close approach record returning slightly different floating-point representations. The resulting `risk_score` values round to the same 5-decimal representation; the true computed scores differ by ~1.7 × 10⁻⁸.

##### Pair B — (1998 SH2), ranks 93 and 94

| Field | Rank 93 (numbered) | Rank 94 (provisional) |
|---|---|---|
| Asteroid ID | 2875163 | 3014109 |
| Name | 875163 (1998 SH2) | (1998 SH2) |
| `diameter_km` | 0.28678 | 0.28678 |
| `velocity_kps` | 17.30020 | 17.30020 |
| `miss_distance_km` | 3,108,484 | 3,108,484 |
| `encounter_frequency` | 1 | 1 |
| `risk_score` | 0.35741 | 0.35741 |

Feature values and score are bit-for-bit identical, indicating both records were populated from exactly the same API response.

##### Root Cause

NASA's NeoWs API exposes asteroids under both their **permanent minor planet number** (e.g., `837253`) and their **provisional designation** (e.g., `2013 FW13`). When the same object is returned by the API under two designations within overlapping date ranges, the ingestion pipeline records it as two separate asteroids. NeoWs asteroid IDs follow a pattern: IDs with a leading `2` prefix (e.g., `2837253`) encode the permanent catalog number; IDs with a leading `3` prefix (e.g., `3633188`) encode a provisional identifier. Both sets of IDs are valid NeoWs references to the same object.

| Designation type | ID pattern | Example |
|---|---|---|
| Permanent (numbered) | `2` + catalog number | 2837253 → asteroid 837253 |
| Provisional | `3` + internal code | 3633188 → (2013 FW13) |

##### Impact

- Each duplicate pair occupies two rank slots, compressing all downstream ranks by one position per pair. Ranks 31 onward are effectively one position lower than they would be after deduplication.
- Scores are independently correct for each record — no scoring logic error is involved.
- PHO classification is unaffected: both entries in each pair carry the same `is_potentially_hazardous` value.
- The top-100 list contains 98 unique physical objects, not 100.

##### Recommendation

Deduplication should be applied at the ingestion layer, not the scoring layer. The preferred key for deduplication is the asteroid's canonical name (the parenthetical provisional designation appears to be stable across both record types). An alternative is to cross-reference the NeoWs `links.self` URL, which encodes the canonical ID.

Until deduplication is implemented, a post-processing filter on `compute_risk_scores` output can collapse duplicate names to the entry with the lower (permanent) asteroid ID, retaining the numbered designation as the canonical record.

---

#### Summary of Findings

| Anomaly | Type | Impact | Action required |
|---|---|---|---|
| Rank 1 (433 Eros) — size-only extreme | Expected model behavior | None on scoring | Document in user-facing output |
| Rank 5 (2025 US6) — proximity-only extreme | Expected model behavior | None on scoring | Document in user-facing output |
| Ranks 29/30 — (2013 FW13) duplicate | Data integrity: numbered vs provisional ID | 2 slots → 1 physical object | Deduplicate at ingestion |
| Ranks 93/94 — (1998 SH2) duplicate | Data integrity: numbered vs provisional ID | 2 slots → 1 physical object | Deduplicate at ingestion |

---

## 5.7 Sensitivity Analysis

**Purpose:** Understand how model behavior changes as weight parameters vary, identify which features dominate the rankings, and determine whether the baseline weights are the best defensible choice.

---

### 5.7.1 Vary Weight Parameters

#### Scenarios

Five weight configurations were tested. Each configuration sums to 1.0 and is scored against all 4,084 scorable asteroids.

| Scenario | `size` (w₁) | `proximity` (w₂) | `velocity` (w₃) | `frequency` (w₄) | Rationale |
|---|---|---|---|---|---|
| **Baseline** | 0.40 | 0.30 | 0.20 | 0.10 | Current production weights (section 5.4.1) |
| **Size-dominant** | 0.60 | 0.20 | 0.15 | 0.05 | Maximises physical size as the primary signal; motivated by kinetic energy ∝ m ∝ diameter³ |
| **Proximity-dominant** | 0.20 | 0.50 | 0.20 | 0.10 | Maximises orbital proximity; nearest-approach distance as the dominant threat criterion |
| **Velocity-dominant** | 0.20 | 0.20 | 0.50 | 0.10 | Maximises impact speed; motivated by kinetic energy ∝ v² |
| **Equal weights** | 0.25 | 0.25 | 0.25 | 0.25 | Flat prior — no feature receives preferential weighting |

#### Methodology

Normalization ranges (`min` and `max` for each feature) are computed once from the full scorable set and held constant across all five scenarios. This ensures that any rank changes reflect the weight rebalancing alone, not a shift in normalization caused by different scoring populations. The formula applied per scenario is:

```
Risk(a) = w₁ · diameter_norm + w₂ · miss_distance_norm + w₃ · velocity_norm + w₄ · encounter_frequency_norm
```

Each scenario produces a complete independent ranking of all 4,084 scorable asteroids. Analysis compares ranks against the baseline to measure stability and identify dominant features.

#### Output

- **`data/output/sensitivity_analysis.csv`** — top-100 baseline asteroids with all five scenario ranks and scores as columns (`rank_baseline`, `score_baseline`, `rank_size_dominant`, etc.)
- Console: top-20 comparison table per scenario; rank-change grid for baseline top 50; mean absolute rank change summary

#### Execution Results

All five scenarios executed successfully against 4,084 scorable asteroids. Output saved to `data/output/sensitivity_analysis.csv` (100 rows × 14 columns).

**Top 5 per scenario:**

| Rank | Baseline | Size-dominant | Proximity-dominant | Velocity-dominant | Equal weights |
|---|---|---|---|---|---|
| 1 | 433 Eros | 433 Eros | (2025 US6) | (2015 TD323) | (2025 US6) |
| 2 | 66008 (1998 QH2) | 887 Alinda | (2019 PJ) | 465402 (2008 HW1) | (2012 VC26) |
| 3 | (2019 PJ) | 66008 (1998 QH2) | (2018 SP2) | (2018 YC2) | (2014 QZ295) |
| 4 | (2014 WF6) | 415029 (2011 UL21) | (2014 WF6) | 276033 (2002 AJ129) | (2015 TD323) |
| 5 | (2025 US6) | 66146 (1998 TU3) | (2019 XF2) | (2019 CH1) | (2018 SP2) |

**Notable observations:**

- **433 Eros** (baseline 1) holds rank 1 under size-dominant but collapses to rank 2279 under proximity-dominant and 1478 under velocity-dominant. Confirmed single-dimension size extreme — no proximity or velocity signal.
- **(2025 US6)** (baseline 5) holds rank 1 under both proximity-dominant and equal-weights. It combines `miss_distance_norm = 1.0` (closest approach in dataset) with `encounter_frequency_norm = 1.0` (maximum encounter frequency, 8 recorded approaches), making it dominant under any weighting that values both dimensions. Falls to rank 56 under size-dominant and 770 under velocity-dominant due to its tiny diameter and slow approach speed.
- **887 Alinda** (baseline 66) rises to rank 2 under size-dominant (`diameter_norm = 0.207`, second largest in dataset after Eros). It is effectively invisible under the baseline formula because its proximity and velocity scores are weak. Under equal-weights it falls further to rank 535.
- **(2015 TD323)** (baseline 12) rises to rank 1 under velocity-dominant (`velocity_norm = 0.780`) and holds top-5 under equal-weights (rank 4), showing it is a genuine multi-feature scorer — high on both velocity and proximity.
- **(2018 YC2)** (baseline 87) rises to rank 3 under velocity-dominant (`velocity_norm = 0.802`, highest in the dataset), but weak proximity (`miss_distance_norm = 0.660`) keeps it below (2015 TD323) even under the velocity-dominant formula.
