# Quick Start - Debug Mode Demo

## Try This First

Copy and run this script to see debug mode in action:

```bash
# Simple verbose example
CLEAR WIP ALL
PROC dynamic_polygon demo VERTICES=4 BOUNDS=200,200,568,568 ITERATIONS=5 VERBOSE=2
INFO demo
```

## Expected Output

When you run the PROC command:
```
Created Polygon 'demo' using dynamic_polygon on WIP
  Modifications: 4 successful (2 failed attempts)
  Use 'INFO demo' to see detailed generation log
```

When you run INFO demo:
```
Shape: demo
Location: WIP
Type: Polygon
Vertices: 8
Points: [(234.5, 267.8), (421.3, 245.6), ...]
Color: black
Width: 2

Procedural Generation:
  Method: dynamic_polygon
  Successful: 4
  Failed: 2

=== PROCEDURAL GENERATION DEBUG LOG ===

Initial State:
  Vertices: 4
  Bounds: (200, 200, 568, 568)
  Centroid: (389.3, 401.2)
  Connection: angle_sort

--- Iteration 1 ---
Selection:
  Segment: 1 (weight: 1.000)
  Length: 234.5px
  Probability: 25.0%

Operation: split_offset
  Depth: 45% (105.5px offset)
  Direction: outward

Result:
  Points: 4 -> 5
  Validation: PASS [OK]

--- Iteration 2 ---
Selection:
  Segment: 3 (weight: 1.000)
  Length: 189.2px

Operation: sawtooth
  Depth: 62% (117.3px offset)
  Direction: inward

Result:
  Points: 5 -> 6
  Validation: PASS [OK]

--- Iteration 3 ---
Selection:
  Segment: 2 (weight: 0.500)
  Length: 102.8px

Operation: split_offset
  Depth: 38% (39.1px offset)
  Direction: outward

Result:
  Points: 6 -> 6
  Validation: FAIL [FAIL]
  Attempts: 3

--- Iteration 4 ---
Selection:
  Segment: 5 (weight: 1.000)
  Length: 267.9px

Operation: split_offset
  Depth: 51% (136.6px offset)
  Direction: inward

Result:
  Points: 6 -> 7
  Validation: PASS [OK]

--- Iteration 5 ---
Selection:
  Segment: 4 (weight: 0.500)
  Length: 98.3px

Operation: sawtooth
  Depth: 44% (43.3px offset)
  Direction: outward

Result:
  Points: 7 -> 8
  Validation: PASS [OK]

Final Statistics:
  Successful modifications: 4
  Failed attempts: 2
  Operations used:
    split_offset: 2
    sawtooth: 2
```

## Now Try Snapshots

```bash
# With visual evolution
CLEAR WIP ALL
PROC dynamic_polygon demo2 VERTICES=4 BOUNDS=200,200,568,568 ITERATIONS=5 \
  VERBOSE=2 SAVE_ITERATIONS=true

LIST WIP
```

Expected:
```
WIP canvas shapes:
  demo2_iter_0 (Polygon)
  demo2_iter_1 (Polygon)
  demo2_iter_2 (Polygon)
  demo2_iter_3 (Polygon)
  demo2_iter_4 (Polygon)
  demo2_iter_5 (Polygon)
  demo2_final (Polygon)
  demo2 (Polygon)
```

Now you can:
1. See each iteration snapshot on the canvas
2. Delete intermediate ones to see progression
3. Use INFO on individual snapshots

```bash
INFO demo2_iter_0  # Initial state
INFO demo2_iter_3  # Midpoint
INFO demo2_final   # Final result
```

## Next: Try Different Verbose Levels

### Verbose 1 - Summary Only
```bash
PROC dynamic_polygon test1 VERTICES=5 BOUNDS=100,100,600,600 VERBOSE=1
INFO test1
```

Shows only final statistics, no iteration details.

### Verbose 2 - Detailed (Recommended)
```bash
PROC dynamic_polygon test2 VERTICES=5 BOUNDS=100,100,600,600 VERBOSE=2
INFO test2
```

Shows iteration-by-iteration with decisions and results.

### Verbose 3 - Full Geometry
```bash
PROC dynamic_polygon test3 VERTICES=4 BOUNDS=100,100,600,600 VERBOSE=3
INFO test3
```

Includes all coordinate data, direction vectors, etc.

## Compare: No Debug vs Debug

### Without Debug (Default)
```bash
PROC dynamic_polygon nodebug VERTICES=5 BOUNDS=100,100,600,600
INFO nodebug
```

Output:
```
Shape: nodebug
Location: WIP
Type: Polygon
Vertices: 11
Points: [...]
Color: black
Width: 2

Procedural Generation:
  Method: dynamic_polygon
  Successful: 6
  Failed: 8
```

### With Debug
```bash
PROC dynamic_polygon debug VERTICES=5 BOUNDS=100,100,600,600 VERBOSE=2
INFO debug
```

Output: Full detailed log showing every iteration.

## Production vs Development

### Development Mode
```bash
# While developing/testing
PROC dynamic_polygon dev VERTICES=5 BOUNDS=100,100,600,600 \
  VERBOSE=2 SAVE_ITERATIONS=true ITERATIONS=10

# Understand what's happening
INFO dev

# See evolution
LIST WIP
```

### Production Mode
```bash
# For BATCH generation (fast, no overhead)
PROC dynamic_polygon prod VERTICES=RAND(5,8) BOUNDS=100,100,668,668 ITERATIONS=20

# Or in batch script:
BATCH 100 my_script.txt dataset MAIN
```

## That's It!

You now know:
- ✅ How to enable debug logging (VERBOSE=1|2|3)
- ✅ How to save iteration snapshots (SAVE_ITERATIONS=true)
- ✅ How to view detailed logs (INFO command)
- ✅ When to use debug mode vs production mode

For more details, see DEBUG_GUIDE.md
