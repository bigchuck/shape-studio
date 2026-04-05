# Shape Studio — Getting Back Up To Speed

A practical primer based on the actual source code, written after a 3-month break.

---

## What Shape Studio Is

Shape Studio is a Python/Tkinter application you run on the desktop. It gives you a three-panel GUI:

- **Left panel** — command log (everything you type and the results)
- **Center panel** — the canvas display (what you're drawing)
- **Right panel** — integrated help browser

You drive it entirely by typing commands into a prompt at the bottom. There is no mouse drawing. Every shape is created or manipulated through a text command. The canvas is **768×768 pixels** and outputs 768×768 PNG files, which was the exact target size for your LoRA training dataset.

---

## The Two-Canvas System

There are always **two canvases** in memory:

| Canvas | Purpose |
|--------|---------|
| `WIP`  | Work-in-progress. Your "scratch pad." |
| `MAIN` | The "clean" canvas. What you save/export. |

At startup the active canvas is WIP. Commands create shapes on whichever canvas is currently active. Use `SWITCH` to move between them.

```
SWITCH MAIN      # make MAIN the active canvas
SWITCH WIP       # switch back to WIP
```

Shapes on WIP and MAIN are completely independent registries. A shape named `foo` on WIP is a different object from a shape named `foo` on MAIN.

---

## File System Layout

All paths are relative to the project root. The key folders are:

```
project/
├── output/          ← PNG files land here (auto-created)
├── scripts/         ← Your .txt and .json script files live here
├── shapes/          ← Per-project stored shapes (STORE/LOAD)
├── projects/        ← Saved project states (.shapestudio files)
├── templates/       ← Template library JSON files
└── config.json      ← System configuration
```

---

## Command Syntax Rules

- Commands are **case-insensitive** for the keyword; names are case-sensitive.
- Coordinates are always `x,y` (no spaces around the comma).
- Parameters in PROC use `KEY=value` syntax (no spaces around `=`).
- Comments in script files start with `#`.
- Inline randomization: `RAND(min,max)` and `RANDBOOL()` are expanded before parsing.

---

## Core Shape Commands

### LINE
Creates a two-point line.
```
LINE <name> <x1>,<y1> <x2>,<y2>

LINE horizon  50,400  718,400
```

### POLY
Creates a polygon from 3 or more points.
```
POLY <name> <x1>,<y1> <x2>,<y2> <x3>,<y3> [...]

POLY triangle  100,600  400,100  700,600
```

---

## Styling Commands

These work on any shape (line or polygon) by name.

```
COLOR <name> <color>       # Outline/stroke color
WIDTH <name> <pixels>      # Stroke width (integer, min 1)
FILL  <name> <color|NONE>  # Fill color, or NONE for no fill
ALPHA <name> <0.0-1.0>     # Transparency (0=invisible, 1=opaque)
ZORDER <name> <int>        # Drawing order (higher = on top)
```

**Color formats accepted everywhere:**
```
black               # Named color
#FF0000             # Hex (6-digit)
#F00                # Hex (3-digit, auto-expanded)
rgb(255,0,0)        # RGB function
255,0,0             # RGB shorthand
hsv(360,100,100)    # HSV function (H:0-360, S/V:0-100)
```

**Examples:**
```
COLOR myshape #2C3E50
FILL  myshape rgb(52,152,219)
ALPHA myshape 0.6
WIDTH myshape 3
ZORDER myshape 10
```

---

## Transformation Commands

```
MOVE   <name> <dx>,<dy>         # Translate by delta
ROTATE <name> <degrees>          # Rotate around centroid
SCALE  <name> <factor>           # Uniform scale from centroid
RESIZE <name> <x_factor> [y_factor]  # Non-uniform scale (omit y for uniform)
```

> **Note:** If a shape is in a group, you cannot transform it directly. You must either transform the group, EXTRACT the shape first, or UNGROUP.

---

## Grouping

```
GROUP  <group_name> <shape1> <shape2> [...]   # Create group
UNGROUP <group_name>                          # Dissolve group, members stay
EXTRACT <member_name> FROM <group_name>       # Remove one member from group
```

Groups can be transformed as a unit. MOVE, ROTATE, SCALE, RESIZE all work on group names.

---

## Canvas Management

```
CLEAR                    # Clear active canvas (prompts unless ALL used)
CLEAR ALL                # Clear active canvas (no prompt)
CLEAR WIP ALL            # Clear WIP specifically
CLEAR MAIN ALL           # Clear MAIN specifically
CLEAR STASH              # Clear the stash

LIST                     # List shapes on active canvas
LIST WIP                 # List shapes on WIP
LIST MAIN                # List shapes on MAIN
LIST STASH               # List stashed shapes
LIST STORE               # List locally stored shapes
LIST GLOBAL              # List globally stored shapes
LIST PROC                # List available procedural methods

INFO <name>              # Show detailed info about a shape
INFO PROC dynamic_polygon  # Show PROC method documentation
```

---

## Stash / Store / Persistence

**Stash** is in-memory, session-only temporary holding:
```
STASH <name>             # Move shape from active canvas to stash
UNSTASH <name>           # Move shape from stash back to active canvas
```

**Store** saves a shape to disk (persists across sessions):
```
STORE <name>             # Save shape to project shapes folder
LOAD  <name>             # Load shape from project/global store onto active canvas
```

**Project** saves the entire session state:
```
SAVE_PROJECT <filename>  # Saves WIP, MAIN, stash to .shapestudio file
LOAD_PROJECT <filename>  # Restores entire session state
```

**PNG export:**
```
SAVE <filename>          # Saves active canvas as PNG (adds .png if omitted)
                         # File goes into output/ folder
```

---

## The PROC System — Procedural Generation

This is the heart of the LoRA dataset generation workflow. PROC algorithmically generates complex shapes.

### Basic Syntax
```
PROC dynamic_polygon <name> PARAM=value [PARAM=value ...]
```

### The `dynamic_polygon` Method

The only currently registered method. It builds a polygon by:
1. Placing random initial vertices inside a bounding box
2. Connecting them (angle sort or convex hull)
3. Iteratively applying "evolution operations" to the edges

**All Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `VERTICES` | `int` or `min,max` | `5,8` | Number of starting vertices |
| `BOUNDS` | `x1,y1,x2,y2` | **Required** | Bounding box |
| `ITERATIONS` | int | 10 | How many evolution steps |
| `CONNECT` | `angle_sort` \| `convex_hull` | `angle_sort` | How initial vertices are wired together |
| `OPERATIONS` | list (see below) | `split_offset,sawtooth` | Which operations to apply per iteration |
| `BREAK_MARGIN` | float 0.0–0.5 | 0.15 | Min distance from endpoints for insertions |
| `BREAK_WIDTH_MAX` | float 0.0–1.0 | 0.5 | Max insertion width as fraction of segment |
| `PROJECTION_MAX` | float 0.5–5.0 | 2.0 | Max projection distance multiplier |
| `MIN_SEGMENT_LENGTH` | int (pixels) | 10 | Skip segments shorter than this |
| `DIRECTION_BIAS` | `inward` \| `outward` \| `random` | `random` | Preferred projection direction |
| `SQUAREWAVE_INDEPENDENT_DIRECTIONS` | bool | false | Squarewave steps can go different ways |
| `SQUAREWAVE_OPPOSITE_DIRECTION_PROB` | float 0.0–1.0 | 0.2 | Prob of reverse direction in squarewave |
| `MAX_RETRIES` | int | 15 | Attempts per modification before skipping |
| `RETURN_MODE` | `single` \| `group` \| `individual` | `single` | How result is returned |
| `VERBOSE` | int | 0 | Debug verbosity (0=off) |

**Operations:**

| Operation | Effect |
|-----------|--------|
| `split_offset` | Inserts a point by splitting a segment and offsetting perpendicularly |
| `sawtooth` | Creates a V-shaped bump on a segment |
| `squarewave` | Creates a rectangular step on a segment |
| `remove_point` | Removes a vertex (simplification) |
| `distort_original` | Shifts an existing vertex |

Operations can be given as a comma-separated list. Equal weight by default. Use `[[op,weight],...]` syntax for weighted selection.

**Built-in Presets** (invoke with `LIST PRESET dynamic_polygon`):

| Preset | Character |
|--------|-----------|
| `simple` | 5–8 verts, 5 iterations, split_offset only |
| `complex` | 8–12 verts, 20 iterations, all ops |
| `organic` | 6–10 verts, 12 iterations, sawtooth, inward bias |

### PROC Examples

```
# Simple polygon in a defined region
PROC dynamic_polygon myshape VERTICES=6 BOUNDS=100,100,668,668 ITERATIONS=10 OPERATIONS=split_offset

# Organic flowing shape
PROC dynamic_polygon blob VERTICES=6,10 BOUNDS=100,100,668,668 ITERATIONS=15 OPERATIONS=sawtooth DIRECTION_BIAS=inward BREAK_WIDTH_MAX=0.4

# Complex angular shape
PROC dynamic_polygon angular VERTICES=4,6 BOUNDS=100,100,668,668 ITERATIONS=12 OPERATIONS=squarewave DIRECTION_BIAS=outward PROJECTION_MAX=2.0

# Full combo — most variety
PROC dynamic_polygon wild VERTICES=8,12 BOUNDS=100,100,668,668 ITERATIONS=20 OPERATIONS=split_offset,sawtooth,squarewave DIRECTION_BIAS=random BREAK_WIDTH_MAX=0.6 PROJECTION_MAX=2.5
```

### Typical Single-Image Workflow
```
SWITCH MAIN
CLEAR MAIN ALL
PROC dynamic_polygon shape VERTICES=6,9 BOUNDS=100,100,668,668 ITERATIONS=12 OPERATIONS=sawtooth DIRECTION_BIAS=inward
COLOR shape black
WIDTH shape 2
FILL shape NONE
SAVE my_shape
```

---

## Script Files

Instead of typing commands one at a time, you can put commands in a file and execute them.

### Text Script Files (.txt)

Plain text, one command per line. Supports labeled sections.

```
# my_script.txt

# Unlabeled section (runs first if no label given)
CLEAR MAIN ALL
PROC dynamic_polygon s1 VERTICES=5 BOUNDS=100,100,668,668 ITERATIONS=8 OPERATIONS=split_offset
COLOR s1 black
WIDTH s1 2

@organic_test
CLEAR MAIN ALL
PROC dynamic_polygon s2 VERTICES=6,10 BOUNDS=100,100,668,668 ITERATIONS=15 OPERATIONS=sawtooth DIRECTION_BIAS=inward
COLOR s2 black
EOF

@complex_test
CLEAR MAIN ALL
PROC dynamic_polygon s3 VERTICES=8,12 BOUNDS=100,100,668,668 ITERATIONS=20 OPERATIONS=split_offset,sawtooth
COLOR s3 black
EOF
```

Run it:
```
RUN my_script.txt                  # Runs unlabeled section (or first section)
RUN my_script.txt organic_test     # Runs the @organic_test section
RUN my_script.txt complex_test     # Runs the @complex_test section
LIST EXECUTABLES my_script.txt     # Lists available labels
```

### JSON Script Files (.json)

Structured format. Each top-level key is a "section." Each section has a `commands` array of strings or dicts.

```json
{
  "my_section": {
    "description": "Example section",
    "commands": [
      "CLEAR MAIN ALL",
      "PROC dynamic_polygon shape VERTICES=6 BOUNDS=100,100,668,668 ITERATIONS=10 OPERATIONS=sawtooth",
      "COLOR shape black",
      "WIDTH shape 2"
    ]
  }
}
```

Run it:
```
RUN my_script.json my_section
```

---

## BATCH — Generating the Training Dataset

BATCH runs a script many times and saves a PNG from each iteration. This is the primary LoRA dataset generation workflow.

### Old-style BATCH (plain .txt or simple .json)
```
BATCH <count> <scriptfile> <output_prefix> [WIP|MAIN]

BATCH 100 gen_script.txt lora_img MAIN
```

Each iteration executes the whole script, saves as `output/lora_img_001.png` through `output/lora_img_100.png`.

Use `RAND(min,max)` in the script to introduce per-iteration variation:
```
# gen_script.txt
CLEAR MAIN ALL
PROC dynamic_polygon shape VERTICES=RAND(5,10) BOUNDS=100,100,668,668 ITERATIONS=RAND(10,25) OPERATIONS=split_offset,sawtooth DIRECTION_BIAS=random
COLOR shape black
WIDTH shape RAND(2,4)
```

### Template-style BATCH (new format .json with executables)
```
BATCH <count> <scriptfile> <executable_name> <output_prefix> [WIP|MAIN]
BATCH <count> <scriptfile> exec1,exec2,exec3 <output_prefix> [WIP|MAIN]   # Multiple executables
BATCH <count> <scriptfile> --ALL <output_prefix> [WIP|MAIN]                # All executables
```

The "executables" format script references template libraries and does parameter substitution. See the Template section below.

---

## The Template System

Templates are reusable parameterized command blueprints stored in JSON library files. Executables are scripts that call templates with specific parameter values.

### Template Library File (e.g., `library_for_lora.json`)

```json
{
  "version": "1.0",
  "templates": {
    "organic_outline_template": {
      "description": "Organic polygon outline",
      "commands": [
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

- `${varname}` is the substitution syntax.
- `required_params` must be provided by the caller.
- `optional_params` are defaults that the caller can override.

### Executable Script File

A JSON file that references template libraries and defines named "executables," each of which calls one or more templates with specific params.

```json
{
  "template_libraries": ["library_for_lora.json"],
  "global_params": {
    "color": "black"
  },
  "executables": {
    "gen_organic": {
      "commands": [
        {
          "template": "organic_outline_template",
          "params": {
            "name": "shape",
            "ops": "sawtooth",
            "iters": "15"
          }
        }
      ]
    },
    "gen_geometric": {
      "commands": [
        {
          "template": "organic_outline_template",
          "params": {
            "name": "shape",
            "ops": "squarewave",
            "iters": "12",
            "verts": "4,6"
          }
        }
      ]
    }
  }
}
```

Run one:
```
RUN my_executables.json gen_organic
```

Batch with one:
```
BATCH 50 my_executables.json gen_organic lora_organic MAIN
```

Batch with all:
```
BATCH 50 my_executables.json --ALL lora_all MAIN
# → output files: output/lora_all_gen_organic_0001.png, output/lora_all_gen_geometric_0001.png, etc.
```

---

## The ENHANCE System

ENHANCE applies intelligent aesthetic analysis and modification to shapes. Less commonly used for raw dataset generation, more useful for polishing individual compositions.

```
ENHANCE <method> <shape_name> INTENT="key:value,key:value,..."
ENHANCE <method> canvas INTENT="..."   # Apply to whole canvas context
```

List available methods:
```
LIST          # includes enhance methods in output
INFO ENHANCE <method_name>
```

---

## VALIDATE — Check a Script Without Running It

```
VALIDATE <scriptfile>
```

Parses the script and checks all referenced templates and parameters are resolvable without actually executing any commands. Useful before a big BATCH run.

---

## ANIMATE — Create GIF Previews

If you have a series of saved PNGs with a shared prefix, ANIMATE can stitch them into a GIF for preview.

```
ANIMATE <base_name> [FPS=2] [LOOP=true|false]

ANIMATE lora_organic FPS=3 LOOP=true
```

---

## RESET_ZORDER

Resets the z-order counter on the active canvas.

```
RESET_ZORDER         # Resets to config default (0)
RESET_ZORDER 10      # Resets to specific value
```

---

## Full Workflow: Generating a LoRA Training Dataset

Here is the complete pattern you used before, reconstructed from the scripts and library files in the project:

### Step 1 — Write a template library
Create or edit a file in `scripts/` (or `templates/`) like `library_for_lora.json` with your reusable shape templates.

### Step 2 — Write an executables script
Create a `.json` script that references your library and defines named executables for each shape family you want. For example `gen_dataset.json`.

### Step 3 — Test manually first
```
SWITCH MAIN
RUN gen_dataset.json gen_organic
SAVE test_organic
```
Inspect the result, adjust parameters.

### Step 4 — Validate the script
```
VALIDATE scripts/gen_dataset.json
```

### Step 5 — Run the batch
```
BATCH 200 gen_dataset.json gen_organic lora_organic MAIN
```
or for all variants at once:
```
BATCH 200 gen_dataset.json --ALL lora_batch MAIN
```

### Step 6 — Output
All PNGs land in `output/` as `lora_organic_0001.png` … `lora_organic_0200.png` (768×768).

---

## Quick Reference Card

```
# Shape creation
LINE  <name> x1,y1 x2,y2
POLY  <name> x1,y1 x2,y2 x3,y3 [...]
PROC  dynamic_polygon <name> VERTICES=5,8 BOUNDS=100,100,668,668 ITERATIONS=10 OPERATIONS=sawtooth

# Styling
COLOR  <name> <color>
WIDTH  <name> <int>
FILL   <name> <color|NONE>
ALPHA  <name> <0.0-1.0>
ZORDER <name> <int>

# Transforms
MOVE   <name> dx,dy
ROTATE <name> <degrees>
SCALE  <name> <factor>
RESIZE <name> <xfactor> [yfactor]

# Groups
GROUP   <gname> s1 s2 ...
UNGROUP <gname>
EXTRACT <member> FROM <gname>

# Canvas
SWITCH WIP|MAIN
CLEAR [WIP|MAIN] ALL
LIST [WIP|MAIN|STASH|STORE|GLOBAL|PROC]
INFO <name>
INFO PROC dynamic_polygon

# Persistence
SAVE <filename>               # PNG → output/
SAVE_PROJECT <name>           # Full session → projects/
LOAD_PROJECT <name>
STORE <name>                  # Shape to shapes/
LOAD  <name>                  # Shape from shapes/
STASH <name>  / UNSTASH <name>

# Scripting & batch
RUN   <file.txt> [label]
RUN   <file.json> [section]
BATCH <n> <file.txt> <prefix> [MAIN|WIP]                       # Simple
BATCH <n> <file.json> <executable|--ALL> <prefix> [MAIN|WIP]   # Template

# Misc
VALIDATE <scriptfile>
RAND(min,max)  RANDBOOL()     # Inline in any command
ENHANCE <method> <shape> INTENT="k:v,k:v"
RESET_ZORDER [value]
ANIMATE <prefix> [FPS=2] [LOOP=true|false]
EXIT | QUIT
```

---

## What the Existing JSON Files Are

| File | Purpose |
|------|---------|
| `library.json` | General-purpose template library with `bg_shape`, `focal_shape`, `textured_shape`, `accent_line` templates |
| `library_for_lora.json` | LoRA-specific library with outline-only templates: `simple_outline_template`, `organic_outline_template`, `geometric_outline_template`, `complex_outline_template`, `random_outline_batch_template`, `centered_outline_template`, `preset_*` variants |
| `library_for_lora_1.json` | Slimmer variant: just `clear_main_template` and `organic_outline_template` (no CLEAR in template; caller handles it) |
| `config.json` | System config: canvas size (768×768), paths, PROC defaults, animation settings |

The key difference between the two LoRA libraries: `library_for_lora.json` includes `CLEAR MAIN ALL` inside each template (self-contained). `library_for_lora_1.json` separates clearing into its own `clear_main_template`, letting you compose them flexibly in an executable.

---

## Things to Watch Out For

**Bounds** — The canvas is 768×768 with origin at top-left. The LoRA library uses `100,100,668,668` as the standard working area, giving a ~100px margin all around. The "centered" template uses `184,184,584,584` for tighter centering.

**Shape names must be unique per canvas** — Creating a shape with a name that already exists raises an error. If your batch scripts don't CLEAR first, they'll fail on iteration 2+.

**Group membership blocks transforms** — If a shape is in a group, individual transforms fail. Transform the group or EXTRACT first.

**BATCH output numbering** — Plain BATCH uses 3-digit padding (`_001`). Template BATCH uses 4-digit padding (`_0001`).

**RAND() timing** — `RAND(min,max)` is expanded at parse time, once per command line. It re-randomizes on every iteration of a BATCH loop. If both bounds are integers, the result is an integer.

**Scripts live in `scripts/`** — RUN and BATCH look for files relative to `config.paths.scripts` which defaults to `scripts/`. Put your `.txt` and `.json` script files there.
