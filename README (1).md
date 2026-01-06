# Shape Studio Phase 1: JSON Script Support

## Overview

Phase 1 adds JSON-based script support to Shape Studio, enabling organized multi-section script files with metadata. This enhances the existing text-based script system without replacing it.

## What's New

### Multi-Section JSON Files
Organize related script variations in a single file:
```json
{
  "test_v1": {"commands": [...]},
  "test_v2": {"commands": [...]},
  "test_v3": {"commands": [...]}
}
```

### Metadata Support
Document your scripts with rich metadata:
```json
{
  "my_section": {
    "description": "What this does",
    "author": "Your name",
    "created": "2026-01-05",
    "comments": "Notes and observations",
    "commands": [...]
  }
}
```

### Selective Execution
Run specific sections from multi-section files:
```bash
RUN library.json section_name
BATCH 10 library.json section_name output
```

## Files Included

### Documentation
- **README.md** (this file) - Overview
- **INSTALLATION_TESTING.md** - Step-by-step installation and testing
- **USAGE_GUIDE.md** - Complete usage documentation

### Code Changes
- **parser_modifications.py** - Parser changes to apply
- **executor_modifications.py** - Executor changes to apply

### Examples
- **example_single_section.json** - Simple single-section example
- **example_multi_section.json** - Multi-section with variations
- **procedural_library.json** - Comprehensive procedural examples

## Quick Start

### 1. Install (5 minutes)
```bash
# Backup current files
cp src/commands/parser.py src/commands/parser.py.backup
cp src/commands/executor.py src/commands/executor.py.backup

# Apply changes from:
# - parser_modifications.py
# - executor_modifications.py

# Copy examples
cp *.json scripts/
```

### 2. Test (2 minutes)
```bash
# Test single section
RUN example_single_section.json

# Test multi-section
RUN example_multi_section.json test_small

# Test batch
BATCH 5 example_multi_section.json batch_random_template test_output
```

### 3. Create Your Own
```json
{
  "my_test": {
    "description": "My first JSON script",
    "commands": [
      "CLEAR WIP ALL",
      "PROC dynamic_polygon test VERTICES=5 BOUNDS=100,100,600,600",
      "COLOR test blue"
    ]
  }
}
```

## Key Features

### ✅ Backward Compatible
- All existing .txt scripts work unchanged
- JSON is an addition, not a replacement
- No impact on current workflow

### ✅ Organized
- Multiple related scripts in one file
- Clear section names
- Rich metadata for documentation

### ✅ Flexible
- Single or multiple sections per file
- Auto-run for single-section files
- Explicit selection for multi-section files

### ✅ Well-Documented
- Description field for each section
- Comments field for notes
- Author and date tracking

### ✅ RAND() Support
- RAND() functions work in JSON commands
- Perfect for batch dataset generation
- Same syntax as text files

## Command Syntax

### RUN Command
```bash
# Text files (unchanged)
RUN script.txt

# JSON files
RUN script.json                  # Auto-run if 1 section
RUN script.json section_name     # Run specific section
```

### BATCH Command
```bash
# Text files (unchanged)
BATCH count script.txt output

# JSON files (section required)
BATCH count script.json section_name output
```

## Use Cases

### 1. Parameter Exploration
Create multiple variations testing different parameters:
```json
{
  "depth_low": {"commands": ["PROC ... DEPTH_RANGE=0.2,0.4"]},
  "depth_med": {"commands": ["PROC ... DEPTH_RANGE=0.4,0.6"]},
  "depth_high": {"commands": ["PROC ... DEPTH_RANGE=0.6,0.8"]}
}
```

### 2. Progressive Refinement
Track evolution of your work:
```json
{
  "v1_initial": {"comments": "First try", "commands": [...]},
  "v2_improved": {"comments": "Better depth", "commands": [...]},
  "v3_final": {"comments": "Perfect!", "commands": [...]}
}
```

### 3. Template Library
Store reference templates and variations:
```json
{
  "organic_template": {"comments": "Reference only", "commands": [...]},
  "variant_1": {"comments": "Copy of template", "commands": [...]},
  "variant_2": {"comments": "Modified depth", "commands": [...]}
}
```

### 4. Dataset Generation
Batch generate with randomization:
```json
{
  "dataset_gen": {
    "commands": [
      "PROC ... VERTICES=RAND(5,8) ITERATIONS=RAND(10,20)",
      "PROMOTE shape"
    ]
  }
}
```
```bash
BATCH 100 dataset.json dataset_gen output
```

## File Organization

### By Purpose
```
scripts/
  quick_tests.json          # Fast iteration tests
  experiments.json          # Parameter exploration
  production.json           # Final versions
  datasets.json            # Batch generation templates
```

### By Project
```
scripts/
  flower_project.json       # All flower variations
  abstract_shapes.json      # All abstract work
  geometric_tests.json      # Geometric explorations
```

## Phase 1 Limitations

These are features for future phases:

- ❌ Structured command format (Phase 2)
- ❌ Template system with inheritance (Phase 3)
- ❌ Variable substitution (Phase 2)
- ❌ Cross-section references (Phase 3)

## What Works Now

- ✅ Multi-section organization
- ✅ Rich metadata
- ✅ Section selection
- ✅ String commands (same as .txt)
- ✅ RAND() functions
- ✅ BATCH generation
- ✅ Auto-run for single sections
- ✅ Helpful error messages
- ✅ Complete validation

## Documentation

### Quick Reference
- **INSTALLATION_TESTING.md** - Installation steps and test checklist
- **USAGE_GUIDE.md** - Complete syntax and examples

### Examples
- **example_single_section.json** - Simple starter example
- **example_multi_section.json** - Multi-section demonstration
- **procedural_library.json** - Real-world procedural examples

### Code
- **parser_modifications.py** - Exact parser changes needed
- **executor_modifications.py** - Exact executor changes needed

## Testing

See **INSTALLATION_TESTING.md** for complete test suite (16 tests).

Quick smoke test:
```bash
RUN example_single_section.json
# Should auto-run and create blue polygon

RUN example_multi_section.json test_small
# Should create red polygon in small bounds

BATCH 3 example_multi_section.json batch_random_template test
# Should create 3 varied PNG files
```

## Troubleshooting

### Error: "File not found"
→ Ensure JSON file is in scripts/ directory

### Error: "Invalid JSON"
→ Validate JSON syntax (check commas, brackets, quotes)

### Error: "Multiple sections found"
→ Specify section name: `RUN file.json section_name`

### Error: "Section not found"
→ Check section name spelling (case sensitive)

See **INSTALLATION_TESTING.md** for complete troubleshooting guide.

## Next Steps

After successful installation:

1. **Test thoroughly** - Use INSTALLATION_TESTING.md checklist
2. **Review examples** - Study the three example JSON files
3. **Convert scripts** - Move related .txt scripts to JSON sections
4. **Create templates** - Build reusable section libraries
5. **Experiment** - Try parameter exploration workflows
6. **Prepare for Phase 2** - Think about structured command format

## Phase 2 Preview

Phase 2 will add:
- Structured command format (dictionaries)
- Mixed string/structured commands
- Enhanced RAND() in structured format
- More validation options

Phase 1 JSON structure is forward-compatible.

## Support

Files provided:
- README.md (this file)
- INSTALLATION_TESTING.md (installation guide)
- USAGE_GUIDE.md (complete documentation)
- parser_modifications.py (code changes)
- executor_modifications.py (code changes)
- Three example JSON files

## Summary

Phase 1 provides:
- ✅ Multi-section JSON script files
- ✅ Rich metadata support
- ✅ Selective section execution
- ✅ Backward compatible with .txt files
- ✅ RAND() support for batch generation
- ✅ Comprehensive validation
- ✅ Helpful error messages

Enables:
- Better organization of related scripts
- Documentation within script files
- Template-based workflows
- Efficient parameter exploration
- Professional dataset generation

**Install time:** ~10 minutes
**Learning curve:** Minimal (same command syntax as .txt)
**Impact:** Significant workflow improvement

Ready to revolutionize your Shape Studio workflow! 🚀
