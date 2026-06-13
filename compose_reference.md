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
2. **command_loop** — drives transforms, random selection, and constraint-based placement
3. **Placement solver** — applies geometry constraints iteratively until satisfied

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
        "shapes": { ... },
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
  "command_loop": { ... }     // optional transform and placement loop
}
```

---

## Shape Loading — shapes key

### Specified (explicit list)

Load named shapes from the `shapes/` store by exact name.

```json
"shapes": {
  "specified": ["sa224/gen1_0033", "sa224/gen4_0050"]
}
```

Shapes are assigned sequential working names: `compose_shape_1`, `compose_shape_2`, ...

Working names are predictable and can be referenced by name in subsequent
`command_loop` commands and `placement_blocks`.

### Source Shape for DERIVE

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

## Outputs

Each COMPOSE batch iteration produces:

- **PNG** — canvas image saved to `output/<prefix>_<NNNN>.png`
- **Construction JSON** — saved to `shapes/<prefix>_<NNNN>.json`

### Construction JSON format

```json
{
  "composition_id": "compose_test1_0001",
  "executable":     "compose_test1",
  "timestamp":      "2026-06-10T...",
  "shapes_loaded": [
    { "working_name": "compose_shape_1", "source": "sa224/gen1_0033" },
    { "working_name": "compose_shape_2", "source": "sa224/gen4_0050" }
  ],
  "commands_applied": []
}
```

`commands_applied` is reserved for future RL-oriented logging.

### Reloading a Composition

`LOAD <composition_name>` detects the `composition_id` key and reloads
all component shapes under their original working names.

```
LOAD sa224/compose_test1_0001
```

---

## command_loop

Optional loop that runs after shapes are loaded. Drives transforms,
random selection blocks, and constraint-based placement blocks.

```json
"command_loop": {
  "verbose":         true,
  "iterations":      3,
  "commands":        [ ... ],
  "select_blocks":   [ ... ],
  "placement_blocks": [ ... ]
}
```

### verbose

`true` (default) — emit decision trace to the app UI log.  
`false` — silent execution.

### iterations

Number of loop iterations. Accepts a fixed integer or a random spec.

```json
"iterations": 3
"iterations": {"random": "uniform_int", "min": 2, "max": 8}
```

---

## commands (top-level)

Commands applied unconditionally to a target on every iteration.
`target` is required at this level.

```json
"commands": [
  {
    "command": "MOVE",
    "target": "all",
    "delta": [5, 5]
  }
]
```

**target values:**
- `"all"` — every working name in the composition
- `"random"` — one shape chosen at random (with replacement)
- `"compose_shape_N"` — a specific working name

---

## select_blocks

Each block fires independently, controlled by `chance`. Multiple blocks
in the list are each evaluated independently per iteration.

```json
"select_blocks": [
  {
    "chance":  0.7,
    "target":  "random",
    "commands": [
      { "command": "DEFORM", "axis": "major", "along": 0.8, "across": 1.0 },
      { "command": "MOVE",   "direction": "SE", "distance": 40 }
    ]
  }
]
```

- `chance` — float 0.0–1.0. Probability this block fires. Default 1.0.
- `target` — same values as top-level commands. Resolved once per block execution; all commands in the block use the same resolved target.
- `commands` — list of transform commands. `name`/`target` field not required inside a block — the block's resolved target is used.

---

## Supported Transform Commands

All numeric parameters accept fixed values or random specs (see Random Values section).

### MOVE

```json
{ "command": "MOVE", "delta": [dx, dy] }
{ "command": "MOVE", "direction": "SE",  "distance": 40 }
{ "command": "MOVE", "direction": 135,   "distance": {"random": "uniform", "min": 20, "max": 80} }
{ "command": "MOVE", "direction": "random", "distance": 40 }
{ "command": "MOVE", "direction": {"random": "choice",  "values": ["N","SE","W"]}, "distance": 40 }
{ "command": "MOVE", "direction": {"random": "degrees", "min": 0, "max": 360},    "distance": 40 }
```

**Compass directions — 16-point:**  
`N  NNE  NE  ENE  E  ESE  SE  SSE  S  SSW  SW  WSW  W  WNW  NW  NNW`

**Numeric degrees:** 0 = North, 90 = East, 180 = South, 270 = West (clockwise).

**`"random"`** as a direction string — picks any of the 16 compass points.

### DEFORM

Stretch or compress along the shape's computed principal axis.

```json
{
  "command": "DEFORM",
  "axis":   "major",
  "along":  1.25,
  "across": 0.85
}
```

- `axis` — `"major"` (longest) or `"minor"` (shortest). `along` applies to this axis; `across` is perpendicular.
- `along` / `across` — scale factors. 1.0 = no change. > 1.0 stretches, < 1.0 compresses.

### ROTATE

```json
{ "command": "ROTATE", "angle": 45 }
{ "command": "ROTATE", "angle": {"random": "uniform", "min": -45, "max": 45} }
```

- `angle` — degrees, positive = clockwise.

### SCALE

```json
{ "command": "SCALE", "factor": 0.8 }
{ "command": "SCALE", "factor": {"random": "uniform", "min": 0.6, "max": 1.4} }
```

- `factor` — uniform scale. 1.0 = no change, < 1.0 = shrink, > 1.0 = grow.

### COLOR

```json
{ "command": "COLOR", "value": "black" }
```

### WIDTH

```json
{ "command": "WIDTH", "value": 2 }
```

### FILL

```json
{ "command": "FILL", "value": "red" }
```

### ALPHA

```json
{ "command": "ALPHA", "value": 0.7 }
```

### ZORDER

```json
{ "command": "ZORDER", "value": 1 }
```

---

## Random Values

Any numeric parameter in a transform command accepts a random spec in place
of a fixed number.

### uniform

Uniform distribution between min and max.

```json
{"random": "uniform", "min": 0.7, "max": 1.3}
```

### normal

Normal (Gaussian) distribution. `min`/`max` clamp the result.

```json
{"random": "normal", "mean": 1.0, "std": 0.2, "min": 0.5, "max": 1.5}
```

### uniform_int

Uniform integer distribution. Used for `iterations`.

```json
{"random": "uniform_int", "min": 2, "max": 8}
```

---

## placement_blocks

Constraint-based placement. Each block runs the placement solver against
the target shape, applying corrective transforms iteratively until all
constraints are satisfied or `max_iterations` is reached.

Unlike `select_blocks`, placement blocks do not have a `chance` parameter —
they always execute.

```json
"placement_blocks": [
  {
    "target":           "compose_shape_2",
    "max_iterations":   20,
    "constraints": [
      { "type": "size_ratio",       "reference": "compose_shape_1", "max": 0.8 },
      { "type": "axis_align",       "reference": "compose_shape_1", "axis": "major", "tolerance_deg": 10 },
      { "type": "axis_not_collinear","reference": "compose_shape_1", "axis": "minor", "min_offset_px": 20 },
      { "type": "tangent",          "reference": "compose_shape_1", "tolerance_px": 3 }
    ]
  }
]
```

- `target` — working name of the shape to place. Accepts `"random"`.
- `max_iterations` — solver iteration limit. Default 20.
- `tolerance_iterations` — stop early if no progress for N iterations. Default 3.
- `constraints` — ordered list. Evaluated and applied in sequence.

---

## Constraints

Constraints are evaluated in order within a placement block.
Each constraint that is not satisfied applies a corrective transform
(MOVE, ROTATE, or SCALE) and re-evaluates from the next constraint.

All constraints that reference another shape use `"reference"` — a working name.

### size_ratio

Target convex hull area must be no more than `max` times the reference hull area.  
Correction: uniform scale.

```json
{"type": "size_ratio", "reference": "compose_shape_1", "max": 0.8}
```

### canvas_size_limit

Target hull must not exceed `max_fraction` of canvas width or height.  
Correction: uniform scale.

```json
{"type": "canvas_size_limit", "max_fraction": 0.25}
```

`canvas_w` and `canvas_h` default to 768 and are injected automatically.

### grid_placement

Target centroid must be within `tolerance_px` of a compositional grid point.  
Correction: move centroid to the grid point.

```json
{"type": "grid_placement", "division": 3, "position": "top_left", "tolerance_px": 20}
```

**`division`** — integer N creates an NxN grid. 3=thirds, 5=fifths, 7=sevenths.

**`position` values:**

| Name | Description |
|---|---|
| `nearest` | Closest grid intersection to current centroid (default) |
| `center` | Canvas dead-center (always canvas_w/2, canvas_h/2) |
| `top_left` | First row, first column intersection |
| `top_center` | First row, second column (use division >= 3) |
| `top_right` | First row, last column |
| `center_left` | Second row, first column |
| `center_right` | Second row, last column |
| `bottom_left` | Last row, first column |
| `bottom_center` | Last row, second column |
| `bottom_right` | Last row, last column |
| `upper_left` | Alias for top_left |
| `upper_right` | Alias for top_right |
| `lower_left` | Alias for bottom_left |
| `lower_right` | Alias for bottom_right |
| `portrait_top` | 1/3 down, horizontally centered |

### axis_align

Target's named axis must be aligned with the reference's named axis within `tolerance_deg`.  
Correction: rotate.

```json
{"type": "axis_align", "reference": "compose_shape_1", "axis": "major", "tolerance_deg": 10}
```

- `axis` — `"major"` or `"minor"`
- `tolerance_deg` — acceptable angular deviation. Default 10.

### axis_misalign

Target's named axis must differ from reference's axis by at least `min_deg`.  
Guarantees the axes are NOT aligned.  
Correction: rotate to push past minimum threshold.

```json
{"type": "axis_misalign", "reference": "compose_shape_1", "axis": "minor", "min_deg": 15}
```

### axis_collinear

Target's named axis must be both parallel to and on the same line as the reference's axis.  
Two-stage: first aligns (parallel), then translates (collinear).  
Correction: rotate then move perpendicular to axis.

```json
{
  "type": "axis_collinear",
  "reference": "compose_shape_1",
  "axis": "minor",
  "align_tolerance_deg": 5,
  "collinear_tolerance_px": 10
}
```

### axis_not_collinear

Target's named axis must be parallel but offset from reference's axis by at least `min_offset_px`.  
Ensures axes are parallel but NOT on the same line — staggered relationship.  
Correction: move perpendicular to axis direction.

```json
{
  "type": "axis_not_collinear",
  "reference": "compose_shape_1",
  "axis": "minor",
  "min_offset_px": 20
}
```

### axis_near_parallel

*(Planned — not yet implemented)*  
Target axis aligned with reference then deliberately offset by `misalign_deg`.  
Intended for secondary cluster shapes that read as a family but are not exact.

```json
{
  "type": "axis_near_parallel",
  "reference": "compose_shape_4",
  "axis": "major",
  "misalign_deg": {"random": "uniform", "min": 5, "max": 20}
}
```

### tangent

Target hull must be within `tolerance_px` of touching the reference hull
at no more than `max_contact_points` contact segments.  
Near-tangency (approximate). Exact tangency is a future enhancement.  
Correction: move toward reference along the closest-approach vector.

```json
{
  "type": "tangent",
  "reference": "compose_shape_1",
  "tolerance_px": 3,
  "max_contact_points": 1
}
```

### separation_from_group

Target hull must be separated from the collective convex hull of a named group
by at least `min_separation_px`.  
Optionally, target must be further from the group than a reference shape (`greater_than`).

```json
{
  "type": "separation_from_group",
  "reference_group": ["compose_shape_1", "compose_shape_2", "compose_shape_3"],
  "min_separation_px": 30,
  "greater_than": "compose_shape_4"
}
```

---

## Solver Behavior

The placement solver works through constraints in order within each iteration:

1. Evaluate constraint against current shape geometry
2. If not satisfied, apply the corrective transform immediately
3. Refresh shape geometry
4. Continue to next constraint
5. Repeat until all satisfied or `max_iterations` reached

Early stopping: if no corrections are applied for `tolerance_iterations`
consecutive iterations, the solver stops.

Corrections applied:
- `move` — `MOVE shape_name dx,dy`
- `rotate` — `ROTATE shape_name angle`
- `scale` — `SCALE shape_name factor`

All solver activity is logged to the app UI log when `verbose: true`.

---

## Scenario 1 — Two Shapes in Adjacency

Full executable example implementing the two-shape adjacency scenario.

```json
"compose_scenario1": {
  "commands": [
    {
      "template": "compose_1",
      "params": { "color": "black", "width": "2" },
      "compose_parameters": {
        "shapes": {
          "specified": ["sa224/gen1_0033", "sa224/gen4_0050"]
        },
        "command_loop": {
          "verbose": true,
          "iterations": 1,
          "commands": [],
          "select_blocks": [
            {
              "chance": 1.0,
              "target": "compose_shape_1",
              "commands": [
                { "command": "DEFORM", "axis": "major",
                  "along": {"random": "uniform", "min": 0.8, "max": 1.2},
                  "across": {"random": "uniform", "min": 0.8, "max": 1.2} }
              ]
            },
            {
              "chance": 1.0,
              "target": "compose_shape_2",
              "commands": [
                { "command": "DEFORM", "axis": "major",
                  "along": {"random": "uniform", "min": 0.7, "max": 1.1},
                  "across": {"random": "uniform", "min": 0.7, "max": 1.1} }
              ]
            }
          ],
          "placement_blocks": [
            {
              "target": "compose_shape_1",
              "max_iterations": 20,
              "constraints": [
                { "type": "canvas_size_limit", "max_fraction": 0.25 },
                { "type": "grid_placement", "division": 3, "position": "top_left" }
              ]
            },
            {
              "target": "compose_shape_2",
              "max_iterations": 30,
              "constraints": [
                { "type": "size_ratio",        "reference": "compose_shape_1", "max": 0.8 },
                { "type": "axis_align",        "reference": "compose_shape_1", "axis": "major", "tolerance_deg": 10 },
                { "type": "axis_not_collinear","reference": "compose_shape_1", "axis": "minor", "min_offset_px": 20 },
                { "type": "tangent",           "reference": "compose_shape_1", "tolerance_px": 3 }
              ]
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

- **Wildcard shape selection** — `"wildcard": {"pattern": "sa224/gen1_*", "count": 2}`
- **axis_near_parallel constraint** — deliberate small misalignment
- **separation_from_shape constraint** — controlled distance between two named shapes
- **commands_applied logging** — full transform log in construction JSON for RL
- **COMPOSE load with command replay** — replay `commands_applied` on reload
- **Exact tangency** — currently approximate within `tolerance_px`
- **fit_to bounding polygon** in DEFORM

---

*Updated: June 2026*