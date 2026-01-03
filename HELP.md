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
