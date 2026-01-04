# Dynamic Polygon Debug Mode - User Guide

## Quick Reference

### Debug Parameters

```bash
VERBOSE = 0|1|2|3
  0 = Silent (default) - no debug output
  1 = Summary - final statistics only
  2 = Detailed - per-iteration logs (RECOMMENDED)
  3 = Full - includes all geometry data

SAVE_ITERATIONS = true|false
  Creates snapshot polygons showing evolution
  
SNAPSHOT_INTERVAL = N
  Save every Nth iteration (default: 1)
```

## Usage Examples

### Example 1: Understanding What Happened

**Problem**: Shape doesn't look right, need to understand the generation process.

```bash
PROC dynamic_polygon shape1 VERTICES=5 BOUNDS=100,100,600,600 ITERATIONS=10 VERBOSE=2
INFO shape1
```

**Output**:
```
=== PROCEDURAL GENERATION DEBUG LOG ===

Initial State:
  Vertices: 5
  Bounds: (100, 100, 600, 600)
  Centroid: (354.2, 378.5)
  Connection: angle_sort

--- Iteration 1 ---
Selection:
  Segment: 2 (weight: 1.000)
  Length: 245.3px
  Probability: 20.0%

Operation: split_offset
  Depth: 52% (127.6px offset)
  Direction: outward

Result:
  Points: 5 -> 6
  Validation: PASS [OK]

--- Iteration 2 ---
...

Final Statistics:
  Successful modifications: 8/10
  Failed attempts: 4
  Operations used:
    split_offset: 5
    sawtooth: 3
```

### Example 2: Visual Evolution

**Problem**: Want to see how shape evolved step-by-step.

```bash
# Generate with snapshots
PROC dynamic_polygon shape1 VERTICES=5 BOUNDS=100,100,600,600 ITERATIONS=10 SAVE_ITERATIONS=true

# List to see all snapshots
LIST WIP
```

**Output**:
```
WIP canvas shapes:
  shape1_iter_0 (Polygon)
  shape1_iter_1 (Polygon)
  shape1_iter_2 (Polygon)
  ...
  shape1_iter_10 (Polygon)
  shape1_final (Polygon)
  shape1 (Polygon)
```

**Visual Inspection**:
- Each `shape1_iter_N` shows the polygon at that iteration
- Can toggle visibility or delete snapshots to see progression
- Compare early vs late iterations

### Example 3: Debugging Failures

**Problem**: Many validation failures, need to understand why.

```bash
PROC dynamic_polygon shape1 VERTICES=10 BOUNDS=100,100,600,600 ITERATIONS=20 VERBOSE=3 SAVE_ITERATIONS=true
INFO shape1
```

**What to look for**:
- `VERBOSE=3` shows exact coordinates of new points
- Can see which segments caused intersections
- Snapshots show where shape was when failure occurred
- Retry counts indicate problem areas

### Example 4: Comparing Operations

**Problem**: Want to understand different operation behaviors.

```bash
CLEAR WIP ALL

# Test each operation individually
PROC dynamic_polygon split_test VERTICES=5 BOUNDS=100,100,300,300 \
  OPERATIONS=split_offset ITERATIONS=10 VERBOSE=2

PROC dynamic_polygon saw_test VERTICES=5 BOUNDS=400,100,600,300 \
  OPERATIONS=sawtooth ITERATIONS=10 VERBOSE=2

PROC dynamic_polygon square_test VERTICES=5 BOUNDS=100,400,300,600 \
  OPERATIONS=squarewave ITERATIONS=10 VERBOSE=2

# Compare logs
INFO split_test
INFO saw_test
INFO square_test
```

**Analysis**:
- Compare points added per iteration
- Compare validation success rates
- See which creates more complex shapes

### Example 5: High Iteration Runs

**Problem**: 50 iterations creates too many snapshots.

```bash
# Sample every 10 iterations
PROC dynamic_polygon shape1 VERTICES=8 BOUNDS=100,100,600,600 \
  ITERATIONS=50 SAVE_ITERATIONS=true SNAPSHOT_INTERVAL=10 VERBOSE=1

LIST WIP
```

**Output**:
```
WIP canvas shapes:
  shape1_iter_0 (Polygon)
  shape1_iter_10 (Polygon)
  shape1_iter_20 (Polygon)
  shape1_iter_30 (Polygon)
  shape1_iter_40 (Polygon)
  shape1_iter_50 (Polygon)
  shape1_final (Polygon)
  shape1 (Polygon)
```

Only 8 shapes instead of 52!

## Understanding the Debug Log

### Selection Section
```
Selection:
  Segment: 2 (weight: 1.000)
  Length: 245.3px
  Probability: 20.0%
```

**Interpretation**:
- Segment 2 was chosen (between points[2] and points[3])
- Current weight is 1.000 (newly split segments have lower weights)
- Had 20% chance of selection (1.0 / sum of all weights)
- Longer segments show more dramatic modifications

### Operation Section
```
Operation: split_offset
  Depth: 52% (127.6px offset)
  Direction: outward
```

**Interpretation**:
- Using split_offset operation
- Offset distance is 52% of segment length = 127.6 pixels
- Direction is "outward" (away from centroid)
- "inward" would mean toward centroid

### Result Section
```
Result:
  Points: 5 -> 6
  Validation: PASS [OK]
  Attempts: 1
```

**Interpretation**:
- Shape grew from 5 to 6 vertices
- No self-intersection detected (PASS)
- Succeeded on first try
- If attempts > 1, there were validation failures

### Statistics Section
```
Final Statistics:
  Successful modifications: 8/10
  Failed attempts: 4
  Operations used:
    split_offset: 5
    sawtooth: 3
```

**Interpretation**:
- 8 of 10 iterations succeeded (2 skipped due to failures)
- 4 total failed validation attempts across all iterations
- split_offset used 5 times, sawtooth 3 times
- If failed_attempts is high, consider:
  - Reducing depth_range
  - Increasing max_retries
  - Using simpler operations

## Troubleshooting

### Problem: Too many failed attempts

**Symptoms**:
```
Successful modifications: 3/20
Failed attempts: 85
```

**Solutions**:
1. Reduce depth: `DEPTH_RANGE=0.1,0.4` (less aggressive)
2. Increase retries: `MAX_RETRIES=20` (more attempts per iteration)
3. Use simpler operations: `OPERATIONS=split_offset` (avoid complex ones)
4. Start with fewer vertices: `VERTICES=4` (less congested)

### Problem: Not enough variation

**Symptoms**: All iterations use same operation/segments

**Check**:
```bash
INFO shape1  # Look at operations_used
```

**Solutions**:
1. Increase weight decay: `WEIGHT_DECAY=0.3` (spreads modifications)
2. More operations: `OPERATIONS=split_offset,sawtooth,squarewave`
3. Wider depth range: `DEPTH_RANGE=0.2,0.9`

### Problem: Can't see evolution clearly

**Solutions**:
```bash
# Fewer snapshots, more spacing
SAVE_ITERATIONS=true SNAPSHOT_INTERVAL=3

# Or just key frames
PROC ... ITERATIONS=15 SAVE_ITERATIONS=true SNAPSHOT_INTERVAL=5
# Shows iterations: 0, 5, 10, 15
```

## Best Practices

### During Development
```bash
# Start with verbose + snapshots
VERBOSE=2 SAVE_ITERATIONS=true ITERATIONS=5

# Once working, increase iterations
ITERATIONS=20 SNAPSHOT_INTERVAL=5

# Final tuning with summary only
VERBOSE=1 ITERATIONS=50
```

### For Production/BATCH
```bash
# No debug overhead
PROC dynamic_polygon shape1 VERTICES=RAND(5,8) BOUNDS=100,100,668,668
# Fast, no snapshots, no logs
```

### For Documentation
```bash
# Capture key evolution stages
SAVE_ITERATIONS=true SNAPSHOT_INTERVAL=3 ITERATIONS=9
# Save snapshots to show progression
```

### For Algorithm Validation
```bash
# Maximum detail
VERBOSE=3 SAVE_ITERATIONS=true ITERATIONS=10
# Verify geometric calculations are correct
```

## Performance Notes

### VERBOSE Impact
- VERBOSE=0: No overhead
- VERBOSE=1: Minimal (just counters)
- VERBOSE=2: Light (~5-10% slower, builds log)
- VERBOSE=3: Moderate (~10-20% slower, deep copies geometry)

### SAVE_ITERATIONS Impact
- Creates N+2 polygon objects (iter_0 through iter_N, final, main)
- Each polygon is a deep copy with full geometry
- Memory usage: ~1KB per vertex per snapshot
- Example: 10 iterations, 8 vertices = ~80KB

### Recommendations
- Use debug mode interactively, not in BATCH
- For BATCH: `VERBOSE=0 SAVE_ITERATIONS=false`
- For learning: `VERBOSE=2 SAVE_ITERATIONS=true SNAPSHOT_INTERVAL=2`
- For troubleshooting: `VERBOSE=3 SAVE_ITERATIONS=true`

## Advanced: Snapshot Inspection

Each snapshot has its own metadata:

```bash
INFO shape1_iter_5
```

**Shows**:
- Stats up to iteration 5
- Which operations were used so far
- Shape state at that point

**Use case**: Understanding when things went wrong
```bash
# Check progression
INFO shape1_iter_3  # All good
INFO shape1_iter_4  # Looks weird
INFO shape1_iter_5  # Still weird

# Conclusion: Iteration 4 introduced the problem
# Check main shape log to see what happened at iteration 4
INFO shape1  # Search for "Iteration 4"
```

## Common Workflows

### 1. Quick Test
```bash
PROC dynamic_polygon test VERTICES=5 BOUNDS=100,100,600,600 VERBOSE=1
```

### 2. Deep Dive
```bash
PROC dynamic_polygon test VERTICES=5 BOUNDS=100,100,600,600 VERBOSE=2 SAVE_ITERATIONS=true
INFO test
LIST WIP
```

### 3. Production Ready
```bash
# Test with debug
PROC dynamic_polygon test VERTICES=5,8 BOUNDS=100,100,668,668 ITERATIONS=15 VERBOSE=2

# Looks good? Run batch without debug
BATCH 100 my_script.txt dataset MAIN
```

### 4. Algorithm Development
```bash
# Maximum instrumentation
PROC dynamic_polygon test VERTICES=5 BOUNDS=100,100,600,600 \
  ITERATIONS=5 VERBOSE=3 SAVE_ITERATIONS=true SNAPSHOT_INTERVAL=1

# Examine every detail
INFO test
INFO test_iter_1
INFO test_iter_2
# etc.
```
