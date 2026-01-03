# SHAPE STUDIO - COMMAND REFERENCE

## SHAPE CREATION

**LINE** `<name>` `<x1>,<y1>` `<x2>,<y2>`
Create a line segment
Example: `LINE l1 100,100 500,500`

**POLY** `<name>` `<x1>,<y1>` `<x2>,<y2>` `<x3>,<y3>` ...
Create a polygon (minimum 3 points, auto-closes)
Example: `POLY tri1 100,100 200,100 150,50`

---

## TRANSFORMATIONS

**MOVE** `<name>` `<dx>,<dy>`
Move shape by delta
Example: `MOVE tri1 50,50`

**ROTATE** `<name>` `<angle>`
Rotate shape by angle (degrees) around center
Example: `ROTATE tri1 45`

**SCALE** `<name>` `<factor>`
Scale shape uniformly
Example: `SCALE tri1 1.5`

**RESIZE** `<name>` `<x_factor>` `[y_factor]`
Resize with separate X/Y factors
Example: `RESIZE tri1 1.2 0.9`
Example: `RESIZE tri1 0.5` (uniform)

---

## GROUPS

**GROUP** `<group_name>` `<shape1>` `<shape2>` ...
Create group from shapes
Example: `GROUP house wall1 wall2 roof`

**UNGROUP** `<group_name>`
Dissolve group, making members independent
Example: `UNGROUP house`

**EXTRACT** `<member>` **FROM** `<group>`
Remove single member from group
Example: `EXTRACT wall1 FROM house`

---

## SHAPE MANAGEMENT

**DELETE** `<shape>` `[CONFIRM]`
Remove shape from active canvas
- Simple shapes: `DELETE tri1`
- Groups: `DELETE house CONFIRM` (required)

**INFO** `<shape>`
Show detailed information about a shape
Example: `INFO tri1`

**STASH** `<shape>`
Move shape to temporary storage
Example: `STASH tri1`

**UNSTASH** `[MOVE]` `<shape>`
Restore from stash to active canvas
- Copy (default): `UNSTASH tri1` (keeps in stash)
- Move: `UNSTASH MOVE tri1` (removes from stash)

---

## CANVAS OPERATIONS

**SWITCH** **WIP**|**MAIN**
Change active canvas
Example: `SWITCH MAIN`

**PROMOTE** `[COPY]` `<shape>`
Move/copy shape from WIP to MAIN
- Move: `PROMOTE tri1`
- Copy: `PROMOTE COPY tri1`

**UNPROMOTE** `[COPY]` `<shape>`
Move/copy shape from MAIN to WIP
- Move: `UNPROMOTE tri1`
- Copy: `UNPROMOTE COPY tri1`

**CLEAR** `[WIP|MAIN|STASH]` `[ALL]`
Clear canvas or stash
- Canvas: `CLEAR WIP ALL` (requires ALL)
- Stash: `CLEAR STASH` (no ALL needed)

**LIST** `[WIP|MAIN|STASH|STORE|GLOBAL]`
List shapes on canvas/stash or in stores
Example: `LIST MAIN`
Example: `LIST STORE`

**SAVE** `<filename>`
Save MAIN canvas to PNG (768x768)
Example: `SAVE final.png`

---

## PERSISTENCE

**SAVE_PROJECT** `<filename>`
Save entire session to file
Example: `SAVE_PROJECT mywork.shapestudio`
Saves: WIP, MAIN, stash, settings

**LOAD_PROJECT** `<filename>`
Load previously saved session
Example: `LOAD_PROJECT mywork.shapestudio`
Restores: All canvases, stash, settings

**STORE** `[GLOBAL]` `<shape>`
Save shape to object library
- Project: `STORE tri1` (current project)
- Global: `STORE GLOBAL tri1` (all projects)

**LOAD** `<shape>`
Load shape from object library
Example: `LOAD tri1`
Searches: project store → global library

**LIST STORE**
List shapes in project store
Example: `LIST STORE`

**LIST GLOBAL**
List shapes in global library
Example: `LIST GLOBAL`

---

## AUTOMATION (NEW!)

**RUN** `<scriptfile>`
Execute commands from a script file
Example: `RUN random_triangle.txt`

Script files:
- Located in `scripts/` directory
- One command per line
- Lines starting with `#` are comments
- Blank lines are ignored

**BATCH** `<count>` `<scriptfile>` `<prefix>` `[WIP|MAIN]`
Generate multiple PNG variations for LoRA training
Example: `BATCH 50 random_triangle.txt dataset MAIN`

Parameters:
- `count` - number of iterations (e.g., 50)
- `scriptfile` - script in scripts/ directory
- `prefix` - output filename prefix
- `WIP|MAIN` - which canvas to create on AND save (default: MAIN)

Behavior:
- Runs script N times with fresh RAND() values
- Saves to `output/<prefix>_001.png`, `_002.png`, etc.
- NO auto-clearing (control via script)
- On error: Randomly branches to early script line (creative recovery)

---

## PROCEDURAL GENERATION (NEW!)

**PROC** `<method>` `<n>` `[PARAM=value ...]`
Generate shapes using procedural algorithms
Example: `PROC dynamic_polygon shape1 VERTICES=5 BOUNDS=100,100,600,600`

**LIST PROC**
List all available procedural methods
Example: `LIST PROC`

**INFO PROC** `<method>`
Show detailed information about a procedural method
Example: `INFO PROC dynamic_polygon`

**LIST PRESET** `<method>`
Show available presets for a method
Example: `LIST PRESET dynamic_polygon`

### Using Presets
```
PROC dynamic_polygon shape1 PRESET=simple BOUNDS=0,0,768,768
PROC dynamic_polygon shape2 PRESET=complex BOUNDS=100,100,600,600
PROC dynamic_polygon shape3 PRESET=organic BOUNDS=200,200,500,500
```

### Parameter Types

**Single values:**
```
VERTICES=5        # Exact count
ITERATIONS=10     # Exact number
```

**Ranges (method chooses randomly):**
```
VERTICES=5,8      # Method picks from 5-8
DEPTH_RANGE=0.2,0.8  # Method picks from 0.2-0.8
```

**Script-level random (changes per BATCH):**
```
VERTICES=RAND(5,8)    # Script picks, different each batch
BOUNDS=100,100,RAND(500,700),RAND(500,700)
```

**Combining both:**
```
PROC dynamic_polygon shape1 VERTICES=RAND(4,10) ITERS=8,15
# Script picks vertices from 4-10 (varies per batch)
# Method picks iterations from 8-15 (varies per call)
# Maximum variation!
```

### Dynamic Polygon Method

**PROC dynamic_polygon** `<n>` `VERTICES=<n|range>` `BOUNDS=<x1,y1,x2,y2>` `[options...]`

Creates evolved polygon through iterative segment modification.

**Parameters:**
- `VERTICES` - Number of initial vertices (int) or range (REQUIRED)
- `BOUNDS` - Bounding box as x1,y1,x2,y2 (REQUIRED)
- `ITERATIONS` - Number of evolution steps (default: 10)
- `CONNECT` - Initial connection: angle_sort or convex_hull (default: angle_sort)
- `OPERATIONS` - Allowed ops: split_offset,sawtooth,squarewave (default: split_offset,sawtooth)
- `DEPTH_RANGE` - Depth percentage (float) or range (default: 0.2,0.8)
- `WEIGHT_DECAY` - Split segment weight multiplier (default: 0.5)
- `MAX_RETRIES` - Max attempts per modification (default: 10)
- `DIRECTION_BIAS` - Preferred direction: inward, outward, random (default: random)

**Examples:**
```
# Basic usage
PROC dynamic_polygon poly1 VERTICES=6 BOUNDS=100,100,600,600

# With preset
PROC dynamic_polygon poly2 PRESET=organic BOUNDS=0,0,768,768

# Full control
PROC dynamic_polygon poly3 VERTICES=8,12 BOUNDS=100,100,600,600 ITERATIONS=20 OPERATIONS=split_offset,sawtooth,squarewave DEPTH_RANGE=0.3,0.9

# Maximum variation for BATCH
PROC dynamic_polygon poly4 VERTICES=RAND(5,10) BOUNDS=100,100,600,600 ITERATIONS=RAND(10,20)
```

**Presets:**
- `simple` - 5-8 vertices, 5 iterations, basic operations
- `complex` - 8-12 vertices, 20 iterations, all operations
- `organic` - 6-10 vertices, 15 iterations, sawtooth bias inward

---

## RANDOMIZATION

**RAND(**`min`,`max`**)**
Random number between min and max
Example: `LINE l1 RAND(100,200),RAND(100,200) 400,400`
Example: `ROTATE tri1 RAND(0,360)`
Example: `SCALE tri1 RAND(0.7,1.3)`

**RANDBOOL()**
Random 0 or 1 (for boolean/binary choices)
Example: `MOVE tri1 RANDBOOL(),RANDBOOL()`

---

## KEYBOARD SHORTCUTS

**Enter** - Execute command
**↑** (Up) - Previous command in history
**↓** (Down) - Next command in history
**ESC** or **F11** - Toggle fullscreen

---

## WORKFLOW EXAMPLES

### Generate LoRA Training Dataset with PROC
```
# Create script: scripts/proc_variations.txt
CLEAR WIP ALL
PROC dynamic_polygon p1 VERTICES=RAND(5,8) BOUNDS=100,100,668,668 PRESET=organic
ROTATE p1 RAND(0,360)
SCALE p1 RAND(0.7,1.3)
PROMOTE p1
CLEAR WIP ALL

# Generate 100 unique procedural variations
BATCH 100 proc_variations.txt training_data MAIN
```

### Discover Available Procedural Methods
```
# See what's available
LIST PROC

# Get details on a method
INFO PROC dynamic_polygon

# Check presets
LIST PRESET dynamic_polygon
```

### Generate LoRA Training Dataset
```
# Create script: scripts/random_shapes.txt
CLEAR WIP ALL
POLY p1 RAND(100,668),RAND(100,668) RAND(100,668),RAND(100,668) RAND(100,668),RAND(100,668)
ROTATE p1 RAND(0,360)
SCALE p1 RAND(0.7,1.3)
PROMOTE p1
CLEAR WIP ALL

# Generate 100 variations
BATCH 100 random_shapes.txt training_data MAIN
```

### Test Script Before Batch
```
# Test your script first
RUN random_shapes.txt
# Check the result, then run batch
BATCH 50 random_shapes.txt dataset MAIN
```

### Build Reusable Library
```
POLY star 384,384 450,350 500,384 450,418
STORE GLOBAL star  # Save to global library
# Later in any project...
LOAD star  # Reuse it!
```

### Complex Multi-Canvas Workflow
```
# Work on WIP canvas
POLY tri RAND(100,668),RAND(100,668) RAND(100,668),RAND(100,668) RAND(100,668),RAND(100,668)
ROTATE tri RAND(0,360)

# Promote to MAIN
PROMOTE tri

# Clear WIP for next shape
CLEAR WIP ALL

# Continue adding to MAIN...
```

---

## STORAGE LOCATIONS

**Scripts**: `scripts/*.txt` (command files)
**Project Store**: `shapes/` (current project only)
**Global Library**: `~/.shapestudio/shapes/` (all projects)
**Project Files**: `projects/*.shapestudio`
**PNG Exports**: `output/*.png`

---

## BATCH GENERATION TIPS

1. **Always clear WIP** in your script (CLEAR WIP ALL)
2. **Use PROMOTE** to move shapes from WIP to target canvas
3. **Fresh RAND() values** each iteration - no repeated outputs!
4. **Error recovery** happens automatically - creative variations!
5. **Start small** - test with 5-10 iterations first
6. **Target canvas** controls both creation AND saving

Example workflow:
- Create shapes on WIP
- Transform randomly
- PROMOTE to MAIN
- MAIN gets saved each iteration
- WIP is cleared for next iteration

---

## TIPS

- Use **STORE** for shapes you'll reuse
- Use **SAVE_PROJECT** to save your work
- **BATCH** is perfect for LoRA training datasets
- **RUN** lets you test scripts interactively
- Build script library in `scripts/`
- WIP for experiments, MAIN for finals
- Stash for temporary "what-if" experiments
