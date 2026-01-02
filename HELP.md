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

## STYLE COMMANDS (NEW in Phase 5!)

**COLOR** `<shape(s)>` `<color>`
Set outline/stroke color of shape(s)
- Multiple shapes: `COLOR tri1,tri2,tri3 red`
- Named colors: `COLOR square1 blue`
- RGB: `COLOR tri1 rgb(255,0,0)`
- RGBA: `COLOR tri1 rgba(255,0,0,128)`
- HSL: `COLOR tri1 hsl(120,100%,50%)`
- HSLA: `COLOR tri1 hsla(240,100%,50%,0.5)`
- Hex: `COLOR tri1 #FF0000`

**WIDTH** `<shape(s)>` `<pixels>`
Set line/outline width
Example: `WIDTH tri1 5`
Example: `WIDTH tri1,tri2 3`

**FILL** `<shape(s)>` `<color|NONE>`
Set fill color (polygons only)
- With color: `FILL tri1 red`
- No fill: `FILL tri1 NONE`
- With alpha: `FILL tri1 rgba(100,150,200,128)`
- Multiple: `FILL tri1,square1 hsl(240,80%,60%)`

**ALPHA** `<shape(s)>` `<0.0-1.0>`
Set transparency/opacity
Example: `ALPHA tri1 0.5` (50% transparent)
Example: `ALPHA tri1,tri2 0.75`

**BRING_FORWARD** `<shape>` `[n]`
Bring shape forward in z-order
Example: `BRING_FORWARD tri1` (1 step)
Example: `BRING_FORWARD tri1 5` (5 steps)

**SEND_BACKWARD** `<shape>` `[n]`
Send shape backward in z-order
Example: `SEND_BACKWARD square1`
Example: `SEND_BACKWARD square1 3`

**Group Style Behavior:**
- Styling a **member** affects only that member
- Styling a **group** applies to all members recursively

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

## RANDOMIZATION

**RAND(**`min`,`max`**)**
Use in any numeric parameter
Example: `LINE l1 RAND(100,200),RAND(100,200) 400,400`
Example: `ROTATE tri1 RAND(0,360)`
Example: `COLOR tri1 rgb(RAND(0,255),RAND(0,255),RAND(0,255))`

---

## KEYBOARD SHORTCUTS

**Enter** - Execute command
**↑** (Up) - Previous command in history
**↓** (Down) - Next command in history
**ESC** or **F11** - Toggle fullscreen

---

## WORKFLOW EXAMPLES

### Basic Styling
```
POLY tri1 100,100 200,100 150,50
COLOR tri1 red
WIDTH tri1 3
FILL tri1 rgba(255,0,0,50)
SAVE styled_triangle.png
```

### Multi-Shape Styling
```
POLY tri1 100,100 200,100 150,50
POLY tri2 300,100 400,100 350,50
POLY tri3 500,100 600,100 550,50
COLOR tri1,tri2,tri3 blue
FILL tri1,tri2,tri3 hsl(240,80%,70%)
WIDTH tri1,tri2,tri3 4
```

### Group Styling
```
POLY wall1 100,400 100,200 150,200 150,400
POLY wall2 150,400 150,200 200,200 200,400
POLY roof 100,200 150,150 200,200
GROUP house wall1 wall2 roof
COLOR house brown
FILL house rgba(139,69,19,180)
```

### Z-Order Control
```
POLY back 100,100 300,100 300,300 100,300
POLY front 200,200 400,200 400,400 200,400
FILL back blue
FILL front red
SEND_BACKWARD front 1
# Now 'back' covers 'front'
```

### Random Color Variations
```
POLY tri1 384,200 300,400 468,400
COLOR tri1 rgb(RAND(100,255),RAND(100,255),RAND(100,255))
FILL tri1 rgba(RAND(0,255),RAND(0,255),RAND(0,255),RAND(100,200))
```

### Complete Scene
```
# Background
POLY sky 0,0 768,0 768,384 0,384
FILL sky hsl(200,80%,70%)
SEND_BACKWARD sky 10

# Sun
POLY sun 600,100 620,100 620,120 600,120
FILL sun yellow
COLOR sun yellow

# Ground
POLY ground 0,384 768,384 768,768 0,768
FILL ground hsl(120,60%,40%)

# House
POLY house_body 200,300 400,300 400,500 200,500
POLY roof 200,300 300,200 400,300
GROUP house house_body roof
COLOR house brown
FILL house_body hsl(30,60%,50%)
FILL roof hsl(0,60%,40%)

PROMOTE house
SAVE village_scene.png
```

---

## COLOR FORMATS

**Named Colors:**
`red`, `blue`, `green`, `yellow`, `black`, `white`, etc.

**RGB:**
`rgb(red, green, blue)` where values are 0-255
Example: `rgb(255, 128, 0)`

**RGBA:**
`rgba(red, green, blue, alpha)` 
- RGB: 0-255
- Alpha: 0-255 or 0.0-1.0
Example: `rgba(255, 0, 0, 128)` or `rgba(255, 0, 0, 0.5)`

**HSL:**
`hsl(hue, saturation%, lightness%)`
- Hue: 0-360 (color wheel degrees)
- Saturation: 0-100%
- Lightness: 0-100%
Example: `hsl(120, 100%, 50%)` (pure green)

**HSLA:**
`hsla(hue, saturation%, lightness%, alpha)`
Example: `hsla(240, 100%, 50%, 0.5)` (semi-transparent blue)

**Hexadecimal:**
`#RRGGBB` or `#RRGGBBAA`
Example: `#FF0000` (red)
Example: `#FF000080` (semi-transparent red)

**None:**
`NONE` or `none` - for no fill (outline only)

---

## STORAGE LOCATIONS

**Project Store**: `shapes/` (current project only)
**Global Library**: `~/.shapestudio/shapes/` (all projects)
**Project Files**: `projects/*.shapestudio`
**PNG Exports**: `output/*.png`

---

## TIPS

- Use **COLOR** for outline, **FILL** for interior
- **ALPHA** affects entire shape (outline + fill)
- Use **HSL** for color variations (easy hue rotation)
- **Z-order** starts at 0; higher = in front
- Style groups to apply styling to all members
- Save styled shapes to STORE for reuse
- RAND() works in color values too!