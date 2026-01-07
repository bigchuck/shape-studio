# Phase 2 JSON Support - Usage Guide

## What's New in Phase 2

Phase 2 adds **structured command format** while maintaining full Phase 1 compatibility.

### Key Features
- ✅ Dictionary-based commands (match parser output)
- ✅ Flexible parameter types (arrays, numbers auto-convert)
- ✅ Mixed string/structured commands in same section
- ✅ RAND() works in structured format
- ✅ Underscore fields for inline comments
- ✅ Case-insensitive command names
- ✅ All commands support structured format

---

## Structured Command Format

### Basic Structure
```json
{
  "command": "COMMAND_NAME",
  "param1": "value1",
  "param2": "value2"
}
```

### PROC Command (Most Common Use Case)
```json
{
  "command": "PROC",
  "method": "dynamic_polygon",
  "name": "shape1",
  "params": {
    "VERTICES": "6,10",
    "BOUNDS": "100,100,600,600",
    "ITERATIONS": "20",
    "OPERATIONS": "sawtooth,split_offset"
  }
}
```

### POLY Command
```json
{
  "command": "POLY",
  "name": "square1",
  "points": [
    [100, 100],
    [300, 100],
    [300, 300],
    [100, 300]
  ]
}
```

### LINE Command
```json
{
  "command": "LINE",
  "name": "line1",
  "start": [100, 100],
  "end": [600, 600]
}
```

### Style Commands
```json
{
  "command": "COLOR",
  "name": "shape1",
  "color": "#3498db"
}
```

```json
{
  "command": "FILL",
  "name": "shape1",
  "fill": "#85c1e9"
}
```

```json
{
  "command": "WIDTH",
  "name": "shape1",
  "width": 3
}
```

---

## Flexible Parameter Types

Phase 2 auto-converts parameter types to strings:

### Arrays → Comma-Separated Strings
```json
{
  "VERTICES": [6, 10],        // Becomes "6,10"
  "BOUNDS": [100, 100, 600, 600],  // Becomes "100,100,600,600"
  "DEPTH_RANGE": [0.3, 0.8]   // Becomes "0.3,0.8"
}
```

### Numbers → Strings
```json
{
  "ITERATIONS": 20,           // Becomes "20"
  "WIDTH": 3,                 // Becomes "3"
  "ALPHA": 0.5                // Becomes "0.5"
}
```

### Booleans → Strings
```json
{
  "SAVE_ITERATIONS": true     // Becomes "true"
}
```

**Why?** More intuitive for hand-editing. Write arrays/numbers naturally, they convert automatically.

---

## RAND() in Structured Format

RAND() works in any string value:

```json
{
  "command": "PROC",
  "method": "dynamic_polygon",
  "name": "shape1",
  "params": {
    "VERTICES": "RAND(5,10)",
    "ITERATIONS": "RAND(15,25)",
    "DEPTH_RANGE": "RAND(0.2,0.5),RAND(0.6,0.9)"
  }
}
```

**Note:** RAND() must be in strings, not bare:
- ✅ `"VERTICES": "RAND(5,10)"`
- ❌ `"VERTICES": RAND(5,10)` (invalid JSON)

---

## Underscore Comments

Any field starting with `_` is ignored:

```json
{
  "_comment": "This creates the background layer",
  "_author": "Mr. Chuck",
  "_tested": "2026-01-06",
  "command": "PROC",
  "method": "dynamic_polygon",
  "name": "background",
  "params": {
    "_note": "These params work well for backgrounds",
    "VERTICES": [10, 14],
    "ITERATIONS": 30
  }
}
```

Use any underscore field name: `_comment`, `_note`, `_TODO`, `_author`, etc.

---

## Mixed Format Strategy

**Recommended approach:** Use what makes sense for each command.

### Use Structured For:
- PROC commands (many parameters, benefits from clarity)
- Complex POLY/LINE (many points, array format clearer)
- When parameters need documentation

### Use Strings For:
- Simple commands (COLOR, CLEAR, PROMOTE)
- Quick one-liners
- When brevity matters

### Example: Balanced Mix
```json
{
  "commands": [
    "CLEAR WIP ALL",
    {
      "_comment": "Complex PROC benefits from structure",
      "command": "PROC",
      "method": "dynamic_polygon",
      "name": "shape1",
      "params": {
        "VERTICES": [6, 10],
        "BOUNDS": [100, 100, 600, 600],
        "ITERATIONS": 20,
        "OPERATIONS": "sawtooth,split_offset"
      }
    },
    "COLOR shape1 blue",
    "FILL shape1 lightblue",
    "PROMOTE shape1"
  ]
}
```

---

## Command Reference

### All Commands Support Structured Format

**Shape Creation:**
- `LINE` - name, start, end
- `POLY` - name, points
- `PROC` - method, name, params

**Transforms:**
- `MOVE` - name, delta
- `ROTATE` - name, angle
- `SCALE` - name, factor
- `RESIZE` - name, x_factor, y_factor

**Styling:**
- `COLOR` - name, color
- `FILL` - name, fill
- `WIDTH` - name, width
- `ALPHA` - name, alpha
- `ZORDER` - name, z_coord

**Groups:**
- `GROUP` - name, members
- `UNGROUP` - name
- `EXTRACT` - member, group

**Canvas:**
- `SWITCH` - target
- `PROMOTE` - name, mode
- `UNPROMOTE` - name, mode
- `CLEAR` - target, all

**Storage:**
- `STASH` - name
- `UNSTASH` - name, mode
- `STORE` - name, scope
- `LOAD` - name

**Other:**
- `DELETE` - name, confirm
- `INFO` - name
- `SAVE` - filename

---

## Real-World Examples

### Dataset Generation
```json
{
  "batch_organic": {
    "description": "Generate varied organic shapes",
    "target_canvas": "MAIN",
    "commands": [
      "CLEAR MAIN ALL",
      {
        "command": "PROC",
        "method": "dynamic_polygon",
        "name": "dataset_shape",
        "params": {
          "VERTICES": "RAND(5,12)",
          "BOUNDS": [100, 100, 600, 600],
          "ITERATIONS": "RAND(15,30)",
          "OPERATIONS": "sawtooth,split_offset",
          "DEPTH_RANGE": "RAND(0.2,0.5),RAND(0.6,0.9)",
          "REMOVE_PROB": "RAND(0.0,0.2)"
        }
      },
      "PROMOTE dataset_shape"
    ]
  }
}
```

**Usage:**
```bash
BATCH 100 datasets.json batch_organic organic_dataset
```

### Parameter Exploration
```json
{
  "explore_depth_low": {
    "description": "Low depth range exploration",
    "commands": [
      "CLEAR WIP ALL",
      {
        "command": "PROC",
        "method": "dynamic_polygon",
        "name": "test",
        "params": {
          "VERTICES": 7,
          "BOUNDS": [100, 100, 600, 600],
          "ITERATIONS": 20,
          "OPERATIONS": "sawtooth",
          "DEPTH_RANGE": [0.1, 0.3]
        }
      },
      "COLOR test #3498db"
    ]
  },
  "explore_depth_high": {
    "description": "High depth range exploration",
    "commands": [
      "CLEAR WIP ALL",
      {
        "command": "PROC",
        "method": "dynamic_polygon",
        "name": "test",
        "params": {
          "VERTICES": 7,
          "BOUNDS": [100, 100, 600, 600],
          "ITERATIONS": 20,
          "OPERATIONS": "sawtooth",
          "DEPTH_RANGE": [0.7, 0.9]
        }
      },
      "COLOR test #e74c3c"
    ]
  }
}
```

### Complex Composition
```json
{
  "layered": {
    "description": "Multi-layer composition",
    "commands": [
      "CLEAR WIP ALL",
      {
        "_comment": "Background layer",
        "command": "PROC",
        "method": "dynamic_polygon",
        "name": "bg",
        "params": {
          "VERTICES": [12, 16],
          "BOUNDS": [0, 0, 768, 768],
          "ITERATIONS": 40
        }
      },
      "COLOR bg gray",
      "FILL bg lightgray",
      "ZORDER bg -10",
      {
        "_comment": "Foreground layer",
        "command": "PROC",
        "method": "dynamic_polygon",
        "name": "fg",
        "params": {
          "VERTICES": [5, 7],
          "BOUNDS": [200, 200, 550, 550],
          "ITERATIONS": 15
        }
      },
      "COLOR fg red",
      "FILL fg pink",
      "ZORDER fg 10"
    ]
  }
}
```

---

## Case Sensitivity

Command names are case-insensitive:

```json
{"command": "PROC", ...}    // OK
{"command": "proc", ...}    // OK
{"command": "Proc", ...}    // OK
```

All convert to uppercase internally.

---

## Validation

### What Gets Validated:
- JSON syntax (must be valid JSON)
- Section structure (must have "commands" array)
- Command structure (dict must have "command" field)
- Underscore-only commands rejected (all fields ignored)

### What Doesn't Get Validated:
- Parameter values (executor handles errors)
- Command-specific requirements (executor handles)
- Parameter types (flexible conversion)

This allows executor to provide better error messages for command-specific issues.

---

## Backward Compatibility

Phase 1 JSON files work unchanged:

```json
{
  "phase1_style": {
    "description": "All strings - works in Phase 2",
    "commands": [
      "CLEAR WIP ALL",
      "PROC dynamic_polygon test VERTICES=5 BOUNDS=100,100,300,300",
      "COLOR test blue"
    ]
  }
}
```

---

## Best Practices

### 1. Use Structure for Clarity
When commands have many parameters, structured format is clearer:
```json
{
  "command": "PROC",
  "params": {
    "VERTICES": [6, 10],
    "BOUNDS": [100, 100, 600, 600],
    "ITERATIONS": 20,
    "OPERATIONS": "sawtooth,split_offset",
    "DIRECTION_BIAS": "inward",
    "DEPTH_RANGE": [0.3, 0.8]
  }
}
```

vs:
```
PROC dynamic_polygon shape1 VERTICES=6,10 BOUNDS=100,100,600,600 ITERATIONS=20 OPERATIONS=sawtooth,split_offset DIRECTION_BIAS=inward DEPTH_RANGE=0.3,0.8
```

### 2. Use Strings for Simplicity
Simple commands are clearer as strings:
```json
"COLOR shape1 blue"
```

vs:
```json
{"command": "COLOR", "name": "shape1", "color": "blue"}
```

### 3. Add Comments Where Helpful
```json
{
  "_comment": "This creates the main feature",
  "command": "PROC",
  ...
}
```

### 4. Use Arrays for Coordinates
More readable than comma-separated strings:
```json
"points": [[100, 100], [200, 100], [200, 200]]
```

vs:
```json
"points": "100,100 200,100 200,200"
```

### 5. Group Related Parameters
Use nested dicts for clarity:
```json
{
  "command": "PROC",
  "method": "dynamic_polygon",
  "name": "shape1",
  "params": {
    // All PROC params grouped here
    "VERTICES": [6, 10],
    "BOUNDS": [100, 100, 600, 600]
  }
}
```

---

## Troubleshooting

### Error: "Command must be string or dict"
**Cause:** Command is wrong type (number, array, etc.)
**Fix:** Ensure each command is either a string or dictionary

### Error: "Command missing 'command' field"
**Cause:** Structured command doesn't have "command" key
**Fix:** Add `"command": "COMMAND_NAME"` to the dict

### Error: "All fields ignored"
**Cause:** All fields start with underscore
**Fix:** At least one non-underscore field required

### RAND() Not Working
**Cause:** RAND() not in quotes
**Fix:** `"VERTICES": "RAND(5,10)"` not `RAND(5,10)`

### Array Not Converting
**Cause:** Should work automatically
**Fix:** Check for typos, ensure valid JSON array syntax

---

## Migration from Phase 1

Convert gradually - both formats work:

**Phase 1:**
```json
{
  "test": {
    "commands": [
      "PROC dynamic_polygon shape1 VERTICES=5 BOUNDS=100,100,300,300"
    ]
  }
}
```

**Phase 2 (Structured):**
```json
{
  "test": {
    "commands": [
      {
        "command": "PROC",
        "method": "dynamic_polygon",
        "name": "shape1",
        "params": {
          "VERTICES": 5,
          "BOUNDS": [100, 100, 300, 300]
        }
      }
    ]
  }
}
```

**Phase 2 (Mixed):**
```json
{
  "test": {
    "commands": [
      "CLEAR WIP ALL",
      {
        "command": "PROC",
        "method": "dynamic_polygon",
        "name": "shape1",
        "params": {"VERTICES": 5, "BOUNDS": [100, 100, 300, 300]}
      },
      "COLOR shape1 blue"
    ]
  }
}
```

---

## Summary

**Phase 2 Adds:**
- Structured command format (dicts)
- Flexible parameter types (auto-convert)
- Inline comments (_fields)
- Mixed format support

**Maintains:**
- Phase 1 string commands
- All existing functionality
- Same command execution
- Same RUN/BATCH syntax

**Use When:**
- PROC has many parameters
- Coordinates benefit from array format
- Commands need inline documentation
- Programmatic generation of JSON

**Stick With Strings When:**
- Commands are simple
- Quick hand-editing
- Brevity matters
