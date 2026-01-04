# Dynamic Polygon - Design Document

## Overview

The `dynamic_polygon` procedural generation method creates complex, organic-looking polygons through iterative evolution. Starting with simple random vertices, it progressively modifies segments to create interesting shapes suitable for LoRA training datasets.

## Algorithm Flow

### Phase 1: Initialization
```
Input: vertices (count or range), bounds (x1,y1,x2,y2)
1. Resolve vertex count (pick random if range)
2. Generate N random points within bounds
3. Return unordered point list
```

### Phase 2: Connection
```
Input: Random points, connection method
1. If angle_sort:
   - Compute centroid of all points
   - Sort by atan2(y-cy, x-cx) for star pattern
2. If convex_hull:
   - Apply Graham scan (TODO: currently uses angle_sort)
3. Return ordered polygon vertices
```

### Phase 3: Weight Initialization
```
All segments start with weight = 1.0
Weights guide selection probability:
- Higher weight = more likely to be selected
- Freshly split segments get reduced weight (via decay)
- Encourages spreading modifications across shape
```

### Phase 4: Evolution Loop
```
For each iteration (0 to N):
  1. Select segment via weighted random
  2. Choose random operation from allowed list
  3. Determine depth_pct (random if range)
  4. For attempt in (0 to max_retries):
     a. Apply operation → new_points, new_weights
     b. Validate polygon (no self-intersections)
     c. If valid:
        - Update current_points, segment_weights
        - Update centroid
        - Record statistics
        - Break retry loop
     d. If invalid:
        - Increment failure counter
        - Retry with same operation
  5. If all retries fail, skip to next iteration
```

### Phase 5: Finalization
```
1. Create Polygon object from final points
2. Attach procedure metadata:
   - Parameters used
   - Statistics (successes, failures, operation counts)
3. Return polygon
```

## Operations

### split_offset
**Visual**: `A---B` → `A---M---B` (M offset perpendicular)

**Algorithm**:
1. Get segment endpoints A, B
2. Compute midpoint M = (A + B) / 2
3. Compute perpendicular direction (rotated 90°)
4. Apply direction bias (inward/outward/random)
5. Offset M by `depth_pct * segment_length`
6. Insert new point at index+1
7. Split weight: `old_weight → [new_weight, new_weight]` where `new_weight = old_weight * weight_decay`

**Points**: +1 (total)  
**Segments**: +1 (A-M, M-B instead of A-B)

### sawtooth
**Visual**: `A---B` → `A-/\-B` (triangular tooth)

**Algorithm**:
1. Get segment endpoints A, B
2. Compute midpoint M = (A + B) / 2
3. Compute perpendicular direction + bias
4. Create peak P = M + perpendicular * (segment_length * depth_pct)
5. Insert P at midpoint
6. Split weight: `old_weight → [new_weight, new_weight]`

**Points**: +1 (total)  
**Segments**: +1 (A-P, P-B instead of A-B)

**Note**: This is a simplified sawtooth. Full implementation could add base points at 1/3 and 2/3.

### squarewave
**Visual**: `A---B` → `A-|_|-B` (rectangular step)

**Algorithm**:
1. Get segment endpoints A, B
2. Compute points at 1/4 and 3/4 along segment: Q1, Q3
3. Compute perpendicular offset
4. Create four corner points:
   - P1 = Q1 (corner)
   - P2 = Q1 + offset (raised corner)
   - P3 = Q3 + offset (raised corner)
   - P4 = Q3 (corner)
5. Insert all four points
6. Weight update: `old_weight → [w, w, w, w, w]` (5 new segments)

**Points**: +4 (total)  
**Segments**: +4 (creates 5 segments from 1)

## Helper Methods

### _select_segment(weights)
Weighted random selection using cumulative distribution.

```python
total = sum(weights)
r = random.uniform(0, total)
cumulative = 0
for i, weight in enumerate(weights):
    cumulative += weight
    if r <= cumulative:
        return i
```

### _is_valid_polygon(points)
Checks for self-intersections using pairwise segment testing.

**Algorithm**:
- For each edge (i, i+1)
- Check against all non-adjacent edges (j, j+1) where j >= i+2
- Use cross-product intersection test
- Return False if any intersection found

### _segments_intersect(p1, p2, p3, p4)
Cross-product method for line segment intersection.

**Algorithm**:
- Segments intersect if endpoints are on opposite sides
- Uses CCW (counter-clockwise) test
- `ccw(A, B, C) = (C.y - A.y)(B.x - A.x) > (B.y - A.y)(C.x - A.x)`
- Intersect if: `ccw(p1,p3,p4) ≠ ccw(p2,p3,p4) AND ccw(p1,p2,p3) ≠ ccw(p1,p2,p4)`

### _get_perpendicular_direction(p1, p2, bias, centroid)
Computes perpendicular vector with directional bias.

**Algorithm**:
1. Segment direction: `(dx, dy) = (p2.x - p1.x, p2.y - p1.y)`
2. Perpendicular: `(perp_x, perp_y) = (-dy, dx)` (90° CCW rotation)
3. Normalize: `(perp_x, perp_y) / length`
4. Compute segment midpoint M
5. Vector from centroid to M: `(to_mid_x, to_mid_y)`
6. Dot product: `dot = perp · to_mid`
   - If `dot > 0`: perpendicular points away from centroid
   - If `dot < 0`: perpendicular points toward centroid
7. Apply bias:
   - `inward`: flip if dot > 0
   - `outward`: flip if dot < 0
   - `random`: 50% chance to flip

## Parameter Guide

### vertices
- **Type**: int or (min, max)
- **Effect**: Starting complexity
- **Recommendations**:
  - Simple shapes: 4-6
  - Medium complexity: 6-10
  - High complexity: 10-15

### iterations
- **Type**: int
- **Effect**: Number of evolution steps
- **Recommendations**:
  - Quick generation: 5-10
  - Moderate detail: 10-20
  - High detail: 20-50

### depth_range
- **Type**: float or (min, max)
- **Effect**: How far modifications protrude (as % of segment length)
- **Recommendations**:
  - Subtle: 0.1-0.3
  - Moderate: 0.2-0.6
  - Dramatic: 0.5-0.9

### weight_decay
- **Type**: float (0.0-1.0)
- **Effect**: How much new segments are de-prioritized
- **Recommendations**:
  - Spread modifications: 0.3-0.5 (aggressive decay)
  - Allow clustering: 0.7-0.9 (gentle decay)
  - Neutral: 0.5

### direction_bias
- **Type**: 'inward' | 'outward' | 'random'
- **Effect**: Preferred modification direction
- **Recommendations**:
  - Organic shapes: `inward`
  - Spiky shapes: `outward`
  - Varied: `random`

### operations
- **Type**: list of operation names
- **Effect**: Available modification types
- **Recommendations**:
  - Clean shapes: `['split_offset']`
  - Textured shapes: `['sawtooth']`
  - Complex shapes: `['split_offset', 'sawtooth', 'squarewave']`

## Testing Strategy

### Unit Tests
1. **_connect_angle_sort**: Verify points are sorted by angle
2. **_select_segment**: Test weighted distribution
3. **_segments_intersect**: Test intersection detection
4. **_get_perpendicular_direction**: Verify bias application

### Integration Tests
1. **Simple generation**: 5 vertices, 10 iterations, verify no crashes
2. **Range parameters**: Verify random selection works
3. **Validation**: Intentionally create invalid polygon, verify detection
4. **Statistics**: Verify stats are tracked correctly

### Visual Verification
```python
# Test script: scripts/test_proc.txt
CLEAR WIP ALL
PROC dynamic_polygon test1 VERTICES=5 BOUNDS=100,100,668,668 ITERATIONS=5
SAVE test_simple.png

CLEAR WIP ALL
PROC dynamic_polygon test2 PRESET=organic BOUNDS=100,100,668,668
SAVE test_organic.png

CLEAR WIP ALL
PROC dynamic_polygon test3 PRESET=complex BOUNDS=100,100,668,668
SAVE test_complex.png
```

### Batch Testing
```bash
# Generate 20 variations to verify randomness
BATCH 20 proc_test.txt variations MAIN
```

Expected outcomes:
- No two shapes should be identical
- All shapes should be valid (no self-intersections)
- Statistics should show successful modifications
- Visual diversity in results

## Edge Cases

### Degenerate Geometry
- **Issue**: Very small segments or nearly collinear points
- **Handling**: Caught by try/except in evolution loop, retries operation

### Failed Validations
- **Issue**: Operation creates self-intersection
- **Handling**: Max retries with same operation, then skip iteration

### All Weights Zero
- **Issue**: Extreme weight decay could zero all weights
- **Handling**: `_select_segment` falls back to uniform random

### Insufficient Bounds
- **Issue**: Bounds too small for requested vertices
- **Handling**: Random generation spreads points, may cluster

## Performance Considerations

### Time Complexity
- Generation: O(V) where V = vertex count
- Connection: O(V log V) for angle sort
- Per iteration: O(S²) where S = segment count (validation)
- Total: O(I × S²) where I = iterations

### Optimization Opportunities
1. **Spatial indexing**: Use quadtree for intersection tests
2. **Early termination**: Skip validation if operation is far from other segments
3. **Batch operations**: Apply multiple non-conflicting operations per iteration

### Typical Performance
- Simple (5 vertices, 10 iterations): < 10ms
- Medium (10 vertices, 20 iterations): < 50ms
- Complex (15 vertices, 50 iterations): < 200ms

## Future Enhancements

### Additional Operations
- **Spiral**: Rotate and scale segment endpoints
- **Wave**: Sinusoidal displacement along segment
- **Fractal**: Recursive subdivision with scaling

### Advanced Features
- **Symmetry constraints**: Force bilateral or radial symmetry
- **Anchor points**: Fix certain vertices during evolution
- **Path following**: Evolve along a guide curve

### Quality Metrics
- **Complexity score**: Measure final shape complexity
- **Diversity metric**: Compare shapes in batch for uniqueness
- **Aesthetic scoring**: ML-based shape quality assessment
