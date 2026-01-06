# Phase 1 JSON Support - Installation & Testing Guide

## Installation Steps

### Step 1: Backup Current Files
```bash
cp src/commands/parser.py src/commands/parser.py.backup
cp src/commands/executor.py src/commands/executor.py.backup
```

### Step 2: Apply Parser Changes

Open `src/commands/parser.py` and apply changes from `parser_modifications.py`:

1. **Find** the `_parse_run` method
2. **Replace** it with the new version from parser_modifications.py
3. **Find** the `_parse_batch` method  
4. **Replace** it with the new version from parser_modifications.py

**Changes summary:**
- `_parse_run`: Now accepts optional section_name parameter
- `_parse_batch`: Now detects .json files and handles section_name parameter

### Step 3: Apply Executor Changes

Open `src/commands/executor.py` and apply changes from `executor_modifications.py`:

1. **Add imports** at the top (if not already present):
   ```python
   import json
   import random
   from pathlib import Path
   ```

2. **Find** the existing `_execute_run` method
3. **Rename** it to `_execute_run_text` (keep all existing code)
4. **Add** new `_execute_run` method (routes to JSON or text)
5. **Find** the existing `_execute_batch` method
6. **Add** JSON detection at the start (see executor_modifications.py)
7. **Add** all 6 new methods:
   - `_execute_run_json`
   - `_execute_batch_json`
   - `_load_json_file`
   - `_select_section`
   - `_validate_section`

**Changes summary:**
- Split text execution into separate method
- Add JSON routing logic
- Add 6 new helper methods for JSON handling

### Step 4: Copy Example Files

Copy example JSON files to your scripts directory:
```bash
cp example_single_section.json scripts/
cp example_multi_section.json scripts/
cp procedural_library.json scripts/
```

### Step 5: Verify Installation

Check that files are in place:
```bash
ls scripts/*.json
# Should show:
# scripts/example_single_section.json
# scripts/example_multi_section.json
# scripts/procedural_library.json
```

## Testing Checklist

### Test 1: Single Section JSON (Auto-Run)
```bash
# Command
RUN example_single_section.json

# Expected Output
Running section 'quick_test' from example_single_section.json
Description: Quick test with a simple 5-vertex polygon

  [1] CLEAR WIP ALL → WIP canvas cleared
  [2] PROC dynamic_polygon test VERTICES=5 BOUNDS=100,100,300,300 ITERATIONS=10 → Created Polygon 'test'...
  [3] COLOR test blue → Set color of 'test' to blue
  [4] WIDTH test 3 → Set width of 'test' to 3

# Verify
- WIP canvas should show a blue 5-vertex polygon
- Polygon should have width 3
```
**Status:** [ ] Pass [ ] Fail

### Test 2: Multi-Section JSON (Error Without Section)
```bash
# Command
RUN example_multi_section.json

# Expected Output
Error: Multiple sections found. Specify which to run.
   Available sections:
     - organic_template
     - test_small
     - organic_inward
     - organic_outward
     - complex_layered
     - batch_random_template
   Usage: RUN example_multi_section.json <section_name>
```
**Status:** [ ] Pass [ ] Fail

### Test 3: Multi-Section JSON (Explicit Section)
```bash
# Command
RUN example_multi_section.json test_small

# Expected Output
Running section 'test_small' from example_multi_section.json
Description: Small canvas test - good for quick iterations

  [1] CLEAR WIP ALL → WIP canvas cleared
  [2] PROC dynamic_polygon test VERTICES=5 BOUNDS=150,150,350,350 ITERATIONS=8... → Created Polygon 'test'...
  [3] COLOR test red → Set color of 'test' to red
  [4] WIDTH test 2 → Set width of 'test' to 2

# Verify
- WIP canvas should show a red polygon
- Polygon should be in smaller bounds (150-350)
```
**Status:** [ ] Pass [ ] Fail

### Test 4: Section Not Found Error
```bash
# Command
RUN example_multi_section.json nonexistent

# Expected Output
Error: Section 'nonexistent' not found in example_multi_section.json
   Available sections:
     - organic_template
     - test_small
     - organic_inward
     - organic_outward
     - complex_layered
     - batch_random_template
```
**Status:** [ ] Pass [ ] Fail

### Test 5: Different Sections
```bash
# Command 1
RUN example_multi_section.json organic_inward

# Verify: Green shape with inward bias

# Command 2
RUN example_multi_section.json organic_outward

# Verify: Brown shape with outward bias (more spiky)

# Command 3
RUN example_multi_section.json complex_layered

# Verify: Two shapes visible (background gray, foreground red)
```
**Status:** [ ] Pass [ ] Fail

### Test 6: BATCH with JSON (Error Without Section)
```bash
# Command
BATCH 5 example_multi_section.json output

# Expected Output
Error: Section name required for BATCH
```
**Status:** [ ] Pass [ ] Fail

### Test 7: BATCH with JSON (With Section)
```bash
# Command
BATCH 5 example_multi_section.json batch_random_template batch_test

# Expected Output
Running section 'batch_random_template' from example_multi_section.json (5 iterations)
Description: Template for batch generation with randomization

  [1/5] Generated batch_test_001.png
  [2/5] Generated batch_test_002.png
  [3/5] Generated batch_test_003.png
  [4/5] Generated batch_test_004.png
  [5/5] Generated batch_test_005.png

BATCH complete: 5/5 successful

# Verify
- output/ directory should contain 5 PNG files
- Each should show different polygon (due to RAND())
- Files named batch_test_001.png through batch_test_005.png
```
**Status:** [ ] Pass [ ] Fail

### Test 8: Text Files Still Work
```bash
# Create a simple text file
echo "CLEAR WIP ALL" > scripts/test.txt
echo "POLY test1 100,100 200,100 200,200 100,200" >> scripts/test.txt
echo "COLOR test1 green" >> scripts/test.txt

# Command
RUN test.txt

# Expected Output
Executed 3 commands from 'test.txt':
  [1] CLEAR WIP ALL → WIP canvas cleared
  [2] POLY test1... → Created polygon 'test1'...
  [3] COLOR test1 green → Set color of 'test1' to green

# Verify
- Text files still work unchanged
- Green square visible on WIP canvas
```
**Status:** [ ] Pass [ ] Fail

### Test 9: Metadata Display
```bash
# Command
RUN procedural_library.json explore_sawtooth_inward

# Verify Output Shows Metadata
Running section 'explore_sawtooth_inward' from procedural_library.json
Description: Sawtooth operation with inward bias - creates compact spiky forms

# Verify
- Description is displayed
- Commands execute correctly
```
**Status:** [ ] Pass [ ] Fail

### Test 10: Advanced Features
```bash
# Test with iterations
RUN procedural_library.json with_removal_probability

# Verify: Shape created with some vertices possibly removed

# Test with distortion  
RUN procedural_library.json with_distortion

# Verify: Shape shows distorted original vertices

# Test with animation
RUN procedural_library.json animation_preview_test

# Verify: Multiple iteration snapshots created (anim_test_iter_0, etc.)
```
**Status:** [ ] Pass [ ] Fail

## Validation Tests

### Test 11: Invalid JSON Syntax
```bash
# Create invalid JSON
echo '{' > scripts/bad.json
echo '  "test": {' >> scripts/bad.json
echo '    "commands": ["CLEAR WIP ALL"]' >> scripts/bad.json
echo '  }' >> scripts/bad.json
# Missing closing brace

# Command
RUN bad.json

# Expected Output
Error: Invalid JSON in bad.json: Unexpected end of JSON input
```
**Status:** [ ] Pass [ ] Fail

### Test 12: Missing Commands Array
```bash
# Create JSON without commands
cat > scripts/no_commands.json << 'EOF'
{
  "test": {
    "description": "Missing commands array"
  }
}
EOF

# Command
RUN no_commands.json

# Expected Output
Error: Section 'test' missing required 'commands' array
```
**Status:** [ ] Pass [ ] Fail

### Test 13: Empty Commands Array
```bash
# Create JSON with empty array
cat > scripts/empty_commands.json << 'EOF'
{
  "test": {
    "commands": []
  }
}
EOF

# Command
RUN empty_commands.json

# Expected Output
Error: Section 'test' has empty commands array
```
**Status:** [ ] Pass [ ] Fail

### Test 14: Non-String Command (Phase 1)
```bash
# Create JSON with structured command (not allowed in Phase 1)
cat > scripts/structured.json << 'EOF'
{
  "test": {
    "commands": [
      {
        "command": "CLEAR",
        "target": "WIP"
      }
    ]
  }
}
EOF

# Command
RUN structured.json

# Expected Output
Error: Section 'test' - command 1 must be a string (got dict)
```
**Status:** [ ] Pass [ ] Fail

## Performance Tests

### Test 15: Large Batch Generation
```bash
# Command (this may take a few minutes)
BATCH 50 procedural_library.json batch_dataset_generation dataset

# Verify
- 50 PNG files created
- Each has different parameters (random)
- All files are valid 768x768 PNG images
```
**Status:** [ ] Pass [ ] Fail

### Test 16: Complex Composition
```bash
# Command
RUN procedural_library.json composition_layered

# Verify
- Three shapes visible
- Background is light gray (behind)
- Midground is blue (middle)
- Foreground is red (front)
- Proper z-ordering visible
```
**Status:** [ ] Pass [ ] Fail

## Troubleshooting

### Problem: "File not found" error
**Solution:** Check that JSON file is in scripts/ directory
```bash
ls scripts/*.json
```

### Problem: "Invalid JSON" error
**Solution:** Validate JSON syntax
- Use online JSON validator
- Check for missing commas, brackets, quotes
- Common errors: trailing commas, missing closing braces

### Problem: "Section not found" error
**Solution:** List available sections
- The error message shows all available sections
- Check spelling (case sensitive)
- Ensure section name matches exactly

### Problem: Commands execute but produce unexpected results
**Solution:** Check command syntax
- Each command in "commands" array is a string
- Strings use same syntax as .txt files
- RAND() functions work in JSON commands

### Problem: BATCH creates same image repeatedly
**Solution:** Verify RAND() usage
- RAND() must be in command strings
- Check example: `"VERTICES": "RAND(5,8)"`
- Not: `"VERTICES": 5` (static value)

### Problem: Metadata not displayed
**Solution:** Check RUN output
- Description shows after "Running section..." line
- Other metadata stored but not displayed in Phase 1
- Use INFO command in future phases

## Success Criteria

All tests passing means Phase 1 is successfully installed:

- [ ] Single section auto-run works
- [ ] Multi-section requires explicit selection
- [ ] Section-not-found errors are helpful
- [ ] BATCH requires section for JSON
- [ ] Text files still work unchanged
- [ ] Metadata displays correctly
- [ ] Validation catches errors
- [ ] RAND() works in JSON commands
- [ ] Complex compositions work
- [ ] Large batch generation works

## Next Steps After Testing

1. **Create your own JSON files** - Start with simple single-section files
2. **Organize existing scripts** - Convert related .txt files to multi-section JSON
3. **Experiment with metadata** - Use description, comments, author fields
4. **Build a library** - Create reusable section libraries for common tasks
5. **Prepare for Phase 2** - Think about which sections would benefit from structured format

## Support Files

- `parser_modifications.py` - Exact parser changes
- `executor_modifications.py` - Exact executor changes
- `USAGE_GUIDE.md` - Complete usage documentation
- `example_single_section.json` - Simple single-section example
- `example_multi_section.json` - Multi-section with variations
- `procedural_library.json` - Comprehensive procedural examples

## Rollback Instructions

If needed, rollback to previous version:
```bash
cp src/commands/parser.py.backup src/commands/parser.py
cp src/commands/executor.py.backup src/commands/executor.py
```

Your .txt scripts will continue working normally with the rollback.
