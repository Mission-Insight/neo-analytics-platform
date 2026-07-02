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
| Total asteroids | 828 |
| Potentially Hazardous Objects (PHOs) | 90 (10.93%) |
| Non-hazardous | 738 (89.07%) |
| Total close approach records | 819 |
| Date range covered | 2026-01-01 – 2026-06-24 |

---

### Finding 1 — Size Is the Strongest Differentiator

PHOs are substantially larger than non-hazardous asteroids on every central measure:

| Statistic | PHOs (n=90) | Non-Hazardous (n=738) | Ratio |
|---|---|---|---|
| Median diameter (max est.) | ~429 m | ~76 m | ~5.6× |
| Mean diameter (max est.) | ~3.1× larger | — | — |

The 44 diameter outliers (3× IQR) flagged in the EDA are disproportionately PHOs, consistent with the size gap. Note: this ratio is partially structural — NASA's PHO definition requires H ≤ 22 (absolute magnitude), which enforces a minimum diameter of roughly 140 m. Small objects cannot be classified as hazardous regardless of orbit.

**Model implication:** Size is the highest-signal feature and should carry the most weight.

---

### Finding 2 — Velocity Shows Meaningful but Weaker Differentiation

PHOs approach Earth roughly 30% faster than non-hazardous asteroids:

| Statistic | PHOs | Non-Hazardous |
|---|---|---|
| Median velocity | ~16.5 km/s | ~12.7 km/s |
| Dataset mean | 13.8 km/s | — |

However, the velocity distributions overlap substantially (both groups span similar ranges with ~7 km/s standard deviations). The fastest recorded approach — 45.52 km/s — belongs to a non-hazardous asteroid. Velocity alone is a weak discriminator, but it carries real information when combined with other features.

The eccentricity–velocity relationship (r = 0.56) and perihelion distance–velocity relationship (r = −0.51) explain the PHO speed advantage: eccentric orbits that dip close to the Sun produce faster Earth encounters.

**Model implication:** Include velocity as a feature but do not overweight it. Its value is in combination with size and proximity, not in isolation.

---

### Finding 3 — Proximity Is Independent of Size and Velocity

The closest approaches are not the fastest ones. The EDA confirmed that proximity and velocity are effectively independent:

- The closest approach in the dataset (2013 GM3, ~260,528 km — inside the Moon's orbit) travelled at only 7.41 km/s.
- No PHOs appear in the top 20 closest approaches in the 2026 window.
- Miss distance and diameter show very weak negative correlation, driven by the MOID orbital criterion rather than a physical causal link.

This independence means proximity adds genuinely new information that size and velocity do not capture.

**Model implication:** Proximity should be included as a distinct, non-redundant feature. Using inverse miss distance (1/Distance) is appropriate since smaller distance = higher concern.

---

### Finding 4 — Encounter Frequency Is Not a Useful Per-Asteroid Feature

Monthly approach frequency across the dataset is approximately stable at ~137 approaches/month with no detectable seasonal trend.

> "Approach frequency is a dataset-level characteristic, not a per-asteroid property. It does not vary meaningfully across individual objects in this dataset and should not be included as a model feature."
> — EDA section 4.4.4

The dataset covers only six months (January–June 2026), and June data is incomplete. Multi-year patterns cannot be assessed from this window.

**Model implication:** The Frequency term in the core formula (`w4(Frequency)`) requires careful definition. Using raw close approach count from the current dataset is not a reliable signal. Options for story 5.3 include: using `data_arc_in_days` as a proxy for observational history, or setting `w4 = 0` with documentation of why.

---

### Finding 5 — No Single Feature Is Sufficient

From section 4.5.5:

> "No single feature achieves |r| > 0.5 with hazard status, confirming that a multi-feature model is necessary."

This validates the composite scoring approach defined in 5.1.1. The combination of size, velocity, and proximity covers three physically independent risk dimensions, and together they provide more discriminating power than any individual feature.

---

### Summary Table for Risk Model Design

| Dimension | EDA Support | Model Confidence |
|---|---|---|
| Size (diameter) | PHOs are 5.6× larger; 44 outliers are PHO-heavy | High |
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

**Justification:** PHOs are 5.6× larger than non-hazardous asteroids by median diameter. Size is the strongest single differentiator in the dataset and represents the potential destructive energy of an impact. 44 extreme outlier values (3× IQR) are disproportionately PHOs — extreme sizes are a genuine signal, not noise.

---

#### Feature 2 — Miss Distance (Proximity)

| Property | Value |
|---|---|
| Source table | `close_approaches` |
| Raw field | `miss_distance_km` |
| Derived value | `MIN(miss_distance_km)` across all recorded approaches |
| Aggregation | Per-asteroid minimum (worst-case proximity) |
| Direction | Lower = more risk (enters formula as `1/Distance`) |

**Justification:** Proximity is independent of both size and velocity, making it a non-redundant contributor. The dataset contains encounters inside the Moon's orbit (~260,528 km). Using the minimum (closest recorded approach) captures the worst-case proximity each asteroid has demonstrated.

---

#### Feature 3 — Relative Velocity

| Property | Value |
|---|---|
| Source table | `close_approaches` |
| Raw field | `relative_velocity_kps` |
| Derived value | `MAX(relative_velocity_kps)` across all recorded approaches |
| Aggregation | Per-asteroid maximum (worst-case speed) |
| Direction | Higher = more risk |

**Justification:** PHOs approach ~30% faster than non-hazardous asteroids (medians: 16.5 vs 12.7 km/s). Higher velocity means greater kinetic energy at impact and less warning time. The maximum is used to capture peak threat level rather than average behavior. The velocity–eccentricity relationship (r = 0.56) indicates this feature also partially encodes orbital shape information.

---

#### Feature 4 — Approach Count (Encounter Frequency)

| Property | Value |
|---|---|
| Source table | `close_approaches` |
| Raw field | `close_approach_id` |
| Derived value | `COUNT(close_approach_id)` per asteroid |
| Aggregation | Per-asteroid total |
| Direction | Higher = more risk |

**Justification (with caveat):** An asteroid that approaches Earth more frequently represents a recurring exposure opportunity. However, the EDA noted that approach count is weakly discriminating across individual objects in the current 6-month dataset — monthly totals are stable at ~137/month with no meaningful per-asteroid variation. This feature is included in the initial set because it appears in the Epic formula (`w4(Frequency)`) and may become more informative as the dataset grows over time. Its weight will be set conservatively (see section 5.4).

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

The EDA found that eccentricity correlates with velocity (r = 0.56) and perihelion distance correlates with velocity (r = −0.51). These relationships mean orbital parameters are already partially represented through the velocity feature — including them separately would introduce collinearity without clear added value.

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
