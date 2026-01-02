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

## PERSISTENCE (NEW!)

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

## RANDOMIZATION

**RAND(**`min`,`max`**)**
Use in any numeric parameter
Example: `LINE l1 RAND(100,200),RAND(100,200) 400,400`
Example: `ROTATE tri1 RAND(0,360)`

---

## KEYBOARD SHORTCUTS

**Enter** - Execute command
**↑** (Up) - Previous command in history
**↓** (Down) - Next command in history
**ESC** or **F11** - Toggle fullscreen

---

## WORKFLOW EXAMPLES

### Save and Resume Work
```
POLY tri1 100,100 200,100 150,50
MOVE tri1 50,50
SAVE_PROJECT mywork
# ... later ...
LOAD_PROJECT mywork  # Everything restored!
```

### Build Reusable Library
```
POLY star 384,384 450,350 500,384 450,418
STORE star  # Save to project
STORE GLOBAL star  # Share across projects
# ... later ...
LOAD star  # Use it again
```

### Template for LoRA Training
```
POLY template 100,100 200,100 150,50
STORE template
# Generate variations:
LOAD template
ROTATE template RAND(0,360)
PROMOTE template
SAVE variant1.png
# Repeat...
```

---

## STORAGE LOCATIONS

**Project Store**: `shapes/` (current project only)
**Global Library**: `~/.shapestudio/shapes/` (all projects)
**Project Files**: `projects/*.shapestudio`
**PNG Exports**: `output/*.png`

---

## TIPS

- Use **STORE** for shapes you'll reuse
- Use **SAVE_PROJECT** to save your work
- **LOAD_PROJECT** restores everything
- Build a personal library in global store
- WIP for experiments, MAIN for finals
- Stash for temporary "what-if" experiments
