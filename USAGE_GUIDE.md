# Phase 1 JSON Support - Usage Guide

## Installation

1. Apply parser modifications from `parser_modifications.py`
2. Apply executor modifications from `executor_modifications.py`
3. Copy example JSON files to your `scripts/` directory
4. Test with examples below

## File Structure

### Single Section JSON
```json
{
  "section_name": {
    "description": "What this does",
    "author": "Your name",
    "created": "2026-01-05",
    "comments": "Notes about this section",
    "commands": [
      "COMMAND1 params",
      "COMMAND2 params"
    ]
  }
}
```

### Multi-Section JSON
```json
{
  "section1": {
    "description": "...",
    "commands": [...]
  },
  "section2": {
    "description": "...",
    "commands": [...]
  }
}
```

## Metadata Fields (Optional)

All metadata fields are optional. Use what makes sense for your workflow:

- `description` - Brief description of what this section does
- `author` - Who created this section
- `created` - When created (freeform date string)
- `modified` - When last modified
- `target_canvas` - WIP or MAIN (documentation only, not enforced)
- `comments` - Longer notes, observations, reminders

You can add custom fields too - they'll be stored but ignored by the executor.

## RUN Command

### Text Files (Unchanged)
```bash
RUN script.txt
```

### JSON Files - Single Section
```bash
# Auto-runs if only one section in file
RUN example_single_section.json

# Output:
# Running section 'quick_test' from example_single_section.json
# Description: Quick test with a simple 5-vertex polygon
#
# [1] CLEAR WIP ALL → WIP canvas cleared
# [2] PROC dynamic_polygon test ... → Created Polygon 'test'...
# [3] COLOR test blue → Set color of 'test' to blue
# [4] WIDTH test 3 → Set width of 'test' to 3
```

### JSON Files - Multiple Sections (Explicit Selection Required)
```bash
# ERROR - must specify which section
RUN example_multi_section.json

# Output:
# Error: Multiple sections found. Specify which to run.
#    Available sections:
#      - organic_template
#      - test_small
#      - organic_inward
#      - organic_outward
#      - complex_layered
#      - batch_random_template
#    Usage: RUN example_multi_section.json <section_name>

# CORRECT - specify section name
RUN example_multi_section.json test_small

# Output:
# Running section 'test_small' from example_multi_section.json
# Description: Small canvas test - good for quick iterations
#
# [1] CLEAR WIP ALL → WIP canvas cleared
# [2] PROC dynamic_polygon test ... → Created Polygon 'test'...
# [3] COLOR test red → Set color of 'test' to red
# [4] WIDTH test 2 → Set width of 'test' to 2
```

### Section Not Found
```bash
RUN example_multi_section.json typo

# Output:
# Error: Section 'typo' not found in example_multi_section.json
#    Available sections:
#      - organic_template
#      - test_small
#      - organic_inward
#      - organic_outward
#      - complex_layered
#      - batch_random_template
```

## BATCH Command

### Text Files (Unchanged)
```bash
BATCH 10 script.txt output
```

### JSON Files - Section Required
```bash
# ERROR - section name required
BATCH 10 example_multi_section.json dataset

# Output:
# Error: Section name required for BATCH

# CORRECT - specify section between filename and output prefix
BATCH 10 example_multi_section.json batch_random_template dataset

# Output:
# Running section 'batch_random_template' from example_multi_section.json (10 iterations)
# Description: Template for batch generation with randomization
#
# [1/10] Generated dataset_001.png
# [2/10] Generated dataset_002.png
# [3/10] Generated dataset_003.png
# ...
# [10/10] Generated dataset_010.png
#
# BATCH complete: 10/10 successful
```

### BATCH with Target Canvas
```bash
# Default is MAIN canvas
BATCH 10 example_multi_section.json batch_random_template dataset

# Explicit WIP canvas
BATCH 10 example_multi_section.json batch_random_template dataset WIP

# Explicit MAIN canvas
BATCH 10 example_multi_section.json batch_random_template dataset MAIN
```

## Command Syntax Summary

```
RUN <file.txt>                              # Text file (existing)
RUN <file.json>                             # JSON, auto-run if 1 section
RUN <file.json> <section>                   # JSON, run specific section

BATCH <n> <file.txt> <prefix> [WIP|MAIN]   # Text file (existing)
BATCH <n> <file.json> <section> <prefix> [WIP|MAIN]   # JSON, section required
```

## Workflow Examples

### Example 1: Quick Testing
```bash
# Create test.json with one section
RUN test.json

# Modify parameters in test.json
RUN test.json

# Iterate until satisfied
```

### Example 2: Trying Variations
```bash
# Create variations.json with multiple sections:
# - test_v1
# - test_v2
# - test_v3

RUN variations.json test_v1    # Try first
RUN variations.json test_v2    # Try second
RUN variations.json test_v3    # Try third
```

### Example 3: Dataset Generation
```bash
# Create dataset.json with randomized section
BATCH 100 dataset.json random_organic dataset_organic
BATCH 100 dataset.json random_geometric dataset_geometric

# Creates:
# output/dataset_organic_001.png through _100.png
# output/dataset_geometric_001.png through _100.png
```

### Example 4: Using Templates
```bash
# In library.json:
# - organic_template (reference only)
# - my_variation_1 (copied from template, modified)
# - my_variation_2 (copied from template, modified)

# Don't run template directly (by convention)
# Run your variations instead:
RUN library.json my_variation_1
RUN library.json my_variation_2
```

## Section Organization Strategies

### By Purpose
```json
{
  "quick_test": {...},
  "debug_vertices": {...},
  "final_version": {...}
}
```

### By Parameters
```json
{
  "template": {...},
  "vertices_5": {...},
  "vertices_8": {...},
  "vertices_12": {...}
}
```

### By Style
```json
{
  "organic_soft": {...},
  "organic_sharp": {...},
  "geometric_clean": {...}
}
```

### By Layer
```json
{
  "background_layer": {...},
  "midground_layer": {...},
  "foreground_layer": {...}
}
```

## Error Handling

### JSON Syntax Error
```bash
RUN bad_syntax.json

# Output:
# Error: Invalid JSON in bad_syntax.json: Expecting ',' delimiter: line 5 column 3
```

### Missing Commands Array
```bash
# Section without "commands" key
# Error: Section 'test' missing required 'commands' array
```

### Empty Commands Array
```bash
# Section with "commands": []
# Error: Section 'test' has empty commands array
```

### Non-String Command (Phase 1)
```bash
# Section with {"command": "PROC", ...} instead of string
# Error: Section 'test' - command 1 must be a string (got dict)
# Note: Structured commands come in Phase 2
```

## Tips for Hand-Editing

1. **Start Simple**: Begin with single section files
2. **Copy & Modify**: Duplicate working sections, rename, adjust
3. **Use Comments Field**: Track what you're testing
4. **Descriptive Names**: Use clear section names like "test_inward_bias"
5. **Template Convention**: Put "template" in name for reference-only sections
6. **Version Control**: Use "created" and "modified" dates
7. **Test Incrementally**: Test after each section addition

## Converting Text Scripts to JSON

### Before (text file: organic.txt)
```
CLEAR WIP ALL
PROC dynamic_polygon shape1 VERTICES=6 BOUNDS=100,100,600,600
COLOR shape1 green
```

### After (JSON file: organic.json)
```json
{
  "organic_basic": {
    "description": "Basic organic polygon",
    "commands": [
      "CLEAR WIP ALL",
      "PROC dynamic_polygon shape1 VERTICES=6 BOUNDS=100,100,600,600",
      "COLOR shape1 green"
    ]
  }
}
```

### Benefits of JSON
- Add multiple related variations in one file
- Document what each section does
- Organize by naming sections clearly
- Track authorship and dates
- Add notes without comment syntax

## Common Patterns

### Pattern 1: Progressive Refinement
```json
{
  "v1_initial": {
    "comments": "First attempt, too simple",
    "commands": [...]
  },
  "v2_more_complex": {
    "comments": "Added more iterations, better",
    "commands": [...]
  },
  "v3_final": {
    "comments": "This is the one!",
    "commands": [...]
  }
}
```

### Pattern 2: Parameter Exploration
```json
{
  "depth_low": {
    "comments": "Depth range 0.2-0.4",
    "commands": ["PROC ... DEPTH_RANGE=0.2,0.4"]
  },
  "depth_medium": {
    "comments": "Depth range 0.4-0.6",
    "commands": ["PROC ... DEPTH_RANGE=0.4,0.6"]
  },
  "depth_high": {
    "comments": "Depth range 0.6-0.8",
    "commands": ["PROC ... DEPTH_RANGE=0.6,0.8"]
  }
}
```

### Pattern 3: Color Variations
```json
{
  "base_template": {
    "comments": "Base geometry - copy and change colors",
    "commands": ["PROC dynamic_polygon shape1 ..."]
  },
  "green_variant": {
    "commands": [
      "CLEAR WIP ALL",
      "PROC dynamic_polygon shape1 ...",
      "COLOR shape1 green",
      "FILL shape1 lightgreen"
    ]
  },
  "blue_variant": {
    "commands": [
      "CLEAR WIP ALL",
      "PROC dynamic_polygon shape1 ...",
      "COLOR shape1 blue",
      "FILL shape1 lightblue"
    ]
  }
}
```

## Next Steps (Phase 2 Preview)

Phase 2 will add:
- Structured command format (dictionaries instead of strings)
- Mixed string/structured commands in same section
- RAND() evaluation in structured format
- Enhanced validation

Phase 1 JSON structure is forward-compatible with Phase 2.
