# NeoWs API Notes

## Base URL

```txt id="5tnglq"
https://api.nasa.gov/neo/rest/v1/
```

---

## Feed Endpoint

Purpose:
Retrieve asteroid data within a date range.

Important Parameters:
- start_date
- end_date
- api_key

Important Response Fields:
- element_count
- near_earth_objects
- estimated_diameter
- close_approach_data

Advantages:
- Time-oriented
- Efficient ingestion
- Supports analytics workflows
- Naturally supports scheduled ETL

Disadvantages:
- Limited historical range
- Not a complete asteroid catalog

Recommended Use:
Primary ingestion endpoint.

---

## Browse Endpoint

Purpose:
Browse many asteroids with pagination.

Important Concepts:
- page number
- page size
- total pages

Advantages:
- Large-scale dataset access
- Supports pagination

Disadvantages:
- Less relevant for time-based analytics
- Higher ingestion volume

Recommended Use:
Supplementary enrichment source.

---

## Lookup Endpoint

Purpose:
Retrieve one asteroid by ID.

Advantages:
- Detailed object data
- Useful for drill-down analysis

Disadvantages:
- Inefficient for bulk ingestion

Recommended Use:
On-demand detail retrieval.

---

## Key Observations

- API responses use nested JSON
- Pagination limits large responses
- API keys are required for authentication
- Dates are heavily used in querying

# Final Recommendation

The Feed endpoint is the best primary ingestion endpoint because the NEO Analytics Platform focuses on time-bounded asteroid close-approach events and analytical trend processing.

# Core NeoWs Data Fields

| Field | Type | Purpose | Importance |
|---|---|---|---|
| id | string | Unique asteroid identifier | Database primary key |
| name | string | Asteroid name | Human-readable labeling |
| estimated_diameter | float range | Asteroid size estimate | Risk analysis |
| is_potentially_hazardous_asteroid | boolean | Hazard classification | Filtering and analytics |
| close_approach_date | date | Date of Earth approach | Time-series analysis |
| miss_distance | float | Distance from Earth | Risk metrics |
| relative_velocity | float | Speed relative to Earth | Motion analytics |