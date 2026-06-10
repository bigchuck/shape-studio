# Shape Studio — Primer

*Built from source. For Mr. Chuck.*

---

## What It Is

Shape Studio is a Python/Tkinter desktop application for generating and exploring procedurally created polygon shapes. The current primary use is producing interesting forms that serve as inspiration for painting composition. It runs entirely by typing commands — there is no mouse drawing.

The canvas is **768×768 pixels**. Output PNGs are 768×768.

---

## The Interface

Three panels:

- **Left** — command log (everything typed and its result)
- **Center** — canvas display
- **Right** — integrated help browser

Type commands at the bottom prompt. Use **↑ / ↓** to scroll command history (history is persisted across sessions). The **status bar** shows the active canvas and any WORKWITH context currently set.

---

## Two Canvases: WIP and MAIN

There are always two independent canvases in memory.

| Canvas | Role |
|--------|------|
| `WIP`  | Work in progress — your scratch space |
| `MAIN` | The output canvas — what gets saved |

At startup, WIP is active. Every drawing command acts on whichever canvas is currently active. Switch with:

```
SWITCH WIP
SWITCH MAIN
```

Shapes on WIP and MAIN are entirely separate. A shape named `s1` on WIP is a different object from a shape named `s1` on MAIN.

---

## Getting Help In-App

```
HELP                   # Compact index of all commands
HELP <command>         # Full usage for a specific command
INFO <shapename>       # Details about a shape on the active canvas
INFO PROC dynamic_polygon   # Full parameter reference for the PROC method
LIST PROC              # List available procedural methods
```

---

## Basic Shape Commands

### LINE
```
LINE <name> <x1>,<y1> <x2>,<y2>

LINE horizon 50,400 718,400
```

### POLY
Three or more points, space-separated.
```
POLY <name> <x1>,<y1> <x2>,<y2> <x3>,<y3> [...]

POLY tri 100,600 400,100 700,600
```

---

## Styling

All style commands accept an optional shape name. If you have a WORKWITH context active (see below), the name can be omitted.

### COLOR — outline/stroke color
```
COLOR [<name>] <color>

COLOR s1 black
COLOR s1 #2C3E50
COLOR s1 rgb(52,152,219)
COLOR s1 hsv(200,80,90)
```

Accepted color formats: named colors (`red`, `black`, `white`…), `#rrggbb` hex, `#rgb` short hex, `rgb(r,g,b)`, `hsv(h,s,v)` (H: 0–360, S/V: 0–100).

### WIDTH — stroke width
```
WIDTH [<name>] <pixels>     # integer, minimum 1

WIDTH s1 3
```

### FILL — fill color, or none
```
FILL [<name>] <color|NONE>

FILL s1 white
FILL s1 #F0F0F0
FILL s1 NONE           # removes fill
```

### ALPHA — opacity
```
ALPHA [<name>] <0.0–1.0>    # 0=invisible, 1=fully opaque

ALPHA s1 0.6
```

### ZORDER — drawing order
```
ZORDER [<name>] <integer>   # lower = further back

ZORDER s1 10
```

Shapes are auto-assigned z-order on creation (incrementing counter). `RESET_ZORDER` resets the counter if it drifts:
```
RESET_ZORDER           # reset to 0
RESET_ZORDER 10        # reset to specific value
```

---

## WORKWITH — Implicit Shape Context

When exploring a shape interactively, repeatedly typing its name gets tedious. WORKWITH sets an implicit target for all style and transform commands.

```
WORKWITH <name>        # set context
WORKWITH OFF           # clear context (also bare WORKWITH)
```

With WORKWITH set, the name argument becomes optional:
```
WORKWITH shape1
COLOR black            # targets shape1
WIDTH 3                # targets shape1
FILL NONE              # targets shape1
WORKWITH OFF
```

An explicit name in a command always overrides WORKWITH. WORKWITH is ignored during RUN and BATCH execution.

---

## Transforms

All transforms accept an optional shape name; WORKWITH applies if name is omitted.

```
MOVE   [<name>] <dx>,<dy>          # translate by delta pixels
ROTATE [<name>] <degrees>           # rotate around centroid
SCALE  [<name>] <factor>            # uniform scale (1.5 = 50% larger)
RESIZE [<name>] <xfactor> [yfactor] # per-axis scale; omit y for uniform
```

> **Group restriction:** if a shape is a member of a group, transforms must be applied to the group, not the individual shape. EXTRACT the shape first if you need to transform it independently.

---

## Grouping

```
GROUP   <group_name> <shape1> <shape2> [...]
UNGROUP <group_name>                    # dissolves group; members stay on canvas
EXTRACT <member> FROM <group_name>      # removes one member from group
```

GROUP, MOVE, ROTATE, SCALE, RESIZE all work on group names.

---

## Other Shape Management

### DELETE
```
DELETE <name> CONFIRM      # CONFIRM flag required to actually delete
```

### RENAME
```
RENAME <old_name> <new_name>
```
The shape's original (canonical) name is preserved internally; the display name changes.

---

## Canvas Management

```
CLEAR [WIP|MAIN|STASH] ALL   # ALL flag required; omit target to use active canvas
CLEAR ALL                     # clear active canvas
CLEAR MAIN ALL                # clear MAIN specifically
CLEAR STASH ALL               # clear the stash

LIST                   # shapes on active canvas
LIST WIP               # shapes on WIP
LIST MAIN              # shapes on MAIN
LIST STASH             # shapes in stash
LIST STORE             # shapes in project store (disk)
LIST GLOBAL            # shapes in global library (disk)
LIST PROC              # available procedural methods
LIST PRESET dynamic_polygon   # built-in presets for dynamic_polygon
LIST EXECUTABLES <file>       # executables defined in a script file
```

---

## Moving Shapes Between Canvases

### PROMOTE — WIP → MAIN
```
PROMOTE <name>           # move (shape leaves WIP)
PROMOTE COPY <name>      # copy (shape stays in WIP too)
```

### UNPROMOTE — MAIN → WIP
```
UNPROMOTE <name>         # move
UNPROMOTE COPY <name>    # copy
```

Name collisions are resolved automatically with a suffix.

---

## Temporary Storage: STASH

The stash is in-memory, session-only holding. Useful for temporarily getting a shape out of the way.

```
STASH <name>       # removes shape from active canvas to stash
UNSTASH <name>     # copies shape from stash back to active canvas
UNSTASH MOVE <name>  # moves (removes from stash after restoring)
```

---

## Permanent Storage: STORE / LOAD

STORE saves a shape as a JSON file on disk. It persists across sessions.

```
STORE <name>           # save to project store (shapes/ directory)
STORE GLOBAL <name>    # save to global library

LOAD <name>            # load onto active canvas (project store searched first, then global)
```

Name collisions on load are resolved automatically with a suffix.

---

## Saving PNGs

```
SAVE <filename>        # saves MAIN canvas as PNG to output/ directory
                       # .png extension added automatically if omitted
```

Note: SAVE always saves **MAIN**, regardless of which canvas is active.

---

## Project Save/Load

Saves the full session state: both canvases, stash.

```
SAVE_PROJECT <filename>      # saves to projects/ directory (.shapestudio extension auto-added)
LOAD_PROJECT <filename>      # restores full session
```

---

## VIEWPORT — Composition Guide

VIEWPORT draws a centered border on the canvas display to help you frame a composition — useful when you have a physical canvas of a specific aspect ratio in mind. It appears on both WIP and MAIN displays. **It does not affect saved PNGs.**

```
VIEWPORT 538,768       # absolute pixels (width, height), centered on 768×768
VIEWPORT 0.7,1.0       # ratio shorthand (same result — 0.7×768 = 538)
VIEWPORT 1.0,1.0       # full canvas border
VIEWPORT OFF           # remove the guide
```

Any value containing a decimal point is treated as a ratio multiplier against 768.

---

## The PROC System — Procedural Generation

PROC is how interesting shapes get made. It algorithmically builds a polygon by placing initial vertices, connecting them, and then iteratively applying evolution operations to the edges.

### Basic syntax
```
PROC dynamic_polygon <name> PARAM=value [PARAM=value ...]
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `VERTICES` | int or `min,max` | Number of starting vertices, or a random range |
| `BOUNDS` | `x1,y1,x2,y2` | Bounding box — shape will stay inside this area |
| `ITERATIONS` | int | How many evolution steps to apply |
| `CONNECT` | `angle_sort` or `convex_hull` | How initial vertices are wired into a polygon |
| `OPERATIONS` | list | Which operations to use (see below) |
| `BREAK_MARGIN` | float 0.0–0.5 | Minimum distance from segment endpoints for insertions |
| `BREAK_WIDTH_MAX` | float 0.0–1.0 | Maximum insertion width as fraction of segment length |
| `PROJECTION_MAX` | float | Maximum projection distance multiplier |
| `MIN_SEGMENT_LENGTH` | int (pixels) | Segments shorter than this are skipped |
| `DIRECTION_BIAS` | `inward`, `outward`, or `random` | Preferred projection direction |
| `SQUAREWAVE_INDEPENDENT_DIRECTIONS` | bool | Each squarewave step can go a different direction |
| `SQUAREWAVE_OPPOSITE_DIRECTION_PROB` | float 0.0–1.0 | Probability of reversing direction in squarewave |
| `VERBOSE` | int | Debug verbosity; 0 = off |

### Operations

Operations are what reshape the polygon each iteration. You specify which ones to use and can weight them.

| Operation | Effect |
|-----------|--------|
| `split_offset` | Splits a segment and offsets the new point perpendicularly |
| `sawtooth` | Inserts a V-shaped bump on a segment |
| `squarewave` | Inserts a rectangular step on a segment |
| `remove_point` | Removes an existing vertex (simplification) |
| `distort_original` | Shifts an existing vertex |

**Specifying operations — three formats:**

Equal weight (any will be chosen with equal probability):
```
OPERATIONS=split_offset,sawtooth
```

Weighted (colon-delimited weight after each name):
```
OPERATIONS=split_offset:10,sawtooth:5,squarewave:3,remove_point:1,distort_original:1
```

Higher number = more likely to be chosen each iteration.

### Built-in presets

Presets provide a shorthand for known-good parameter sets:
```
LIST PRESET dynamic_polygon

PROC dynamic_polygon s1 PRESET=organic BOUNDS=100,100,668,668
```

Available presets: `simple`, `complex`, `organic`.

### Examples

```
# Simple, low-complexity shape
PROC dynamic_polygon s1 VERTICES=5,7 BOUNDS=100,100,668,668 ITERATIONS=8 OPERATIONS=split_offset

# Organic, flowing form — inward bias, moderate complexity
PROC dynamic_polygon s1 VERTICES=6,10 BOUNDS=100,100,668,668 ITERATIONS=15 OPERATIONS=sawtooth DIRECTION_BIAS=inward BREAK_WIDTH_MAX=0.4 PROJECTION_MAX=1.5

# Angular, outward-reaching form
PROC dynamic_polygon s1 VERTICES=4,6 BOUNDS=100,100,668,668 ITERATIONS=12 OPERATIONS=squarewave DIRECTION_BIAS=outward PROJECTION_MAX=2.0

# Full variety — weighted mix of all operations
PROC dynamic_polygon s1 VERTICES=6,10 BOUNDS=150,150,618,618 ITERATIONS=20 OPERATIONS=split_offset:10,sawtooth:5,squarewave:4,remove_point:1,distort_original:1 DIRECTION_BIAS=random BREAK_WIDTH_MAX=0.15 PROJECTION_MAX=4.0
```

### Typical single-image workflow

```
SWITCH MAIN
CLEAR MAIN ALL
PROC dynamic_polygon s1 VERTICES=6,10 BOUNDS=100,100,668,668 ITERATIONS=15 OPERATIONS=split_offset:5,sawtooth:3,squarewave:2 DIRECTION_BIAS=random BREAK_WIDTH_MAX=0.15 PROJECTION_MAX=4.0
COLOR s1 black
WIDTH s1 3
FILL s1 NONE
SAVE myshape
```

---

## RAND() — Inline Randomization

`RAND(min,max)` and `RANDBOOL()` can appear anywhere in a command. They are evaluated once at parse time (before the command runs). In a BATCH loop they re-evaluate on every iteration, which is how you get variety across a run.

```
PROC dynamic_polygon s1 VERTICES=RAND(5,10) BOUNDS=100,100,668,668 ITERATIONS=RAND(10,25) OPERATIONS=sawtooth
WIDTH s1 RAND(2,4)
```

If both bounds are integers, the result is an integer. If either is a float, the result is a float.

`RANDBOOL()` returns 0 or 1.

---

## Script Files

Instead of typing commands one at a time, put them in a file and run them. Script files live in the `scripts/` directory.

### RUN — execute a script once

```
RUN <scriptfile> [section_or_executable]
```

### Text scripts (.txt)

One command per line. Lines starting with `#` are comments.

```
# myscript.txt
SWITCH MAIN
CLEAR MAIN ALL
PROC dynamic_polygon s1 VERTICES=6,9 BOUNDS=100,100,668,668 ITERATIONS=15 OPERATIONS=sawtooth DIRECTION_BIAS=inward
COLOR s1 black
WIDTH s1 3
```

Run it:
```
RUN myscript.txt
```

Text scripts support labeled sections using `@label` / `EOF` markers:

```
@setup
SWITCH MAIN
CLEAR MAIN ALL
EOF

@organic
PROC dynamic_polygon s1 VERTICES=6,10 BOUNDS=100,100,668,668 ITERATIONS=15 OPERATIONS=sawtooth DIRECTION_BIAS=inward
COLOR s1 black
EOF
```

```
RUN myscript.txt organic
LIST EXECUTABLES myscript.txt      # lists available labels
```

### JSON executable scripts

The format you use in practice. A JSON file with a `template_libraries` list and an `executables` dictionary. Each executable is a named set of template calls with parameters.

```
RUN myscript.json gen1             # run executable 'gen1'
RUN myscript.json --ALL            # run all executables in sequence
LIST EXECUTABLES myscript.json     # list what's available
```

---

## The Template System

Templates are parameterized, reusable command blueprints stored in JSON library files. Executables call templates with specific parameter values.

### Template library file

```json
{
  "version": "1.0",
  "templates": {
    "my_template": {
      "description": "...",
      "commands": [
        "CLEAR MAIN ALL",
        "PROC dynamic_polygon ${name} vertices=${verts} bounds=${bounds} iterations=${iters} operations=${ops} direction_bias=inward",
        "COLOR ${name} ${color}",
        "WIDTH ${name} ${width}"
      ],
      "required_params": ["name", "ops"],
      "optional_params": {
        "verts": "6,10",
        "bounds": "100,100,668,668",
        "iters": "15",
        "color": "black",
        "width": "2"
      }
    }
  }
}
```

- `${varname}` — substitution token
- `required_params` — must be supplied by the caller
- `optional_params` — defaults used when caller doesn't supply them

### Executable script file

```json
{
  "version": "1.0",
  "template_libraries": ["library.json"],
  "executables": {
    "gen1": {
      "description": "...",
      "randomization": {
        "iters": [10, 25],
        "projection": {"type": "normal", "min": 0.5, "max": 1.5, "mean": 1.0, "std": 0.3}
      },
      "commands": [
        {
          "template": "my_template",
          "params": {
            "name": "shape1",
            "ops": "split_offset:10,sawtooth:5,squarewave:4,remove_point:1,distort_original:1",
            "bounds": "150,150,618,618",
            "projection": "4.0",
            "width": "3"
          }
        }
      ]
    }
  }
}
```

### The `_` prefix convention — commenting out parameters

Any parameter key starting with `_` (one or more underscores) is **silently ignored**. This is how you keep alternative values in the file without deleting them:

```json
"params": {
  "verts": "6,10",          ← active
  "_verts": "4",            ← disabled (ignored)
  "__verts": "8,12"         ← also disabled
}
```

This is the standard way to preserve experiments while using a different value.

### Randomization in executables

The `randomization` block in an executable specifies how certain parameters are randomized on each BATCH iteration. Four formats:

**Uniform range** (two numbers):
```json
"iters": [10, 25]
```
Produces a random integer between 10 and 25.

**Simple list** (random choice):
```json
"color": ["black", "red", "blue"]
```
Picks one uniformly at random.

**Weighted list** (list of `[value, weight]` pairs):
```json
"color": [["black", 70], ["red", 20], ["blue", 10]]
```
Higher weight = more likely.

**Normal distribution:**
```json
"projection": {"type": "normal", "min": 0.5, "max": 1.5, "mean": 1.0, "std": 0.3}
```
Samples from a normal distribution with rejection sampling to stay within `[min, max]`.

Randomized values become parameters available for template substitution via `${varname}`.

---

## BATCH — Generating Many Images

BATCH runs an executable repeatedly, saving a PNG from each iteration. Randomization re-fires every iteration, producing variety.

```
BATCH <count> <scriptfile> <executable> <output_prefix> [WIP|MAIN] [STORE]
```

- `count` — number of images to generate
- `scriptfile` — JSON file in `scripts/`
- `executable` — which executable to run (or comma-separated list, or `--ALL`)
- `output_prefix` — path prefix for output files (relative to `output/`)
- `WIP|MAIN` — which canvas to save (default: MAIN)
- `STORE` — optional flag: also save shape JSON to `shapes/` alongside each PNG

### Output naming

Files are named `<prefix>_NNNN.png`. Numbering **continues from where it left off** — if `output/run1_0023.png` already exists, the next run starts at `_0024`. You can re-run BATCH on the same prefix to extend a set.

When running multiple executables (comma-separated or `--ALL`), the executable name is appended to the prefix: `<prefix>_<execname>_NNNN.png`.

### Examples

```
# 50 images from a single executable
BATCH 50 sa224.json gen1 sa224/run1 MAIN

# 100 images, also saving shape JSON
BATCH 100 generate_02.json gen02a results/organic MAIN STORE

# All executables in the file
BATCH 20 generate_02.json --ALL results/explore MAIN

# Multiple specific executables
BATCH 30 generate_02.json gen02a,gen02b results/both MAIN
```

---

## Your Current Scripts and Libraries

The files actively in use reference `library.json` as their template source.

### Template Libraries

| File | Key templates |
|------|--------------|
| `templates/library.json` | `clear_main_template`, `organic_outline_template`, `organic_outline_nofill`, `organic_outline` (with fill), `u_block_skinny_legs`, `bg_shape`, `focal_shape`, `textured_shape`, `accent_line` |
| `templates/library_for_lora.json` | Older set; all templates self-clear MAIN. Use for legacy reference |
| `templates/library_for_lora_1.json` | Minimal: `clear_main_template` + `organic_outline_template` only |

### Script Files

| File | Contents |
|------|---------|
| `scripts/sa224.json` | `clear_main`, `gen1`, `gen2` — for SA224 painting work |
| `scripts/generate_02.json` | `clear_main`, `gen02a`, `gen02b` — block/slab forms |
| `scripts/generate_03_u.json` | `clear_main`, `gen02a`, `gen03u` — U-block variant |
| `scripts/lora_trial_01.json` | Legacy: `clear_main`, `trial_01`, `trial_01b` |
| `scripts/lora_trial_conglomeration.json` | Legacy: larger collection of named trial executables |
| `scripts/weighted_examples.json` | Example of weighted randomization patterns |

---

## File System Layout

```
project root/
├── output/          ← PNG files land here (auto-created)
├── scripts/         ← Your .txt and .json script files
├── shapes/          ← Stored shapes (STORE command), JSON format
├── projects/        ← Saved session states (SAVE_PROJECT)
└── templates/       ← Template library JSON files

config.json          ← System configuration
```

---

## Quick Reference

```
# Shape creation
LINE  <name> x1,y1 x2,y2
POLY  <name> x1,y1 x2,y2 x3,y3 [...]
PROC  dynamic_polygon <name> VERTICES=6,10 BOUNDS=100,100,668,668 ITERATIONS=15 OPERATIONS=split_offset:5,sawtooth:3

# Style (name optional if WORKWITH set)
COLOR  [<name>] <color>          # named / #hex / rgb() / hsv()
WIDTH  [<name>] <int>
FILL   [<name>] <color|NONE>
ALPHA  [<name>] <0.0–1.0>
ZORDER [<name>] <int>
RESET_ZORDER [value]

# WORKWITH context
WORKWITH <name>
WORKWITH OFF

# Transforms (name optional if WORKWITH set)
MOVE   [<name>] dx,dy
ROTATE [<name>] <degrees>
SCALE  [<name>] <factor>
RESIZE [<name>] <xfactor> [yfactor]

# Groups
GROUP   <gname> s1 s2 [...]
UNGROUP <gname>
EXTRACT <member> FROM <gname>

# Other shape ops
DELETE  <name> CONFIRM
RENAME  <old> <new>

# Canvases
SWITCH WIP|MAIN
CLEAR [WIP|MAIN|STASH] ALL
PROMOTE      [COPY] <name>      # WIP → MAIN
UNPROMOTE    [COPY] <name>      # MAIN → WIP

# Stash (in-memory)
STASH   <name>
UNSTASH [MOVE] <name>

# Store (on disk)
STORE [GLOBAL] <name>
LOAD  <name>

# Saving
SAVE <filename>                  # MAIN canvas → output/ as PNG
SAVE_PROJECT <name>              # full session → projects/
LOAD_PROJECT <name>

# Inspection
LIST [WIP|MAIN|STASH|STORE|GLOBAL|PROC]
LIST PRESET dynamic_polygon
LIST EXECUTABLES <scriptfile>
INFO <name>
INFO PROC dynamic_polygon
HELP [<command>]

# Viewport guide (display only, not in PNG)
VIEWPORT <w>,<h>    # pixels or ratios (e.g. 0.7,1.0)
VIEWPORT OFF

# Scripting
RUN   <file.json> <executable>
RUN   <file.txt>  [label]
BATCH <n> <file.json> <exec|exec1,exec2|--ALL> <prefix> [MAIN|WIP] [STORE]

# Inline randomization (re-fires each BATCH iteration)
RAND(min,max)
RANDBOOL()

EXIT | QUIT
```
