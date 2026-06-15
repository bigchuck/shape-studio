# Shape Studio — Composition Directives Reference

**Version:** June 2026  
**Status:** Living document — updated as composition system evolves

---

## Overview

The composition system generates multi-shape arrangements through batch-driven
executable JSON. All composition behavior is specified in JSON files — no
inline command syntax is used for composition directives.

The system is built around three layers:

1. **COMPOSE command** — loads shapes onto the canvas
2. **command_loop** — drives transforms and constraint-based placement
3. **Placement solver** — applies geometry constraints until satisfied

Canvas dimensions are 768 x 768 pixels.  
All shapes are Polygons. Geometric primitive is the **convex hull** of the shape's point set.

---

## Executable Structure

Composition executables live in the standard batch JSON file alongside other executables.
The COMPOSE command is invoked via a template reference inside the executable's `commands` list.

```json
"my_composition": {
  "target_canvas": "MAIN",
  "commands": [
    {
      "template": "compose_1",
      "params": {
        "color": "black",
        "width": "2"
      },
      "compose_parameters": {
        "shapes":       { ... },
        "on_load":      [ ... ],
        "command_loop": { ... }
      }
    }
  ]
}
```

`compose_parameters` is passed through to the COMPOSE engine intact —
it is not subject to template string substitution.

---

## Template: compose_1

Base template for composition operations. Provides visual parameter defaults.
Defined in `templates/library.json`.

```json
"compose_1": {
  "description": "Base composition template - visual defaults",
  "target_canvas": "MAIN",
  "commands": [
    { "command": "COMPOSE" }
  ],
  "optional_params": {
    "bounds": "100,100,668,668",
    "color": "black",
    "width": "2"
  }
}
```

---

## compose_parameters

Top-level key in the executable command dict. Contains all composition directives.

```json
"compose_parameters": {
  "shapes":       { ... },    // shape loading specification
  "on_load":      [ ... ],    // commands applied to each shape immediately on arrival
  "command_loop": { ... }     // transform and placement loop
}
```

---

## Shape Loading — shapes key

### Specified (explicit list)

Load named shapes from the `shapes/` store by exact name. All shapes in the
list are always loaded.

```json
"shapes": {
  "specified": ["sa224/gen1_0033", "sa224/gen4_0050"]
}
```

### Pool (random selection from list)

Pick N shapes at random from an explicit list, without replacement by default.

```json
"shapes": {
  "selection": [
    {
      "method": "pool",
      "shapes": ["sa224/gen4_0050", "sa224/gen4_0051", "sa224/gen4_0052"],
      "count": 2,
      "replacement": false
    }
  ]
}
```

- `count` — fixed integer or `{"random": "uniform_int", "min": 2, "max": 4}`
- `replacement` — if `true`, same shape may appear more than once. Default `false`.

### Wildcard (filesystem glob)

Match shapes in the `shapes/` store by full-path pattern. `*` and `?` supported.

```json
"shapes": {
  "selection": [
    {
      "method": "wildcard",
      "pattern": "sa224/gen4_*",
      "count": 3,
      "replacement": false
    }
  ]
}
```

### Combined selection (anchor + pool)

Use `selection` array to mix methods. Shapes load in order; working names
are assigned sequentially across all entries.

```json
"shapes": {
  "selection": [
    {"method": "specified", "shapes": ["sa224/gen1_0033"]},
    {"method": "wildcard",  "pattern": "sa224/gen4_*", "count": 2}
  ]
}
```

Shape 1 is always the specified anchor; shapes 2-3 are random wildcard picks.

### Working names

Shapes are assigned sequential working names: `compose_shape_1`, `compose_shape_2`, ...

Working names are stable and predictable — they can be referenced by name,
range, or list in `command_loop` and `placement_blocks`. Missing working names
(when random count produces fewer shapes than controls expect) are skipped silently.

---

## on_load

Commands applied to every loaded shape immediately after it arrives on canvas,
before `command_loop` runs. No `target` field needed — each loaded shape is
the target in turn.

```json
"on_load": [
  {"command": "FILL",    "value": "#d0d0d0"},
  {"command": "WIDTH",   "value": 1},
  {"command": "REFLECT", "axis": "random",       "chance": 0.5},
  {"command": "REFLECT", "axis": {"random": "choice", "values": ["horizontal", "vertical"]}, "chance": 0.3}
]
```

- `chance` — optional float 0.0–1.0. Each shape independently rolls against this value.
  Default 1.0 (always applies).
- `on_load` commands are recorded in `commands_applied` and replayed on LOAD.

---

## Outputs

Each COMPOSE batch iteration produces:

- **PNG** — canvas image saved to `output/<prefix>_<NNNN>.png`
- **Construction JSON** — saved to `shapes/<prefix>_<NNNN>.json`

### Construction JSON format

```json
{
  "composition_id":   "compose_test1_0001",
  "executable":       "compose_test1",
  "timestamp":        "2026-06-10T...",
  "shapes_loaded": [
    { "working_name": "compose_shape_1", "source": "sa224/gen1_0033" },
    { "working_name": "compose_shape_2", "source": "sa224/gen4_0050" }
  ],
  "commands_applied": [
    "FILL compose_shape_1 #d0d0d0",
    "REFLECT compose_shape_1 AXIS=horizontal",
    "MOVE compose_shape_2 34.5000,12.2000",
    ...
  ]
}
```

`commands_applied` records every transform applied during the run, in order.
These are replayed when the composition is reloaded.

### Reloading a Composition

`LOAD <composition_name>` detects the `composition_id` key and reloads
all component shapes under their original working names, then replays
`commands_applied` to reconstruct the exact composition state.

```
LOAD sa224/compose_test1_0001
```

---

## Source Shape for DERIVE

When a template has `source_shape` set, the named shape is loaded as a seed
for subsequent PROC calls. The loaded geometry is passed as `seed_points`
to `dynamic_polygon`, skipping Phase 1 and Phase 2 (convex hull generation).

```json
"source_shape": "sa224/gen1_0033"
```

The derived shape carries a `derived_from` breadcrumb in its stored JSON:

```json
{
  "name": "sa224/derive_0001",
  "derived_from": "sa224/gen1_0033",
  ...
}
```

---

## command_loop

Optional loop that runs after shapes are loaded and `on_load` commands execute.

```json
"command_loop": {
  "verbose":                true,
  "iterations":             1,
  "always_transforms":      [ ... ],
  "conditional_transforms": [ ... ],
  "placement_blocks":       [ ... ]
}
```

**`verbose`** — `true` (default) emits decision trace to the app UI log.

**`iterations`** — fixed integer or random spec:
```json
"iterations": 3
"iterations": {"random": "uniform_int", "min": 2, "max": 8}
```

**Backward-compatible aliases:** `commands` = `always_transforms`,
`select_blocks` = `conditional_transforms`.

---

## Target Specification

All blocks that specify a `target` accept these forms:

```json
"target": "compose_shape_2"              // specific name
"target": "all"                          // every loaded shape
"target": "random"                       // one shape at random (with replacement)
"target": {"range": [2, 5]}             // compose_shape_2 through compose_shape_5
"target": {"list": [1, 3, 5]}           // compose_shape_1, compose_shape_3, compose_shape_5
"target": {"list": ["compose_shape_2"]} // explicit name list
```

Range and list targets skip any working name not present on canvas — safe to use
when shape count varies via random selection.

---

## always_transforms

Commands applied unconditionally to a target on every iteration.
`target` is required.

```json
"always_transforms": [
  {
    "command": "MOVE",
    "target": "all",
    "delta": [5, 5]
  }
]
```

---

## conditional_transforms

Each block fires independently, controlled by `chance`.

```json
"conditional_transforms": [
  {
    "chance":  0.7,
    "target":  {"range": [1, 5]},
    "commands": [
      { "command": "DEFORM", "axis": "major",
        "along":  {"random": "uniform", "min": 0.8, "max": 1.2},
        "across": {"random": "uniform", "min": 0.8, "max": 1.2} },
      { "command": "REFLECT", "axis": "random" }
    ]
  }
]
```

- `chance` — float 0.0–1.0. Default 1.0.
- `target` — any target spec form above. Resolved once per block per iteration;
  all commands in the block use the same resolved target(s).
- `commands` — list of transform commands.

---

## Supported Transform Commands

All numeric parameters accept fixed values or random specs (see Random Values section).

### MOVE

```json
{ "command": "MOVE", "delta": [dx, dy] }
{ "command": "MOVE", "direction": "SE",     "distance": 40 }
{ "command": "MOVE", "direction": 135,      "distance": {"random": "uniform", "min": 20, "max": 80} }
{ "command": "MOVE", "direction": "random", "distance": 40 }
{ "command": "MOVE", "direction": {"random": "choice",  "values": ["N","SE","W"]}, "distance": 40 }
{ "command": "MOVE", "direction": {"random": "degrees", "min": 0, "max": 360},    "distance": 40 }
```

**Compass directions — 16-point:**
`N  NNE  NE  ENE  E  ESE  SE  SSE  S  SSW  SW  WSW  W  WNW  NW  NNW`

**Numeric degrees:** 0 = North, 90 = East, 180 = South, 270 = West (clockwise).

### DEFORM

Stretch or compress along the shape's computed principal axis.

```json
{
  "command": "DEFORM",
  "axis":   "major",
  "along":  {"random": "uniform", "min": 0.8, "max": 1.2},
  "across": {"random": "uniform", "min": 0.8, "max": 1.2}
}
```

- `axis` — `"major"` (longest) or `"minor"` (shortest).
- `along` / `across` — scale factors. 1.0 = no change.

### ROTATE

```json
{ "command": "ROTATE", "angle": 45 }
{ "command": "ROTATE", "angle": {"random": "uniform", "min": -45, "max": 45} }
```

### SCALE

```json
{ "command": "SCALE", "factor": 0.8 }
{ "command": "SCALE", "factor": {"random": "uniform", "min": 0.6, "max": 1.4} }
```

### REFLECT

Mirror a polygon across an axis through its centroid. Reverses handedness
(distinct from ROTATE).

```json
{ "command": "REFLECT", "axis": "horizontal" }
{ "command": "REFLECT", "axis": "random" }
{ "command": "REFLECT", "axis": {"random": "choice", "values": ["horizontal", "vertical"]} }
```

- `axis` — `"horizontal"` (top/bottom swap), `"vertical"` (left/right swap),
  `"major"` (across major axis), `"minor"` (across minor axis),
  `"random"` (pick any of the four).

### COLOR / WIDTH / FILL / ALPHA / ZORDER

```json
{ "command": "COLOR",  "value": "black" }
{ "command": "WIDTH",  "value": 2 }
{ "command": "FILL",   "value": "#d0d0d0" }
{ "command": "ALPHA",  "value": 0.7 }
{ "command": "ZORDER", "value": 1 }
```

---

## Random Values

Any numeric parameter accepts a fixed value or a random spec.

```json
{"random": "uniform",     "min": 0.7, "max": 1.3}
{"random": "normal",      "mean": 1.0, "std": 0.2, "min": 0.5, "max": 1.5}
{"random": "uniform_int", "min": 2, "max": 8}
```

`min`/`max` on `normal` clamp the result. `uniform_int` returns a whole number
(used for `iterations`).

---

## placement_blocks

Constraint-based placement blocks. Each block runs the placement solver against
the target shape. Unlike `conditional_transforms`, placement blocks always execute
(no `chance` parameter). Missing targets are skipped silently.

### Legacy format

Simple iterative constraint loop — used for shape 1 placement (grid, size limit):

```json
"placement_blocks": [
  {
    "target": "compose_shape_1",
    "max_iterations": 20,
    "tolerance_iterations": 3,
    "constraints": [
      {"type": "canvas_size_limit", "max_fraction": 0.25},
      {"type": "grid_placement", "division": 3, "position": "random", "random_mode": "per_iteration"}
    ]
  }
]
```

- `target` — any target spec (name, range, list). Missing names skipped silently.
- `max_iterations` — solver iteration limit. Default 20.
- `tolerance_iterations` — stop if no progress for N iterations. Default 3.
- `constraints` — ordered list evaluated and corrected in sequence.

### New format (pre-placement transforms + tangent placement)

Used for shapes 2+ that need tangent placement against a reference cluster:

```json
"placement_blocks": [
  {
    "target": "compose_shape_2",
    "max_iterations": 10,
    "fit_rules": [
      {"type": "size_ratio", "reference": "compose_shape_1", "max": 0.8}
    ],
    "placement": {
      "type": "tangent",
      "reference": "compose_shape_1",
      "approach": "random",
      "tolerance_px": 3,
      "canvas_bounds_margin_px": 5,
      "overlap_allowed": false
    }
  }
]
```

**Execution sequence:**
1. `fit_rules` — iterative constraint loop on shape in loaded position
2. Pre-size — scale shape to fit within usable canvas area
3. Pre-position — move to approach side of reference (clamped to canvas)
4. Tangent move — close gap to reference hull in one direct move
5. Bounds fit — if hull exceeds canvas: exact resize + re-tangent
6. Overlap check — push off any overlapping shapes (if `overlap_allowed: false`)

**`fit_rules`** (alias: `pre_constraints`) — constraints evaluated before placement.
Typically `size_ratio` and axis constraints.

**`placement.approach`** — direction to approach the reference from:
```json
"approach": "random"
"approach": "SE"
"approach": 135
"approach": {"random": "degrees", "min": 0, "max": 360}
"approach": {"random": "choice", "values": ["N", "S", "E", "W"]}
```

**`placement.reference_group`** — reference the combined hull of multiple shapes:
```json
"reference_group": ["compose_shape_1", "compose_shape_2"]
```

**`placement.overlap_allowed`** — if `false` (default), push shape off any overlapping
shapes after placement. If `true`, overlaps are permitted.

---

## Constraints

Used in `constraints` (legacy) and `fit_rules` (new format) lists.

### size_ratio

Target hull area <= `max` * reference hull area. Correction: scale.

```json
{"type": "size_ratio", "reference": "compose_shape_1", "max": 0.8}
```

### canvas_size_limit

Target hull must not exceed `max_fraction` of canvas in either dimension. Correction: scale.

```json
{"type": "canvas_size_limit", "max_fraction": 0.25}
```

### canvas_bounds

All hull points must lie within canvas bounds. When exceeded, shape is scaled
down around its centroid (preserving contact). Used internally by `placement`
via `canvas_bounds_margin_px` — not typically needed in `constraints` list directly.

```json
{"type": "canvas_bounds", "margin_px": 5}
```

### grid_placement

Target centroid must be within `tolerance_px` of a compositional grid point.
Correction: move to grid point.

```json
{"type": "grid_placement", "division": 3, "position": "top_left",   "tolerance_px": 20}
{"type": "grid_placement", "division": 3, "position": "random",      "random_mode": "per_iteration"}
{"type": "grid_placement", "division": 4, "position": "random",      "random_mode": "per_batch"}
```

**`division`** — integer N creates an NxN grid. 3=thirds (4 intersections),
4=quarters (9 intersections), 5=fifths (16 intersections).

**`position` values:**

| Name | Description |
|---|---|
| `nearest` | Closest intersection to current centroid (default) |
| `center` | Canvas dead-center |
| `top_left` | First row, first column |
| `top_center` | First row, center column |
| `top_right` | First row, last column |
| `center_left` | Middle row, first column |
| `center_right` | Middle row, last column |
| `bottom_left` | Last row, first column |
| `bottom_center` | Last row, center column |
| `bottom_right` | Last row, last column |
| `portrait_top` | 1/3 down, horizontally centered |
| `random` | Randomly chosen intersection — see `random_mode` |

**`random_mode`** (when `position` is `"random"`):

| Mode | Behavior |
|---|---|
| `per_iteration` | New random intersection chosen each batch iteration (default) |
| `per_batch` | Random intersection chosen once before the batch run, same for all iterations |

### axis_align

Target axis aligned with reference axis within `tolerance_deg`. Correction: rotate.

```json
{"type": "axis_align", "reference": "compose_shape_1", "axis": "major", "tolerance_deg": 10}
```

### axis_misalign

Target axis must differ from reference by at least `min_deg`. Correction: rotate.

```json
{"type": "axis_misalign", "reference": "compose_shape_1", "axis": "minor", "min_deg": 15}
```

### axis_collinear

Target axis parallel to and on the same line as reference axis. Two-stage correction:
rotate then move perpendicular.

```json
{"type": "axis_collinear", "reference": "compose_shape_1", "axis": "minor",
 "align_tolerance_deg": 5, "collinear_tolerance_px": 10}
```

### axis_not_collinear

Target axis parallel but offset from reference axis by at least `min_offset_px`.
Correction: move perpendicular to axis.

```json
{"type": "axis_not_collinear", "reference": "compose_shape_1", "axis": "minor", "min_offset_px": 20}
```

### tangent

Target hull within `tolerance_px` of touching reference hull. Correction: move toward
reference. Overlap is detected and corrected (push apart then re-approach).

```json
{
  "type": "tangent",
  "reference": "compose_shape_1",
  "tolerance_px": 3,
  "max_contact_points": 1
}
```

Supports `reference_group` for combined cluster hull:
```json
{
  "type": "tangent",
  "reference_group": ["compose_shape_1", "compose_shape_2"],
  "tolerance_px": 3
}
```

### separation_from_group

Target hull separated from group's combined hull by at least `min_separation_px`.
Optionally must be further than `greater_than` shape.

```json
{
  "type": "separation_from_group",
  "reference_group": ["compose_shape_1", "compose_shape_2"],
  "min_separation_px": 30,
  "greater_than": "compose_shape_4"
}
```

---

## Solver Behavior

**Legacy constraint loop** (`constraints`):
1. Evaluate each constraint in order
2. Apply corrective transform if not satisfied
3. Repeat until all satisfied or `max_iterations` reached
4. Early stop if no progress for `tolerance_iterations` consecutive iterations

**New placement solver** (`fit_rules` + `placement`):
1. Run `fit_rules` constraint loop (shape in loaded position)
2. Pre-size: scale to fit usable canvas area
3. Pre-position: move to approach side (clamped to canvas bounds)
4. Tangent move: single direct move to contact
5. Bounds fit: if out of bounds, resize to fit + re-tangent (no loop)
6. Overlap check: push off all overlapping shapes if `overlap_allowed: false`

All solver activity is logged to the app UI log when `verbose: true`.

---

## Full Example — Multi-shape Composition

```json
"compose_multi": {
  "commands": [
    {
      "template": "compose_1",
      "params": {"color": "black", "width": "2"},
      "compose_parameters": {
        "shapes": {
          "selection": [
            {"method": "specified", "shapes": ["sa224/gen1_0033"]},
            {"method": "wildcard",  "pattern": "sa224/gen4_*",
             "count": {"random": "uniform_int", "min": 2, "max": 4}}
          ]
        },
        "on_load": [
          {"command": "FILL",    "value": "#d0d0d0"},
          {"command": "REFLECT", "axis": "random", "chance": 0.5}
        ],
        "command_loop": {
          "verbose": true,
          "iterations": 1,
          "conditional_transforms": [
            {
              "chance": 1.0,
              "target": {"range": [1, 5]},
              "commands": [
                {"command": "DEFORM", "axis": "major",
                 "along":  {"random": "uniform", "min": 0.8, "max": 1.2},
                 "across": {"random": "uniform", "min": 0.8, "max": 1.2}}
              ]
            }
          ],
          "placement_blocks": [
            {
              "target": "compose_shape_1",
              "constraints": [
                {"type": "canvas_size_limit", "max_fraction": 0.25},
                {"type": "grid_placement", "division": 3,
                 "position": "random", "random_mode": "per_iteration"}
              ]
            },
            {
              "target": {"range": [2, 5]},
              "fit_rules": [
                {"type": "size_ratio", "reference": "compose_shape_1", "max": 0.8}
              ],
              "placement": {
                "type": "tangent",
                "reference_group": ["compose_shape_1"],
                "approach": "random",
                "tolerance_px": 3,
                "canvas_bounds_margin_px": 5,
                "overlap_allowed": false
              }
            }
          ]
        }
      }
    }
  ]
}
```

---

## Planned / Not Yet Implemented

- **axis_near_parallel constraint** — deliberate small axis misalignment
- **separation_from_shape constraint** — controlled distance between two named shapes
- **RL command logging** — full transform log for reinforcement learning analysis
- **Exact tangency** — currently approximate within `tolerance_px`
- **fit_to bounding polygon** in DEFORM
- **Cluster definitions** — named groups of shapes for compositional reference

---

*Updated: June 2026*