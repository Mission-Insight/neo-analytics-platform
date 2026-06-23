## Nesting Depth

Level 1
- links
- element_count
- near_earth_objects

Level 2
- date keys inside near_earth_objects

Level 3
- asteroid objects

Level 4+
- estimated_diameter
- close_approach_data
- relative_velocity
- miss_distance
- orbiting_body

## Repeated Structures

### Asteroid Record
Appears once per NEO.

### Close Approach Record
Appears multiple times per asteroid.

### Relative Velocity Record
Appears within each close approach.

### Miss Distance Record
Appears within each close approach.

## Optional Fields

Observed fields that may be absent or empty:

- sentry_object

## Nullability Patterns

Observed representations of missing data:

- presently, none so far