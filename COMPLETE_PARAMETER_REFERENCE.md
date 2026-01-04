# SHAPE STUDIO - COMPLETE PARAMETER REFERENCE

This document lists EVERY parameter for EVERY command in Shape Studio.

---

## BASIC SHAPE CREATION

### LINE <name> <x1>,<y1> <x2>,<y2>

**Required Parameters:**
- `<name>` - Shape identifier (string, no spaces)
- `<x1>,<y1>` - Start point coordinates (integers, 0-768)
- `<x2>,<y2>` - End point coordinates (integers, 0-768)

**Examples:**
```
LINE l1 100,100 500,500
LINE vertical RAND(100,668),100 RAND(100,668),668
```

---

### POLY <name> <x1>,<y1> <x2>,<y2> <x3>,<y3> [...]

**Required Parameters:**
- `<name>` - Shape identifier (string, no spaces)
- `<points>` - At least 3 coordinate pairs (integers, 0-768)

**Notes:**
- Polygon automatically closes (last point connects to first)
- Points are rendered in order given

**Examples:**
```
POLY tri 100,100 500,100 300,400
POLY square 200,200 400,200 400,400 200,400
POLY random RAND(0,768),RAND(0,768) RAND(0,768),RAND(0,768) RAND(0,768),RAND(0,768)
```

---

## TRANSFORMATIONS

### MOVE <name> <dx>,<dy>

**Required Parameters:**
- `<name>` - Shape to move
- `<dx>` - Horizontal displacement (float, can be negative)
- `<dy>` - Vertical displacement (float, can be negative)

**Examples:**
```
MOVE tri1 50,100
MOVE square -20,-20
MOVE shape1 RAND(-50,50),RAND(-50,50)
```

---

### ROTATE <name> <angle>

**Required Parameters:**
- `<name>` - Shape to rotate
- `<angle>` - Rotation in degrees (float)
  - Positive = counter-clockwise
  - Negative = clockwise
  - Rotates around shape's centroid

**Examples:**
```
ROTATE tri1 45
ROTATE square -90
ROTATE shape1 RAND(0,360)
```

---

### SCALE <name> <factor>

**Required Parameters:**
- `<name>` - Shape to scale
- `<factor>` - Scale multiplier (float, >0)
  - 1.0 = no change
  - <1.0 = shrink
  - >1.0 = grow
  - Scales from shape's centroid

**Examples:**
```
SCALE tri1 1.5
SCALE square 0.8
SCALE shape1 RAND(0.5,1.5)
```

---

### RESIZE <name> <x_factor> [y_factor]

**Required Parameters:**
- `<name>` - Shape to resize
- `<x_factor>` - Horizontal scale (float, >0)

**Optional Parameters:**
- `[y_factor]` - Vertical scale (float, >0)
  - Default: same as x_factor (uniform scaling)

**Examples:**
```
RESIZE tri1 1.2 0.8
RESIZE square 0.5
RESIZE shape1 RAND(0.7,1.3) RAND(0.7,1.3)
```

---

## GROUPING

### GROUP <group_name> <shape1> <shape2> [...]

**Required Parameters:**
- `<group_name>` - New group identifier (string, no spaces)
- `<shapes>` - At least 1 shape name to include

**Restrictions:**
- Shapes cannot already be in another group
- Group name cannot already exist

**Examples:**
```
GROUP house wall1 wall2 roof
GROUP allshapes tri1 square1 line1
```

---

### UNGROUP <group_name>

**Required Parameters:**
- `<group_name>` - Group to dissolve

**Effect:**
- All members become independent shapes
- Group name is removed
- Members retain their names and positions

**Examples:**
```
UNGROUP house
```

---

### EXTRACT <member> FROM <group>

**Required Parameters:**
- `<member>` - Shape to extract
- `FROM` - Literal keyword
- `<group>` - Group containing the shape

**Effect:**
- Member becomes independent
- Group remains with other members
- If group has ≤1 member after extraction, group is dissolved

**Examples:**
```
EXTRACT wall1 FROM house
```

---

## SHAPE MANAGEMENT

### DELETE <shape> [CONFIRM]

**Required Parameters:**
- `<shape>` - Shape to delete

**Optional Parameters:**
- `CONFIRM` - Required flag if deleting a group with members

**Restrictions:**
- Cannot delete shapes that are in a group (extract first)

**Examples:**
```
DELETE tri1
DELETE mygroup CONFIRM
```

---

### INFO <shape>

**Required Parameters:**
- `<shape>` - Shape to inspect

**Output:**
- Location (WIP/MAIN/STASH)
- Type (Line/Polygon/ShapeGroup)
- Geometry details
- Style (color, width)
- Group membership
- Command history (last 5)

**Examples:**
```
INFO tri1
```

---

### STASH <shape>

**Required Parameters:**
- `<shape>` - Shape to move to temporary storage

**Effect:**
- Removes shape from active canvas
- Stores in stash (accessible from any canvas)
- Cannot stash shapes in groups

**Examples:**
```
STASH tri1
```

---

### UNSTASH [MOVE] <shape>

**Required Parameters:**
- `<shape>` - Shape to retrieve from stash

**Optional Parameters:**
- `MOVE` - Remove from stash after copying
  - Default: Copy (keeps in stash)

**Examples:**
```
UNSTASH tri1
UNSTASH MOVE square1
```

---

## CANVAS OPERATIONS

### SWITCH <target>

**Required Parameters:**
- `<target>` - Canvas to activate
  - `WIP` - Working/scratch canvas
  - `MAIN` - Final composition canvas

**Examples:**
```
SWITCH MAIN
SWITCH WIP
```

---

### PROMOTE [COPY] <shape>

**Required Parameters:**
- `<shape>` - Shape to move from WIP to MAIN

**Optional Parameters:**
- `COPY` - Copy instead of move
  - Default: Move (removes from WIP)

**Restrictions:**
- Only works if active canvas is WIP
- Shape must exist on WIP
- Shape cannot already exist on MAIN

**Examples:**
```
PROMOTE tri1
PROMOTE COPY square1
```

---

### UNPROMOTE [COPY] <shape>

**Required Parameters:**
- `<shape>` - Shape to move from MAIN to WIP

**Optional Parameters:**
- `COPY` - Copy instead of move
  - Default: Move (removes from MAIN)

**Restrictions:**
- Shape must exist on MAIN
- Shape cannot already exist on WIP

**Examples:**
```
UNPROMOTE tri1
UNPROMOTE COPY square1
```

---

### CLEAR [target] [ALL]

**Required Parameters:**
- None (clears active canvas)

**Optional Parameters:**
- `[target]` - Specific canvas to clear
  - `WIP` - Clear WIP canvas
  - `MAIN` - Clear MAIN canvas
  - `STASH` - Clear stash
- `ALL` - Safety confirmation
  - Required for canvas clearing
  - NOT required for stash

**Examples:**
```
CLEAR WIP ALL
CLEAR MAIN ALL
CLEAR STASH
```

---

### LIST [target]

**Required Parameters:**
- None (lists active canvas)

**Optional Parameters:**
- `[target]` - What to list
  - `WIP` - WIP canvas shapes
  - `MAIN` - MAIN canvas shapes
  - `STASH` - Stashed shapes
  - `STORE` - Project object store
  - `GLOBAL` - Global object library
  - `PROC` - Available procedural methods

**Examples:**
```
LIST
LIST MAIN
LIST STORE
LIST PROC
```

---

### SAVE <filename>

**Required Parameters:**
- `<filename>` - Output filename (automatically adds .png)

**Effect:**
- Always saves MAIN canvas (not WIP)
- Saves to `output/` directory
- Creates 768x768 PNG image

**Examples:**
```
SAVE final.png
SAVE mywork
```

---

## PERSISTENCE

### SAVE_PROJECT <filename>

**Required Parameters:**
- `<filename>` - Project filename (automatically adds .shapestudio)

**Saves:**
- WIP canvas shapes
- MAIN canvas shapes
- Stash contents
- Canvas settings (grid, rulers)
- Active canvas state

**Examples:**
```
SAVE_PROJECT mywork
SAVE_PROJECT session_2024.shapestudio
```

---

### LOAD_PROJECT <filename>

**Required Parameters:**
- `<filename>` - Project filename (automatically adds .shapestudio)

**Effect:**
- Clears current session
- Restores entire project state

**Examples:**
```
LOAD_PROJECT mywork
```

---

### STORE [GLOBAL] <shape>

**Required Parameters:**
- `<shape>` - Shape to save to object library

**Optional Parameters:**
- `GLOBAL` - Save to global library (all projects)
  - Default: Project store (current project only)

**Examples:**
```
STORE tri1
STORE GLOBAL star
```

---

### LOAD <shape>

**Required Parameters:**
- `<shape>` - Shape name to load from library

**Search Order:**
1. Project store
2. Global library

**Examples:**
```
LOAD star
```

---

## AUTOMATION

### RUN <scriptfile>

**Required Parameters:**
- `<scriptfile>` - Script in `scripts/` directory

**Script Format:**
- One command per line
- Lines starting with `#` are comments
- Blank lines ignored
- RAND() functions get new values

**Examples:**
```
RUN random_shapes.txt
RUN test_triangles.txt
```

---

### BATCH <count> <scriptfile> <prefix> [target]

**Required Parameters:**
- `<count>` - Number of iterations (integer, ≥1)
- `<scriptfile>` - Script in `scripts/` directory
- `<prefix>` - Output filename prefix

**Optional Parameters:**
- `[target]` - Canvas to use and save
  - `WIP` - Work on and save WIP
  - `MAIN` - Work on and save MAIN (default)

**Behavior:**
- Runs script N times
- Fresh RAND() values each iteration
- Saves to `output/<prefix>_001.png`, `_002.png`, etc.
- On error: Random branch to earlier script line (creative recovery)
- NO auto-clearing (control via script)

**Examples:**
```
BATCH 50 random_triangle.txt dataset MAIN
BATCH 100 shapes.txt training WIP
```

---

## PROCEDURAL GENERATION

### PROC <method> <name> [PARAM=value ...]

**Required Parameters:**
- `<method>` - Procedural method name
- `<name>` - Shape name (or prefix for multiple shapes)

**Optional Parameters:**
- Method-specific parameters (see method documentation)

**Examples:**
```
PROC dynamic_polygon shape1 VERTICES=5 BOUNDS=100,100,600,600
PROC dynamic_polygon shape2 PRESET=organic BOUNDS=0,0,768,768
```

---

### PROC dynamic_polygon - COMPLETE PARAMETERS

**Required Parameters:**

- **VERTICES** - Number of initial vertices
  - Type: `int` or `int,int` (range)
  - Examples: `VERTICES=5` or `VERTICES=5,8`
  - Script random: `VERTICES=RAND(5,8)` (varies per BATCH)
  - Method random: `VERTICES=5,8` (varies per call)

- **BOUNDS** - Bounding rectangle
  - Type: `x1,y1,x2,y2` (4 integers)
  - Example: `BOUNDS=100,100,600,600`
  - Can use RAND: `BOUNDS=100,100,RAND(500,700),RAND(500,700)`

**Optional Parameters:**

- **ITERATIONS** - Number of evolution steps
  - Type: `int`
  - Default: `10`
  - Range: 1-1000
  - Example: `ITERATIONS=20`

- **CONNECT** - Initial vertex connection method
  - Type: choice
  - Choices: `angle_sort`, `convex_hull`
  - Default: `angle_sort`
  - Example: `CONNECT=convex_hull`

- **OPERATIONS** - Segment modification operations
  - Type: comma-separated list
  - Choices: `split_offset`, `sawtooth`, `squarewave`
  - Default: `split_offset,sawtooth`
  - Example: `OPERATIONS=split_offset,sawtooth,squarewave`
  - Note: Does NOT include remove_point or distort_original (use probabilities)

- **DEPTH_RANGE** - Offset depth as percentage
  - Type: `float` or `float,float` (range)
  - Default: `0.2,0.8`
  - Range: 0.0-1.0 (0% to 100% of segment length)
  - Examples: `DEPTH_RANGE=0.5` or `DEPTH_RANGE=0.3,0.9`

- **WEIGHT_DECAY** - Segment weight multiplier
  - Type: `float`
  - Default: `0.5`
  - Range: 0.0-1.0
  - Example: `WEIGHT_DECAY=0.3`
  - Effect: Lower = more modification on same segments

- **MAX_RETRIES** - Attempts per modification
  - Type: `int`
  - Default: `10`
  - Range: 1-100
  - Example: `MAX_RETRIES=20`

- **DIRECTION_BIAS** - Preferred modification direction
  - Type: choice
  - Choices: `inward`, `outward`, `random`
  - Default: `random`
  - Example: `DIRECTION_BIAS=inward`

- **REMOVE_PROB** - Probability of vertex removal ⭐ NEW
  - Type: `float`
  - Default: `0.0` (disabled)
  - Range: 0.0-1.0 (0% to 100% chance per iteration)
  - Example: `REMOVE_PROB=0.2` (20% chance)
  - Effect: Removes vertices, simplifying polygon

- **DISTORT_PROB** - Probability of original vertex distortion ⭐ NEW
  - Type: `float`
  - Default: `0.0` (disabled)
  - Range: 0.0-1.0 (0% to 100% chance per iteration)
  - Example: `DISTORT_PROB=0.3` (30% chance)
  - Effect: Moves original vertices toward/away from center
  - Uses DIRECTION_BIAS: `inward`=squish, `outward`=stretch

- **VERBOSE** - Debug verbosity level
  - Type: `int`
  - Default: `0`
  - Choices: 0, 1, 2, 3
    - `0` = Silent (production use)
    - `1` = Summary statistics
    - `2` = Detailed iteration logs
    - `3` = Full geometry dumps
  - Example: `VERBOSE=2`

- **SAVE_ITERATIONS** - Create iteration snapshots
  - Type: `bool`
  - Default: `false`
  - Choices: `true`, `false`
  - Example: `SAVE_ITERATIONS=true`
  - Returns: List of shapes (one per iteration)

- **SNAPSHOT_INTERVAL** - Snapshot sampling rate
  - Type: `int`
  - Default: `1` (every iteration)
  - Example: `SNAPSHOT_INTERVAL=5` (every 5th)
  - Only used if SAVE_ITERATIONS=true

- **PRESET** - Use predefined configuration
  - Type: choice
  - Choices: `simple`, `complex`, `organic`
  - Example: `PRESET=organic`
  - Overrides defaults for multiple parameters
  - Can combine with explicit parameters

**Preset Details:**

**PRESET=simple**
```
VERTICES=5,8
ITERATIONS=5
OPERATIONS=split_offset
DEPTH_RANGE=0.2,0.6
```

**PRESET=complex**
```
VERTICES=8,12
ITERATIONS=20
OPERATIONS=split_offset,sawtooth,squarewave
DEPTH_RANGE=0.3,0.9
WEIGHT_DECAY=0.3
```

**PRESET=organic**
```
VERTICES=6,10
ITERATIONS=15
OPERATIONS=sawtooth
DEPTH_RANGE=0.3,0.8
DIRECTION_BIAS=inward
```

---

## PROCEDURAL GENERATION - OTHER COMMANDS

### LIST PROC

Lists all available procedural methods with descriptions.

**Example:**
```
LIST PROC
```

---

### LIST PRESET <method>

Lists available presets for a procedural method.

**Required Parameters:**
- `<method>` - Method name

**Example:**
```
LIST PRESET dynamic_polygon
```

---

### INFO PROC <method>

Shows detailed information about a procedural method including parameters and examples.

**Required Parameters:**
- `<method>` - Method name

**Example:**
```
INFO PROC dynamic_polygon
```

---

## RANDOMIZATION FUNCTIONS

### RAND(min, max)

Generates random value between min and max.

**Parameters:**
- `min` - Minimum value (float)
- `max` - Maximum value (float)

**Behavior:**
- Returns integer if both min and max are integers
- Returns float otherwise
- New value each time script is run (including BATCH iterations)

**Examples:**
```
LINE l1 RAND(0,768),RAND(0,768) RAND(0,768),RAND(0,768)
ROTATE tri RAND(0,360)
SCALE square RAND(0.5,1.5)
PROC dynamic_polygon p VERTICES=RAND(4,10) BOUNDS=100,100,600,600
```

---

### RANDBOOL()

Generates random boolean (0 or 1).

**Examples:**
```
MOVE shape RANDBOOL(),RANDBOOL()
```

---

## PARAMETER TYPE REFERENCE

**int** - Integer number
- Example: `5`, `100`, `-20`

**float** - Decimal number
- Example: `0.5`, `1.23`, `-4.5`

**int_or_range** - Integer or range
- Examples: `5` or `5,8`

**float_or_range** - Float or range
- Examples: `0.5` or `0.2,0.8`

**bounds** - Rectangle coordinates
- Format: `x1,y1,x2,y2`
- Example: `100,100,600,600`

**point** - Coordinate pair
- Format: `x,y`
- Example: `400,300`

**list** - Comma-separated values
- Example: `split_offset,sawtooth,squarewave`

**choice** - One of predefined values
- Example: `inward` (from: inward, outward, random)

**bool** - Boolean value
- Values: `true`, `false`, `TRUE`, `FALSE`, `1`, `0`, `yes`, `no`

---

## NOTES

- All coordinates are 0-768 (canvas is 768x768)
- Canvas origin (0,0) is top-left
- Positive X is right, positive Y is down
- Commands are case-insensitive
- Shape names are case-sensitive
- RAND() resolves at script parse time
- Parameters in [brackets] are optional
- Parameters in <angle brackets> are required
